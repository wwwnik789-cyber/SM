#!/usr/bin/env python3
"""Generate concrete branding concept graphics for the Anikom Arena deck."""
from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageEnhance

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
OUT = ROOT / "concepts"
OUT.mkdir(parents=True, exist_ok=True)

NAVY = "#091A2B"
NAVY_2 = "#102B45"
NAVY_3 = "#173B59"
RED = "#D94B43"
RED_DARK = "#A42F35"
WHITE = "#F6F8FA"
MIST = "#DCE5EC"
STEEL = "#91A3B2"
GREEN = "#2E765B"
GOLD = "#D5B363"

REG = str(ROOT / "fonts" / "DejaVuSans.ttf")
BOLD = str(ROOT / "fonts" / "DejaVuSans-Bold.ttf")
LOGO = Image.open(ASSETS / "anikom-arena-logo.png").convert("RGBA")


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(BOLD if bold else REG, size)


def gradient(size: tuple[int, int], top: str, bottom: str) -> Image.Image:
    w, h = size
    a = Image.new("RGB", size, top)
    b = Image.new("RGB", size, bottom)
    mask = Image.new("L", size)
    md = ImageDraw.Draw(mask)
    for y in range(h):
        md.line((0, y, w, y), fill=int(255 * y / max(1, h - 1)))
    return Image.composite(b, a, mask).convert("RGBA")


def paste_logo(canvas: Image.Image, box: tuple[int, int, int, int], opacity: int = 255) -> None:
    x, y, w, h = box
    logo = LOGO.copy()
    logo.thumbnail((w, h), Image.Resampling.LANCZOS)
    if opacity != 255:
        alpha = logo.getchannel("A").point(lambda p: p * opacity // 255)
        logo.putalpha(alpha)
    canvas.alpha_composite(logo, (x + (w - logo.width) // 2, y + (h - logo.height) // 2))


def centered(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, fnt, fill: str, anchor="mm") -> None:
    draw.text(xy, text, font=fnt, fill=fill, anchor=anchor)


def pitch(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], fill=WHITE, width=6) -> None:
    x0, y0, x1, y1 = box
    draw.rounded_rectangle(box, radius=28, outline=fill, width=width)
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    draw.line((cx, y0, cx, y1), fill=fill, width=width)
    r = min(x1 - x0, y1 - y0) // 7
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=fill, width=width)
    draw.rectangle((x0, cy - 120, x0 + 150, cy + 120), outline=fill, width=width)
    draw.rectangle((x1 - 150, cy - 120, x1, cy + 120), outline=fill, width=width)


def tower_artwork() -> Image.Image:
    w, h = 1800, 1000
    im = gradient((w, h), NAVY_2, NAVY)
    d = ImageDraw.Draw(im, "RGBA")
    d.polygon([(0, 0), (490, 0), (760, h), (0, h)], fill=RED)
    d.polygon([(180, 0), (500, 0), (770, h), (640, h)], fill=WHITE)
    pitch(d, (1060, 95, 1740, 905), fill=(246, 248, 250, 58), width=5)
    paste_logo(im, (80, 90, 670, 820))
    d.rounded_rectangle((820, 132, 1710, 230), radius=25, fill=NAVY_3, outline=STEEL, width=2)
    d.text((865, 180), "МЕДИА-БАШНЯ", font=font(68, True), fill=WHITE, anchor="lm")
    d.rectangle((865, 278, 1090, 292), fill=RED)
    d.text((865, 350), "МАТЧ", font=font(84, True), fill=WHITE)
    d.text((865, 446), "ТРАНСЛЯЦИЯ", font=font(84, True), fill=WHITE)
    d.text((865, 565), "АНИКОМ АРЕНА", font=font(32, True), fill=MIST)
    d.text((865, 612), "ПОЛЕ  •  СОБЫТИЯ  •  КОНТЕНТ", font=font(25), fill=STEEL)
    y = 740
    for i in range(3):
        x = 865 + i * 260
        d.rounded_rectangle((x, y, x + 220, y + 92), radius=16, outline=(246, 248, 250, 100), width=3)
        centered(d, (x + 110, y + 46), f"ПАРТНЁР {i + 1:02d}", font(18, True), MIST)
    return im


def tower_mockup(art: Image.Image) -> Image.Image:
    base = Image.open(ASSETS / "camera-tower.jpg").convert("RGBA")
    # The blank front panel is almost frontal; a restrained inset preserves its seams.
    panel = ImageOps.fit(art.convert("RGB"), (752, 454), Image.Resampling.LANCZOS).convert("RGBA")
    panel.putalpha(238)
    shadow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle((397, 1282, 1167, 1752), radius=8, fill=(0, 0, 0, 95))
    base.alpha_composite(shadow)
    base.alpha_composite(panel, (405, 1290))
    # Keep the physical blue side posts visible.
    d = ImageDraw.Draw(base, "RGBA")
    d.rectangle((394, 1282, 412, 1747), fill=(9, 26, 43, 180))
    d.rectangle((1150, 1282, 1168, 1747), fill=(9, 26, 43, 180))
    return base.convert("RGB")


def partner_presswall() -> Image.Image:
    w, h = 1200, 1000
    im = gradient((w, h), NAVY_2, NAVY)
    d = ImageDraw.Draw(im, "RGBA")
    pitch(d, (45, 45, 1155, 955), fill=(255, 255, 255, 24), width=4)
    for row in range(5):
        for col in range(5):
            x = 45 + col * 230 + (115 if row % 2 else 0)
            if x > 1070:
                continue
            if (row + col) % 2 == 0:
                paste_logo(im, (x, 55 + row * 185, 120, 155), 230)
            else:
                d.rounded_rectangle((x, 100 + row * 185, x + 150, 165 + row * 185), radius=12, outline=(246, 248, 250, 155), width=3)
                centered(d, (x + 75, 132 + row * 185), "ПАРТНЁР", font(18, True), MIST)
    d.rectangle((0, 0, 1200, 24), fill=RED)
    d.rectangle((0, 976, 1200, 1000), fill=RED)
    return im


def matchday_presswall() -> Image.Image:
    w, h = 1200, 1000
    im = gradient((w, h), NAVY_3, NAVY)
    d = ImageDraw.Draw(im, "RGBA")
    d.polygon([(0, 0), (455, 0), (760, h), (0, h)], fill=RED_DARK)
    d.polygon([(960, 0), (1200, 0), (1200, h), (690, h)], fill=(217, 75, 67, 70))
    d.ellipse((305, 120, 895, 710), outline=(246, 248, 250, 32), width=6)
    paste_logo(im, (372, 125, 456, 610))
    centered(d, (600, 770), "MATCH DAY", font(58, True), WHITE)
    centered(d, (600, 830), "АНИКОМ АРЕНА", font(27, True), MIST)
    for x, label in ((90, "КОМАНДА 01"), (900, "КОМАНДА 02")):
        d.rounded_rectangle((x, 770, x + 210, 885), radius=20, outline=(246, 248, 250, 150), width=4)
        centered(d, (x + 105, 828), label, font(20, True), WHITE)
    d.rectangle((0, 946, 1200, 1000), fill=RED)
    return im


def hero_photozone() -> Image.Image:
    w, h = 1500, 900
    im = gradient((w, h), NAVY_2, NAVY)
    d = ImageDraw.Draw(im, "RGBA")
    pitch(d, (50, 45, 1450, 855), fill=(246, 248, 250, 64), width=6)
    d.polygon([(0, 0), (320, 0), (650, h), (0, h)], fill=RED_DARK)
    d.polygon([(1500, 0), (1260, 0), (940, h), (1500, h)], fill=(217, 75, 67, 65))
    paste_logo(im, (445, 100, 610, 690))
    d.text((75, 795), "ФОТОЗОНА • НАГРАЖДЕНИЕ • ПАРТНЁРЫ", font=font(27, True), fill=MIST)
    for idx, x in enumerate((1120, 1250, 1380), 1):
        d.rounded_rectangle((x, 745, x + 95, 815), radius=12, outline=(246, 248, 250, 120), width=3)
        centered(d, (x + 48, 780), f"P{idx}", font(18, True), WHITE)
    return im


def long_banner(variant: int) -> Image.Image:
    w, h = 1800, 360
    im = gradient((w, h), NAVY_2, NAVY)
    d = ImageDraw.Draw(im, "RGBA")
    if variant == 1:
        for x in range(20, w, 355):
            paste_logo(im, (x, 35, 210, 290), 245)
        d.rectangle((0, 0, w, 18), fill=RED)
        d.rectangle((0, h - 18, w, h), fill=RED)
    elif variant == 2:
        d.polygon([(0, 0), (520, 0), (720, h), (0, h)], fill=RED_DARK)
        paste_logo(im, (40, 25, 250, 310))
        d.text((700, 92), "ПАРТНЁРСКАЯ ЛИНИЯ", font=font(48, True), fill=WHITE)
        d.text((700, 160), "СМЕННЫЕ БЛОКИ НА СЕЗОН / ТУРНИР", font=font(25), fill=MIST)
        for i in range(4):
            x = 700 + i * 250
            d.rounded_rectangle((x, 220, x + 210, 315), radius=15, outline=(246, 248, 250, 140), width=3)
            centered(d, (x + 105, 268), f"ПАРТНЁР {i + 1}", font(17, True), WHITE)
    else:
        pitch(d, (30, 20, 1770, 340), fill=(246, 248, 250, 30), width=3)
        d.rectangle((0, 0, 500, h), fill=RED)
        d.text((55, 88), "ТУРНИР", font=font(63, True), fill=WHITE)
        d.text((55, 175), "MATCH DAY", font=font(45, True), fill=WHITE)
        d.text((610, 75), "РАСПИСАНИЕ • СЧЁТ • ПАРТНЁРЫ", font=font(37, True), fill=WHITE)
        d.text((610, 145), "СМЕННОЕ ПОЛОТНО ДЛЯ СОБЫТИЯ", font=font(24), fill=MIST)
        paste_logo(im, (1410, 25, 260, 310))
    return im


def placement_map() -> Image.Image:
    base = Image.open(ASSETS / "stand-close.jpg").convert("RGBA")
    d = ImageDraw.Draw(base, "RGBA")
    zones = [
        ((235, 742, 1965, 865), "F1", "БАЛКОННАЯ ЛЕНТА"),
        ((228, 1110, 915, 1215), "F2", "НИЖНИЙ ЛЕВЫЙ МОДУЛЬ"),
        ((1265, 1110, 1960, 1215), "F3", "НИЖНИЙ ПРАВЫЙ МОДУЛЬ"),
        ((770, 530, 1435, 640), "F4", "ЦЕНТРАЛЬНЫЙ ВХОД"),
    ]
    for box, code, label in zones:
        d.rounded_rectangle(box, radius=14, fill=(9, 26, 43, 190), outline=RED, width=7)
        x0, y0, x1, y1 = box
        d.ellipse((x0 - 8, y0 - 48, x0 + 74, y0 + 34), fill=RED)
        centered(d, (x0 + 33, y0 - 7), code, font(25, True), WHITE)
        d.rounded_rectangle((x0 + 85, y0 - 40, min(x1, x0 + 500), y0 + 25), radius=14, fill=(9, 26, 43, 220))
        d.text((x0 + 110, y0 - 22), label, font=font(20, True), fill=WHITE)
    return base.convert("RGB")


def build() -> None:
    art = tower_artwork()
    art.save(OUT / "tower-banner-artwork.png", optimize=True)
    tower_mockup(art).save(OUT / "tower-banner-mockup.jpg", quality=91, optimize=True, progressive=True)
    partner_presswall().save(OUT / "presswall-partner-3000x2500.png", optimize=True)
    matchday_presswall().save(OUT / "presswall-matchday-3000x2500.png", optimize=True)
    hero_photozone().save(OUT / "photozone-hero-5000x3000.png", optimize=True)
    for idx in range(1, 4):
        long_banner(idx).save(OUT / f"flat-frame-banner-{idx}.png", optimize=True)
    placement_map().save(OUT / "flat-frame-placement-map.jpg", quality=91, optimize=True, progressive=True)
    for path in sorted(OUT.iterdir()):
        print(path.name, path.stat().st_size)


if __name__ == "__main__":
    build()
