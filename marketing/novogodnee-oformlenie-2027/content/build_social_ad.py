#!/usr/bin/env python3
"""Рекламная картинка к посту об открытии сезона — с текстом.

Основа — сгенерированный кадр оформленного зала: белая панель с резными
снежинками, световое дерево, тёмный потолок с лучами света. Верхние две
пятых кадра уходят под тёмную плашку: там стоит весь текст, фотография
остаётся видимой полностью.

Что на макете (всё — из текста поста):
  СЕЗОН 2027 · НОВОГОДНЕЕ ОФОРМЛЕНИЕ
  Успеть до 30 декабря
  Заявки — до 1 декабря
  ≈ 2 недели от заявки до готовой конструкции
  +7 (495) 799-00-19 · sm-production.ru

Запуск из корня репозитория:
    .venv/bin/python marketing/novogodnee-oformlenie-2027/content/build_social_ad.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
FONT_VF = REPO / "banners" / "anikom-arena-3000x2500-concepts" / "source" / "Montserrat-Variable.ttf"
SOURCE = HERE / "images" / "generated" / "ny-post-hero-4x5.jpg"
OUT = HERE / "images" / "generated"

NAVY = (8, 26, 43)
CORAL = (217, 74, 67)
WHITE = (255, 255, 255)
MUTED = (176, 190, 206)
DIM = (124, 142, 160)

KICKER = "НОВОГОДНЕЕ ОФОРМЛЕНИЕ · СЕЗОН 2027"
TITLE = "Успеть до 30 декабря"
PROMISE = "Заявки — до 1 декабря"
NOTE = "≈ 2 недели от заявки до готовой конструкции"
CONTACT = "+7 (495) 799-00-19"

FORMATS = [
    ("ny-ad-post-4x5.jpg", (1080, 1350), 0.50, 84, (0.50, 0.55)),
    ("ny-ad-post-1x1.jpg", (1080, 1080), 0.545, 78, (0.50, 0.50)),
    ("ny-ad-story-9x16.jpg", (1080, 1920), 0.44, 92, (0.72, 0.50)),
]


def font(size: int, weight: int = 500) -> ImageFont.FreeTypeFont:
    face = ImageFont.truetype(str(FONT_VF), size)
    face.set_variation_by_axes([weight])
    return face


def tw(draw: ImageDraw.ImageDraw, text: str, face) -> int:
    box = draw.textbbox((0, 0), text, font=face)
    return box[2] - box[0]


def lh(face, factor: float = 1.16) -> int:
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


def cover(image: Image.Image, size: tuple[int, int], focus: tuple[float, float] = (0.5, 0.5)) -> Image.Image:
    w, h = size
    scale = max(w / image.width, h / image.height)
    resized = image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS)
    left = round((resized.width - w) * focus[0])
    top = round((resized.height - h) * focus[1])
    left = max(0, min(left, resized.width - w))
    top = max(0, min(top, resized.height - h))
    return resized.crop((left, top, left + w, top + h))


def spaced(draw, text: str, face, x: int, y: int, fill, gap: int) -> int:
    for char in text:
        draw.text((x, y), char, font=face, fill=fill)
        x += tw(draw, char, face) + gap
    return x


def lockup(draw, x: int, y: int, size: int) -> int:
    rule_h = max(3, round(size * 0.13))
    draw.rectangle([x, y, x + round(size * 3.1), y + rule_h], fill=CORAL)
    face = font(size, 750)
    draw.text((x, y + rule_h + round(size * 0.55)), "SM PRODUCTION", font=face, fill=WHITE)
    return rule_h + round(size * 0.55) + lh(face, 1.0)


def build(size: tuple[int, int], panel: float, title_size: int, focus: tuple[float, float]) -> Image.Image:
    w, h = size
    m = round(w * 0.062)
    inner_w = w - m * 2
    panel_h = round(h * panel)

    canvas = cover(Image.open(SOURCE).convert("RGB"), size, focus)

    # ── тёмная плашка сверху: текст должен читаться, не споря с фотографией
    fade = round(h * 0.10)
    scrim_h = min(h, panel_h + fade)
    scrim = Image.new("RGBA", (w, h), NAVY + (0,))
    sd = ImageDraw.Draw(scrim)
    for y in range(scrim_h):
        alpha = 255 if y < panel_h else round(255 * (1 - (y - panel_h) / fade) ** 1.4)
        sd.rectangle([0, y, w, y + 1], fill=NAVY + (alpha,))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), scrim).convert("RGB")

    draw = ImageDraw.Draw(canvas)

    # ── нижний блок собираем снизу вверх, чтобы текст не наехал на фото
    contact_face = font(round(h * 0.0215), 700)
    site_face = font(round(h * 0.0165), 500)
    contact_y = panel_h - round(h * 0.030) - lh(contact_face, 1.0)
    site_y = contact_y - round(h * 0.012) - lh(site_face, 1.0)

    note_face = font(round(h * 0.0175), 500)
    note_lines = wrap(draw, NOTE, note_face, inner_w)
    note_step = lh(note_face, 1.2)
    note_y = site_y - round(h * 0.022) - len(note_lines) * note_step

    promise_face = font(round(h * 0.029), 750)
    while tw(draw, PROMISE, promise_face) > inner_w and promise_face.size > 20:
        promise_face = font(promise_face.size - 1, 750)
    promise_y = note_y - round(h * 0.016) - lh(promise_face, 1.0)
    rule_y = promise_y - round(h * 0.020)

    # ── заголовок занимает всё, что осталось сверху
    top = m
    lock_h = lockup(draw, m, top, round(h * 0.0175))
    kicker_face = font(round(h * 0.0155), 700)
    kicker_y = top + lock_h + round(h * 0.030)
    spaced(draw, KICKER, kicker_face, m, kicker_y, CORAL, round(h * 0.0024))

    title_top = kicker_y + lh(kicker_face, 1.0) + round(h * 0.026)
    room = rule_y - round(h * 0.028) - title_top
    size_px = title_size
    while size_px > 30:
        face = font(size_px, 800)
        lines = wrap(draw, TITLE, face, inner_w)
        if len(lines) * lh(face, 1.06) <= room and max(tw(draw, l, face) for l in lines) <= inner_w:
            break
        size_px -= 2
    face = font(size_px, 800)
    lines = wrap(draw, TITLE, face, inner_w)
    assert len(lines) * lh(face, 1.06) <= room, f"заголовок не влезает: {size_px}"

    y = title_top
    for line in lines:
        draw.text((m, y), line, font=face, fill=WHITE)
        y += lh(face, 1.06)

    draw.rectangle([m, rule_y, m + round(w * 0.075), rule_y + max(3, round(h * 0.0035))], fill=CORAL)
    draw.text((m, promise_y), PROMISE, font=promise_face, fill=CORAL)
    for i, line in enumerate(note_lines):
        draw.text((m, note_y + i * note_step), line, font=note_face, fill=MUTED)

    draw.text((m, contact_y), CONTACT, font=contact_face, fill=WHITE)
    draw.text((w - m, contact_y + round(h * 0.004)), "sm-production.ru", font=site_face, fill=DIM, anchor="ra")

    assert y <= rule_y, f"заголовок наезжает на обещание: {y} → {rule_y}"
    return canvas


def main() -> int:
    if not SOURCE.exists():
        print(f"Нет исходника: {SOURCE}")
        return 1
    OUT.mkdir(parents=True, exist_ok=True)
    for name, size, panel, title_size, focus in FORMATS:
        image = build(size, panel, title_size, focus)
        path = OUT / name
        image.save(path, format="JPEG", quality=93, optimize=True, progressive=True)
        print(f"{path.relative_to(HERE)}: {size[0]}×{size[1]}, {path.stat().st_size // 1024} КБ")
    return 0


if __name__ == "__main__":
    sys.exit(main())
