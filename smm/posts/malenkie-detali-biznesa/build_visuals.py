#!/usr/bin/env python3
"""Prepare four 1200x675 publication visuals with exact Russian labels."""
from pathlib import Path
from math import cos, sin, radians
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parent
W, H = 1200, 675
FONT_PATH = ROOT.parents[2] / "presentations" / "dealerships-2026" / "fonts" / "Montserrat-Variable.ttf"
PURPLE = "#7550b5"
GOLD = "#d5a600"
DARK = "#14141b"
WHITE = "#ffffff"


def font(size, weight="Regular"):
    f = ImageFont.truetype(str(FONT_PATH), size=size)
    try:
        f.set_variation_by_name(weight)
    except Exception:
        pass
    return f


def cover(path):
    return ImageOps.fit(Image.open(path).convert("RGB"), (W, H), method=Image.Resampling.LANCZOS)


def rounded_panel(im, box, radius=18, fill=DARK, outline=GOLD, width=3, shadow=10):
    x1, y1, x2, y2 = box
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ld.rounded_rectangle((x1 + shadow, y1 + shadow, x2 + shadow, y2 + shadow), radius=radius, fill=(0, 0, 0, 100))
    layer = layer.filter(ImageFilter.GaussianBlur(6))
    im.paste(layer, (0, 0), layer)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def center_text(draw, box, text, f, fill=WHITE, spacing=3):
    x1, y1, x2, y2 = box
    bbox = draw.multiline_textbbox((0, 0), text, font=f, spacing=spacing, align="center")
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.multiline_text(((x1 + x2 - tw) / 2, (y1 + y2 - th) / 2 - bbox[1]), text, font=f, fill=fill, spacing=spacing, align="center")


def build_fotoprops():
    im = cover(ROOT / "base-fotoprops.jpg")
    im.save(ROOT / "01-fotoprops-pizza-croissant-coffee.jpg", quality=94)


def build_navigation():
    im = cover(ROOT / "base-navigation.jpg")
    d = ImageDraw.Draw(im)
    # Three physically plausible, high-contrast wayfinding plaques.
    panels = [
        ((150, 174, 485, 242), "ОСНОВНОЙ ЗАЛ   →", 25),
        ((815, 185, 1090, 253), "WC   →", 29),
        ((735, 300, 1090, 405), "КАБИНЕТ ГЕНЕРАЛЬНОГО\nДИРЕКТОРА   →", 20),
    ]
    for box, text, size in panels:
        rounded_panel(im, box, radius=15)
        center_text(d, box, text, font(size, "Bold"))
    # Accent marker that ties the system together.
    d.rounded_rectangle((150, 252, 270, 260), radius=4, fill=PURPLE)
    d.rounded_rectangle((815, 263, 905, 271), radius=4, fill=PURPLE)
    d.rounded_rectangle((735, 415, 855, 423), radius=4, fill=PURPLE)
    im.save(ROOT / "02-navigation-signs.jpg", quality=94)


def fit_multiline(draw, text, max_width, max_height, start=19, minimum=12):
    for size in range(start, minimum - 1, -1):
        f = font(size, "Bold")
        bbox = draw.multiline_textbbox((0, 0), text, font=f, spacing=1, align="center")
        if bbox[2] - bbox[0] <= max_width and bbox[3] - bbox[1] <= max_height:
            return f
    return font(minimum, "Bold")


def build_wheel():
    im = cover(ROOT / "base-wheel-clean.jpg").convert("RGBA")
    # Soft shadow behind wheel and stand.
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    cx, cy, r = 950, 286, 182
    sd.ellipse((cx-r+12, cy-r+15, cx+r+12, cy+r+15), fill=(0, 0, 0, 120))
    sd.rounded_rectangle((915, 430, 997, 612), radius=20, fill=(0, 0, 0, 110))
    shadow = shadow.filter(ImageFilter.GaussianBlur(12))
    im.alpha_composite(shadow)

    d = ImageDraw.Draw(im)
    colors = [PURPLE, GOLD, "#24242f", "#9b69d2", "#e4b812", "#363642"]
    labels = [
        "СКИДКА\n10%",
        "БЕСПЛАТНЫЙ\nКОФЕ",
        "БЕСПЛАТНЫЙ\nДЕСЕРТ",
        "СКИДКА\n15%",
        "БЕСПЛАТНЫЙ\nКОФЕ",
        "БЕСПЛАТНЫЙ\nДЕСЕРТ",
    ]
    # Stand first, wheel on top.
    d.rounded_rectangle((918, 408, 982, 605), radius=18, fill="#24242d", outline=GOLD, width=4)
    d.rounded_rectangle((850, 588, 1050, 625), radius=18, fill=DARK, outline=GOLD, width=4)
    for i in range(6):
        start = -90 + i * 60
        d.pieslice((cx-r, cy-r, cx+r, cy+r), start=start, end=start+60, fill=colors[i], outline=WHITE, width=4)
    d.ellipse((cx-r-8, cy-r-8, cx+r+8, cy+r+8), outline=DARK, width=12)
    d.ellipse((cx-32, cy-32, cx+32, cy+32), fill=DARK, outline=WHITE, width=4)
    d.ellipse((cx-10, cy-10, cx+10, cy+10), fill=GOLD)
    # Labels remain horizontal for social-feed readability.
    for i, text in enumerate(labels):
        angle = radians(-60 + i * 60)
        tx = cx + cos(angle) * 112
        ty = cy + sin(angle) * 112
        f = fit_multiline(d, text, 116, 46, start=16, minimum=12)
        bbox = d.multiline_textbbox((0, 0), text, font=f, spacing=1, align="center")
        tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
        # Dark micro-shadow improves contrast over gold segments.
        d.multiline_text((tx-tw/2+1, ty-th/2-bbox[1]+2), text, font=f, fill="#09090d", spacing=1, align="center")
        d.multiline_text((tx-tw/2, ty-th/2-bbox[1]), text, font=f, fill=WHITE, spacing=1, align="center")
    # Pointer.
    d.polygon([(cx, cy-r-17), (cx-22, cy-r-55), (cx+22, cy-r-55)], fill=GOLD, outline=DARK)
    # Small neutral plaque on the stand.
    d.rounded_rectangle((875, 506, 1025, 555), radius=12, fill=PURPLE, outline=WHITE, width=2)
    center_text(d, (875, 506, 1025, 555), "КРУТИ!", font(19, "ExtraBold"))
    im.convert("RGB").save(ROOT / "03-prize-wheel-cafe.jpg", quality=94)


def build_standee():
    im = cover(ROOT / "04-edward-cullen-standee-clean.jpg")
    im.save(ROOT / "04-edward-cullen-standee.jpg", quality=94)


if __name__ == "__main__":
    build_fotoprops()
    build_navigation()
    build_wheel()
    build_standee()
    print("Built 4 visuals at 1200x675")
