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
