from __future__ import annotations

import importlib.util
import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / "skills" / "project-preflight"
SCRIPT = SKILL_ROOT / "scripts" / "validate_preflight.py"
SPEC = importlib.util.spec_from_file_location("validate_preflight_contract", SCRIPT)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)
if str(SCRIPT.parent) not in sys.path:
    sys.path.insert(0, str(SCRIPT.parent))

from preflight_runtime._contract import (  # noqa: E402
    STAGE_ADAPTERS,
)
from preflight_runtime._projections import ContractProjection  # noqa: E402


class RepositoryContractTests(unittest.TestCase):
    def test_readme_language_switches_are_reciprocal(self):
        english = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        chinese = (REPO_ROOT / "README.zh-CN.md").read_text(encoding="utf-8")
        self.assertIn("[简体中文](README.zh-CN.md)", english)
        self.assertIn("[English](README.md)", chinese)
        self.assertIn("(docs/workflow.md)", english)
        self.assertIn("(docs/workflow.zh-CN.md)", chinese)

    def test_workflow_guides_are_reciprocal_and_have_mermaid_maps(self):
        english = (REPO_ROOT / "docs" / "workflow.md").read_text(encoding="utf-8")
        chinese = (REPO_ROOT / "docs" / "workflow.zh-CN.md").read_text(encoding="utf-8")
        self.assertIn("[简体中文](workflow.zh-CN.md)", english)
        self.assertIn("[English](workflow.md)", chinese)
        self.assertIn("```mermaid", english)
        self.assertIn("```mermaid", chinese)
        self.assertIn("READY_FOR_IMPLEMENTATION", english)
        self.assertIn("READY_FOR_IMPLEMENTATION", chinese)

    def test_distributable_skill_has_no_obsolete_to_prd_name(self):
        matches = []
        for path in SKILL_ROOT.rglob("*"):
            if path.is_file() and path.suffix in {".md", ".yaml", ".py"}:
                if "to-prd" in path.read_text(encoding="utf-8"):
                    matches.append(str(path.relative_to(REPO_ROOT)))
        self.assertEqual([], matches)

    def test_skill_markdown_links_exist(self):
        skill = SKILL_ROOT / "SKILL.md"
        text = skill.read_text(encoding="utf-8")
        missing = []
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
            if target.startswith(("http://", "https://", "#")):
                continue
            path = (skill.parent / target.split("#", 1)[0]).resolve()
            if not path.exists():
                missing.append(target)
        self.assertEqual([], missing)

    def test_skill_md_is_ascii_compatible_with_windows_validator(self):
        text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        text.encode("ascii")

    def test_preflight_asset_is_a_valid_initial_state(self):
        asset = SKILL_ROOT / "assets" / "preflight-template.md"
        errors, data = VALIDATOR.validate_path(asset, asset.parent)
        self.assertEqual([], errors)
        self.assertEqual("IDEA", data["current_stage"])

    def test_openai_default_prompt_invokes_skill_explicitly(self):
        metadata = (SKILL_ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertIn("$project-preflight", metadata)

    def test_runtime_docs_are_exact_projections_of_the_canonical_registry(self):
        self.assertEqual((), ContractProjection(REPO_ROOT).check())

    def test_projection_module_detects_and_repairs_document_drift(self):
        with tempfile.TemporaryDirectory() as temp:
            copied = Path(temp) / "repository"
            shutil.copytree(
                REPO_ROOT,
                copied,
                ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"),
            )
            workflow = copied / "skills" / "project-preflight" / "references" / "workflow.md"
            workflow.write_text(
                workflow.read_text(encoding="utf-8").replace(
                    "`project-preflight-grill-me`",
                    "`project-preflight-wayfinder`",
                    1,
                ),
                encoding="utf-8",
            )
            projection = ContractProjection(copied)
            self.assertTrue(any(item.path.endswith("workflow.md") for item in projection.check()))
            self.assertEqual(
                ("skills/project-preflight/references/workflow.md",),
                projection.write(),
            )
            self.assertEqual((), projection.check())
            self.assertEqual((), projection.write())

    def test_projection_module_detects_eval_mapping_drift(self):
        with tempfile.TemporaryDirectory() as temp:
            copied = Path(temp) / "repository"
            shutil.copytree(
                REPO_ROOT,
                copied,
                ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"),
            )
            cases_path = copied / "evals" / "cases.json"
            cases = json.loads(cases_path.read_text(encoding="utf-8"))
            cases["cases"][0]["expected"]["directive"]["adapter_skill"] = (
                "project-preflight-wayfinder"
            )
            cases_path.write_text(json.dumps(cases), encoding="utf-8")
            findings = ContractProjection(copied).check()
            self.assertTrue(any("directive mapping" in item.message for item in findings))

    def test_behavior_eval_manifest_is_canonical_and_complete(self):
        manifest = json.loads((REPO_ROOT / "evals" / "cases.json").read_text(encoding="utf-8"))
        self.assertEqual(1, manifest["schema_version"])
        self.assertEqual(8, len(manifest["rubric"]))
        self.assertEqual(8, len(manifest["cases"]))
        self.assertEqual(8, len({case["id"] for case in manifest["cases"]}))
        self.assertEqual(
            {"positive": 5, "negative": 3},
            {
                kind: sum(case["submission_kind"] == kind for case in manifest["cases"])
                for kind in ("positive", "negative")
            },
        )

    def test_plugin_and_current_architecture_decision_exist(self):
        self.assertTrue((REPO_ROOT / "CONTEXT.md").is_file())
        self.assertTrue(
            (REPO_ROOT / "docs" / "decisions" / "0003-single-entry-automatic-orchestration-plugin.md").is_file()
        )
        self.assertTrue(
            (REPO_ROOT / "docs" / "decisions" / "0005-outcome-oriented-preflight-session.md").is_file()
        )
        manifest = json.loads((REPO_ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual("project-preflight", manifest["name"])
        self.assertEqual("./skills/", manifest["skills"])

    def test_release_harness_and_budget_are_current(self):
        manifest = json.loads(
            (REPO_ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        version = manifest["version"]
        changelog = (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn(f"## [{version}]", changelog)
        for path in (
            "README.md",
            "README.zh-CN.md",
            "CONTRIBUTING.md",
            "SECURITY.md",
            ".github/workflows/ci.yml",
            ".github/workflows/release.yml",
            "docs/upstream-adapter-policy.md",
            "docs/decisions/0004-public-release-hardening.md",
        ):
            self.assertTrue((REPO_ROOT / path).is_file(), path)

        budgets = json.loads((REPO_ROOT / "evals" / "budgets.json").read_text(encoding="utf-8"))
        self.assertEqual(1, budgets["schema_version"])
        profile = budgets["profiles"]["full-happy-path-high-reasoning"]
        baseline = profile["baseline"]
        ceiling = profile["regression_ceiling"]
        self.assertTrue((REPO_ROOT / baseline["source"]).is_file())
        self.assertGreater(ceiling["total_tokens"], baseline["total_tokens_approx"])
        self.assertGreater(ceiling["latency_ms"], baseline["latency_ms_approx"])

    def test_public_readiness_routes_and_workflows_exist(self):
        for path in (
            "SUPPORT.md",
            "docs/privacy.md",
            "docs/terms.md",
            "docs/plugin-submission.md",
            "docs/knowledge-map.json",
            ".github/ISSUE_TEMPLATE/bug.yml",
            ".github/ISSUE_TEMPLATE/feature.yml",
            ".github/pull_request_template.md",
            "scripts/release_harness.py",
        ):
            self.assertTrue((REPO_ROOT / path).is_file(), path)

        for path in (".github/workflows/ci.yml", ".github/workflows/release.yml"):
            workflow = (REPO_ROOT / path).read_text(encoding="utf-8")
            self.assertIn("python scripts/release_harness.py verify", workflow)
        release = (REPO_ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
        self.assertIn("release_harness.py build", release)

        for path in ("README.md", "README.zh-CN.md"):
            text = (REPO_ROOT / path).read_text(encoding="utf-8")
            self.assertIn("GitHub Release", text)
            self.assertIn("Plugin Directory", text)
            self.assertIn("scripts/release_harness.py verify", text)

    def test_readmes_document_synced_quick_start_and_lifecycle_commands(self):
        headings = {
            "README.md": "## Quick start from source",
            "README.zh-CN.md": "## 从源码快速开始",
        }
        for path, heading in headings.items():
            text = (REPO_ROOT / path).read_text(encoding="utf-8")
            self.assertIn(heading, text)
            self.assertIn("git clone https://github.com/NaCr05/project-preflight.git", text)
            self.assertIn("Use $plugin-creator to add the existing Plugin", text)
            self.assertIn("codex plugin add project-preflight@personal", text)
            self.assertIn("codex plugin list", text)
            self.assertIn("Use $project-preflight.", text)
            self.assertIn(".project/preflight.md", text)
            self.assertIn("codex plugin remove project-preflight@personal", text)
            self.assertIn("pull --ff-only", text)

    def test_all_stage_adapters_are_bundled_and_implicitly_invokable(self):
        for adapter in STAGE_ADAPTERS.values():
            root = REPO_ROOT / "skills" / adapter
            self.assertTrue((root / "SKILL.md").is_file())
            metadata = (root / "agents" / "openai.yaml").read_text(encoding="utf-8")
            self.assertIn("allow_implicit_invocation: true", metadata)
            skill_text = (root / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("Never ask the user to invoke another Skill", skill_text)
            self.assertIn("Do not choose a target Stage or Gate", skill_text)

    def test_primary_skill_uses_the_outcome_oriented_session_seam(self):
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("current --json", skill)
        self.assertIn("apply --json", skill)
        self.assertIn("StageOutcome", skill)
        self.assertIn("compatibility interfaces", skill)


if __name__ == "__main__":
    unittest.main()
