"""Canonical finite contract for Project Preflight state and routing."""

from __future__ import annotations

from dataclasses import dataclass


SCHEMA_VERSION = 1
GATE_KEYS = ("gate_1", "gate_2", "gate_3", "gate_4")
GATE_STATUSES = {"not_evaluated", "blocked", "passed", "invalidated"}
ARTIFACT_KEYS = ("idea", "decision_map", "spec", "tickets")
DEPENDENCY_KEYS = ("grill-me", "wayfinder", "to-spec", "to-tickets")
DEPENDENCY_STATUSES = {"available", "missing", "not_checked"}


@dataclass(frozen=True)
class StageContract:
    name: str
    passed_gates: int
    required_artifacts: tuple[str, ...]
    handoff_skill: str | None


STAGE_CONTRACTS = (
    StageContract("IDEA", 0, (), None),
    StageContract("DISCOVERY", 0, ("idea",), "grill-me"),
    StageContract("DECISION", 1, ("idea",), "wayfinder"),
    StageContract("SPECIFICATION", 2, ("idea", "decision_map"), "to-spec"),
    StageContract("TICKETING", 3, ("idea", "decision_map", "spec"), "to-tickets"),
    StageContract("READY_FOR_IMPLEMENTATION", 4, ARTIFACT_KEYS, None),
)
STAGES_BY_NAME = {contract.name: contract for contract in STAGE_CONTRACTS}
ALLOWED_STAGES = tuple(STAGES_BY_NAME)
DIRECT_DEPENDENCIES = {
    contract.name: contract.handoff_skill
    for contract in STAGE_CONTRACTS
    if contract.handoff_skill is not None
}

FORWARD_TRANSITIONS = (
    ("IDEA", "DISCOVERY"),
    ("DISCOVERY", "DECISION"),
    ("DECISION", "SPECIFICATION"),
    ("SPECIFICATION", "TICKETING"),
    ("TICKETING", "READY_FOR_IMPLEMENTATION"),
)
REGRESSION_TARGETS = {
    "DECISION": ("DISCOVERY",),
    "SPECIFICATION": ("DECISION", "DISCOVERY"),
    "TICKETING": ("SPECIFICATION", "DECISION", "DISCOVERY"),
    "READY_FOR_IMPLEMENTATION": (
        "TICKETING",
        "SPECIFICATION",
        "DECISION",
        "DISCOVERY",
    ),
}
REGRESSION_TRANSITIONS = tuple(
    (source, target)
    for source, targets in REGRESSION_TARGETS.items()
    for target in targets
)
ALLOWED_TRANSITIONS = frozenset(FORWARD_TRANSITIONS + REGRESSION_TRANSITIONS)

TOP_LEVEL_ORDER = (
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
)
TOP_LEVEL_KEYS = frozenset(TOP_LEVEL_ORDER)
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

HANDOFF_PURPOSES = {
    "DISCOVERY": (
        "clarify the target user, problem, value, inputs, outputs, MVP, non-goals, "
        "measurable success criteria, material assumptions, and whether an agent is required"
    ),
    "DECISION": (
        "resolve architecture-reversing unknowns and produce or identify the canonical decision map"
    ),
    "SPECIFICATION": (
        "synthesize the approved scope and decisions into the canonical specification without reopening discovery"
    ),
    "TICKETING": (
        "turn the canonical specification into narrow tracer-bullet tickets with explicit blockers and verification"
    ),
}


def transition_gate(source: str, target: str) -> str | None:
    """Return the gate passed by a forward transition, if any."""

    pair = (source, target)
    if pair not in FORWARD_TRANSITIONS or source == "IDEA":
        return None
    return GATE_KEYS[STAGES_BY_NAME[source].passed_gates]


def invalidated_gates(target: str) -> tuple[str, ...]:
    """Return every gate made non-authoritative by regression to target."""

    passed = STAGES_BY_NAME[target].passed_gates
    return GATE_KEYS[passed:]


def handoff_text(stage: str, project: str) -> str | None:
    """Build the exact user-invoked handoff and return instruction for a Stage."""

    skill = DIRECT_DEPENDENCIES.get(stage)
    if skill is None:
        return None
    purpose = HANDOFF_PURPOSES[stage]
    return (
        f"Use ${skill} for project {project!r} to {purpose}. "
        "Do not implement production code. When the durable result is saved or linked, stop that Skill and then run: "
        f"Use $project-preflight to resume project {project!r} and evaluate the current gate."
    )
