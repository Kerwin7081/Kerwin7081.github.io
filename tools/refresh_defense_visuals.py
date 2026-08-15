#!/usr/bin/env python3
from __future__ import annotations

import os
import re
from pathlib import Path
from urllib.parse import urlparse

import cv2
import qrcode
import requests
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SPACEX_DIR = ROOT / "spacex-vs-rocket-lab-defense-launch-20260815"
GOLDEN_DIR = ROOT / "golden-dome-defense-investment-map-20260815"

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/131 Safari/537.36"
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": UA, "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8"})

IMAGES = {
    SPACEX_DIR / "assets" / "victus-haze-pioneer.jpg": [
        "https://rocketlabcorp.com/assets/Uploads/CSN_1150_1_sml__FillWzExNTAsMTM4MF0.jpg",
    ],
    SPACEX_DIR / "assets" / "rocketlab-lightning.png": [
        "https://rocketlabcorp.com/assets/Uploads/Asset-113.png",
    ],
    GOLDEN_DIR / "assets" / "rocketlab-lightning.png": [
        "https://rocketlabcorp.com/assets/Uploads/Asset-113.png",
    ],
    GOLDEN_DIR / "assets" / "rtx-sm3.jpg": [
        "https://prd-sc102-cdn.rtx.com/raytheon/-/media/ray/what-we-do/missile-defense/strategic-engagement-systems/sm-3-interceptor/sm3_lead_1600x450.jpg?rev=9d1e506cd43a4522b8f7677a62afc3a5&rid=e967f4c04ec241e18cd5f53c9954fc25",
    ],
    GOLDEN_DIR / "assets" / "gbi-launch.jpg": [
        "https://media.northropgrumman.com/1d25840a-fd03-4fd6-8f52-b3850023d5d3/Ground-Based-Interceptor-launch-001_Original%20file.jpg?mw=3840",
        "https://media.defense.gov/2023/Dec/13/2003358301/-1/-1/0/231211-D-D0500-1006C.JPG",
    ],
    GOLDEN_DIR / "assets" / "gitai-s3.jpg": [
        "https://gitai.tech/wp-content/uploads/2026/05/Picture1.jpg",
    ],
}

COLORS = {
    "surface": "#fff1e5",
    "paper": "#fffaf5",
    "green": "#103f35",
    "ink": "#262220",
    "muted": "#746b65",
    "copper": "#9a5c38",
    "risk": "#9f332b",
    "rule": "#cdbfb3",
}

FONT_SERIF_BOLD = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"
FONT_SANS = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
FONT_SANS_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"


def download_image(target: Path, urls: list[str]) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    errors = []
    for url in urls:
        try:
            headers = {"Referer": f"{urlparse(url).scheme}://{urlparse(url).netloc}/"}
            r = SESSION.get(url, headers=headers, timeout=45, allow_redirects=True)
            r.raise_for_status()
            if len(r.content) < 5000:
                raise RuntimeError(f"suspiciously small payload: {len(r.content)} bytes")
            target.write_bytes(r.content)
            with Image.open(target) as im:
                im.verify()
            with Image.open(target) as im:
                print(f"OK image {target.relative_to(ROOT)} <- {url} | {im.size} {im.format}")
            return
        except Exception as exc:
            errors.append(f"{url}: {exc}")
            if target.exists():
                target.unlink()
    raise RuntimeError("All image sources failed for %s\n%s" % (target, "\n".join(errors)))


def patch_html() -> None:
    sp = SPACEX_DIR / "index.html"
    s = sp.read_text(encoding="utf-8")
    s = s.replace(
        'https://rocketlabcorp.com/assets/Uploads/Rocket-Lab-VictusHaze-small.png',
        './assets/victus-haze-pioneer.jpg',
    )
    s = s.replace(
        'https://rocketlabcorp.com/assets/Uploads/Rocket-Lab-Lightning-Spacecraft.jpg',
        './assets/rocketlab-lightning.png',
    )
    s = s.replace(
        'alt="Rocket Lab VICTUS HAZE 任务中的 Pioneer 航天器"',
        'alt="Rocket Lab VICTUS HAZE 任务中的 Pioneer 航天器实物"',
    )
    s = s.replace(
        'Rocket Lab 官方任务图。该任务把 Electron 发射与 Pioneer（先锋号，高机动卫星平台）在轨行动串成一条快速响应链。来源：Rocket Lab。',
        'Rocket Lab 官方实物图：VICTUS HAZE 所用 Pioneer（先锋号，高机动卫星平台）。该任务把卫星制造、Electron 发射与在轨 RPO（交会与近距操作）串成一条快速响应链。来源：Rocket Lab。',
    )
    s = s.replace(
        'Rocket Lab 官方渲染图。它代表公司从单纯“发射火箭”走向自己制造军用星座平台的另一半能力。来源：Rocket Lab。',
        'Rocket Lab 官方产品图：Lightning（闪电，中大型卫星平台）是其高功率、长寿命卫星平台，并被用于 SDA（太空发展局）相关星座方案。来源：Rocket Lab。',
    )
    s = s.replace('object-fit:cover;background:#ddd', 'object-fit:contain;background:#f3eee8')
    sp.write_text(s, encoding="utf-8")

    gd = GOLDEN_DIR / "index.html"
    g = gd.read_text(encoding="utf-8")
    repl = {
        'https://rocketlabcorp.com/assets/Uploads/Rocket-Lab-Lightning-Spacecraft.jpg': './assets/rocketlab-lightning.png',
        'https://prd-sc102-cdn.rtx.com/raytheon/-/media/ray/what-we-do/missile-defense/strategic-engagement-systems/sm-3-interceptor/sm3_lead_1600x450.jpg?rev=9d1e506cd43a4522b8f7677a62afc3a5&amp;rid=e967f4c04ec241e18cd5f53c9954fc25': './assets/rtx-sm3.jpg',
        'https://media.northropgrumman.com/1d25840a-fd03-4fd6-8f52-b3850023d5d3/Ground-Based-Interceptor-launch-001_Original%20file.jpg?mw=3840': './assets/gbi-launch.jpg',
        'https://gitai.tech/wp-content/uploads/2026/05/Picture1.jpg': './assets/gitai-s3.jpg',
    }
    for old, new in repl.items():
        g = g.replace(old, new)
    g = g.replace('object-fit:cover;background:#ddd', 'object-fit:contain;background:#f3eee8')
    g = g.replace(
        '来源：Northrop Grumman 官方。',
        '产品说明来源：Northrop Grumman；图片优先采用其官方媒体源，下载失败时回退至美国国防部/MDA 同型号 GBI 实弹测试图。',
    )
    gd.write_text(g, encoding="utf-8")


def font(path: str, size: int, index: int = 2):
    return ImageFont.truetype(path, size=size, index=index)


def text_width(draw: ImageDraw.ImageDraw, text: str, fnt) -> float:
    b = draw.textbbox((0, 0), text, font=fnt)
    return b[2] - b[0]


def wrap_px(draw: ImageDraw.ImageDraw, text: str, fnt, max_width: int) -> list[str]:
    lines = []
    for para in text.split("\n"):
        if not para:
            lines.append("")
            continue
        cur = ""
        for ch in para:
            test = cur + ch
            if cur and text_width(draw, test, fnt) > max_width:
                lines.append(cur)
                cur = ch
            else:
                cur = test
        if cur:
            lines.append(cur)
    return lines


def draw_wrapped(draw, xy, text, fnt, fill, max_width, line_gap=8, max_lines=None):
    x, y = xy
    lines = wrap_px(draw, text, fnt, max_width)
    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines]
        last = lines[-1]
        while last and text_width(draw, last + "…", fnt) > max_width:
            last = last[:-1]
        lines[-1] = last + "…"
    bbox = draw.textbbox((x, y), "国Ag", font=fnt)
    lh = bbox[3] - bbox[1]
    for line in lines:
        draw.text((x, y), line, font=fnt, fill=fill)
        y += lh + line_gap
    return y


def add_qr(canvas: Image.Image, url: str, xy: tuple[int, int], size: int = 190):
    qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=8, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    q = qr.make_image(fill_color=COLORS["green"], back_color=COLORS["paper"]).convert("RGB")
    q = q.resize((size, size), Image.Resampling.NEAREST)
    canvas.paste(q, xy)


def render_summary(path: Path, *, series: str, title: str, subtitle: str, intro: str, takeaways: list[tuple[str, str]], hero: str, hero_note: str, url: str, short_sign: str):
    W, H = 1080, 1440
    im = Image.new("RGB", (W, H), COLORS["surface"])
    d = ImageDraw.Draw(im)
    margin = 58

    serif_title = font(FONT_SERIF_BOLD, 52)
    serif_sub = font(FONT_SERIF_BOLD, 31)
    sans = font(FONT_SANS, 25)
    sans_sm = font(FONT_SANS, 21)
    sans_b = font(FONT_SANS_BOLD, 25)
    sans_b_sm = font(FONT_SANS_BOLD, 19)
    hero_f = font(FONT_SERIF_BOLD, 48)

    # Header
    d.rectangle((0, 0, W, 78), fill=COLORS["green"])
    d.text((margin, 22), "KERWIN RESEARCH HUB", font=sans_b_sm, fill=COLORS["paper"])
    sw = text_width(d, series, sans_b_sm)
    d.text((W - margin - sw, 22), series, font=sans_b_sm, fill="#dce8e2")

    y = 114
    y = draw_wrapped(d, (margin, y), title, serif_title, COLORS["ink"], W - 2 * margin, line_gap=6, max_lines=3)
    y += 12
    y = draw_wrapped(d, (margin, y), subtitle, serif_sub, COLORS["green"], W - 2 * margin, line_gap=4, max_lines=2)

    y += 24
    d.line((margin, y, W - margin, y), fill=COLORS["rule"], width=2)
    y += 22
    d.text((margin, y), "KERWIN 导语", font=sans_b_sm, fill=COLORS["copper"])
    y += 36
    y = draw_wrapped(d, (margin, y), intro, sans_sm, COLORS["ink"], W - 2 * margin, line_gap=8, max_lines=5)

    y += 22
    d.line((margin, y, W - margin, y), fill=COLORS["rule"], width=2)
    y += 18
    d.text((margin, y), "全文要点", font=sans_b_sm, fill=COLORS["green"])
    y += 38

    col_gap = 30
    col_w = (W - 2 * margin - col_gap) // 2
    card_h = 150
    for i, (head, body) in enumerate(takeaways[:4]):
        row, col = divmod(i, 2)
        x = margin + col * (col_w + col_gap)
        cy = y + row * (card_h + 18)
        d.rectangle((x, cy, x + col_w, cy + card_h), fill=COLORS["paper"], outline=COLORS["rule"], width=2)
        d.text((x + 18, cy + 16), f"0{i+1}", font=sans_b_sm, fill=COLORS["copper"])
        draw_wrapped(d, (x + 62, cy + 14), head, sans_b, COLORS["green"], col_w - 80, line_gap=3, max_lines=2)
        draw_wrapped(d, (x + 18, cy + 67), body, sans_sm, COLORS["muted"], col_w - 36, line_gap=5, max_lines=3)
    y += 2 * (card_h + 18) + 6

    # Hero judgment
    d.rectangle((margin, y, W - margin, y + 145), fill=COLORS["green"])
    d.text((margin + 24, y + 17), "核心判断 / HERO", font=sans_b_sm, fill="#dce8e2")
    d.text((margin + 24, y + 52), hero, font=hero_f, fill=COLORS["paper"])
    draw_wrapped(d, (margin + 420, y + 55), hero_note, sans_sm, "#dce8e2", W - margin - (margin + 420) - 22, line_gap=5, max_lines=3)
    y += 170

    # QR/footer
    qr_size = 174
    add_qr(im, url, (margin, y), qr_size)
    tx = margin + qr_size + 28
    d.text((tx, y + 5), "扫码阅读全文", font=serif_sub, fill=COLORS["green"])
    d.text((tx, y + 48), "enyaclawd.com", font=sans_b, fill=COLORS["ink"])
    draw_wrapped(d, (tx, y + 85), short_sign, sans_sm, COLORS["muted"], W - margin - tx, line_gap=4, max_lines=2)

    footer_y = H - 104
    d.line((margin, footer_y, W - margin, footer_y), fill=COLORS["rule"], width=2)
    d.text((margin, footer_y + 24), "判断框架：Kerwin", font=sans_b_sm, fill=COLORS["green"])
    right = "自动化研究、校验与排版：Enya"
    rw = text_width(d, right, sans_b_sm)
    d.text((W - margin - rw, footer_y + 24), right, font=sans_b_sm, fill=COLORS["muted"])

    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path, format="PNG", optimize=True)
    print(f"Rendered {path.relative_to(ROOT)} {im.size}")

    detector = cv2.QRCodeDetector()
    decoded, _, _ = detector.detectAndDecode(cv2.imread(str(path)))
    if decoded != url:
        raise RuntimeError(f"QR decode mismatch for {path}: {decoded!r} != {url!r}")
    print(f"QR OK {path.relative_to(ROOT)} -> {decoded}")


def generate_summaries() -> None:
    render_summary(
        SPACEX_DIR / "assets" / "fulltext-summary.png",
        series="DEFENSE × SPACE × AI · 01",
        title="SpaceX vs Rocket Lab：美国国防航天与运载体系的两条路线",
        subtitle="从 Falcon 9 / Starship 到 Electron / HASTE / Neutron / GHOST",
        intro="一则 Golden Dome（金穹）天基拦截器 Gate 1 全员通过的新闻，把 SpaceX 与 Rocket Lab 放进同一张国家安全航天地图。真正值得研究的不是谁的火箭更大，而是谁能把发射、卫星、网络、载荷与在轨运营做成可持续交付的国防基础设施。",
        takeaways=[
            ("SpaceX：规模与网络", "Falcon 9 + Starshield + 太空数据网络已形成平台级闭环。"),
            ("RKLB：快速响应与第二供应链", "VICTUS HAZE 从发射通知到 Electron 起飞仅 16h42m；GHOST 强化可转场部署。"),
            ("合同验证已跨过十亿美元", "SpaceX 2026 年相关公开合同约 $8.05B；RKLB 两笔 SDA 卫星 Prime 合同合计约 $1.33B。"),
            ("真正分水岭是下一代运载", "SpaceX 看 Starship 稳定复用；RKLB 看 Neutron 能否按成本和节奏进入国家安全中型运载。"),
        ],
        hero="16h42m",
        hero_note="VICTUS HAZE：从美国太空军发出 Notice-to-Launch（发射通知）到 Electron 起飞。",
        url="https://enyaclawd.com/spacex-vs-rocket-lab-defense-launch-20260815/",
        short_sign="SpaceX vs Rocket Lab · Defense Space & Launch Infrastructure",
    )

    render_summary(
        GOLDEN_DIR / "assets" / "fulltext-summary.png",
        series="DEFENSE × SPACE × AI · 02",
        title="美国 Golden Dome（金穹）：$1850 亿国防航天产业投资地图",
        subtitle="从 Gate 1 全员通过，拆到预算、杀伤链与公司价值池",
        intro="美国太空军披露，12 家 SBI（天基拦截器）供应商全部通过 Gate 1。这个节点本身还不是量产胜负，却揭示了 Golden Dome 的真实形态：它不是一枚导弹，而是把太空传感器、低延迟网络、AI/C2（人工智能/指挥控制）与多层拦截器连接起来的国家级实时防御系统。",
        takeaways=[
            ("$185B 不是生命周期总上限", "FY26 $25B、FY27 约 $17.5B、$185B 目标架构、CBO 约 $1.2T 二十年情景是不同口径，不能相加。"),
            ("六步杀伤链决定价值池", "Detect → Track → Transport → Fuse & Decide → Intercept → Assess & Rebuild。"),
            ("12 家 Gate 1 ≠ 12 家量产赢家", "Gate 1 只是设计与组件级验证；Gate 2/3 的太空飞行与在轨验证信息量更高。"),
            ("新旧军工被接进同一网络", "SpaceX/RKLB/LHX 吃太空层；PLTR/Anduril 争 AI/C2；LMT/RTX/NOC 把守成熟拦截与系统工程。"),
        ],
        hero="$185B ≠ 总预算",
        hero_note="研究基准是十年 objective architecture（目标架构）；最终生命周期成本取决于 SBI 数量、单价、寿命与补网频率。",
        url="https://enyaclawd.com/golden-dome-defense-investment-map-20260815/",
        short_sign="Golden Dome · Defense × Space × AI Investment Map",
    )


def qa_html_images() -> None:
    for directory in (SPACEX_DIR, GOLDEN_DIR):
        html = (directory / "index.html").read_text(encoding="utf-8")
        srcs = re.findall(r'<img[^>]+src="([^"]+)"', html)
        if not srcs:
            raise RuntimeError(f"No article images found in {directory.name}")
        for src in srcs:
            if src.startswith("http://") or src.startswith("https://"):
                raise RuntimeError(f"External img src remains in {directory.name}: {src}")
            if src.startswith("./"):
                asset = directory / src[2:]
            elif src.startswith("/"):
                asset = ROOT / src.lstrip("/")
            else:
                asset = directory / src
            if not asset.exists():
                raise RuntimeError(f"Missing local image for {directory.name}: {src}")
            with Image.open(asset) as im:
                im.verify()
        print(f"HTML image QA OK {directory.name}: {len(srcs)} local images")


def main() -> None:
    for target, urls in IMAGES.items():
        download_image(target, urls)
    patch_html()
    generate_summaries()
    qa_html_images()


if __name__ == "__main__":
    main()
