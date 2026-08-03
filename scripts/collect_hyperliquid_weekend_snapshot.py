#!/usr/bin/env python3
"""Collect a read-only Hyperliquid XYZ snapshot for the weekend dashboard.

The script deliberately has no trading code and uses only the public Info API.
US cash baselines are refreshed when Alpaca market-data secrets are available;
otherwise the latest verified baseline is retained and reported as stale.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "hyperliquid-weekend-stock-signal-20260803" / "data"
LATEST_PATH = DATA_DIR / "latest.json"
HISTORY_PATH = DATA_DIR / "history.json"
API = "https://api.hyperliquid.xyz/info"
DEX = "xyz"

TARGETS = {
    "NVDA": "AI半导体", "AMD": "AI半导体", "MU": "存储", "TSM": "晶圆代工",
    "AVGO": "AI半导体", "MSFT": "平台", "AMZN": "平台", "META": "平台",
    "GOOGL": "平台", "TSLA": "高波动", "SMSN": "存储", "SKHX": "存储",
    "SNDK": "存储", "DRAM": "存储", "SP500": "指数", "XYZ100": "指数",
}
US_BASELINE_SYMBOLS = [
    "NVDA", "AMD", "MU", "TSM", "AVGO", "MSFT", "AMZN", "META", "GOOGL", "TSLA", "SNDK"
]


def http_json(url: str, *, method: str = "GET", body: Any = None, headers: dict[str, str] | None = None) -> Any:
    payload = None if body is None else json.dumps(body).encode("utf-8")
    request = Request(url, data=payload, method=method, headers=headers or {})
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def within_weekend_window(now: datetime) -> bool:
    """Friday 16:00 UTC through Monday 08:00 HKT, inclusive for manual runs."""
    hkt = now.astimezone(timezone(timedelta(hours=8)))
    if hkt.weekday() in (5, 6):
        return True
    return hkt.weekday() == 0 and hkt.hour < 8


def collect_hyperliquid() -> list[dict[str, Any]]:
    meta_ctx = http_json(
        API,
        method="POST",
        body={"type": "metaAndAssetCtxs", "dex": DEX},
        headers={"Content-Type": "application/json"},
    )
    mids_response = http_json(
        API,
        method="POST",
        body={"type": "allMids", "dex": DEX},
        headers={"Content-Type": "application/json"},
    )
    if not isinstance(meta_ctx, list) or len(meta_ctx) < 2:
        raise RuntimeError("Unexpected metaAndAssetCtxs response")
    universe = meta_ctx[0].get("universe", [])
    contexts = meta_ctx[1]
    mids = mids_response.get("mids", {}) if isinstance(mids_response, dict) else {}
    assets: list[dict[str, Any]] = []
    for index, item in enumerate(universe):
        raw_symbol = item.get("name", "")
        symbol = raw_symbol.rsplit(":", 1)[-1]
        if symbol not in TARGETS or index >= len(contexts):
            continue
        ctx = contexts[index] or {}
        mid = mids.get(raw_symbol, mids.get(symbol, ctx.get("midPx")))
        assets.append({
            "symbol": symbol,
            "category": TARGETS[symbol],
            "midPx": number(mid),
            "markPx": number(ctx.get("markPx")),
            "oraclePx": number(ctx.get("oraclePx")),
            "funding": number(ctx.get("funding")),
            "openInterest": number(ctx.get("openInterest")),
            "prevDayPx": number(ctx.get("prevDayPx")),
        })
    if len(assets) < 4:
        raise RuntimeError(f"Only {len(assets)} requested assets found in Hyperliquid response")
    return assets


def number(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def refresh_alpaca_baseline(previous: dict[str, Any], now: datetime) -> dict[str, Any]:
    key = os.getenv("APCA_API_KEY_ID") or os.getenv("ALPACA_API_KEY_ID")
    secret = os.getenv("APCA_API_SECRET_KEY") or os.getenv("ALPACA_API_SECRET_KEY")
    if not key or not secret:
        return previous
    end = now.astimezone(timezone.utc).date() + timedelta(days=1)
    start = end - timedelta(days=10)
    query = urlencode({
        "symbols": ",".join(US_BASELINE_SYMBOLS),
        "timeframe": "1Day",
        "start": f"{start.isoformat()}T00:00:00Z",
        "end": f"{end.isoformat()}T00:00:00Z",
        "feed": "sip",
        "adjustment": "all",
        "limit": "1000",
    })
    response = http_json(
        f"https://data.alpaca.markets/v2/stocks/bars?{query}",
        headers={"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": secret},
    )
    bars = response.get("bars", {}) if isinstance(response, dict) else {}
    result = dict(previous)
    for symbol in US_BASELINE_SYMBOLS:
        rows = bars.get(symbol, [])
        if not rows:
            continue
        row = rows[-1]
        close = number(row.get("c"))
        timestamp = str(row.get("t", ""))
        if close is not None:
            result[symbol] = {
                "close": close,
                "date": timestamp[:10],
                "source": "Alpaca SIP · consolidated US equities",
            }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Allow collection outside the weekend window")
    parser.add_argument("--fixture", action="store_true", help="Validate the writer with existing data only")
    args = parser.parse_args()
    now = datetime.now(timezone.utc)
    if not args.force and not args.fixture and not within_weekend_window(now):
        print("Outside weekend collection window; no snapshot written.")
        return 0

    existing = read_json(LATEST_PATH, {})
    previous_assets = {row.get("symbol"): row for row in existing.get("assets", []) if row.get("symbol")}
    baseline = existing.get("cashBaseline", {})
    if args.fixture:
        assets = existing.get("assets", [])
    else:
        assets = collect_hyperliquid()
        baseline = refresh_alpaca_baseline(baseline, now)
    if not assets:
        raise RuntimeError("No assets available to write")

    snapshot = {
        "schema_version": 1,
        "observedAtUtc": now.isoformat().replace("+00:00", "Z"),
        "observedAtHkt": now.astimezone(timezone(timedelta(hours=8))).isoformat(),
        "source": API,
        "dex": DEX,
        "mode": "live_snapshot" if not args.fixture else "fixture_validation",
        "cadenceHours": 4,
        "cashBaseline": baseline,
        "assets": assets,
        "previousAssets": previous_assets,
    }
    history = read_json(HISTORY_PATH, [])
    if not isinstance(history, list):
        history = []
    history.append({"observedAtUtc": snapshot["observedAtUtc"], "assets": assets})
    snapshot["history"] = history[-250:]
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LATEST_PATH.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    HISTORY_PATH.write_text(json.dumps(history[-250:], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(assets)} assets to {LATEST_PATH}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"snapshot collection failed: {exc}", file=sys.stderr)
        raise
