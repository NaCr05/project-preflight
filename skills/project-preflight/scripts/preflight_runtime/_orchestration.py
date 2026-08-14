"""Stage routing and user-visible Skill transparency for Project Preflight."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping

from ._contract import DIRECT_DEPENDENCIES, STAGE_ADAPTERS, STAGE_PURPOSES


@dataclass(frozen=True)
class OrchestrationDirective:
    """One authoritative instruction for the conversational orchestrator."""

    kind: str
    stage: str
    display_skill: str | None
    adapter_skill: str | None
    announcement: str
    instruction: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def directive_for_state(data: Mapping[str, Any]) -> OrchestrationDirective:
    """Derive the next conversational action from validated state."""

    stage = str(data["current_stage"])
    if stage == "IDEA":
        return OrchestrationDirective(
            kind="CAPTURE_IDEA",
            stage=stage,
            display_skill=None,
            adapter_skill=None,
            announcement="Project Preflight · Idea — 正在记录你的初步想法。你只需用一段话描述它。",
            instruction="Capture the user's rough idea, initialize durable state, and continue to DISCOVERY.",
        )
    if stage == "READY_FOR_IMPLEMENTATION":
        return OrchestrationDirective(
            kind="READY",
            stage=stage,
            display_skill=None,
            adapter_skill=None,
            announcement="Project Preflight · Ready — 四道 Gate 已通过，正在整理实施交接。",
            instruction="Present the canonical spec, ticket set, first tracer bullet, verification, and residual risks; then stop.",
        )

    display_skill = DIRECT_DEPENDENCIES[stage]
    adapter_skill = STAGE_ADAPTERS[stage]
    status = data.get("dependencies", {}).get(display_skill, "not_checked")
    if status == "missing":
        return OrchestrationDirective(
            kind="BLOCKED",
            stage=stage,
            display_skill=display_skill,
            adapter_skill=adapter_skill,
            announcement=f"Project Preflight · {stage.title()} — `{display_skill}` 阶段适配器当前不可用。",
            instruction="Keep the current Stage, record the blocker, and explain how to restore the bundled adapter.",
        )

    purpose = STAGE_PURPOSES[stage]
    return OrchestrationDirective(
        kind="RUN_STAGE_ADAPTER",
        stage=stage,
        display_skill=display_skill,
        adapter_skill=adapter_skill,
        announcement=(
            f"Project Preflight · {stage.title()} — 正在使用 `{display_skill}`"
            "（Project Preflight 内置适配器）。你只需回答或确认。"
        ),
        instruction=(
            f"Load and follow the bundled `${adapter_skill}` Skill to {purpose}. "
            "Do not ask the user to invoke or paste another Skill command. After its durable artifact is saved, "
            "return control to Project Preflight in the same task, evaluate the Gate, persist the transition, and continue."
        ),
    )
