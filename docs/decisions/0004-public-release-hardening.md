# ADR 0004: Harden public release boundaries

- **Status:** Accepted
- **Date:** 2026-08-14

## Context

The v0.3 Plugin completed a real single-entry happy path, but public distribution exposed four gaps: remote evidence transport policy was split across Adapters, announcements were Chinese-only, canonical contract projections were hand-maintained, and repository verification depended on one maintainer's machine.

## Decision

Project Preflight will:

1. place remote DNS, address pinning, redirects, credentials, timeout, response-size, and content-type policy behind one Safe Remote Fetch Module Interface;
2. keep GitHub Issue and generic URL behavior as Artifact Evidence Adapters using that Module;
3. render user-visible announcements through a two-locale message catalog selected by the orchestrator;
4. generate or exactly validate marked normative contract blocks from `_contract.py` through one Contract Projection Module;
5. run deterministic verification on Windows and Linux in GitHub Actions;
6. publish immutable tagged archives with checksums after tag and manifest versions agree;
7. maintain an explicit upstream-review baseline and a measured full-run cost/latency budget.

## Consequences

- Remote reachability checks have one security Locality and can be tested through a deterministic transport Adapter.
- English and Simplified Chinese users receive matching Stage visibility without duplicating orchestration logic.
- A Stage or Adapter mapping change fails CI until normative projections, packaging, and eval expectations agree exactly.
- Official Codex Plugin and Skill validators remain release checks because CI does not assume private local system paths.
- GitHub source installation continues through a personal marketplace while the repository remains a Plugin root; direct Git marketplace distribution would require a separately approved repository-layout migration.

## Reopen when

- Codex provides a stable locale signal directly to Skills;
- Plugin distribution supports a Plugin-root Git source without a marketplace wrapper;
- a remote tracker write Adapter needs methods beyond safe bounded GET;
- measured forward tests justify changing the cost or latency budget.
