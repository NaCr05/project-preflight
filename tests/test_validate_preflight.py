from __future__ import annotations

import importlib.util
import tempfile
import textwrap
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "skills" / "project-preflight" / "scripts" / "validate_preflight.py"
SPEC = importlib.util.spec_from_file_location("validate_preflight", SCRIPT)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


def state_text(
    *,
    stage: str,
    previous: str | None,
    ready: bool,
    gates: tuple[str, str, str, str],
    idea: str | None,
    decision_map: str | None,
    spec: str | None,
    tickets: str | None,
    gate_evidence: tuple[str, str, str, str] | None = None,
) -> str:
    def scalar(value: object) -> str:
        if value is None:
            return "null"
        if isinstance(value, bool):
            return str(value).lower()
        return f'"{value}"'

    evidence = gate_evidence or tuple(
        "Evidence recorded." if status != "not_evaluated" else "Not evaluated."
        for status in gates
    )
    return textwrap.dedent(
        f"""\
        ---
        schema_version: 1
        project: "test-project"
        current_stage: "{stage}"
        previous_stage: {scalar(previous)}
        last_transition: {scalar("2026-08-13T08:00:00Z" if previous else None)}
        transition_reason: "Test transition"
        tracker: "local-markdown"
        ready_for_implementation: {str(ready).lower()}
        gates:
          gate_1: "{gates[0]}"
          gate_2: "{gates[1]}"
          gate_3: "{gates[2]}"
          gate_4: "{gates[3]}"
        artifacts:
          idea: {scalar(idea)}
          decision_map: {scalar(decision_map)}
          spec: {scalar(spec)}
          tickets: {scalar(tickets)}
        dependencies:
          grill-me: "available"
          wayfinder: "available"
          to-spec: "available"
          to-tickets: "available"
        ---

        # Project Preflight

        ## Original Idea

        A test project idea.

        ## Gate Evidence

        ### Gate 1

        {evidence[0]}

        ### Gate 2

        {evidence[1]}

        ### Gate 3

        {evidence[2]}

        ### Gate 4

        {evidence[3]}

        ## Blockers

        None recorded.

        ## Next Action

        Continue safely.
        """
    )


class ValidatePreflightTests(unittest.TestCase):
    def validate_text(self, text: str, setup=None):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            if setup:
                setup(root)
            state = root / ".project" / "preflight.md"
            state.parent.mkdir()
            state.write_text(text, encoding="utf-8")
            return VALIDATOR.validate_path(state, root)[0]

    def test_valid_idea_fixture(self):
        fixture = REPO_ROOT / "tests" / "fixtures" / "valid-idea.md"
        errors, data = VALIDATOR.validate_path(fixture, fixture.parent)
        self.assertEqual([], errors)
        self.assertEqual("IDEA", data["current_stage"])

    def test_valid_ready_state(self):
        def setup(root: Path):
            (root / "docs").mkdir()
            (root / "docs" / "idea.md").write_text("idea", encoding="utf-8")
            (root / "docs" / "decisions.md").write_text("decisions", encoding="utf-8")
            (root / "docs" / "spec.md").write_text("spec", encoding="utf-8")
            (root / "tickets").mkdir()

        text = state_text(
            stage="READY_FOR_IMPLEMENTATION",
            previous="TICKETING",
            ready=True,
            gates=("passed", "passed", "passed", "passed"),
            idea="docs/idea.md",
            decision_map="docs/decisions.md",
            spec="docs/spec.md",
            tickets="tickets",
        )
        self.assertEqual([], self.validate_text(text, setup))

    def test_invalid_ready_fixture_reports_missing_gate_and_artifacts(self):
        fixture = REPO_ROOT / "tests" / "fixtures" / "invalid-ready.md"
        errors, _ = VALIDATOR.validate_path(fixture, fixture.parent)
        joined = "\n".join(errors)
        self.assertIn("gate_4 must be passed", joined)
        self.assertIn("artifact idea is required", joined)
        self.assertIn("artifact tickets is required", joined)

    def test_rejects_gate_passed_ahead_of_stage(self):
        text = state_text(
            stage="DISCOVERY",
            previous="IDEA",
            ready=False,
            gates=("passed", "not_evaluated", "not_evaluated", "not_evaluated"),
            idea="inline:#original-idea",
            decision_map=None,
            spec=None,
            tickets=None,
        )
        errors = self.validate_text(text)
        self.assertTrue(any("gate_1 cannot already be passed" in error for error in errors))

    def test_rejects_missing_local_artifact_target(self):
        text = state_text(
            stage="TICKETING",
            previous="SPECIFICATION",
            ready=False,
            gates=("passed", "passed", "passed", "not_evaluated"),
            idea="inline:#original-idea",
            decision_map="not-required",
            spec="docs/missing-spec.md",
            tickets=None,
        )
        errors = self.validate_text(text)
        self.assertTrue(any("missing local target" in error for error in errors))

    def test_rejects_passed_gate_without_evidence(self):
        text = state_text(
            stage="DECISION",
            previous="DISCOVERY",
            ready=False,
            gates=("passed", "not_evaluated", "not_evaluated", "not_evaluated"),
            idea="inline:#original-idea",
            decision_map=None,
            spec=None,
            tickets=None,
            gate_evidence=("Not evaluated.", "Not evaluated.", "Not evaluated.", "Not evaluated."),
        )
        errors = self.validate_text(text)
        self.assertTrue(any("gate_1 status passed requires" in error for error in errors))

    def test_rejects_illegal_transition(self):
        text = state_text(
            stage="TICKETING",
            previous="IDEA",
            ready=False,
            gates=("passed", "passed", "passed", "not_evaluated"),
            idea="inline:#original-idea",
            decision_map="not-required",
            spec="https://example.test/spec",
            tickets=None,
        )
        errors = self.validate_text(text)
        self.assertTrue(any("illegal transition: IDEA -> TICKETING" in error for error in errors))

    def test_rejects_ready_flag_outside_ready_stage(self):
        text = state_text(
            stage="DECISION",
            previous="DISCOVERY",
            ready=True,
            gates=("passed", "not_evaluated", "not_evaluated", "not_evaluated"),
            idea="inline:#original-idea",
            decision_map=None,
            spec=None,
            tickets=None,
        )
        errors = self.validate_text(text)
        self.assertTrue(any("if and only if" in error for error in errors))

    def test_rejects_missing_direct_dependency_key(self):
        text = state_text(
            stage="IDEA",
            previous=None,
            ready=False,
            gates=("not_evaluated", "not_evaluated", "not_evaluated", "not_evaluated"),
            idea=None,
            decision_map=None,
            spec=None,
            tickets=None,
        ).replace('  to-tickets: "available"\n', "")
        errors = self.validate_text(text)
        self.assertTrue(any("dependencies must contain exactly" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
