from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TOOL = PROJECT_ROOT / "tools" / "homepage_registry.py"


class HomepageRegistryToolTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.registry = Path(self.temporary_directory.name) / "registry.json"

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def run_tool(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(TOOL),
                "--registry",
                str(self.registry),
                *args,
            ],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )

    def test_update_preserves_optional_registry_fields(self) -> None:
        self.registry.write_text(
            json.dumps(
                [
                    {
                        "slug": "topic",
                        "title": "Old",
                        "date": "2026年7月25日",
                        "deck": "Old deck",
                        "tag": "Research",
                        "category": "AI",
                        "source": "enya",
                        "homepage_approved": True,
                        "published_at": "2026-07-25T10:00:00+08:00",
                        "path": "/topic/",
                        "featured_rank": 1,
                    }
                ]
            ),
            encoding="utf-8",
        )

        result = self.run_tool(
            "approve",
            "--slug",
            "topic",
            "--title",
            "New",
            "--date",
            "2026年7月26日",
            "--deck",
            "New deck",
            "--tag",
            "Research",
            "--published-at",
            "2026-07-26T10:00:00+08:00",
        )

        self.assertEqual(result.returncode, 0, result.stdout)
        item = json.loads(self.registry.read_text(encoding="utf-8"))[0]
        self.assertEqual(item["title"], "New")
        self.assertEqual(item["category"], "AI")
        self.assertEqual(item["path"], "/topic/")
        self.assertEqual(item["featured_rank"], 1)

    def test_new_feature_replaces_the_same_rank(self) -> None:
        self.registry.write_text(
            json.dumps(
                [
                    {
                        "slug": "old",
                        "title": "Old",
                        "date": "2026年7月25日",
                        "deck": "Old deck",
                        "tag": "Research",
                        "source": "enya",
                        "homepage_approved": True,
                        "published_at": "2026-07-25T10:00:00+08:00",
                        "featured_rank": 2,
                    }
                ]
            ),
            encoding="utf-8",
        )

        result = self.run_tool(
            "approve",
            "--slug",
            "new",
            "--title",
            "New",
            "--date",
            "2026年7月26日",
            "--deck",
            "New deck",
            "--tag",
            "Research",
            "--published-at",
            "2026-07-26T10:00:00+08:00",
            "--featured-rank",
            "2",
        )

        self.assertEqual(result.returncode, 0, result.stdout)
        items = {
            item["slug"]: item
            for item in json.loads(self.registry.read_text(encoding="utf-8"))
        }
        self.assertNotIn("featured_rank", items["old"])
        self.assertEqual(items["new"]["featured_rank"], 2)


if __name__ == "__main__":
    unittest.main()
