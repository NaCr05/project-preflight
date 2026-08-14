# Behavior Evaluation Harness

`cases.json` is the canonical manifest for the five behavior cases, their isolated fixtures, active-Skill assumptions, expected state, and seven-point rubric. `workflow-cases.md` explains the intent for human reviewers. Dated result files are evidence, not normative contracts.

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
  --dependency-version project-preflight=<version-or-commit>
```

The scorer writes `result.json` and `result.md`. Both include the date, model, dependency versions, optional latency and cost, validator findings, baseline/result fingerprints, each rubric check, and critical failures.

## Evidence boundary

The scorer deterministically checks Stage selection, dependency observations, Gate statuses, Artifact Evidence preservation, production-code guardrails, state validity, and one changed Next Action. It does not prove that product decisions or prose are semantically good. A real behavior claim still requires a fresh-context evaluator; a deterministic test driver proves only that the eval module and fixtures work.

## Recorded runs

- [2026-08-14 Handoff and lifecycle validation](results-2026-08-14.md) separates two live user-invoked Handoffs from the deterministic Gate 2-4, regression, atomic-write, and readiness checks that followed.
