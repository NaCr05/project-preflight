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

| Current stage | Explicit user handoff | Durable result |
|---|---|---|
| `IDEA` | Project Preflight | Captured idea pointer |
| `DISCOVERY` | `grill-me` | Evidence for Gate 1 |
| `DECISION` | `wayfinder` | Decision-map pointer or `not-required` |
| `SPECIFICATION` | `to-spec` | Specification pointer |
| `TICKETING` | `to-tickets` | Ticket-set pointer and first frontier ticket |
| `READY_FOR_IMPLEMENTATION` | None | Implementation handoff |

Project Preflight never invokes the named Skill internally. It prints an exact `$skill-name` instruction, stops, and waits for the user to invoke that Skill. After the upstream work has a durable result, the instruction sends the user back to `$project-preflight` for Gate evaluation. Do not embed a frozen copy of upstream behavior here.

Generate the instruction with:

```text
python scripts/preflight_state.py handoff
```

The handoff must name the upstream Skill, the bounded purpose, the production-code guardrail, and the explicit return to `$project-preflight`.

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

Use `scripts/preflight_state.py advance` to update the Gate, Stage, previous Stage, timestamp, reason, artifact pointers, and evidence in one validated atomic change. Do not edit the frontmatter directly.

## Regress

Regress to the earliest stage affected by new evidence. Allowed regression targets are:

- from `DECISION`: `DISCOVERY`;
- from `SPECIFICATION`: `DECISION` or `DISCOVERY`;
- from `TICKETING`: `SPECIFICATION`, `DECISION`, or `DISCOVERY`;
- from `READY_FOR_IMPLEMENTATION`: `TICKETING`, `SPECIFICATION`, `DECISION`, or `DISCOVERY`.

Use `scripts/preflight_state.py regress`. It marks the Gate that would advance from the target Stage and all later Gates `invalidated` in one validated atomic change. Keep old artifacts as historical evidence, but do not treat them as current authority until the affected Gates pass again.

## Control each cycle

Use this order:

1. **Detect** the earliest unresolved stage.
2. **Check** the Stage dependency in the active catalog and check tracker authorization.
3. **Handoff** one exact user-invoked upstream Skill instruction, then stop.
4. **Resume** only after the user explicitly invokes `$project-preflight` again.
5. **Evaluate** one Gate using the returned durable evidence.
6. **Persist** state and artifact pointers through the State lifecycle interface.
7. **Report** current Stage, evidence, blockers, and the next handoff or terminal implementation handoff.

Do not invoke an upstream Skill and do not autonomously cross multiple Gates in one run. The visible handoff preserves human control and prevents a plausible-looking chain of unsupported conclusions.

## Guard implementation

Before readiness, permit only planning, research, evaluation, or a disposable prototype explicitly required to resolve a decision. Do not initialize or modify production application code as speculative momentum.

At readiness, hand off the canonical spec, ticket set, first unblocked tracer bullet, verification path, and residual risks. Starting implementation remains a separate action.
