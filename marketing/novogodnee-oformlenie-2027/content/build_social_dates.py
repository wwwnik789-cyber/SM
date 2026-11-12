#!/usr/bin/env python3
"""Карточка сроков к посту «Открыт сезон новогоднего оформления».

Отличие от `build_social_sroki.py`: там обложка с фотографией и одним
обещанием, здесь — вторая карточка серии, чисто информационная: две даты
крупными цифрами и две недели между ними. В ленте она читается без
разглядывания и годится вторым слайдом карусели или отдельной публикацией
в Telegram, где фотографическая обложка уже была.

Цифры берутся из текста поста:
  заявки на гарантированный монтаж — до 1 декабря;
  сам монтаж — до 30 декабря;
  цикл от заявки до готовой конструкции — около двух недель.

Запуск из корня репозитория:
    .venv/bin/python marketing/novogodnee-oformlenie-2027/content/build_social_dates.py
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
    cover,
    font,
    lh,
    lockup,
    photo,
    push_text,
    spaced,
    tw,
    wrap,
)

LOCKUP = "SM PRODUCTION"
KICKER = "НОВОГОДНЕЕ ОФОРМЛЕНИЕ · СЕЗОН 2027"

ROWS = [
    ("01.12", "последний день заявок"),
    ("30.12", "последний монтаж в графике"),
]

LEAD = "≈ 2 недели от заявки до готовой конструкции"
NOTE = "В ноябре график спокойный. В декабре — срочное производство и ограниченный выбор."
FOOTER = "Москва и Московская область · производство 750 м² · монтаж 24/7"


def fit_size(draw, text: str, weight: int, start: int, max_width: int, floor: int = 20) -> int:
    size = start
    while size > floor and tw(draw, text, font(size, weight)) > max_width:
        size -= 1
    return size


def build(size: tuple[int, int], *, photo_share: float, show_note: bool) -> Image.Image:
    w, h = size
    m = round(w * 0.06)
    inner_w = w - m * 2
    photo_h = round(h * photo_share)

    canvas = Image.new("RGB", size, NAVY)
    canvas.paste(cover(photo("lobby"), (w, photo_h), (0.58, 0.46)), (0, 0))

    # мягкий переход от фото к панели, чтобы стык не был линейкой
    grad_h = round(h * 0.055)
    strip = canvas.crop((0, photo_h - grad_h, w, photo_h)).convert("RGBA")
    for i in range(grad_h):
        alpha = int(255 * (i / grad_h) ** 1.35)
        ImageDraw.Draw(strip).rectangle([0, i, w, i + 1], fill=NAVY + (alpha,))
    canvas.paste(strip.convert("RGB"), (0, photo_h - grad_h))

    draw = ImageDraw.Draw(canvas)

    # ── шапка
    lock_top = photo_h + round(h * 0.035)
    lock_h = lockup(draw, m, lock_top, round(h * 0.017))
    kicker_face = font(round(h * 0.0155), 700)
    ky = lock_top + lock_h + round(h * 0.024)
    spaced(draw, KICKER, kicker_face, m, ky, CORAL, round(h * 0.0026))

    # ── две даты
    date_size = round(h * 0.095)
    label_face = font(round(h * 0.0205), 500)
    label_gap = round(h * 0.010)
    row_gap = round(h * 0.018)
    rows_top = ky + lh(kicker_face, 1.0) + round(h * 0.028)

    date_face = font(date_size, 800)
    row_step = lh(date_face, 0.92) + label_gap + lh(label_face, 1.0) + row_gap
    for index, (date, label) in enumerate(ROWS):
        row_y = rows_top + index * row_step
        draw.text((m, row_y), date, font=date_face, fill=WHITE if index else WHITE)
        label_y = row_y + lh(date_face, 0.92) + label_gap
        draw.text((m, label_y), label, font=label_face, fill=MUTED)
        # коралловая черта справа от даты — выравнивает блок по вертикали
        line_y = row_y + round(date_size * 0.52)
        line_x = m + tw(draw, date, date_face) + round(w * 0.035)
        draw.rectangle([line_x, line_y, w - m, line_y + max(2, round(h * 0.0022))], fill=(26, 52, 78))

    last_row_bottom = rows_top + (len(ROWS) - 1) * row_step + lh(date_face, 0.92) + label_gap + lh(label_face, 1.0)

    # ── обещание
    rule_y = last_row_bottom + round(h * 0.034)
    draw.rectangle([m, rule_y, m + round(w * 0.062), rule_y + max(3, round(h * 0.004))], fill=CORAL)

    lead_face = font(round(h * 0.0295), 750)
    while tw(draw, LEAD, lead_face) > inner_w and lead_face.size > 16:
        lead_face = font(lead_face.size - 1, 750)
    lead_y = rule_y + round(h * 0.028)
    draw.text((m, lead_y), LEAD, font=lead_face, fill=CORAL)
    cursor = lead_y + lh(lead_face, 1.0)

    # ── пояснение и подпись
    footer_face = font(round(h * 0.0165), 500)
    footer_lines = wrap(draw, FOOTER, footer_face, inner_w)
    footer_step = lh(footer_face, 1.2)
    footer_y = h - round(h * 0.042) - len(footer_lines) * footer_step

    if show_note:
        note_face = font(round(h * 0.0195), 500)
        note_lines = wrap(draw, NOTE, note_face, inner_w)
        note_step = lh(note_face, 1.22)
        note_y = footer_y - round(h * 0.045) - len(note_lines) * note_step
        assert cursor + round(h * 0.02) <= note_y, f"текст наезжает на пояснение: {cursor} → {note_y}"
        push_text(draw, note_lines, note_face, m, note_y, MUTED, 1.22)
    else:
        assert cursor + round(h * 0.03) <= footer_y, f"текст наезжает на подпись: {cursor} → {footer_y}"

    for i, line in enumerate(footer_lines):
        draw.text((m, footer_y + i * footer_step), line, font=footer_face, fill=DIM)
    return canvas


def save(image: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format="JPEG", quality=90, optimize=True, progressive=True)
    print(f"{path.relative_to(OUT.parents[3])}  {image.width}×{image.height}  "
          f"{path.stat().st_size // 1024} КБ")


def main() -> int:
    save(build((1080, 1350), photo_share=0.26, show_note=True),
         OUT / "social" / "1080x1350" / "sroki-02-daty-4x5.jpg")
    save(build((1080, 1080), photo_share=0.30, show_note=False),
         OUT / "social" / "1080x1080" / "sroki-02-daty-1x1.jpg")
    return 0


if __name__ == "__main__":
    sys.exit(main())
