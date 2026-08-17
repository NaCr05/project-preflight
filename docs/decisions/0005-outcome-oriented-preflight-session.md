# ADR 0005: Use an outcome-oriented Preflight Session interface

- **Status:** Accepted
- **Date:** 2026-08-17
- **Refines:** ADR 0002 State lifecycle interface
- **Preserves:** ADR 0003 single-entry automatic orchestration

## Context

`StateStore` successfully centralized parsing, validation, transition mechanics, recovery, and atomic persistence. However, its public operations still required the calling Agent, CLI, and tests to coordinate `record`, `advance`, `regress`, and `directive` separately. Callers selected raw target Stages and Gate keys and had to preserve the ordering between evidence updates, state movement, and the next directive.

That choreography leaked lifecycle complexity through the Module Interface. It could drift between the Skill instructions, deterministic eval driver, CLI use, and future integrations even though all of them intended to express the same semantic result from a Stage Adapter.

## Decision

Introduce `PreflightSession` as the primary outcome-oriented State lifecycle Module Interface.

1. A caller submits one `StageOutcome` with a semantic verdict: `recorded`, `gate_passed`, `gate_blocked`, or `evidence_invalidated`.
2. A Stage outcome may include evidence, artifact pointers, dependency observations, blockers, and the next action, but never a target Stage, target Gate, raw Gate-status map, or transition command.
3. `PreflightSession` derives the current Gate, the next forward Stage, or the earliest regression Stage from the canonical contract registry and artifact ownership.
4. The Module validates and atomically persists one candidate, then returns validated state and exactly one `OrchestrationDirective` in the same result.
5. `StateStore` and the existing low-level CLI operations remain v0.3 compatibility interfaces. New Skill instructions, CLI examples, and behavior-eval drivers use `PreflightSession`.
6. Python continues to derive directives only. Codex remains responsible for visibly loading and following the selected bundled Skill, preserving ADR 0003.

## Consequences

- Callers express domain results rather than state-machine coordinates.
- Gate selection, forward movement, regression, persistence, and routing have one Locality.
- A successful mutation cannot forget to derive the next directive.
- Invalidated artifact authority maps deterministically to the earliest affected Stage while historical files remain intact.
- Compatibility callers may still use `StateStore`, but new features do not expand that lower-level Interface.
- Concurrency control and schema migration remain deferred because there is still one writer and one state schema in real use.

## Rejected alternatives

### Add more helper methods to `StateStore`

Rejected because it would preserve caller-selected Stage and Gate coordinates and continue spreading orchestration order across consumers.

### Let `StageOutcome` contain a target Stage or Gate

Rejected because it would rename the existing leak instead of deepening the Module.

### Infer regression from arbitrary natural-language evidence in Python

Rejected because deterministic runtime code cannot reliably classify semantic project evidence. The caller identifies the invalidated domain artifact; the Module owns its lifecycle mapping.

## Reopen when

- a stable native Skill-composition API changes the directive boundary;
- more than one real writer requires optimistic concurrency or locking;
- a second durable schema requires explicit migration policy;
- real evidence shows artifact ownership is insufficient to derive the earliest regression Stage.
