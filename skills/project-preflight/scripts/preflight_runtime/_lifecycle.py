"""Deep State lifecycle module for Project Preflight."""

from __future__ import annotations

import copy
import os
import re
import tempfile
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ._contract import (
    ALLOWED_STAGES,
    ALLOWED_TRANSITIONS,
    ARTIFACT_KEYS,
    DEPENDENCY_KEYS,
    DEPENDENCY_STATUSES,
    FORWARD_TRANSITIONS,
    GATE_KEYS,
    GATE_STATUSES,
    REQUIRED_HEADINGS,
    SCHEMA_VERSION,
    STAGES_BY_NAME,
    TOP_LEVEL_KEYS,
    handoff_text,
    invalidated_gates,
    transition_gate,
)
from ._document import ParseError, render_state, replace_section, section, split_state
from ._evidence import ArtifactEvidenceChecker


@dataclass(frozen=True)
class ValidationReport:
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    data: dict[str, Any]

    @property
    def valid(self) -> bool:
        return not self.errors


@dataclass(frozen=True)
class StateChange:
    artifacts: Mapping[str, str | None] = field(default_factory=dict)
    dependencies: Mapping[str, str] = field(default_factory=dict)
    gate_statuses: Mapping[str, str] = field(default_factory=dict)
    gate_evidence: Mapping[str, str] = field(default_factory=dict)
    original_idea: str | None = None
    blockers: str | None = None
    next_action: str | None = None


class StateOperationError(RuntimeError):
    """Raised before an invalid candidate can replace the last valid state."""

    def __init__(self, message: str, errors: tuple[str, ...] = ()) -> None:
        super().__init__(message)
        self.errors = errors


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


def _validate_data(
    data: dict[str, Any],
    body: str,
    repo_root: Path,
    check_remote: bool,
    evidence_checker: ArtifactEvidenceChecker | None = None,
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    missing = sorted(TOP_LEVEL_KEYS - data.keys())
    unknown = sorted(data.keys() - TOP_LEVEL_KEYS)
    if missing:
        errors.append(f"missing top-level keys: {', '.join(missing)}")
    if unknown:
        errors.append(f"unknown top-level keys: {', '.join(unknown)}")
    if missing:
        return errors, warnings

    if data["schema_version"] != SCHEMA_VERSION:
        errors.append(f"schema_version must be integer {SCHEMA_VERSION}")
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

    dependencies = data["dependencies"]
    if not isinstance(dependencies, dict):
        errors.append("dependencies must be a mapping")
    else:
        if set(dependencies) != set(DEPENDENCY_KEYS):
            errors.append(
                "dependencies must contain exactly grill-me, wayfinder, to-spec, and to-tickets"
            )
        for key, value in dependencies.items():
            if value not in DEPENDENCY_STATUSES:
                errors.append(f"dependency {key} has invalid status: {value!r}")

    for heading in REQUIRED_HEADINGS:
        if not re.search(rf"(?m)^{re.escape(heading)}[ \t]*$", body):
            errors.append(f"missing Markdown heading: {heading}")

    if stage in ALLOWED_STAGES and isinstance(gates, dict) and set(gates) == set(GATE_KEYS):
        passed_count = STAGES_BY_NAME[stage].passed_gates
        for index, key in enumerate(GATE_KEYS, start=1):
            status = gates[key]
            if index <= passed_count and status != "passed":
                errors.append(f"{key} must be passed at stage {stage}")
            if index > passed_count and status == "passed":
                errors.append(f"{key} cannot already be passed at stage {stage}")
            evidence = section(body, f"### Gate {index}")
            if status in {"passed", "blocked", "invalidated"}:
                if not evidence or evidence.casefold() in {"not evaluated.", "not evaluated"}:
                    errors.append(f"{key} status {status} requires recorded evidence or a reason")

    expected_ready = stage == "READY_FOR_IMPLEMENTATION"
    if (
        isinstance(data["ready_for_implementation"], bool)
        and data["ready_for_implementation"] != expected_ready
    ):
        errors.append(
            "ready_for_implementation must be true if and only if current_stage is READY_FOR_IMPLEMENTATION"
        )

    if stage in ALLOWED_STAGES and isinstance(artifacts, dict):
        for key in STAGES_BY_NAME[stage].required_artifacts:
            if artifacts.get(key) is None:
                errors.append(f"artifact {key} is required at stage {stage}")

    if isinstance(artifacts, dict):
        checker = evidence_checker or ArtifactEvidenceChecker()
        for key, pointer in artifacts.items():
            if not isinstance(pointer, str) or not pointer:
                continue
            findings = checker.check(key, pointer, body, repo_root, check_remote)
            errors.extend(findings.errors)
            warnings.extend(findings.warnings)
    return errors, warnings


def _inspect_text(
    text: str,
    repo_root: Path,
    check_remote: bool = False,
    evidence_checker: ArtifactEvidenceChecker | None = None,
) -> ValidationReport:
    try:
        data, body = split_state(text)
    except (UnicodeError, ParseError) as exc:
        return ValidationReport((str(exc),), (), {})
    errors, warnings = _validate_data(
        data, body, repo_root, check_remote, evidence_checker=evidence_checker
    )
    return ValidationReport(tuple(errors), tuple(warnings), data)


def inspect_path(
    state_path: Path,
    repo_root: Path | None = None,
    check_remote: bool = False,
) -> ValidationReport:
    state_path = state_path.resolve()
    if repo_root is None:
        repo_root = state_path.parent.parent if state_path.parent.name == ".project" else state_path.parent
    try:
        text = state_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return ValidationReport((str(exc),), (), {})
    return _inspect_text(text, repo_root.resolve(), check_remote)


def validate_path(
    state_path: Path,
    repo_root: Path | None = None,
) -> tuple[list[str], dict[str, Any]]:
    """Compatibility interface retained for existing callers."""

    report = inspect_path(state_path, repo_root)
    return list(report.errors), report.data


def _initial_data(project: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "project": project,
        "current_stage": "IDEA",
        "previous_stage": None,
        "last_transition": None,
        "transition_reason": "Initial preflight state",
        "tracker": "local-markdown",
        "ready_for_implementation": False,
        "gates": {key: "not_evaluated" for key in GATE_KEYS},
        "artifacts": {key: None for key in ARTIFACT_KEYS},
        "dependencies": {key: "not_checked" for key in DEPENDENCY_KEYS},
    }


def _initial_body() -> str:
    return """# Project Preflight

## Original Idea

Not captured.

## Gate Evidence

### Gate 1

Not evaluated.

### Gate 2

Not evaluated.

### Gate 3

Not evaluated.

### Gate 4

Not evaluated.

## Blockers

None recorded.

## Next Action

Capture the original project idea and move to `DISCOVERY`."""


def render_initial_state(project: str = "unnamed-project") -> str:
    """Render the derived initial-state asset from the canonical contract."""

    return render_state(_initial_data(project), _initial_body())


def handoff_for_stage(stage: str, project: str) -> str | None:
    if stage not in ALLOWED_STAGES:
        raise StateOperationError(f"unknown Stage: {stage}")
    return handoff_text(stage, project)


class StateStore:
    """Small interface hiding parsing, transitions, validation, persistence, and recovery."""

    def __init__(
        self,
        state_path: Path | str = Path(".project/preflight.md"),
        repo_root: Path | str | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.path = Path(state_path).resolve()
        if repo_root is None:
            repo_root = self.path.parent.parent if self.path.parent.name == ".project" else self.path.parent
        self.repo_root = Path(repo_root).resolve()
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def validate(self, check_remote: bool = False) -> ValidationReport:
        return inspect_path(self.path, self.repo_root, check_remote)

    def initialize(self, project: str, original_idea: str | None = None) -> ValidationReport:
        if self.path.exists():
            raise StateOperationError(f"state already exists: {self.path}")
        data = _initial_data(project)
        body = _initial_body()
        if original_idea is not None:
            change = StateChange(original_idea=original_idea)
            data, body = self._apply_change(data, body, change)
            data["previous_stage"] = "IDEA"
            data["current_stage"] = "DISCOVERY"
            data["last_transition"] = self._timestamp()
            data["transition_reason"] = "Captured the original idea"
            data["artifacts"]["idea"] = "inline:#original-idea"
            body = replace_section(body, "## Next Action", handoff_text("DISCOVERY", project) or "")
        return self._commit(data, body)

    def record(self, change: StateChange) -> ValidationReport:
        data, body = self._load_valid()
        data, body = self._apply_change(data, body, change)
        return self._commit(data, body)

    def advance(
        self,
        target_stage: str,
        reason: str,
        change: StateChange = StateChange(),
    ) -> ValidationReport:
        data, body = self._load_valid()
        source = data["current_stage"]
        if (source, target_stage) not in FORWARD_TRANSITIONS:
            raise StateOperationError(f"illegal forward transition: {source} -> {target_stage}")
        data, body = self._apply_change(data, body, change)
        gate = transition_gate(source, target_stage)
        if gate is not None:
            evidence = change.gate_evidence.get(gate)
            if not evidence:
                raise StateOperationError(f"{gate} evidence is required to advance to {target_stage}")
            data["gates"][gate] = "passed"
            body = replace_section(body, f"### Gate {GATE_KEYS.index(gate) + 1}", evidence)
        data["previous_stage"] = source
        data["current_stage"] = target_stage
        data["last_transition"] = self._timestamp()
        data["transition_reason"] = reason
        data["ready_for_implementation"] = target_stage == "READY_FOR_IMPLEMENTATION"
        if change.next_action is None:
            default_next = handoff_text(target_stage, data["project"])
            if default_next is not None:
                body = replace_section(body, "## Next Action", default_next)
        return self._commit(data, body)

    def regress(
        self,
        target_stage: str,
        reason: str,
        change: StateChange = StateChange(),
    ) -> ValidationReport:
        data, body = self._load_valid()
        source = data["current_stage"]
        if (source, target_stage) not in ALLOWED_TRANSITIONS or (source, target_stage) in FORWARD_TRANSITIONS:
            raise StateOperationError(f"illegal regression: {source} -> {target_stage}")
        data, body = self._apply_change(data, body, change)
        for gate in invalidated_gates(target_stage):
            data["gates"][gate] = "invalidated"
            evidence = change.gate_evidence.get(gate, reason)
            body = replace_section(body, f"### Gate {GATE_KEYS.index(gate) + 1}", evidence)
        data["previous_stage"] = source
        data["current_stage"] = target_stage
        data["last_transition"] = self._timestamp()
        data["transition_reason"] = reason
        data["ready_for_implementation"] = False
        if change.next_action is None:
            body = replace_section(
                body,
                "## Next Action",
                handoff_text(target_stage, data["project"]) or "Re-evaluate the invalidated evidence.",
            )
        return self._commit(data, body)

    def recover(self, valid_source: Path | str) -> ValidationReport:
        """Atomically restore an explicitly supplied valid state document."""

        source = Path(valid_source).resolve()
        try:
            text = source.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise StateOperationError(f"recovery source cannot be read: {exc}") from exc
        report = _inspect_text(text, self.repo_root)
        if not report.valid:
            raise StateOperationError("recovery source is invalid", report.errors)
        data, body = split_state(text)
        return self._commit(data, body)

    def handoff(self) -> str | None:
        data, _ = self._load_valid()
        return handoff_text(data["current_stage"], data["project"])

    def _load_valid(self) -> tuple[dict[str, Any], str]:
        try:
            text = self.path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise StateOperationError(f"state cannot be read: {exc}") from exc
        report = _inspect_text(text, self.repo_root)
        if not report.valid:
            raise StateOperationError("existing state is invalid", report.errors)
        data, body = split_state(text)
        return copy.deepcopy(data), body

    def _apply_change(
        self,
        data: dict[str, Any],
        body: str,
        change: StateChange,
    ) -> tuple[dict[str, Any], str]:
        for key, value in change.artifacts.items():
            if key not in ARTIFACT_KEYS:
                raise StateOperationError(f"unknown artifact key: {key}")
            data["artifacts"][key] = value
        for key, value in change.dependencies.items():
            if key not in DEPENDENCY_KEYS:
                raise StateOperationError(f"unknown dependency key: {key}")
            if value not in DEPENDENCY_STATUSES:
                raise StateOperationError(f"invalid dependency status for {key}: {value}")
            data["dependencies"][key] = value
        for key, value in change.gate_statuses.items():
            if key not in GATE_KEYS or value not in GATE_STATUSES:
                raise StateOperationError(f"invalid gate update: {key}={value}")
            data["gates"][key] = value
        for key, evidence in change.gate_evidence.items():
            if key not in GATE_KEYS:
                raise StateOperationError(f"unknown gate evidence key: {key}")
            body = replace_section(body, f"### Gate {GATE_KEYS.index(key) + 1}", evidence)
        if change.original_idea is not None:
            body = replace_section(body, "## Original Idea", change.original_idea)
        if change.blockers is not None:
            body = replace_section(body, "## Blockers", change.blockers)
        if change.next_action is not None:
            body = replace_section(body, "## Next Action", change.next_action)
        return data, body

    def _commit(self, data: dict[str, Any], body: str) -> ValidationReport:
        text = render_state(data, body)
        report = _inspect_text(text, self.repo_root)
        if not report.valid:
            raise StateOperationError(
                "candidate state is invalid; the last valid state was left unchanged",
                report.errors,
            )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temp_name = tempfile.mkstemp(
            prefix=f".{self.path.name}.", suffix=".tmp", dir=self.path.parent
        )
        temp_path = Path(temp_name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(text)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_path, self.path)
        except Exception:
            temp_path.unlink(missing_ok=True)
            raise
        return report

    def _timestamp(self) -> str:
        value = self._clock().astimezone(timezone.utc).isoformat(timespec="seconds")
        return value.replace("+00:00", "Z")
