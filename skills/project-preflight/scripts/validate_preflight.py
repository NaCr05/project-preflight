#!/usr/bin/env python3
"""Validate a Project Preflight state file using only the Python standard library."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ALLOWED_STAGES = (
    "IDEA",
    "DISCOVERY",
    "DECISION",
    "SPECIFICATION",
    "TICKETING",
    "READY_FOR_IMPLEMENTATION",
)
GATE_KEYS = ("gate_1", "gate_2", "gate_3", "gate_4")
GATE_STATUSES = {"not_evaluated", "blocked", "passed", "invalidated"}
ARTIFACT_KEYS = ("idea", "decision_map", "spec", "tickets")
DEPENDENCY_STATUSES = {"available", "missing", "not_checked"}
TOP_LEVEL_KEYS = {
    "schema_version",
    "project",
    "current_stage",
    "previous_stage",
    "last_transition",
    "transition_reason",
    "tracker",
    "ready_for_implementation",
    "gates",
    "artifacts",
    "dependencies",
}
REQUIRED_HEADINGS = (
    "# Project Preflight",
    "## Original Idea",
    "## Gate Evidence",
    "### Gate 1",
    "### Gate 2",
    "### Gate 3",
    "### Gate 4",
    "## Blockers",
    "## Next Action",
)
PASSED_GATE_COUNT = {
    "IDEA": 0,
    "DISCOVERY": 0,
    "DECISION": 1,
    "SPECIFICATION": 2,
    "TICKETING": 3,
    "READY_FOR_IMPLEMENTATION": 4,
}
REQUIRED_ARTIFACTS = {
    "IDEA": (),
    "DISCOVERY": ("idea",),
    "DECISION": ("idea",),
    "SPECIFICATION": ("idea", "decision_map"),
    "TICKETING": ("idea", "decision_map", "spec"),
    "READY_FOR_IMPLEMENTATION": ARTIFACT_KEYS,
}
ALLOWED_TRANSITIONS = {
    ("IDEA", "DISCOVERY"),
    ("DISCOVERY", "DECISION"),
    ("DECISION", "SPECIFICATION"),
    ("SPECIFICATION", "TICKETING"),
    ("TICKETING", "READY_FOR_IMPLEMENTATION"),
    ("DECISION", "DISCOVERY"),
    ("SPECIFICATION", "DECISION"),
    ("SPECIFICATION", "DISCOVERY"),
    ("TICKETING", "SPECIFICATION"),
    ("TICKETING", "DECISION"),
    ("TICKETING", "DISCOVERY"),
    ("READY_FOR_IMPLEMENTATION", "TICKETING"),
    ("READY_FOR_IMPLEMENTATION", "SPECIFICATION"),
    ("READY_FOR_IMPLEMENTATION", "DECISION"),
    ("READY_FOR_IMPLEMENTATION", "DISCOVERY"),
}


class ParseError(ValueError):
    """Raised when the restricted YAML frontmatter cannot be parsed."""


def _parse_scalar(raw: str, line_number: int) -> Any:
    value = raw.strip()
    if value == "null":
        return None
    if value == "true":
        return True
    if value == "false":
        return False
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    if value.startswith(('"', "'")):
        if not value.startswith('"'):
            raise ParseError(
                f"line {line_number}: quote strings with double quotes in restricted YAML"
            )
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ParseError(f"line {line_number}: invalid quoted value: {exc.msg}") from exc
        if not isinstance(parsed, str):
            raise ParseError(f"line {line_number}: quoted values must be strings")
        return parsed
    if not value:
        raise ParseError(f"line {line_number}: missing scalar value")
    if value[0] in "[{&*!>|":
        raise ParseError(f"line {line_number}: unsupported YAML construct")
    return value


def parse_restricted_yaml(lines: list[str]) -> dict[str, Any]:
    data: dict[str, Any] = {}
    current_map: str | None = None

    for index, line in enumerate(lines, start=2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if "\t" in line:
            raise ParseError(f"line {index}: tabs are not allowed")

        if line.startswith("  "):
            if line.startswith("    ") or current_map is None:
                raise ParseError(f"line {index}: only one two-space mapping level is allowed")
            entry = line[2:]
            if ":" not in entry:
                raise ParseError(f"line {index}: expected key: value")
            key, raw = entry.split(":", 1)
            key = key.strip()
            if not key or key in data[current_map]:
                raise ParseError(f"line {index}: empty or duplicate nested key")
            data[current_map][key] = _parse_scalar(raw, index)
            continue

        if line.startswith(" "):
            raise ParseError(f"line {index}: top-level keys must not be indented")
        if ":" not in line:
            raise ParseError(f"line {index}: expected key: value")
        key, raw = line.split(":", 1)
        key = key.strip()
        if not key or key in data:
            raise ParseError(f"line {index}: empty or duplicate top-level key")
        if raw.strip():
            data[key] = _parse_scalar(raw, index)
            current_map = None
        else:
            data[key] = {}
            current_map = key

    return data


def split_state(text: str) -> tuple[dict[str, Any], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ParseError("state file must begin with YAML frontmatter delimiter ---")
    try:
        closing = next(i for i, line in enumerate(lines[1:], start=1) if line.strip() == "---")
    except StopIteration as exc:
        raise ParseError("state file is missing the closing frontmatter delimiter ---") from exc
    return parse_restricted_yaml(lines[1:closing]), "\n".join(lines[closing + 1 :])


def _section(body: str, heading: str) -> str | None:
    level = len(heading) - len(heading.lstrip("#"))
    pattern = re.compile(
        rf"(?ms)^{re.escape(heading)}[ \t]*\n(.*?)(?=^#{{1,{level}}} |\Z)"
    )
    match = pattern.search(body)
    return match.group(1).strip() if match else None


def _anchors(body: str) -> set[str]:
    anchors: set[str] = set()
    for line in body.splitlines():
        match = re.match(r"^#{1,6}\s+(.+?)\s*$", line)
        if not match:
            continue
        label = match.group(1).strip().lower()
        label = re.sub(r"[^\w\- ]", "", label, flags=re.UNICODE)
        label = re.sub(r"[\s\-]+", "-", label).strip("-")
        anchors.add(label)
    return anchors


def _valid_timestamp(value: Any) -> bool:
    if value is None:
        return True
    if not isinstance(value, str) or not value.strip():
        return False
    candidate = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        datetime.fromisoformat(candidate)
    except ValueError:
        return False
    return True


def _resolve_local_pointer(pointer: str, repo_root: Path) -> tuple[Path | None, str | None]:
    if pointer.startswith(("http://", "https://", "inline:#")) or pointer == "not-required":
        return None, None
    path_text = pointer.split("#", 1)[0]
    if not path_text:
        return None, "local pointer has no path before its anchor"
    if Path(path_text).is_absolute() or re.match(r"^[A-Za-z]:[\\/]", path_text):
        return None, "artifact pointers must be repository-relative, not absolute"
    root = repo_root.resolve()
    candidate = (root / path_text).resolve()
    if candidate != root and root not in candidate.parents:
        return None, "artifact pointer escapes the repository root"
    return candidate, None


def validate_state(data: dict[str, Any], body: str, repo_root: Path) -> list[str]:
    errors: list[str] = []

    missing = sorted(TOP_LEVEL_KEYS - data.keys())
    unknown = sorted(data.keys() - TOP_LEVEL_KEYS)
    if missing:
        errors.append(f"missing top-level keys: {', '.join(missing)}")
    if unknown:
        errors.append(f"unknown top-level keys: {', '.join(unknown)}")
    if missing:
        return errors

    if data["schema_version"] != 1:
        errors.append("schema_version must be integer 1")
    if not isinstance(data["project"], str) or not data["project"].strip():
        errors.append("project must be a non-empty string")
    stage = data["current_stage"]
    if stage not in ALLOWED_STAGES:
        errors.append(f"current_stage must be one of: {', '.join(ALLOWED_STAGES)}")
    if not isinstance(data["tracker"], str) or not data["tracker"].strip():
        errors.append("tracker must be a non-empty string")
    if not isinstance(data["ready_for_implementation"], bool):
        errors.append("ready_for_implementation must be true or false")
    if not _valid_timestamp(data["last_transition"]):
        errors.append("last_transition must be null or an ISO-8601 timestamp")
    if not isinstance(data["transition_reason"], str) or not data["transition_reason"].strip():
        errors.append("transition_reason must be a non-empty string")

    previous = data["previous_stage"]
    if previous is not None and previous not in ALLOWED_STAGES:
        errors.append("previous_stage must be null or an allowed stage")
    elif previous is not None and stage in ALLOWED_STAGES:
        if (previous, stage) not in ALLOWED_TRANSITIONS:
            errors.append(f"illegal transition: {previous} -> {stage}")
        if data["last_transition"] is None:
            errors.append("last_transition is required when previous_stage is set")

    gates = data["gates"]
    if not isinstance(gates, dict):
        errors.append("gates must be a mapping")
    else:
        if set(gates) != set(GATE_KEYS):
            errors.append("gates must contain exactly gate_1 through gate_4")
        for key, value in gates.items():
            if value not in GATE_STATUSES:
                errors.append(f"{key} has invalid status: {value!r}")

    artifacts = data["artifacts"]
    if not isinstance(artifacts, dict):
        errors.append("artifacts must be a mapping")
    else:
        if set(artifacts) != set(ARTIFACT_KEYS):
            errors.append("artifacts must contain exactly idea, decision_map, spec, and tickets")
        for key, value in artifacts.items():
            if value is not None and (not isinstance(value, str) or not value.strip()):
                errors.append(f"artifact {key} must be null or a non-empty string")
            if value == "not-required" and key != "decision_map":
                errors.append("not-required is allowed only for decision_map")

    dependencies = data["dependencies"]
    if not isinstance(dependencies, dict) or not dependencies:
        errors.append("dependencies must be a non-empty mapping")
    else:
        for key, value in dependencies.items():
            if value not in DEPENDENCY_STATUSES:
                errors.append(f"dependency {key} has invalid status: {value!r}")

    for heading in REQUIRED_HEADINGS:
        if not re.search(rf"(?m)^{re.escape(heading)}[ \t]*$", body):
            errors.append(f"missing Markdown heading: {heading}")

    if stage in ALLOWED_STAGES and isinstance(gates, dict) and set(gates) == set(GATE_KEYS):
        passed_count = PASSED_GATE_COUNT[stage]
        for index, key in enumerate(GATE_KEYS, start=1):
            status = gates[key]
            if index <= passed_count and status != "passed":
                errors.append(f"{key} must be passed at stage {stage}")
            if index > passed_count and status == "passed":
                errors.append(f"{key} cannot already be passed at stage {stage}")

        for index, key in enumerate(GATE_KEYS, start=1):
            status = gates[key]
            evidence = _section(body, f"### Gate {index}")
            if status in {"passed", "blocked", "invalidated"}:
                if not evidence or evidence.casefold() in {"not evaluated.", "not evaluated"}:
                    errors.append(f"{key} status {status} requires recorded evidence or a reason")

    expected_ready = stage == "READY_FOR_IMPLEMENTATION"
    if isinstance(data["ready_for_implementation"], bool) and data["ready_for_implementation"] != expected_ready:
        errors.append(
            "ready_for_implementation must be true if and only if current_stage is READY_FOR_IMPLEMENTATION"
        )

    if stage in ALLOWED_STAGES and isinstance(artifacts, dict):
        for key in REQUIRED_ARTIFACTS[stage]:
            if artifacts.get(key) is None:
                errors.append(f"artifact {key} is required at stage {stage}")

    if isinstance(artifacts, dict):
        anchors = _anchors(body)
        for key, pointer in artifacts.items():
            if not isinstance(pointer, str) or not pointer:
                continue
            if pointer.startswith("inline:#"):
                anchor = pointer.removeprefix("inline:#")
                if anchor not in anchors:
                    errors.append(f"artifact {key} points to missing inline anchor: {anchor}")
                if key == "idea":
                    idea = _section(body, "## Original Idea")
                    if not idea or idea.casefold() in {"not captured.", "not captured"}:
                        errors.append("inline idea pointer requires captured Original Idea content")
                continue
            local, pointer_error = _resolve_local_pointer(pointer, repo_root)
            if pointer_error:
                errors.append(f"artifact {key}: {pointer_error}")
            elif local is not None and not local.exists():
                errors.append(f"artifact {key} points to missing local target: {pointer}")

    return errors


def validate_path(state_path: Path, repo_root: Path | None = None) -> tuple[list[str], dict[str, Any]]:
    state_path = state_path.resolve()
    if repo_root is None:
        repo_root = state_path.parent.parent if state_path.parent.name == ".project" else state_path.parent
    try:
        text = state_path.read_text(encoding="utf-8")
        data, body = split_state(text)
    except (OSError, UnicodeError, ParseError) as exc:
        return [str(exc)], {}
    return validate_state(data, body, repo_root), data


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
    args = parser.parse_args(argv)

    path = Path(args.state_file)
    errors, data = validate_path(path, args.repo_root)
    if errors:
        print(f"INVALID: {path}", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"VALID: {path} ({data['current_stage']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
