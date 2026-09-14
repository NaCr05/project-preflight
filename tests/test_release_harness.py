from __future__ import annotations

import hashlib
import json
import re
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path


from scripts.release_harness import ReleaseHarness, ReleaseHarnessError


REPO_ROOT = Path(__file__).resolve().parents[1]


class ReleaseHarnessTests(unittest.TestCase):
    def test_current_repository_passes_release_inspection(self):
        self.assertEqual((), ReleaseHarness(REPO_ROOT).inspect())

    def test_version_drift_is_detected(self):
        with tempfile.TemporaryDirectory() as temp:
            copied = self._copy_repository(Path(temp))
            manifest = copied / ".codex-plugin" / "plugin.json"
            data = json.loads(manifest.read_text(encoding="utf-8"))
            data["version"] = "9.9.9"
            manifest.write_text(json.dumps(data), encoding="utf-8")
            findings = ReleaseHarness(copied).inspect()
            self.assertTrue(any(item.location == "CHANGELOG.md" for item in findings))
            self.assertTrue(any(item.location == "README.md" for item in findings))

    def test_two_builds_have_the_same_archive_hash_and_members(self):
        harness = ReleaseHarness(REPO_ROOT)
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            archive_a, checksum_a = harness.build(first)
            archive_b, checksum_b = harness.build(second)
            self.assertEqual(
                hashlib.sha256(archive_a.read_bytes()).hexdigest(),
                hashlib.sha256(archive_b.read_bytes()).hexdigest(),
            )
            self.assertEqual(checksum_a.read_text(), checksum_b.read_text())
            with zipfile.ZipFile(archive_a) as left, zipfile.ZipFile(archive_b) as right:
                self.assertEqual(left.namelist(), right.namelist())
                self.assertNotIn("scripts/release_harness.py", left.namelist())
                self.assertFalse(
                    any(name.startswith("docs/diagrams/sources/") for name in left.namelist())
                )
                for readme in ("README.md", "README.zh-CN.md"):
                    text = left.read(readme).decode("utf-8")
                    assets = set(re.findall(r'docs/diagrams/assets/[^)"\s]+', text))
                    self.assertTrue(assets, f"{readme} must expose its diagram assets")
                    for asset in assets:
                        self.assertIn(asset, left.namelist(), f"{readme}: {asset}")
                        self.assertEqual((REPO_ROOT / asset).read_bytes(), left.read(asset))

    def test_missing_required_release_file_blocks_build(self):
        for required in (
            "SUPPORT.md",
            "docs/diagrams/assets/overview.en.dark.png",
        ):
            with self.subTest(required=required), tempfile.TemporaryDirectory() as temp:
                copied = self._copy_repository(Path(temp))
                (copied / required).unlink()
                with self.assertRaises(ReleaseHarnessError):
                    ReleaseHarness(copied).build(Path(temp) / "dist")

    @staticmethod
    def _copy_repository(destination: Path) -> Path:
        copied = destination / "repository"
        shutil.copytree(
            REPO_ROOT,
            copied,
            ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc", "dist"),
        )
        return copied


if __name__ == "__main__":
    unittest.main()
