---
name: project-preflight
description: Orchestrate the pre-coding lifecycle for a new or existing software project, especially an AI or agent project. Use when a user has a vague project idea, wants to resume interrupted planning, needs to determine whether a project is ready to implement, or already has decisions, a spec, or tickets that must be assessed and routed through grill-me, wayfinder, to-spec, and to-tickets. Persist stage and evidence in .project/preflight.md, enforce planning gates, and prevent production implementation before READY_FOR_IMPLEMENTATION.
---

# Project Preflight

Turn project context into an evidence-backed implementation handoff. Orchestrate installed planning skills; do not reproduce their interviews, decision work, specification synthesis, or ticket generation.

## Load the contracts

Read these files before acting:

1. [references/workflow.md](references/workflow.md) for states, transitions, routing, and rollback.
2. [references/artifact-contract.md](references/artifact-contract.md) for the canonical state file and artifact pointers.
3. [references/dependency-contract.md](references/dependency-contract.md) before routing to another skill or tracker.
4. [references/gates.md](references/gates.md) when evaluating or invalidating a gate.

Respect repository instructions before these contracts. If a repository rule conflicts with this skill, stop and identify the conflict instead of silently choosing one.

## Run one controlled cycle

1. Inspect the repository and conversation without modifying production code.
2. Read `.project/preflight.md` when it exists. Validate it with `scripts/validate_preflight.py` before trusting its stage.
3. If state is absent, reconstruct the highest defensible stage from existing evidence. Create the state file from `assets/preflight-template.md` only when the user's request authorizes project changes.
4. Check only the dependencies needed for the selected stage. Do not assume that a named skill or remote tracker is available.
5. Select the earliest gate that is not supported by evidence. Do not skip it merely because a later artifact exists.
6. Load and follow the installed stage skill:
   - `DISCOVERY` -> `grill-me`
   - `DECISION` -> `wayfinder`
   - `SPECIFICATION` -> `to-spec`
   - `TICKETING` -> `to-tickets`
7. Evaluate the stage gate from repository or tracker evidence. A conversation claim alone is not enough when a durable artifact should exist.
8. Update `.project/preflight.md` atomically after meaningful progress. Record artifact pointers rather than copying upstream artifacts into the state file.
9. Run the validator after every state update. Do not advance when validation fails.
10. Report the current stage, gate evidence, blockers, changed artifact pointers, and one next action.

## Enforce the guardrail

Before `READY_FOR_IMPLEMENTATION`, do not implement production features, initialize an application stack, or make speculative architecture changes. Permit a throwaway prototype only when `wayfinder` identifies it as evidence needed to resolve a decision; label it as disposable and keep it outside production paths.

Do not advance more than one gate in a single autonomous pass. Continue a live interview as required, but give the user a reviewable gate decision before routing to the next stage.

When adopting an existing project, reconstruct and evaluate earlier gates instead of assuming that an existing spec or ticket set proves readiness.

## Handle invalidation

Regress to the earliest affected stage when new evidence invalidates a gate. Mark the affected gate `invalidated`, retain the durable rationale, and leave later artifacts in place as historical evidence unless the user asks to remove them. Treat them as non-authoritative until their gates pass again.

If a dependency is missing, a tracker write is unauthorized, or evidence is contradictory, remain at the current stage and record a blocker. Never imitate a missing upstream skill or publish externally without authorization.

## Hand off implementation

Set `READY_FOR_IMPLEMENTATION` only after all four gates pass and the state validates. The handoff must name:

- the canonical spec;
- the approved ticket set;
- the first unblocked tracer-bullet ticket;
- the commands or evaluations that will verify it;
- any non-blocking residual risks.

End the preflight there. Begin implementation only in response to a separate implementation request or an already explicit instruction to continue after readiness.
