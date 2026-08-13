from __future__ import annotations

import importlib.util
import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / "skills" / "project-preflight"
SCRIPT = SKILL_ROOT / "scripts" / "validate_preflight.py"
SPEC = importlib.util.spec_from_file_location("validate_preflight_contract", SCRIPT)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


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


if __name__ == "__main__":
    unittest.main()
