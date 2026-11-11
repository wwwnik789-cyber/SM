#!/usr/bin/env python3
"""Полный набор изображений для контент-пакета «Новый год 2027».

Что собирает:
  content/images/blog/       4 обложки 1600×900 (плюс копия в public/media для сайта)
  content/images/social/     11 постов × 2 формата: 1080×1350 (ВК) и 1080×1080 (Telegram)
  content/images/stories/    5 вертикальных карточек 1080×1920
  content/images/site/       герой 1920×1080 и 3 блока 1200×800 для страницы услуги
  content/images/preview/    контактные листы — всё сразу на одном экране

Запуск из корня репозитория:
    .venv/bin/python marketing/novogodnee-oformlenie-2027/content/build_images.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SOURCE = REPO / "marketing" / "novogodnee-oformlenie-2027" / "creatives" / "source"
FONT_VF = REPO / "banners" / "anikom-arena-3000x2500-concepts" / "source" / "Montserrat-Variable.ttf"
PUBLIC = REPO / "public" / "media"
OUT = HERE / "images"

NAVY = (8, 26, 43)
NAVY_SOFT = (13, 34, 56)
INK = (6, 19, 32)
CORAL = (217, 74, 67)
WHITE = (255, 255, 255)
MUTED = (176, 188, 202)
DIM = (124, 140, 158)

if not FONT_VF.exists():
    raise SystemExit(f"Не найден шрифт: {FONT_VF}")


# ─── типографика ─────────────────────────────────────────────────────────────


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


def fit(draw, text: str, max_width: int, max_height: int, start: int,
        weight: int = 800, factor: float = 1.06, floor: int = 22):
    size = start
    while size > floor:
        face = font(size, weight)
        lines = wrap(draw, text, face, max_width)
        if max(tw(draw, line, face) for line in lines) <= max_width and len(lines) * lh(face, factor) <= max_height:
            return face, lines
        size -= 2
    face = font(floor, weight)
    return face, wrap(draw, text, face, max_width)


def push_text(draw, lines, face, x: int, y: int, fill, factor: float = 1.06,
              align: str = "left", width: int = 0) -> int:
    step = lh(face, factor)
    for line in lines:
        dx = x
        if align == "center" and width:
            dx = x + (width - tw(draw, line, face)) // 2
        draw.text((dx, y), line, font=face, fill=fill)
        y += step
    return y


def spaced(draw, text: str, face, x: int, y: int, fill, gap: int) -> int:
    for ch in text:
        draw.text((x, y), ch, font=face, fill=fill)
        x += tw(draw, ch, face) + gap
    return x


# ─── фото ────────────────────────────────────────────────────────────────────


def cover(image: Image.Image, size: tuple[int, int], focus: tuple[float, float] = (.5, .5)) -> Image.Image:
    w, h = size
    scale = max(w / image.width, h / image.height)
    resized = image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS)
    left = int(max(0, min((resized.width - w) * focus[0], resized.width - w)))
    top = int(max(0, min((resized.height - h) * focus[1], resized.height - h)))
    return resized.crop((left, top, left + w, top + h))


def photo(name: str) -> Image.Image:
    return Image.open(SOURCE / f"{name}.jpg").convert("RGB")


def soft_shadow(canvas: Image.Image, box: tuple[int, int, int, int]) -> None:
    """Мягкая тень под панелью — чтобы блок не «прилипал» к фото."""
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rectangle(box, fill=(0, 0, 0, 120))
    layer = layer.filter(ImageFilter.GaussianBlur(26))
    canvas.paste(layer, (0, 0), layer)


# ─── фирменный блок ──────────────────────────────────────────────────────────


LOCKUP_TEXT = "SM PRODUCTION"


def lockup(draw, x: int, y: int, size: int, fill=WHITE, accent=CORAL) -> int:
    """Черта + начертание. Возвращает высоту блока."""
    rule_h = max(3, round(size * 0.13))
    draw.rectangle([x, y, x + round(size * 3.1), y + rule_h], fill=accent)
    face = font(size, 750)
    draw.text((x, y + rule_h + round(size * 0.55)), LOCKUP_TEXT, font=face, fill=fill)
    return rule_h + round(size * 0.55) + lh(face, 1.0)


def footer_note(draw, x: int, y: int, text: str, size: int, width: int) -> None:
    face = font(size, 500)
    for line in wrap(draw, text, face, width):
        draw.text((x, y), line, font=face, fill=DIM)
        y += lh(face, 1.18)


# ─── шаблоны ─────────────────────────────────────────────────────────────────


def card_photo(
    size: tuple[int, int],
    band: float,
    photo_name: str,
    kicker: str,
    title: str,
    sub: str,
    promise: str,
    note: str,
    focus: tuple[float, float] = (.5, .5),
) -> Image.Image:
    """Фото сверху, тёмная панель снизу. Основной формат постов.

    Панель собирается снизу вверх. Если на заголовок остаётся мало места,
    сначала убирается подзаголовок, потом сжимаются отступы — но заголовок
    никогда не наезжает на нижний блок.
    """
    w, h = size
    m = round(w * 0.066)
    inner_w = w - m * 2
    band_h = round(h * band)

    canvas = Image.new("RGB", size, NAVY)
    canvas.paste(cover(photo(photo_name), (w, band_h), focus), (0, 0))

    grad_h = round(h * 0.06)
    strip = canvas.crop((0, band_h - grad_h, w, band_h)).convert("RGBA")
    for i in range(grad_h):
        alpha = int(255 * (i / grad_h) ** 1.4)
        ImageDraw.Draw(strip).rectangle([0, i, w, i + 1], fill=NAVY + (alpha,))
    canvas.paste(strip.convert("RGB"), (0, band_h - grad_h))

    draw = ImageDraw.Draw(canvas)

    # ── верх панели
    lock_top = band_h + round(h * 0.036)
    lock_h = lockup(draw, m, lock_top, round(h * 0.018))
    kicker_face = font(round(h * 0.0215), 700)
    kicker_y = lock_top + lock_h + round(h * 0.026)
    spaced(draw, kicker.upper(), kicker_face, m, kicker_y, CORAL, round(h * 0.0036))
    title_top = kicker_y + lh(kicker_face, 1.0) + round(h * 0.024)

    # ── нижний блок: собираем снизу вверх
    note_face = font(round(h * 0.0175), 500)
    note_lines = wrap(draw, note, note_face, inner_w)
    note_step = lh(note_face, 1.2)
    note_y = h - round(h * 0.04) - len(note_lines) * note_step

    promise_face = font(round(h * 0.0335), 750)
    while tw(draw, promise, promise_face) > inner_w and promise_face.size > 15:
        promise_face = font(promise_face.size - 1, 750)
    promise_h = lh(promise_face, 1.0)
    promise_y = note_y - round(h * 0.04) - promise_h
    rule_y = promise_y - round(h * 0.028)

    # ── подзаголовок: место под него решается после расчёта заголовка
    sub_face = font(round(h * 0.021), 500)
    sub_raw = [line for line in sub.split("\n") if line.strip()] if sub else []
    while sub_raw and any(tw(draw, line, sub_face) > inner_w for line in sub_raw) and sub_face.size > 12:
        sub_face = font(sub_face.size - 1, 500)
    sub_step = lh(sub_face, 1.18)

    bottom_limit = rule_y - round(h * 0.03)

    def layout(drop_sub: bool, tight: bool) -> tuple:
        gap_title = round(h * (0.016 if tight else 0.022))
        sub_h = 0 if drop_sub else len(sub_raw) * sub_step + round(h * 0.032)
        room = bottom_limit - sub_h - gap_title - title_top
        face, lines = fit(draw, title, inner_w, max(room, 0), round(h * 0.064), factor=1.05, floor=round(h * 0.036))
        return face, lines, room, sub_h

    face, lines, room, sub_h = layout(False, False)
    title_h = len(lines) * lh(face, 1.05)
    if title_h > room:                      # не влезло — убираем подзаголовок
        face, lines, room, sub_h = layout(True, False)
        title_h = len(lines) * lh(face, 1.05)
    if title_h > room:                      # всё ещё не влезло — сжимаем отступы
        face, lines, room, sub_h = layout(True, True)
        title_h = len(lines) * lh(face, 1.05)
    show_sub = sub_h > 0

    title_y = title_top + max(0, room - title_h) // 3
    push_text(draw, lines, face, m, title_y, WHITE, 1.05)

    if show_sub:
        sub_top = title_y + title_h + round(h * 0.03)
        push_text(draw, sub_raw, sub_face, m, min(sub_top, bottom_limit - len(sub_raw) * sub_step), MUTED, 1.18)

    draw.rectangle([m, rule_y, m + round(w * 0.055), rule_y + max(3, round(h * 0.004))], fill=CORAL)
    draw.text((m, promise_y), promise, font=promise_face, fill=CORAL)
    for i, line in enumerate(note_lines):
        draw.text((m, note_y + i * note_step), line, font=note_face, fill=DIM)

    return canvas


def card_type(
    size: tuple[int, int],
    kicker: str,
    big: str,
    sub: str,
    promise: str,
    note: str,
    accent_bar: bool = True,
) -> Image.Image:
    """Полностью типографская карточка: тёмный фон, крупная цифра или фраза."""
    w, h = size
    m = round(w * 0.066)
    canvas = Image.new("RGB", size, NAVY)
    draw = ImageDraw.Draw(canvas)

    if accent_bar:
        draw.rectangle([w - round(w * 0.22), 0, w, h], fill=(10, 31, 50))
        draw.rectangle([w - round(w * 0.22), 0, w - round(w * 0.216), h], fill=(26, 52, 78))

    lockup(draw, m, round(h * 0.055), round(h * 0.019))

    kicker_face = font(round(h * 0.0235), 700)
    ky = round(h * 0.28)
    spaced(draw, kicker.upper(), kicker_face, m, ky, CORAL, round(h * 0.004))

    big_face, big_lines = fit(draw, big, w - m * 2 - round(w * 0.06), round(h * 0.34), round(h * 0.155),
                              weight=800, factor=1.0)
    by = ky + lh(kicker_face, 1.0) + round(h * 0.035)
    by = push_text(draw, big_lines, big_face, m, by, WHITE, 1.0)
    by += round(h * 0.03)

    if sub:
        sub_face = font(round(h * 0.0245), 500)
        sub_lines = wrap(draw, sub, sub_face, w - m * 2 - round(w * 0.05))
        push_text(draw, sub_lines, sub_face, m, by, MUTED, 1.2)

    promise_face = font(round(h * 0.033), 750)
    while tw(draw, promise, promise_face) > w - m * 2 and promise_face.size > 15:
        promise_face = font(promise_face.size - 1, 750)
    py = h - round(h * 0.13) - lh(promise_face, 1.0)
    draw.rectangle([m, py - round(h * 0.03), m + round(w * 0.055), py - round(h * 0.03) + max(3, round(h * 0.0045))], fill=CORAL)
    draw.text((m, py), promise, font=promise_face, fill=CORAL)
    footer_note(draw, m, h - round(h * 0.085), note, round(h * 0.0195), w - m * 2)
    return canvas


def card_list(
    size: tuple[int, int],
    kicker: str,
    title: str,
    items: list[str],
    promise: str,
    note: str,
    numbered: bool = True,
) -> Image.Image:
    """Заголовок и список — для чек-листов и разборов ошибок."""
    w, h = size
    m = round(w * 0.066)
    inner_w = w - m * 2
    canvas = Image.new("RGB", size, NAVY)
    draw = ImageDraw.Draw(canvas)
    draw.rectangle([0, 0, w, round(h * 0.012)], fill=CORAL)

    lock_h = lockup(draw, m, round(h * 0.05), round(h * 0.0185))
    kicker_face = font(round(h * 0.0205), 700)
    kicker_y = round(h * 0.05) + lock_h + round(h * 0.032)
    spaced(draw, kicker.upper(), kicker_face, m, kicker_y, CORAL, round(h * 0.0038))

    # низ: сначала считаем, сколько занимает подпись и обещание
    note_face = font(round(h * 0.018), 500)
    note_lines = wrap(draw, note, note_face, inner_w)
    note_step = lh(note_face, 1.2)
    note_y = h - round(h * 0.042) - len(note_lines) * note_step

    promise_face = font(round(h * 0.0275), 750)
    while tw(draw, promise, promise_face) > inner_w and promise_face.size > 14:
        promise_face = font(promise_face.size - 1, 750)
    promise_h = lh(promise_face, 1.0)
    promise_y = note_y - round(h * 0.038) - promise_h

    # заголовок
    title_top = kicker_y + lh(kicker_face, 1.0) + round(h * 0.026)
    title_face, title_lines = fit(draw, title, inner_w, round(h * 0.16), round(h * 0.058), factor=1.05)
    title_h = len(title_lines) * lh(title_face, 1.05)
    push_text(draw, title_lines, title_face, m, title_top, WHITE, 1.05)

    # список получает ровно то место, что осталось
    list_top = title_top + title_h + round(h * 0.034)
    list_bottom = promise_y - round(h * 0.032)
    row_h = (list_bottom - list_top) // max(1, len(items))
    text_face = font(min(round(h * 0.0265), round(row_h * 0.34)), 600)
    num_face = font(min(round(h * 0.0205), round(row_h * 0.27)), 800)
    text_x = m + round(w * 0.088)

    y = list_top
    for i, item in enumerate(items, 1):
        if numbered:
            draw.text((m, y + (row_h - lh(num_face, 1.0)) // 2), f"{i:02d}", font=num_face, fill=CORAL)
        else:
            box = max(10, round(row_h * 0.16))
            by = y + (row_h - box) // 2
            draw.rectangle([m, by, m + box, by + box], outline=CORAL, width=max(2, round(box * 0.16)))
        lines = wrap(draw, item, text_face, w - m - text_x)
        ty = y + (row_h - len(lines) * lh(text_face, 1.12)) // 2
        for line in lines:
            draw.text((text_x, ty), line, font=text_face, fill=WHITE)
            ty += lh(text_face, 1.12)
        y += row_h

    draw.rectangle([m, promise_y - round(h * 0.024), m + round(w * 0.055),
                    promise_y - round(h * 0.024) + max(3, round(h * 0.004))], fill=CORAL)
    draw.text((m, promise_y), promise, font=promise_face, fill=CORAL)
    for i, line in enumerate(note_lines):
        draw.text((m, note_y + i * note_step), line, font=note_face, fill=DIM)
    return canvas


def card_calendar(size: tuple[int, int], rows: list[tuple[str, str]], note: str) -> Image.Image:
    """Таймлайн сезона: дата слева, смысл справа."""
    w, h = size
    m = round(w * 0.066)
    canvas = Image.new("RGB", size, NAVY)
    draw = ImageDraw.Draw(canvas)
    draw.rectangle([0, 0, w, round(h * 0.012)], fill=CORAL)
    lockup(draw, m, round(h * 0.05), round(h * 0.019))

    kicker_face = font(round(h * 0.0215), 700)
    spaced(draw, "КАЛЕНДАРЬ СЕЗОНА", kicker_face, m, round(h * 0.145), CORAL, round(h * 0.004))
    title_face, title_lines = fit(draw, "Что успеваем к 20 декабря", w - m * 2, round(h * 0.13), round(h * 0.058))
    ty = round(h * 0.145) + lh(kicker_face, 1.0) + round(h * 0.025)
    ty = push_text(draw, title_lines, title_face, m, ty, WHITE, 1.04)

    top = ty + round(h * 0.04)
    bottom = h - round(h * 0.13)
    row_h = (bottom - top) // len(rows)
    date_face = font(min(round(h * 0.0205), round(row_h * 0.3)), 750)
    text_face = font(min(round(h * 0.0245), round(row_h * 0.34)), 500)
    col = round(w * 0.30)

    for i, (when, what) in enumerate(rows):
        y = top + i * row_h
        if i:
            draw.rectangle([m, y, w - m, y + 1], fill=(32, 55, 78))
        draw.text((m, y + round(row_h * 0.22)), when, font=date_face, fill=CORAL)
        lines = wrap(draw, what, text_face, w - m * 2 - col)
        push_text(draw, lines, text_face, m + col, y + round(row_h * 0.2), WHITE, 1.12)

    footer_note(draw, m, h - round(h * 0.075), note, round(h * 0.018), w - m * 2)
    return canvas


def card_compare(size: tuple[int, int], note: str) -> Image.Image:
    """Две колонки: брус-баннер против труб."""
    w, h = size
    m = round(w * 0.066)
    canvas = Image.new("RGB", size, NAVY)
    draw = ImageDraw.Draw(canvas)
    draw.rectangle([0, 0, w, round(h * 0.012)], fill=CORAL)
    lockup(draw, m, round(h * 0.05), round(h * 0.019))

    kicker_face = font(round(h * 0.0215), 700)
    spaced(draw, "СРАВНЕНИЕ", kicker_face, m, round(h * 0.145), CORAL, round(h * 0.004))
    title_face, title_lines = fit(draw, "Что видно на фотографиях", w - m * 2, round(h * 0.13), round(h * 0.058))
    ty = round(h * 0.145) + lh(kicker_face, 1.0) + round(h * 0.025)
    ty = push_text(draw, title_lines, title_face, m, ty, WHITE, 1.04)

    top = ty + round(h * 0.05)
    col_w = (w - m * 2 - round(w * 0.04)) // 2
    right_x = m + col_w + round(w * 0.04)
    height = round(h * 0.40)

    draw.rectangle([m, top, m + col_w, top + height], fill=NAVY_SOFT)
    draw.rectangle([right_x, top, right_x + col_w, top + height], fill=(21, 44, 68))

    head_face = font(round(h * 0.026), 750)
    kick_face = font(round(h * 0.019), 700)
    item_face = font(round(h * 0.0215), 500)

    for x, caption, head, items, color in (
        (m, "ТРУБЫ", "Каркас виден", ["виден сбоку", "складки и волны", "белые торцы"], DIM),
        (right_x, "БРУС-БАННЕР", "Каркас скрыт", ["ровное полотно", "торцы в дизайн", "любая форма"], CORAL),
    ):
        pad = round(w * 0.035)
        spaced(draw, caption, kick_face, x + pad, top + pad, color, round(h * 0.003))
        push_text(draw, wrap(draw, head, head_face, col_w - pad * 2), head_face,
                  x + pad, top + pad + round(h * 0.045), WHITE, 1.06)
        yy = top + pad + round(h * 0.045) + lh(head_face, 1.06) + round(h * 0.028)
        for item in items:
            draw.rectangle([x + pad, yy + round(h * 0.008), x + pad + round(w * 0.012), yy + round(h * 0.008) + round(w * 0.012)],
                           fill=color)
            draw.text((x + pad + round(w * 0.03), yy), item, font=item_face, fill=MUTED)
            yy += round(h * 0.045)

    promise_face = font(round(h * 0.028), 750)
    py = top + height + round(h * 0.05)
    draw.rectangle([m, py, m + round(w * 0.055), py + max(3, round(h * 0.004))], fill=CORAL)
    draw.text((m, py + round(h * 0.025)), "Скрытый каркас = чистый кадр", font=promise_face, fill=CORAL)
    footer_note(draw, m, h - round(h * 0.075), note, round(h * 0.018), w - m * 2)
    return canvas


# ─── сценарии ────────────────────────────────────────────────────────────────

NOTE_ARENA = "Москва и Московская область · монтаж 24/7"

POSTS: list[tuple[str, str]] = [
    # (slug, тип)
    ("01-start-sezona", "photo"),
    ("02-kalendar", "calendar"),
    ("03-sostav-ofisa", "list"),
    ("04-sem-oshibok", "list"),
    ("05-brus-protiv-trub", "compare"),
    ("06-korporativ", "photo"),
    ("07-chek-list", "list"),
    ("08-agentstvam", "photo"),
    ("09-desyat-dnej", "number"),
    ("10-poslednij-den", "number"),
    ("11-pozdravlenie", "photo"),
]


def post_1080x1350(slug: str, kind: str) -> Image.Image:
    size = (1080, 1350)
    if slug == "01-start-sezona":
        return card_photo(size, .52, "lobby", "Сезон 2027", "Сезон открыт.\nДальше — график",
                          "Заявки на монтаж до 20 декабря\nпринимаем до 10 декабря.",
                          "Монтаж до 20 декабря", NOTE_ARENA, (.5, .55))
    if slug == "03-sostav-ofisa":
        return card_list(size, "Состав сета", "Что входит в офисный сет",
                         ["Конструкция с печатью", "Ёлка или арт-объект", "Свет и гирлянды",
                          "Декор и упаковка", "Монтаж в нерабочее время", "Паспорт и документы"],
                         "Своё производство 750 м²", NOTE_ARENA)
    if slug == "04-sem-oshibok":
        return card_list(size, "Фотозоны", "7 ошибок, из-за которых фото не выходят",
                         ["Глянцевая печать", "Видимый каркас", "Незапечатанные торцы", "Мелкий текст",
                          "Свет сверху", "Мало места", "Неудачное место"], "Разбор — в блоге", NOTE_ARENA)
    if slug == "06-korporativ":
        return card_photo(size, .55, "corporate", "Корпоративы", "Сцена, фотозона\nи навигация",
                          "Монтаж в ночное окно.\nДежурство технической группы.",
                          "Работаем по брендбуку", NOTE_ARENA, (.5, .5))
    if slug == "08-agentstvam":
        return card_photo(size, .5, "art", "Агентствам", "Производство\nна декабрь",
                          "Смета, макеты и сроки — в вашем\nпредложении клиенту.",
                          "Расчёт за 1 рабочий день", NOTE_ARENA, (.45, .5))
    if slug == "11-pozdravlenie":
        return card_photo(size, .62, "photozone", "28 декабря", "С Новым годом!",
                          "Спасибо за проекты, ночные монтажи\nи ёлки, которые не влезали в лифт.",
                          "Команда SM Production", "Москва · 8 495 799-00-19", (.5, .45))
    if slug == "02-kalendar":
        return card_calendar(size, [
            ("до 10.11", "оптимально: любой состав"),
            ("10–25.11", "стандартные сроки"),
            ("26.11–10.12", "монтаж до 20 декабря"),
            ("11–15.12", "срочно, состав ограничен"),
            ("после 20.12", "без гарантии даты"),
        ], NOTE_ARENA)
    if slug == "05-brus-protiv-trub":
        return card_compare(size, NOTE_ARENA)
    if slug == "07-chek-list":
        return card_list(size, "Перед заявкой", "5 вопросов, которые экономят неделю",
                         ["Где стоит конструкция", "Что на ней должно быть", "Есть ли брендбук",
                          "Кто принимает работу", "Когда можно монтировать"],
                         "Ответьте — пришлём эскиз", NOTE_ARENA, numbered=False)
    if slug == "09-desyat-dnej":
        return card_type(size, "Дедлайн", "10 дней", "До конца приёма заявок\nна монтаж до 20 декабря.",
                         "Успеть ещё можно", NOTE_ARENA)
    if slug == "10-poslednij-den":
        return card_type(size, "Последний день", "10.12", "Заявки на гарантированный\nмонтаж до 20 декабря.",
                         "Дальше — только очередь", NOTE_ARENA)
    raise ValueError(slug)


def post_1080x1080(slug: str) -> Image.Image:
    """Квадратная версия: та же мысль, компактнее."""
    size = (1080, 1080)
    mapping = {
        "01-start-sezona": dict(band=.46, photo="lobby", kicker="Сезон 2027", title="Сезон открыт",
                                sub="Заявки на монтаж до 20 декабря — до 10 декабря.",
                                promise="Монтаж до 20 декабря", focus=(.5, .55)),
        "03-sostav-ofisa": dict(band=.46, photo="lobby", kicker="Офисный сет", title="Что входит в оформление",
                                sub="Конструкция, ёлка, свет, декор, монтаж.",
                                promise="Своё производство 750 м²", focus=(.55, .5)),
        "04-sem-oshibok": dict(band=.46, photo="photozone", kicker="Фотозоны", title="7 ошибок в фотозоне",
                               sub="Глянец, каркас, торцы, мелкий текст.",
                               promise="Разбор — в блоге", focus=(.5, .5)),
        "06-korporativ": dict(band=.5, photo="corporate", kicker="Корпоративы", title="Сцена и фотозона",
                              sub="Монтаж в ночное окно.", promise="Работаем по брендбуку", focus=(.5, .5)),
        "08-agentstvam": dict(band=.46, photo="art", kicker="Агентствам", title="Производство на декабрь",
                              sub="Смета и макеты — в вашем предложении.",
                              promise="Расчёт за 1 рабочий день", focus=(.45, .5)),
        "11-pozdravlenie": dict(band=.58, photo="photozone", kicker="28 декабря", title="С Новым годом!",
                                sub="Спасибо за сезон и ночные монтажи.",
                                promise="Команда SM Production", focus=(.5, .45)),
    }
    if slug in mapping:
        return card_photo(size, mapping[slug]["band"], mapping[slug]["photo"], mapping[slug]["kicker"],
                          mapping[slug]["title"], mapping[slug]["sub"], mapping[slug]["promise"],
                          NOTE_ARENA, mapping[slug]["focus"])
    if slug == "02-kalendar":
        return card_calendar(size, [
            ("до 10.11", "оптимально"),
            ("10–25.11", "стандарт"),
            ("26.11–10.12", "монтаж до 20.12"),
            ("после 20.12", "без гарантии"),
        ], NOTE_ARENA)
    if slug == "05-brus-protiv-trub":
        return card_compare(size, NOTE_ARENA)
    if slug == "07-chek-list":
        return card_list(size, "Перед заявкой", "5 вопросов перед заявкой",
                         ["Где стоит конструкция", "Что на ней должно быть", "Есть ли брендбук",
                          "Кто принимает работу", "Когда можно монтировать"],
                         "Ответьте — пришлём эскиз", NOTE_ARENA, numbered=False)
    if slug == "09-desyat-dnej":
        return card_type(size, "Дедлайн", "10 дней", "До конца приёма заявок.", "Успеть ещё можно", NOTE_ARENA)
    if slug == "10-poslednij-den":
        return card_type(size, "Последний день", "10.12", "Заявки на монтаж до 20 декабря.", "Дальше — только очередь", NOTE_ARENA)
    raise ValueError(slug)


def story(slug: str) -> Image.Image:
    """1080×1920: фото-полоса по центру, текст сверху и снизу."""
    w, h = 1080, 1920
    m = round(w * 0.072)
    canvas = Image.new("RGB", size := (w, h), NAVY)
    draw = ImageDraw.Draw(canvas)

    config = {
        "01-sroki": dict(kicker="Сезон 2027", title="Успеть до 20 декабря", photo="lobby",
                         footer="Свайп вверх — календарь сезона", focus=(.5, .55)),
        "02-oshibki": dict(kicker="Фотозоны", title="7 ошибок в фотозоне", photo="photozone",
                           footer="Разбор в статье — ссылка в шапке", focus=(.5, .5)),
        "03-brus": dict(kicker="Сравнение", title="Брус против труб", photo="corporate",
                        footer="Что видно на фото — в статье", focus=(.5, .5)),
        "04-dedlajn": dict(kicker="Дедлайн", title="10 дней до конца заявок", photo="art",
                           footer="Пишите — посчитаем за день", focus=(.45, .5)),
        "05-pozdravlenie": dict(kicker="28 декабря", title="С Новым годом!", photo="photozone",
                                footer="Команда SM Production", focus=(.5, .45)),
    }[slug]

    lockup(draw, m, round(h * 0.06), round(w * 0.021))

    kicker_face = font(round(w * 0.026), 700)
    spaced(draw, config["kicker"].upper(), kicker_face, m, round(h * 0.19), CORAL, round(w * 0.0045))

    title_face, title_lines = fit(draw, config["title"], w - m * 2, round(h * 0.11), round(w * 0.088))
    ty = round(h * 0.19) + lh(kicker_face, 1.0) + round(h * 0.02)
    ty = push_text(draw, title_lines, title_face, m, ty, WHITE, 1.04)

    band_top = ty + round(h * 0.042)
    band_h = round(h * 0.34)
    canvas.paste(cover(photo(config["photo"]), (w, band_h), config["focus"]), (0, band_top))

    draw.rectangle([0, band_top - 4, w, band_top], fill=CORAL)

    face = font(round(w * 0.03), 600)
    lines = wrap(draw, config["footer"], face, w - m * 2)
    fy = band_top + band_h + round(h * 0.06)
    push_text(draw, lines, face, m, fy, MUTED, 1.2)

    # нижний блок: телефон, под ним плашка с адресом сайта
    tel_face = font(round(w * 0.028), 600)
    tel_text = "8 495 799-00-19 · Москва"
    chip_text = "sm-production.ru"
    chip_face = font(round(w * 0.03), 750)
    chip_h = round(w * 0.082)
    chip_w = tw(draw, chip_text, chip_face) + round(w * 0.062)

    chip_y = h - round(h * 0.045) - chip_h
    tel_y = chip_y - round(h * 0.022) - lh(tel_face, 1.0)

    draw.text((m, tel_y), tel_text, font=tel_face, fill=MUTED)
    draw.rectangle([m, chip_y, m + chip_w, chip_y + chip_h], fill=CORAL)
    draw.text((m + round(w * 0.031), chip_y + (chip_h - lh(chip_face, 1.0)) // 2), chip_text,
              font=chip_face, fill=WHITE)
    return canvas


def site_hero() -> Image.Image:
    w, h = 1920, 1080
    canvas = cover(photo("lobby"), (w, h), (.5, .55)).convert("RGBA")
    canvas = Image.alpha_composite(canvas, Image.new("RGBA", (w, h), NAVY + (80,)))
    scrim = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sd = ImageDraw.Draw(scrim)
    for x in range(0, round(w * 0.62)):
        t = 1 - x / (w * 0.62)
        sd.rectangle([x, 0, x + 1, h], fill=NAVY + (int(240 * t ** 1.25),))
    canvas = Image.alpha_composite(canvas, scrim).convert("RGB")
    draw = ImageDraw.Draw(canvas)
    m = round(w * 0.07)
    lockup(draw, m, round(h * 0.12), round(h * 0.0125))

    kicker_face = font(round(h * 0.0165), 700)
    spaced(draw, "СЕЗОН 2027 · МОСКВА И ОБЛАСТЬ", kicker_face, m, round(h * 0.34), CORAL, round(w * 0.0028))

    title_face, title_lines = fit(draw, "Новогоднее оформление офисов, фотозон и событий",
                                  round(w * 0.52), round(h * 0.24), round(h * 0.085))
    ty = round(h * 0.4)
    ty = push_text(draw, title_lines, title_face, m, ty, WHITE, 1.06)

    sub_face = font(round(h * 0.024), 500)
    push_text(draw, wrap(draw, "Монтаж до 20 декабря. Расчёт за 1 рабочий день. Своё производство 750 м².",
                         sub_face, round(w * 0.44)), sub_face, m, ty + round(h * 0.035), MUTED, 1.25)
    return canvas


def site_block(slug: str) -> Image.Image:
    w, h = 1200, 800
    config = {
        "01-sroki": dict(photo="lobby", kicker="Сроки", title="Календарь сезона",
                         sub="Заявки до 10 декабря — монтаж до 20-го.", focus=(.5, .55)),
        "02-fotozona": dict(photo="photozone", kicker="Фотозоны", title="Скрытый каркас",
                            sub="Ровное полотно, торцы в дизайн, матовая печать.", focus=(.5, .5)),
        "03-proizvodstvo": dict(photo="art", kicker="Производство", title="750 м² в Москве",
                                sub="Печать, фрезеровка, сборка, свет.", focus=(.45, .5)),
    }[slug]
    canvas = cover(photo(config["photo"]), (w, h), config["focus"])
    canvas = canvas.convert("RGBA")
    # общий холодный тон + плотный градиент снизу под текст
    canvas = Image.alpha_composite(canvas, Image.new("RGBA", (w, h), NAVY + (70,)))
    scrim = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sd = ImageDraw.Draw(scrim)
    for y in range(round(h * 0.35), h):
        t = (y - h * 0.35) / (h * 0.65)
        sd.rectangle([0, y, w, y + 1], fill=NAVY + (int(235 * t ** 1.5),))
    canvas = Image.alpha_composite(canvas, scrim).convert("RGB")
    draw = ImageDraw.Draw(canvas)
    m = round(w * 0.07)

    kicker_face = font(round(h * 0.026), 700)
    spaced(draw, config["kicker"].upper(), kicker_face, m, round(h * 0.63), CORAL, round(w * 0.004))
    title_face, title_lines = fit(draw, config["title"], w - m * 2, round(h * 0.16), round(h * 0.072))
    ty = round(h * 0.63) + lh(kicker_face, 1.0) + round(h * 0.025)
    ty = push_text(draw, title_lines, title_face, m, ty, WHITE, 1.04)
    sub_face = font(round(h * 0.031), 500)
    push_text(draw, wrap(draw, config["sub"], sub_face, w - m * 2), sub_face, m, ty + round(h * 0.02), MUTED, 1.18)
    return canvas


def blog_cover(name: str, target: str, focus: tuple[float, float]) -> Image.Image:
    return cover(photo(name), (1600, 900), focus)


# ─── контактные листы ────────────────────────────────────────────────────────


def contact_sheet(files: list[tuple[Path, str]], columns: int, cell: tuple[int, int],
                  out: Path, title: str) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    pad, label_h, header = 28, 46, 96
    rows = (len(files) + columns - 1) // columns
    w = pad * (columns + 1) + cell[0] * columns
    h = header + rows * (cell[1] + label_h + pad) + pad
    canvas = Image.new("RGB", (w, h), (14, 20, 28))
    draw = ImageDraw.Draw(canvas)

    draw.rectangle([0, 0, w, 8], fill=CORAL)
    draw.text((pad, 34), title, font=font(34, 800), fill=WHITE)

    for i, (path, label) in enumerate(files):
        col, row = i % columns, i // columns
        x = pad + col * (cell[0] + pad)
        y = header + row * (cell[1] + label_h + pad)
        img = Image.open(path).convert("RGB")
        scale = min(cell[0] / img.width, cell[1] / img.height)
        img = img.resize((round(img.width * scale), round(img.height * scale)), Image.Resampling.LANCZOS)
        tile = Image.new("RGB", cell, (30, 40, 52))
        tile.paste(img, ((cell[0] - img.width) // 2, (cell[1] - img.height) // 2))
        canvas.paste(tile, (x, y))
        draw.text((x + 2, y + cell[1] + 12), label, font=font(19, 600), fill=(200, 210, 220))
    canvas.save(out, quality=90, optimize=True)
    print(f"{out.relative_to(OUT)}: {canvas.width}×{canvas.height}, {out.stat().st_size // 1024} КБ")


# ─── сборка ──────────────────────────────────────────────────────────────────


def save(img: Image.Image, path: Path, quality: int = 90) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, format="JPEG", quality=quality, optimize=True, progressive=True)


def main() -> int:
    made: dict[str, list[tuple[Path, str]]] = {"blog": [], "social": [], "stories": [], "site": []}

    # 1. Обложки блога: в пакет и в public/media для сайта
    covers = [
        ("lobby", "ng-2027-office.jpg", (.55, .5)),
        ("photozone", "ng-2027-photozone.jpg", (.55, .5)),
        ("corporate", "ng-2027-brus-banner.jpg", (.55, .5)),
        ("art", "ng-2027-brandbook.jpg", (.55, .45)),
    ]
    for name, target, focus in covers:
        img = blog_cover(name, target, focus)
        save(img, PUBLIC / target, 88)
        path = OUT / "blog" / target
        save(img, path, 88)
        made["blog"].append((path, f"{target} · 1600×900"))

    # 2. Посты: 1080×1350 и 1080×1080
    for slug, _kind in POSTS:
        portrait = post_1080x1350(slug, _kind)
        p = OUT / "social" / "1080x1350" / f"{slug}-4x5.jpg"
        save(portrait, p)
        made["social"].append((p, f"{slug} · 4:5"))

        square = post_1080x1080(slug)
        s = OUT / "social" / "1080x1080" / f"{slug}-1x1.jpg"
        save(square, s)
        made["social"].append((s, f"{slug} · 1:1"))

    # 3. Сторис
    for slug in ("01-sroki", "02-oshibki", "03-brus", "04-dedlajn", "05-pozdravlenie"):
        img = story(slug)
        p = OUT / "stories" / f"{slug}-1080x1920.jpg"
        save(img, p)
        made["stories"].append((p, f"{slug} · 9:16"))

    # 4. Сайт
    hero = site_hero()
    save(hero, OUT / "site" / "hero-1920x1080.jpg")
    made["site"].append((OUT / "site" / "hero-1920x1080.jpg", "hero · 1920×1080"))
    for slug in ("01-sroki", "02-fotozona", "03-proizvodstvo"):
        img = site_block(slug)
        p = OUT / "site" / f"{slug}-1200x800.jpg"
        save(img, p)
        made["site"].append((p, f"{slug} · 1200×800"))

    # 5. Контактные листы
    preview = OUT / "preview"
    contact_sheet(made["blog"], 2, (760, 428), preview / "01-blog.jpg", "Блог · обложки 1600×900")
    social = [f for f in made["social"] if f[0].parent.name == "1080x1350"]
    contact_sheet(social, 4, (360, 450), preview / "02-social-4x5.jpg", "Соцсети · 1080×1350 (ВК)")
    squares = [f for f in made["social"] if f[0].parent.name == "1080x1080"]
    contact_sheet(squares, 4, (360, 360), preview / "03-social-1x1.jpg", "Соцсети · 1080×1080 (Telegram)")
    contact_sheet(made["stories"], 5, (300, 533), preview / "04-stories.jpg", "Сторис · 1080×1920")
    contact_sheet(made["site"], 2, (720, 480), preview / "05-site.jpg", "Сайт · герой и блоки")

    total = sum(len(v) for v in made.values())
    print(f"\nВсего изображений: {total}")
    for key, files in made.items():
        size = sum(p.stat().st_size for p, _ in files) // 1024
        print(f"  {key}: {len(files)} файлов, {size} КБ")
    return 0


if __name__ == "__main__":
    sys.exit(main())
