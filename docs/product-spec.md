# Project Preflight v0.3.2 Product Specification

## Purpose

Project Preflight is a single-entry Codex Plugin that moves a rough software idea or incomplete project plan to an evidence-backed implementation-ready ticket frontier. It automatically coordinates bundled discovery, decision, specification, and ticketing Skills while keeping their identity visible to the user.

## Intended users and input

Solo developers, open-source maintainers, contributors auditing an existing plan, and AI/agent builders. The normal input is one immature paragraph, not a prepared project plan. Existing repositories and planning artifacts may also be supplied.

## Outputs

- `.project/preflight.md` with canonical Stage, Gate, blocker, dependency, and artifact-pointer state;
- durable idea/discovery evidence, decision map, specification, and ticket frontier;
- a visible active-Skill notice at every Stage entry or resume;
- a `READY_FOR_IMPLEMENTATION` handoff naming the first tracer bullet and verification path.

## Goals

1. Require only one `$project-preflight` invocation.
2. Automatically load the correct bundled Stage Adapter and return control after its artifact is durable.
3. Let the user interact only through answers and confirmations.
4. Make Skill use transparent without exposing copy/paste orchestration.
5. Prevent gate skipping and production implementation before readiness.
6. Preserve atomic state transitions, regression, recovery, artifact authority, and deterministic validation.

## Non-goals

- Programmatic Python execution of Skills or automatic installation of unrelated Skills.
- A general-purpose project manager or remote tracker writer.
- External publication without authorization.
- Production implementation during preflight.
- Deterministically proving the semantic quality of a human product decision.

## Behavioral requirements

- Select the earliest unsupported Gate even when later artifacts exist.
- Accept one semantic Stage Outcome, derive any Gate or transition internally, and return one orchestration directive from validated state.
- Announce the public capability name before Stage work and after resume.
- Ask one consequential question at a time during discovery and decision work.
- Persist each Gate crossing as one validated atomic transition, while allowing the conversation to continue automatically across Stages.
- Regress to the earliest invalidated Stage and preserve later artifacts as non-authoritative history.
- Stop only for user input, a genuine blocker, cancellation, or readiness.

## Reliability requirements

- **Prompt:** `$project-preflight` owns the loop; adapter instructions forbid asking the user to invoke another Skill.
- **Context:** durable state and artifact pointers make resumption independent of chat history.
- **Tools:** local Markdown is default; remote writes require authorization.
- **Output:** finite values come from the canonical registry; `PreflightSession` accepts no caller-selected target Stage or Gate, and candidates validate before atomic persistence.
- **Failure:** missing adapters, invalid state, and contradictory evidence block advancement with an actionable message.
- **Evaluation:** deterministic tests cover directives, visibility, lifecycle, rollback, atomic writes, Plugin contracts, and behavior fixtures.

## v0.3.2 success criteria

- Plugin and all five Skills pass their official structure validators.
- A rough idea yields a `RUN_STAGE_ADAPTER` directive for the bundled discovery adapter without a user-invoked Handoff.
- All four Stage directives expose the correct public Skill label and a user-visible banner.
- Behavior evals cover automatic routing, missing adapter blocking, adoption, rollback, and final readiness.
- The Handoff experiment remains preserved on its branch while ADR 0003 governs the new branch.
- No current workflow instruction uses `to-prd` or asks the user to paste another Skill command.
- User-visible Stage announcements are available in English and Simplified Chinese without changing routing facts.
- Remote checks revalidate redirects, pin approved public addresses, bound responses, and strip credentials across origins.
- CI verifies tests, exact contract projections, templates, and behavior manifests on Windows and Linux.
- Full happy-path forward tests record tokens and latency and compare them with `evals/budgets.json`.
- Maintainers, CI, and tagged releases share one repository-owned Release Harness.
- Two builds from identical source produce byte-identical Plugin archives and checksums.
- The public-submission inventory contains at least five positive and three negative fresh-context cases.
- Reader-facing status distinguishes source availability, GitHub releases, and the public Plugin Directory.
- Privacy, terms, support, contribution, security, and repository knowledge-authority routes are explicit and verifiable.
- Skill instructions and behavior-eval drivers use the outcome-oriented `PreflightSession` seam while lower-level StateStore commands remain compatible.

## Deferred work

- First-class native Skill composition if Codex exposes a stable dependency API.
- Remote tracker publishing adapters beyond existing read-only evidence checks.
- A synchronization tool for deliberately adopting future upstream workflow improvements.
- Statistical cost and latency distributions after multiple comparable real traces exist.
