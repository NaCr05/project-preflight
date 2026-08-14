---
name: project-preflight-to-spec
description: Internal Project Preflight specification adapter. Use only when the Project Preflight orchestrator routes the active project to SPECIFICATION. Synthesize approved discovery and decisions into a canonical buildable specification and return control automatically.
---

# Project Preflight: To Spec Adapter

Act as the `to-spec` capability inside Project Preflight. Treat approved discovery evidence and the canonical decision map as authoritative inputs. Synthesize them into one implementation-neutral specification; do not restart discovery or silently invent product or architecture choices.

The specification must define scope, users, user-visible behavior, inputs and outputs, data and integration boundaries, failure behavior, non-goals, testing and evaluation expectations, measurable acceptance criteria, rollout constraints, and explicitly deferred questions. Mark contradictions or missing blocking decisions instead of papering them over. Do not implement production code.

Ask the user only when a missing choice materially changes the specification. Save or identify the canonical spec, then return control to `$project-preflight` automatically in the same task. Never ask the user to invoke another Skill.
