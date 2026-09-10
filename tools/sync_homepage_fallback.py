#!/usr/bin/env python3
"""Keep no-JavaScript homepage/library catalog fallbacks synchronized with registry.json.

The public site is a compiled Vinext/React export. Runtime pages fetch /registry.json
and refresh after hydration, so this tool deliberately does *not* rewrite React's
server-rendered DOM or hashed bundles. Instead it maintains a small <noscript>
catalog generated from the same registry. That gives no-JS readers and crawlers a
fresh, deterministic catalog without creating hydration mismatches.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry.json"
TARGETS = (
    (ROOT / "index.html", "homepage", "最新研究 · Registry 静态目录", 5),
    (ROOT / "library" / "index.html", "library", "研究库 · Registry 静态目录", 12),
)
DATE_IN_TEXT = re.compile(r"(20\d{2})年(\d{1,2})月(\d{1,2})日")
AXIS_NAMES = {
    "physical-infrastructure": "物理基础设施",
    "compute-chain": "算力产业链",
    "agent-economy": "Token 与 Agent",
    "capital-macro": "资本与宏观",
    "frontier-infrastructure": "前沿基础设施",
}
CONTENT_NAMES = {
    "earnings": "财报",
    "deep-dive": "深度研究",
    "brief": "简报",
    "interactive": "互动工具",
    "tracker": "持续跟踪",
}


def esc(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def parsed_time(item: dict) -> datetime | None:
    for field in ("updated_at", "published_at"):
        value = item.get(field)
        if not value:
            continue
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            pass
    match = DATE_IN_TEXT.search(str(item.get("date", "")))
    if match:
        return datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)))
    return None


def timestamp(item: dict) -> float:
    value = parsed_time(item)
    return value.timestamp() if value else 0.0


def date_label(item: dict) -> str:
    value = parsed_time(item)
    return value.strftime("%Y.%m.%d") if value else "—"


def route(item: dict) -> str:
    value = str(item.get("path") or f"/{item['slug']}/")
    return value if value.startswith("/") else "/" + value


def approved_pages(registry: list[object]) -> list[dict]:
    pages = [
        item for item in registry
        if isinstance(item, dict)
        and item.get("homepage_approved") is True
        and item.get("slug")
        and item.get("title")
    ]
    return sorted(pages, key=timestamp, reverse=True)


def meta_label(item: dict) -> str:
    axis = AXIS_NAMES.get(str(item.get("axis") or ""), "研究")
    kind = CONTENT_NAMES.get(str(item.get("content_type") or ""), "研究")
    return f"{axis} · {kind}"


def render_catalog(pages: list[dict], title: str, limit: int) -> str:
    rows = []
    for item in pages[:limit]:
        rows.append(
            '<li style="padding:12px 0;border-bottom:1px solid #d8cabc">'
            f'<a href="{esc(route(item))}" style="color:#103f35;text-decoration:none">'
            f'<strong style="display:block;font-size:16px;line-height:1.45">{esc(item["title"])}</strong>'
            f'<span style="display:block;margin-top:4px;color:#746b65;font-size:12px;line-height:1.5">'
            f'{esc(date_label(item))} · {esc(meta_label(item))}</span></a></li>'
        )
    count = len(pages)
    return (
        '<noscript>'
        '<section class="kw-registry-noscript" aria-label="最新研究静态目录" '
        'style="max-width:1120px;margin:24px auto;padding:24px 32px;background:#fffaf5;'
        'border-top:4px solid #103f35;color:#262220;font-family:Arial,\'PingFang SC\',sans-serif">'
        f'<div style="font-size:11px;font-weight:800;letter-spacing:.08em;color:#9a5c38">{esc(title)}</div>'
        f'<h2 style="margin:8px 0 4px;font:700 26px/1.2 Georgia,serif">最新目录</h2>'
        f'<p style="margin:0 0 12px;color:#746b65;font-size:13px">来自 registry.json · 当前收录 {count} 篇已发布研究。启用 JavaScript 后使用完整交互目录。</p>'
        f'<ul style="list-style:none;margin:0;padding:0">{"".join(rows)}</ul>'
        '</section>'
        '</noscript>'
    )


def marker_pair(name: str) -> tuple[str, str]:
    return (
        f"<!-- REGISTRY_NOSCRIPT_FALLBACK:{name}:start -->",
        f"<!-- REGISTRY_NOSCRIPT_FALLBACK:{name}:end -->",
    )


def update_target(source: str, name: str, payload: str) -> str:
    start, end = marker_pair(name)
    block = f"{start}{payload}{end}"
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.S)
    if pattern.search(source):
        updated, count = pattern.subn(block, source, count=1)
        if count != 1:
            raise ValueError(f"expected exactly one {name} no-JS fallback block")
        return updated

    # Prefer immediately before the footer so no-JS users see the catalog in a
    # natural location. This insertion is outside React's <main> subtree and is
    # wrapped in <noscript>, so it cannot cause a hydration mismatch.
    footer_at = source.find("<footer")
    if footer_at >= 0:
        return source[:footer_at] + block + source[footer_at:]
    body_at = source.rfind("</body>")
    if body_at < 0:
        raise ValueError(f"cannot find insertion point for {name}")
    return source[:body_at] + block + source[body_at:]


def build_outputs(registry: list[object]) -> list[tuple[Path, str, str]]:
    pages = approved_pages(registry)
    if not pages:
        raise ValueError("registry has no homepage-approved entries")
    outputs = []
    for path, name, title, limit in TARGETS:
        if not path.is_file():
            raise ValueError(f"missing compiled target: {path.relative_to(ROOT)}")
        source = path.read_text(encoding="utf-8")
        expected = update_target(source, name, render_catalog(pages, title, limit))
        outputs.append((path, source, expected))
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if generated fallbacks are stale")
    args = parser.parse_args()

    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    if not isinstance(registry, list):
        raise SystemExit("registry.json must contain an array")

    outputs = build_outputs(registry)
    stale = [(path, expected) for path, source, expected in outputs if source != expected]
    if args.check:
        if stale:
            for path, _ in stale:
                print(f"stale registry no-JS fallback: {path.relative_to(ROOT)}", file=sys.stderr)
            return 1
        print("registry no-JS fallbacks synchronized")
        return 0

    if not stale:
        print("registry no-JS fallbacks already synchronized")
        return 0
    for path, expected in stale:
        path.write_text(expected, encoding="utf-8")
        print(f"synchronized registry no-JS fallback: {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
