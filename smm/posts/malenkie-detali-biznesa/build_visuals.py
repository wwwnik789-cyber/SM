#!/usr/bin/env python3
"""Build the second, documentary-style set of four 1200x675 visuals."""
from pathlib import Path
from math import cos, sin, radians
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent
W, H = 1200, 675
FONT_PATH = ROOT.parents[2] / "presentations" / "dealerships-2026" / "fonts" / "Montserrat-Variable.ttf"
WHITE = "#ffffff"
GOLD = "#d5a600"


def font(size, weight="Regular"):
    f = ImageFont.truetype(str(FONT_PATH), size=size)
    try:
        f.set_variation_by_name(weight)
    except Exception:
        pass
    return f


def cover(path):
    return ImageOps.fit(Image.open(path).convert("RGB"), (W, H), method=Image.Resampling.LANCZOS)


def centered_text(draw, center, text, f, fill=WHITE, spacing=1, shadow=True):
    bbox = draw.multiline_textbbox((0, 0), text, font=f, spacing=spacing, align="center")
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = center[0] - tw / 2
    y = center[1] - th / 2 - bbox[1]
    if shadow:
        draw.multiline_text((x + 2, y + 2), text, font=f, fill="#111116", spacing=spacing, align="center")
    draw.multiline_text((x, y), text, font=f, fill=fill, spacing=spacing, align="center")


def build_fotoprops():
    cover(ROOT / "v2-base-fotoprops-final.jpg").save(
        ROOT / "01-fotoprops-pizza-croissant-coffee.jpg", quality=94
    )


def build_navigation():
    im = cover(ROOT / "v2-base-navigation.jpg")
    d = ImageDraw.Draw(im)
    # Text is placed directly on the three real acrylic plaques generated in the scene.
    centered_text(d, (320, 104), "ОСНОВНОЙ ЗАЛ  →", font(22, "Bold"), shadow=False)
    centered_text(d, (717, 327), "WC", font(20, "ExtraBold"), shadow=False)
    centered_text(d, (1064, 314), "КАБИНЕТ\nГЕНЕРАЛЬНОГО\nДИРЕКТОРА", font(13, "Bold"), spacing=0, shadow=False)
    # Small arrows stay inside the mounted plates instead of floating over the wall.
    d.text((723, 350), "↓", font=font(15, "Bold"), fill=GOLD, anchor="mm")
    d.text((1136, 348), "→", font=font(15, "Bold"), fill=GOLD, anchor="mm")
    im.save(ROOT / "02-navigation-signs.jpg", quality=94)


def wheel_font(draw, text):
    for size in range(13, 9, -1):
        f = font(size, "ExtraBold")
        box = draw.multiline_textbbox((0, 0), text, font=f, spacing=0, align="center")
        if box[2] - box[0] <= 92 and box[3] - box[1] <= 34:
            return f
    return font(9, "ExtraBold")


def build_wheel():
    im = cover(ROOT / "v2-base-wheel-clean.jpg")
    d = ImageDraw.Draw(im)
    cx, cy = 627, 320
    labels = [
        "СКИДКА\n10%",
        "БЕСПЛАТНЫЙ\nКОФЕ",
        "БЕСПЛАТНЫЙ\nДЕСЕРТ",
        "СКИДКА\n15%",
        "БЕСПЛАТНЫЙ\nКОФЕ",
        "БЕСПЛАТНЫЙ\nДЕСЕРТ",
        "СКИДКА\n10%",
        "БЕСПЛАТНЫЙ\nКОФЕ",
    ]
    # Eight segment centers on the real, almost front-facing physical wheel.
    for i, text in enumerate(labels):
        angle = radians(-112.5 + i * 45)
        x = cx + cos(angle) * 118
        y = cy + sin(angle) * 118
        centered_text(d, (x, y), text, wheel_font(d, text), spacing=0)
    im.save(ROOT / "03-prize-wheel-cafe.jpg", quality=94)


def build_character():
    cover(ROOT / "v2-04-fictional-character-standee-clean.jpg").save(
        ROOT / "04-fictional-character-standee.jpg", quality=94
    )


if __name__ == "__main__":
    build_fotoprops()
    build_navigation()
    build_wheel()
    build_character()
    print("Built four documentary-style visuals at 1200x675")
