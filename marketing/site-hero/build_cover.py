#!/usr/bin/env python3
"""Сборка готовой обложки первого экрана для sm-production.ru.

Из двух сгенерированных сцен делает полный набор файлов:
  cover-desktop-text-2560x1440.jpg   обложка с типографикой, широкие экраны
  cover-desktop-text-1920x1080.jpg   то же, базовый размер Tilda
  cover-desktop-clean-1920x1080.jpg  без текста — если заголовок живёт в HTML
  cover-mobile-text-1080x1920.jpg    мобильная обложка с текстом
  cover-mobile-clean-1080x1920.jpg   мобильная без текста
  og-1200x630.jpg                    превью для соцсетей
  preview.jpg                        контактный лист

Запуск из корня репозитория:
    .venv/bin/python marketing/site-hero/build_cover.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
SRC = HERE / "generated"
OUT = HERE / "cover"
FONT_VF = HERE.parents[1] / "banners" / "anikom-arena-3000x2500-concepts" / "source" / "Montserrat-Variable.ttf"

NAVY = (8, 26, 43)
CORAL = (217, 74, 67)
WHITE = (255, 255, 255)
MUTED = (188, 199, 212)
DIM = (138, 152, 168)

if not FONT_VF.exists():
    raise SystemExit(f"нет шрифта: {FONT_VF}")


# ─── шрифт и текст ───────────────────────────────────────────────────────────


def font(size: int, weight: int = 500) -> ImageFont.FreeTypeFont:
    face = ImageFont.truetype(str(FONT_VF), size)
    face.set_variation_by_axes([weight])
    return face


def tw(draw, text: str, face) -> int:
    box = draw.textbbox((0, 0), text, font=face)
    return box[2] - box[0]


def lh(face, factor: float = 1.14) -> int:
    ascent, descent = face.getmetrics()
    return round((ascent + descent) * factor)


def wrap(draw, text: str, face, max_width: int) -> list[str]:
    lines, current = [], ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if tw(draw, candidate, face) <= max_width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def fit(draw, text: str, max_width: int, max_height: int, start: int,
        weight: int = 800, factor: float = 1.06, floor: int = 26):
    size = start
    while size > floor:
        face = font(size, weight)
        lines = wrap(draw, text, face, max_width)
        if max(tw(draw, line, face) for line in lines) <= max_width and len(lines) * lh(face, factor) <= max_height:
            return face, lines
        size -= 2
    face = font(floor, weight)
    return face, wrap(draw, text, face, max_width)


def push(draw, lines, face, x, y, fill, factor=1.06, shadow: int = 0) -> int:
    step = lh(face, factor)
    for line in lines:
        if shadow:
            for dx, dy in ((shadow, shadow), (shadow, 0), (0, shadow)):
                draw.text((x + dx, y + dy), line, font=face, fill=(4, 10, 18))
        draw.text((x, y), line, font=face, fill=fill)
        y += step
    return y


def tracked(draw, text: str, face, x: int, y: int, fill, gap: int) -> int:
    for ch in text:
        draw.text((x, y), ch, font=face, fill=fill)
        x += tw(draw, ch, face) + gap
    return x


# ─── цветокоррекция ──────────────────────────────────────────────────────────


def curve(points: list[tuple[int, int]]) -> list[int]:
    """Кусочно-линейная кривая по 256 точкам."""
    lut = []
    for i in range(256):
        for (x0, y0), (x1, y1) in zip(points, points[1:]):
            if x0 <= i <= x1:
                t = 0 if x1 == x0 else (i - x0) / (x1 - x0)
                lut.append(round(y0 + (y1 - y0) * t))
                break
        else:
            lut.append(points[-1][1] if i > points[-1][0] else points[0][1])
    return [max(0, min(255, v)) for v in lut]


# Тени уводим в глубокий синий, света — в тёплый; средние тона чуть контрастнее
R_LUT = curve([(0, 0), (40, 30), (128, 132), (200, 214), (255, 255)])
G_LUT = curve([(0, 4), (40, 40), (128, 130), (200, 204), (255, 252)])
B_LUT = curve([(0, 26), (40, 62), (128, 138), (200, 196), (255, 240)])


def grade(image: Image.Image) -> Image.Image:
    image = image.convert("RGB")
    r, g, b = image.split()
    image = Image.merge("RGB", (r.point(R_LUT), g.point(G_LUT), b.point(B_LUT)))
    return image


def vignette(image: Image.Image, strength: float = 0.34) -> Image.Image:
    w, h = image.size
    small = Image.new("L", (w // 8, h // 8), 0)
    d = ImageDraw.Draw(small)
    d.ellipse([-w // 10, -h // 10, w // 8 + w // 10, h // 8 + h // 10], fill=255)
    mask = small.filter(ImageFilter.GaussianBlur(w // 40)).resize((w, h), Image.LANCZOS)
    dark = Image.new("RGB", (w, h), (2, 8, 16))
    return Image.composite(image, Image.blend(image, dark, strength), mask)


def text_scrim(image: Image.Image, side: str = "left", strength: int = 238) -> Image.Image:
    """Плотная шторка под текст: слева для десктопа, сверху для мобильного."""
    w, h = image.size
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    if side == "left":
        band = int(w * 0.62)
        for x in range(band):
            t = 1 - x / band
            d.rectangle([x, 0, x + 1, h], fill=(6, 15, 27, int(strength * t ** 1.5)))
        # общее лёгкое затемнение, чтобы свет не бил в глаза
        d.rectangle([0, 0, w, h], fill=(6, 15, 27, 26))
    else:
        band = int(h * 0.78)
        for y in range(band):
            t = 1 - y / band
            d.rectangle([0, y, w, y + 1], fill=(6, 15, 27, int(strength * t ** 1.1)))
        d.rectangle([0, 0, w, h], fill=(6, 15, 27, 30))
    layer = layer.filter(ImageFilter.GaussianBlur(round(min(w, h) * 0.012)))
    return Image.alpha_composite(image.convert("RGBA"), layer).convert("RGB")


def cover_crop(image: Image.Image, size: tuple[int, int], focus=(0.5, 0.5),
               sharpen: bool = False) -> Image.Image:
    """Кроп по размеру кадра (не по размеру пикселей), потом ресайз в точный размер."""
    w, h = size
    target_ratio = w / h
    src_ratio = image.width / image.height
    if src_ratio > target_ratio:
        new_w = round(image.height * target_ratio)
        left = round((image.width - new_w) * focus[0])
        box = (left, 0, left + new_w, image.height)
    else:
        new_h = round(image.width / target_ratio)
        top = round((image.height - new_h) * focus[1])
        box = (0, top, image.width, top + new_h)

    cropped = image.crop(box)
    resized = cropped.resize((w, h), Image.Resampling.LANCZOS)
    if sharpen and w > cropped.width:
        # лёгкая резкость после апскейла — иначе фон выглядит мылом
        resized = resized.filter(ImageFilter.UnsharpMask(radius=1.6, percent=70, threshold=3))
    return resized


# ─── типографика обложки ─────────────────────────────────────────────────────


TITLE = "Оформление\nмероприятий\nи праздников"
KICKER = "СЕЗОН 2027"
SUB = "Декорации, сцены, фотозоны\nи бренд-зоны под ключ"
PROOF = "Своё производство  \u00b7  Москва и Санкт-Петербург  \u00b7  Монтаж 24/7"


def lockup(draw, x: int, y: int, size: int, accent=CORAL, fill=WHITE) -> int:
    rule = max(3, round(size * 0.15))
    draw.rectangle([x, y, x + round(size * 3.4), y + rule], fill=accent)
    face = font(size, 750)
    draw.text((x, y + rule + round(size * 0.5)), "SM PRODUCTION", font=face, fill=fill)
    return rule + round(size * 0.5) + lh(face, 1.0)


def compose_desktop(image: Image.Image, with_text: bool) -> Image.Image:
    w, h = image.size
    img = text_scrim(vignette(grade(image), 0.30), "left", 232)
    if not with_text:
        return text_scrim(vignette(grade(image), 0.30), "left", 120)

    draw = ImageDraw.Draw(img)
    m = round(w * 0.072)
    top = round(h * 0.13)

    lock_h = lockup(draw, m, top, round(h * 0.0125))

    kicker_face = font(round(h * 0.0165), 700)
    ky = top + lock_h + round(h * 0.085)
    tracked(draw, KICKER, kicker_face, m, ky, CORAL, round(w * 0.0026))

    title_face, title_lines = fit(draw, TITLE.replace("\n", " "), round(w * 0.40),
                                  round(h * 0.34), round(h * 0.088), factor=1.04, floor=40)
    # держим авторскую разбивку на строки
    manual = TITLE.split("\n")
    widest = max(tw(draw, line, title_face) for line in manual)
    while widest > round(w * 0.42) and title_face.size > 40:
        title_face = font(title_face.size - 2, 800)
        widest = max(tw(draw, line, title_face) for line in manual)

    ty = ky + lh(kicker_face, 1.0) + round(h * 0.030)
    ty = push(draw, manual, title_face, m, ty, WHITE, 1.04)

    sub_face = font(round(h * 0.0225), 520)
    sy = ty + round(h * 0.028)
    push(draw, SUB.split("\n"), sub_face, m, sy, (222, 230, 240), 1.2, shadow=1)

    proof_face = font(round(h * 0.0155), 600)
    py = h - round(h * 0.105)
    draw.rectangle([m, py - round(h * 0.026), m + round(w * 0.020), py - round(h * 0.026) + max(3, round(h * 0.003))], fill=CORAL)
    draw.text((m, py), PROOF, font=proof_face, fill=DIM)
    return img


def compose_mobile(image: Image.Image, with_text: bool) -> Image.Image:
    w, h = image.size
    img = text_scrim(vignette(grade(image), 0.32), "top", 250)
    if not with_text:
        return text_scrim(vignette(grade(image), 0.32), "top", 110)

    draw = ImageDraw.Draw(img)
    m = round(w * 0.088)
    top = round(h * 0.085)

    lock_h = lockup(draw, m, top, round(w * 0.0155))
    kicker_face = font(round(w * 0.024), 700)
    ky = top + lock_h + round(h * 0.038)
    tracked(draw, KICKER, kicker_face, m, ky, CORAL, round(w * 0.004))

    title_face = font(round(w * 0.083), 800)
    manual = TITLE.split("\n")
    while max(tw(draw, line, title_face) for line in manual) > w - m * 2 and title_face.size > 28:
        title_face = font(title_face.size - 2, 800)

    ty = ky + lh(kicker_face, 1.0) + round(h * 0.022)
    ty = push(draw, manual, title_face, m, ty, WHITE, 1.04)

    sub_face = font(round(w * 0.036), 550)
    sy = ty + round(h * 0.022)
    push(draw, ["Декорации, сцены, фотозоны", "и бренд-зоны под ключ"], sub_face, m, sy,
         (238, 243, 249), 1.2, shadow=2)

    proof_face = font(round(w * 0.028), 600)
    py = h - round(h * 0.062)
    draw.text((m, py), "Москва и Санкт-Петербург", font=proof_face, fill=DIM)
    return img


def save(image: Image.Image, name: str, max_kb: int) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    q = 90
    while True:
        image.save(path, format="JPEG", quality=q, optimize=True, progressive=True)
        kb = path.stat().st_size // 1024
        if kb <= max_kb or q <= 66:
            print(f"  {name:38} {image.width}×{image.height}  {kb} КБ")
            return
        q -= 3


def main() -> int:
    desk = Image.open(SRC / "scene-v2-big.jpg").convert("RGB")
    mob_src = Image.open(SRC / "scene-v2-mobile.jpg").convert("RGB")

    # приводим сцены к точным целевым размерам до наложения текста
    desk_wide = cover_crop(desk, (2560, 1440), (0.5, 0.45))
    mob = cover_crop(mob_src, (1080, 1920), (0.5, 0.42), sharpen=True)

    wide = compose_desktop(desk_wide, True)
    save(wide, "cover-desktop-text-2560x1440.jpg", 480)
    save(wide.resize((1920, 1080), Image.LANCZOS), "cover-desktop-text-1920x1080.jpg", 320)

    clean = compose_desktop(desk_wide, False)
    save(clean, "cover-desktop-clean-2560x1440.jpg", 460)
    save(clean.resize((1920, 1080), Image.LANCZOS), "cover-desktop-clean-1920x1080.jpg", 300)

    mtext = compose_mobile(mob, True)
    save(mtext, "cover-mobile-text-1080x1920.jpg", 300)
    save(compose_mobile(mob, False), "cover-mobile-clean-1080x1920.jpg", 280)

    # OG: 1200×630 из десктопной обложки, кроп по левой части с заголовком
    og = cover_crop(wide, (1200, 630), (0.0, 0.5))
    save(og, "og-1200x630.jpg", 165)

    # контактный лист
    tiles = [
        (wide, "десктоп с текстом"),
        (clean, "десктоп без текста"),
        (mtext, "мобильный с текстом"),
        (compose_mobile(mob, False), "мобильный без текста"),
    ]
    pad, ch = 26, 560
    widths = [round(t[0].width * (ch / t[0].height)) for t in tiles]
    W = sum(widths) + pad * (len(tiles) + 1)
    H = ch + 106
    sheet = Image.new("RGB", (W, H), (14, 18, 25))
    d = ImageDraw.Draw(sheet)
    d.rectangle([0, 0, W, 6], fill=CORAL)
    d.text((pad, 24), "Обложка первого экрана — итог", font=font(30, 800), fill=WHITE)
    x = pad
    for (img, label), wdt in zip(tiles, widths):
        thumb = img.resize((wdt, ch), Image.LANCZOS)
        sheet.paste(thumb, (x, 74))
        d.text((x + 2, ch + 80), label, font=font(17, 600), fill=(200, 209, 220))
        x += wdt + pad
    sheet.save(OUT / "preview.jpg", quality=90, optimize=True)
    print(f"  preview.jpg                            {sheet.width}×{sheet.height}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
