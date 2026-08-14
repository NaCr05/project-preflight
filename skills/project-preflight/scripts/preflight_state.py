#!/usr/bin/env python3
"""Safely initialize, update, transition, recover, and inspect Project Preflight state."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from preflight_runtime import (  # noqa: E402
    StateChange,
    StateOperationError,
    StateStore,
    render_initial_state,
)


def _pairs(values: list[str] | None, null_allowed: bool = False) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for item in values or ():
        if "=" not in item:
            raise ValueError(f"expected KEY=VALUE, got: {item}")
        key, value = item.split("=", 1)
        if not key or not value:
            raise ValueError(f"expected non-empty KEY=VALUE, got: {item}")
        result[key] = None if null_allowed and value == "null" else value
    return result


def _change(args: argparse.Namespace) -> StateChange:
    return StateChange(
        artifacts=_pairs(args.artifact, null_allowed=True),
        dependencies=_pairs(args.dependency),
        gate_statuses=_pairs(args.gate),
        gate_evidence=_pairs(args.evidence),
        original_idea=args.idea,
        blockers=args.blockers,
        next_action=args.next_action,
    )


def _add_change_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--artifact", action="append", help="Artifact update KEY=VALUE; use null to clear")
    parser.add_argument("--dependency", action="append", help="Dependency observation KEY=STATUS")
    parser.add_argument("--gate", action="append", help="Gate update gate_N=STATUS")
    parser.add_argument("--evidence", action="append", help="Gate evidence gate_N=TEXT")
    parser.add_argument("--idea", help="Replace the Original Idea section")
    parser.add_argument("--blockers", help="Replace the Blockers section")
    parser.add_argument("--next-action", help="Replace the Next Action section")


def _print_report(report) -> None:
    for warning in report.warnings:
        print(f"WARNING: {warning}", file=sys.stderr)
    print(f"VALID: {report.data['current_stage']}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-file", type=Path, default=Path(".project/preflight.md"))
    parser.add_argument("--repo-root", type=Path)
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="Validate current state")
    validate.add_argument("--check-remote", action="store_true")

    initialize = subparsers.add_parser("init", help="Create canonical initial state")
    initialize.add_argument("--project", required=True)
    initialize.add_argument("--idea")

    record = subparsers.add_parser("record", help="Record evidence without changing Stage")
    _add_change_arguments(record)

    advance = subparsers.add_parser("advance", help="Advance exactly one forward Stage")
    advance.add_argument("target_stage")
    advance.add_argument("--reason", required=True)
    _add_change_arguments(advance)

    regress = subparsers.add_parser("regress", help="Regress to the earliest affected Stage")
    regress.add_argument("target_stage")
    regress.add_argument("--reason", required=True)
    _add_change_arguments(regress)

    directive = subparsers.add_parser("directive", help="Print the next automatic orchestration directive")
    directive.add_argument("--json", action="store_true", help="Emit the directive as JSON")

    recover = subparsers.add_parser("recover", help="Atomically restore an explicitly supplied valid state")
    recover.add_argument("--source", type=Path, required=True)

    template = subparsers.add_parser("template", help="Render or check the derived initial-state asset")
    template.add_argument("--check", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    store = StateStore(args.state_file, args.repo_root)
    try:
        if args.command == "validate":
            report = store.validate(check_remote=args.check_remote)
            if not report.valid:
                raise StateOperationError("state is invalid", report.errors)
            _print_report(report)
            return 0
        if args.command == "init":
            _print_report(store.initialize(args.project, args.idea))
            return 0
        if args.command == "record":
            _print_report(store.record(_change(args)))
            return 0
        if args.command == "advance":
            _print_report(store.advance(args.target_stage, args.reason, _change(args)))
            return 0
        if args.command == "regress":
            _print_report(store.regress(args.target_stage, args.reason, _change(args)))
            return 0
        if args.command == "directive":
            directive = store.directive()
            if args.json:
                print(json.dumps(directive.to_dict(), ensure_ascii=False, indent=2))
            else:
                print(directive.announcement)
                print(directive.instruction)
            return 0
        if args.command == "recover":
            _print_report(store.recover(args.source))
            return 0
        if args.command == "template":
            rendered = render_initial_state()
            if args.check is None:
                print(rendered, end="")
                return 0
            try:
                current = args.check.read_text(encoding="utf-8")
            except (OSError, UnicodeError) as exc:
                raise StateOperationError(f"template cannot be read: {exc}") from exc
            if current != rendered:
                raise StateOperationError(
                    f"derived template is stale: {args.check}; regenerate it with this command"
                )
            print(f"CURRENT: {args.check}")
            return 0
    except (StateOperationError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        for error in getattr(exc, "errors", ()):
            print(f"- {error}", file=sys.stderr)
        return 1
    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
