# Public Plugin Directory Submission Packet

This is the maintained submission-preparation record for Project Preflight. The source repository is public, and the tagged `v0.3.2` GitHub Release is public. The Plugin has not been submitted or accepted by the public Plugin Directory.

## Current status

| Item | Status | Evidence or next action |
|---|---|---|
| Skills-only Plugin structure | Ready locally | `.codex-plugin/plugin.json` and five Skill directories |
| Repository-owned verification | Ready locally | `python scripts/release_harness.py verify` |
| Reproducible release archive | Ready locally | `python scripts/release_harness.py build --output dist` |
| 5 positive and 3 negative test cases | Prepared | `evals/cases.json` |
| Privacy, terms, and support pages | Prepared in repository | `docs/privacy.md`, `docs/terms.md`, `SUPPORT.md` |
| Public website URLs | Ready | Anonymous HTTPS checks pass for the repository, support, privacy, and terms pages |
| Private vulnerability reporting | Ready | Enabled on the public GitHub repository |
| Developer or business verification | External action required | Complete in the OpenAI submission flow |
| GitHub tagged release | Ready | `v0.3.2` with deterministic archive and SHA-256 record |
| Public Plugin Directory submission | Not authorized in this change | Submit only after all external checks pass |

## Proposed listing

- **Name:** Project Preflight
- **Category:** Productivity
- **Short description:** Turn a rough software idea into an implementation-ready plan.
- **Long description:** Invoke Project Preflight once. It visibly coordinates discovery, architecture decisions, specification, and ticketing while preserving durable evidence and preventing implementation before four readiness Gates pass.
- **Developer:** NaCr05
- **Support URL:** <https://github.com/NaCr05/project-preflight/blob/main/SUPPORT.md>
- **Privacy URL:** <https://github.com/NaCr05/project-preflight/blob/main/docs/privacy.md>
- **Terms URL:** <https://github.com/NaCr05/project-preflight/blob/main/docs/terms.md>

## Starter prompts

1. `Use $project-preflight. I want to build an open-source tool that summarizes what matters from a few technical creators.`
2. `Use $project-preflight to audit this existing project and continue from the earliest unsupported Gate.`
3. `Use $project-preflight. I have a rough one-paragraph idea and want to know whether it is ready to implement.`

## Submission test inventory

The machine-readable manifest is canonical. Positive cases demonstrate intended invocations; negative cases demonstrate refusal or safe blocking when a user attempts to bypass the workflow or a required capability is absent.

| Kind | Case id | Purpose |
|---|---|---|
| Positive | `vague-idea` | Start from an immature paragraph |
| Positive | `blocked-decision` | Resume durable decision work |
| Positive | `existing-spec-missing-discovery` | Adopt an existing repository without trusting later artifacts blindly |
| Positive | `ready-invalidated` | Regress when new evidence reverses a decision |
| Positive | `ready-handoff` | Present a valid terminal implementation handoff |
| Negative | `missing-stage-skill` | Block when a required bundled Adapter is unavailable |
| Negative | `skip-gates-request` | Refuse a user request to skip readiness Gates |
| Negative | `implement-before-ready` | Refuse production implementation during Preflight |

## Maintainer submission checklist

1. Recheck the public repository and every listing URL without authentication before submission.
2. Run `python scripts/release_harness.py verify` and both official Plugin and Skill validators.
3. Run the eight fresh-context behavior cases without exposing expected outcomes to the execution task; retain machine-readable and Markdown results.
4. Compare any full real happy path with `evals/budgets.json` and investigate a budget breach.
5. Confirm that GitHub private vulnerability reporting remains enabled and that `SECURITY.md` matches it.
6. Use the current tagged release, confirm its archive checksum, and repeat clean-session installation if submission occurs after runtime changes.
7. Complete developer verification, listing metadata, and submission in the official OpenAI flow.

Official references: [Build plugins](https://developers.openai.com/plugins/build/plugins), [Submit a plugin](https://developers.openai.com/plugins/deploy/submission), and [Plugin user guide](https://learn.chatgpt.com/docs/plugins).
