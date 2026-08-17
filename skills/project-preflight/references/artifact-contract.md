# Artifact and State Contract

## Contents

1. [Canonical state](#canonical-state)
2. [Frontmatter schema](#frontmatter-schema)
3. [Artifact pointers](#artifact-pointers)
4. [Stage invariants](#stage-invariants)
5. [Human-readable evidence](#human-readable-evidence)
6. [Write and recovery rules](#write-and-recovery-rules)

## Canonical state

Use exactly one project-scoped state file:

```text
.project/preflight.md
```

Create and mutate it through the `PreflightSession` Interface exposed by `scripts/preflight_state.py`. YAML frontmatter is canonical for finite state; the Markdown body is canonical for explanations, evidence summaries, blockers, and the next action. Do not maintain a parallel status file or hand-edit the frontmatter.

`scripts/preflight_runtime/_contract.py` is canonical for finite Stage, Gate, artifact, dependency, transition, and adapter mappings. `scripts/preflight_runtime/_orchestration.py` derives user-visible directives from that registry. `assets/preflight-template.md` is derived from the registry and must match `preflight_state.py template --check`.

## Frontmatter schema

Use this restricted YAML subset: top-level scalar fields plus two-space-indented scalar maps. Do not use arrays, aliases, tags, or multiline YAML values.

```yaml
---
schema_version: 1
project: "example-project"
current_stage: "DISCOVERY"
previous_stage: "IDEA"
last_transition: "2026-08-13T08:00:00Z"
transition_reason: "Captured the original idea"
tracker: "local-markdown"
ready_for_implementation: false
gates:
  gate_1: "not_evaluated"
  gate_2: "not_evaluated"
  gate_3: "not_evaluated"
  gate_4: "not_evaluated"
artifacts:
  idea: "inline:#original-idea"
  decision_map: null
  spec: null
  tickets: null
dependencies:
  grill-me: "available"
  wayfinder: "not_checked"
  to-spec: "not_checked"
  to-tickets: "not_checked"
---
```

Allowed stages are `IDEA`, `DISCOVERY`, `DECISION`, `SPECIFICATION`, `TICKETING`, and `READY_FOR_IMPLEMENTATION`.

The `gates`, `artifacts`, and `dependencies` maps must contain exactly the keys shown. The State lifecycle module renders them in canonical registry order, while validation remains compatible with an existing v0.1 file whose mapping keys use a different order.

## Artifact pointers

Each artifact value is one of:

- `null` when not produced yet;
- a repository-relative file or directory path, optionally followed by a Markdown anchor;
- an `http://` or `https://` tracker URL;
- `inline:#section-anchor` when the state file itself contains the artifact;
- `not-required` only for `decision_map`, with an explanation in Gate 2 evidence.

Do not place artifact content in frontmatter. Do not use absolute local paths because another contributor or CI run cannot resolve them.

Artifact Evidence is checked through one adapter seam:

| Pointer | Adapter behavior |
|---|---|
| `inline:#anchor` | Verify that the state body contains the anchor and required content. |
| Repository-relative path | Verify containment, existence, readability, and a Markdown anchor when supplied. |
| GitHub Issue URL | Verify Issue syntax; with `--check-remote`, query the GitHub Issue record. |
| Other HTTP(S) URL | Report that semantic sufficiency is unverified; with `--check-remote`, also check accessibility. |

Local pointers required for the current Stage must exist. A reachable URL proves location and accessibility, not semantic sufficiency; the Gate still requires human review of the evidence. Remote checking is read-only. The Safe Remote Fetch Module rejects localhost and non-public targets, pins an approved address, revalidates every redirect, bounds response size and time, and strips credentials on cross-origin redirects. The GitHub Issue Adapter may use `GH_TOKEN` or `GITHUB_TOKEN` without storing either value.

## Stage invariants

The current stage must match the first gate that has not passed:

<!-- project-preflight:generated stage-invariant-table:start -->
| Current stage | Required passed gates | Required artifact pointers |
|---|---|---|
| `IDEA` | None | None |
| `DISCOVERY` | None | `idea` |
| `DECISION` | Gate 1 | `idea` |
| `SPECIFICATION` | Gates 1–2 | `idea`, `decision_map` |
| `TICKETING` | Gates 1–3 | `idea`, `decision_map`, `spec` |
| `READY_FOR_IMPLEMENTATION` | Gates 1–4 | `idea`, `decision_map`, `spec`, `tickets` |
<!-- project-preflight:generated stage-invariant-table:end -->

At non-ready stages, the gate owned by that stage must not already be `passed`. Later gates must not be passed either. `ready_for_implementation` is true if and only if the current stage is `READY_FOR_IMPLEMENTATION`.

`previous_stage` may be null only for reconstructed or initial state. Otherwise it must form an allowed transition with `current_stage`, and `transition_reason` must explain the change.

## Human-readable evidence

Keep these headings:

```markdown
# Project Preflight

## Original Idea

## Gate Evidence

### Gate 1
### Gate 2
### Gate 3
### Gate 4

## Blockers

## Next Action
```

For a passed gate, its section must contain durable evidence or pointers and must not say only `Not evaluated.` For blocked or invalidated gates, record the reason and the evidence needed to continue.

The Original Idea section may be the canonical idea through `inline:#original-idea`. Keep it concise and preserve the user's intent; later refinement belongs in upstream artifacts.

## Write and recovery rules

1. Read and validate the current file through `PreflightSession.current()`.
2. Gather new evidence.
3. Build one semantic `StageOutcome` without a target Stage or Gate.
4. Let `PreflightSession.apply()` derive the Gate, transition or regression, and complete candidate state.
5. Let the module atomically replace the old state only after validation passes.
6. If an operation fails, keep the last valid file unchanged. Use `recover --source <valid-state>` only with an explicitly chosen valid recovery source. The lower-level `record`, `advance`, and `regress` commands remain compatibility paths, not the primary Skill workflow.

Never delete historical upstream artifacts during regression. Change their authority by invalidating the relevant gate and updating pointers only when a replacement becomes canonical.

If state and repository evidence disagree, treat repository or tracker canonical artifacts as evidence, but do not silently rewrite state. Report the discrepancy and make the synchronization explicit.
