# Workflow contract

## Canonical state machine

```text
IDEA
  -> DISCOVERY
  -> DECISION       (Gate 1 passed)
  -> SPECIFICATION  (Gate 2 passed)
  -> TICKETING      (Gate 3 passed)
  -> READY_FOR_IMPLEMENTATION (Gate 4 passed)
```

`DISCOVERY`, `DECISION`, `SPECIFICATION`, and `TICKETING` each run through a bundled stage adapter selected automatically by `preflight_state.py directive`. The user invokes `$project-preflight` once and then only answers or confirms.

<!-- project-preflight:generated stage-routing-table:start -->
| Current Stage | Bundled adapter | Public Skill label | Durable result |
|---|---|---|---|
| `IDEA` | None | Project Preflight | Rough idea captured |
| `DISCOVERY` | `project-preflight-grill-me` | `grill-me` | Canonical idea/discovery evidence |
| `DECISION` | `project-preflight-wayfinder` | `wayfinder` | Decision map |
| `SPECIFICATION` | `project-preflight-to-spec` | `to-spec` | Canonical specification |
| `TICKETING` | `project-preflight-to-tickets` | `to-tickets` | Ticket frontier |
| `READY_FOR_IMPLEMENTATION` | None | Project Preflight | Implementation handoff |
<!-- project-preflight:generated stage-routing-table:end -->

## Controlled loop

1. Validate or reconstruct the earliest defensible Stage.
2. Derive the current orchestration directive.
3. Show the user-visible Skill banner.
4. Follow the bundled adapter until it needs one user answer or produces its durable result.
5. Evaluate the current Gate; persist evidence and cross at most one transition per mutation.
6. Derive the next directive and continue automatically.

The conversation may cross multiple Gates without requiring a new `$project-preflight` invocation, but every Gate is still a separate validated state transition. Stop only for user input, missing authority/capability, contradictory evidence, explicit cancellation, or readiness.

## Regression

New evidence returns the project to the earliest affected Stage. All later Gates become `invalidated`; later artifacts remain as non-authoritative history. The next directive announces the adapter for the regression target and resumes from there.

## Guardrail

No production implementation before `READY_FOR_IMPLEMENTATION`. Planning artifacts, evidence research, and explicitly disposable decision prototypes are allowed.
