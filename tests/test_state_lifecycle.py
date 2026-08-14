from __future__ import annotations

import sys
import subprocess
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ROOT = REPO_ROOT / "skills" / "project-preflight" / "scripts"
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from preflight_runtime import (  # noqa: E402
    StateChange,
    StateOperationError,
    StateStore,
    inspect_path,
    render_initial_state,
)


FIXED_TIME = datetime(2026, 8, 13, 10, 0, tzinfo=timezone.utc)


class StateLifecycleTests(unittest.TestCase):
    def make_store(self, root: Path) -> StateStore:
        return StateStore(
            root / ".project" / "preflight.md",
            root,
            clock=lambda: FIXED_TIME,
        )

    def test_initialize_with_idea_enters_discovery_and_prints_explicit_handoff(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            store = self.make_store(root)
            report = store.initialize("demo", "A durable idea.")
            self.assertTrue(report.valid)
            self.assertEqual("DISCOVERY", report.data["current_stage"])
            self.assertEqual("inline:#original-idea", report.data["artifacts"]["idea"])
            handoff = store.handoff()
            self.assertIn("Use $grill-me", handoff)
            self.assertIn("Use $project-preflight to resume", handoff)

    def test_invalid_candidate_does_not_replace_last_valid_state(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            store = self.make_store(root)
            store.initialize("demo", "A durable idea.")
            before = store.path.read_text(encoding="utf-8")
            with self.assertRaises(StateOperationError):
                store.advance("DECISION", "Claimed Gate 1 without evidence")
            self.assertEqual(before, store.path.read_text(encoding="utf-8"))

    def test_happy_path_and_regression_cross_the_same_interface(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "docs").mkdir()
            (root / "docs" / "decisions.md").write_text("# Decisions\n", encoding="utf-8")
            (root / "docs" / "spec.md").write_text("# Spec\n", encoding="utf-8")
            (root / "tickets").mkdir()
            (root / "tickets" / "01-tracer.md").write_text("# Tracer\n", encoding="utf-8")

            store = self.make_store(root)
            store.initialize("demo", "A durable idea.")
            store.advance(
                "DECISION",
                "Problem is clear",
                StateChange(gate_evidence={"gate_1": "Discovery evidence."}),
            )
            store.advance(
                "SPECIFICATION",
                "Decisions are ready",
                StateChange(
                    artifacts={"decision_map": "docs/decisions.md"},
                    gate_evidence={"gate_2": "Decision evidence."},
                ),
            )
            store.advance(
                "TICKETING",
                "Specification is ready",
                StateChange(
                    artifacts={"spec": "docs/spec.md"},
                    gate_evidence={"gate_3": "Specification evidence."},
                ),
            )
            ready = store.advance(
                "READY_FOR_IMPLEMENTATION",
                "Tickets are ready",
                StateChange(
                    artifacts={"tickets": "tickets"},
                    gate_evidence={"gate_4": "Execution evidence."},
                    next_action="Implement ticket 01 and run its verification.",
                ),
            )
            self.assertTrue(ready.data["ready_for_implementation"])
            self.assertEqual(["passed"] * 4, list(ready.data["gates"].values()))

            regressed = store.regress("DECISION", "The selected provider cannot supply required data.")
            self.assertEqual("DECISION", regressed.data["current_stage"])
            self.assertEqual("passed", regressed.data["gates"]["gate_1"])
            self.assertEqual("invalidated", regressed.data["gates"]["gate_2"])
            self.assertEqual("invalidated", regressed.data["gates"]["gate_3"])
            self.assertEqual("invalidated", regressed.data["gates"]["gate_4"])
            self.assertFalse(regressed.data["ready_for_implementation"])
            self.assertIn("Use $wayfinder", store.handoff())

    def test_recover_rejects_invalid_source_and_preserves_current_state(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            store = self.make_store(root)
            store.initialize("demo", "A durable idea.")
            before = store.path.read_text(encoding="utf-8")
            invalid = root / "invalid.md"
            invalid.write_text("not a state", encoding="utf-8")
            with self.assertRaises(StateOperationError):
                store.recover(invalid)
            self.assertEqual(before, store.path.read_text(encoding="utf-8"))

    def test_local_anchor_is_checked(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            docs = root / "docs"
            docs.mkdir()
            (docs / "idea.md").write_text("# Different Heading\n", encoding="utf-8")
            state = root / ".project" / "preflight.md"
            state.parent.mkdir()
            text = render_initial_state().replace(
                'current_stage: "IDEA"', 'current_stage: "DISCOVERY"'
            ).replace(
                "previous_stage: null", 'previous_stage: "IDEA"'
            ).replace(
                "last_transition: null", 'last_transition: "2026-08-13T10:00:00Z"'
            ).replace(
                "idea: null", 'idea: "docs/idea.md#original-idea"'
            )
            state.write_text(text, encoding="utf-8")
            report = inspect_path(state, root)
            self.assertTrue(any("missing local anchor" in error for error in report.errors))

    def test_remote_urls_are_reported_instead_of_silently_skipped(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state = root / ".project" / "preflight.md"
            state.parent.mkdir()
            text = render_initial_state().replace(
                'current_stage: "IDEA"', 'current_stage: "DISCOVERY"'
            ).replace(
                "previous_stage: null", 'previous_stage: "IDEA"'
            ).replace(
                "last_transition: null", 'last_transition: "2026-08-13T10:00:00Z"'
            ).replace(
                "idea: null", 'idea: "https://example.test/idea"'
            )
            state.write_text(text, encoding="utf-8")
            report = inspect_path(state, root)
            self.assertTrue(report.valid)
            self.assertTrue(any("semantic sufficiency" in warning for warning in report.warnings))

    def test_github_issue_adapter_checks_structured_issue_record(self):
        class FakeResponse:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                return False

            def read(self):
                return b'{"html_url":"https://github.com/example/demo/issues/7","title":"Spec"}'

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state = root / ".project" / "preflight.md"
            state.parent.mkdir()
            text = render_initial_state().replace(
                'current_stage: "IDEA"', 'current_stage: "DISCOVERY"'
            ).replace(
                "previous_stage: null", 'previous_stage: "IDEA"'
            ).replace(
                "last_transition: null", 'last_transition: "2026-08-13T10:00:00Z"'
            ).replace(
                "idea: null", 'idea: "https://github.com/example/demo/issues/7"'
            )
            state.write_text(text, encoding="utf-8")
            with mock.patch("urllib.request.urlopen", return_value=FakeResponse()) as opener:
                report = inspect_path(state, root, check_remote=True)
            self.assertTrue(report.valid, report.errors)
            self.assertEqual((), report.warnings)
            request = opener.call_args.args[0]
            self.assertEqual(
                "https://api.github.com/repos/example/demo/issues/7",
                request.full_url,
            )

    def test_remote_check_refuses_non_public_targets(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state = root / ".project" / "preflight.md"
            state.parent.mkdir()
            text = render_initial_state().replace(
                'current_stage: "IDEA"', 'current_stage: "DISCOVERY"'
            ).replace(
                "previous_stage: null", 'previous_stage: "IDEA"'
            ).replace(
                "last_transition: null", 'last_transition: "2026-08-13T10:00:00Z"'
            ).replace(
                "idea: null", 'idea: "http://127.0.0.1/private"'
            )
            state.write_text(text, encoding="utf-8")
            with mock.patch("urllib.request.urlopen") as opener:
                report = inspect_path(state, root, check_remote=True)
            self.assertTrue(any("non-public IP" in error for error in report.errors))
            opener.assert_not_called()

    def test_template_asset_is_derived_from_contract(self):
        asset = REPO_ROOT / "skills" / "project-preflight" / "assets" / "preflight-template.md"
        self.assertEqual(render_initial_state(), asset.read_text(encoding="utf-8"))

    def test_cli_initializes_and_emits_handoff_through_public_interface(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state = root / ".project" / "preflight.md"
            script = SCRIPT_ROOT / "preflight_state.py"
            initialized = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--state-file",
                    str(state),
                    "--repo-root",
                    str(root),
                    "init",
                    "--project",
                    "cli-demo",
                    "--idea",
                    "A CLI idea.",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, initialized.returncode, initialized.stderr)
            handoff = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--state-file",
                    str(state),
                    "--repo-root",
                    str(root),
                    "handoff",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, handoff.returncode, handoff.stderr)
            self.assertIn("Use $grill-me", handoff.stdout)
            self.assertIn("Use $project-preflight to resume", handoff.stdout)


if __name__ == "__main__":
    unittest.main()
