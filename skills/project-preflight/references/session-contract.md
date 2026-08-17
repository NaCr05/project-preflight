# Preflight Session Contract

The `PreflightSession` Module is the primary state lifecycle Interface. A caller supplies one semantic `StageOutcome`; the Module owns Gate selection, the next forward Stage, the earliest regression Stage, invariants, validation, atomic persistence, and the next `OrchestrationDirective`.

## Interface

- `start(project, original_idea)` creates state and returns validated state plus the first directive.
- `current()` validates durable state and returns exactly one directive.
- `apply(outcome)` atomically applies one Stage result and returns validated state plus the next directive.
- `recover(valid_source)` restores an explicitly selected valid document and returns the resumed directive.

`StateStore` and the CLI commands `record`, `advance`, `regress`, and `directive` are v0.3 compatibility interfaces. New Skill behavior and evaluation drivers use `PreflightSession`.

## StageOutcome

A Stage outcome contains a non-empty reason plus durable updates such as artifact pointers, dependency observations, the original idea, blockers, or the next action. It never contains a target Stage, target Gate, raw Gate status map, or transition command.

Use exactly one verdict:

<!-- project-preflight:generated session-outcome-table:start -->
| Verdict | Meaning | Session behavior |
|---|---|---|
| `recorded` | Durable observations changed but no Gate was judged | Preserve the Stage, persist updates, derive the directive |
| `gate_passed` | The current Stage's Gate has sufficient evidence | Derive the current Gate and next Stage, advance once |
| `gate_blocked` | The current Stage's Gate lacks required evidence | Derive and block the current Gate without advancing |
| `evidence_invalidated` | Canonical artifact authority was contradicted | Derive the earliest affected Stage from artifact ownership and invalidate later Gates |
<!-- project-preflight:generated session-outcome-table:end -->

`gate_passed`, `gate_blocked`, and `evidence_invalidated` require concrete evidence. A `recorded` outcome must contain at least one durable update.

## Regression derivation

The caller identifies invalidated evidence by domain artifact, not by state-machine coordinates:

<!-- project-preflight:generated artifact-regression-table:start -->
| Invalidated artifact | Earliest affected Stage |
|---|---|
| `idea` | `DISCOVERY` |
| `decision_map` | `DECISION` |
| `spec` | `SPECIFICATION` |
| `tickets` | `TICKETING` |
<!-- project-preflight:generated artifact-regression-table:end -->

When multiple artifacts are invalidated, the session selects the earliest owner. Evidence for an artifact that is not yet authoritative cannot force a later Stage. Historical files remain on disk unless a separately authorized operation changes them.

## CLI examples

Start from a rough idea and receive the first directive:

```text
python scripts/preflight_state.py init --project example --idea "A rough idea" --json --locale en
```

Pass the current Gate and save its canonical artifact pointer:

```text
python scripts/preflight_state.py apply --verdict gate_passed --reason "Decision readiness passed" --evidence "Approved decision map and feasibility evidence." --artifact decision_map=docs/decisions.md --json --locale en
```

Invalidate decision evidence without choosing `DECISION` or `gate_2` directly:

```text
python scripts/preflight_state.py apply --verdict evidence_invalidated --reason "Provider capability changed" --evidence "Current provider docs contradict the decision map." --invalidated-artifact decision_map --json --locale en
```

Every successful result contains `state` and `directive`. An invalid candidate raises an error before replacement, leaving the last valid state byte-for-byte unchanged.
