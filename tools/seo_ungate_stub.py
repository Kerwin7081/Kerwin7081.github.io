#!/usr/bin/env python3
"""Step 2 of ungating: for pages whose gate element was removed, make kept
inline scripts null-safe by giving gate-element lookups a no-op stub fallback:
  var gate = document.getElementById("editorial-gate") || <STUB>
The stub swallows addEventListener/focus/classList/style writes and reports
hidden=true, so leftover unlock handlers stay inert. Only assignment contexts
(= ...) for known gate-related ids / gate class selectors are rewritten."""
import re, glob, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STUB = ('{style:{},dataset:{},classList:{add:function(){},remove:function(){},'
        'toggle:function(){}},addEventListener:function(){},'
        'removeEventListener:function(){},setAttribute:function(){},'
        'getAttribute:function(){return null},focus:function(){},blur:function(){},'
        'value:"",hidden:true,textContent:"",innerHTML:""}')
GATE_IDS = ["gate", "editorial-gate", "access-gate", "home-gate", "reader-gate",
            "editorialGate", "access-key", "access-form", "access-error",
            "gateInput", "accessKey", "gate-form", "gate-error", "gate-key",
            "gate-input", "gateInput".lower()]
ids = "|".join(re.escape(i) for i in GATE_IDS)
pat_id = re.compile(r"(=\s*(?:document\.)?getElementById\(\s*['\"](?:" + ids + r")['\"]\s*\))")
pat_dollar = re.compile(r"(=\s*\$\(\s*['\"](?:" + ids + r")['\"]\s*\))")
pat_qs = re.compile(r"(=\s*(?:document\.)?querySelector\(\s*['\"][^'\"]*kw-editorial-gate[^'\"]*['\"]\s*\))")

changed = {}
files = [ROOT / "index.html"] + sorted(ROOT.glob("*.html")) + sorted(ROOT.glob("*/index.html"))
for f in files:
    if f.name == "404.html":
        continue
    html = f.read_text(encoding="utf-8", errors="replace")
    if "kw-editorial-gate" not in html and "kw-gate-pending" not in html:
        continue  # only pages that had a gate (CSS markers remain in <style>)
    n = 0
    def repl(m):
        # idempotency: do not stub twice
        tail = m.string[m.end():m.end() + 3]
        return m.group(1) if tail.startswith("||{") else m.group(1) + "||" + STUB
    for pat in (pat_id, pat_dollar, pat_qs):
        html, k = pat.subn(repl, html)
        n += k
    if n:
        f.write_text(html, encoding="utf-8")
        changed[str(f.relative_to(ROOT))] = n
print(json.dumps({"pages_stubbed": len(changed), "total_lookups": sum(changed.values())}, ensure_ascii=False))
