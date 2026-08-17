# ADR 0002: Use explicit handoffs and one State lifecycle interface

- **Status:** Superseded by ADR 0003
- **Date:** 2026-08-13
- **Amends:** ADR 0001 routing mechanism; its orchestration boundary remains accepted
- **State interface refined by:** ADR 0005

## Context

This ADR records the architecture of the validated `agent/handoff-state-lifecycle` experiment. Its State lifecycle, contract registry, evidence adapters, and deterministic evaluations remain accepted foundations. ADR 0003 replaces only its user-invoked Handoff orchestration mechanism.

The first release described upstream Skills as capabilities Project Preflight could load and follow inside one run. In practice, an upstream Skill may be installed on disk but absent from the active catalog, and several upstream Skills require explicit user invocation. The state contract also required atomic updates while providing only a validator, leaving transition construction and persistence to the calling Agent.

Finite Stage, Gate, artifact, dependency, and transition facts were repeated across the validator, template, contracts, and tests. Remote artifact URLs were accepted without an explicit validation result.

## Decision

Project Preflight will use handoff orchestration:

1. detect the current Stage;
2. verify the required Skill in the active catalog;
3. produce one exact user-invoked `$skill-name` instruction;
4. stop;
5. evaluate the durable result only after the user explicitly returns to `$project-preflight`.

All state mutation crosses the `StateStore` interface. Its implementation owns restricted YAML parsing, transition and regression calculation, Gate and artifact invariants, validation, atomic persistence, and explicit recovery. The previous validator path remains a compatibility interface.

Finite contract values live in `_contract.py`. The initial-state asset is derived from that registry. Artifact Evidence uses concrete inline, local path, GitHub Issue, and generic HTTP adapters behind one seam.

## Consequences

- Upstream Skills remain independent and retain authority for their own behavior.
- Every Stage change has a visible human control point.
- Invalid candidate state cannot replace the last valid state.
- Tests and Skill execution cross the same State lifecycle interface.
- Remote accessibility can be checked, but semantic Gate sufficiency remains human-reviewed.
- Explanatory contracts must stay synchronized with the canonical finite registry.

## Rejected alternatives

### Invoke upstream Skills internally when files are present

Rejected because filesystem presence does not prove active-catalog availability or permission for model invocation.

### Keep hand-editing state and add more validator checks

Rejected because it improves detection without preventing invalid transitions or partial writes.

### Add a tracker adapter abstraction without a real remote adapter

Rejected. The seam was introduced only after inline, local path, GitHub Issue, and generic HTTP behaviors all existed.

## Reopen when

- Codex provides a stable native Skill composition mechanism with explicit dependency metadata;
- real concurrency requires revision checks or locking beyond atomic replacement;
- another tracker has repeated real-world demand and a testable read contract.
