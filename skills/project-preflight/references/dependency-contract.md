# Dependency Contract

Project Preflight composes capabilities that remain independently installed and maintained.

## Direct stage dependencies

| Stage | Required Skill |
|---|---|
| `DISCOVERY` | `grill-me` |
| `DECISION` | `wayfinder` |
| `SPECIFICATION` | `to-spec` |
| `TICKETING` | `to-tickets` |

Check the active Codex Skill catalog first. Do not rely on a fixed global filesystem path: files on disk do not prove that the current session can explicitly invoke a Skill. Check only the Skill required for the current Stage, while recording other observations when already known.

Project Preflight uses **handoff orchestration**. Even when a dependency is available, do not invoke it internally. Generate the exact `$skill-name` instruction with `scripts/preflight_state.py handoff`, show it to the user, and stop. The instruction must return the user to `$project-preflight` after a durable result exists. This explicit invocation is required for upstream Skills that disable model invocation and remains the rule for all four dependencies.

An upstream Skill may have its own transitive capabilities, such as grilling, domain modeling, research, prototypes, or tracker setup. When the user invokes it, that Skill follows its own instructions; Project Preflight surfaces returned failures without substituting its behavior.

## Missing Skill behavior

When a required Skill is unavailable:

1. Do not imitate or paraphrase it.
2. Keep the current stage and gate unchanged.
3. Record the dependency as `missing` and add an actionable blocker.
4. Name the exact missing Skill and explain which stage it blocks.
5. If files exist but the Skill is absent from the active catalog, explain that the environment may need installation, reload, or a new session; do not record it as `available`.
6. Offer installation guidance only when a trustworthy source is available; do not install automatically.

## Tracker selection

Use local Markdown by default. Reuse a repository's configured tracker when all of these are true:

- the tracker contract is discoverable;
- required tools and authentication are available;
- the user has authorized external publication or it is clearly part of the requested workflow;
- the upstream Skill supports the tracker behavior.

Without those conditions, persist local artifact pointers and do not publish externally.

## Compatibility rule

The explicitly invoked upstream Skill is authoritative for its own interview, mapping, spec, or ticket behavior. Project Preflight is authoritative only for handoff routing, Gates, state, and readiness. If the contracts conflict, stop and report the incompatibility rather than silently overriding either side.

## State vocabulary

Record dependency observations as:

- `available` — present in the active catalog and explicitly invokable by the user;
- `missing`
- `not_checked`

Do not store credentials, tokens, email addresses, or secret environment values in `.project/preflight.md`.
