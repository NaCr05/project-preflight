# Automatic orchestration validation — 2026-08-14

## Scope

This run validates ADR 0003 on branch `agent/automatic-orchestration-plugin`. The prior explicit-Handoff evidence remains attached to the preserved experimental branch.

## Deterministic checks

- 34 repository tests passed.
- The Plugin manifest passed the Codex Plugin validator.
- The public orchestrator and all four bundled adapters passed Skill Creator validation.
- The derived state template matched the canonical registry.
- Behavior fixtures scored automatic routing, dependency behavior, Gate evidence, artifact authority, production guardrails, state validity, changed Next Action, and visible Skill announcements.
- The lifecycle happy path covered all four adapter directives, Gate 2–4, final readiness, regression, recovery, and atomic-write failure preservation.

## Fresh-context forward test

Prompt:

```text
Use $project-preflight. 我想做一个帮独立开发者从用户反馈里找出最值得做功能的开源工具。
```

Observed first response:

```text
Project Preflight · Discovery — 正在使用 `grill-me`（Project Preflight 内置适配器）。你只需回答或确认。

这个工具第一版最想服务哪类独立开发者：已经有产品并持续收到用户反馈的人，还是仍在寻找方向、手里只有零散反馈的人？
```

Result:

- active capability was visible;
- exactly one focused question was asked;
- no Skill invocation, copy/paste command, or manual resume was requested;
- production implementation did not begin.

The test identified one ambiguity: first-run state initialization should be invisible when the user's opening message already contains the idea. The orchestration contract was tightened accordingly before this result was recorded.

## Installed Plugin full happy path

The Plugin was installed from the personal Marketplace as `project-preflight@personal` version `0.3.0`. A fresh Codex CLI process then ran project `feedback-compass` in an isolated Git repository from one `$project-preflight` invocation. Recommended defaults were pre-approved so the run could cross every Gate without simulated follow-up turns.

Session: `019fff88-0e86-7983-abd4-32403c9faf42`

The assistant emitted these user-visible Stage messages as actual assistant responses:

```text
Project Preflight · Discovery — 正在使用 `grill-me`（Project Preflight 内置适配器）。你只需回答或确认。
Project Preflight · Decision — 正在使用 `wayfinder`（Project Preflight 内置适配器）。你只需回答或确认。
Project Preflight · Specification — 正在使用 `to-spec`（Project Preflight 内置适配器）。你只需回答或确认。
Project Preflight · Ticketing — 正在使用 `to-tickets`（Project Preflight 内置适配器）。你只需回答或确认。
Project Preflight · Ready — 四道 Gate 已通过，正在整理实施交接。
```

Durable outputs:

- `.project/discovery.md`
- `.project/decision-map.md`
- `.project/spec.md`
- `.project/tickets.md`
- `.project/preflight.md`

Independent validation with the installed runtime returned `VALID: READY_FOR_IMPLEMENTATION` and a `READY` orchestration directive. All four Gates were `passed`, all artifact pointers resolved, and the project root contained no production source or application scaffold.

The first frontier ticket, `FC-001`, is an end-to-end CSV tracer bullet with a concrete offline verification command. The run made no external writes and did not ask the user to invoke or copy another Skill.

Operational observation: the full planning run consumed approximately 108k model tokens and about ten minutes with high reasoning effort. Functional orchestration passed, but a future optimization pass should bound artifact verbosity and repeated context loading before treating this as the desired routine cost profile.
