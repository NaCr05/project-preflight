#!/usr/bin/env python3
"""Check or refresh repository projections of the canonical Preflight contract."""

from __future__ import annotations

import argparse
from pathlib import Path

from preflight_runtime._projections import ContractProjection


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[3])
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--check", action="store_true")
    action.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)

    projection = ContractProjection(args.repo_root)
    if args.write:
        for path in projection.write():
            print(f"UPDATED: {path}")
    findings = projection.check()
    if findings:
        for finding in findings:
            print(f"STALE: {finding.path}: {finding.message}")
        return 1
    print("CURRENT: canonical contract projections")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
