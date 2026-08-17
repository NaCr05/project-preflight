from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ROOT = REPO_ROOT / "skills" / "project-preflight" / "scripts"
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from preflight_runtime import (  # noqa: E402
    PreflightSession,
    StageOutcome,
    StateOperationError,
)


FIXED_TIME = datetime(2026, 8, 17, 10, 0, tzinfo=timezone.utc)


class PreflightSessionTests(unittest.TestCase):
    def make_session(self, root: Path) -> PreflightSession:
        return PreflightSession(
            root / ".project" / "preflight.md",
            root,
            clock=lambda: FIXED_TIME,
        )

    def test_start_and_current_return_validated_state_with_one_directive(self):
        with tempfile.TemporaryDirectory() as temp:
            session = self.make_session(Path(temp))
            started = session.start("demo", "A rough durable idea.")
            self.assertEqual("DISCOVERY", started.state.data["current_stage"])
            self.assertEqual("RUN_STAGE_ADAPTER", started.directive.kind)
            self.assertEqual("project-preflight-grill-me", started.directive.adapter_skill)
            self.assertIn("StageOutcome", started.directive.instruction)
            self.assertIn("PreflightSession", started.directive.instruction)
            self.assertEqual(started.to_dict(), session.current().to_dict())

    def test_stage_outcomes_drive_the_full_path_without_target_stage_or_gate(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            docs = root / "docs"
            docs.mkdir()
            (docs / "decisions.md").write_text("# Decisions\n", encoding="utf-8")
            (docs / "spec.md").write_text("# Spec\n", encoding="utf-8")
            tickets = root / "tickets"
            tickets.mkdir()
            (tickets / "01-tracer.md").write_text("# Tracer\n", encoding="utf-8")

            session = self.make_session(root)
            session.start("demo", "A rough durable idea.")
            decision = session.apply(
                StageOutcome.pass_gate("Problem is clear", "Discovery evidence.")
            )
            self.assertEqual("DECISION", decision.state.data["current_stage"])
            specification = session.apply(
                StageOutcome.pass_gate(
                    "Decisions are ready",
                    "Decision evidence.",
                    artifacts={"decision_map": "docs/decisions.md"},
                )
            )
            self.assertEqual("SPECIFICATION", specification.state.data["current_stage"])
            ticketing = session.apply(
                StageOutcome.pass_gate(
                    "Specification is ready",
                    "Specification evidence.",
                    artifacts={"spec": "docs/spec.md"},
                )
            )
            self.assertEqual("TICKETING", ticketing.state.data["current_stage"])
            ready = session.apply(
                StageOutcome.pass_gate(
                    "Tickets are ready",
                    "Execution evidence.",
                    artifacts={"tickets": "tickets"},
                    next_action="Implement ticket 01 and run its verification.",
                )
            )
            self.assertEqual("READY_FOR_IMPLEMENTATION", ready.state.data["current_stage"])
            self.assertEqual("READY", ready.directive.kind)

    def test_gate_blocking_is_derived_from_the_current_stage(self):
        with tempfile.TemporaryDirectory() as temp:
            session = self.make_session(Path(temp))
            session.start("demo", "A rough durable idea.")
            result = session.apply(
                StageOutcome.block_gate(
                    "Success criteria are missing",
                    "No measurable outcome is recorded.",
                )
            )
            self.assertEqual("DISCOVERY", result.state.data["current_stage"])
            self.assertEqual("blocked", result.state.data["gates"]["gate_1"])
            self.assertIn("Success criteria are missing", session.path.read_text(encoding="utf-8"))
            advanced = session.apply(
                StageOutcome.pass_gate(
                    "Problem evidence is now complete",
                    "Measurable success criteria were approved.",
                )
            )
            self.assertEqual("DECISION", advanced.state.data["current_stage"])
            self.assertIn("## Blockers\n\nNone recorded.", session.path.read_text(encoding="utf-8"))

    def test_invalidated_artifact_derives_earliest_regression_and_next_directive(self):
        fixture = REPO_ROOT / "evals" / "fixtures" / "ready-handoff"
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._copy_tree(fixture, root)
            session = self.make_session(root)
            result = session.apply(
                StageOutcome.invalidate(
                    "The provider cannot satisfy the approved data contract.",
                    "Provider documentation contradicts the decision map.",
                    invalidated_artifacts=("decision_map", "spec"),
                )
            )
            self.assertEqual("DECISION", result.state.data["current_stage"])
            self.assertEqual("passed", result.state.data["gates"]["gate_1"])
            self.assertEqual("invalidated", result.state.data["gates"]["gate_2"])
            self.assertEqual("project-preflight-wayfinder", result.directive.adapter_skill)
            repeated = session.apply(
                StageOutcome.invalidate(
                    "The replacement decision evidence is still contradictory.",
                    "Two canonical sources disagree.",
                    invalidated_artifacts=("decision_map",),
                )
            )
            self.assertEqual("DECISION", repeated.state.data["current_stage"])
            self.assertIn("Continue the active Project Preflight session", session.path.read_text(encoding="utf-8"))

    def test_invalid_outcome_leaves_the_last_valid_state_unchanged(self):
        with tempfile.TemporaryDirectory() as temp:
            session = self.make_session(Path(temp))
            session.start("demo", "A rough durable idea.")
            before = session.path.read_bytes()
            with self.assertRaises(StateOperationError):
                session.apply(
                    StageOutcome.pass_gate(
                        "Problem is clear",
                        "Discovery evidence.",
                        artifacts={"decision_map": "docs/missing.md"},
                    )
                )
            self.assertEqual(before, session.path.read_bytes())

    def test_recorded_missing_dependency_returns_blocked_directive_without_gate_mutation(self):
        fixture = REPO_ROOT / "evals" / "fixtures" / "missing-stage-skill"
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._copy_tree(fixture, root)
            session = self.make_session(root)
            result = session.apply(
                StageOutcome.record(
                    "The bundled ticketing Adapter is unavailable.",
                    dependencies={"to-tickets": "missing"},
                    blockers="`to-tickets` is absent from the active Skill catalog.",
                    next_action="Restore the bundled Adapter, then resume Project Preflight.",
                )
            )
            self.assertEqual("not_evaluated", result.state.data["gates"]["gate_4"])
            self.assertEqual("BLOCKED", result.directive.kind)

    def test_cli_apply_returns_state_and_directive_in_one_json_result(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            session = self.make_session(root)
            session.start("cli-session", "A CLI idea.")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_ROOT / "preflight_state.py"),
                    "--state-file",
                    str(session.path),
                    "--repo-root",
                    str(root),
                    "apply",
                    "--verdict",
                    "gate_passed",
                    "--reason",
                    "Problem is clear",
                    "--evidence",
                    "Discovery evidence.",
                    "--json",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual("DECISION", payload["state"]["data"]["current_stage"])
            self.assertEqual("project-preflight-wayfinder", payload["directive"]["adapter_skill"])

    @staticmethod
    def _copy_tree(source: Path, destination: Path) -> None:
        import shutil

        shutil.copytree(source, destination, dirs_exist_ok=True)


if __name__ == "__main__":
    unittest.main()
