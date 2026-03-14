#!/usr/bin/env python3
"""
Score sf-docs benchmark results.

Input files:
- benchmark definition JSON
- results JSON recording qmd_first and no_qmd outcomes per case

A case counts as a pass when:
- status == "pass"
- grounded == true
- source family matches one of the expected families (if provided)
- guide matches one of the expected guides when expected guides are listed

Usage:
  python3 score_retrieval_benchmark.py \
    --benchmark skills/sf-docs/assets/retrieval-benchmark.json \
    --results skills/sf-docs/assets/retrieval-benchmark.results-template.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple


VALID_STATUSES = {"pass", "fail", "partial", "pending"}


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text())


def index_benchmark_cases(benchmark: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {case["id"]: case for case in benchmark.get("cases", [])}


def evaluate_mode(case: Dict[str, Any], result: Dict[str, Any]) -> Tuple[bool, List[str]]:
    reasons: List[str] = []
    status = result.get("status")
    source_family = result.get("source_family")
    guide = result.get("guide")
    grounded = result.get("grounded")

    if status not in VALID_STATUSES:
        reasons.append(f"invalid status: {status}")
        return False, reasons

    if status != "pass":
        reasons.append(f"status is {status}")
        return False, reasons

    if grounded is not True:
        reasons.append("result not grounded")

    expected_families = case.get("expected_families") or []
    if expected_families and source_family not in expected_families:
        reasons.append(f"family {source_family!r} not in expected families {expected_families}")

    expected_guides = case.get("expected_guides") or []
    if expected_guides and guide not in expected_guides:
        reasons.append(f"guide {guide!r} not in expected guides {expected_guides}")

    return len(reasons) == 0, reasons


def score(benchmark: Dict[str, Any], results: Dict[str, Any]) -> Dict[str, Any]:
    cases_by_id = index_benchmark_cases(benchmark)
    totals = {
        "qmd_first": {"pass": 0, "fail": 0, "pending": 0, "details": []},
        "no_qmd": {"pass": 0, "fail": 0, "pending": 0, "details": []},
    }

    for row in results.get("results", []):
        case_id = row.get("id")
        case = cases_by_id.get(case_id)
        if not case:
            continue

        for mode in ("qmd_first", "no_qmd"):
            mode_result = row.get(mode, {})
            status = mode_result.get("status", "pending")
            if status == "pending":
                totals[mode]["pending"] += 1
                totals[mode]["details"].append({"id": case_id, "status": "pending", "reasons": []})
                continue

            passed, reasons = evaluate_mode(case, mode_result)
            if passed:
                totals[mode]["pass"] += 1
                totals[mode]["details"].append({"id": case_id, "status": "pass", "reasons": []})
            else:
                totals[mode]["fail"] += 1
                totals[mode]["details"].append({"id": case_id, "status": "fail", "reasons": reasons})

    return totals


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Score sf-docs retrieval benchmark results")
    parser.add_argument("--benchmark", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    benchmark = load_json(args.benchmark)
    results = load_json(args.results)
    totals = score(benchmark, results)

    for mode in ("qmd_first", "no_qmd"):
        summary = totals[mode]
        total_scored = summary["pass"] + summary["fail"] + summary["pending"]
        print(f"{mode}: pass={summary['pass']} fail={summary['fail']} pending={summary['pending']} total={total_scored}")
        for detail in summary["details"]:
            if detail["status"] == "fail":
                print(f"  FAIL {detail['id']}: {'; '.join(detail['reasons'])}")
            elif detail["status"] == "pending":
                print(f"  PENDING {detail['id']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
