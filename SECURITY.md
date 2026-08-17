# Security policy

## Supported version

Security fixes target the latest source version on `main` and the latest tagged release when one exists. Older experimental branches are retained as historical evidence and are not supported release lines.

## Reporting a vulnerability

Do not open a public issue with vulnerability details. Use **Report a vulnerability** on the repository's Security page; GitHub private vulnerability reporting is enabled for this public repository.

In the private report, include the affected version, reproduction steps, impact, and any suggested mitigation. Do not include real credentials or private project artifacts. If the GitHub reporting control is unexpectedly unavailable, open a minimal non-sensitive support issue asking the maintainer to restore the private channel; include no vulnerability facts.

## Security model

Project Preflight normally reads and writes local planning artifacts. It does not publish tracker content or implement production code without separate authorization.

Remote artifact checking is opt-in through `--check-remote`. The Safe Remote Fetch Module:

- accepts only HTTP(S) URLs without embedded credentials;
- rejects localhost, local-network names, and non-public IP addresses;
- resolves and pins an approved public address for each request;
- revalidates every redirect target;
- strips authorization, cookie, and proxy-authorization headers on cross-origin redirects;
- bounds timeout, redirect count, and response size;
- restricts GitHub Issue responses to JSON.

Reachability never proves that an artifact is semantically sufficient for a Gate. `GH_TOKEN` and `GITHUB_TOKEN`, when present, are used only for the GitHub Issue request and are not persisted.

## Maintainer response

Maintainers should acknowledge a complete report privately, reproduce it in an isolated fixture, prepare the smallest compatible fix with regression tests, and disclose it after users have a safe upgrade path.
