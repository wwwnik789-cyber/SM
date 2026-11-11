#!/usr/bin/env python3
"""Build 16:9 covers for the New Year 2027 blog articles."""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
SOURCES = REPO / "marketing" / "novogodnee-oformlenie-2027" / "creatives" / "source"
OUT = REPO / "public" / "media"

W, H = 1600, 900

COVERS = [
    ("lobby.jpg", "ng-2027-office.jpg", (0.55, 0.50)),
    ("photozone.jpg", "ng-2027-photozone.jpg", (0.55, 0.50)),
    ("corporate.jpg", "ng-2027-brus-banner.jpg", (0.55, 0.50)),
    ("art.jpg", "ng-2027-brandbook.jpg", (0.55, 0.45)),
]


def cover(path: Path, focus: tuple[float, float]) -> Image.Image:
    image = Image.open(path).convert("RGB")
    scale = max(W / image.width, H / image.height)
    resized = image.resize(
        (round(image.width * scale), round(image.height * scale)),
        Image.Resampling.LANCZOS,
    )
    left = round((resized.width - W) * focus[0])
    top = round((resized.height - H) * focus[1])
    left = max(0, min(left, resized.width - W))
    top = max(0, min(top, resized.height - H))
    return resized.crop((left, top, left + W, top + H))


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for source, target, focus in COVERS:
        src = SOURCES / source
        if not src.exists():
            print(f"Нет исходника: {src}")
            return 1
        image = cover(src, focus)
        path = OUT / target
        image.save(path, format="JPEG", quality=88, optimize=True, progressive=True)
        print(f"{target}: {W}×{H}, {path.stat().st_size // 1024} КБ")
    return 0


if __name__ == "__main__":
    sys.exit(main())
