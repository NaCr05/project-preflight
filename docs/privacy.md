# Privacy Notice

Last reviewed: 2026-08-17

Project Preflight is a local-first Codex Plugin. It has no publisher-operated server, account system, analytics endpoint, advertising SDK, or telemetry collector. The publisher does not receive the rough idea, answers, project files, `.project/preflight.md`, specifications, tickets, or model conversation through this Plugin.

## Data the Plugin uses

The Plugin may read repository context and planning artifacts that the user places in the active workspace. It writes planning state and durable artifacts into that workspace as described in the product documentation. Codex and the user's configured model provider may process conversation and workspace context under their own terms and privacy controls; those services are outside this Plugin's control.

## Optional network access

Remote Artifact Evidence checking is disabled unless `--check-remote` is explicitly used. When enabled, the runtime may send bounded read-only HTTP(S) GET requests to the URL in an artifact pointer. A GitHub token available in `GH_TOKEN` or `GITHUB_TOKEN` may be sent only to the matching GitHub API request. Tokens are not written into Preflight state or planning artifacts, and credential headers are removed when a redirect crosses origins.

Remote sites receive normal request metadata such as the requesting IP address and user agent and apply their own privacy policies. Link reachability does not prove the semantic quality of the linked evidence.

## Retention and deletion

The Plugin does not maintain a separate publisher-side copy. Local artifacts remain until the user edits or deletes them. Uninstalling the Plugin does not delete repository files or the Plugin source checkout.

## Contact

For privacy questions, use the repository's support process in `SUPPORT.md`. Do not include private project content or credentials in a public issue.
