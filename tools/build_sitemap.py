#!/usr/bin/env python3
"""Build the public sitemap from the approved homepage registry."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry.json"
OUTPUT = ROOT / "sitemap.xml"
BASE_URL = "https://enyaclawd.com"


def page_path(item: dict) -> str:
    return item.get("path") or f"/{item['slug']}/"


def last_modified(item: dict) -> str:
    value = item.get("updated_at") or item.get("published_at") or ""
    if not value:
        return ""
    try:
        return datetime.fromisoformat(value).date().isoformat()
    except ValueError:
        return ""


def build() -> None:
    items = json.loads(REGISTRY.read_text(encoding="utf-8"))
    approved = [item for item in items if item.get("homepage_approved") is True]
    approved.sort(key=lambda item: item.get("updated_at") or item.get("published_at") or "", reverse=True)
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        "  <url>",
        f"    <loc>{BASE_URL}/</loc>",
        "    <changefreq>daily</changefreq>",
        "    <priority>1.0</priority>",
        "  </url>",
    ]
    for item in approved:
        path = "/" + page_path(item).lstrip("/")
        lines.extend(["  <url>", f"    <loc>{escape(BASE_URL + path)}</loc>"])
        modified = last_modified(item)
        if modified:
            lines.append(f"    <lastmod>{modified}</lastmod>")
        lines.extend(["    <priority>0.8</priority>", "  </url>"])
    lines.append("</urlset>")
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"built sitemap: {len(approved) + 1} URLs")


if __name__ == "__main__":
    build()
