#!/usr/bin/env python3
"""Download and validate the art-special media before GitHub Pages deployment.

The page is served from /1600-caravaggio-qinhuai-art-special/. This script mirrors
all artwork images and audio to that page's own assets directory, verifies the
file signatures and SHA-256 hashes, and checks that the HTML references only
those local media files for primary playback/rendering.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
PAGE_DIR = ROOT / "1600-caravaggio-qinhuai-art-special"
ASSET_DIR = PAGE_DIR / "assets"
HTML_FILE = PAGE_DIR / "index.html"
PUBLIC_PREFIX = "/1600-caravaggio-qinhuai-art-special/assets/"
MAX_BYTES = 35 * 1024 * 1024
USER_AGENT = "KerwinResearchHub-Media-QA/1.0 (+https://enyaclawd.com/)"

# filename, kind, primary URL, fallback URLs
ASSETS = [
    ("01-boy-with-fruit.jpg", "jpeg", "https://upload.wikimedia.org/wikipedia/commons/thumb/6/64/Boy_with_a_Basket_of_Fruit-Caravaggio_%281593%29.jpg/960px-Boy_with_a_Basket_of_Fruit-Caravaggio_%281593%29.jpg", [
        "https://upload.wikimedia.org/wikipedia/commons/6/64/Boy_with_a_Basket_of_Fruit-Caravaggio_%281593%29.jpg",
    ]),
    ("02-lute-player.jpg", "jpeg", "https://upload.wikimedia.org/wikipedia/commons/6/65/Caravaggio-The_Lute_Player-Hermitage.jpg", [
        "https://commons.wikimedia.org/wiki/Special:Redirect/file/Caravaggio-The_Lute_Player-Hermitage.jpg",
    ]),
    ("03-judith-beheading.jpg", "jpeg", "https://upload.wikimedia.org/wikipedia/commons/4/4d/Caravaggio_-_Giuditta_che_taglia_la_testa_a_Oloferne.jpg", [
        "https://upload.wikimedia.org/wikipedia/commons/b/b2/Caravaggio_Judith_Beheading_Holofernes.jpg",
        "https://commons.wikimedia.org/wiki/Special:Redirect/file/Caravaggio_-_Giuditta_che_taglia_la_testa_a_Oloferne.jpg",
    ]),
    ("04-calling-saint-matthew.jpg", "jpeg", "https://upload.wikimedia.org/wikipedia/commons/thumb/4/48/The_Calling_of_Saint_Matthew-Caravaggo_%281599-1600%29.jpg/960px-The_Calling_of_Saint_Matthew-Caravaggo_%281599-1600%29.jpg", [
        "https://upload.wikimedia.org/wikipedia/commons/4/48/The_Calling_of_Saint_Matthew-Caravaggo_%281599-1600%29.jpg",
    ]),
    ("05-supper-at-emmaus.jpg", "jpeg", "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5c/Caravaggio_-_Supper_at_Emmaus_-_National_Gallery_London.jpeg/960px-Caravaggio_-_Supper_at_Emmaus_-_National_Gallery_London.jpeg", [
        "https://upload.wikimedia.org/wikipedia/commons/5/5c/Caravaggio_-_Supper_at_Emmaus_-_National_Gallery_London.jpeg",
    ]),
    ("06-david-head-goliath.jpg", "jpeg", "https://upload.wikimedia.org/wikipedia/commons/4/40/David_with_the_Head_of_Goliath_by_Michelangelo_Merisi_da_Caravaggio.jpg", [
        "https://commons.wikimedia.org/wiki/Special:Redirect/file/David_with_the_Head_of_Goliath_by_Michelangelo_Merisi_da_Caravaggio.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/5/5a/David_holding_the_head_of_Goliath_by_Caravaggio.jpg",
    ]),
    ("07-xu-wei-ink-grapes.jpg", "jpeg", "https://upload.wikimedia.org/wikipedia/commons/4/41/Xu_Wei_Grapes.jpg", [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/41/Xu_Wei_Grapes.jpg/250px-Xu_Wei_Grapes.jpg",
    ]),
    ("08-dong-qichang-wanluan.jpg", "jpeg", "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/Wanluan_Thatched_Hall_by_Dong_Qichang.jpg/500px-Wanluan_Thatched_Hall_by_Dong_Qichang.jpg", [
        "https://upload.wikimedia.org/wikipedia/commons/1/1e/Wanluan_Thatched_Hall_by_Dong_Qichang.jpg",
    ]),
    ("09-chen-hongshou-leaf-album.jpg", "jpeg", "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d7/Chen_Hongshou%2C_leaf_album_painting.jpg/960px-Chen_Hongshou%2C_leaf_album_painting.jpg", [
        "https://upload.wikimedia.org/wikipedia/commons/d/d7/Chen_Hongshou%2C_leaf_album_painting.jpg",
    ]),
    ("10-zeng-jing-wang-shimin.jpg", "jpeg", "https://thumb.wikimedia.org/wikipedia/commons/thumb/c/c7/Zeng_Jing_-_Portrait_of_Wang_Shimin.JPG/500px-Zeng_Jing_-_Portrait_of_Wang_Shimin.JPG", [
        "https://upload.wikimedia.org/wikipedia/commons/c/c7/Zeng_Jing_-_Portrait_of_Wang_Shimin.JPG",
    ]),
    ("11-qiu-ying-han-palace.jpg", "jpeg", "https://upload.wikimedia.org/wikipedia/commons/thumb/f/fa/Ch%27iu_Ying_001.jpg/960px-Ch%27iu_Ying_001.jpg", [
        "https://upload.wikimedia.org/wikipedia/commons/f/fa/Ch%27iu_Ying_001.jpg",
    ]),
    ("12-tang-yin-court-ladies.jpg", "jpeg", "https://upload.wikimedia.org/wikipedia/commons/thumb/8/82/Court_Ladies_of_the_Former_Shu_by_Tang_Yin.jpg/960px-Court_Ladies_of_the_Former_Shu_by_Tang_Yin.jpg", [
        "https://upload.wikimedia.org/wikipedia/commons/8/82/Court_Ladies_of_the_Former_Shu_by_Tang_Yin.jpg",
    ]),
    ("13-ma-shouzhen-orchid-rock.jpg", "jpeg", "https://upload.wikimedia.org/wikipedia/commons/a/a9/%E6%98%8E_%E5%82%B3%E9%A6%AC%E5%AE%88%E7%9C%9F_%E8%98%AD%E7%9F%B3%E5%9C%96_%E8%BB%B8-Orchid_and_Rock_MET_DT8794.jpg", [
        "https://commons.wikimedia.org/wiki/Special:Redirect/file/%E6%98%8E_%E5%82%B3%E9%A6%AC%E5%AE%88%E7%9C%9F_%E8%98%AD%E7%9F%B3%E5%9C%96_%E8%BB%B8-Orchid_and_Rock_MET_DT8794.jpg",
    ]),
    ("14-liu-rushi-portrait.jpg", "jpeg", "https://upload.wikimedia.org/wikipedia/commons/0/0d/Portrait_of_Liu_Rushi.jpg", [
        "https://commons.wikimedia.org/wiki/Special:Redirect/file/Portrait_of_Liu_Rushi.jpg",
    ]),
    ("15-li-xiangjun-portrait.jpg", "jpeg", "https://upload.wikimedia.org/wikipedia/commons/a/a9/Portrait_of_Li_Xiangjun_%28%E6%9D%8E%E9%A6%99%E5%90%9B%29_by_Cui_He.jpg", [
        "https://commons.wikimedia.org/wiki/Special:Redirect/file/Portrait_of_Li_Xiangjun_(%E6%9D%8E%E9%A6%99%E5%90%9B)_by_Cui_He.jpg",
    ]),
    ("16-gu-hengbo-orchid-fan.jpg", "jpeg", "https://upload.wikimedia.org/wikipedia/commons/2/2d/%E9%A1%BE%E7%9C%89%E5%85%B0%E8%8A%B1%E5%9B%BE%E6%89%87%E9%A1%B5.jpg", [
        "https://commons.wikimedia.org/wiki/Special:Redirect/file/%E9%A1%BE%E7%9C%89%E5%85%B0%E8%8A%B1%E5%9B%BE%E6%89%87%E9%A1%B5.jpg",
    ]),
    ("17-dong-xiaowan-portrait.jpg", "jpeg", "https://upload.wikimedia.org/wikipedia/commons/f/f6/Dong_Xiaowan.jpg", [
        "https://commons.wikimedia.org/wiki/Special:Redirect/file/Dong_Xiaowan.jpg",
    ]),
    ("18-bian-yujing-orchid-rock.jpg", "jpeg", "https://upload.wikimedia.org/wikipedia/commons/5/56/Bian_Yujing_-_yujing_%E5%85%B0%E7%9F%B3.jpg", [
        "https://commons.wikimedia.org/wiki/Special:Redirect/file/Bian_Yujing_-_yujing_%E5%85%B0%E7%9F%B3.jpg",
    ]),
    ("19-kou-baimen-small-portrait.jpg", "jpeg", "https://upload.wikimedia.org/wikipedia/commons/d/dc/%E3%80%8A%E6%A0%A1%E6%9B%B8%E5%AF%87%E7%99%BD%E9%96%80%E5%B0%8F%E5%BD%B1%E3%80%8B.jpg", [
        "https://commons.wikimedia.org/wiki/Special:Redirect/file/%E3%80%8A%E6%A0%A1%E6%9B%B8%E5%AF%87%E7%99%BD%E9%96%80%E5%B0%8F%E5%BD%B1%E3%80%8B.jpg",
    ]),
    ("20-chen-yuanyuan-portrait.jpg", "jpeg", "https://upload.wikimedia.org/wikipedia/commons/d/d0/Portrait_of_Chen_Yuanyuan.jpg", [
        "https://commons.wikimedia.org/wiki/Special:Redirect/file/Portrait_of_Chen_Yuanyuan.jpg",
    ]),
    ("21-xue-susu-plum-narcissus.jpg", "jpeg", "https://upload.wikimedia.org/wikipedia/commons/7/7e/%E8%96%9B%E7%B4%A0%E7%B4%A0_%E6%A2%85%E8%8A%B1%E6%B0%B4%E4%BB%99%E5%9B%BE%E8%BD%B4.jpg", [
        "https://commons.wikimedia.org/wiki/Special:Redirect/file/%E8%96%9B%E7%B4%A0%E7%B4%A0_%E6%A2%85%E8%8A%B1%E6%B0%B4%E4%BB%99%E5%9B%BE%E8%BD%B4.jpg",
    ]),
    ("audio-orfeo-toccata.ogg", "ogg", "https://upload.wikimedia.org/wikipedia/commons/3/3d/Orfeo_-_Toccata.ogg", [
        "https://commons.wikimedia.org/wiki/Special:Redirect/file/Orfeo_-_Toccata.ogg",
    ]),
    ("audio-lamento-della-ninfa.ogg", "ogg", "https://upload.wikimedia.org/wikipedia/commons/4/41/Monteverdi_-_Lamento_della_Ninfa.ogg", [
        "https://commons.wikimedia.org/wiki/Special:Redirect/file/Monteverdi_-_Lamento_della_Ninfa.ogg",
    ]),
    ("audio-liu-shui-guqin.ogg", "ogg", "https://upload.wikimedia.org/wikipedia/commons/e/e0/Liu_Shui.ogg", [
        "https://commons.wikimedia.org/wiki/Special:Redirect/file/Liu_Shui.ogg",
    ]),
]

def valid_signature(data: bytes, kind: str) -> bool:
    if kind == "jpeg":
        return data.startswith(b"\xff\xd8\xff")
    if kind == "ogg":
        return data.startswith(b"OggS")
    return False

def download_one(filename: str, kind: str, urls: list[str]) -> dict:
    destination = ASSET_DIR / filename
    errors: list[str] = []
    for url in urls:
        for attempt in range(1, 4):
            try:
                request = Request(
                    url,
                    headers={
                        "User-Agent": USER_AGENT,
                        "Accept": "*/*",
                    },
                )
                with urlopen(request, timeout=60) as response:
                    status = getattr(response, "status", 200)
                    content_type = response.headers.get_content_type()
                    data = response.read(MAX_BYTES + 1)
                if status != 200:
                    raise RuntimeError(f"HTTP {status}")
                if len(data) > MAX_BYTES:
                    raise RuntimeError(f"file exceeds {MAX_BYTES} bytes")
                if len(data) < (50_000 if kind == "ogg" else 8_000):
                    raise RuntimeError(f"file too small ({len(data)} bytes)")
                if not valid_signature(data, kind):
                    raise RuntimeError(f"unexpected file signature; content-type={content_type}")
                destination.write_bytes(data)
                return {
                    "file": filename,
                    "kind": kind,
                    "source": url,
                    "bytes": len(data),
                    "sha256": hashlib.sha256(data).hexdigest(),
                    "content_type": content_type,
                }
            except (HTTPError, URLError, TimeoutError, OSError, RuntimeError) as exc:
                errors.append(f"{url} [attempt {attempt}]: {exc}")
                time.sleep(1.2 * attempt)
    raise RuntimeError(f"Could not fetch {filename}:\n" + "\n".join(errors))

def verify_html() -> None:
    html = HTML_FILE.read_text(encoding="utf-8")
    image_srcs = re.findall(r"<img\b[^>]*\bsrc=[\"']([^\"']*)[\"']", html, flags=re.I)
    image_srcs = [src for src in image_srcs if src]
    audio_srcs = re.findall(r"<audio\b[^>]*\bsrc=[\"']([^\"']*)[\"']", html, flags=re.I)
    if len(image_srcs) != 21:
        raise RuntimeError(f"Expected 21 rendered artwork images, found {len(image_srcs)}")
    if len(audio_srcs) != 4:
        raise RuntimeError(f"Expected 4 audio elements (3 tracks + global player), found {len(audio_srcs)}")
    if any(not src.startswith(PUBLIC_PREFIX) for src in image_srcs):
        raise RuntimeError("At least one displayed image still uses a remote URL instead of local hosting")
    if any(not src.startswith(PUBLIC_PREFIX) for src in audio_srcs):
        raise RuntimeError("At least one audio element still uses a remote URL instead of local hosting")
    for filename, _, _, _ in ASSETS:
        if f"{PUBLIC_PREFIX}{filename}" not in html:
            raise RuntimeError(f"HTML does not reference expected local asset: {filename}")
        if not (ASSET_DIR / filename).is_file():
            raise RuntimeError(f"Missing local asset after download: {filename}")
    if re.search(r"(chatgpt\.com|utm_source=chatgpt|openai\.com)", html, flags=re.I):
        raise RuntimeError("GPT tracking text found in public page source")

def main() -> int:
    if not HTML_FILE.is_file():
        raise SystemExit(f"Missing page HTML: {HTML_FILE}")
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    results = []
    for filename, kind, primary, fallbacks in ASSETS:
        result = download_one(filename, kind, [primary, *fallbacks])
        results.append(result)
        print(f"OK {filename}: {result['bytes']:,} bytes sha256={result['sha256']}")
    manifest = {
        "page": "/1600-caravaggio-qinhuai-art-special/",
        "generated_by": "tools/prepare_art_special_media.py",
        "assets": results,
    }
    (ASSET_DIR / "asset-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    verify_html()
    print(f"MEDIA QA PASSED: {len([x for x in results if x['kind'] == 'jpeg'])} images + {len([x for x in results if x['kind'] == 'ogg'])} audio files")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"MEDIA QA FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)
