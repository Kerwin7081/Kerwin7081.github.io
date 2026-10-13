from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from tools.audit_pages import audit


ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"
REGISTRY = ROOT / "registry.json"
HUB_CSS = ROOT / "assets" / "kerwin-hub.css"
HUB_JS = ROOT / "assets" / "kerwin-hub.js"

AXES = {
    "physical-infrastructure",
    "compute-chain",
    "agent-economy",
    "capital-macro",
    "frontier-infrastructure",
}
CONTENT_TYPES = {
    "earnings",
    "earnings-deep-dive",
    "deep-dive",
    "brief",
    "interactive",
    "tracker",
}


class HomepageV5Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.index = INDEX.read_text(encoding="utf-8")
        cls.registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        cls.javascript = HUB_JS.read_text(encoding="utf-8")

    def test_hub_assets_are_versioned_and_present(self) -> None:
        self.assertTrue(HUB_CSS.is_file())
        self.assertTrue(HUB_JS.is_file())
        self.assertIn('/assets/kerwin-hub.css?v=20261013hub', self.index)
        self.assertIn('/assets/kerwin-hub.js?v=20261013hub', self.index)
        self.assertIn('data-registry="/registry.json"', self.index)
        self.assertNotIn('kerwin-home-v4.js', self.index)
        self.assertNotIn('kerwin-home-v5.js', self.index)
        self.assertNotIn('home-gate', self.index)
        self.assertNotIn('2026.09.08', self.index)

    def test_current_auditor_accepts_hub_homepage_loader(self) -> None:
        errors, _warnings = audit(ROOT / "index.html", ROOT)
        self.assertNotIn("homepage missing current homepage loader", errors)
        self.assertNotIn("homepage missing canonical homepage stylesheet", errors)
        self.assertEqual(errors, [])

    def test_locked_brand_title_and_navigation_remain(self) -> None:
        self.assertIn('整理成一张投资地图。', self.index)
        self.assertIn('电力、交付与利用率。', self.index)
        self.assertIn('class="skill-promo"', self.index)
        self.assertIn('href="/kerwin-ai-investment-skill/"', self.index)
        self.assertIn('不构成投资建议', self.index)
        for label in ("首页", "研究地图", "财报桌", "研究库", "系列"):
            self.assertIn(f">{label}</a>", self.index)
        self.assertIn('>Kerwin</strong>', self.index)
        self.assertNotIn('目标价', self.index)
        self.assertNotIn('买入', self.index)

    def test_registry_is_the_only_runtime_source(self) -> None:
        self.assertNotIn('manualPages', self.javascript)
        self.assertNotIn('homepage overlay', self.javascript.lower())
        self.assertIn("homepage_approved === true", self.javascript)
        self.assertIn("item.content_type === 'earnings'", self.javascript)
        self.assertIn("item.content_type === 'earnings-deep-dive'", self.javascript)
        self.assertNotIn('text-transform', (ROOT / "assets" / "kerwin-hub.css").read_text(encoding="utf-8").split(".company")[1][:400])

    def test_all_approved_entries_have_one_axis_and_content_type(self) -> None:
        approved = [item for item in self.registry if item.get("homepage_approved") is True]
        self.assertGreaterEqual(len(approved), 75)
        self.assertTrue(all(item.get("axis") in AXES for item in approved))
        self.assertTrue(all(item.get("content_type") in CONTENT_TYPES for item in approved))
        self.assertEqual(sum(1 for _ in approved), sum(1 for item in approved if item["axis"] in AXES))

    def test_featured_ranks_are_bounded_and_cover_the_three_slots(self) -> None:
        ranks = [item["featured_rank"] for item in self.registry if item.get("featured_rank") is not None]
        self.assertTrue(ranks)
        self.assertTrue(all(rank in (1, 2, 3) for rank in ranks))
        self.assertEqual(set(ranks), {1, 2, 3})

    def test_static_fallback_contains_clickable_research(self) -> None:
        self.assertIn('请启用 JavaScript 以载入研究目录。', self.index)
        self.assertNotIn('class="story-link"', self.index)
        self.assertNotIn('class="noscript-catalog"', self.index)
        approved = [item for item in self.registry if item.get("homepage_approved") is True]
        by_slug = {item["slug"]: item for item in self.registry}
        self.assertEqual(by_slug["amd-system-level-turn-20260805"]["content_type"], "earnings-deep-dive")
        self.assertEqual(by_slug["amd-system-level-turn-20260805"]["company"], "超威")
        self.assertEqual(by_slug["dell-fy27-q2-ai-factory-20260903"]["ticker"], "DELL")
        self.assertEqual(len(approved), 110)

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
        self.assertIn('name="description"', self.index)


if __name__ == "__main__":
    unittest.main()

