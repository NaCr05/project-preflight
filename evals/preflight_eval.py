"""Reproducible preparation and scoring interface for Project Preflight behavior cases."""

from __future__ import annotations

import hashlib
import json
import platform
import shutil
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ROOT = REPO_ROOT / "skills" / "project-preflight" / "scripts"
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from preflight_runtime import inspect_path  # noqa: E402


@dataclass(frozen=True)
class EvalCheck:
    passed: bool
    evidence: str


@dataclass(frozen=True)
class EvalResult:
    schema_version: int
    case_id: str
    title: str
    passed: bool
    score: int
    maximum_score: int
    checks: Mapping[str, EvalCheck]
    critical_failures: tuple[str, ...]
    validator_errors: tuple[str, ...]
    validator_warnings: tuple[str, ...]
    metadata: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["checks"] = {
            name: asdict(check) for name, check in self.checks.items()
        }
        return payload


class BehaviorEvalHarness:
    """Deep eval module: manifest, fixtures, scoring, metadata, and evidence output."""

    def __init__(self, manifest_path: Path | str = Path(__file__).with_name("cases.json")) -> None:
        self.manifest_path = Path(manifest_path).resolve()
        self.root = self.manifest_path.parent
        self.manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        if self.manifest.get("schema_version") != 1:
            raise ValueError("unsupported behavior-eval manifest schema")
        rubric = self.manifest.get("rubric")
        cases = self.manifest.get("cases")
        if not isinstance(rubric, list) or len(rubric) != 7 or not isinstance(cases, list):
            raise ValueError("behavior-eval manifest must define seven rubric items and cases")
        self.rubric = tuple(rubric)
        self._cases = {case["id"]: case for case in cases}
        if len(self._cases) != len(cases):
            raise ValueError("behavior-eval case ids must be unique")

    def list_cases(self) -> tuple[dict[str, Any], ...]:
        return tuple(self._cases.values())

    def prepare(self, case_id: str, destination: Path | str) -> Path:
        case = self._case(case_id)
        prepared = Path(destination).resolve()
        if prepared.exists() and any(prepared.iterdir()):
            raise ValueError(f"evaluation destination is not empty: {prepared}")
        prepared.mkdir(parents=True, exist_ok=True)
        workspace = prepared / "workspace"
        fixture = case.get("fixture")
        if fixture:
            fixture_path = (self.root / fixture).resolve()
            if self.root not in fixture_path.parents or not fixture_path.is_dir():
                raise ValueError(f"invalid fixture for {case_id}: {fixture}")
            shutil.copytree(fixture_path, workspace)
        else:
            workspace.mkdir()

        case_record = {
            "schema_version": 1,
            "case_id": case_id,
            "title": case["title"],
            "prompt": case["prompt"],
            "active_skills": case.get("active_skills", []),
            "instruction": (
                "Run the prompt in workspace/ with only the listed active Skills. "
                "Do not read expected outcomes from the source manifest."
            ),
        }
        (prepared / "case.json").write_text(
            json.dumps(case_record, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        baseline = {
            "schema_version": 1,
            "case_id": case_id,
            "prepared_at": self._now(),
            "files": self._hash_tree(workspace),
            "next_action": self._next_action(workspace / ".project" / "preflight.md")
            if (workspace / ".project" / "preflight.md").exists()
            else None,
        }
        (prepared / "baseline.json").write_text(
            json.dumps(baseline, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return prepared

    def score(
        self,
        prepared_directory: Path | str,
        *,
        model: str,
        dependency_versions: Mapping[str, str] | None = None,
        latency_ms: int | None = None,
        cost_usd: float | None = None,
    ) -> EvalResult:
        prepared = Path(prepared_directory).resolve()
        case_record = json.loads((prepared / "case.json").read_text(encoding="utf-8"))
        baseline = json.loads((prepared / "baseline.json").read_text(encoding="utf-8"))
        case = self._case(case_record["case_id"])
        workspace = prepared / "workspace"
        expected = case["expected"]
        state_path = workspace / ".project" / "preflight.md"
        report = inspect_path(state_path, workspace) if state_path.exists() else None
        data = report.data if report is not None else {}

        current_hashes = self._hash_tree(workspace)
        baseline_state = baseline["files"].get(".project/preflight.md")
        current_state = current_hashes.get(".project/preflight.md")
        state_changed = baseline_state != current_state

        stage_ok = data.get("current_stage") == expected["current_stage"]
        dependencies_ok, dependencies_evidence = self._mapping_matches(
            data.get("dependencies"), expected.get("dependencies", {})
        )
        gates_ok, gates_evidence = self._mapping_matches(
            data.get("gates"), expected.get("gates", {})
        )
        artifacts_ok, artifacts_evidence = self._mapping_matches(
            data.get("artifacts"), expected.get("artifacts", {})
        )
        missing_paths = [
            path for path in expected.get("required_paths", []) if not (workspace / path).exists()
        ]
        forbidden_paths = [
            path for path in expected.get("forbidden_paths", []) if (workspace / path).exists()
        ]
        artifacts_ok = artifacts_ok and not missing_paths
        artifact_evidence = artifacts_evidence
        if missing_paths:
            artifact_evidence += f"; missing preserved paths: {', '.join(missing_paths)}"

        state_valid = report is not None and report.valid
        next_action = self._next_action(state_path) if state_path.exists() else None
        next_action_ok = bool(
            next_action
            and next_action.casefold()
            not in {"not evaluated", "not evaluated.", "none", "none recorded", "none recorded."}
        )
        if expected.get("state_must_change"):
            next_action_ok = (
                next_action_ok
                and state_changed
                and next_action != baseline.get("next_action")
            )

        checks = {
            "correct_stage_selection": EvalCheck(
                stage_ok,
                f"expected {expected['current_stage']}, observed {data.get('current_stage')!r}",
            ),
            "correct_dependency_behavior": EvalCheck(dependencies_ok, dependencies_evidence),
            "gate_evidence_respected": EvalCheck(gates_ok and state_valid, gates_evidence),
            "artifact_authority_preserved": EvalCheck(artifacts_ok, artifact_evidence),
            "production_guardrail_respected": EvalCheck(
                not forbidden_paths,
                "no forbidden production paths" if not forbidden_paths else f"created: {', '.join(forbidden_paths)}",
            ),
            "state_contract_conforms": EvalCheck(
                state_valid,
                "state validator passed" if state_valid else "state missing or invalid",
            ),
            "one_clear_next_action": EvalCheck(
                next_action_ok,
                (
                    f"state and Next Action changed; current Next Action is: {next_action}"
                    if next_action_ok
                    else "state/Next Action did not change or Next Action is missing/placeholder"
                ),
            ),
        }
        if tuple(checks) != self.rubric:
            raise ValueError("eval implementation and manifest rubric are out of sync")

        critical: list[str] = []
        if report is None:
            critical.append("state file was not produced")
        elif report.errors:
            critical.append("state file failed deterministic validation")
        if forbidden_paths:
            critical.append("production implementation guardrail was violated")
        if data.get("current_stage") == "READY_FOR_IMPLEMENTATION" and expected["current_stage"] != "READY_FOR_IMPLEMENTATION":
            critical.append("readiness was declared for a non-ready case")

        score = sum(check.passed for check in checks.values())
        metadata = {
            "evaluated_at": self._now(),
            "model": model,
            "dependency_versions": dict(dependency_versions or {}),
            "active_skills": case.get("active_skills", []),
            "latency_ms": latency_ms,
            "cost_usd": cost_usd,
            "python": platform.python_version(),
            "platform": platform.platform(),
            "manifest_sha256": self._hash_file(self.manifest_path),
            "baseline_state_sha256": baseline_state,
            "result_state_sha256": current_state,
        }
        return EvalResult(
            schema_version=1,
            case_id=case["id"],
            title=case["title"],
            passed=score == len(self.rubric) and not critical,
            score=score,
            maximum_score=len(self.rubric),
            checks=checks,
            critical_failures=tuple(critical),
            validator_errors=tuple(report.errors if report else ("state missing",)),
            validator_warnings=tuple(report.warnings if report else ()),
            metadata=metadata,
        )

    def write_result(
        self,
        result: EvalResult,
        json_path: Path | str,
        markdown_path: Path | str,
    ) -> None:
        Path(json_path).write_text(
            json.dumps(result.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        Path(markdown_path).write_text(self.render_markdown(result), encoding="utf-8")

    def render_markdown(self, result: EvalResult) -> str:
        lines = [
            f"# Behavior Eval Result — {result.title}",
            "",
            f"- **Case:** `{result.case_id}`",
            f"- **Result:** {'Pass' if result.passed else 'Fail'}",
            f"- **Score:** {result.score}/{result.maximum_score}",
            f"- **Model:** `{result.metadata['model']}`",
            f"- **Evaluated:** {result.metadata['evaluated_at']}",
            "",
            "| Check | Result | Evidence |",
            "|---|---|---|",
        ]
        for name, check in result.checks.items():
            evidence = check.evidence.replace("|", "\\|").replace("\n", " ")
            lines.append(f"| `{name}` | {'Pass' if check.passed else 'Fail'} | {evidence} |")
        lines.extend(("", "## Critical failures", ""))
        if result.critical_failures:
            lines.extend(f"- {failure}" for failure in result.critical_failures)
        else:
            lines.append("None.")
        lines.extend(("", "## Validator warnings", ""))
        if result.validator_warnings:
            lines.extend(f"- {warning}" for warning in result.validator_warnings)
        else:
            lines.append("None.")
        return "\n".join(lines) + "\n"

    def _case(self, case_id: str) -> dict[str, Any]:
        try:
            return self._cases[case_id]
        except KeyError as exc:
            raise ValueError(f"unknown behavior-eval case: {case_id}") from exc

    @staticmethod
    def _mapping_matches(actual: Any, expected: Mapping[str, Any]) -> tuple[bool, str]:
        if not isinstance(actual, dict):
            return False, "observed value is not a mapping"
        mismatches = [
            f"{key}: expected {value!r}, observed {actual.get(key)!r}"
            for key, value in expected.items()
            if actual.get(key) != value
        ]
        return not mismatches, "matched expected values" if not mismatches else "; ".join(mismatches)

    @staticmethod
    def _next_action(state_path: Path) -> str | None:
        text = state_path.read_text(encoding="utf-8")
        marker = "## Next Action"
        if marker not in text:
            return None
        tail = text.split(marker, 1)[1].strip()
        return tail.split("\n## ", 1)[0].strip() or None

    @classmethod
    def _hash_tree(cls, root: Path) -> dict[str, str]:
        return {
            path.relative_to(root).as_posix(): cls._hash_file(path)
            for path in sorted(root.rglob("*"))
            if path.is_file()
        }

    @staticmethod
    def _hash_file(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
