#!/usr/bin/env python3
"""Same treatment as seo_inject.py, for root-level standalone .html pages
(article files and hub pages). Idempotent."""
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://enyaclawd.com"
DEFAULT_IMG = f"{BASE}/assets/kerwin-home-og-v5.png"
PERSON = {"@type": "Person", "name": "Kerwin Ye", "alternateName": "叶高峰",
          "url": f"{BASE}/", "sameAs": ["https://www.linkedin.com/in/kerwin-ye-a86447aa/"]}
ORG = {"@type": "Organization", "name": "Kerwin Research Hub", "alternateName": "EnyaClawd",
       "url": f"{BASE}/", "logo": DEFAULT_IMG, "founder": {"@type": "Person", "name": "Kerwin Ye"}}
HUB = {"earnings.html", "library.html", "map.html", "method.html", "models.html", "series.html"}

def meta(html, prop):
    m = re.search(rf'<meta[^>]+(?:property|name)="{re.escape(prop)}"[^>]+content="([^"]*)"', html)
    if m: return m.group(1)
    m = re.search(rf'<meta[^>]+content="([^"]*)"[^>]+(?:property|name)="{re.escape(prop)}"', html)
    return m.group(1) if m else None

for f in sorted(ROOT.glob("*.html")):
    if f.name in ("404.html", "index.html"):
        continue
    html = f.read_text(encoding="utf-8", errors="replace")
    orig = html
    url = f"{BASE}/{f.name}"
    inserts = []
    if 'rel="canonical"' not in html:
        inserts.append(f'<link rel="canonical" href="{url}"/>')
    ogimg = meta(html, "og:image")
    if not ogimg:
        inserts.append(f'<meta property="og:image" content="{DEFAULT_IMG}"/>')
        ogimg = DEFAULT_IMG
    if 'property="og:url"' not in html:
        inserts.append(f'<meta property="og:url" content="{url}"/>')
    if "application/ld+json" not in html:
        title = meta(html, "og:title")
        if not title:
            m = re.search(r"<title>([^<]*)</title>", html)
            title = m.group(1).strip() if m else f.stem
        desc = meta(html, "description") or meta(html, "og:description") or ""
        if f.name in HUB:
            data = {"@context": "https://schema.org", "@type": "WebPage",
                    "name": title, "description": desc, "url": url,
                    "inLanguage": "zh-CN", "isPartOf": {"@type": "WebSite", "name": "EnyaClawd · Kerwin Research Hub", "url": f"{BASE}/"}}
        else:
            art = {"@type": "Article", "headline": title, "description": desc,
                   "image": ogimg, "inLanguage": "zh-CN", "mainEntityOfPage": url,
                   "author": PERSON, "publisher": ORG}
            m = re.search(r"(20\d{2})(\d{2})(\d{2})", f.stem)
            if m: art["datePublished"] = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
            data = {"@context": "https://schema.org", **art}
        inserts.append('<script type="application/ld+json">\n' + json.dumps(data, ensure_ascii=False, indent=1) + "\n</script>")
    if inserts:
        html = html.replace("</head>", "\n".join(inserts) + "\n</head>", 1)
    if html != orig:
        f.write_text(html, encoding="utf-8")
        print("updated", f.name)
