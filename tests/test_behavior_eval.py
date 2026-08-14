from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
EVAL_ROOT = REPO_ROOT / "evals"
SCRIPT_ROOT = REPO_ROOT / "skills" / "project-preflight" / "scripts"
for path in (EVAL_ROOT, SCRIPT_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from preflight_eval import BehaviorEvalHarness, EvalBudgetRegistry  # noqa: E402
from preflight_runtime import StateChange, StateStore  # noqa: E402


class BehaviorEvalTests(unittest.TestCase):
    def setUp(self):
        self.harness = BehaviorEvalHarness(EVAL_ROOT / "cases.json")

    def test_manifest_defines_all_five_cases_and_eight_checks(self):
        self.assertEqual(5, len(self.harness.list_cases()))
        self.assertEqual(8, len(self.harness.rubric))

    def test_all_cases_prepare_and_score_through_the_eval_interface(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            prepared = {}
            for case in self.harness.list_cases():
                prepared[case["id"]] = self.harness.prepare(case["id"], root / case["id"])

            vague_store = self._store(prepared["vague-idea"])
            vague_store.initialize("vague-idea", "Watch technical creators and report what matters.")
            vague_store.record(
                StateChange(
                    dependencies={"grill-me": "available"},
                    blockers="None recorded.",
                    next_action="Continue automatically with `grill-me`; the user only answers or confirms.",
                )
            )

            blocked_store = self._store(prepared["blocked-decision"])
            blocked_store.record(
                StateChange(
                    dependencies={"wayfinder": "available"},
                    blockers="Data-source feasibility remains unresolved.",
                    next_action=(
                        "Continue Project Preflight automatically with `wayfinder`; "
                        "the user only answers or confirms."
                    ),
                )
            )

            existing_store = self._store(prepared["existing-spec-missing-discovery"])
            existing_store.initialize("existing-spec", "An existing plan with unclear users and success criteria.")
            existing_store.record(
                StateChange(
                    dependencies={"grill-me": "available"},
                    blockers="Discovery evidence is missing; later artifacts remain historical evidence.",
                    next_action="Continue automatically with `grill-me`; the user only answers or confirms.",
                )
            )

            missing_store = self._store(prepared["missing-stage-skill"])
            missing_store.record(
                StateChange(
                    dependencies={"to-tickets": "missing"},
                    blockers="`to-tickets` is absent from the active Skill catalog.",
                    next_action="Install or activate `to-tickets`, then resume Project Preflight.",
                )
            )

            invalidated_store = self._store(prepared["ready-invalidated"])
            invalidated_store.regress(
                "DECISION",
                "The selected API cannot return the required data under the current plan.",
            )

            for case_id, directory in prepared.items():
                result = self.harness.score(
                    directory,
                    model="deterministic-test-driver",
                    dependency_versions={"project-preflight": "working-tree"},
                    latency_ms=1,
                    cost_usd=0.0,
                    total_tokens=1,
                )
                self.assertTrue(result.passed, (case_id, result.to_dict()))
                self.assertEqual((8, 8), (result.score, result.maximum_score))
                self.assertIn("manifest_sha256", result.metadata)
                self.assertEqual(1, result.metadata["total_tokens"])

    def test_unchanged_fixture_cannot_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            prepared = self.harness.prepare("blocked-decision", Path(temp) / "case")
            result = self.harness.score(prepared, model="no-op")
            self.assertFalse(result.passed)
            self.assertFalse(result.checks["one_clear_next_action"].passed)

    def test_result_writes_machine_and_human_readable_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            prepared = self.harness.prepare("vague-idea", Path(temp) / "case")
            store = self._store(prepared)
            store.initialize("vague", "A vague idea.")
            store.record(
                StateChange(
                    dependencies={"grill-me": "available"},
                    blockers="None recorded.",
                    next_action="Continue automatically with `grill-me`.",
                )
            )
            result = self.harness.score(prepared, model="test-model")
            json_path = prepared / "result.json"
            markdown_path = prepared / "result.md"
            self.harness.write_result(result, json_path, markdown_path)
            self.assertIn('"score": 8', json_path.read_text(encoding="utf-8"))
            self.assertIn("| Check | Result | Evidence |", markdown_path.read_text(encoding="utf-8"))

    def test_budget_registry_enforces_token_and_latency_ceilings(self):
        registry = EvalBudgetRegistry(EVAL_ROOT / "budgets.json")
        within_budget = registry.check(
            "full-happy-path-high-reasoning",
            total_tokens=130000,
            latency_ms=720000,
        )
        over_budget = registry.check(
            "full-happy-path-high-reasoning",
            total_tokens=130001,
            latency_ms=720001,
        )

        self.assertTrue(within_budget.passed)
        self.assertFalse(over_budget.passed)
        self.assertEqual(2, len(over_budget.violations))

    @staticmethod
    def _store(prepared: Path) -> StateStore:
        workspace = prepared / "workspace"
        return StateStore(workspace / ".project" / "preflight.md", workspace)


if __name__ == "__main__":
    unittest.main()
