---
schema_version: 1
project: "ready-invalidated"
current_stage: "READY_FOR_IMPLEMENTATION"
previous_stage: "TICKETING"
last_transition: "2026-08-13T08:00:00Z"
transition_reason: "All readiness Gates passed"
tracker: "local-markdown"
ready_for_implementation: true
gates:
  gate_1: "passed"
  gate_2: "passed"
  gate_3: "passed"
  gate_4: "passed"
artifacts:
  idea: "docs/idea.md"
  decision_map: "docs/decisions.md"
  spec: "docs/spec.md"
  tickets: "tickets"
dependencies:
  grill-me: "available"
  wayfinder: "available"
  to-spec: "available"
  to-tickets: "available"
---

# Project Preflight

## Original Idea

See `docs/idea.md`.

## Gate Evidence

### Gate 1

Discovery passed.

### Gate 2

The old data-source decision passed before invalidation evidence appeared.

### Gate 3

The old specification passed.

### Gate 4

The old ticket frontier passed.

## Blockers

None recorded.

## Next Action

Implement the first tracer bullet.
