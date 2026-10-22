#!/usr/bin/env python3
"""
Сравнение качества мастеров: Q92 против Q78 (или любой другой пары).

Перекодирует мастер в целевое качество, потом сравнивает кропы —
важно увидеть, не появляются ли полосы (banding) на гладком маджентовом
градиенте стены.

Запуск:
  python3 scripts/banners/compare_quality.py <master.jpg> <Q> [x0 y0 x1 y1]
"""
from __future__ import annotations

import sys
from pathlib import Path

import pyvips
from PIL import Image, ImageChops, ImageStat

Image.MAX_IMAGE_PIXELS = None

SHRINK = 2  # во сколько раз уменьшаем для сравнения


def recode(src: Path, q: int, out: Path) -> Path:
    """Мастер → JPEG в целевом качестве (уменьшенный, для быстрого сравнения)."""
    img = pyvips.Image.jpegload(str(src), shrink=SHRINK, access="sequential")
    img.write_to_file(str(out), Q=q, subsample_mode="off", strip=True)
    del img
    return out


def main() -> int:
    src = Path(sys.argv[1])
    q = int(sys.argv[2])
    box = tuple(int(x) for x in sys.argv[3:7]) if len(sys.argv) >= 7 else (9000, 4000, 13000, 7000)

    a_small = Path(f"/tmp/cmp-q92-{src.stem}.jpg")
    b_small = Path(f"/tmp/cmp-q{q}-{src.stem}.jpg")
    recode(src, 92, a_small)
    recode(src, q, b_small)

    box2 = tuple(v // SHRINK for v in box)
    a = Image.open(a_small).crop(box2)
    b = Image.open(b_small).crop(box2)
    diff = ImageChops.difference(a, b)
    stat = ImageStat.Stat(diff)
    print(f"средняя разница по каналам: {[round(v, 2) for v in stat.mean]}; "
          f"максимум по каналу: {max(d[1] for d in diff.getextrema())}")

    w, h = a.size
    sheet = Image.new("RGB", (w, h * 2 + 12), (255, 255, 255))
    sheet.paste(a, (0, 0))
    sheet.paste(b, (0, h + 12))
    out = Path(f"/tmp/cmp-{src.stem}-q{q}.png")
    sheet.save(out)
    print(f"сравнение (сверху Q92, снизу Q{q}): {out} {sheet.size}")
    a_small.unlink(missing_ok=True)
    b_small.unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
