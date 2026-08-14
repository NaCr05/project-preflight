#!/usr/bin/env python3
"""Validate a Project Preflight state file using the State lifecycle module."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from preflight_runtime import inspect_path, validate_path  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "state_file",
        nargs="?",
        default=".project/preflight.md",
        help="State file to validate (default: .project/preflight.md)",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        help="Repository root used to resolve artifact pointers",
    )
    parser.add_argument(
        "--check-remote",
        action="store_true",
        help="Check remote URL accessibility; may require GH_TOKEN or GITHUB_TOKEN",
    )
    args = parser.parse_args(argv)
    path = Path(args.state_file)
    report = inspect_path(path, args.repo_root, check_remote=args.check_remote)
    for warning in report.warnings:
        print(f"WARNING: {warning}", file=sys.stderr)
    if report.errors:
        print(f"INVALID: {path}", file=sys.stderr)
        for error in report.errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"VALID: {path} ({report.data['current_stage']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
