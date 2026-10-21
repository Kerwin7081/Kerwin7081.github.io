#!/usr/bin/env python3
"""Demote every h1 after the first to h2 (attributes preserved) on pages
with >=2 h1. Pages with 0 h1 are only listed, never modified."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = ['ai-agent-wallet-war-20260720/index.html',
         'ai-datacenter-connectivity-20260512/index.html',
         'china-open-model-global-token-value-chain-20260722/index.html',
         'cowos-asic-2026/index.html',
         'hyperliquid-financial-market-infrastructure-20260718/index.html',
         'hyperliquid-series-2-competitive-encirclement-20260719/index.html',
         'stablecoin-profit-war-dollar-treasury-20260719/index.html']
TOKEN = re.compile(r"<h1\b[^>]*>|</h1>")

for rel in PAGES:
    f = ROOT / rel
    html = f.read_text(encoding="utf-8")
    out, pair_no, demoted = [], 0, 0
    pos = 0
    for m in TOKEN.finditer(html):
        out.append(html[pos:m.start()])
        tok = m.group(0)
        if tok.startswith("</"):
            out.append("</h2>" if pair_no >= 2 else tok)
            if pair_no >= 2: demoted += 1
        else:
            pair_no += 1
            out.append("<h2" + tok[3:] if pair_no >= 2 else tok)
        pos = m.end()
    out.append(html[pos:])
    new = "".join(out)
    assert len(re.findall(r"<h1[\s>]", new)) == 1, rel
    f.write_text(new, encoding="utf-8")
    print(f"{rel}: demoted {demoted} h1 -> h2")
