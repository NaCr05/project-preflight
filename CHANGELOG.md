# Changelog

All notable changes to Project Preflight are documented here. Versions follow Semantic Versioning.

## [0.3.2] - 2026-08-17

### Added

- One repository-owned Release Harness for local verification, CI, tagged release checks, and deterministic archive construction.
- An outcome-oriented `PreflightSession` Module that accepts `StageOutcome` results and internally derives Gate changes, forward transitions, regressions, atomic persistence, and the next directive.
- Reproducible Plugin archives with a two-build checksum regression test.
- A public-submission preparation packet with five positive and three negative behavior cases.
- Privacy, terms, support, issue, pull-request, and repository knowledge-governance artifacts.
- A stable GitHub Release distribution path, immutable GitHub Actions references, monthly grouped Action updates, ownership metadata, and low-frequency maintenance guidance.

### Changed

- English and Simplified Chinese READMEs now distinguish source availability, GitHub release status, and public Plugin Directory status.
- CI and the tagged Release workflow now use the same maintainer verification Interface.
- Product, release, and behavior-eval version facts are checked against the Plugin manifest.

### Distribution status

- The source repository is public and `v0.3.2` is the first tagged GitHub Release. Public Plugin Directory submission remains deferred.

## [0.3.1] - 2026-08-14

### Added

- English and Simplified Chinese orchestration announcements selected through `directive --locale`.
- Safe Remote Fetch Module with address pinning, redirect revalidation, bounded responses, and cross-origin credential stripping.
- Exact canonical contract projections for normative Skill and reference tables.
- GitHub CI across Windows, Linux, Python 3.11, and Python 3.14.
- Automated tagged release archives and SHA-256 checksums.
- Source-install, upgrade, uninstall, contribution, security, upstream-review, and release guidance.
- A recorded full-run cost and latency regression budget.

### Changed

- Repository contract tests now compare exact Stage-to-Adapter mappings instead of checking only for string presence.
- Remote GitHub Issue and generic URL evidence checks share one hardened transport policy.

## [0.3.0] - 2026-08-14

- Replaced user-operated Handoff orchestration with a single-entry Plugin.
- Bundled namespaced `grill-me`, `wayfinder`, `to-spec`, and `to-tickets` Stage Adapters.
- Added visible Skill banners and automatic return to Project Preflight.
- Preserved the State lifecycle, evidence adapters, regression, recovery, and behavior-eval harness.

## [0.2.0] - 2026-08-14

- Implemented and validated explicit Handoff orchestration as an experiment.
- Added the deep State lifecycle Module, canonical registry, Artifact Evidence Adapters, and deterministic eval cases.

## [0.1.0] - 2026-08-13

- Introduced the gated Project Preflight workflow and validator.
