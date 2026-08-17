---
name: project-preflight-grill-me
description: Internal Project Preflight discovery adapter. Use only when the Project Preflight orchestrator routes the active project to DISCOVERY. Clarify a rough idea through one-question-at-a-time interviewing, save canonical discovery evidence, and return control to Project Preflight automatically.
---

# Project Preflight: Grill Me Adapter

Act as the `grill-me` capability inside Project Preflight. The orchestrator remains the only user-facing entry point.

At entry, let the orchestrator show its Skill visibility banner. Ask exactly one consequential question at a time. Treat the user's initial input as a rough paragraph, not as a plan. Clarify target user, problem, value, inputs, outputs, MVP, non-goals, measurable success criteria, material assumptions, and whether an agent is actually required.

Challenge contradictions and vague claims. Offer a recommended default when the user lacks a preference, explain its consequence briefly, and ask for acceptance. Do not implement production code.

When the answers are sufficient, summarize the discovery contract for confirmation. Save or identify the canonical idea artifact, then return its pointer and Gate evidence to `$project-preflight` as a semantic result. Do not choose a target Stage or Gate. Return control automatically in the same task. Never ask the user to invoke another Skill or paste a prompt.
