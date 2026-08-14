# ADR 0003: Ship a Plugin with single-entry automatic orchestration

- **Status:** Accepted
- **Date:** 2026-08-14
- **Supersedes:** ADR 0002's explicit Handoff orchestration
- **Retains:** ADR 0002's State lifecycle, canonical registry, evidence adapters, and evaluation seam

## Context

The Handoff experiment proved that the four planning stages, Gates, regression, and atomic persistence work. It also showed a product-level cost: users had to copy a generated Skill command, invoke it, and manually resume Project Preflight after every stage. That exposed implementation boundaries instead of providing one coherent planning experience.

Codex Plugins can package multiple Skills. The upstream Skills used for the experiment currently disable implicit invocation, so depending on separate installations cannot provide a reliable automatic flow. There is also no supported Python `call_skill()` primitive; orchestration must remain instruction-driven inside Codex rather than claiming that the state runtime executes Skills.

## Decision

Project Preflight will ship as one Plugin with:

1. one public entry, `$project-preflight`;
2. four bundled, namespaced stage-adapter Skills for `grill-me`, `wayfinder`, `to-spec`, and `to-tickets` behavior;
3. a runtime directive interface that maps validated state to `CAPTURE_IDEA`, `RUN_STAGE_ADAPTER`, `BLOCKED`, or `READY`;
4. automatic return from each adapter to the orchestrator after durable evidence exists;
5. a mandatory visibility banner at every Stage entry and resumed session naming the capability currently in use.

The user answers questions and confirms choices. They are never asked to invoke an internal adapter or paste a generated command.

The adapters are namespaced to avoid collisions with independently installed upstream Skills. Their instructions are tailored integrations, with upstream inspiration and MIT attribution recorded in `THIRD_PARTY_NOTICES.md`.

## Consequences

- One invocation can carry a project from a rough paragraph to implementation readiness.
- Skill boundaries remain visible without becoming user-operated workflow steps.
- State routing and conversation execution remain separate, testable seams.
- The Plugin is self-contained for its core planning path.
- A conversation may cross several Gates, but every Gate still uses one validated atomic transition.
- Internal adapters appear as Plugin Skills because the current manifest has no hidden-Skill field; namespacing and descriptions mark them as internal.

## Rejected alternatives

### Keep explicit Handoff as the main UX

Rejected because repeated invocation and copy/paste adds work without adding meaningful approval control; users already approve decisions in the interview.

### Depend on separate upstream Skill installations

Rejected because their invocation policies and versions are outside this Plugin's control and can make the happy path unavailable.

### Claim the Python runtime invokes Skills

Rejected because the runtime only derives directives. Codex loads and follows Skill instructions.

### Copy upstream Skills under their original names

Rejected because duplicate names collide with independent installations and obscure provenance.

## Reopen when

- Codex introduces first-class Skill dependency metadata or a hidden internal-Skill facility;
- native composition provides stronger execution guarantees than instruction-driven adapters;
- adapter divergence from upstream behavior creates a maintenance cost that warrants a synchronization tool.
