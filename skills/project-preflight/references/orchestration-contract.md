# Automatic orchestration contract

Project Preflight is the only user-facing entry. Bundled stage Skills are adapters, not separate user steps.

## Directive interface

Run:

```text
python scripts/preflight_state.py directive --json
```

The runtime returns exactly one directive:

- `CAPTURE_IDEA` — capture a rough paragraph and initialize state;
- `RUN_STAGE_ADAPTER` — announce and follow the named bundled adapter;
- `BLOCKED` — preserve Stage, record why the adapter cannot run, and explain recovery;
- `READY` — present the implementation handoff and end preflight.

On the first invocation, initialize durable state silently after capturing the supplied rough idea. Do not expose `init` as a user step or show an `IDEA` banner when the same message already contains an idea. Derive and show the `DISCOVERY` directive immediately.

The runtime owns stage-to-adapter mapping. The conversational orchestrator owns loading and following the adapter instructions. There is no unsupported claim that Python programmatically calls a Skill.

## Visibility banner

Before entering any specialist Stage, and again after a resumed session, show the directive's `announcement`. The banner must include:

- `Project Preflight` and the current Stage;
- the public capability label: `grill-me`, `wayfinder`, `to-spec`, or `to-tickets`;
- a short reassurance that the user only needs to answer or confirm.

Example:

```text
Project Preflight · Discovery — 正在使用 `grill-me`（Project Preflight 内置适配器）。你只需回答或确认。
```

Do not repeat the full banner before every question in an uninterrupted interview. Repeat it when the Stage changes or the task resumes after interruption.

## Automatic return

After an adapter saves or identifies its canonical artifact, it returns control to Project Preflight in the same task. Project Preflight evaluates the Gate, persists one transition, derives a fresh directive, shows the next banner, and continues. The user never copies a generated command.
