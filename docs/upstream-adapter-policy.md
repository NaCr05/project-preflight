# Upstream adapter review policy

Project Preflight's four bundled Stage Adapters are original namespaced integrations informed by workflow concepts from Matt Pocock's public `skills` repository. They are not vendored snapshots and are not represented as upstream releases.

## Recorded review baseline

- Upstream repository: <https://github.com/mattpocock/skills>
- Reviewed revision: `8b78b531ab965735c5dc74f6f7a219e1e37326df`
- Upstream revision date: 2026-08-13
- Project Preflight review date: 2026-08-14
- License at review: MIT

Reviewed paths:

| Project Preflight Adapter | Upstream reference |
|---|---|
| `project-preflight-grill-me` | `skills/productivity/grill-me/SKILL.md` |
| `project-preflight-wayfinder` | `skills/engineering/wayfinder/SKILL.md` |
| `project-preflight-to-spec` | `skills/engineering/to-spec/SKILL.md` |
| `project-preflight-to-tickets` | `skills/engineering/to-tickets/SKILL.md` |

The revision is a review baseline, not a claim that Project Preflight copied those files verbatim.

## Adoption workflow

1. Compare the recorded revision with the new upstream revision.
2. Classify each change as behavior, terminology, platform metadata, or implementation detail.
3. Adopt only changes that preserve Project Preflight's single-entry Plugin contract and artifact authority.
4. Update the appropriate bundled Adapter rather than copying an entire upstream Skill blindly.
5. Update tests and behavior cases before changing this baseline.
6. Run a fresh-context forward test when question pacing, automatic return, artifact shape, or readiness behavior changes.
7. Record the new revision, review date, adopted changes, and rejected changes in the pull request and `CHANGELOG.md`.

Do not build an automatic synchronization tool until at least two real review cycles demonstrate a stable, repeatable transformation.
