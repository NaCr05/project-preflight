# Contributing to Project Preflight

Thanks for helping make pre-coding planning more reliable. Project Preflight is an agent-intensive repository: prompts, contracts, state logic, documentation, and evals are all product behavior.

## Before you start

- Use Python 3.11 or newer. The runtime intentionally uses only the standard library.
- Read `AGENTS.md`, `CONTEXT.md`, `docs/product-spec.md`, and the current ADRs.
- Keep `$project-preflight` as the only public workflow entry.
- Do not ask users to invoke a bundled Stage Adapter.
- Do not implement production application code during Preflight.

Open an issue before a large behavior or state-schema change. Security reports follow `SECURITY.md`, not public issues.

## Development workflow

1. Create a focused branch from `main`.
2. Change the smallest authoritative source. Finite Stage, Gate, artifact, dependency, transition, and Adapter facts belong in `_contract.py`.
3. Run `python skills/project-preflight/scripts/sync_contract.py --write` after changing canonical finite facts. Review every generated change.
4. Add or update tests through the affected Module Interface.
5. Update an ADR when the change alters a durable architectural decision.
6. Keep English and Simplified Chinese reader documentation synchronized.

## Required verification

Run from the repository root:

```text
python -m compileall -q skills evals tests
python -m unittest discover -s tests -v
python skills/project-preflight/scripts/sync_contract.py --check
python skills/project-preflight/scripts/preflight_state.py template --check skills/project-preflight/assets/preflight-template.md
python evals/run_behavior_evals.py list
git diff --check
```

Also run the Codex Plugin validator on the repository root and Skill Creator validation on every directory under `skills/`. These official validators are part of the maintainer release check; CI cannot assume their local system paths.

## Pull requests

Describe:

- the observed problem;
- the authoritative files changed;
- user-visible behavior before and after;
- checks actually run;
- residual risk, especially for prompts, remote access, state transitions, cost, and latency.

Do not include generated caches, local state, credentials, test transcripts containing private content, or unrelated formatting changes.

## Releases

Maintainers:

1. update `.codex-plugin/plugin.json` and `CHANGELOG.md` with the same semantic version;
2. run the complete local and official-validator suite;
3. merge through a green CI run;
4. create and push an annotated `v<version>` tag;
5. verify that the Release workflow publishes the archive and SHA-256 checksum;
6. install the released Plugin in a clean session and run at least the first-turn smoke case;
7. record any full happy-path forward test under `evals/` and enforce its observed metrics with `python evals/run_behavior_evals.py check-budget full-happy-path-high-reasoning --total-tokens <observed-total> --latency-ms <observed-milliseconds>`.
