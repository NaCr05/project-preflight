# Workflow Contract

## State model

Use exactly one current stage:

```text
IDEA
  ↓ capture a durable idea
DISCOVERY
  ↓ Gate 1: problem clarity
DECISION
  ↓ Gate 2: decision readiness
SPECIFICATION
  ↓ Gate 3: specification readiness
TICKETING
  ↓ Gate 4: execution readiness
READY_FOR_IMPLEMENTATION
```

The current stage is the work now in progress. A passed gate advances immediately and atomically to the next stage.

## Route stages

| Current stage | Capability to load | Durable result |
|---|---|---|
| `IDEA` | Project Preflight | Captured idea pointer |
| `DISCOVERY` | `grill-me` | Evidence for Gate 1 |
| `DECISION` | `wayfinder` | Decision-map pointer or `not-required` |
| `SPECIFICATION` | `to-spec` | Specification pointer |
| `TICKETING` | `to-tickets` | Ticket-set pointer and first frontier ticket |
| `READY_FOR_IMPLEMENTATION` | None | Implementation handoff |

Load the current installed version of the named Skill. Do not embed a frozen copy of its behavior here.

## Detect the stage

1. Validate existing state before trusting it.
2. Inventory repository and tracker evidence.
3. Find the earliest gate without sufficient evidence.
4. Set the current stage to the work immediately before that gate.
5. If all gates have evidence, verify pointers and readiness invariants before declaring readiness.

The presence of a later artifact does not waive earlier gates. An existing project may be adopted at a later stage only after earlier gates are reconstructed and passed from evidence.

## Advance

Advance only through these forward transitions:

- `IDEA` → `DISCOVERY`
- `DISCOVERY` → `DECISION`
- `DECISION` → `SPECIFICATION`
- `SPECIFICATION` → `TICKETING`
- `TICKETING` → `READY_FOR_IMPLEMENTATION`

Update the gate, stage, previous stage, timestamp, reason, artifact pointers, and evidence in one change. Run the validator immediately afterward.

## Regress

Regress to the earliest stage affected by new evidence. Allowed regression targets are:

- from `DECISION`: `DISCOVERY`;
- from `SPECIFICATION`: `DECISION` or `DISCOVERY`;
- from `TICKETING`: `SPECIFICATION`, `DECISION`, or `DISCOVERY`;
- from `READY_FOR_IMPLEMENTATION`: `TICKETING`, `SPECIFICATION`, `DECISION`, or `DISCOVERY`.

Mark the gate that would advance from the target stage as `invalidated`. Mark later passed gates `invalidated` as well. Keep old artifacts as historical evidence, but do not treat them as current authority until the affected gates pass again.

## Control each cycle

Use this order:

1. **Detect** the earliest unresolved stage.
2. **Check** the stage dependency and tracker authorization.
3. **Route** to one upstream capability.
4. **Evaluate** one gate using durable evidence.
5. **Persist** state and artifact pointers.
6. **Validate** the state file.
7. **Report** current stage, evidence, blockers, and next action.

Do not autonomously cross multiple gates in one pass. This preserves human review and prevents a plausible-looking chain of unsupported conclusions.

## Guard implementation

Before readiness, permit only planning, research, evaluation, or a disposable prototype explicitly required to resolve a decision. Do not initialize or modify production application code as speculative momentum.

At readiness, hand off the canonical spec, ticket set, first unblocked tracer bullet, verification path, and residual risks. Starting implementation remains a separate action.
