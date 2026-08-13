# Project Preflight Repository Guide

## Start here

Read `README.md` and `docs/product-spec.md` before changing behavior. For runtime behavior, treat these files as authoritative:

- `skills/project-preflight/SKILL.md` — orchestration procedure and guardrails.
- `skills/project-preflight/references/workflow.md` — states, routing, and transitions.
- `skills/project-preflight/references/gates.md` — gate criteria.
- `skills/project-preflight/references/artifact-contract.md` — state schema and artifact pointers.
- `skills/project-preflight/references/dependency-contract.md` — upstream Skill and tracker behavior.

Decision records under `docs/decisions/` explain why the contracts exist. They do not override the current contracts.

## Boundaries

- Keep this Skill an orchestrator. Do not copy the behavior or long instructions of `grill-me`, `wayfinder`, `to-spec`, or `to-tickets` into this repository.
- Keep `SKILL.md` concise. Put detailed contracts one level down in `references/`.
- Do not claim that Codex can automatically install Skill dependencies.
- Do not allow production implementation before all readiness gates pass.
- Prefer artifact pointers over duplicated decision, spec, or ticket content.
- Use only the Python standard library for the v0.1 validator and tests.

## Verification

Run from the repository root:

```text
python skills/project-preflight/scripts/validate_preflight.py tests/fixtures/valid-idea.md --repo-root tests/fixtures
python -m unittest discover -s tests -v
python <path-to-skill-creator>/scripts/quick_validate.py skills/project-preflight
git diff --check
```

Also search for the obsolete name `to-prd`. It may appear only in an explicit migration or compatibility note; current workflow instructions must use `to-spec`.
