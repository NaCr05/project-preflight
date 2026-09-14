#!/usr/bin/env python3
"""Verify and reproducibly package a Project Preflight release candidate."""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import re
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXED_ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
SEMVER = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?$")

PACKAGE_FILES = (
    ".codex-plugin/plugin.json",
    "CHANGELOG.md",
    "LICENSE",
    "README.md",
    "README.zh-CN.md",
    "SECURITY.md",
    "SUPPORT.md",
    "THIRD_PARTY_NOTICES.md",
    "docs/privacy.md",
    "docs/terms.md",
    "docs/diagrams/assets/language-en.svg",
    "docs/diagrams/assets/language-zh-CN.svg",
    "docs/diagrams/assets/overview.en.png",
    "docs/diagrams/assets/overview.en.dark.png",
    "docs/diagrams/assets/overview.zh-CN.png",
    "docs/diagrams/assets/overview.zh-CN.dark.png",
    "docs/diagrams/assets/recovery.en.png",
    "docs/diagrams/assets/recovery.en.dark.png",
    "docs/diagrams/assets/recovery.zh-CN.png",
    "docs/diagrams/assets/recovery.zh-CN.dark.png",
)
PACKAGE_DIRECTORIES = ("skills",)

ROLES = {
    "navigation_routing",
    "rules_boundaries",
    "specifications_contracts",
    "state_evidence",
    "rationale_history",
    "execution_verification",
}
UPDATE_SEMANTICS = {
    "stable_entry",
    "synchronized",
    "append_only",
    "derived_generated",
}
AUTHORITIES = {"canonical", "explanatory", "evidence"}
RELATIONSHIPS = {
    "routes_to",
    "source_of_truth",
    "evidenced_by",
    "verified_by",
    "generated_from",
    "supersedes",
}
ENFORCEMENT_LEVELS = {
    "documented",
    "review_required",
    "automated_warning",
    "automated_blocking",
    "structural_prevention",
}


@dataclass(frozen=True)
class ReleaseFinding:
    location: str
    message: str


class ReleaseHarnessError(RuntimeError):
    """Raised when a release candidate violates a deterministic contract."""


class ReleaseHarness:
    """One maintainer Interface for release inspection, verification, and packaging."""

    def __init__(self, repo_root: Path | str = REPO_ROOT) -> None:
        self.repo_root = Path(repo_root).resolve()

    @property
    def version(self) -> str:
        manifest = self.repo_root / ".codex-plugin" / "plugin.json"
        try:
            value = json.loads(manifest.read_text(encoding="utf-8"))["version"]
        except (OSError, UnicodeError, ValueError, KeyError, TypeError) as exc:
            raise ReleaseHarnessError(f"cannot read Plugin version: {exc}") from exc
        if not isinstance(value, str) or not SEMVER.fullmatch(value):
            raise ReleaseHarnessError(f"Plugin version is not supported SemVer: {value!r}")
        return value

    def inspect(self, *, tag: str | None = None) -> tuple[ReleaseFinding, ...]:
        """Inspect cross-file release facts without running subprocess checks."""

        findings: list[ReleaseFinding] = []
        try:
            version = self.version
        except ReleaseHarnessError as exc:
            return (ReleaseFinding(".codex-plugin/plugin.json", str(exc)),)

        if tag is not None and tag != f"v{version}":
            findings.append(
                ReleaseFinding("release tag", f"expected v{version}, observed {tag}")
            )

        expected_text = {
            "CHANGELOG.md": f"## [{version}]",
            "docs/product-spec.md": f"# Project Preflight v{version} Product Specification",
            "README.md": f"Plugin-{version}-",
            "README.zh-CN.md": f"Plugin-{version}-",
        }
        for relative, marker in expected_text.items():
            path = self.repo_root / relative
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeError) as exc:
                findings.append(ReleaseFinding(relative, str(exc)))
                continue
            if marker not in text:
                findings.append(
                    ReleaseFinding(relative, f"does not declare Plugin version {version}")
                )

        for relative in PACKAGE_FILES:
            if not (self.repo_root / relative).is_file():
                findings.append(ReleaseFinding(relative, "required release file is missing"))
        for relative in PACKAGE_DIRECTORIES:
            if not (self.repo_root / relative).is_dir():
                findings.append(ReleaseFinding(relative, "required release directory is missing"))

        findings.extend(self._inspect_eval_manifest())
        findings.extend(self._inspect_knowledge_registry())
        return tuple(findings)

    def verify(self) -> None:
        """Run the complete repository-owned verification sequence."""

        self._raise_findings(self.inspect())
        commands = (
            (sys.executable, "-m", "compileall", "-q", "skills", "evals", "tests", "scripts"),
            (sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"),
            (
                sys.executable,
                "skills/project-preflight/scripts/sync_contract.py",
                "--check",
            ),
            (
                sys.executable,
                "skills/project-preflight/scripts/preflight_state.py",
                "template",
                "--check",
                "skills/project-preflight/assets/preflight-template.md",
            ),
            (sys.executable, "evals/run_behavior_evals.py", "list"),
        )
        for command in commands:
            print(f"RUN: {' '.join(command)}", flush=True)
            completed = subprocess.run(command, cwd=self.repo_root, check=False)
            if completed.returncode:
                raise ReleaseHarnessError(
                    f"verification command failed with exit code {completed.returncode}: "
                    f"{' '.join(command)}"
                )

    def build(self, destination: Path | str, *, tag: str | None = None) -> tuple[Path, Path]:
        """Build a deterministic Plugin archive and its SHA-256 record."""

        self._raise_findings(self.inspect(tag=tag))
        output = Path(destination).resolve()
        output.mkdir(parents=True, exist_ok=True)
        archive = output / f"project-preflight-{self.version}.zip"
        checksum = output / f"project-preflight-{self.version}.sha256"
        members = tuple(self._package_members())
        if not members:
            raise ReleaseHarnessError("release package has no members")

        with zipfile.ZipFile(
            archive,
            "w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9,
        ) as bundle:
            for relative, path in members:
                info = zipfile.ZipInfo(relative, FIXED_ZIP_TIMESTAMP)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                bundle.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)

        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        checksum.write_text(f"{digest}  {archive.name}\n", encoding="ascii", newline="\n")
        return archive, checksum

    def _inspect_eval_manifest(self) -> list[ReleaseFinding]:
        relative = "evals/cases.json"
        path = self.repo_root / relative
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
            cases = manifest["cases"]
        except (OSError, UnicodeError, ValueError, KeyError, TypeError) as exc:
            return [ReleaseFinding(relative, f"cannot load behavior cases: {exc}")]
        counts = {"positive": 0, "negative": 0}
        for case in cases:
            kind = case.get("submission_kind")
            if kind in counts:
                counts[kind] += 1
            else:
                return [
                    ReleaseFinding(
                        relative,
                        f"case {case.get('id')!r} has invalid submission_kind {kind!r}",
                    )
                ]
        findings = []
        for kind, minimum in (("positive", 5), ("negative", 3)):
            if counts[kind] < minimum:
                findings.append(
                    ReleaseFinding(
                        relative,
                        f"requires at least {minimum} {kind} submission cases; found {counts[kind]}",
                    )
                )
        return findings

    def _inspect_knowledge_registry(self) -> list[ReleaseFinding]:
        relative = "docs/knowledge-map.json"
        path = self.repo_root / relative
        try:
            registry = json.loads(path.read_text(encoding="utf-8"))
            artifacts = registry["artifacts"]
        except (OSError, UnicodeError, ValueError, KeyError, TypeError) as exc:
            return [ReleaseFinding(relative, f"cannot load knowledge registry: {exc}")]
        if registry.get("schema_version") != 1 or not isinstance(artifacts, list):
            return [ReleaseFinding(relative, "expected schema_version 1 and an artifacts list")]

        findings: list[ReleaseFinding] = []
        required = {
            "artifact",
            "path",
            "primary_role",
            "secondary_roles",
            "update_semantics",
            "authority",
            "authority_scope",
            "owner",
            "update_trigger",
            "verification",
            "enforcement_level",
            "enforced_by",
            "relations",
        }
        by_id: dict[str, Mapping[str, object]] = {}
        for item in artifacts:
            if not isinstance(item, dict):
                findings.append(ReleaseFinding(relative, "artifact entries must be objects"))
                continue
            missing = required - set(item)
            artifact_id = str(item.get("artifact", "<missing>"))
            if missing:
                findings.append(
                    ReleaseFinding(relative, f"{artifact_id} is missing fields: {sorted(missing)}")
                )
                continue
            if artifact_id in by_id:
                findings.append(ReleaseFinding(relative, f"duplicate artifact id: {artifact_id}"))
            by_id[artifact_id] = item
            location_value = str(item["path"])
            location_exists = (
                bool(tuple(self.repo_root.glob(location_value)))
                if glob.has_magic(location_value)
                else (self.repo_root / location_value).exists()
            )
            if not location_exists:
                findings.append(
                    ReleaseFinding(relative, f"{artifact_id} points to missing path {item['path']}")
                )
            if item["primary_role"] not in ROLES:
                findings.append(ReleaseFinding(relative, f"{artifact_id} has invalid primary_role"))
            secondary = item["secondary_roles"]
            if (
                not isinstance(secondary, list)
                or len(secondary) > 2
                or any(role not in ROLES for role in secondary)
            ):
                findings.append(ReleaseFinding(relative, f"{artifact_id} has invalid secondary_roles"))
            if item["update_semantics"] not in UPDATE_SEMANTICS:
                findings.append(ReleaseFinding(relative, f"{artifact_id} has invalid update_semantics"))
            if item["authority"] not in AUTHORITIES:
                findings.append(ReleaseFinding(relative, f"{artifact_id} has invalid authority"))
            if item["enforcement_level"] not in ENFORCEMENT_LEVELS:
                findings.append(ReleaseFinding(relative, f"{artifact_id} has invalid enforcement_level"))
            for field in ("authority_scope", "owner", "update_trigger", "verification"):
                if not isinstance(item[field], str) or not item[field].strip():
                    findings.append(ReleaseFinding(relative, f"{artifact_id} has empty {field}"))
            enforced_by = item["enforced_by"]
            if not isinstance(enforced_by, list) or not enforced_by:
                findings.append(ReleaseFinding(relative, f"{artifact_id} has no enforcement target"))
            elif any(not (self.repo_root / str(target)).exists() for target in enforced_by):
                findings.append(ReleaseFinding(relative, f"{artifact_id} has a missing enforcement target"))

        for artifact_id, item in by_id.items():
            relations = item["relations"]
            if not isinstance(relations, list):
                findings.append(ReleaseFinding(relative, f"{artifact_id} relations must be a list"))
                continue
            relation_types = set()
            for relation in relations:
                if not isinstance(relation, dict):
                    findings.append(ReleaseFinding(relative, f"{artifact_id} has an invalid relation"))
                    continue
                relation_type = relation.get("type")
                target = relation.get("target")
                relation_types.add(relation_type)
                if relation_type not in RELATIONSHIPS:
                    findings.append(ReleaseFinding(relative, f"{artifact_id} has unknown relation {relation_type!r}"))
                if target not in by_id:
                    findings.append(ReleaseFinding(relative, f"{artifact_id} targets unknown artifact {target!r}"))
            if item["authority"] == "explanatory" and "source_of_truth" not in relation_types:
                findings.append(
                    ReleaseFinding(relative, f"explanatory artifact {artifact_id} has no source_of_truth")
                )
        return findings

    def _package_members(self) -> Iterable[tuple[str, Path]]:
        paths: dict[str, Path] = {}
        for relative in PACKAGE_FILES:
            paths[relative] = self.repo_root / relative
        for directory in PACKAGE_DIRECTORIES:
            root = self.repo_root / directory
            for path in root.rglob("*"):
                if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
                    relative = path.relative_to(self.repo_root).as_posix()
                    paths[relative] = path
        for relative in sorted(paths):
            yield relative, paths[relative]

    @staticmethod
    def _raise_findings(findings: tuple[ReleaseFinding, ...]) -> None:
        if not findings:
            return
        detail = "\n".join(f"- {item.location}: {item.message}" for item in findings)
        raise ReleaseHarnessError(f"release inspection failed:\n{detail}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("inspect", help="check deterministic cross-file release facts")
    subparsers.add_parser("verify", help="run all repository-owned release checks")
    build = subparsers.add_parser("build", help="create a deterministic archive and checksum")
    build.add_argument("--output", type=Path, default=Path("dist"))
    build.add_argument("--tag")
    args = parser.parse_args(argv)

    harness = ReleaseHarness(args.repo_root)
    try:
        if args.command == "inspect":
            harness._raise_findings(harness.inspect())
            print(f"CURRENT: release contracts for {harness.version}")
        elif args.command == "verify":
            harness.verify()
            print(f"VERIFIED: release candidate {harness.version}")
        else:
            archive, checksum = harness.build(args.output, tag=args.tag)
            print(f"BUILT: {archive}")
            print(f"CHECKSUM: {checksum}")
    except ReleaseHarnessError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
