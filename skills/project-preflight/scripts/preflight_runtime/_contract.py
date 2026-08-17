"""Canonical finite contract for Project Preflight state and routing."""

from __future__ import annotations

from dataclasses import dataclass


SCHEMA_VERSION = 1
GATE_KEYS = ("gate_1", "gate_2", "gate_3", "gate_4")
GATE_STATUSES = {"not_evaluated", "blocked", "passed", "invalidated"}
ARTIFACT_KEYS = ("idea", "decision_map", "spec", "tickets")
DEPENDENCY_KEYS = ("grill-me", "wayfinder", "to-spec", "to-tickets")
DEPENDENCY_STATUSES = {"available", "missing", "not_checked"}
OUTCOME_BEHAVIORS = {
    "recorded": (
        "Durable observations changed but no Gate was judged",
        "Preserve the Stage, persist updates, derive the directive",
    ),
    "gate_passed": (
        "The current Stage's Gate has sufficient evidence",
        "Derive the current Gate and next Stage, advance once",
    ),
    "gate_blocked": (
        "The current Stage's Gate lacks required evidence",
        "Derive and block the current Gate without advancing",
    ),
    "evidence_invalidated": (
        "Canonical artifact authority was contradicted",
        "Derive the earliest affected Stage from artifact ownership and invalidate later Gates",
    ),
}
OUTCOME_VERDICTS = tuple(OUTCOME_BEHAVIORS)
ARTIFACT_STAGES = {
    "idea": "DISCOVERY",
    "decision_map": "DECISION",
    "spec": "SPECIFICATION",
    "tickets": "TICKETING",
}


@dataclass(frozen=True)
class StageContract:
    name: str
    passed_gates: int
    required_artifacts: tuple[str, ...]
    display_skill: str | None
    adapter_skill: str | None
    durable_result: str


STAGE_CONTRACTS = (
    StageContract("IDEA", 0, (), None, None, "Rough idea captured"),
    StageContract(
        "DISCOVERY",
        0,
        ("idea",),
        "grill-me",
        "project-preflight-grill-me",
        "Canonical idea/discovery evidence",
    ),
    StageContract(
        "DECISION",
        1,
        ("idea",),
        "wayfinder",
        "project-preflight-wayfinder",
        "Decision map",
    ),
    StageContract(
        "SPECIFICATION",
        2,
        ("idea", "decision_map"),
        "to-spec",
        "project-preflight-to-spec",
        "Canonical specification",
    ),
    StageContract(
        "TICKETING",
        3,
        ("idea", "decision_map", "spec"),
        "to-tickets",
        "project-preflight-to-tickets",
        "Ticket frontier",
    ),
    StageContract(
        "READY_FOR_IMPLEMENTATION",
        4,
        ARTIFACT_KEYS,
        None,
        None,
        "Implementation handoff",
    ),
)
STAGES_BY_NAME = {contract.name: contract for contract in STAGE_CONTRACTS}
ALLOWED_STAGES = tuple(STAGES_BY_NAME)
DIRECT_DEPENDENCIES = {
    contract.name: contract.display_skill
    for contract in STAGE_CONTRACTS
    if contract.display_skill is not None
}
STAGE_ADAPTERS = {
    contract.name: contract.adapter_skill
    for contract in STAGE_CONTRACTS
    if contract.adapter_skill is not None
}

FORWARD_TRANSITIONS = (
    ("IDEA", "DISCOVERY"),
    ("DISCOVERY", "DECISION"),
    ("DECISION", "SPECIFICATION"),
    ("SPECIFICATION", "TICKETING"),
    ("TICKETING", "READY_FOR_IMPLEMENTATION"),
)
FORWARD_TARGETS = dict(FORWARD_TRANSITIONS)
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

STAGE_PURPOSES = {
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


def next_action_text(stage: str) -> str:
    """Render the durable next action without asking the user to invoke another Skill."""

    skill = DIRECT_DEPENDENCIES.get(stage)
    if skill is None:
        if stage == "IDEA":
            return "Capture the original project idea, then continue automatically to `DISCOVERY`."
        return "Preflight is complete; present the implementation handoff and stop."
    return (
        f"Continue the active Project Preflight session automatically with `{skill}`. "
        "The user only needs to answer or confirm; do not ask them to invoke another Skill."
    )
