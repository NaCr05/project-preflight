# Maintenance Status

Project Preflight `v0.3.2` is the stable supported release. The repository is in low-frequency maintenance: the documented workflow, public interfaces, and release artifacts remain supported, while new features and integrations are intentionally deferred.

## Supported surface

- the latest tagged release and the current `main` branch;
- source and GitHub Release installation paths;
- the five bundled Skills, `.project/preflight.md` lifecycle, deterministic validators, and Release Harness;
- security reports submitted through GitHub private vulnerability reporting.

Historical experiment branches, locally modified forks, unrelated third-party Skills, and production code created after the implementation handoff are outside the supported release line.

## Automation during low-frequency maintenance

- Pull requests must pass the Windows/Linux and Python 3.11/3.14 CI matrix.
- GitHub Actions are pinned to immutable commit SHAs.
- Dependabot checks GitHub Actions monthly and may open a grouped update pull request. Updates are never merged automatically.
- Secret scanning, push protection, private vulnerability reporting, protected `main`, and protected `v*` release tags remain enabled.

## Resuming active development

Before changing behavior, read `AGENTS.md`, `docs/product-spec.md`, the applicable decision records, and `docs/knowledge-map.json`. Start from a current `main`, work through a pull request, run `python scripts/release_harness.py verify`, and follow `CONTRIBUTING.md`. User-visible lifecycle changes require synchronized documentation and behavior evidence; release changes require a new semantic version and changelog entry.

The public Plugin Directory submission remains a separate future milestone because external review may require an active maintenance cycle.
