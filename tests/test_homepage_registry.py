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
                        "axis": "compute-chain",
                        "content_type": "deep-dive",
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
            "--axis",
            "compute-chain",
            "--content-type",
            "deep-dive",
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
                        "axis": "capital-macro",
                        "content_type": "brief",
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
            "--axis",
            "agent-economy",
            "--content-type",
            "deep-dive",
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

    def test_approve_records_structured_homepage_fields(self) -> None:
        result = self.run_tool(
            "approve",
            "--slug",
            "structured-topic",
            "--title",
            "Structured topic",
            "--date",
            "2026年8月26日",
            "--deck",
            "A decision-focused summary.",
            "--tag",
            "AI Factory",
            "--published-at",
            "2026-08-26T18:00:00+08:00",
            "--axis",
            "physical-infrastructure",
            "--content-type",
            "deep-dive",
            "--series-id",
            "ai-factory",
            "--series-title",
            "AI Factory生产函数",
            "--series-order",
            "7",
            "--homepage-deck",
            "Homepage summary.",
            "--status",
            "updated",
        )

        self.assertEqual(result.returncode, 0, result.stdout)
        item = json.loads(self.registry.read_text(encoding="utf-8"))[0]
        self.assertEqual(item["axis"], "physical-infrastructure")
        self.assertEqual(item["content_type"], "deep-dive")
        self.assertEqual(item["series_id"], "ai-factory")
        self.assertEqual(item["series_order"], 7)
        self.assertEqual(item["status"], "updated")

    def test_validate_rejects_duplicate_featured_rank(self) -> None:
        site_root = Path(self.temporary_directory.name)
        for slug in ("first", "second"):
            page_dir = site_root / slug
            page_dir.mkdir()
            (page_dir / "index.html").write_text("ok", encoding="utf-8")
        self.registry.write_text(
            json.dumps(
                [
                    {
                        "slug": slug,
                        "title": slug.title(),
                        "date": "2026年8月26日",
                        "deck": "Deck",
                        "tag": "Research",
                        "source": "enya",
                        "homepage_approved": True,
                        "published_at": "2026-08-26T10:00:00+08:00",
                        "axis": "agent-economy",
                        "content_type": "deep-dive",
                        "featured_rank": 1,
                    }
                    for slug in ("first", "second")
                ]
            ),
            encoding="utf-8",
        )

        result = self.run_tool("validate", "--site-root", str(site_root))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("featured_rank 1 already used", result.stdout)


if __name__ == "__main__":
    unittest.main()
