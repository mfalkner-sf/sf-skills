#!/usr/bin/env python3
"""
Bootstrap qmd for the sf-docs local corpus.

This helper configures a single qmd collection rooted at the normalized
Salesforce docs corpus and optionally runs embedding.

Examples:
  python3 bootstrap_qmd.py --corpus-root ~/.sf-docs
  python3 bootstrap_qmd.py --corpus-root ~/.sf-docs --embed
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List

DEFAULT_CORPUS_ROOT = Path.home() / ".sf-docs"

GLOBAL_CONTEXT = (
    "Official Salesforce public documentation corpus used by sf-docs. "
    "Prefer this source over third-party blogs for platform guidance, API references, "
    "setup documentation, and release-sensitive behavior."
)

SUBPATH_CONTEXTS = {
    "atlas": "Legacy official Salesforce guide and reference docs",
    "platform": "Modern developer.salesforce.com platform guides",
    "help": "Salesforce Help and setup documentation",
    "pdf": "Official Salesforce guide PDFs normalized for local search",
}


def run(cmd: List[str], dry_run: bool = False) -> int:
    printable = " ".join(cmd)
    if dry_run:
        print(f"DRY RUN: {printable}")
        return 0
    result = subprocess.run(cmd)
    return result.returncode


def detect_qmd() -> bool:
    return shutil.which("qmd") is not None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bootstrap qmd for sf-docs")
    parser.add_argument("--corpus-root", default=str(DEFAULT_CORPUS_ROOT))
    parser.add_argument("--name", default="sf-docs")
    parser.add_argument("--embed", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not detect_qmd():
        print("qmd is not installed or not on PATH")
        return 1

    corpus_root = Path(args.corpus_root).expanduser()
    normalized_root = corpus_root / "normalized" / "md"
    if not normalized_root.exists():
        print(f"Normalized corpus not found: {normalized_root}")
        return 1

    rc = run(["qmd", "collection", "add", str(normalized_root), "--name", args.name], dry_run=args.dry_run)
    if rc != 0 and not args.dry_run:
        print("warning: qmd collection add returned non-zero (collection may already exist)")

    run(["qmd", "context", "add", f"qmd://{args.name}", GLOBAL_CONTEXT], dry_run=args.dry_run)
    for subpath, context in SUBPATH_CONTEXTS.items():
        run(["qmd", "context", "add", f"qmd://{args.name}/{subpath}", context], dry_run=args.dry_run)

    if args.embed:
        run(["qmd", "embed"], dry_run=args.dry_run)

    print("qmd bootstrap complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
