---
name: project-preflight
description: Single-entry pre-coding orchestrator for a new or existing software project, especially an AI or agent project. Use when a user has a rough idea, wants to resume planning, or needs to determine implementation readiness. Automatically coordinate bundled grill-me, wayfinder, to-spec, and to-tickets stage adapters; persist evidence in .project/preflight.md; show which Skill is active; and prevent production implementation before READY_FOR_IMPLEMENTATION.
---

# Project Preflight

Own the pre-coding conversation from one `$project-preflight` invocation until user input, a genuine blocker, explicit cancellation, or `READY_FOR_IMPLEMENTATION`. The user answers questions and confirms decisions; never ask them to invoke another Skill or copy a prompt.

## Load the contracts

Read, in order:

1. [references/workflow.md](references/workflow.md) for stages, transitions, and rollback.
2. [references/orchestration-contract.md](references/orchestration-contract.md) for automatic adapter routing and Skill visibility.
3. [references/artifact-contract.md](references/artifact-contract.md) for canonical evidence.
4. [references/dependency-contract.md](references/dependency-contract.md) for bundled adapter availability and tracker authorization.
5. [references/gates.md](references/gates.md) when evaluating or invalidating a Gate.
6. [references/session-contract.md](references/session-contract.md) before applying a Stage result or regression.

Respect repository instructions. Stop and surface an actual conflict instead of silently choosing one.

## Use the session seam

Use `scripts/preflight_state.py` for every state mutation; never hand-edit YAML frontmatter.

- `init --json` captures the rough idea and returns the first directive.
- `current --json` validates existing state and returns exactly one directive.
- `apply --json` submits one `StageOutcome`; the session derives Gate status, advance or regression, atomic persistence, and the next directive.
- `recover` atomically restores an explicitly supplied valid state.

Do not choose a target Stage or Gate in new orchestration code. The `record`, `advance`, `regress`, and `directive` commands remain only as v0.3 compatibility interfaces. Candidate state is validated before atomic replacement. A failed operation leaves the last valid state unchanged.

## Run the automatic loop

1. Inspect project context without implementing production code. Run `current --json`, or use `init --json` when no state exists and the user's rough paragraph is available.
2. Select `--locale en` for English or `--locale zh-CN` for Simplified Chinese based on the user's current language. Show the returned directive's `announcement` before stage work so the user always knows which capability is active.
3. For `RUN_STAGE_ADAPTER`, read and follow the bundled adapter at `../<adapter_skill>/SKILL.md`. Do this yourself; do not delegate invocation to the user.
4. Keep one-question-at-a-time interaction where the adapter requires it. Persist its durable artifact or pointer.
5. Return control to this orchestrator automatically, evaluate the evidence, and submit one `StageOutcome` with `apply --json`. Use `gate_passed`, `gate_blocked`, `recorded`, or `evidence_invalidated`; never supply a target Stage or Gate.
6. Use the directive returned by the same `apply` result. Announce the next Skill and continue until a user answer is required, a blocker exists, or readiness is reached.
7. On resumed conversations, validate state, show the active Skill banner again, and continue the same loop.

Stage routing is canonical:

<!-- project-preflight:generated stage-routing-list:start -->
- `DISCOVERY` -> `project-preflight-grill-me` (shown to the user as `grill-me`)
- `DECISION` -> `project-preflight-wayfinder` (shown to the user as `wayfinder`)
- `SPECIFICATION` -> `project-preflight-to-spec` (shown to the user as `to-spec`)
- `TICKETING` -> `project-preflight-to-tickets` (shown to the user as `to-tickets`)
<!-- project-preflight:generated stage-routing-list:end -->

Do not pretend that Python invokes a Skill. The runtime chooses the stage and renders the directive; the Codex orchestrator loads and follows the bundled Skill instructions.

## Guardrails and invalidation

Before readiness, do not implement production features, initialize an application stack, or make speculative architecture changes. A disposable prototype is allowed only when the decision adapter identifies it as necessary evidence and it stays outside production paths.

If new evidence invalidates a Gate, regress to the earliest affected Stage, preserve later artifacts as non-authoritative history, show the newly active Skill, and continue from there. If a bundled adapter is unavailable, a tracker write lacks authorization, or evidence conflicts, remain at the current Stage and record a blocker.

## Finish at readiness

Set `READY_FOR_IMPLEMENTATION` only after all four Gates pass and state validates. Present the canonical spec, approved ticket set, first unblocked tracer bullet, verification commands or evaluations, and residual non-blocking risks. End preflight there; implementation needs a separate or already explicit instruction.
