#!/usr/bin/env python3
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
TARGETS = [
    ROOT / "spacex-vs-rocket-lab-defense-launch-20260815/assets/victus-haze-pioneer.jpg",
    ROOT / "spacex-vs-rocket-lab-defense-launch-20260815/assets/rocketlab-lightning.png",
    ROOT / "golden-dome-defense-investment-map-20260815/assets/rocketlab-lightning.png",
    ROOT / "golden-dome-defense-investment-map-20260815/assets/rtx-sm3.jpg",
    ROOT / "golden-dome-defense-investment-map-20260815/assets/gbi-launch.jpg",
    ROOT / "golden-dome-defense-investment-map-20260815/assets/gitai-s3.jpg",
]

for path in TARGETS:
    if not path.exists():
        raise FileNotFoundError(path)
    with Image.open(path) as src:
        src.load()
        if path.suffix.lower() in {".jpg", ".jpeg"}:
            out = src.convert("RGB")
            out.save(path, format="JPEG", quality=92, optimize=True, progressive=True)
            expected = "JPEG"
        elif path.suffix.lower() == ".png":
            if src.mode not in {"RGB", "RGBA"}:
                src = src.convert("RGBA")
            src.save(path, format="PNG", optimize=True)
            expected = "PNG"
        else:
            raise RuntimeError(f"Unsupported extension: {path}")
    with Image.open(path) as check:
        check.verify()
    with Image.open(path) as check:
        if check.format != expected:
            raise RuntimeError(f"MIME/extension normalization failed: {path}: {check.format} != {expected}")
        print(f"MIME OK {path.relative_to(ROOT)} | {check.size} {check.format}")
