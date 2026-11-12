#!/usr/bin/env python3
"""Креативы 240 × 400 под запросы про корпоративы, сцену, зал и конференции.

Четыре файла, каждый меньше 120 КБ. Композиция и типографика — те же, что
в `build_240x400.py`: фото сверху, тёмно-синяя панель снизу, коралловая линия
на стыке, текст на панели. Отличие — четвёртый креатив полностью текстовый:
в узкой выдаче Директа он даёт контраст к фотографическим и часто выигрывает
по клику, потому что читается без разглядывания.

Запросы, под которые собраны креативы:

  05 — оформление новогоднего корпоратива / декор новогоднего корпоратива /
       оформление новогоднего праздника / новогоднее оформление мероприятия
  06 — оформление зала на новый год / новогодний декор для банкета
  07 — новогоднее оформление конференции
  08 — оформление сцены на новогодний корпоратив / новогоднее оформление сцены

Запуск из корня репозитория:
    .venv/bin/python marketing/novogodnee-oformlenie-2027/creatives/build_240x400_events.py
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

from PIL import Image, ImageDraw

from build_240x400 import (  # type: ignore[import-not-found]
    CORAL,
    FONT_VF,
    H,
    LIMIT_KB,
    MUTED,
    NAVY,
    OUT_DIR,
    SOURCE,
    W,
    WHITE,
    cover,
    font,
    text_width,
    wrap,
)

SCENES = [
    {
        "slug": "05-corporate-stage",
        "image": "corporate.jpg",
        "photo_h": 218,
        "kicker": "КОРПОРАТИВЫ",
        "title": "Оформление новогоднего корпоратива",
        "promise": "Монтаж в ночное окно",
        "sub": "Сцена, каше, раус, фотозона",
        "focus": (0.62, 0.42),
    },
    {
        "slug": "06-hall-banquet",
        "image": "photozone.jpg",
        "photo_h": 218,
        "kicker": "ЗАЛЫ И БАНКЕТЫ",
        "title": "Декор зала на Новый год",
        "promise": "Монтаж за 7 дней",
        "sub": "Свет, текстиль, арт-объекты",
        "focus": (0.88, 0.30),
    },
    {
        "slug": "07-conference",
        "image": "art.jpg",
        "photo_h": 218,
        "kicker": "КОНФЕРЕНЦИИ",
        "title": "Новогоднее оформление конференции",
        "promise": "Смета за 1 рабочий день",
        "sub": "Зона регистрации, сцена, навигация",
        "focus": (0.62, 0.40),
    },
]

TYPE_SCENE = {
    "slug": "08-typed-scene",
    "kicker": "СЕЗОН 2027",
    "title": "Сцена, зал, фотозона",
    "promise": "Смета за 1 рабочий день",
    "sub_lines": ["Производство 750 м² · монтаж 24/7", "Москва и Московская область"],
}


def build_photo(scene: dict) -> Image.Image:
    canvas = Image.new("RGB", (W, H), NAVY)
    draw = ImageDraw.Draw(canvas)

    photo_h = scene["photo_h"]
    photo = cover(Image.open(SOURCE / scene["image"]).convert("RGB"), (W, photo_h), scene["focus"])
    canvas.paste(photo, (0, 0))

    # мягкий переход от фото к панели
    fade_h = 34
    for offset in range(fade_h):
        y = photo_h - fade_h + offset
        alpha = int(255 * (offset / fade_h) ** 1.5)
        stripe = Image.new("RGB", (W, 1), NAVY)
        canvas.paste(stripe, (0, y), Image.new("L", (W, 1), alpha))
    draw.rectangle([0, photo_h - 2, W, photo_h], fill=CORAL)

    margin = 14
    inner_w = W - margin * 2
    cursor = photo_h + 12

    draw.text((margin, cursor), scene["kicker"], font=font(9, 700), fill=CORAL)
    cursor += 15

    size = 20
    while size > 12:
        face = font(size, 800)
        lines = wrap(draw, scene["title"], face, inner_w)
        if len(lines) <= 3 and max(text_width(draw, line, face) for line in lines) <= inner_w - 6:
            break
        size -= 1
    face = font(size, 800)
    lines = wrap(draw, scene["title"], face, inner_w)
    for line in lines:
        draw.text((margin, cursor), line, font=face, fill=WHITE)
        cursor += round(size * 1.12)

    cursor += 7
    draw.rectangle([margin, cursor, margin + 22, cursor + 2], fill=CORAL)
    cursor += 9
    promise_face = font(11, 700)
    while text_width(draw, scene["promise"], promise_face) > inner_w and promise_face.size > 8:
        promise_face = font(promise_face.size - 1, 700)
    draw.text((margin, cursor), scene["promise"], font=promise_face, fill=CORAL)
    cursor += 17

    sub_face = font(8, 500)
    for line in wrap(draw, scene["sub"], sub_face, inner_w):
        draw.text((margin, cursor), line, font=sub_face, fill=MUTED)
        cursor += 11

    if cursor > H - 34:
        raise RuntimeError(f"{scene['slug']}: текст наезжает на подпись бренда ({cursor} px)")

    brand = font(9, 750)
    brand_y = H - 22
    draw.rectangle([margin, brand_y - 3, margin + 16, brand_y - 1], fill=CORAL)
    draw.text((margin, brand_y + 4), "SM PRODUCTION", font=brand, fill=(150, 164, 180))
    draw.text((W - margin, brand_y + 5), "sm-production.ru", font=font(7, 500), fill=(96, 112, 130), anchor="ra")
    return canvas


def build_typed(scene: dict) -> Image.Image:
    """Полностью типографский креатив: без фото, только текст на тёмном поле."""
    canvas = Image.new("RGB", (W, H), NAVY)
    draw = ImageDraw.Draw(canvas)

    margin = 16
    inner_w = W - margin * 2
    top_band = 6
    brand_top = H - 40
    content_top, content_bottom = top_band + 20, brand_top - 8

    draw.rectangle([0, 0, W, top_band], fill=CORAL)
    draw.rectangle([margin - 6, margin - 6, W - margin + 6, H - margin + 6], outline=(21, 45, 70), width=1)

    # ── заголовок: максимальный кегль, который влезает в три строки
    size = 40
    while size > 20:
        face = font(size, 800)
        lines = wrap(draw, scene["title"], face, inner_w)
        if len(lines) <= 3 and max(text_width(draw, line, face) for line in lines) <= inner_w - 6:
            break
        size -= 1
    title_face = font(size, 800)
    title_lines = wrap(draw, scene["title"], title_face, inner_w)
    title_h = round(size * 1.1) * len(title_lines)

    promise_face = font(14, 700)
    while text_width(draw, scene["promise"], promise_face) > inner_w and promise_face.size > 9:
        promise_face = font(promise_face.size - 1, 700)
    promise_h = round(promise_face.size * 1.25)

    sub_face = font(10, 500)
    sub_step = 14
    sub_lines = scene["sub_lines"]
    for line in sub_lines:
        assert text_width(draw, line, sub_face) <= inner_w, f"слишком длинная строка: {line}"

    gaps = {"kicker": 26, "rule_top": 14, "rule_bottom": 16, "promise": 10}
    total = (
        round(10 * 1.2) + gaps["kicker"] + title_h + gaps["rule_top"] + 3
        + gaps["rule_bottom"] + promise_h + gaps["promise"] + sub_step * len(sub_lines)
    )

    # свободное место уходит в отступы между блоками: низ не остаётся пустым
    free = content_bottom - content_top - total
    if free > 0:
        gaps = {key: value + round(free * share) for (key, value), share in zip(
            gaps.items(), (0.22, 0.12, 0.12, 0.22, 0.14, 0.18))}
        total = (
            round(10 * 1.2) + gaps["kicker"] + title_h + gaps["rule_top"] + 3
            + gaps["rule_bottom"] + promise_h + gaps["promise"] + sub_step * len(sub_lines)
        )
    cursor = content_top + max(0, (content_bottom - content_top - total) // 2)

    draw.text((margin, cursor), scene["kicker"], font=font(10, 700), fill=CORAL)
    cursor += round(10 * 1.2) + gaps["kicker"]

    for line in title_lines:
        draw.text((margin, cursor), line, font=title_face, fill=WHITE)
        cursor += round(size * 1.1)
    cursor += gaps["rule_top"]

    draw.rectangle([margin, cursor, margin + 30, cursor + 3], fill=CORAL)
    cursor += 3 + gaps["rule_bottom"]

    draw.text((margin, cursor), scene["promise"], font=promise_face, fill=CORAL)
    cursor += promise_h + gaps["promise"]
    for line in sub_lines:
        draw.text((margin, cursor), line, font=sub_face, fill=MUTED)
        cursor += sub_step

    assert cursor <= brand_top, f"{scene['slug']}: текст наезжает на подпись бренда"

    brand_y = H - 24
    draw.rectangle([margin, brand_y - 3, margin + 16, brand_y - 1], fill=CORAL)
    draw.text((margin, brand_y + 4), "SM PRODUCTION", font=font(9, 750), fill=(150, 164, 180))
    draw.text((W - margin, brand_y + 5), "sm-production.ru", font=font(7, 500), fill=(96, 112, 130), anchor="ra")
    return canvas


def save_under_limit(image: Image.Image, path: Path) -> int:
    """Сохраняет JPEG и, если файл тяжелее лимита, понижает качество."""
    for quality in (88, 84, 80, 76, 72, 68, 64, 60):
        image.save(path, format="JPEG", quality=quality, optimize=True, progressive=True, subsampling=2)
        if path.stat().st_size <= LIMIT_KB * 1024:
            break
    return path.stat().st_size


def contact_sheet(files: list[Path], path: Path) -> None:
    """Один лист с четырьмя креативами — чтобы проверить серию целиком."""
    pad, label_h = 18, 26
    cell_w, cell_h = W * 2, H * 2
    sheet = Image.new("RGB", (pad + (cell_w + pad) * len(files), pad * 2 + cell_h + label_h), (232, 228, 220))
    draw = ImageDraw.Draw(sheet)
    for index, file in enumerate(files):
        with Image.open(file) as image:
            scaled = image.convert("RGB").resize((cell_w, cell_h), Image.Resampling.LANCZOS)
        x = pad + index * (cell_w + pad)
        sheet.paste(scaled, (x, pad))
        draw.text(
            (x, pad + cell_h + 6),
            f"{file.stem} · {file.stat().st_size // 1024} КБ",
            font=font(15, 600),
            fill=(40, 52, 66),
        )
    sheet.save(path, format="JPEG", quality=92, optimize=True, progressive=True)


def main() -> int:
    OUT_DIR.mkdir(exist_ok=True)
    made: list[Path] = []
    over = 0
    print(f"Montserrat: {FONT_VF.name}")
    for scene in SCENES:
        out = OUT_DIR / f"{scene['slug']}-240x400.jpg"
        size = save_under_limit(build_photo(scene), out)
        made.append(out)
        over += size > LIMIT_KB * 1024
        print(f"{out.name}: {size / 1024:.1f} КБ")

    out = OUT_DIR / f"{TYPE_SCENE['slug']}-240x400.jpg"
    size = save_under_limit(build_typed(TYPE_SCENE), out)
    made.append(out)
    over += size > LIMIT_KB * 1024
    print(f"{out.name}: {size / 1024:.1f} КБ")

    print()
    for file in made:
        with Image.open(file) as check:
            dims = check.size
            ok = dims == (W, H) and file.stat().st_size <= LIMIT_KB * 1024
        print(f"{file.name}: {dims[0]}×{dims[1]} · {'OK' if ok else 'НЕ ПРОШЁЛ ПРОВЕРКУ'}")
        if not ok:
            over += 1

    sheet = ROOT_PREVIEW / "240x400-events-preview.jpg"
    contact_sheet(made, sheet)
    print(f"\nЛист превью: {sheet.relative_to(ROOT_PREVIEW.parents[2])}")
    print(f"Лимит {LIMIT_KB} КБ · превышений: {over}")
    return 1 if over else 0


ROOT_PREVIEW = Path(__file__).resolve().parent

if __name__ == "__main__":
    sys.exit(main())
