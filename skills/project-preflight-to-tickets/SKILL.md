---
name: project-preflight-to-tickets
description: Internal Project Preflight ticketing adapter. Use only when the Project Preflight orchestrator routes the active project to TICKETING. Convert the canonical specification into narrow tracer-bullet tickets and return control automatically.
---

# Project Preflight: To Tickets Adapter

Act as the `to-tickets` capability inside Project Preflight. Use the canonical specification as the scope boundary. Produce a small dependency-aware ticket set that begins with the thinnest end-to-end tracer bullet and grows through verifiable vertical slices.

Every ticket must name its outcome, in-scope and out-of-scope work, dependencies or blockers, acceptance criteria, and verification. Avoid horizontal layer tickets, speculative infrastructure, duplicated requirements, and hidden scope expansion. Flag any specification contradiction rather than resolving it silently. Do not implement production code.

Save or identify the canonical ticket set and first unblocked tracer bullet, then return control to `$project-preflight` automatically in the same task. Never ask the user to invoke another Skill.
