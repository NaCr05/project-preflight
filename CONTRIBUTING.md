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
python scripts/release_harness.py verify
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
2. update reader status, product criteria, the knowledge map, and submission evidence when affected;
3. run `python scripts/release_harness.py verify` and the official-validator suite;
4. run `python scripts/release_harness.py build --output dist` twice when changing the package builder and compare checksums;
5. merge through a green CI run;
6. obtain explicit authorization before creating and pushing an annotated `v<version>` tag;
7. verify that the Release workflow publishes the archive and SHA-256 checksum;
8. install the released Plugin in a clean session and run at least the first-turn smoke case;
9. record any full happy-path forward test under `evals/` and enforce its observed metrics with `python evals/run_behavior_evals.py check-budget full-happy-path-high-reasoning --total-tokens <observed-total> --latency-ms <observed-milliseconds>`.

Creating a tag, making the repository public, and submitting to the public Plugin Directory are separate actions. Follow `docs/plugin-submission.md`; none is implied by a source-version bump.
