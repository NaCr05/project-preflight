"""Stage routing and user-visible Skill transparency for Project Preflight."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping

from ._contract import DIRECT_DEPENDENCIES, STAGE_ADAPTERS, STAGE_PURPOSES
from ._messages import message


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


def directive_for_state(
    data: Mapping[str, Any], locale: str | None = None
) -> OrchestrationDirective:
    """Derive the next conversational action from validated state."""

    stage = str(data["current_stage"])
    if stage == "IDEA":
        return OrchestrationDirective(
            kind="CAPTURE_IDEA",
            stage=stage,
            display_skill=None,
            adapter_skill=None,
            announcement=message(locale, "idea"),
            instruction="Capture the user's rough idea, initialize durable state, and continue to DISCOVERY.",
        )
    if stage == "READY_FOR_IMPLEMENTATION":
        return OrchestrationDirective(
            kind="READY",
            stage=stage,
            display_skill=None,
            adapter_skill=None,
            announcement=message(locale, "ready"),
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
            announcement=message(
                locale,
                "blocked",
                stage=stage.title(),
                skill=display_skill,
            ),
            instruction="Keep the current Stage, record the blocker, and explain how to restore the bundled adapter.",
        )

    purpose = STAGE_PURPOSES[stage]
    return OrchestrationDirective(
        kind="RUN_STAGE_ADAPTER",
        stage=stage,
        display_skill=display_skill,
        adapter_skill=adapter_skill,
        announcement=message(
            locale,
            "running",
            stage=stage.title(),
            skill=display_skill,
        ),
        instruction=(
            f"Load and follow the bundled `${adapter_skill}` Skill to {purpose}. "
            "Do not ask the user to invoke or paste another Skill command. After its durable artifact is saved, "
            "return control to Project Preflight in the same task and submit one semantic StageOutcome. "
            "PreflightSession derives and persists any Gate transition and returns the next directive."
        ),
    )
