#!/usr/bin/env python3
"""Ungate round 2: the non-kw-editorial gate families.
- kw-legacy-gate: remove #kw-legacy-gate-overlay and .gate-prompt elements;
  add 'visible' to .gated-content so CSS-hidden content shows.
- gate-overlay family: remove #gate-overlay; strip body 'gate-locked'.
- access-gate / kw-access-gate / plain #gate overlays: remove the element.
Scripts: delete gate-dedicated inline blocks; stub gate lookups in mixed
blocks (same stub as seo_ungate_stub.py, wider id set)."""
import re, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = [l.strip() for l in open("/tmp/extra_abs.txt") if l.strip()]
STUB = ('{style:{},dataset:{},classList:{add:function(){},remove:function(){},'
        'toggle:function(){}},addEventListener:function(){},'
        'removeEventListener:function(){},setAttribute:function(){},'
        'getAttribute:function(){return null},focus:function(){},blur:function(){},'
        'value:"",hidden:true,textContent:"",innerHTML:""}')
GATE_TOKENS = ["kw-gate-pending", "accessKey", "gateInput", "access-key",
               "access-form", "access-gate", "openGate", "unlock",
               "editorial-gate", "reader-gate", "kw-access", "kerwinUnlocked",
               "kw-legacy-gate", "gate-prompt", "gate-overlay", "gate-locked",
               "kw-access-gate", "gated-content"]
OTHER_MARKERS = ["readingProgress", "backTop", "addEventListener('scroll'",
                 'addEventListener("scroll"', "querySelectorAll",
                 "Chart", "canvas", "requestAnimationFrame"]
GATE_IDS = ["gate", "editorial-gate", "access-gate", "home-gate", "reader-gate",
            "editorialGate", "access-key", "access-form", "access-error",
            "gateInput", "accessKey", "gate-form", "gate-error", "gate-key",
            "gate-input", "kw-legacy-gate-input", "kw-legacy-gate-overlay",
            "gate-overlay", "gate-prompt", "kw-access-gate"]
ids = "|".join(re.escape(i) for i in GATE_IDS)
pat_id = re.compile(r"(=\s*(?:document\.)?getElementById\(\s*['\"](?:" + ids + r")['\"]\s*\))")
pat_dollar = re.compile(r"(=\s*\$\(\s*['\"](?:" + ids + r")['\"]\s*\))")
pat_qs = re.compile(r"(=\s*(?:document\.)?querySelector\(\s*['\"][^'\"]*(?:kw-editorial-gate|kw-legacy-gate|access-gate|gate-overlay)[^'\"]*['\"]\s*\))")

def remove_element(html, start_re):
    m = re.search(start_re, html)
    if not m:
        return html, False
    tag = m.group(1)
    depth = 0
    for t in re.finditer(rf'</?{tag}\b[^>]*>', html[m.start():]):
        tok = t.group(0)
        if tok.startswith('</'):
            depth -= 1
            if depth == 0:
                return html[:m.start()] + html[m.start() + t.end():], True
        elif not tok.endswith('/>'):
            depth += 1
    return html, False

ELEMENT_RES = [
    r'<(div|section|aside)\b[^>]*id="kw-legacy-gate-overlay"[^>]*>',
    r'<(div|section|aside)\b[^>]*class="[^"]*gate-prompt[^"]*"[^>]*>',
    r'<(div|section|aside)\b[^>]*id="gate-overlay"[^>]*>',
    r'<(div|section|aside)\b[^>]*class="[^"]*kw-access-gate[^"]*"[^>]*>',
    r'<(div|section|aside)\b[^>]*class="[^"]*access-gate[^"]*"[^>]*>',
    r'<(div|section|aside)\b[^>]*id="access-gate"[^>]*>',
    r'<(div|section|aside)\b[^>]*id="gate"[^>]*>',
]

report = {}
for p in PAGES:
    f = Path(p)
    html = f.read_text(encoding="utf-8", errors="replace")
    orig = html
    actions = []
    for r in ELEMENT_RES:
        html, ok = remove_element(html, r)
        if ok:
            actions.append("element:" + r.split('"')[1][:28])
    # strip body lock classes
    bm = re.search(r"<body[^>]*>", html)
    if bm:
        tag = bm.group(0)
        newtag = tag
        for tok in ("gate-locked", "kw-gate-pending"):
            newtag = newtag.replace(tok, "")
        if newtag != tag:
            newtag = re.sub(r'class="\s+', 'class="', newtag)
            newtag = re.sub(r'\s+"', '"', newtag)
            newtag = re.sub(r'class="\s*"', "", newtag)
            newtag = re.sub(r"<body\s+>", "<body>", newtag)
            html = html[:bm.start()] + newtag + html[bm.end():]
            actions.append("body-class")
    # reveal gated-content
    def reveal(m):
        cls = m.group(2)
        if "visible" in cls.split():
            return m.group(0)
        actions.append("reveal-gated-content")
        return m.group(1) + 'class="' + cls + ' visible"'
    html = re.sub(r'(<(?:div|section|main|article)\b[^>]*?)class="([^"]*gated-content[^"]*)"', reveal, html)
    # scripts: delete gate-dedicated blocks
    def script_sub(m):
        attrs, body = m.group(1), m.group(2)
        if "src=" in attrs:
            return m.group(0)
        if "gate" not in body.lower():
            return m.group(0)
        if not any(t in body for t in GATE_TOKENS):
            return m.group(0)
        if any(t in body for t in OTHER_MARKERS):
            return m.group(0)
        if "calc(" in body and "gate" not in body.split("calc(")[0][-200:]:
            return m.group(0)
        actions.append("gate-script")
        return ""
    html = re.sub(r"<script([^>]*)>(.*?)</script>", script_sub, html, flags=re.S)
    # stub gate lookups in remaining blocks
    n = 0
    def repl(m):
        tail = m.string[m.end():m.end() + 3]
        return m.group(1) if tail.startswith("||{") else m.group(1) + "||" + STUB
    for pat in (pat_id, pat_dollar, pat_qs):
        html, k = pat.subn(repl, html)
        n += k
    if n:
        actions.append(f"stubs:{n}")
    if html != orig:
        f.write_text(html, encoding="utf-8")
    report[str(f.relative_to(ROOT))] = actions

for k, v in report.items():
    print(k, "->", v)
print(json.dumps({"pages": len(report),
                  "no_element_removed": [k for k, v in report.items() if not any(a.startswith("element:") for a in v)]}, ensure_ascii=False))
