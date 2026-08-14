# Project Preflight Domain Language

- **Stage** — the single lifecycle position where pre-coding work is currently focused.
- **Gate** — an evidence-backed decision that must pass before the next Stage becomes authoritative.
- **Preflight State** — the canonical `.project/preflight.md` record of the current Stage, Gate statuses, blockers, and Artifact Evidence pointers.
- **Artifact Evidence** — a durable inline section, repository path, or tracker record used to justify a Gate decision without duplicating the artifact.
- **Stage Adapter** — a bundled, namespaced Skill that supplies one specialist planning capability while Project Preflight retains conversational control.
- **Orchestration Directive** — the runtime result that selects idea capture, one Stage Adapter, a blocker, or readiness from validated state.
- **Skill Visibility Banner** — the compact user-facing notice shown at Stage entry or resume that names the active planning capability.
- **Implementation Handoff** — the terminal output produced after all four Gates pass; it names the canonical spec, approved tickets, first tracer bullet, verification path, and residual risks.
- **Safe Remote Fetch Module** — the shared remote transport policy for public-address pinning, redirect revalidation, credential stripping, and bounded responses.
- **Contract Projection Module** — the exact generated view of finite registry facts used by normative docs, package checks, and eval mapping validation.
- **Announcement Locale** — `en` or `zh-CN`; it changes user-visible wording only, never Stage routing or Gate behavior.

These terms name the stable seams in this repository. Runtime contracts under `skills/project-preflight/references/` explain their behavior; `_contract.py` is canonical for finite state values and mappings, `_orchestration.py` derives directives, and `_messages.py`, `_remote.py`, and `_projections.py` own their named concerns.
