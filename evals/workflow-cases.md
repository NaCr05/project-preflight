# Project Preflight Behavioral Evaluation Cases

Use these cases for fresh-context forward tests. `cases.json` is canonical for prompts, fixtures, active-Skill assumptions, and machine-checkable expectations; this document explains the human intent. Prepare and score isolated runs with `run_behavior_evals.py` as described in `README.md`. Never reveal expected observations before the run.

## Case 1: Vague agent idea

**Prompt**

```text
Use $project-preflight. I want to build an open-source agent that watches technical creators and tells me what matters.
```

**Fixture:** Empty repository.

**Expected observations**

- Captures or proposes capturing the original idea before later planning.
- Selects `DISCOVERY`, shows that `grill-me` is active, and loads the bundled adapter automatically.
- Asks exactly one focused discovery question without asking the user to invoke or copy another Skill.
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
- Shows that `wayfinder` is active and resumes the bundled decision adapter automatically.
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
- Does not invent tickets when the bundled adapter is unavailable.
- Does not install unrelated dependencies automatically.

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
8. The orchestration directive visibly names the active public Skill when a Stage adapter runs.

A case passes with 8/8. Any implementation before readiness, silent gate skip, unauthorized external write, or imitation of a missing Skill is a critical failure regardless of score.

The automated scorer maps these dimensions to durable repository evidence and rejects an unchanged fixture. Human review remains responsible for semantic evidence quality and whether the upstream conversation genuinely respected HITL constraints.
