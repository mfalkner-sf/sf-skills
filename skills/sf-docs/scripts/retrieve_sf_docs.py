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
