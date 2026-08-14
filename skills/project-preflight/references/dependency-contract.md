# Dependency contract

The Plugin bundles four namespaced stage adapters. A normal installation therefore does not require the user to install or invoke `grill-me`, `wayfinder`, `to-spec`, or `to-tickets` separately.

<!-- project-preflight:generated dependency-table:start -->
| Public capability | Bundled Skill | Stage |
|---|---|---|
| `grill-me` | `project-preflight-grill-me` | `DISCOVERY` |
| `wayfinder` | `project-preflight-wayfinder` | `DECISION` |
| `to-spec` | `project-preflight-to-spec` | `SPECIFICATION` |
| `to-tickets` | `project-preflight-to-tickets` | `TICKETING` |
<!-- project-preflight:generated dependency-table:end -->

Dependency status records runtime observation:

- `available` — the bundled adapter can be loaded and followed;
- `missing` — its Skill directory or instructions are unavailable;
- `not_checked` — no runtime check has yet been recorded.

`not_checked` does not block a directive; the orchestrator attempts the bundled adapter and records the result. `missing` produces a `BLOCKED` directive and keeps the current Stage.

Each adapter is authoritative for its bounded stage behavior. Project Preflight is authoritative for routing, visibility, Gates, state, rollback, and readiness. The orchestrator reads the adapter's bundled `SKILL.md` directly, returns automatically after durable evidence exists, and never asks the user to invoke it.

Tracker reads and writes remain separate capabilities. Local Markdown is the default. Remote writes require user authorization and must not be inferred from adapter availability.
