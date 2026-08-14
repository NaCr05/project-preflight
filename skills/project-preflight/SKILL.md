---
name: project-preflight
description: Orchestrate the pre-coding lifecycle for a new or existing software project, especially an AI or agent project. Use when a user has a vague project idea, wants to resume interrupted planning, needs to determine whether a project is ready to implement, or already has decisions, a spec, or tickets that must be assessed and routed through grill-me, wayfinder, to-spec, and to-tickets. Persist stage and evidence in .project/preflight.md, enforce planning gates, and prevent production implementation before READY_FOR_IMPLEMENTATION.
---

# Project Preflight

Turn project context into an evidence-backed implementation handoff. Orchestrate installed planning skills through explicit user-invoked handoffs; do not invoke them internally or reproduce their interviews, decision work, specification synthesis, or ticket generation.

## Load the contracts

Read these files before acting:

1. [references/workflow.md](references/workflow.md) for states, transitions, routing, and rollback.
2. [references/artifact-contract.md](references/artifact-contract.md) for the canonical state file and artifact pointers.
3. [references/dependency-contract.md](references/dependency-contract.md) before routing to another skill or tracker.
4. [references/gates.md](references/gates.md) when evaluating or invalidating a gate.

Respect repository instructions before these contracts. If a repository rule conflicts with this skill, stop and identify the conflict instead of silently choosing one.

## Use the State lifecycle interface

Use `scripts/preflight_state.py` for every state mutation. Do not hand-edit YAML frontmatter.

- `init` creates canonical state and can capture the original idea.
- `record` updates evidence, blockers, pointers, or dependency observations without changing Stage.
- `advance` crosses exactly one forward transition and requires evidence for the Gate it passes.
- `regress` invalidates every affected Gate and returns to the earliest affected Stage.
- `recover` atomically restores an explicitly supplied valid state.
- `handoff` prints the exact upstream Skill invocation and return instruction.

The lifecycle module validates a complete candidate before atomically replacing the old file. A failed operation leaves the last valid state unchanged. Use `scripts/validate_preflight.py` as the compatibility validator and add `--check-remote` only when network access and any required authorization are available.

## Run one controlled cycle

1. Inspect the repository and conversation without modifying production code.
2. Read `.project/preflight.md` when it exists. Validate it through `scripts/preflight_state.py validate` before trusting its Stage.
3. If state is absent, reconstruct the highest defensible Stage from existing evidence. Use `scripts/preflight_state.py init` only when the user's request authorizes project changes. The asset is a derived example, not a file to copy and edit by hand.
4. Check only the dependency needed for the selected Stage. A directory on disk is not proof that a Skill is present in the active catalog and explicitly invokable.
5. Select the earliest gate that is not supported by evidence. Do not skip it merely because a later artifact exists.
6. Generate an explicit handoff for the current Stage:
   - `DISCOVERY` -> `grill-me`
   - `DECISION` -> `wayfinder`
   - `SPECIFICATION` -> `to-spec`
   - `TICKETING` -> `to-tickets`
7. Show the exact `$skill-name` instruction to the user and stop this Project Preflight run. Do not invoke or imitate the upstream Skill inside the same run.
8. When the user explicitly returns to `$project-preflight`, inspect the durable result and evaluate the current Gate. A conversation claim alone is not enough when a durable artifact should exist.
9. Persist meaningful progress through the State lifecycle interface. Record artifact pointers rather than copying upstream artifacts into the state file.
10. Report the current Stage, Gate evidence, blockers, changed artifact pointers, and either one explicit handoff or the implementation handoff.

## Enforce the guardrail

Before `READY_FOR_IMPLEMENTATION`, do not implement production features, initialize an application stack, or make speculative architecture changes. Permit a throwaway prototype only when `wayfinder` identifies it as evidence needed to resolve a decision; label it as disposable and keep it outside production paths.

Do not advance more than one Gate in a single Project Preflight run. Every upstream Stage is a visible user-invoked handoff followed by a separate return to `$project-preflight`.

When adopting an existing project, reconstruct and evaluate earlier gates instead of assuming that an existing spec or ticket set proves readiness.

## Handle invalidation

Regress to the earliest affected stage when new evidence invalidates a gate. Mark the affected gate `invalidated`, retain the durable rationale, and leave later artifacts in place as historical evidence unless the user asks to remove them. Treat them as non-authoritative until their gates pass again.

If a dependency is missing from the active catalog, a tracker write is unauthorized, or evidence is contradictory, remain at the current Stage and record a blocker. Never treat filesystem presence as callable availability, imitate a missing upstream Skill, or publish externally without authorization.

## Hand off implementation

Set `READY_FOR_IMPLEMENTATION` only after all four gates pass and the state validates. The handoff must name:

- the canonical spec;
- the approved ticket set;
- the first unblocked tracer-bullet ticket;
- the commands or evaluations that will verify it;
- any non-blocking residual risks.

End the preflight there. Begin implementation only in response to a separate implementation request or an already explicit instruction to continue after readiness.
