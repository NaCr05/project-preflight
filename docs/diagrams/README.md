# README diagram maintenance

The English `README.md` is the default repository entry. `README.zh-CN.md` is its synchronized Simplified Chinese version; both have a compact text link for switching languages.

## Sources and reader assets

| Story | English source | Simplified Chinese source |
|---|---|---|
| Gates and planning artifacts | [overview.en.workflow.json](sources/overview.en.workflow.json) | [overview.zh-CN.workflow.json](sources/overview.zh-CN.workflow.json) |
| Decision-evidence regression | [recovery.en.workflow.json](sources/recovery.en.workflow.json) | [recovery.zh-CN.workflow.json](sources/recovery.zh-CN.workflow.json) |

The READMEs embed `assets/<story>.<locale>.png`, select `assets/<story>.<locale>.dark.png` in dark mode, and link each figure to its full-size light PNG. Text beneath each figure preserves the reading path on narrow screens and when images are unavailable. Language switching uses native Markdown links and needs no image assets.

The diagrams are explanatory views. The [finite runtime registry](../../skills/project-preflight/scripts/preflight_runtime/_contract.py), [Preflight Session](../../skills/project-preflight/scripts/preflight_runtime/_session.py), and [Gate criteria](../../skills/project-preflight/references/gates.md) remain authoritative. Source review for this edition used commit `1009c79f0a838ba8223a5d694d4b437062b56e0a` on 2026-09-14.

## Update the diagrams

1. Update paired sources together when a Stage, Gate, artifact, or regression rule changes. Keep the same IDs, main path, and semantic relationships in both locales; labels and measured node widths may differ to fit the translated text.
2. Use [Archify](https://github.com/tt-a1i/archify) as a documentation authoring tool. This edition was rendered with `2.17.0-dev.1`, workflow schema v2, static motion, and the default classic style. Archify is not a Plugin runtime or CI dependency.
3. Validate and deliver each source into a scratch directory, then inspect the exact delivered HTML:

```text
node <archify-path>/bin/archify.mjs validate workflow docs/diagrams/sources/overview.en.workflow.json --quality showcase --json
node <archify-path>/bin/archify.mjs deliver workflow docs/diagrams/sources/overview.en.workflow.json <scratch>/overview.en.html --quality showcase --json
node <archify-path>/bin/archify.mjs visual-check <scratch>/overview.en.html --json
```

4. Repeat for both stories and locales. Require all nine artifact checks and zero composition errors or warnings. Review the desktop screenshots in light and dark themes; automated containment checks do not establish visual quality.
5. Use the original viewer's PNG export once in light mode and once in dark mode. Copy the exports to their matching asset names without editing SVG serialization or the exported pixels. Keep scratch HTML, browser receipts, and screenshots outside the repository.
6. Review both rendered READMEs at desktop and narrow widths. Verify language switching, theme selection, text alternatives, and full-size image links. The compact recovery figure is intended for README embedding; a presentation may need a separate layout.
7. Run `python scripts/release_harness.py verify` and the official checks in [CONTRIBUTING.md](../../CONTRIBUTING.md). When package membership changes, build twice and check identical checksums and complete image membership.

The Release Harness explicitly includes the eight PNGs required by the READMEs. Diagram source JSON, this authoring guide, and local preview HTML do not become Plugin runtime files. Changes to documentation on `main` do not replace an existing immutable GitHub Release archive.
