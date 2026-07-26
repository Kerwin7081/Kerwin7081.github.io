#!/usr/bin/env python3
"""Audit EnyaClawd HTML pages against the current publishing contract."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

TAGLINE = "Enya：香港首个由 OpenClaw 打造的女性投顾 Agent"
MODEL_LINE = "底层模型：GPT 5.6 Sol 及 Claude Fable 付费版"
DEFAULT_IGNORE = {".git", ".github", "preview", "previews", "publish", "staging"}


def audit(path: Path, root: Path | None) -> tuple[list[str], list[str]]:
    html = path.read_text(encoding="utf-8")
    lower = html.lower()
    errors: list[str] = []
    warnings: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    require("<title" in lower and "</title>" in lower, "missing <title>")
    require('name="viewport"' in lower or "name='viewport'" in lower, "missing viewport meta")
    require('name="description"' in lower or "name='description'" in lower, "missing meta description")

    is_home = (
        'data-page-slug="home"' in lower
        or "data-page-slug='home'" in lower
        or "site-header" in lower
        or (path.name == "index.html" and root is not None and path.parent == root)
    )
    is_experience = "kw-experience" in lower
    title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
    title_text = re.sub(r"<[^>]+>", " ", title_match.group(1) if title_match else "")
    page_signals = f"{path.parent.name} {path.stem} {title_text}".lower()
    meta_path = path.parent / "meta.json"
    if meta_path.exists():
        try:
            page_meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            page_meta = {}
        page_signals += " " + " ".join(
            str(page_meta.get(field, ""))
            for field in ("title", "slug", "category")
        ).lower()
    is_earnings = path.name == "index.html" and not is_home and any(
        token in page_signals
        for token in (
            "earnings",
            "management-call",
            "management call",
            "quarterly-results",
            "quarterly results",
            "财报",
            "业绩会",
            "电话会",
        )
    )
    has_v2_css = "kerwin-system-v2.css" in lower
    has_v2_js = "kerwin-system-v2.js" in lower
    has_v3_css = "kerwin-system-v3.css" in lower
    has_v3_js = "kerwin-system-v3.js" in lower
    has_home_css = "kerwin-home-v2.css" in lower or "kerwin-home-v3.css" in lower
    has_home_js = "kerwin-home-v3.js" in lower
    has_inline_css = "<style" in lower and "</style>" in lower
    has_shared_shell = (has_v2_css and has_v2_js) or (has_v3_css and has_v3_js)

    if is_home:
        require(has_home_css, "homepage missing canonical homepage stylesheet")
        require(has_home_js, "homepage missing kerwin-home-v3.js")
        require("access-gate" in lower, "homepage missing editorial access gate")
        require(MODEL_LINE in html, "homepage missing current model line")
    else:
        require(
            has_shared_shell or has_inline_css,
            "page has neither a complete shared shell nor self-contained inline CSS",
        )
        if has_v2_css != has_v2_js:
            errors.append("legacy v2 shared shell is incomplete: CSS and JS must appear together")
        if has_v3_css != has_v3_js:
            errors.append("v3 shared shell is incomplete: CSS and JS must appear together")
        if has_v2_css and has_v2_js:
            warnings.append("uses frozen legacy kerwin-system-v2 assets; do not overwrite, migrate by page")

        require(
            "kw-research" in lower
            or "kw-experience" in lower
            or has_inline_css,
            "missing page mode or self-contained page styling",
        )

        if not is_experience:
            require(
                TAGLINE in html or has_v2_js or has_v3_js,
                "missing Enya tagline or injected brand block",
            )
            require(
                MODEL_LINE in html or has_v2_js or has_v3_js,
                "missing current model line or injected brand block",
            )
            require('href="/"' in lower or "href='/'" in lower, "missing homepage route")
            require(
                "免责声明" in html or "不构成" in html or has_v2_js or has_v3_js,
                "missing disclaimer",
            )
            if not (has_v2_js or has_v3_js or "输入 “k” 即可显示" in html):
                warnings.append("standard page has no editorial k/K access interaction")

    if re.search(
        r"请输入\s*<strong>k</strong>|<input[^>]+id=[\"']gate-input[\"']|<div[^>]+id=[\"']gate-overlay[\"']",
        html,
        re.I,
    ):
        warnings.append("legacy single-letter access gate remains")
    if "gpt-5.5" in lower or "gpt 5.5" in lower:
        warnings.append("contains obsolete GPT-5.5 model copy")
    if "http://" in lower:
        warnings.append("contains insecure http:// link")
    if 'target="_blank"' in lower and "noopener" not in lower:
        warnings.append("external target=_blank link may lack noopener")
    if "<table" in lower and not any(
        token in lower
        for token in ("table-wrap", "matrix", "compare", "overflow-x:auto", "overflow-x: auto")
    ):
        warnings.append("table may lack a horizontal overflow wrapper")

    if is_earnings:
        nav_match = re.search(
            r"<nav[^>]*class=[\"'][^\"']*\bnav\b[^\"']*[\"'][^>]*>(.*?)</nav>",
            html,
            re.I | re.S,
        )
        if nav_match:
            nav_count = len(re.findall(r"<a\b", nav_match.group(1), re.I))
            if nav_count > 7:
                warnings.append(f"earnings page navigation has {nav_count} entries; target 5–7")

        internal_note_patterns = (
            "截图工具",
            "技术错误，因此",
            "crawler error",
            "workflow failed",
            "调试说明",
            "debugging note",
        )
        if any(pattern.lower() in lower for pattern in internal_note_patterns):
            errors.append("public earnings copy contains an internal production or debugging note")

        order_signal_count = sum(
            lower.count(token)
            for token in ("订单", "bookings", "backlog", "contracted capacity")
        )
        if order_signal_count >= 3:
            has_conversion_terms = (
                "收入" in html
                and "利润" in html
                and ("自由现金流" in html or "free cash flow" in lower)
            )
            has_conversion_visual = any(
                token in lower
                for token in ("funnel", "order-to-cash", "订单到自由现金流", "订单到现金")
            )
            require(
                has_conversion_terms and has_conversion_visual,
                "order-led earnings thesis lacks an explicit order-to-revenue-to-profit-to-cash path",
            )

        if not any(token in html for token in ("估值", "再评级", "目标价", "Valuation")):
            warnings.append("earnings page has no explicit valuation or rerating framework")

        related_start = max(html.find("下一条研究路径"), html.find("相关研究"))
        if related_start < 0:
            warnings.append("earnings page has no related-research reading path")
        else:
            related_end = html.find("</section>", related_start)
            related_snippet = html[
                related_start : related_end if related_end > related_start else None
            ]
            related_links = len(re.findall(r'href=["\']/[^"\']+', related_snippet, re.I))
            if related_links == 0:
                warnings.append("related-research section contains no internal route")
            elif related_links > 3:
                warnings.append(
                    f"related-research path has {related_links} links; maximum is 3"
                )

        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                errors.append(f"invalid sibling meta.json: {exc}")
            else:
                for field in ("published_at", "updated_at"):
                    if not meta.get(field):
                        errors.append(f"earnings page meta.json missing {field}")
                for field in ("title", "slug", "date", "author", "category", "summary"):
                    if not meta.get(field):
                        warnings.append(f"earnings page meta.json missing {field}")

    if root:
        for href in re.findall(r'href=["\'](/[^"\'#?]+)', html, re.I):
            if href.startswith("//") or href.startswith("/assets/"):
                continue
            candidate = root / href.lstrip("/")
            if href.endswith("/"):
                candidate /= "index.html"
            elif candidate.suffix == "":
                candidate /= "index.html"
            if not candidate.exists():
                warnings.append(f"unresolved internal link: {href}")

    return errors, sorted(set(warnings))


def discover_pages(root: Path) -> list[Path]:
    """Find production page entrypoints while excluding preview and staging trees."""
    pages: list[Path] = []
    for path in root.rglob("index.html"):
        relative = path.relative_to(root)
        if any(part in DEFAULT_IGNORE for part in relative.parts):
            continue
        pages.append(path)
    return sorted(pages)


def resolve_page(page: Path, root: Path) -> Path:
    if page.is_absolute():
        return page.resolve()
    from_working_directory = (Path.cwd() / page).resolve()
    if from_working_directory.exists():
        return from_working_directory
    return (root / page).resolve()


def display_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path)


def inspect_page(path: Path, root: Path) -> dict[str, object]:
    if not path.is_file():
        errors = ["page does not exist or is not a file"]
        warnings: list[str] = []
    else:
        try:
            errors, warnings = audit(path, root)
        except (OSError, UnicodeError) as exc:
            errors = [f"unable to read page: {exc}"]
            warnings = []

    return {
        "path": display_path(path, root),
        "issues": errors,
        "warnings": warnings,
        "ok": not errors,
    }


def print_human(results: list[dict[str, object]]) -> None:
    for result in results:
        issues = result["issues"]
        warnings = result["warnings"]
        state = "PASS" if result["ok"] else "FAIL"
        print(f"[{state}] {result['path']}")
        for item in issues:
            print(f"  error: {item}")
        for item in warnings:
            print(f"  warning: {item}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "pages",
        nargs="*",
        type=Path,
        help="HTML page(s) to audit; defaults to production index.html entrypoints",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Local site root for discovery and internal-link checks",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the backwards-compatible JSON report for explicitly named pages",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return a non-zero status when the default full-site scan finds errors",
    )
    args = parser.parse_args()

    root = args.root.resolve()
    pages = (
        [resolve_page(page, root) for page in args.pages]
        if args.pages
        else discover_pages(root)
    )
    results = [inspect_page(page, root) for page in pages]
    bad_count = sum(not result["ok"] for result in results)
    warning_count = sum(bool(result["warnings"]) for result in results)
    json_mode = args.json or not args.pages

    if json_mode:
        print(
            json.dumps(
                {
                    "total_html": len(results),
                    "with_issues": bad_count,
                    "with_warnings": warning_count,
                    "results": results,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print_human(results)

    should_fail = bad_count > 0 and (bool(args.pages) or args.strict)
    return 1 if should_fail else 0


if __name__ == "__main__":
    sys.exit(main())
