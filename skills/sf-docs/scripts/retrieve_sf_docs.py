#!/usr/bin/env python3
"""
End-to-end sf-docs retrieval.

Modes:
- qmd_first: use qmd local search first, then fall back to Salesforce-aware retrieval
- no_qmd: skip qmd and use Salesforce-aware retrieval only
- auto: choose based on runtime status

Output is structured JSON for benchmarking and operator review.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from sf_docs_runtime import (  # type: ignore
    DEFAULT_CORPUS_ROOT,
    DEFAULT_MANIFEST,
    build_lookup_plan,
    build_query_signature,
    evaluate_qmd_results,
    evaluate_text_evidence,
    normalize_query,
)
from sync_sf_docs import extract_pdf_text, read_json, run_browser_scraper  # type: ignore


HELP_ARTICLE_HINTS = {
    'agentforce': [
        'https://help.salesforce.com/s/articleView?id=ai.generative_ai.htm',
        'https://help.salesforce.com/s/articleView?id=sf.copilot_intro.htm&type=5',
    ],
    'generative ai': [
        'https://help.salesforce.com/s/articleView?id=ai.generative_ai.htm',
    ],
    'messaging': [
        'https://help.salesforce.com/s/articleView?id=service.miaw_intro_landing.htm',
    ],
    'enhanced web chat': [
        'https://help.salesforce.com/s/articleView?id=service.miaw_intro_landing.htm',
    ],
    'in-app and web': [
        'https://help.salesforce.com/s/articleView?id=service.miaw_intro_landing.htm',
    ],
}

HELP_DISCOVERY_SOURCES = {
    'agentforce': [
        'https://developer.salesforce.com/docs/ai/agentforce/guide/',
    ],
    'generative ai': [
        'https://developer.salesforce.com/docs/ai/agentforce/guide/',
    ],
    'messaging': [
        'https://developer.salesforce.com/docs/service/messaging-web/guide/',
    ],
    'enhanced web chat': [
        'https://developer.salesforce.com/docs/service/messaging-web/guide/',
    ],
    'in-app and web': [
        'https://developer.salesforce.com/docs/service/messaging-web/guide/',
    ],
}


def load_manifest(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text())


def parse_frontmatter(md_text: str) -> Tuple[Dict[str, str], str]:
    if not md_text.startswith('---\n'):
        return {}, md_text
    parts = md_text.split('\n---\n', 1)
    if len(parts) != 2:
        return {}, md_text
    fm_text = parts[0].split('---\n', 1)[1]
    body = parts[1]
    meta: Dict[str, str] = {}
    for line in fm_text.splitlines():
        if ':' in line:
            k, v = line.split(':', 1)
            meta[k.strip()] = v.strip().strip('"')
    return meta, body


def guide_by_slug(manifest: Dict[str, Any], slug: Optional[str]) -> Optional[Dict[str, Any]]:
    if not slug:
        return None
    for g in manifest.get('guides', []):
        if g.get('slug') == slug:
            return g
    return None


def infer_slug_from_result(result: Dict[str, Any], manifest: Dict[str, Any]) -> Optional[str]:
    candidates: List[str] = []
    for key in ('path', 'displayPath', 'filepath', 'file'):
        value = result.get(key)
        if not isinstance(value, str) or not value:
            continue
        if value.startswith('qmd://'):
            match = re.match(r'qmd://[^/]+/([^/]+)/', value)
            if match:
                candidates.append(match.group(1))
        parts = [p for p in value.strip('/').split('/') if p]
        if parts:
            candidates.extend(parts)

    manifest_slugs = {g.get('slug'): g for g in manifest.get('guides', [])}
    normalized = {slug.replace('_', '-'): slug for slug in manifest_slugs if slug}
    for candidate in candidates:
        key = candidate.replace('.md', '').replace('index', '').strip('/').strip()
        if not key:
            continue
        if key in manifest_slugs:
            return key
        if key in normalized:
            return normalized[key]
        if key.replace('-', '_') in manifest_slugs:
            return key.replace('-', '_')
    return None


def _parse_qmd_search_output(stdout: str) -> List[Dict[str, Any]]:
    data = json.loads(stdout)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ('results', 'matches', 'items'):
            if isinstance(data.get(key), list):
                return data[key]
    return []


def qmd_search(query: str, limit: int = 8) -> Tuple[List[Dict[str, Any]], str]:
    signature = build_query_signature(query)
    compact_parts: List[str] = []
    compact_parts.extend(signature.get('identifiers', [])[:2])
    compact_parts.extend(signature.get('phrases', [])[:2])
    compact_parts.extend(signature.get('terms', [])[:4])
    compact_query = ' '.join(compact_parts).strip()
    candidates = [query]
    if compact_query and compact_query != query:
        candidates.append(compact_query)

    last_error = 'qmd search failed'
    for candidate in candidates:
        proc = subprocess.run(
            ['qmd', 'search', candidate, '--json', '-n', str(limit)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if proc.returncode != 0:
            last_error = proc.stderr.strip() or proc.stdout.strip() or last_error
            continue
        results = _parse_qmd_search_output(proc.stdout)
        if results:
            return results, candidate
    if last_error:
        raise RuntimeError(last_error)
    return [], query


def qmd_get(doc_path: str) -> str:
    proc = subprocess.run(
        ['qmd', 'get', doc_path, '--full'],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if proc.returncode != 0:
        return ''
    return proc.stdout


def build_excerpt(text: str, needles: List[str], limit: int = 800) -> str:
    cleaned = text.strip()
    if not cleaned:
        return ''
    lowered = normalize_query(cleaned)
    for needle in needles:
        normalized = normalize_query(needle)
        if not normalized:
            continue
        idx = lowered.find(normalized)
        if idx >= 0:
            start = max(0, idx - 220)
            end = min(len(cleaned), idx + max(limit - 220, 280))
            return cleaned[start:end].strip()
    return cleaned[:limit].strip()


def enrich_result(base: Dict[str, Any], evidence: Dict[str, Any], text: str) -> Dict[str, Any]:
    needles = evidence.get('matched_evidence') or evidence.get('matched_terms') or []
    enriched = {
        **base,
        'confidence': evidence.get('confidence'),
        'evidence_score': evidence.get('score'),
        'evidence_reason': evidence.get('reason'),
        'matched_terms': evidence.get('matched_terms', []),
        'matched_phrases': evidence.get('matched_phrases', []),
        'matched_identifiers': evidence.get('matched_identifiers', []),
        'matched_evidence': evidence.get('matched_evidence', []),
        'excerpt': build_excerpt(text, list(needles)),
    }
    return enriched


def canonical_help_url(url: str) -> str:
    return re.sub(r'([?&])language=en_US&?', r'\1', url).rstrip('?&')


def help_article_id(url: str) -> str:
    match = re.search(r'[?&]id=([^&#]+)', url)
    if match:
        return match.group(1)
    return canonical_help_url(url).rstrip('/').rsplit('/', 1)[-1]


def help_article_missing(payload: Dict[str, Any]) -> bool:
    title = normalize_query(payload.get('title') or '')
    text = normalize_query(payload.get('text') or '')
    bad_signals = [
        'we looked high and low',
        "couldn't find that page",
        '404 error',
        'salesforce help | article',
    ]
    return any(signal in title or signal in text for signal in bad_signals)


def help_article_urls_from_payload(payload: Dict[str, Any]) -> List[str]:
    urls: List[str] = []
    for link in payload.get('childLinks', []) or []:
        if isinstance(link, str) and 'help.salesforce.com/s/articleView' in link:
            urls.append(canonical_help_url(link))
    deduped: List[str] = []
    seen = set()
    for url in urls:
        if url not in seen:
            seen.add(url)
            deduped.append(url)
    return deduped


def local_scrape_payloads(manifest: Dict[str, Any], guides: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    payloads: List[Dict[str, Any]] = []
    seen_paths = set()
    for guide in guides + manifest.get('guides', []):
        raw_scrape_path = guide.get('raw_scrape_path')
        if not raw_scrape_path:
            continue
        path = str(Path(raw_scrape_path).expanduser())
        if path in seen_paths:
            continue
        seen_paths.add(path)
        scrape_path = Path(path)
        if scrape_path.is_file():
            try:
                payloads.append(read_json(scrape_path))
            except Exception:
                continue
    return payloads


def score_help_url(query: str, url: str) -> int:
    lowered = normalize_query(query)
    canonical = canonical_help_url(url).lower()
    score = 0
    for needle, urls in HELP_ARTICLE_HINTS.items():
        if needle in lowered and canonical_help_url(urls[0]).lower() == canonical:
            score += 12
    signature = build_query_signature(query)
    article_id = help_article_id(url).lower()
    for phrase in signature.get('phrases', []):
        if phrase.replace(' ', '_') in article_id or phrase.replace(' ', '.') in article_id:
            score += 8
    for term in signature.get('terms', []):
        if term in article_id:
            score += 2
    if 'miaw' in article_id and any(token in lowered for token in ('messaging', 'web chat', 'in-app and web', 'enhanced chat')):
        score += 12
    if any(token in article_id for token in ('setup', 'optimize', 'allowlist', 'cors')) and any(token in lowered for token in ('allowed domains', 'cors', 'allowed origins', 'origin')):
        score += 10
    if 'release-notes' in article_id or article_id.startswith('release-notes.'):
        score -= 12
    if 'copilot' in article_id and 'agentforce' in lowered:
        score += 8
    if 'generative_ai' in article_id and any(token in lowered for token in ('agentforce', 'generative ai')):
        score += 8
    return score


def build_help_guide(plan: Dict[str, Any], article_url: str) -> Dict[str, Any]:
    product = plan.get('classification', {}).get('product') or 'platform'
    return {
        'slug': help_article_id(article_url),
        'family': 'help',
        'product': product,
        'root_url': article_url,
    }


def scrape_help_article(query: str, plan: Dict[str, Any], article_url: str, crawl_children: bool = True) -> Optional[Dict[str, Any]]:
    ok, payload = run_browser_scraper(article_url, timeout=60)
    if not ok or help_article_missing(payload):
        return None

    guide = build_help_guide(plan, payload.get('url') or article_url)
    result = evaluate_artifact(
        query,
        guide,
        str(payload.get('text') or ''),
        f"help_article:{payload.get('strategy', 'unknown')}",
        payload.get('url') or article_url,
    )

    if not crawl_children:
        return result

    child_urls = help_article_urls_from_payload(payload)
    child_urls.sort(key=lambda item: score_help_url(query, item), reverse=True)
    best_result = result

    should_crawl = bool(child_urls) and (
        result.get('status') != 'pass'
        or result.get('evidence_score', 0) < 18
        or any(phrase in normalize_query(query) for phrase in ('allowed domains', 'allowed origins', 'cors allowlist', 'origin restrictions'))
    )
    if not should_crawl:
        return result

    for child_url in child_urls[:8]:
        child = scrape_help_article(query, plan, child_url, crawl_children=False)
        if not child:
            continue
        child['discovered_via'] = payload.get('url') or article_url
        child_rank = 2 if child.get('status') == 'pass' else (1 if child.get('status') == 'partial' else 0)
        best_rank = 2 if best_result.get('status') == 'pass' else (1 if best_result.get('status') == 'partial' else 0)
        if (child_rank, child.get('evidence_score', 0)) > (best_rank, best_result.get('evidence_score', 0)):
            best_result = child

    return best_result


def help_article_fallback(query: str, manifest: Dict[str, Any], plan: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    lowered = normalize_query(query)
    likely_guides = [guide_by_slug(manifest, g.get('slug')) or g for g in plan.get('fallback', {}).get('likely_guides', [])]
    urls: List[str] = []

    for needle, hinted_urls in HELP_ARTICLE_HINTS.items():
        if needle in lowered:
            urls.extend(hinted_urls)

    for payload in local_scrape_payloads(manifest, likely_guides):
        urls.extend(help_article_urls_from_payload(payload))

    for needle, source_urls in HELP_DISCOVERY_SOURCES.items():
        if needle not in lowered:
            continue
        for source_url in source_urls:
            ok, payload = run_browser_scraper(source_url, timeout=60)
            if ok:
                urls.extend(help_article_urls_from_payload(payload))

    deduped: List[str] = []
    seen = set()
    for url in urls:
        canonical = canonical_help_url(url)
        if canonical not in seen:
            seen.add(canonical)
            deduped.append(canonical)

    deduped.sort(key=lambda item: score_help_url(query, item), reverse=True)
    best_partial: Optional[Dict[str, Any]] = None
    for article_url in deduped[:10]:
        result = scrape_help_article(query, plan, article_url, crawl_children=True)
        if not result:
            continue
        if result.get('status') == 'pass':
            return result
        if result.get('status') == 'partial' and (
            best_partial is None or result.get('evidence_score', 0) > best_partial.get('evidence_score', 0)
        ):
            best_partial = result
    return best_partial


def evaluate_artifact(query: str, guide: Dict[str, Any], text: str, method: str, source_url: str) -> Dict[str, Any]:
    evidence = evaluate_text_evidence(query, text, guide)
    fail_reasons = {'wrong_family_match', 'external_term_missing', 'missing_identifier', 'partial_identifier_match'}
    if evidence.get('acceptable'):
        status = 'pass'
    elif evidence.get('reason') in fail_reasons:
        status = 'fail'
    else:
        status = 'partial' if evidence.get('score', 0) > 0 else 'fail'
    grounded = status in ('pass', 'partial')
    result = {
        'status': status,
        'guide': guide.get('slug'),
        'source_family': guide.get('family'),
        'source_product': guide.get('product'),
        'grounded': grounded,
        'method': method,
        'source_url': source_url,
    }
    return enrich_result(result, evidence, text)


def retrieve_from_local_artifacts(query: str, guide: Dict[str, Any], live_scrape: bool = False) -> Optional[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []

    normalized_dir_value = guide.get('normalized_dir')
    normalized_dir = Path(normalized_dir_value).expanduser() if normalized_dir_value else None
    normalized_path = normalized_dir / 'index.md' if normalized_dir else None
    if normalized_path and normalized_path.is_file():
        md = normalized_path.read_text(errors='ignore')
        meta, body = parse_frontmatter(md)
        candidates.append(evaluate_artifact(
            query,
            guide,
            body,
            'normalized_markdown',
            meta.get('source_url') or guide.get('root_url'),
        ))

    raw_scrape_path = guide.get('raw_scrape_path')
    scrape_path = Path(raw_scrape_path).expanduser() if raw_scrape_path else None
    if scrape_path and scrape_path.is_file():
        payload = read_json(scrape_path)
        text = str(payload.get('text') or '').strip()
        if text and not payload.get('likelyShell'):
            candidates.append(evaluate_artifact(
                query,
                guide,
                text,
                f"browser_scrape:{payload.get('strategy', 'unknown')}",
                payload.get('url') or guide.get('root_url'),
            ))

    raw_pdf_path = guide.get('raw_pdf_path')
    pdf_path = Path(raw_pdf_path).expanduser() if raw_pdf_path else None
    if pdf_path and pdf_path.is_file():
        text, note = extract_pdf_text(pdf_path)
        if text:
            candidates.append(evaluate_artifact(
                query,
                guide,
                text,
                f'pdf:{note}',
                guide.get('pdf_verified') or (guide.get('pdf_candidates') or [guide.get('root_url')])[0],
            ))

    if live_scrape and guide.get('root_url'):
        ok, payload = run_browser_scraper(guide['root_url'])
        if ok:
            text = str(payload.get('text') or '').strip()
            if text and not payload.get('likelyShell'):
                candidates.append(evaluate_artifact(
                    query,
                    guide,
                    text,
                    f"live_browser_scrape:{payload.get('strategy', 'unknown')}",
                    payload.get('url') or guide.get('root_url'),
                ))

    if not candidates:
        return None

    rank = {'pass': 3, 'partial': 2, 'fail': 1}
    candidates.sort(key=lambda item: (rank.get(item['status'], 0), item.get('evidence_score', 0)), reverse=True)
    return candidates[0]


def fallback_retrieve(query: str, manifest: Dict[str, Any], plan: Dict[str, Any], live_scrape: bool = False) -> Dict[str, Any]:
    likely_guides = plan.get('fallback', {}).get('likely_guides', [])
    tried: List[str] = []
    best_partial: Optional[Dict[str, Any]] = None

    if plan.get('fallback', {}).get('family_hint') == 'help':
        help_result = help_article_fallback(query, manifest, plan)
        if help_result:
            help_result['tried'] = ['help-article-discovery']
            if help_result.get('status') == 'pass':
                return help_result
            best_partial = help_result if help_result.get('status') == 'partial' else best_partial

    for candidate in likely_guides:
        slug = candidate.get('slug')
        guide = guide_by_slug(manifest, slug) or candidate
        tried.append(slug or guide.get('title', 'unknown'))
        result = retrieve_from_local_artifacts(query, guide, live_scrape=live_scrape)
        if not result:
            continue
        result['tried'] = tried.copy()
        if result.get('status') == 'pass':
            return result
        if result.get('status') == 'partial' and (
            best_partial is None or result.get('evidence_score', 0) > best_partial.get('evidence_score', 0)
        ):
            best_partial = result

    if best_partial:
        if 'tried' not in best_partial:
            best_partial['tried'] = tried
        return best_partial

    return {
        'status': 'fail',
        'guide': likely_guides[0].get('slug') if likely_guides else None,
        'source_family': plan.get('fallback', {}).get('family_hint'),
        'source_product': None,
        'grounded': False,
        'method': 'fallback_failed',
        'source_url': likely_guides[0].get('root_url') if likely_guides else None,
        'excerpt': '',
        'confidence': 'low',
        'evidence_score': 0,
        'evidence_reason': 'no_viable_artifact',
        'matched_terms': [],
        'matched_phrases': [],
        'matched_identifiers': [],
        'matched_evidence': [],
        'tried': tried,
    }


def retrieve(query: str, manifest_path: Path, corpus_root: Path, mode: str, live_scrape: bool) -> Dict[str, Any]:
    manifest = load_manifest(manifest_path)
    plan = build_lookup_plan(query, manifest_path, corpus_root)
    resolved_mode = mode
    if mode == 'auto':
        resolved_mode = 'qmd_first' if plan.get('mode') == 'qmd_enabled' else 'no_qmd'

    if resolved_mode == 'qmd_first':
        qmd_available = plan['qmd']['available'] and plan['qmd']['corpus_ready']
        if qmd_available:
            try:
                results, qmd_query_used = qmd_search(query)
                evaluation = evaluate_qmd_results(query, results)
                if evaluation.get('strong') and results:
                    best_index = evaluation.get('best_index') or 0
                    top = results[best_index]
                    slug = infer_slug_from_result(top, manifest)
                    guide = guide_by_slug(manifest, slug)
                    doc_text = ''
                    for key in ('path', 'displayPath', 'filepath', 'file'):
                        if isinstance(top.get(key), str):
                            doc_text = qmd_get(top[key])
                            if doc_text:
                                break
                    qmd_text = doc_text or json.dumps(top)
                    evidence = {
                        'acceptable': True,
                        'confidence': 'high' if evaluation.get('matched_identifiers') else 'medium',
                        'score': evaluation.get('best_evidence_score', 0),
                        'reason': evaluation.get('reason'),
                        'matched_terms': evaluation.get('matched_terms', []),
                        'matched_phrases': evaluation.get('matched_phrases', []),
                        'matched_identifiers': evaluation.get('matched_identifiers', []),
                        'matched_evidence': evaluation.get('matched_evidence', []),
                    }
                    base = {
                        'status': 'pass',
                        'guide': slug,
                        'source_family': guide.get('family') if guide else None,
                        'source_product': guide.get('product') if guide else None,
                        'grounded': True,
                        'method': 'qmd_search',
                        'source_url': guide.get('root_url') if guide else None,
                        'qmd_evaluation': {**evaluation, 'query_used': qmd_query_used},
                    }
                    return enrich_result(base, evidence, qmd_text or json.dumps(top))

                fallback = fallback_retrieve(query, manifest, plan, live_scrape=live_scrape)
                fallback['qmd_evaluation'] = {**evaluation, 'query_used': qmd_query_used}
                fallback['method'] = f"qmd_fallback:{fallback['method']}"
                return fallback
            except Exception as e:
                fallback = fallback_retrieve(query, manifest, plan, live_scrape=live_scrape)
                fallback['qmd_error'] = str(e)
                fallback['method'] = f"qmd_error_fallback:{fallback['method']}"
                return fallback

        return fallback_retrieve(query, manifest, plan, live_scrape=live_scrape)

    return fallback_retrieve(query, manifest, plan, live_scrape=live_scrape)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Retrieve Salesforce docs using sf-docs runtime flow')
    parser.add_argument('--query', required=True)
    parser.add_argument('--manifest', type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument('--corpus-root', type=Path, default=DEFAULT_CORPUS_ROOT)
    parser.add_argument('--mode', choices=('auto', 'qmd_first', 'no_qmd'), default='auto')
    parser.add_argument('--live-scrape', action='store_true', help='Allow live browser scraping during fallback')
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = retrieve(args.query, args.manifest.expanduser(), args.corpus_root.expanduser(), args.mode, args.live_scrape)
    print(json.dumps(result, indent=2))
    return 0 if result.get('status') == 'pass' else 1


if __name__ == '__main__':
    sys.exit(main())
