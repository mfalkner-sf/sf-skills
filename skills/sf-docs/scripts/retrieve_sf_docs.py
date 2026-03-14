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
    detect_qmd,
    evaluate_qmd_results,
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


def guide_by_slug(manifest: Dict[str, Any], slug: str) -> Optional[Dict[str, Any]]:
    for g in manifest.get('guides', []):
        if g.get('slug') == slug:
            return g
    return None


def infer_slug_from_result(result: Dict[str, Any]) -> Optional[str]:
    for key in ('path', 'displayPath', 'filepath', 'file'):
        value = result.get(key)
        if isinstance(value, str) and value:
            parts = value.strip('/').split('/')
            if parts:
                return parts[0]
    return None


def qmd_search(query: str, limit: int = 8) -> List[Dict[str, Any]]:
    proc = subprocess.run(
        ['qmd', 'search', query, '--json', '-n', str(limit)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or 'qmd search failed')
    data = json.loads(proc.stdout)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ('results', 'matches', 'items'):
            if isinstance(data.get(key), list):
                return data[key]
    return []


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


def excerpt(text: str, limit: int = 800) -> str:
    return text[:limit].strip()


def retrieve_from_local_artifacts(guide: Dict[str, Any], live_scrape: bool = False) -> Optional[Dict[str, Any]]:
    slug = guide.get('slug')
    normalized_dir_value = guide.get('normalized_dir')
    normalized_dir = Path(normalized_dir_value).expanduser() if normalized_dir_value else None
    normalized_path = normalized_dir / 'index.md' if normalized_dir else None
    if normalized_path and normalized_path.is_file():
        md = normalized_path.read_text(errors='ignore')
        meta, body = parse_frontmatter(md)
        return {
            'status': 'pass',
            'guide': slug,
            'source_family': guide.get('family'),
            'grounded': True,
            'method': 'normalized_markdown',
            'source_url': meta.get('source_url') or guide.get('root_url'),
            'excerpt': excerpt(body),
        }

    raw_scrape_path = guide.get('raw_scrape_path')
    scrape_path = Path(raw_scrape_path).expanduser() if raw_scrape_path else None
    if scrape_path and scrape_path.is_file():
        payload = read_json(scrape_path)
        text = str(payload.get('text') or '').strip()
        if text and not payload.get('likelyShell'):
            return {
                'status': 'pass',
                'guide': slug,
                'source_family': guide.get('family'),
                'grounded': True,
                'method': f"browser_scrape:{payload.get('strategy', 'unknown')}",
                'source_url': payload.get('url') or guide.get('root_url'),
                'excerpt': excerpt(text),
            }

    raw_pdf_path = guide.get('raw_pdf_path')
    pdf_path = Path(raw_pdf_path).expanduser() if raw_pdf_path else None
    if pdf_path and pdf_path.is_file():
        text, note = extract_pdf_text(pdf_path)
        if text:
            return {
                'status': 'pass',
                'guide': slug,
                'source_family': guide.get('family'),
                'grounded': True,
                'method': f'pdf:{note}',
                'source_url': guide.get('pdf_verified') or (guide.get('pdf_candidates') or [guide.get('root_url')])[0],
                'excerpt': excerpt(text),
            }

    if live_scrape and guide.get('root_url'):
        ok, payload = run_browser_scraper(guide['root_url'])
        if ok:
            text = str(payload.get('text') or '').strip()
            if text and not payload.get('likelyShell'):
                return {
                    'status': 'pass',
                    'guide': slug,
                    'source_family': guide.get('family'),
                    'grounded': True,
                    'method': f"live_browser_scrape:{payload.get('strategy', 'unknown')}",
                    'source_url': payload.get('url') or guide.get('root_url'),
                    'excerpt': excerpt(text),
                }

    return None


def fallback_retrieve(query: str, manifest: Dict[str, Any], plan: Dict[str, Any], live_scrape: bool = False) -> Dict[str, Any]:
    likely_guides = plan.get('fallback', {}).get('likely_guides', [])
    tried: List[str] = []
    for candidate in likely_guides:
        slug = candidate.get('slug')
        guide = guide_by_slug(manifest, slug) or candidate
        tried.append(slug or guide.get('title', 'unknown'))
        result = retrieve_from_local_artifacts(guide, live_scrape=live_scrape)
        if result:
            result['tried'] = tried
            return result

    return {
        'status': 'fail',
        'guide': likely_guides[0].get('slug') if likely_guides else None,
        'source_family': plan.get('fallback', {}).get('family_hint'),
        'grounded': False,
        'method': 'fallback_failed',
        'source_url': likely_guides[0].get('root_url') if likely_guides else None,
        'excerpt': '',
        'tried': tried,
    }


def retrieve(query: str, manifest_path: Path, corpus_root: Path, mode: str, live_scrape: bool) -> Dict[str, Any]:
    manifest = load_manifest(manifest_path)
    plan = build_lookup_plan(query, manifest_path, corpus_root)
    resolved_mode = mode
    if mode == 'auto':
        resolved_mode = plan.get('mode', 'no_qmd')

    if resolved_mode == 'qmd_first':
        qmd_available = plan['qmd']['available'] and plan['qmd']['corpus_ready']
        if qmd_available:
            try:
                results = qmd_search(query)
                evaluation = evaluate_qmd_results(query, results)
                if evaluation.get('strong') and results:
                    top = results[0]
                    slug = infer_slug_from_result(top)
                    doc_text = ''
                    for key in ('path', 'displayPath', 'filepath', 'file'):
                        if isinstance(top.get(key), str):
                            doc_text = qmd_get(top[key])
                            if doc_text:
                                break
                    return {
                        'status': 'pass',
                        'guide': slug,
                        'source_family': (guide_by_slug(manifest, slug) or {}).get('family') if slug else None,
                        'grounded': True,
                        'method': 'qmd_search',
                        'source_url': (guide_by_slug(manifest, slug) or {}).get('root_url') if slug else None,
                        'excerpt': excerpt(doc_text or json.dumps(top)),
                        'qmd_evaluation': evaluation,
                    }
                fallback = fallback_retrieve(query, manifest, plan, live_scrape=live_scrape)
                fallback['qmd_evaluation'] = evaluation
                fallback['method'] = f"qmd_fallback:{fallback['method']}"
                return fallback
            except Exception as e:
                fallback = fallback_retrieve(query, manifest, plan, live_scrape=live_scrape)
                fallback['qmd_error'] = str(e)
                fallback['method'] = f"qmd_error_fallback:{fallback['method']}"
                return fallback

        return fallback_retrieve(query, manifest, plan, live_scrape=live_scrape)

    # no_qmd
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
