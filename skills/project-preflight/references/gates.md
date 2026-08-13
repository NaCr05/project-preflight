# Gate Contract

Use the finite statuses `not_evaluated`, `blocked`, `passed`, and `invalidated`. Record concrete evidence for every passed gate and an actionable reason for every blocked or invalidated gate.

## Gate 1: Problem clarity

Pass only when durable evidence identifies:

- the target user or actor;
- the situation and problem;
- the promised value and core mechanism;
- primary inputs and outputs;
- the initial MVP boundary and explicit non-goals;
- measurable success criteria;
- material assumptions;
- why an agent is or is not required.

The project should be explainable in one concise statement, but writing quality alone is not proof. Missing input, output, scope, or success evidence blocks the gate.

## Gate 2: Decision readiness

Pass only when:

- architecture-reversing decision points have recorded resolutions;
- unresolved decisions are explicitly shown to be non-blocking;
- core data or API feasibility has evidence;
- relevant access, price, rate-limit, privacy, security, and compliance constraints have been considered;
- runtime, persistence, interface, model, tool, context, memory, and failure boundaries are decided when applicable;
- there is no known assumption likely to force an immediate redesign.

Use `not-required` for the decision-map pointer only when the effort is small enough that no decision map is justified and the Gate 2 evidence explains why.

## Gate 3: Specification readiness

Pass only when the canonical spec defines:

- problem and user-facing solution;
- numbered user stories or equivalent observable behaviors;
- implementation and interface decisions at stable seams;
- testing decisions based on external behavior;
- MVP scope and out-of-scope work;
- success criteria and relevant edge or failure cases;
- open questions, none of which block ticketing.

A reviewer must be able to classify any proposed feature as in scope or out of scope without inventing a new product decision.

## Gate 4: Execution readiness

Pass only when:

- the ticket set points back to the canonical spec;
- each ticket is a narrow, complete, independently verifiable vertical slice;
- each ticket has observable acceptance criteria;
- blocking edges are explicit and represent genuine prerequisites;
- at least one unblocked frontier ticket exists;
- the first tracer bullet crosses the minimum useful end-to-end path;
- no ticket silently adds behavior outside the spec;
- verification commands or evaluation paths are identified.

Horizontal infrastructure work may be separate only when a documented expand-contract or prefactoring constraint makes a vertical slice impossible.

## Evidence rules

- Prefer repository files, tracker records, prototypes, tests, and research results over conversation summaries.
- Use artifact pointers instead of copying full decisions or requirements into the state file.
- A URL may be evidence without being locally reachable, but mark it blocked if the current agent cannot access information required to judge it.
- Never pass a gate to reward progress. Pass it only when its contract is satisfied.
- When evidence conflicts, keep the gate blocked and identify the canonical source that must be corrected.
