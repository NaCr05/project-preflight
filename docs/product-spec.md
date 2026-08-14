# Project Preflight v0.2 Product Specification

## Purpose

Project Preflight is a Codex Skill that reliably moves a software project from incomplete planning to an implementation-ready ticket frontier. It supplies explicit user-invoked Handoff orchestration around specialized planning Skills without internally invoking, copying, or replacing them.

## Intended users

- Solo developers shaping an open-source project.
- Maintainers resuming planning across several Codex sessions.
- AI or agent project builders who need explicit prompt, context, tool, memory, failure, cost, latency, and reliability checks before coding.
- Contributors auditing an existing spec and ticket set before implementation.

## Inputs

- A vague idea, existing repository, or both.
- Existing planning artifacts when available.
- Planning Skills exposed in the active catalog and an optional configured issue tracker.
- Human answers for decisions that require product judgment.

## Outputs

- One canonical `.project/preflight.md` state file in the target project.
- Durable pointers to the idea, decision map, specification, and ticket set.
- Evidence-backed gate decisions and explicit blockers.
- One exact upstream Skill invocation and return instruction at each non-terminal Stage.
- A `READY_FOR_IMPLEMENTATION` handoff naming the first unblocked tracer bullet and its verification path.

## Goals

1. Resume planning without replaying a long conversation.
2. Produce an explicit Handoff from each unresolved Stage to the appropriate active Skill.
3. Prevent silent gate skipping and speculative production implementation.
4. Preserve upstream artifacts in their native tracker or file location.
5. Detect invalid state, broken local pointers, contradictory readiness, and illegal transitions deterministically.
6. Regress safely when implementation or research invalidates an earlier assumption.
7. Prevent invalid or partial state writes by validating complete candidates before atomic replacement.

## Non-goals

- Reimplementing `grill-me`, `wayfinder`, `to-spec`, or `to-tickets`.
- Automatically installing or internally invoking Skills, or modifying the user's global Codex environment.
- Providing a general-purpose project manager or issue tracker.
- Implementing product features in the target repository.
- Automatically publishing to GitHub, Linear, or another external tracker without authorization.
- Proving the semantic quality of a product decision using deterministic code alone.

## Behavioral requirements

The runtime contracts under `skills/project-preflight/references/` define the exact behavior. At minimum, the Skill must:

- inspect existing repository evidence before creating state;
- select the earliest unsupported gate even when later artifacts exist;
- check stage-specific dependencies before routing;
- produce one exact explicit Handoff and stop until the user returns;
- record pointers rather than duplicate upstream content;
- mutate state only through the State lifecycle interface;
- expose failures and remain at the current stage when evidence is insufficient;
- allow explicit rollback to the earliest invalidated stage;
- require all four gates before readiness.

## AI and agent reliability requirements

- **Prompt:** Each routed Stage must emit an exact explicit invocation for the active upstream Skill rather than internally calling or paraphrasing it.
- **Context:** The state file must identify canonical artifacts and blockers without requiring conversation history.
- **Tools:** Remote writes require existing configuration and user authorization; local Markdown is the default.
- **Output:** Stage and Gate values use the canonical finite registry and are validated before atomic persistence.
- **Memory:** State is project-scoped, contains no credentials, and treats broken or stale pointers as blockers.
- **Failure handling:** Missing dependencies, invalid state, and conflicting evidence stop advancement with an actionable message.
- **Evaluation:** Deterministic tests cover schema and transition integrity; behavioral cases cover routing, resumption, adoption, dependency failure, and rollback.
- **Cost and latency:** The Skill loads detailed references only when needed and avoids rereading every upstream artifact on every turn.

## v0.2 success criteria

- The distributable Skill passes the official Skill structure validator.
- The State lifecycle interface accepts valid IDEA and READY examples, prevents invalid replacement, and safely regresses invalidated readiness.
- A fresh agent can correctly start, resume, and audit preflight using only repository artifacts and the Skill.
- The five behavior cases can be prepared, scored, and recorded through one reproducible eval interface.
- No runtime instruction uses the obsolete `to-prd` name.
- The Skill reaches readiness only when four gates pass and all required artifact pointers are present.

## Deferred work

- Automated Skill installation.
- Tracker-specific publishing adapters beyond the read-only GitHub Issue evidence adapter.
- A generated visual dashboard.
- Organization-wide policy packs.
- Statistical benchmarks for model cost and latency after real usage traces exist.
