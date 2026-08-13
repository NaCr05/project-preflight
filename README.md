# Project Preflight

**English** | [简体中文](README.zh-CN.md)

> A gated pre-coding workflow orchestrator for AI coding agents.

`project-preflight` turns a vague software idea—or a partially planned project—into an evidence-backed implementation handoff. It detects the current stage, routes work through compatible planning Skills, persists progress across sessions, and stops production coding until the project is demonstrably ready.

## How it works

```mermaid
flowchart LR
    A["Vague idea"] --> B["Discovery<br/>grill-me"]
    B -->|"Gate 1"| C["Decisions<br/>wayfinder"]
    C -->|"Gate 2"| D["Specification<br/>to-spec"]
    D -->|"Gate 3"| E["Tickets<br/>to-tickets"]
    E -->|"Gate 4"| F["READY_FOR_IMPLEMENTATION"]
```

Project Preflight advances one evidence-backed gate at a time. You remain responsible for product and architecture decisions; Codex interviews, maps decisions, synthesizes the approved spec, and proposes a reviewable ticket frontier. The endpoint is an implementation handoff—not completed product code.

**[Read the complete workflow guide →](docs/workflow.md)**

## Why this exists

Planning Skills are useful individually, but a project can still skip a step, lose state between sessions, duplicate decisions across documents, or treat the existence of a spec as proof of readiness. Project Preflight supplies the missing lifecycle:

- stage detection and resumption;
- evidence-based gates;
- tracker-agnostic artifact pointers;
- scope and implementation guardrails;
- rollback when a technical assumption fails;
- a precise `READY_FOR_IMPLEMENTATION` handoff.

It orchestrates rather than replaces:

- `grill-me` for discovery;
- `wayfinder` for unresolved decisions;
- `to-spec` for specification synthesis;
- `to-tickets` for tracer-bullet tickets.

Those Skills are not bundled with this repository and retain their own behavior and licensing.

## Install locally

Copy `skills/project-preflight` into your Codex Skills directory as `project-preflight`. For example, place it under:

```text
<CODEX_HOME>/skills/project-preflight
```

Install the four upstream Skills separately. Project Preflight checks stage dependencies before routing and stops with a useful blocker when one is unavailable.

## Use it

Start from an idea:

```text
Use $project-preflight. I want to build an open-source agent that ...
```

Resume later:

```text
Use $project-preflight to resume this project's preflight.
```

Audit an existing plan:

```text
Use $project-preflight to determine whether this spec and ticket set are ready for implementation.
```

The Skill maintains one canonical state file in the target project:

```text
.project/preflight.md
```

The file records stage, gate status, blockers, and pointers to the canonical idea, decision map, spec, and ticket set. It does not duplicate those artifacts.

## Readiness gates

1. **Problem clarity** — user, problem, value, input, output, MVP, non-goals, and measurable success are clear.
2. **Decision readiness** — architecture-reversing unknowns and feasibility risks are resolved or explicitly non-blocking.
3. **Specification readiness** — scope, behavior, testing decisions, and open questions are precise enough to judge every proposed feature.
4. **Execution readiness** — tickets are vertical, testable, correctly blocked, scope-preserving, and include a first tracer bullet.

Only Gate 4 produces `READY_FOR_IMPLEMENTATION`.

## Repository layout

- `skills/project-preflight/` — the distributable Skill.
- `docs/product-spec.md` — v0.1 product scope and success criteria.
- `docs/workflow.md` — complete user journey, gates, artifacts, pauses, and rollback behavior.
- `docs/decisions/` — append-only architectural rationale.
- `tests/` — deterministic state-contract tests.
- `evals/` — realistic behavioral cases and dated forward-test evidence.

## Validate changes

The validator uses only the Python standard library:

```text
python -m unittest discover -s tests -v
python skills/project-preflight/scripts/validate_preflight.py tests/fixtures/valid-idea.md --repo-root tests/fixtures
```

Run the Skill Creator `quick_validate.py` against `skills/project-preflight` to validate packaging metadata.

## Status

This repository currently targets a small, reviewable v0.1 contract: local Markdown state, optional remote tracker pointers, explicit upstream dependencies, and deterministic readiness validation. A self-hosted local happy path has reached validated `READY_FOR_IMPLEMENTATION`; live remote-tracker publication and automatic dependency installation are intentionally deferred.

## License

MIT. See `LICENSE`.
