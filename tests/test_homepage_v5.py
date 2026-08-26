from __future__ import annotations

import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

from tools.audit_pages import audit


ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"
REGISTRY = ROOT / "registry.json"
V5_CSS = ROOT / "assets" / "kerwin-home-v5.css"
V5_JS = ROOT / "assets" / "kerwin-home-v5.js"

AXES = {
    "physical-infrastructure",
    "compute-chain",
    "agent-economy",
    "capital-macro",
    "frontier-infrastructure",
}
CONTENT_TYPES = {"earnings", "deep-dive", "brief", "interactive", "tracker"}


class HomepageV5Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.index = INDEX.read_text(encoding="utf-8")
        cls.registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        cls.javascript = V5_JS.read_text(encoding="utf-8")

    def test_v5_assets_are_versioned_and_present(self) -> None:
        self.assertTrue(V5_CSS.is_file())
        self.assertTrue(V5_JS.is_file())
        self.assertIn('/assets/kerwin-home-v5.css?v=20260826v5', self.index)
        self.assertIn('/assets/kerwin-home-v5.js?v=20260826v5', self.index)
        self.assertNotIn('kerwin-home-v4.js', self.index)

    def test_current_auditor_accepts_v5_homepage_loader(self) -> None:
        errors, _warnings = audit(ROOT / "index.html", ROOT)
        self.assertNotIn("homepage missing current homepage loader", errors)
        self.assertNotIn("homepage missing canonical homepage stylesheet", errors)

    def test_locked_brand_title_and_navigation_remain(self) -> None:
        self.assertGreaterEqual(self.index.count('home-gate__title-line'), 2)
        self.assertIn('>把复杂世界</span>', self.index)
        self.assertIn('>整理成一张投资地图</span>', self.index)
        for label in ("最近更新", "财报桌", "研究地图", "研究库", "关于 Enya"):
            self.assertIn(f">{label}</a>", self.index)
        self.assertIn('home-brand__mark">Kerwin</span>', self.index)

    def test_registry_is_the_only_runtime_source(self) -> None:
        self.assertNotIn('manualPages', self.javascript)
        self.assertNotIn('homepage overlay', self.javascript.lower())
        self.assertIn("page.axis === axis.id", self.javascript)
        self.assertIn("page.content_type === 'earnings'", self.javascript)

    def test_all_approved_entries_have_one_axis_and_content_type(self) -> None:
        approved = [item for item in self.registry if item.get("homepage_approved") is True]
        self.assertGreaterEqual(len(approved), 75)
        self.assertTrue(all(item.get("axis") in AXES for item in approved))
        self.assertTrue(all(item.get("content_type") in CONTENT_TYPES for item in approved))
        self.assertEqual(sum(1 for _ in approved), sum(1 for item in approved if item["axis"] in AXES))

    def test_featured_ranks_are_unique_and_bounded(self) -> None:
        ranks = [item["featured_rank"] for item in self.registry if item.get("featured_rank") is not None]
        self.assertEqual(sorted(ranks), [1, 2, 3])

    def test_static_fallback_contains_clickable_research(self) -> None:
        self.assertIn('/agent-economy-server-audit-cost-20260825/', self.index)
        self.assertIn('/ai-factory-agent-production-function-20260824/', self.index)
        self.assertIn('/ai-cloud-unit-economics-dashboard-20260817/', self.index)
        self.assertGreaterEqual(len(re.findall(r'class="story-link" href="/', self.index)), 8)

    def test_static_fallback_is_synchronized_with_registry(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "sync_homepage_fallback.py"), "--check"],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_seo_surface_is_complete(self) -> None:
        for path in ("robots.txt", "sitemap.xml", "favicon.svg", "site.webmanifest", "404.html"):
            self.assertTrue((ROOT / path).is_file(), path)
        self.assertIn('<link rel="canonical" href="https://enyaclawd.com/">', self.index)
        self.assertIn('property="og:image"', self.index)
        self.assertIn('type="application/ld+json"', self.index)


if __name__ == "__main__":
    unittest.main()
