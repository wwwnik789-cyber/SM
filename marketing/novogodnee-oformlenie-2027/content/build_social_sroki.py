#!/usr/bin/env python3
"""Обложка к посту о сроках сезона 2027: «Успеть до 30 декабря».

Три файла под одну публикацию:
  images/social/1080x1350/sroki-01-dekabrya-4x5.jpg   ВК, лента
  images/social/1080x1080/sroki-01-dekabrya-1x1.jpg   Telegram, кросс-пост
  images/stories/sroki-01-dekabrya-1080x1920.jpg      сторис, вертикаль

Все цифры — из текста поста: заявки до 1 декабря, гарантированный монтаж
до 30 декабря, около двух недель от заявки до готовой конструкции.

Запуск из корня репозитория:
    .venv/bin/python marketing/novogodnee-oformlenie-2027/content/build_social_sroki.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw

from build_images import (  # type: ignore[import-not-found]
    CORAL,
    DIM,
    MUTED,
    NAVY,
    OUT,
    WHITE,
    card_photo,
    cover,
    fit,
    font,
    lh,
    lockup,
    photo,
    push_text,
    spaced,
    tw,
    wrap,
)

KICKER = "Новогоднее оформление · сезон 2027"
TITLE = "Успеть до 30 декабря"
SUB = (
    "Около двух недель от заявки до готовой конструкции.\n"
    "В ноябре график спокойный, в декабре — срочное производство "
    "и ограниченный выбор."
)
PROMISE = "Заявки — до 1 декабря"
NOTE = "Москва и Московская область · своё производство 750 м² · монтаж 24/7"
NOTE_STORY = "Москва и МО · производство 750 м² · монтаж 24/7"


def story_deadline() -> Image.Image:
    """1080×1920: фото офиса, дата последнего дня заявок и обещание по монтажу."""
    w, h = 1080, 1920
    m = round(w * 0.075)
    inner_w = w - m * 2
    photo_h = round(h * 0.345)
    gap = round(h * 0.024)

    canvas = Image.new("RGB", (w, h), NAVY)
    canvas.paste(cover(photo("lobby"), (w, photo_h), (0.55, 0.50)), (0, 0))

    # мягкий переход от фото к панели
    grad_h = round(h * 0.075)
    strip = canvas.crop((0, photo_h - grad_h, w, photo_h)).convert("RGBA")
    for i in range(grad_h):
        alpha = int(255 * (i / grad_h) ** 1.35)
        ImageDraw.Draw(strip).rectangle([0, i, w, i + 1], fill=NAVY + (alpha,))
    canvas.paste(strip.convert("RGB"), (0, photo_h - grad_h))

    draw = ImageDraw.Draw(canvas)

    lock_h = lockup(draw, m, photo_h + round(h * 0.026), round(h * 0.0155))
    kicker_face = font(round(h * 0.0155), 700)
    ky = photo_h + round(h * 0.026) + lock_h + round(h * 0.022)
    spaced(draw, "СЕЗОН 2027", kicker_face, m, ky, CORAL, round(h * 0.0032))

    label_face = font(round(h * 0.0175), 600)
    ly = ky + lh(kicker_face, 1.0) + round(h * 0.022)
    spaced(draw, "ПОСЛЕДНИЙ ДЕНЬ ЗАЯВОК", label_face, m, ly, MUTED, round(h * 0.003))

    # ── «01 ДЕКАБРЯ» в одну строку, выровнено по нижнему краю
    day_face = font(round(h * 0.090), 800)
    month_face = font(round(h * 0.0625), 750)
    dy = ly + lh(label_face, 1.0) + round(h * 0.014)
    day_box = draw.textbbox((0, 0), "01", font=day_face)
    month_box = draw.textbbox((0, 0), "ДЕКАБРЯ", font=month_face)
    draw.text((m - round(w * 0.004), dy), "01", font=day_face, fill=WHITE)
    month_x = m + (day_box[2] - day_box[0]) + round(w * 0.028)
    draw.text((month_x, dy + day_box[3] - month_box[3]), "ДЕКАБРЯ", font=month_face, fill=CORAL)
    assert month_x + (month_box[2] - month_box[0]) <= w - m, "дата не влезает в поля"

    rule_y = dy + day_box[3] + round(h * 0.022)
    draw.rectangle([m, rule_y, m + round(w * 0.075), rule_y + max(4, round(h * 0.0035))], fill=CORAL)

    promise_face, promise_lines = fit(
        draw, "Гарантированный монтаж до 30 декабря", inner_w, round(h * 0.115),
        round(h * 0.034), weight=750, factor=1.14, floor=40,
    )
    py = rule_y + round(h * 0.022)
    py = push_text(draw, promise_lines, promise_face, m, py, WHITE, 1.14)

    cta_face = font(round(h * 0.0215), 600)
    cta_lines = ["Напишите дату монтажа —", "зафиксируем окно."]
    cy = py + round(h * 0.020)
    cy = push_text(draw, cta_lines, cta_face, m, cy, CORAL, 1.24)

    note_face = font(round(h * 0.0175), 500)
    note_lines = wrap(draw, NOTE_STORY, note_face, inner_w)
    note_step = lh(note_face, 1.2)
    ny = h - round(h * 0.145) - len(note_lines) * note_step
    assert cy + round(h * 0.014) <= ny, f"сторис: контент наезжает на подпись ({cy} → {ny})"
    assert ny + len(note_lines) * note_step <= h - round(h * 0.13), "подпись в зоне интерфейса"
    for i, line in enumerate(note_lines):
        draw.text((m, ny + i * note_step), line, font=note_face, fill=DIM)

    return canvas


def square_cover() -> Image.Image:
    """1080×1080: без подзаголовка, только два срока — формат читают в ленте."""
    return card_photo(
        (1080, 1080),
        0.50,
        "lobby",
        KICKER,
        TITLE,
        "Около двух недель от заявки до готовой конструкции.",
        PROMISE,
        "Москва и МО · производство 750 м² · монтаж 24/7",
        focus=(0.55, 0.50),
    )


def main() -> int:
    made: list[tuple[Path, str]] = []

    wide = card_photo(
        (1080, 1350),
        0.46,
        "lobby",
        KICKER,
        TITLE,
        SUB,
        PROMISE,
        NOTE,
        focus=(0.55, 0.50),
    )
    p = OUT / "social" / "1080x1350" / "sroki-01-dekabrya-4x5.jpg"
    p.parent.mkdir(parents=True, exist_ok=True)
    wide.save(p, format="JPEG", quality=90, optimize=True, progressive=True)
    made.append((p, "4:5"))

    p = OUT / "social" / "1080x1080" / "sroki-01-dekabrya-1x1.jpg"
    p.parent.mkdir(parents=True, exist_ok=True)
    square_cover().save(p, format="JPEG", quality=90, optimize=True, progressive=True)
    made.append((p, "1:1"))

    p = OUT / "stories" / "sroki-01-dekabrya-1080x1920.jpg"
    p.parent.mkdir(parents=True, exist_ok=True)
    story_deadline().save(p, format="JPEG", quality=90, optimize=True, progressive=True)
    made.append((p, "9:16"))

    for path, label in made:
        with Image.open(path) as img:
            print(f"{path.relative_to(OUT.parents[3])}  {label}  {img.width}×{img.height}"
                  f"  {path.stat().st_size // 1024} КБ")
    return 0


if __name__ == "__main__":
    sys.exit(main())
