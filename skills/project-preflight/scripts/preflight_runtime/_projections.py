"""Exact repository projections derived from the canonical finite contract."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from ._contract import ARTIFACT_STAGES, OUTCOME_BEHAVIORS, STAGE_CONTRACTS, STAGES_BY_NAME


START = "<!-- project-preflight:generated {name}:start -->"
END = "<!-- project-preflight:generated {name}:end -->"


@dataclass(frozen=True)
class ProjectionFinding:
    path: str
    message: str


@dataclass(frozen=True)
class ProjectionTarget:
    path: str
    name: str
    render: Callable[[], str]


def _routing_table() -> str:
    lines = [
        "| Current Stage | Bundled adapter | Public Skill label | Durable result |",
        "|---|---|---|---|",
    ]
    for contract in STAGE_CONTRACTS:
        adapter = f"`{contract.adapter_skill}`" if contract.adapter_skill else "None"
        label = f"`{contract.display_skill}`" if contract.display_skill else "Project Preflight"
        lines.append(
            f"| `{contract.name}` | {adapter} | {label} | {contract.durable_result} |"
        )
    return "\n".join(lines)


def _routing_list() -> str:
    return "\n".join(
        f"- `{contract.name}` -> `{contract.adapter_skill}` (shown to the user as `{contract.display_skill}`)"
        for contract in STAGE_CONTRACTS
        if contract.adapter_skill is not None
    )


def _dependency_table() -> str:
    lines = [
        "| Public capability | Bundled Skill | Stage |",
        "|---|---|---|",
    ]
    for contract in STAGE_CONTRACTS:
        if contract.adapter_skill is not None:
            lines.append(
                f"| `{contract.display_skill}` | `{contract.adapter_skill}` | `{contract.name}` |"
            )
    return "\n".join(lines)


def _stage_invariant_table() -> str:
    lines = [
        "| Current stage | Required passed gates | Required artifact pointers |",
        "|---|---|---|",
    ]
    for contract in STAGE_CONTRACTS:
        gates = "None" if contract.passed_gates == 0 else f"Gates 1–{contract.passed_gates}"
        if contract.passed_gates == 1:
            gates = "Gate 1"
        artifacts = (
            "None"
            if not contract.required_artifacts
            else ", ".join(f"`{item}`" for item in contract.required_artifacts)
        )
        lines.append(f"| `{contract.name}` | {gates} | {artifacts} |")
    return "\n".join(lines)


def _session_outcome_table() -> str:
    lines = [
        "| Verdict | Meaning | Session behavior |",
        "|---|---|---|",
    ]
    for verdict, (meaning, behavior) in OUTCOME_BEHAVIORS.items():
        lines.append(f"| `{verdict}` | {meaning} | {behavior} |")
    return "\n".join(lines)


def _artifact_regression_table() -> str:
    lines = [
        "| Invalidated artifact | Earliest affected Stage |",
        "|---|---|",
    ]
    for artifact, stage in ARTIFACT_STAGES.items():
        lines.append(f"| `{artifact}` | `{stage}` |")
    return "\n".join(lines)


TARGETS = (
    ProjectionTarget(
        "skills/project-preflight/references/workflow.md",
        "stage-routing-table",
        _routing_table,
    ),
    ProjectionTarget(
        "skills/project-preflight/SKILL.md",
        "stage-routing-list",
        _routing_list,
    ),
    ProjectionTarget(
        "skills/project-preflight/references/dependency-contract.md",
        "dependency-table",
        _dependency_table,
    ),
    ProjectionTarget(
        "skills/project-preflight/references/artifact-contract.md",
        "stage-invariant-table",
        _stage_invariant_table,
    ),
    ProjectionTarget(
        "skills/project-preflight/references/session-contract.md",
        "session-outcome-table",
        _session_outcome_table,
    ),
    ProjectionTarget(
        "skills/project-preflight/references/session-contract.md",
        "artifact-regression-table",
        _artifact_regression_table,
    ),
)


class ContractProjection:
    """One Interface for checking or writing every canonical contract projection."""

    def __init__(self, repo_root: Path | str) -> None:
        self.repo_root = Path(repo_root).resolve()

    def check(self) -> tuple[ProjectionFinding, ...]:
        findings: list[ProjectionFinding] = []
        for target in TARGETS:
            path = self.repo_root / target.path
            try:
                text = path.read_text(encoding="utf-8")
                observed = self._block(text, target.name)
            except (OSError, UnicodeError, ValueError) as exc:
                findings.append(ProjectionFinding(target.path, str(exc)))
                continue
            if observed != target.render():
                findings.append(
                    ProjectionFinding(target.path, f"generated block {target.name!r} is stale")
                )
        findings.extend(self._package_findings())
        findings.extend(self._eval_findings())
        return tuple(findings)

    def write(self) -> tuple[str, ...]:
        changed: list[str] = []
        for target in TARGETS:
            path = self.repo_root / target.path
            text = path.read_text(encoding="utf-8")
            current = self._block(text, target.name)
            expected = target.render()
            if current == expected:
                continue
            start = START.format(name=target.name)
            end = END.format(name=target.name)
            prefix, remainder = text.split(start, 1)
            _, suffix = remainder.split(end, 1)
            path.write_text(
                f"{prefix}{start}\n{expected}\n{end}{suffix}",
                encoding="utf-8",
                newline="\n",
            )
            changed.append(target.path)
        return tuple(changed)

    @staticmethod
    def _block(text: str, name: str) -> str:
        start = START.format(name=name)
        end = END.format(name=name)
        if text.count(start) != 1 or text.count(end) != 1:
            raise ValueError(f"expected exactly one generated block {name!r}")
        _, remainder = text.split(start, 1)
        body, _ = remainder.split(end, 1)
        return body.strip("\r\n")

    def _package_findings(self) -> list[ProjectionFinding]:
        findings: list[ProjectionFinding] = []
        for contract in STAGE_CONTRACTS:
            if contract.adapter_skill is None:
                continue
            relative = f"skills/{contract.adapter_skill}"
            root = self.repo_root / relative
            skill = root / "SKILL.md"
            metadata = root / "agents" / "openai.yaml"
            if not skill.is_file():
                findings.append(ProjectionFinding(relative, "bundled adapter SKILL.md is missing"))
                continue
            skill_text = skill.read_text(encoding="utf-8")
            if f"name: {contract.adapter_skill}" not in skill_text:
                findings.append(ProjectionFinding(relative, "adapter Skill name does not match registry"))
            if not metadata.is_file() or "allow_implicit_invocation: true" not in metadata.read_text(
                encoding="utf-8"
            ):
                findings.append(
                    ProjectionFinding(relative, "adapter must allow implicit invocation")
                )
        return findings

    def _eval_findings(self) -> list[ProjectionFinding]:
        relative = "evals/cases.json"
        path = self.repo_root / relative
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, ValueError) as exc:
            return [ProjectionFinding(relative, str(exc))]
        findings: list[ProjectionFinding] = []
        for case in manifest.get("cases", []):
            expected = case.get("expected", {})
            stage = expected.get("current_stage")
            directive = expected.get("directive", {})
            if stage not in STAGES_BY_NAME:
                findings.append(ProjectionFinding(relative, f"case {case.get('id')} has unknown Stage"))
                continue
            contract = STAGES_BY_NAME[stage]
            if directive.get("kind") in {"RUN_STAGE_ADAPTER", "BLOCKED"}:
                observed = (directive.get("display_skill"), directive.get("adapter_skill"))
                canonical = (contract.display_skill, contract.adapter_skill)
                if observed != canonical:
                    findings.append(
                        ProjectionFinding(
                            relative,
                            f"case {case.get('id')} directive mapping {observed!r} != {canonical!r}",
                        )
                    )
        return findings
