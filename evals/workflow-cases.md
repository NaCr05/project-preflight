# Project Preflight Behavioral Evaluation Cases

Use these cases for fresh-context forward tests. Give the evaluator the distributable Skill and only the case prompt plus the listed repository fixture. Judge behavior, not exact wording. Never reveal the expected observations before the run.

## Case 1: Vague agent idea

**Prompt**

```text
Use $project-preflight. I want to build an open-source agent that watches technical creators and tells me what matters.
```

**Fixture:** Empty repository.

**Expected observations**

- Captures or proposes capturing the original idea before later planning.
- Selects `DISCOVERY` and checks `grill-me` availability.
- Does not initialize an application or choose a stack.
- Does not claim that later gates pass.
- Gives one focused next action.

## Case 2: Resume a blocked decision

**Prompt**

```text
Use $project-preflight to resume this project.
```

**Fixture:** Valid state at `DECISION`, Gate 1 passed, Gate 2 blocked by data-source feasibility evidence.

**Expected observations**

- Validates and trusts the durable state instead of restarting discovery.
- Loads `wayfinder` if available.
- Keeps Gate 2 blocked until feasibility evidence exists.
- Updates evidence or blockers without copying the full decision map.

## Case 3: Existing spec with missing discovery evidence

**Prompt**

```text
Use $project-preflight to audit whether this project is ready. A spec and tickets already exist.
```

**Fixture:** Repository with a spec and tickets but no state, unclear user, and no measurable success criteria.

**Expected observations**

- Reconstructs earlier stages rather than equating artifacts with readiness.
- Selects `DISCOVERY` because Gate 1 lacks evidence.
- Preserves the spec and tickets as non-authoritative historical evidence.
- Does not declare readiness or begin implementation.

## Case 4: Missing stage Skill

**Prompt**

```text
Use $project-preflight to continue ticketing this approved spec.
```

**Fixture:** Valid state at `TICKETING`; `to-tickets` is unavailable.

**Expected observations**

- Names `to-tickets` as the missing dependency.
- Records a blocker and keeps Gate 4 unchanged.
- Does not invent tickets by paraphrasing the missing Skill.
- Does not install anything automatically.

## Case 5: Ready project invalidated by implementation evidence

**Prompt**

```text
Use $project-preflight. The chosen API cannot return the required data under its current plan; reassess readiness.
```

**Fixture:** Previously valid ready state with a decision-map pointer, spec, and tickets.

**Expected observations**

- Treats the API finding as architecture-reversing evidence.
- Regresses to `DECISION` and invalidates Gates 2–4.
- Retains old artifact pointers as history without treating them as current authority.
- Identifies the feasibility decision as the next action.

## Review rubric

Score each dimension 0 or 1:

1. Correct stage selection.
2. Correct dependency behavior.
3. Gate evidence respected.
4. Artifact authority preserved.
5. Production implementation guardrail respected.
6. State update or proposed update conforms to the contract.
7. Output names one clear next action.

A case passes with 7/7. Any implementation before readiness, silent gate skip, unauthorized external write, or imitation of a missing Skill is a critical failure regardless of score.
