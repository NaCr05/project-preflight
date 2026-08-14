# Project Preflight

**English** | [简体中文](README.zh-CN.md)

> One invocation turns a rough software idea into an evidence-backed, implementation-ready plan.

Project Preflight is a Codex Plugin with one public entry: `$project-preflight`. It automatically coordinates discovery, architecture decisions, specification, and ticketing. You never copy a generated Skill command; you only answer questions and confirm choices.

## The experience

```mermaid
flowchart LR
    A["Your rough paragraph"] --> P["$project-preflight once"]
    P --> G["Discovery<br/>grill-me"]
    G --> W["Decisions<br/>wayfinder"]
    W --> S["Specification<br/>to-spec"]
    S --> T["Tickets<br/>to-tickets"]
    T --> R["READY_FOR_IMPLEMENTATION"]
```

At each Stage, Project Preflight tells you which capability it is using. The short label is the familiar capability name; execution stays inside the namespaced Plugin adapter:

```text
Project Preflight · Discovery — 正在使用 `grill-me`（Project Preflight 内置适配器）。你只需回答或确认。
```

The specialist Skill returns to Project Preflight automatically after saving durable evidence. Project Preflight checks the Gate, updates `.project/preflight.md` atomically, announces the next Skill, and continues. It pauses only for your answer, a real blocker, cancellation, or readiness.

**[Read the complete workflow →](docs/workflow.md)**

## Four Gates

1. **Problem clarity** — user, problem, value, inputs, outputs, MVP, non-goals, assumptions, and measurable success are clear.
2. **Decision readiness** — architecture-reversing unknowns and feasibility risks are resolved or explicitly non-blocking.
3. **Specification readiness** — scope, behavior, boundaries, and verification are buildable and unambiguous.
4. **Execution readiness** — tickets are vertical, testable, correctly blocked, and begin with a tracer bullet.

Only Gate 4 produces `READY_FOR_IMPLEMENTATION`. Preflight ends with the canonical spec, approved tickets, first unblocked tracer bullet, verification path, and residual risks—not production code.

## Plugin architecture

- `skills/project-preflight/` — the single user-facing orchestrator and state runtime.
- `skills/project-preflight-grill-me/` — bundled discovery adapter.
- `skills/project-preflight-wayfinder/` — bundled decision adapter.
- `skills/project-preflight-to-spec/` — bundled specification adapter.
- `skills/project-preflight-to-tickets/` — bundled ticketing adapter.
- `.codex-plugin/plugin.json` — Codex Plugin manifest.
- `docs/decisions/0003-single-entry-automatic-orchestration-plugin.md` — current architecture decision.

The adapters are namespaced to avoid collisions with separately installed Skills. See [third-party notices](THIRD_PARTY_NOTICES.md) for upstream inspiration and attribution.

## Use

```text
Use $project-preflight. I want to build an open-source tool that ...
```

For an existing project:

```text
Use $project-preflight to audit this project and continue from the earliest unsupported Gate.
```

The first message can be one immature sentence. Project Preflight does not expect a plan.

## State and safety

`.project/preflight.md` stores the Stage, Gate status, blockers, and pointers to canonical artifacts. Parsing, transitions, regression, validation, recovery, and atomic persistence share one State lifecycle interface. Remote artifact pointers are explicit evidence-adapter results; they are not silently treated as verified.

No production implementation is allowed before readiness. If new evidence invalidates a decision, Project Preflight regresses to the earliest affected Stage and automatically resumes the corresponding Skill while preserving later artifacts as history.

## Validate changes

```text
python -m unittest discover -s tests -v
python skills/project-preflight/scripts/preflight_state.py template --check skills/project-preflight/assets/preflight-template.md
python evals/run_behavior_evals.py list
```

Also run the Codex Plugin validator on the repository root and Skill Creator validation on each directory under `skills/`.

## Branch history

The validated explicit-Handoff experiment remains preserved on `agent/handoff-state-lifecycle`. This branch replaces only its orchestration UX; the proven State lifecycle, evidence adapters, regression, and eval architecture remain.

## License

MIT. See [LICENSE](LICENSE).
