#!/usr/bin/env python3
"""Synchronize the homepage's no-JavaScript fallback with registry.json."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"
REGISTRY = ROOT / "registry.json"

AXIS_NAMES = {
    "physical-infrastructure": "Physical Infrastructure",
    "compute-chain": "Compute Chain",
    "agent-economy": "Agent Economy",
    "capital-macro": "Capital & Macro",
    "frontier-infrastructure": "Frontier Infrastructure",
}

DATE_IN_TEXT = re.compile(r"(20\d{2})年(\d{1,2})月(\d{1,2})日")


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
        return datetime(
            int(match.group(1)), int(match.group(2)), int(match.group(3))
        )
    return None


def timestamp(item: dict) -> float:
    value = parsed_time(item)
    return value.timestamp() if value else 0.0


def date_label(item: dict) -> str:
    value = parsed_time(item)
    if value:
        return value.strftime("%m.%d")
    return "—"


def approved_pages(registry: list[object]) -> list[dict]:
    return [
        item
        for item in registry
        if isinstance(item, dict) and item.get("homepage_approved") is True
    ]


def route(item: dict) -> str:
    value = str(item.get("path") or f"/{item['slug']}/")
    return value if value.startswith("/") else "/" + value


def summary(item: dict) -> str:
    return str(item.get("homepage_deck") or item.get("deck") or "")


def axis_name(item: dict) -> str:
    return AXIS_NAMES.get(str(item.get("axis") or ""), "Research")


def feature_rank(item: dict) -> int:
    rank = item.get("featured_rank")
    return rank if isinstance(rank, int) and not isinstance(rank, bool) else 99


def feature_sort_key(item: dict) -> tuple[int, float]:
    return feature_rank(item), -timestamp(item)


def select_recent_auxiliary(ranked: list[dict], lead: dict, limit: int = 3) -> list[dict]:
    selected: list[dict] = []
    selected_slugs = {lead.get("slug")}
    used_series = {lead["series_id"]} if lead.get("series_id") else set()
    used_axes = {lead["axis"]} if lead.get("axis") else set()

    for page in ranked:
        if len(selected) >= limit or page.get("slug") in selected_slugs:
            continue
        if not page.get("featured_rank"):
            continue
        if page.get("series_id") and page["series_id"] in used_series:
            continue
        selected.append(page)
        selected_slugs.add(page.get("slug"))
        if page.get("series_id"):
            used_series.add(page["series_id"])
        if page.get("axis"):
            used_axes.add(page["axis"])

    for page in ranked:
        if len(selected) >= limit or page.get("slug") in selected_slugs:
            continue
        if page.get("series_id") and page["series_id"] in used_series:
            continue
        if page.get("axis") and page["axis"] in used_axes:
            continue
        selected.append(page)
        selected_slugs.add(page.get("slug"))
        if page.get("series_id"):
            used_series.add(page["series_id"])
        if page.get("axis"):
            used_axes.add(page["axis"])

    for page in ranked:
        if len(selected) >= limit or page.get("slug") in selected_slugs:
            continue
        if page.get("series_id") and page["series_id"] in used_series:
            continue
        selected.append(page)
        selected_slugs.add(page.get("slug"))
        if page.get("series_id"):
            used_series.add(page["series_id"])
    return selected


def render_recent_lead(item: dict) -> str:
    title = str(item.get("title") or "未命名专题")
    return (
        f'<div class="recent-lead__kicker">Featured Research · {esc(date_label(item))}</div>'
        f"<h3>{esc(title)}</h3>"
        f"<p>{esc(summary(item))}</p>"
        f'<a class="story-link" href="{esc(route(item))}" aria-label="阅读{esc(title)}"></a>'
    )


def render_dispatch_row(item: dict) -> str:
    title = str(item.get("title") or "未命名专题")
    label = item.get("series_title") or axis_name(item)
    return (
        '<article class="dispatch-row">'
        f'<div class="dispatch-row__date">{esc(date_label(item))}</div>'
        f"<div><b>{esc(title)}</b><span>{esc(label)}</span></div>"
        '<span>↗</span>'
        f'<a class="story-link" href="{esc(route(item))}" aria-label="阅读{esc(title)}"></a>'
        "</article>"
    )


def render_series(pages: list[dict]) -> str:
    groups: dict[str, list[dict]] = defaultdict(list)
    for item in pages:
        series_id = item.get("series_id")
        if series_id:
            groups[str(series_id)].append(item)

    ordered = sorted(
        (
            (series_id, group)
            for series_id, group in groups.items()
            if len(group) >= 2
        ),
        key=lambda pair: max(timestamp(item) for item in pair[1]),
        reverse=True,
    )[:3]

    cards = []
    for series_id, group in ordered:
        orders = sorted(
            item["series_order"]
            for item in group
            if isinstance(item.get("series_order"), int)
            and not isinstance(item.get("series_order"), bool)
        )
        if not orders:
            range_label = "持续更新"
        elif orders[0] == orders[-1]:
            range_label = f"第 {orders[-1]} 篇"
        else:
            range_label = f"第 {orders[0]}–{orders[-1]} 篇"
        title = next(
            (str(item.get("series_title")) for item in group if item.get("series_title")),
            series_id,
        )
        cards.append(
            f'<a href="#library" data-series-link="{esc(series_id)}">'
            f"<b>{esc(title)}</b><span>{len(group)} 篇 · {esc(range_label)}</span></a>"
        )
    return "\n".join(cards)


def render_ticker(pages: list[dict]) -> str:
    selected: list[dict] = []
    seen: set[str] = set()
    for item in sorted(pages, key=timestamp, reverse=True):
        key = str(item.get("series_id") or item.get("slug"))
        if key in seen:
            continue
        seen.add(key)
        selected.append(item)
        if len(selected) >= 7:
            break
    return "\n".join(
        f'<a href="{esc(route(item))}"><b>{esc(item.get("title") or "未命名专题")}</b>'
        f"<small>{esc(date_label(item))}</small></a>"
        for item in selected
    )


def render_library_row(item: dict) -> str:
    title = str(item.get("title") or "未命名专题")
    badges = []
    if item.get("series_title"):
        order = item.get("series_order")
        suffix = f" · {order}" if isinstance(order, int) and not isinstance(order, bool) else ""
        badges.append(f"<span>{esc(item['series_title'])}{suffix}</span>")
    if item.get("status") and item["status"] != "evergreen":
        status = esc(item["status"])
        badges.append(f'<span class="is-status-{status}">{status}</span>')
    badge_html = (
        f'<div class="library-row__badges">{"".join(badges)}</div>'
        if badges
        else ""
    )
    return (
        '<article class="library-row">'
        f'<div class="library-row__meta"><span>{esc(date_label(item))}</span>'
        f"<small>{esc(axis_name(item))}</small></div>"
        f"<div><h3>{esc(title)}</h3><p>{esc(summary(item))}</p>{badge_html}</div>"
        '<span class="library-row__arrow">↗</span>'
        f'<a class="story-link" href="{esc(route(item))}" aria-label="阅读{esc(title)}"></a>'
        "</article>"
    )


def company_name(item: dict) -> str:
    haystack = " ".join(str(item.get(key, "")) for key in ("title", "tag", "category")).lower()
    if re.search(r"alphabet|google|goog", haystack):
        return "ALPHABET · GOOG / GOOGL"
    if re.search(r"tesla|tsla", haystack):
        return "TESLA · TSLA"
    if "nokia" in haystack:
        return "NOKIA · NOK"
    first = re.split(r"[\n｜|]", str(item.get("title") or "财报"))[0].strip()
    return first if re.search(r"[\u4e00-\u9fff]", first) else first.upper()


def quarter_label(item: dict) -> str:
    match = re.search(r"(20\d{2})\s*Q([1-4])", str(item.get("title") or ""), re.I)
    return f"{match.group(1)} · QUARTER {match.group(2)} EARNINGS" if match else "EARNINGS & MANAGEMENT CALL"


def render_earnings(pages: list[dict]) -> tuple[str, str]:
    earnings = sorted(
        [item for item in pages if item.get("content_type") == "earnings"],
        key=timestamp,
        reverse=True,
    )
    if not earnings:
        return "", ""
    lead = earnings[0]
    title = str(lead.get("title") or "财报专题")
    lead_html = (
        f'<div class="earnings-lead__top"><b>{esc(company_name(lead))}</b>'
        f"<span>{esc(date_label(lead))}</span></div>"
        f'<div class="earnings-lead__quarter">{esc(quarter_label(lead))}</div>'
        f"<h3>{esc(title)}</h3><p>{esc(summary(lead))}</p>"
        '<div class="earnings-lead__foot"><span>财务质量 · 管理层指引 · 估值变量</span>'
        "<b>阅读全文 ↗</b></div>"
        f'<a class="story-link" href="{esc(route(lead))}" aria-label="阅读{esc(title)}"></a>'
    )
    rows = []
    for index, item in enumerate(earnings[1:4], start=2):
        title = str(item.get("title") or "财报电话会")
        rows.append(
            '<article class="earnings-row">'
            f'<div class="earnings-row__num">{index:02d}</div><div>'
            f'<div class="earnings-row__meta"><span>{esc(company_name(item))}</span>'
            f"<span>{esc(date_label(item))}</span></div>"
            f"<h3>{esc(title)}</h3>"
            f'<a class="story-link" href="{esc(route(item))}" aria-label="阅读{esc(title)}"></a>'
            "</div></article>"
        )
    return lead_html, "\n".join(rows)


def replace_marker(source: str, name: str, content: str) -> str:
    start = f"<!-- HOME_FALLBACK:{name}:start -->"
    end = f"<!-- HOME_FALLBACK:{name}:end -->"
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.S)
    replacement = f"{start}\n{content}\n{end}"
    updated, count = pattern.subn(replacement, source)
    if count != 1:
        raise ValueError(f"expected one fallback marker pair for {name}, found {count}")
    return updated


def replace_axis_counts(source: str, pages: list[dict]) -> str:
    counts = defaultdict(int)
    for item in pages:
        counts[item.get("axis")] += 1
    updated = source
    for axis in AXIS_NAMES:
        pattern = re.compile(
            r'(<a class="axis-row"[^>]*data-axis-link="'
            + re.escape(axis)
            + r'"[^>]*>.*?<i>)[^<]*(</i>)',
            re.S,
        )
        updated, count = pattern.subn(
            rf"\g<1>{counts[axis]}\g<2>", updated, count=1
        )
        if count != 1:
            raise ValueError(f"could not update static axis count for {axis}")
    return updated


def build_index(source: str, registry: list[object]) -> str:
    pages = approved_pages(registry)
    chronological = sorted(pages, key=timestamp, reverse=True)
    ranked = sorted(pages, key=feature_sort_key)
    if not ranked:
        raise ValueError("registry has no homepage-approved entries")

    lead = ranked[0]
    auxiliary = select_recent_auxiliary(ranked, lead)
    earnings_lead, earnings_rows = render_earnings(pages)
    updated = replace_marker(source, "ticker-items", render_ticker(pages))
    updated = replace_marker(updated, "recent-lead", render_recent_lead(lead))
    updated = replace_marker(
        updated, "recent-list", "\n".join(render_dispatch_row(item) for item in auxiliary)
    )
    updated = replace_marker(updated, "series-strip", render_series(pages))
    updated = replace_marker(updated, "earnings-lead", earnings_lead)
    updated = replace_marker(updated, "earnings-list", earnings_rows)
    updated = replace_marker(
        updated,
        "library-list",
        "\n".join(render_library_row(item) for item in chronological[:2]),
    )
    updated = re.sub(
        r'(<b id="recent-count">)[^<]*(</b>)',
        rf"\g<1>{len(pages)}\g<2>",
        updated,
        count=1,
    )
    return replace_axis_counts(updated, pages)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail when index.html is not synchronized; do not write files",
    )
    args = parser.parse_args()

    source = INDEX.read_text(encoding="utf-8")
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    if not isinstance(registry, list):
        raise SystemExit("registry.json must contain an array")
    expected = build_index(source, registry)
    if args.check:
        if expected != source:
            print("homepage fallback is out of sync with registry.json", file=sys.stderr)
            return 1
        print("homepage fallback synchronized")
        return 0
    if expected != source:
        INDEX.write_text(expected, encoding="utf-8")
        print(f"synchronized homepage fallback: {len(approved_pages(registry))} approved entries")
    else:
        print("homepage fallback already synchronized")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
