#!/usr/bin/env python3
"""SEO audit for enyaclawd.com local mirror: checks every sitemap URL's page
for title/description/h1/canonical/og:image/JSON-LD/gate presence."""
import re, sys, urllib.request, xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UA = {"User-Agent": "Mozilla/5.0 (seo-audit)"}

def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")

sm = get("https://enyaclawd.com/sitemap.xml")
ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
urls = [e.text for e in ET.fromstring(sm).findall(".//s:loc", ns)]
print(f"sitemap URLs: {len(urls)}")

issues = {}
rows = []
for u in urls:
    path = u.replace("https://enyaclawd.com", "").strip("/")
    f = ROOT / (path + "/index.html" if path else "index.html")
    if not f.exists():
        rows.append((u, ["NO LOCAL FILE"]))
        issues["no_local_file"] = issues.get("no_local_file", 0) + 1
        continue
    html = f.read_text(encoding="utf-8", errors="replace")
    probs = []
    if not re.search(r"<title>[^<]{4,}</title>", html): probs.append("no/short title")
    if 'name="description"' not in html: probs.append("no meta description")
    if len(re.findall(r"<h1[\s>]", html)) != 1: probs.append(f"h1 count={len(re.findall(chr(60)+'h1', html))}")
    if 'rel="canonical"' not in html: probs.append("no canonical")
    if 'property="og:image"' not in html: probs.append("no og:image")
    if "application/ld+json" not in html: probs.append("no JSON-LD")
    # Reading gate = an actual gate overlay element or a body lock class in
    # body markup. Gate CSS rules left in <style> are inert and do NOT count
    # (the string-based check false-positived on them after ungating).
    _body = html.split("</head>", 1)[1] if "</head>" in html else html
    _bm = re.search(r"<body[^>]*>", html)
    _body_ns = re.sub(r"<script.*?</script>|<style.*?</style>", "", _body, flags=re.S)
    if ((_bm and ("kw-gate-pending" in _bm.group(0) or "gate-locked" in _bm.group(0)))
            or re.search(r'<(div|section|aside)\b[^>]*(?:id="(?:gate|access-gate|gate-overlay|gate-prompt|kw-legacy-gate-overlay)"|class="[^"]*(?:kw-editorial-gate|access-gate|kw-access-gate|gate-overlay)[^"]*")', _body_ns)):
        probs.append("READING GATE")
    for p in probs:
        key = p.split("=")[0]
        issues[key] = issues.get(key, 0) + 1
    rows.append((u, probs))

print("\n=== issue counts ===")
for k, v in sorted(issues.items(), key=lambda x: -x[1]):
    print(f"{v:4d}  {k}")
clean = sum(1 for _, p in rows if not p)
print(f"\nclean pages: {clean}/{len(rows)}")
