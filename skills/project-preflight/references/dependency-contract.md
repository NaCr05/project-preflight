# Dependency Contract

Project Preflight composes capabilities that remain independently installed and maintained.

## Direct stage dependencies

| Stage | Required Skill |
|---|---|
| `DISCOVERY` | `grill-me` |
| `DECISION` | `wayfinder` |
| `SPECIFICATION` | `to-spec` |
| `TICKETING` | `to-tickets` |

Check the active Codex Skill catalog first. Do not rely on a fixed global filesystem path. Check only the Skill required for the current stage, while recording the availability of other dependencies when it is already known.

An upstream Skill may have its own transitive capabilities, such as grilling, domain modeling, research, prototypes, or tracker setup. Follow the installed upstream instructions and surface their failures without substituting Project Preflight behavior.

## Missing Skill behavior

When a required Skill is unavailable:

1. Do not imitate or paraphrase it.
2. Keep the current stage and gate unchanged.
3. Record the dependency as `missing` and add an actionable blocker.
4. Name the exact missing Skill and explain which stage it blocks.
5. Offer installation guidance only when a trustworthy source is available; do not install automatically.

## Tracker selection

Use local Markdown by default for v0.1. Reuse a repository's configured tracker when all of these are true:

- the tracker contract is discoverable;
- required tools and authentication are available;
- the user has authorized external publication or it is clearly part of the requested workflow;
- the upstream Skill supports the tracker behavior.

Without those conditions, persist local artifact pointers and do not publish externally.

## Compatibility rule

The installed upstream Skill is authoritative for its own interview, mapping, spec, or ticket behavior. Project Preflight is authoritative only for routing, gates, state, and readiness. If the contracts conflict, stop and report the incompatibility rather than silently overriding either side.

## State vocabulary

Record dependency observations as:

- `available`
- `missing`
- `not_checked`

Do not store credentials, tokens, email addresses, or secret environment values in `.project/preflight.md`.
