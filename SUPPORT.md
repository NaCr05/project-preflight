# Support

Project Preflight is maintained as an open-source Codex Plugin. `v0.3.2` is the stable supported release and the repository is in [low-frequency maintenance](docs/maintenance.md). Before requesting help, update to the latest version, start a new Codex task, and run:

```text
codex plugin list
python scripts/release_harness.py inspect
```

## Where to ask

- Use a **bug report** for reproducible failures, incorrect Stage routing, invalid state, unsafe remote behavior, or documentation that does not match the Plugin.
- Use a **feature request** for new workflow behavior or integrations.
- Use `SECURITY.md` for suspected vulnerabilities. Never put vulnerability details, credentials, or private project artifacts in a public issue.

Include the Plugin version, operating system, Python version, invocation prompt, observed Stage, expected behavior, and the smallest sanitized reproduction. Maintainers do not need your full private planning documents.

## Support boundaries

Support covers the current version on `main` and the latest tagged release. Historical experiment branches, locally modified forks, unrelated third-party Skills, and production application code generated after the handoff are outside the supported release line.

There is no guaranteed response time or hosted-service uptime commitment. Project Preflight runs through the user's Codex environment and local project workspace.
