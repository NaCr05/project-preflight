# Behavior Evaluation Harness

`cases.json` is the canonical manifest for eight behavior cases: five positive intended-use cases and three negative safety/boundary cases required by the public-submission preparation. It also owns isolated fixtures, bundled-adapter assumptions, expected state, and the eight-point rubric. `workflow-cases.md` explains the intent for human reviewers. Dated result files are evidence, not normative contracts.

## Reproduce a case

List the cases:

```text
python evals/run_behavior_evals.py list
```

Prepare an isolated workspace:

```text
python evals/run_behavior_evals.py prepare vague-idea <empty-output-directory>
```

The prepared directory contains:

- `case.json` — the prompt and active-Skill assumptions visible to the evaluator;
- `workspace/` — the isolated repository fixture where the evaluator runs;
- `baseline.json` — file hashes used to reject a no-op run.

After a fresh-context evaluator completes the prompt, score the durable result:

```text
python evals/run_behavior_evals.py score <prepared-directory> \
  --model <model-name> \
  --dependency-version project-preflight=<version-or-commit> \
  --total-tokens <observed-total> \
  --latency-ms <observed-milliseconds>
```

The scorer writes `result.json` and `result.md`. Both include the date, model, dependency versions, optional tokens, latency and cost, validator findings, baseline/result fingerprints, each rubric check, and critical failures.

## Cost and latency budget

`budgets.json` records the first comparable full happy-path baseline and the release regression ceilings. A new full run above either ceiling requires investigation and an explicitly accepted result before release. Always record the model and reasoning effort on future runs; the initial v0.3.0 baseline did not capture the exact model and therefore supports regression triage, not cross-model performance claims.

After a comparable full run, enforce both ceilings with the observed metrics:

```text
python evals/run_behavior_evals.py check-budget full-happy-path-high-reasoning \
  --total-tokens <observed-total> \
  --latency-ms <observed-milliseconds>
```

The command exits nonzero if either ceiling is exceeded. Accepting a regression requires updating the policy evidence and recording the rationale in the release notes or an ADR; do not bypass the check silently.

## Evidence boundary

The scorer deterministically checks Stage selection, dependency observations, Gate statuses, Artifact Evidence preservation, production-code guardrails, state validity, one changed Next Action, and the expected user-visible Skill directive. It does not prove that product decisions or prose are semantically good. A real behavior or submission claim still requires a fresh-context evaluator; a deterministic test driver proves only that the eval module and fixtures work.

## Recorded runs

- [2026-08-14 automatic orchestration validation](results-2026-08-14-automatic-orchestration.md) covers Plugin packaging, all Stage directives, visible Skill announcements, and a fresh-context single-entry response.
- [2026-08-14 Handoff and lifecycle validation](results-2026-08-14.md) is retained as evidence for the experimental branch. ADR 0003 supersedes its user-invoked routing while keeping the validated Gate 2-4, regression, atomic-write, and readiness results.
