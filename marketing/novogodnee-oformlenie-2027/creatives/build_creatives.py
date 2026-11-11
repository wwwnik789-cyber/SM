#!/usr/bin/env python3
"""Build New Year 2027 ad creatives in 1080x1080 and 1920x1080."""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
SOURCE = ROOT / "source"
FONT_VF = REPO / "banners" / "anikom-arena-3000x2500-concepts" / "source" / "Montserrat-Variable.ttf"

if not FONT_VF.exists():
    raise SystemExit(f"Не найден шрифт: {FONT_VF}")

NAVY = (8, 26, 43)
NAVY_SOFT = (13, 34, 56)
CORAL = (217, 74, 67)
WHITE = (255, 255, 255)
MUTED = (176, 188, 202)

SCENES = [
    {
        "slug": "01-office",
        "image": "lobby.jpg",
        "kicker": "СЕЗОН 2027",
        "title": "Новогоднее оформление офиса",
        "sub": "Эскиз, печать, каркас, монтаж.\nРабота по брендбуку.",
        "promise": "Расчёт за 1 рабочий день",
        "note": "Москва и Московская область",
    },
    {
        "slug": "02-photozone",
        "image": "photozone.jpg",
        "kicker": "ФОТОЗОНЫ",
        "title": "Фотозона к Новому году",
        "sub": "Скрытый каркас и ровное полотно.\nСвет и объёмный декор.",
        "promise": "Монтаж за 7 дней",
        "note": "Паспорт декорации и документы",
    },
    {
        "slug": "03-corporate",
        "image": "corporate.jpg",
        "kicker": "КОРПОРАТИВЫ",
        "title": "Оформление новогоднего события",
        "sub": "Сцена, фотозона и навигация.\nДежурство технической группы.",
        "promise": "Монтаж в ночное окно",
        "note": "Москва и Московская область",
    },
    {
        "slug": "04-art",
        "image": "art.jpg",
        "kicker": "АРТ-ОБЪЕКТЫ",
        "title": "Ёлка как арт-объект",
        "sub": "Каркас, подсветка, брендинг.\nЛюбой размер и форма.",
        "promise": "Улица и интерьер",
        "note": "Своё производство 750 м²",
    },
]


def font(size: int, weight: int) -> ImageFont.FreeTypeFont:
    face = ImageFont.truetype(str(FONT_VF), size)
    face.set_variation_by_axes([weight])
    return face


def text_width(draw: ImageDraw.ImageDraw, text: str, face) -> int:
    box = draw.textbbox((0, 0), text, font=face)
    return box[2] - box[0]


def line_height(face, factor: float = 1.18) -> int:
    ascent, descent = face.getmetrics()
    return round((ascent + descent) * factor)


def wrap(draw, text: str, face, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if text_width(draw, candidate, face) <= max_width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def fit_title(draw, text: str, max_width: int, max_height: int, start: int) -> tuple[object, list[str]]:
    size = start
    while size > 24:
        face = font(size, 800)
        lines = wrap(draw, text, face, max_width)
        height = len(lines) * line_height(face, 1.06)
        widest = max(text_width(draw, line, face) for line in lines)
        if widest <= max_width and height <= max_height:
            return face, lines
        size -= 2
    face = font(24, 800)
    return face, wrap(draw, text, face, max_width)


def cover(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    target_w, target_h = size
    scale = max(target_w / image.width, target_h / image.height)
    resized = image.resize(
        (round(image.width * scale), round(image.height * scale)),
        Image.Resampling.LANCZOS,
    )
    left = (resized.width - target_w) // 2
    top = (resized.height - target_h) // 2
    return resized.crop((left, top, left + target_w, top + target_h))


def build(scene: dict, size: tuple[int, int], panel_ratio: float, out_path: Path) -> None:
    width, height = size
    photo = cover(Image.open(SOURCE / scene["image"]).convert("RGB"), size)

    # Right edge of the photo fades into the panel colour so the seam is soft.
    fade = Image.new("L", (width, height), 0)
    fade_draw = ImageDraw.Draw(fade)
    panel_w = round(width * panel_ratio)
    fade_start = panel_w
    fade_end = panel_w + round(width * 0.06)
    for x in range(fade_start, min(fade_end, width)):
        t = (x - fade_start) / max(1, fade_end - fade_start)
        fade_draw.line([(x, 0), (x, height)], fill=int(255 * (1 - t)))
    tint = Image.new("RGB", (width, height), NAVY)
    photo.paste(tint, (0, 0), fade)

    canvas = photo
    draw = ImageDraw.Draw(canvas)

    # Solid panel
    draw.rectangle([0, 0, panel_w, height], fill=NAVY)
    draw.rectangle([panel_w - 6, 0, panel_w, height], fill=CORAL)

    margin = round(panel_w * 0.115)
    inner_w = panel_w - margin * 2

    # Header
    bar_y = round(height * 0.075)
    draw.rectangle([margin, bar_y, margin + round(inner_w * 0.22), bar_y + max(4, round(height * 0.004))], fill=CORAL)
    header = font(round(height * 0.021), 750)
    draw.text((margin, bar_y + round(height * 0.022)), "SM PRODUCTION", font=header, fill=WHITE)

    # Bottom block anchored to the bottom, no price anymore
    note_face = font(round(height * 0.019), 500)
    sub_face = font(round(height * 0.027), 500)
    kicker_face = font(round(height * 0.021), 700)
    promise_face = font(round(height * 0.034), 750)

    bottom = height - round(height * 0.085)

    note_h = line_height(note_face, 1.2)
    note_y = bottom - note_h

    promise_h = line_height(promise_face, 1.0)
    promise_y = note_y - round(height * 0.032) - promise_h

    rule_y = promise_y - round(height * 0.026)
    rule_w = round(height * 0.062)

    sub_lines = scene["sub"].split("\n")
    sub_line_h = line_height(sub_face, 1.12)
    sub_block_h = len(sub_lines) * sub_line_h
    sub_bottom = rule_y - round(height * 0.03)
    sub_top = sub_bottom - sub_block_h

    kicker_h = line_height(kicker_face, 1.0)
    kicker_y = sub_top - round(height * 0.035) - kicker_h

    # Title fills the space between header and kicker
    title_top = bar_y + round(height * 0.10)
    title_max_h = kicker_y - round(height * 0.025) - title_top
    title_face, title_lines = fit_title(
        draw, scene["title"], inner_w, max(title_max_h, 60), round(height * 0.088)
    )
    title_line_h = line_height(title_face, 1.05)
    title_block_h = len(title_lines) * title_line_h
    title_y = kicker_y - round(height * 0.025) - title_block_h

    if title_y < title_top:
        title_y = title_top

    draw.text((margin, kicker_y), scene["kicker"], font=kicker_face, fill=CORAL)

    cursor = title_y
    for line in title_lines:
        draw.text((margin, cursor), line, font=title_face, fill=WHITE)
        cursor += title_line_h

    # Shrink the sub-copy until every line fits inside the text column.
    while any(text_width(draw, line, sub_face) > inner_w for line in sub_lines) and sub_face.size > 11:
        sub_face = font(sub_face.size - 1, 500)
        sub_line_h = line_height(sub_face, 1.12)
        sub_block_h = len(sub_lines) * sub_line_h
        sub_top = sub_bottom - sub_block_h

    cursor = sub_top
    for line in sub_lines:
        draw.text((margin, cursor), line, font=sub_face, fill=MUTED)
        cursor += sub_line_h

    # Accent rule + promise instead of a price chip
    draw.rectangle([margin, rule_y, margin + rule_w, rule_y + max(3, round(height * 0.005))], fill=CORAL)
    while text_width(draw, scene["promise"], promise_face) > inner_w and promise_face.size > 12:
        promise_face = font(promise_face.size - 1, 750)
    draw.text((margin, promise_y), scene["promise"], font=promise_face, fill=CORAL)
    draw.text((margin, note_y), scene["note"], font=note_face, fill=(138, 152, 168))

    canvas.save(out_path, quality=94)


def main() -> int:
    built = 0
    for scene in SCENES:
        for suffix, size, ratio in (
            ("1x1", (1080, 1080), 0.52),
            ("16x9", (1920, 1080), 0.44),
        ):
            out = ROOT / f"{scene['slug']}-{suffix}.jpg"
            build(scene, size, ratio, out)
            print(f"{out.name}: {out.stat().st_size // 1024} КБ")
            built += 1
    print(f"Готово креативов: {built}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
