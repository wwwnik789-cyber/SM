#!/usr/bin/env python3
"""Собирает наглядный лист со всеми вариантами «нежного» фона.

    python previews.py
"""

import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))
MANROPE = os.path.join(ROOT, "fonts", "Manrope-Variable.ttf")

VARIANTS = [
    ("01-pudrovyj-rozovyj", "01 · пудрово-розовый", "#F8E7E3"),
    ("02-shampan", "02 · шампань", "#F8EFE3"),
    ("03-holodnyj-pudrovyj", "03 · холодный пудровый", "#F0E8ED"),
    ("04-svetlyj-len", "04 · светлый лён", "#F6EEE6"),
]

BG = (26, 24, 23)
TXT = (240, 233, 226)


def font(size, weight=600):
    f = ImageFont.truetype(MANROPE, size)
    try:
        f.set_variation_by_axes([weight])
    except Exception:
        pass
    return f


def sheet(kind: str, tile_w: int, name: str):
    rows = []
    for key, title, hexv in VARIANTS:
        path = os.path.join(ROOT, "variants", f"{kind}--{key}.jpg")
        if not os.path.exists(path):
            continue
        im = Image.open(path).convert("RGB")
        h = int(tile_w * im.height / im.width)
        rows.append((im.resize((tile_w, h), Image.LANCZOS), title, hexv))

    if not rows:
        return

    pad, gap, cap = 36, 26, 62
    cols = 2 if len(rows) > 1 else 1
    tile_h = rows[0][0].height
    n_rows = (len(rows) + cols - 1) // cols
    W = pad * 2 + cols * tile_w + (cols - 1) * gap
    H = pad * 2 + n_rows * (tile_h + cap) + (n_rows - 1) * gap

    out = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(out)

    f_cap = font(24, 700)
    f_hex = font(18, 500)
    for i, (im, title, hexv) in enumerate(rows):
        cx = pad + (i % cols) * (tile_w + gap)
        cy = pad + (i // cols) * (tile_h + cap + gap)
        out.paste(im, (cx, cy))
        d.rectangle([cx, cy, cx + tile_w - 1, cy + tile_h - 1], outline=(70, 62, 56), width=1)
        d.text((cx + 2, cy + tile_h + 14), title, font=f_cap, fill=TXT)
        d.text((cx + tile_w - 2, cy + tile_h + 17), hexv.upper(), font=f_hex,
               fill=(150, 136, 122), anchor="ra")

    path = os.path.join(ROOT, name)
    out.save(path, quality=92, optimize=True)
    print("✓", path, out.size)


if __name__ == "__main__":
    sheet("16x9", 1120, "preview-16x9-varianty.jpg")
    sheet("4x5", 560, "preview-4x5-varianty.jpg")
