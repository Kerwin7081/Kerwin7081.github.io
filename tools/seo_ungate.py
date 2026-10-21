#!/usr/bin/env python3
"""Remove the kw-editorial-gate reading gate from all pages:
- delete the gate element (section/div/aside with class kw-editorial-gate)
- strip 'kw-gate-pending' from <body> class
- delete inline script blocks that are gate-dedicated (gate behavior tokens
  present, no other-feature markers). Mixed blocks are kept (null-guarded in
  the wild) and verified afterwards via jsdom error diffing.
CSS rules for the gate are left in place (harmless, per instructions)."""
import re, glob, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GATE_TOKENS = ["kw-gate-pending", "accessKey", "gateInput", "access-key",
               "access-form", "access-gate", "openGate", "unlock",
               "editorial-gate", "reader-gate", "kw-access", "kerwinUnlocked"]
OTHER_MARKERS = ["readingProgress", "backTop", "addEventListener('scroll'",
                 'addEventListener("scroll"', "calc(", "querySelectorAll",
                 "localStorage", "Chart", "canvas", "requestAnimationFrame"]

def remove_gate_element(html):
    """Remove first element whose class contains kw-editorial-gate, using
    same-tag depth counting. Returns (html, removed_bool)."""
    m = re.search(r'<(section|div|aside)\b[^>]*class="[^"]*kw-editorial-gate[^"]*"[^>]*>', html)
    if not m:
        return html, False
    tag = m.group(1)
    depth = 0
    for t in re.finditer(rf'</?{tag}\b[^>]*>', html[m.start():]):
        tok = t.group(0)
        if tok.startswith('</'):
            depth -= 1
            if depth == 0:
                end = m.start() + t.end()
                return html[:m.start()] + html[end:], True
        elif not tok.endswith('/>'):
            depth += 1
    return html, False

report = {}
files = [ROOT / "index.html"] + sorted(ROOT.glob("*.html")) + sorted(ROOT.glob("*/index.html"))
for f in files:
    if f.name == "404.html":
        continue
    html = f.read_text(encoding="utf-8", errors="replace")
    if "kw-gate-pending" not in html and "kw-editorial-gate" not in html:
        continue
    orig = html
    actions = []
    html, removed = remove_gate_element(html)
    if removed: actions.append("gate-element")
    # body class token strip (only inside <body ...> tag)
    bm = re.search(r"<body[^>]*>", html)
    if bm and "kw-gate-pending" in bm.group(0):
        newtag = bm.group(0).replace("kw-gate-pending", "")
        newtag = re.sub(r'class="\s+', 'class="', newtag)
        newtag = re.sub(r'\s+"', '"', newtag)
        newtag = re.sub(r'class="\s*"', "", newtag)  # drop empty class attr
        newtag = re.sub(r"<body\s+>", "<body>", newtag)
        html = html[:bm.start()] + newtag + html[bm.end():]
        actions.append("body-class")
    # gate-dedicated script blocks
    def script_sub(m):
        attrs, body = m.group(1), m.group(2)
        if "src=" in attrs:
            return m.group(0)
        low = body.lower()
        if "gate" not in low:
            return m.group(0)
        if not any(t in body for t in GATE_TOKENS):
            return m.group(0)
        if any(t in body for t in OTHER_MARKERS):
            return m.group(0)
        actions.append("gate-script")
        return ""
    html = re.sub(r"<script([^>]*)>(.*?)</script>", script_sub, html, flags=re.S)
    if html != orig:
        f.write_text(html, encoding="utf-8")
        report[str(f.relative_to(ROOT))] = actions

print(json.dumps({"pages_changed": len(report),
                  "gate_elements": sum("gate-element" in a for a in report.values()),
                  "body_class": sum("body-class" in a for a in report.values()),
                  "gate_scripts": sum("gate-script" in a for a in report.values())}, ensure_ascii=False))
for k, v in report.items():
    if "gate-element" not in v:
        print("NO-ELEMENT-REMOVED:", k, v)
