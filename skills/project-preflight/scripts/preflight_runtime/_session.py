"""Outcome-oriented Project Preflight session module."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any, Callable, Mapping

from ._contract import (
    ARTIFACT_KEYS,
    ARTIFACT_STAGES,
    DEPENDENCY_KEYS,
    DEPENDENCY_STATUSES,
    DIRECT_DEPENDENCIES,
    FORWARD_TARGETS,
    OUTCOME_VERDICTS,
    STAGES_BY_NAME,
    invalidated_gates,
    next_action_text,
    transition_gate,
)
from ._lifecycle import (
    StateChange,
    StateOperationError,
    StateStore,
    ValidationReport,
)
from ._orchestration import OrchestrationDirective, directive_for_state


@dataclass(frozen=True)
class StageOutcome:
    """One Stage result without caller-selected Stage, Gate, or transition commands."""

    verdict: str
    reason: str
    evidence: str | None = None
    artifacts: Mapping[str, str | None] = field(default_factory=dict)
    dependencies: Mapping[str, str] = field(default_factory=dict)
    invalidated_artifacts: tuple[str, ...] = ()
    original_idea: str | None = None
    blockers: str | None = None
    next_action: str | None = None

    def __post_init__(self) -> None:
        if self.verdict not in OUTCOME_VERDICTS:
            raise ValueError(
                f"verdict must be one of {', '.join(OUTCOME_VERDICTS)}: {self.verdict!r}"
            )
        if not isinstance(self.reason, str) or not self.reason.strip():
            raise ValueError("StageOutcome reason must be a non-empty string")

        artifacts = dict(self.artifacts)
        dependencies = dict(self.dependencies)
        invalidated = tuple(dict.fromkeys(self.invalidated_artifacts))
        object.__setattr__(self, "artifacts", MappingProxyType(artifacts))
        object.__setattr__(self, "dependencies", MappingProxyType(dependencies))
        object.__setattr__(self, "invalidated_artifacts", invalidated)

        for key, value in artifacts.items():
            if key not in ARTIFACT_KEYS:
                raise ValueError(f"unknown artifact key: {key}")
            if value is not None and (not isinstance(value, str) or not value.strip()):
                raise ValueError(f"artifact {key} must be null or a non-empty string")
        for key, value in dependencies.items():
            if key not in DEPENDENCY_KEYS:
                raise ValueError(f"unknown dependency key: {key}")
            if value not in DEPENDENCY_STATUSES:
                raise ValueError(f"invalid dependency status for {key}: {value}")
        for key in invalidated:
            if key not in ARTIFACT_STAGES:
                raise ValueError(f"unknown invalidated artifact: {key}")

        gate_verdicts = {"gate_passed", "gate_blocked", "evidence_invalidated"}
        if self.verdict in gate_verdicts and (
            not isinstance(self.evidence, str) or not self.evidence.strip()
        ):
            raise ValueError(f"{self.verdict} requires non-empty evidence")
        if self.verdict == "evidence_invalidated" and not invalidated:
            raise ValueError("evidence_invalidated requires at least one invalidated artifact")
        if self.verdict != "evidence_invalidated" and invalidated:
            raise ValueError("invalidated_artifacts are allowed only for evidence_invalidated")
        if self.verdict == "recorded" and self.evidence is not None:
            raise ValueError("recorded outcomes do not update Gate evidence")
        if self.verdict == "recorded" and not any(
            (
                artifacts,
                dependencies,
                self.original_idea is not None,
                self.blockers is not None,
                self.next_action is not None,
            )
        ):
            raise ValueError("recorded outcomes require at least one durable state update")

        for field_name in ("original_idea", "blockers", "next_action"):
            value = getattr(self, field_name)
            if value is not None and (not isinstance(value, str) or not value.strip()):
                raise ValueError(f"{field_name} must be null or a non-empty string")

    @classmethod
    def record(cls, reason: str, **updates: Any) -> "StageOutcome":
        return cls("recorded", reason, **updates)

    @classmethod
    def pass_gate(cls, reason: str, evidence: str, **updates: Any) -> "StageOutcome":
        return cls("gate_passed", reason, evidence=evidence, **updates)

    @classmethod
    def block_gate(cls, reason: str, evidence: str, **updates: Any) -> "StageOutcome":
        return cls("gate_blocked", reason, evidence=evidence, **updates)

    @classmethod
    def invalidate(
        cls,
        reason: str,
        evidence: str,
        *,
        invalidated_artifacts: tuple[str, ...],
        **updates: Any,
    ) -> "StageOutcome":
        return cls(
            "evidence_invalidated",
            reason,
            evidence=evidence,
            invalidated_artifacts=invalidated_artifacts,
            **updates,
        )


@dataclass(frozen=True)
class SessionResult:
    """Validated state and the one directive derived from it."""

    state: ValidationReport
    directive: OrchestrationDirective

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": {
                "valid": self.state.valid,
                "errors": list(self.state.errors),
                "warnings": list(self.state.warnings),
                "data": self.state.data,
            },
            "directive": self.directive.to_dict(),
        }


class PreflightSession:
    """Deep session Interface owning outcome interpretation through the next directive."""

    def __init__(
        self,
        state_path: Path | str = Path(".project/preflight.md"),
        repo_root: Path | str | None = None,
        clock: Callable[[], Any] | None = None,
    ) -> None:
        self._store = StateStore(state_path, repo_root, clock=clock)

    @property
    def path(self) -> Path:
        return self._store.path

    def start(
        self,
        project: str,
        original_idea: str | None = None,
        *,
        locale: str | None = None,
    ) -> SessionResult:
        report = self._store.initialize(project, original_idea)
        return self._result(report, locale)

    def current(
        self,
        *,
        locale: str | None = None,
        check_remote: bool = False,
    ) -> SessionResult:
        report = self._store.validate(check_remote=check_remote)
        if not report.valid:
            raise StateOperationError("existing state is invalid", report.errors)
        return self._result(report, locale)

    def apply(self, outcome: StageOutcome, *, locale: str | None = None) -> SessionResult:
        current = self.current(locale=locale).state
        stage = str(current.data["current_stage"])
        change = self._change(outcome)

        if outcome.verdict == "recorded":
            active_dependency = DIRECT_DEPENDENCIES.get(stage)
            if active_dependency and outcome.dependencies.get(active_dependency) == "missing":
                change = StateChange(
                    artifacts=change.artifacts,
                    dependencies=change.dependencies,
                    original_idea=change.original_idea,
                    blockers=change.blockers or outcome.reason,
                    next_action=change.next_action
                    or f"Restore the bundled `{active_dependency}` Adapter, then resume Project Preflight.",
                )
            report = self._store.record(change)
        elif outcome.verdict == "gate_passed":
            target = FORWARD_TARGETS.get(stage)
            if target is None or stage == "IDEA":
                raise StateOperationError(f"Stage {stage} has no Gate that can advance")
            gate = transition_gate(stage, target)
            if gate is None:
                raise StateOperationError(f"Stage {stage} does not own a readiness Gate")
            report = self._store.advance(
                target,
                outcome.reason,
                self._with_gate_evidence(
                    change,
                    gate,
                    outcome.evidence,
                    default_blockers="None recorded.",
                ),
            )
        elif outcome.verdict == "gate_blocked":
            target = FORWARD_TARGETS.get(stage)
            if target is None or stage == "IDEA":
                raise StateOperationError(f"Stage {stage} has no Gate that can be blocked")
            gate = transition_gate(stage, target)
            if gate is None:
                raise StateOperationError(f"Stage {stage} does not own a readiness Gate")
            report = self._store.record(
                StateChange(
                    artifacts=change.artifacts,
                    dependencies=change.dependencies,
                    gate_statuses={gate: "blocked"},
                    gate_evidence={gate: outcome.evidence or outcome.reason},
                    original_idea=change.original_idea,
                    blockers=change.blockers or outcome.reason,
                    next_action=change.next_action
                    or f"Resolve the recorded {stage.title()} blocker, then resume Project Preflight.",
                )
            )
        else:
            target = self._invalidation_target(outcome.invalidated_artifacts)
            current_rank = STAGES_BY_NAME[stage].passed_gates
            target_rank = STAGES_BY_NAME[target].passed_gates
            if target_rank > current_rank:
                raise StateOperationError(
                    f"artifact evidence for {target} is not authoritative at current Stage {stage}"
                )
            if target == stage:
                target_forward = FORWARD_TARGETS.get(stage)
                gate = transition_gate(stage, target_forward) if target_forward else None
                if gate is None:
                    raise StateOperationError(f"Stage {stage} has no Gate to invalidate")
                report = self._store.record(
                    StateChange(
                        artifacts=change.artifacts,
                        dependencies=change.dependencies,
                        gate_statuses={gate: "invalidated"},
                        gate_evidence={gate: outcome.evidence or outcome.reason},
                        original_idea=change.original_idea,
                        blockers=change.blockers or outcome.reason,
                        next_action=change.next_action or next_action_text(stage),
                    )
                )
            else:
                report = self._store.regress(
                    target,
                    outcome.reason,
                    StateChange(
                        artifacts=change.artifacts,
                        dependencies=change.dependencies,
                        original_idea=change.original_idea,
                        blockers=change.blockers or outcome.reason,
                        next_action=change.next_action,
                        gate_evidence={
                            gate: outcome.evidence or outcome.reason
                            for gate in invalidated_gates(target)
                        },
                    ),
                )
        return self._result(report, locale)

    def recover(
        self,
        valid_source: Path | str,
        *,
        locale: str | None = None,
    ) -> SessionResult:
        return self._result(self._store.recover(valid_source), locale)

    @staticmethod
    def _change(outcome: StageOutcome) -> StateChange:
        return StateChange(
            artifacts=outcome.artifacts,
            dependencies=outcome.dependencies,
            original_idea=outcome.original_idea,
            blockers=outcome.blockers,
            next_action=outcome.next_action,
        )

    @staticmethod
    def _with_gate_evidence(
        change: StateChange,
        gate: str,
        evidence: str | None,
        default_blockers: str | None = None,
    ) -> StateChange:
        return StateChange(
            artifacts=change.artifacts,
            dependencies=change.dependencies,
            gate_evidence={gate: evidence or "Evidence recorded by the active Stage Adapter."},
            original_idea=change.original_idea,
            blockers=change.blockers if change.blockers is not None else default_blockers,
            next_action=change.next_action,
        )

    @staticmethod
    def _invalidation_target(invalidated_artifacts: tuple[str, ...]) -> str:
        return min(
            (ARTIFACT_STAGES[key] for key in invalidated_artifacts),
            key=lambda stage: STAGES_BY_NAME[stage].passed_gates,
        )

    @staticmethod
    def _result(report: ValidationReport, locale: str | None) -> SessionResult:
        return SessionResult(report, directive_for_state(report.data, locale=locale))
