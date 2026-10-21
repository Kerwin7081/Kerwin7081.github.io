#!/usr/bin/env python3
"""Inject canonical / og:image fallback / JSON-LD structured data into every
page of the enyaclawd.com static mirror. Idempotent: skips tags already present.
Usage: python3 tools/seo_inject.py [--dry-run]"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://enyaclawd.com"
DEFAULT_IMG = f"{BASE}/assets/kerwin-home-og-v5.png"
DRY = "--dry-run" in sys.argv

PERSON = {
    "@type": "Person",
    "name": "Kerwin Ye",
    "alternateName": "叶高峰",
    "url": f"{BASE}/",
    "sameAs": ["https://www.linkedin.com/in/kerwin-ye-a86447aa/"],
}
ORG = {
    "@type": "Organization",
    "name": "Kerwin Research Hub",
    "alternateName": "EnyaClawd",
    "url": f"{BASE}/",
    "logo": DEFAULT_IMG,
    "founder": {"@type": "Person", "name": "Kerwin Ye"},
}

def meta(html, prop):
    m = re.search(rf'<meta[^>]+(?:property|name)="{re.escape(prop)}"[^>]+content="([^"]*)"', html)
    if m: return m.group(1)
    m = re.search(rf'<meta[^>]+content="([^"]*)"[^>]+(?:property|name)="{re.escape(prop)}"', html)
    return m.group(1) if m else None

def find_date(html, slug):
    m = re.search(r"-(\d{4})(\d{2})(\d{2})/?$", slug)
    if m: return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    head = html[:8000]
    m = re.search(r"(20\d{2})年(\d{1,2})月(\d{1,2})日", head)
    if m: return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    m = re.search(r"(20\d{2})[./-](\d{1,2})[./-](\d{1,2})", head)
    if m: return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    return None

def page_url(path: Path) -> str:
    rel = path.parent.relative_to(ROOT).as_posix()
    return f"{BASE}/" if rel == "." else f"{BASE}/{rel}/"

changed = {"canonical": 0, "ogimage": 0, "jsonld": 0, "files": 0}
files = [ROOT / "index.html"] + sorted(ROOT.glob("*/index.html"))
for f in files:
    html = f.read_text(encoding="utf-8", errors="replace")
    orig = html
    url = page_url(f)
    slug = url.replace(BASE, "")
    inserts = []

    if 'rel="canonical"' not in html:
        inserts.append(f'<link rel="canonical" href="{url}"/>')
        changed["canonical"] += 1
    ogimg = meta(html, "og:image")
    if not ogimg:
        inserts.append(f'<meta property="og:image" content="{DEFAULT_IMG}"/>')
        ogimg = DEFAULT_IMG
        changed["ogimage"] += 1
    if 'property="og:url"' not in html:
        inserts.append(f'<meta property="og:url" content="{url}"/>')

    if "application/ld+json" not in html:
        if f == ROOT / "index.html":
            data = {"@context": "https://schema.org", "@graph": [
                ORG,
                {"@type": "WebSite", "name": "EnyaClawd · Kerwin Research Hub",
                 "url": f"{BASE}/", "inLanguage": "zh-CN", "publisher": {"@type": "Organization", "name": "Kerwin Research Hub"}},
                PERSON,
            ]}
        else:
            title = meta(html, "og:title")
            if not title:
                m = re.search(r"<title>([^<]*)</title>", html)
                title = m.group(1).strip() if m else slug
            desc = meta(html, "description") or meta(html, "og:description") or ""
            art = {
                "@type": "Article",
                "headline": title,
                "description": desc,
                "image": ogimg,
                "inLanguage": "zh-CN",
                "mainEntityOfPage": url,
                "author": PERSON,
                "publisher": ORG,
            }
            d = find_date(html, slug)
            if d: art["datePublished"] = d
            data = {"@context": "https://schema.org", **art}
        block = '<script type="application/ld+json">\n' + json.dumps(data, ensure_ascii=False, indent=1) + "\n</script>"
        inserts.append(block)
        changed["jsonld"] += 1

    if inserts:
        html = html.replace("</head>", "\n".join(inserts) + "\n</head>", 1)
    if html != orig:
        changed["files"] += 1
        if not DRY:
            f.write_text(html, encoding="utf-8")

print(json.dumps(changed, ensure_ascii=False))
