# Project Preflight Domain Language

- **Stage** — the single lifecycle position where pre-coding work is currently focused.
- **Gate** — an evidence-backed decision that must pass before the next Stage becomes authoritative.
- **Preflight State** — the canonical `.project/preflight.md` record of the current Stage, Gate statuses, blockers, and Artifact Evidence pointers.
- **Preflight Session** — the outcome-oriented lifecycle boundary that accepts one Stage Outcome and returns validated state plus the next Orchestration Directive. Avoid: state manager, transition helper.
- **Stage Outcome** — one semantic result from active planning work: durable observations recorded, the current Gate passed or blocked, or named artifact evidence invalidated. It never names a target Stage or Gate. Avoid: state patch, transition request.
- **Artifact Evidence** — a durable inline section, repository path, or tracker record used to justify a Gate decision without duplicating the artifact.
- **Stage Adapter** — a bundled, namespaced Skill that supplies one specialist planning capability while Project Preflight retains conversational control.
- **Orchestration Directive** — the runtime result that selects idea capture, one Stage Adapter, a blocker, or readiness from validated state.
- **Skill Visibility Banner** — the compact user-facing notice shown at Stage entry or resume that names the active planning capability.
- **Implementation Handoff** — the terminal output produced after all four Gates pass; it names the canonical spec, approved tickets, first tracer bullet, verification path, and residual risks.
- **Safe Remote Fetch Module** — the shared remote transport policy for public-address pinning, redirect revalidation, credential stripping, and bounded responses.
- **Contract Projection Module** — the exact generated view of finite registry facts used by normative docs, package checks, and eval mapping validation.
- **Announcement Locale** — `en` or `zh-CN`; it changes user-visible wording only, never Stage routing or Gate behavior.
- **Release Harness** — the repository-owned Interface that verifies one source candidate and builds its reproducible Plugin archive for maintainers, CI, and tagged releases. Avoid: release script, CI checklist.

These terms name the stable seams in this repository. Runtime contracts under `skills/project-preflight/references/` explain their behavior; `_contract.py` is canonical for finite state values and mappings, `_session.py` owns outcome interpretation and lifecycle completion, `_orchestration.py` derives directives, `_messages.py`, `_remote.py`, and `_projections.py` own their named concerns, and `scripts/release_harness.py` owns release verification and packaging.
