# Project Preflight Repository Guide

## Start here

Read `README.md` and `docs/product-spec.md` before changing behavior. For runtime behavior, treat these files as authoritative:

- `skills/project-preflight/SKILL.md` — orchestration procedure and guardrails.
- `skills/project-preflight/references/workflow.md` — states, routing, and transitions.
- `skills/project-preflight/references/gates.md` — gate criteria.
- `skills/project-preflight/references/artifact-contract.md` — state schema and artifact pointers.
- `skills/project-preflight/references/orchestration-contract.md` — automatic adapter routing and visible Skill announcements.
- `skills/project-preflight/references/dependency-contract.md` — bundled adapter and tracker behavior.
- `skills/project-preflight/scripts/preflight_runtime/_contract.py` — canonical finite Stage, Gate, artifact, dependency, transition, and adapter mappings.
- `skills/project-preflight/scripts/preflight_runtime/_session.py` — primary outcome-oriented lifecycle Interface; derives Gate, transition/regression, persistence, and next directive.
- `skills/project-preflight/scripts/preflight_runtime/_projections.py` — exact generated contract projections and repository drift checks.
- `skills/project-preflight/scripts/preflight_runtime/_remote.py` — safe remote transport policy shared by Artifact Evidence adapters.
- `docs/knowledge-map.json` — canonical roles, authority, ownership, update triggers, and verification routes for repository knowledge.
- `scripts/release_harness.py` — the shared maintainer, CI, and tagged-release verification and packaging Interface.

Decision records under `docs/decisions/` explain why the contracts exist. They do not override the current contracts.

## Boundaries

- Keep `$project-preflight` the only public workflow entry. Users answer and confirm; never ask them to invoke a stage adapter.
- Keep specialist behavior inside the four namespaced bundled adapter Skills and preserve third-party attribution.
- Show a Skill Visibility Banner at every Stage entry and resumed session.
- Match the Banner locale to the user's language by passing `--locale en` or `--locale zh-CN` to `directive`.
- Keep `SKILL.md` concise. Put detailed contracts one level down in `references/`.
- Mutate `.project/preflight.md` through `PreflightSession` and `StageOutcome`; do not hand-edit frontmatter or select raw target Stages/Gates in new behavior.
- Keep `StateStore` and its low-level CLI commands compatible in v0.3, but do not expand them as the primary orchestration Interface.
- Do not claim that Python programmatically invokes Skills; it derives directives and Codex follows bundled Skill instructions.
- Do not allow production implementation before all readiness gates pass.
- Prefer artifact pointers over duplicated decision, spec, or ticket content.
- Keep the runtime and tests on the Python standard library unless an accepted decision record changes that constraint.
- Keep remote DNS, redirect, credential, timeout, response-size, and content-type policy inside the Safe Remote Fetch Module.
- Change finite contract facts only in `_contract.py`, then refresh marked projections with `sync_contract.py --write`.

## Verification

Run from the repository root:

```text
python scripts/release_harness.py verify
python <path-to-plugin-creator>/scripts/validate_plugin.py .
python <path-to-skill-creator>/scripts/quick_validate.py <each-directory-under-skills>
git diff --check
```

Before a release, compare a full forward test with `evals/budgets.json` and follow `CONTRIBUTING.md` plus `docs/plugin-submission.md`. The Release Harness checks manifest/version drift, the 5+3 submission inventory, knowledge-registry structure, exact projections, templates, tests, and package reproducibility contracts. Also search for the obsolete name `to-prd`. It may appear only in an explicit migration or compatibility note; current workflow instructions must use `to-spec`.
