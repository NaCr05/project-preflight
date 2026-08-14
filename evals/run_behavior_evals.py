#!/usr/bin/env python3
"""Prepare and score reproducible Project Preflight behavior-eval workspaces."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from preflight_eval import BehaviorEvalHarness, EvalBudgetRegistry


def _pairs(values: list[str] | None) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in values or ():
        if "=" not in item:
            raise ValueError(f"expected NAME=VERSION, got: {item}")
        name, version = item.split("=", 1)
        if not name or not version:
            raise ValueError(f"expected non-empty NAME=VERSION, got: {item}")
        result[name] = version
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=Path(__file__).with_name("cases.json"))
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("list")

    budget = subparsers.add_parser("check-budget")
    budget.add_argument("profile")
    budget.add_argument("--total-tokens", type=int, required=True)
    budget.add_argument("--latency-ms", type=int, required=True)
    budget.add_argument(
        "--budgets",
        type=Path,
        default=Path(__file__).with_name("budgets.json"),
    )

    prepare = subparsers.add_parser("prepare")
    prepare.add_argument("case_id")
    prepare.add_argument("destination", type=Path)

    score = subparsers.add_parser("score")
    score.add_argument("prepared_directory", type=Path)
    score.add_argument("--model", required=True)
    score.add_argument("--dependency-version", action="append")
    score.add_argument("--latency-ms", type=int)
    score.add_argument("--cost-usd", type=float)
    score.add_argument("--total-tokens", type=int)
    score.add_argument("--json-out", type=Path)
    score.add_argument("--markdown-out", type=Path)

    args = parser.parse_args(argv)
    try:
        harness = BehaviorEvalHarness(args.manifest)
        if args.command == "list":
            for case in harness.list_cases():
                print(f"{case['id']}\t{case['title']}")
            return 0
        if args.command == "prepare":
            print(harness.prepare(args.case_id, args.destination))
            return 0
        if args.command == "check-budget":
            result = EvalBudgetRegistry(args.budgets).check(
                args.profile,
                total_tokens=args.total_tokens,
                latency_ms=args.latency_ms,
            )
            print(f"{'PASS' if result.passed else 'FAIL'} {result.profile}")
            print(
                f"total_tokens: {result.observed['total_tokens']} / "
                f"{result.ceilings['total_tokens']}"
            )
            print(
                f"latency_ms: {result.observed['latency_ms']} / "
                f"{result.ceilings['latency_ms']}"
            )
            for violation in result.violations:
                print(f"VIOLATION: {violation}", file=sys.stderr)
            return 0 if result.passed else 1
        if args.command == "score":
            result = harness.score(
                args.prepared_directory,
                model=args.model,
                dependency_versions=_pairs(args.dependency_version),
                latency_ms=args.latency_ms,
                cost_usd=args.cost_usd,
                total_tokens=args.total_tokens,
            )
            json_out = args.json_out or args.prepared_directory / "result.json"
            markdown_out = args.markdown_out or args.prepared_directory / "result.md"
            harness.write_result(result, json_out, markdown_out)
            print(f"{'PASS' if result.passed else 'FAIL'} {result.score}/{result.maximum_score}")
            print(json_out)
            print(markdown_out)
            return 0 if result.passed else 1
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
