# Project Preflight Domain Language

- **Stage** — the single lifecycle position where pre-coding work is currently focused.
- **Gate** — an evidence-backed decision that must pass before the next Stage becomes authoritative.
- **Preflight State** — the canonical `.project/preflight.md` record of the current Stage, Gate statuses, blockers, and Artifact Evidence pointers.
- **Artifact Evidence** — a durable inline section, repository path, or tracker record used to justify a Gate decision without duplicating the artifact.
- **Handoff** — the explicit user-invoked transfer from Project Preflight to one upstream planning Skill, followed by an explicit return to `$project-preflight`.
- **Implementation Handoff** — the terminal output produced after all four Gates pass; it names the canonical spec, approved tickets, first tracer bullet, verification path, and residual risks.

These terms name the stable seams in this repository. Runtime contracts under `skills/project-preflight/references/` explain their behavior; `skills/project-preflight/scripts/preflight_runtime/_contract.py` is canonical for finite state values and mappings.
