# ADR 0001: Keep orchestration separate from planning capabilities

- **Status:** Accepted; invocation mechanism superseded by ADR 0003 and release boundaries hardened by ADR 0004
- **Date:** 2026-08-13

## Context

The pre-coding workflow depends on specialized Skills for discovery, decision mapping, specification synthesis, and ticket generation. Copying those instructions into Project Preflight would create duplicated authority, context bloat, and version drift. Their current artifact behavior also varies: some use issue trackers while local Markdown remains a useful deterministic fallback.

## Decision

Project Preflight will own only lifecycle concerns:

- stage detection and routing;
- gate evaluation;
- project-scoped state persistence;
- dependency and authorization checks;
- rollback and implementation handoff.

It will store pointers to specialist artifacts rather than restating their content. ADR 0002 later validated explicit Handoff orchestration; ADR 0003 superseded that invocation mechanism with bundled automatic Stage Adapters while retaining this boundary. Local Markdown is the default; configured remote tracker artifacts may be referenced when their writes are authorized.

The canonical state will be a single `.project/preflight.md` file with restricted YAML frontmatter and human-readable evidence sections.

## Alternatives considered

### Combine all planning instructions in one Skill

Rejected because upstream improvements would not propagate and the combined Skill would consume excessive context.

### Require GitHub Issues

Rejected for v0.1 because it would make local evaluation nondeterministic and would require external authorization and credentials.

### Store state only in conversation memory

Rejected because planning must resume reliably across sessions and agents.

### Maintain separate YAML state and Markdown report

Rejected because two synchronized artifacts create an unnecessary drift risk. YAML frontmatter and Markdown evidence can share one canonical file.

## Consequences

- A missing bundled Stage Adapter blocks the affected stage instead of triggering an imitation.
- Remote and local artifacts share a pointer contract.
- The State lifecycle module can enforce structural readiness, while human review remains responsible for product judgment and evidence quality.
- Compatibility with upstream behavior must be rechecked as those Skills evolve.

## Reopen when

- Codex provides a stable native Skill dependency mechanism.
- A tracker adapter becomes necessary for repeated real-world use.
- The single-file state format cannot support safe concurrent planning.
