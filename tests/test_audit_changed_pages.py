from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
GUARD = PROJECT_ROOT / "tools" / "audit_changed_pages.py"
STUB_AUDITOR = """\
import sys

print("AUDITOR_ARGS=" + "|".join(sys.argv[1:]))
raise SystemExit(0)
"""
MINIMAL_HTML = """\
<!doctype html>
<html lang="zh-HK">
<head>
<meta name="viewport" content="width=device-width">
<meta name="description" content="test">
<title>Test</title>
</head>
<body><a href="/">Home</a><p>免责声明</p></body>
</html>
"""


class ChangedPageAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.repo = Path(self.temporary_directory.name)
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Audit Test")
        self.git("config", "user.email", "audit@example.invalid")
        self.write("tools/audit_pages.py", STUB_AUDITOR)
        self.write("index.html", MINIMAL_HTML)
        self.write("legacy/index.html", "<html>legacy debt</html>")
        self.commit("base")

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def git(self, *args: str) -> str:
        completed = subprocess.run(
            ["git", "-C", str(self.repo), *args],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return completed.stdout.strip()

    def write(self, relative_path: str, content: str) -> None:
        path = self.repo / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def commit(self, message: str) -> str:
        self.git("add", ".")
        self.git("commit", "-m", message)
        return self.git("rev-parse", "HEAD")

    def run_guard(self, base: str, head: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(GUARD),
                "--root",
                str(self.repo),
                "--base",
                base,
                "--head",
                head,
            ],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )

    def valid_meta(self, slug: str) -> str:
        return json.dumps(
            {
                "title": "Test",
                "slug": slug,
                "date": "2026-07-26",
                "homepage_approved": False,
                "published_at": "2026-07-26T15:00:00+08:00",
                "updated_at": "2026-07-26T15:00:00+08:00",
            },
            ensure_ascii=False,
        )

    def test_audits_only_new_production_page(self) -> None:
        base = self.git("rev-parse", "HEAD")
        self.write("new-topic/index.html", MINIMAL_HTML)
        self.write("new-topic/meta.json", self.valid_meta("new-topic"))
        head = self.commit("add page")

        result = self.run_guard(base, head)

        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("new-topic/index.html", result.stdout)
        self.assertNotIn("legacy/index.html", result.stdout)

    def test_meta_change_audits_sibling_page(self) -> None:
        self.write("topic/index.html", MINIMAL_HTML)
        self.write("topic/meta.json", self.valid_meta("topic"))
        base = self.commit("add existing topic")
        meta = json.loads((self.repo / "topic/meta.json").read_text(encoding="utf-8"))
        meta["updated_at"] = "2026-07-26T16:00:00+08:00"
        self.write("topic/meta.json", json.dumps(meta))
        head = self.commit("update metadata")

        result = self.run_guard(base, head)

        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("topic/index.html", result.stdout)

    def test_rejects_new_temporary_path(self) -> None:
        base = self.git("rev-parse", "HEAD")
        self.write("publish/draft/index.html", MINIMAL_HTML)
        head = self.commit("add temporary page")

        result = self.run_guard(base, head)

        self.assertEqual(result.returncode, 1)
        self.assertIn("new files are not allowed", result.stdout)

    def test_allows_existing_temporary_page_cleanup(self) -> None:
        self.write("publish/old/index.html", "<html>old</html>")
        base = self.commit("add historical temporary page")
        self.write("publish/old/index.html", "<html>redirect</html>")
        head = self.commit("replace historical temporary page")

        result = self.run_guard(base, head)

        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("No production HTML page was affected", result.stdout)

    def test_rejects_frozen_v2_asset_change(self) -> None:
        self.write("assets/kerwin-system-v2.css", "/* frozen */")
        base = self.commit("add frozen asset")
        self.write("assets/kerwin-system-v2.css", "/* changed */")
        head = self.commit("change frozen asset")

        result = self.run_guard(base, head)

        self.assertEqual(result.returncode, 1)
        self.assertIn("frozen legacy v2 asset", result.stdout)

    def test_rejects_duplicate_registry_slug(self) -> None:
        base = self.git("rev-parse", "HEAD")
        entry = {
            "slug": "legacy",
            "title": "Legacy",
            "date": "2026年7月26日",
            "deck": "Test",
            "tag": "Test",
            "source": "enya",
            "homepage_approved": True,
            "published_at": "2026-07-26T15:00:00+08:00",
        }
        self.write("registry.json", json.dumps([entry, entry]))
        head = self.commit("add invalid registry")

        result = self.run_guard(base, head)

        self.assertEqual(result.returncode, 1)
        self.assertIn("duplicate slug", result.stdout)

    def test_accepts_explicit_legacy_public_path(self) -> None:
        self.write("legacy-topic.html", MINIMAL_HTML)
        base = self.commit("add historical legacy page")
        entry = {
            "slug": "legacy-topic",
            "title": "Legacy",
            "date": "2026年7月26日",
            "deck": "Test",
            "tag": "Test",
            "source": "codex",
            "homepage_approved": True,
            "published_at": "2026-07-26T15:00:00+08:00",
            "path": "/legacy-topic.html",
        }
        self.write("registry.json", json.dumps([entry]))
        head = self.commit("add explicit legacy route")

        result = self.run_guard(base, head)

        self.assertEqual(result.returncode, 0, result.stdout)

    def test_rejects_duplicate_featured_rank(self) -> None:
        base = self.git("rev-parse", "HEAD")
        entries = []
        for slug in ("legacy", "second"):
            self.write(f"{slug}/index.html", MINIMAL_HTML)
            entries.append(
                {
                    "slug": slug,
                    "title": slug,
                    "date": "2026年7月26日",
                    "deck": "Test",
                    "tag": "Test",
                    "source": "enya",
                    "homepage_approved": True,
                    "published_at": "2026-07-26T15:00:00+08:00",
                    "featured_rank": 1,
                }
            )
        self.write("registry.json", json.dumps(entries))
        head = self.commit("add duplicate featured rank")

        result = self.run_guard(base, head)

        self.assertEqual(result.returncode, 1)
        self.assertIn("duplicate featured_rank", result.stdout)

    def test_rejects_hardcoded_homepage_content_fallback(self) -> None:
        self.write(
            "assets/kerwin-home-v3.js",
            "var current = true;\nArray.isArray(registry);\np.featured_rank;\np.path;\n",
        )
        base = self.commit("add current homepage loader")
        self.write(
            "assets/kerwin-home-v3.js",
            "var legacyPages = [];\nArray.isArray(registry);\np.featured_rank;\np.path;\n",
        )
        head = self.commit("restore duplicate fallback")

        result = self.run_guard(base, head)

        self.assertEqual(result.returncode, 1)
        self.assertIn("obsolete loader logic remains", result.stdout)


if __name__ == "__main__":
    unittest.main()
