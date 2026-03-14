#!/usr/bin/env python3
"""
Run the sf-docs retrieval benchmark against qmd_first and no_qmd modes.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from retrieve_sf_docs import retrieve  # type: ignore


DEFAULT_BENCHMARK = SCRIPT_DIR.parent / 'assets' / 'retrieval-benchmark.json'
DEFAULT_RESULTS = SCRIPT_DIR.parent / 'assets' / 'retrieval-benchmark.results-template.json'
DEFAULT_MANIFEST = Path.home() / '.sf-docs' / 'manifest' / 'guides.json'
DEFAULT_CORPUS_ROOT = Path.home() / '.sf-docs'


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text())


def expected_match(case: Dict[str, Any], result: Dict[str, Any]) -> bool:
    if result.get('status') != 'pass' or result.get('grounded') is not True:
        return False
    families = case.get('expected_families') or []
    guides = case.get('expected_guides') or []
    if families and result.get('source_family') not in families:
        return False
    if guides and result.get('guide') not in guides:
        return False
    return True


def run_case(case: Dict[str, Any], manifest: Path, corpus_root: Path, live_scrape: bool) -> Dict[str, Any]:
    qmd_result = retrieve(case['query'], manifest, corpus_root, 'qmd_first', live_scrape=live_scrape)
    no_qmd_result = retrieve(case['query'], manifest, corpus_root, 'no_qmd', live_scrape=live_scrape)

    def adapt(result: Dict[str, Any]) -> Dict[str, Any]:
        status = 'pass' if expected_match(case, result) else ('partial' if result.get('status') == 'pass' else 'fail')
        return {
            'status': status,
            'source_family': result.get('source_family'),
            'guide': result.get('guide'),
            'grounded': result.get('grounded'),
            'notes': result.get('method', ''),
            'source_url': result.get('source_url'),
        }

    return {
        'id': case['id'],
        'qmd_first': adapt(qmd_result),
        'no_qmd': adapt(no_qmd_result),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Run sf-docs retrieval benchmark')
    parser.add_argument('--benchmark', type=Path, default=DEFAULT_BENCHMARK)
    parser.add_argument('--results', type=Path, default=DEFAULT_RESULTS)
    parser.add_argument('--manifest', type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument('--corpus-root', type=Path, default=DEFAULT_CORPUS_ROOT)
    parser.add_argument('--live-scrape', action='store_true')
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    benchmark = load_json(args.benchmark)
    out = {
        'version': 1,
        'benchmark': args.benchmark.name,
        'generated_at': benchmark.get('generated_at'),
        'modes': {
            'qmd_first': {'description': 'qmd-first local retrieval with Salesforce-aware fallback on weak/missing results'},
            'no_qmd': {'description': 'Salesforce-aware retrieval without qmd/local index'},
        },
        'results': [run_case(case, args.manifest.expanduser(), args.corpus_root.expanduser(), args.live_scrape) for case in benchmark.get('cases', [])],
    }
    args.results.write_text(json.dumps(out, indent=2) + '\n')
    print(f'Wrote benchmark results: {args.results}')
    print(f"Cases: {len(out['results'])}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
