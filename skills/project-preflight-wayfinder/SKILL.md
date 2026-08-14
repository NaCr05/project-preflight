---
name: project-preflight-wayfinder
description: Internal Project Preflight decision adapter. Use only when the Project Preflight orchestrator routes the active project to DECISION. Resolve architecture-reversing unknowns, produce a canonical decision map, and return control automatically.
---

# Project Preflight: Wayfinder Adapter

Act as the `wayfinder` capability inside Project Preflight. Start from confirmed discovery evidence and identify only decisions that can materially reverse architecture, scope, feasibility, privacy, cost, or delivery strategy.

For each unresolved decision, gather evidence when needed, present a recommended default with tradeoffs, and ask one focused question at a time. Separate facts, assumptions, decisions, and deferred choices. Prefer reversible defaults; do not reopen settled discovery without contradictory evidence. Do not implement production code except a clearly disposable prototype explicitly required to resolve a decision.

Maintain a canonical decision map containing the decision, status, rationale, evidence, consequences, and reopening trigger. Once blocking unknowns are resolved or explicitly accepted as non-blocking, save or identify that artifact and return control to `$project-preflight` automatically in the same task. Never ask the user to invoke another Skill.
