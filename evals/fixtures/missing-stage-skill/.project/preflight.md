---
schema_version: 1
project: "missing-stage-skill"
current_stage: "TICKETING"
previous_stage: "SPECIFICATION"
last_transition: "2026-08-13T08:00:00Z"
transition_reason: "Specification readiness passed"
tracker: "local-markdown"
ready_for_implementation: false
gates:
  gate_1: "passed"
  gate_2: "passed"
  gate_3: "passed"
  gate_4: "not_evaluated"
artifacts:
  idea: "docs/idea.md"
  decision_map: "docs/decisions.md"
  spec: "docs/spec.md"
  tickets: null
dependencies:
  grill-me: "available"
  wayfinder: "available"
  to-spec: "available"
  to-tickets: "not_checked"
---

# Project Preflight

## Original Idea

See `docs/idea.md`.

## Gate Evidence

### Gate 1

See the approved idea.

### Gate 2

See the approved decisions.

### Gate 3

See the canonical specification.

### Gate 4

Not evaluated.

## Blockers

None recorded.

## Next Action

Check whether `to-tickets` is available for explicit invocation.
