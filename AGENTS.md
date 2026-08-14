# Project Preflight Repository Guide

## Start here

Read `README.md` and `docs/product-spec.md` before changing behavior. For runtime behavior, treat these files as authoritative:

- `skills/project-preflight/SKILL.md` — orchestration procedure and guardrails.
- `skills/project-preflight/references/workflow.md` — states, routing, and transitions.
- `skills/project-preflight/references/gates.md` — gate criteria.
- `skills/project-preflight/references/artifact-contract.md` — state schema and artifact pointers.
- `skills/project-preflight/references/dependency-contract.md` — upstream Skill and tracker behavior.
- `skills/project-preflight/scripts/preflight_runtime/_contract.py` — canonical finite Stage, Gate, artifact, dependency, transition, and handoff mappings.

Decision records under `docs/decisions/` explain why the contracts exist. They do not override the current contracts.

## Boundaries

- Keep this Skill an orchestrator. Do not copy the behavior or long instructions of `grill-me`, `wayfinder`, `to-spec`, or `to-tickets` into this repository.
- Keep upstream routing as an explicit user-invoked handoff. Do not invoke an upstream Skill inside a Project Preflight run.
- Keep `SKILL.md` concise. Put detailed contracts one level down in `references/`.
- Mutate `.project/preflight.md` only through the State lifecycle interface; do not hand-edit frontmatter.
- Do not claim that Codex can automatically install Skill dependencies.
- Do not allow production implementation before all readiness gates pass.
- Prefer artifact pointers over duplicated decision, spec, or ticket content.
- Use only the Python standard library for the v0.1 validator and tests.

## Verification

Run from the repository root:

```text
python skills/project-preflight/scripts/validate_preflight.py tests/fixtures/valid-idea.md --repo-root tests/fixtures
python skills/project-preflight/scripts/preflight_state.py template --check skills/project-preflight/assets/preflight-template.md
python -m unittest discover -s tests -v
python evals/run_behavior_evals.py list
python <path-to-skill-creator>/scripts/quick_validate.py skills/project-preflight
git diff --check
```

Also search for the obsolete name `to-prd`. It may appear only in an explicit migration or compatibility note; current workflow instructions must use `to-spec`.
