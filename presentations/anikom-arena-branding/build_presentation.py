#!/usr/bin/env python3
"""Build the client-facing Anikom Arena branding concept PDF.

The deck uses only the supplied venue photographs and logos. Visual proposals
are deliberately conceptual: production dimensions and mounting details must be
confirmed after an on-site survey.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pymupdf
from PIL import Image, ImageOps, ImageDraw, ImageFont
from reportlab.lib.colors import Color, HexColor, white
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
FONTS = ROOT / "fonts"
OUTPUT = ROOT / "Anikom-Arena-branding-concept.pdf"
PREVIEW = ROOT / "presentation-preview.jpg"

PAGE_W = 960
PAGE_H = 540
TOTAL_SLIDES = 11

NAVY = HexColor("#091A2B")
NAVY_2 = HexColor("#102B45")
NAVY_3 = HexColor("#173B59")
RED = HexColor("#D94B43")
RED_DARK = HexColor("#9F2E31")
WHITE = HexColor("#F6F8FA")
MIST = HexColor("#E7EDF2")
STEEL = HexColor("#A8B5C2")
SLATE = HexColor("#5E7081")
INK = HexColor("#172330")
GOLD = HexColor("#D3B166")
GREEN = HexColor("#3E8B70")

FONT = "DejaVu"
FONT_BOLD = "DejaVu-Bold"
FONT_DISPLAY = "Montserrat"
FONT_ITALIC = "Montserrat-Italic"

pdfmetrics.registerFont(TTFont(FONT, str(FONTS / "DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont(FONT_BOLD, str(FONTS / "DejaVuSans-Bold.ttf")))
pdfmetrics.registerFont(TTFont(FONT_DISPLAY, str(FONTS / "Montserrat-Variable.ttf")))
pdfmetrics.registerFont(TTFont(FONT_ITALIC, str(FONTS / "Montserrat-Italic-Variable.ttf")))


def set_alpha(c: canvas.Canvas, fill: float | None = None, stroke: float | None = None) -> None:
    if fill is not None:
        try:
            c.setFillAlpha(fill)
        except Exception:
            pass
    if stroke is not None:
        try:
            c.setStrokeAlpha(stroke)
        except Exception:
            pass


def reset_alpha(c: canvas.Canvas) -> None:
    set_alpha(c, 1, 1)


def image_size(path: Path) -> tuple[int, int]:
    with Image.open(path) as im:
        return im.size


def draw_image_cover(
    c: canvas.Canvas,
    path: Path,
    x: float,
    y: float,
    w: float,
    h: float,
    focus_x: float = 0.5,
    focus_y: float = 0.5,
) -> None:
    iw, ih = image_size(path)
    scale = max(w / iw, h / ih)
    dw, dh = iw * scale, ih * scale
    dx = x + (w - dw) * focus_x
    dy = y + (h - dh) * focus_y
    c.saveState()
    clip = c.beginPath()
    clip.rect(x, y, w, h)
    c.clipPath(clip, stroke=0, fill=0)
    c.drawImage(ImageReader(str(path)), dx, dy, dw, dh, mask="auto")
    c.restoreState()


def draw_image_contain(c: canvas.Canvas, path: Path, x: float, y: float, w: float, h: float) -> None:
    iw, ih = image_size(path)
    scale = min(w / iw, h / ih)
    dw, dh = iw * scale, ih * scale
    c.drawImage(ImageReader(str(path)), x + (w - dw) / 2, y + (h - dh) / 2, dw, dh, mask="auto")


def lines_for(text: str, font: str, size: float, max_width: float) -> list[str]:
    result: list[str] = []
    for paragraph in text.split("\n"):
        words = paragraph.split()
        if not words:
            result.append("")
            continue
        line = words[0]
        for word in words[1:]:
            candidate = f"{line} {word}"
            if pdfmetrics.stringWidth(candidate, font, size) <= max_width:
                line = candidate
            else:
                result.append(line)
                line = word
        result.append(line)
    return result


def paragraph(
    c: canvas.Canvas,
    text: str,
    x: float,
    top: float,
    max_width: float,
    size: float = 15,
    leading: float | None = None,
    color=INK,
    font: str = FONT,
    max_lines: int | None = None,
) -> float:
    leading = leading or size * 1.35
    lines = lines_for(text, font, size, max_width)
    if max_lines is not None:
        lines = lines[:max_lines]
    c.setFillColor(color)
    c.setFont(font, size)
    y = top
    for line in lines:
        c.drawString(x, y, line)
        y -= leading
    return y


def bullet_list(
    c: canvas.Canvas,
    items: Iterable[str],
    x: float,
    top: float,
    max_width: float,
    size: float = 13,
    leading: float = 17,
    color=INK,
    bullet_color=RED,
    gap: float = 8,
) -> float:
    y = top
    for item in items:
        wrapped = lines_for(item, FONT, size, max_width - 24)
        c.setFillColor(bullet_color)
        c.circle(x + 4, y + 4, 3.5, stroke=0, fill=1)
        c.setFillColor(color)
        c.setFont(FONT, size)
        for idx, line in enumerate(wrapped):
            c.drawString(x + 18, y - idx * leading, line)
        y -= len(wrapped) * leading + gap
    return y


def title_block(c: canvas.Canvas, kicker: str, title: str, x: float = 58, top: float = 488, width: float = 820, dark=False) -> float:
    fg = WHITE if dark else INK
    muted = STEEL if dark else SLATE
    c.setFillColor(RED)
    c.roundRect(x, top - 2, 34, 5, 2.5, stroke=0, fill=1)
    c.setFillColor(muted)
    c.setFont(FONT_BOLD, 10)
    c.drawString(x + 46, top - 5, kicker.upper())
    return paragraph(c, title, x, top - 32, width, size=29, leading=32, color=fg, font=FONT_BOLD)


def footer(c: canvas.Canvas, number: int, dark=False) -> None:
    color = Color(1, 1, 1, alpha=.58) if dark else SLATE
    c.setStrokeColor(Color(1, 1, 1, alpha=.18) if dark else HexColor("#D9E1E7"))
    c.setLineWidth(.7)
    c.line(58, 28, 902, 28)
    c.setFillColor(color)
    c.setFont(FONT, 8)
    c.drawString(58, 14, "АНИКОМ АРЕНА • КОНЦЕПЦИЯ ОФОРМЛЕНИЯ")
    c.drawRightString(902, 14, f"{number:02d} / {TOTAL_SLIDES:02d}")


def rounded_card(c: canvas.Canvas, x: float, y: float, w: float, h: float, fill=WHITE, stroke=None, radius=18, alpha=1) -> None:
    set_alpha(c, alpha, alpha)
    c.setFillColor(fill)
    if stroke:
        c.setStrokeColor(stroke)
        c.setLineWidth(1)
    c.roundRect(x, y, w, h, radius, stroke=1 if stroke else 0, fill=1)
    reset_alpha(c)


def photo_card(c: canvas.Canvas, path: Path, x: float, y: float, w: float, h: float, label: str | None = None, focus_y=.5) -> None:
    rounded_card(c, x, y, w, h, WHITE, HexColor("#D9E1E7"), 14)
    draw_image_cover(c, path, x + 5, y + 5, w - 10, h - 10, focus_y=focus_y)
    if label:
        set_alpha(c, .88)
        c.setFillColor(NAVY)
        c.roundRect(x + 14, y + 14, max(80, pdfmetrics.stringWidth(label, FONT_BOLD, 9) + 22), 24, 7, stroke=0, fill=1)
        reset_alpha(c)
        c.setFillColor(WHITE)
        c.setFont(FONT_BOLD, 9)
        c.drawString(x + 25, y + 22, label.upper())


def arena_logo(c: canvas.Canvas, x: float, y: float, w: float, h: float) -> None:
    draw_image_contain(c, ASSETS / "anikom-arena-logo.png", x, y, w, h)


def sm_logo(c: canvas.Canvas, x: float, y: float, w: float, h: float) -> None:
    draw_image_contain(c, ASSETS / "sm-production-logo.png", x, y, w, h)


def number_marker(c: canvas.Canvas, x: float, y: float, number: str, label: str | None = None) -> None:
    c.setFillColor(RED)
    c.circle(x, y, 15, stroke=0, fill=1)
    c.setFillColor(WHITE)
    c.setFont(FONT_BOLD, 10)
    c.drawCentredString(x, y - 3.5, number)
    if label:
        tw = pdfmetrics.stringWidth(label, FONT_BOLD, 9) + 18
        set_alpha(c, .88)
        c.setFillColor(NAVY)
        c.roundRect(x + 19, y - 11, tw, 22, 7, stroke=0, fill=1)
        reset_alpha(c)
        c.setFillColor(WHITE)
        c.setFont(FONT_BOLD, 9)
        c.drawString(x + 28, y - 3, label)


def pitch_motif(c: canvas.Canvas, x: float, y: float, w: float, h: float, color=WHITE, alpha=.12) -> None:
    set_alpha(c, None, alpha)
    c.setStrokeColor(color)
    c.setLineWidth(1.2)
    c.roundRect(x, y, w, h, 12, stroke=1, fill=0)
    c.line(x + w / 2, y, x + w / 2, y + h)
    c.circle(x + w / 2, y + h / 2, min(w, h) * .16, stroke=1, fill=0)
    c.rect(x, y + h * .25, w * .16, h * .5, stroke=1, fill=0)
    c.rect(x + w * .84, y + h * .25, w * .16, h * .5, stroke=1, fill=0)
    reset_alpha(c)


def slide_01(c: canvas.Canvas) -> None:
    draw_image_cover(c, ASSETS / "field-front.jpg", 0, 0, PAGE_W, PAGE_H, focus_y=.46)
    set_alpha(c, .80)
    c.setFillColor(NAVY)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    reset_alpha(c)
    c.saveState()
    set_alpha(c, .16)
    c.setFillColor(RED)
    c.transform(1, 0, -.22, 1, 0, 0)
    c.rect(-80, 0, 320, PAGE_H, stroke=0, fill=1)
    c.restoreState()
    reset_alpha(c)
    pitch_motif(c, 570, 75, 330, 390, WHITE, .14)
    arena_logo(c, 62, 328, 132, 178)
    c.setFillColor(RED)
    c.roundRect(238, 448, 58, 7, 3, stroke=0, fill=1)
    c.setFillColor(STEEL)
    c.setFont(FONT_BOLD, 10)
    c.drawString(312, 445, "КОНЦЕПТ-ПРЕЗЕНТАЦИЯ • 2026")
    paragraph(c, "КОНЦЕПЦИЯ\nОФОРМЛЕНИЯ", 238, 400, 520, size=43, leading=45, color=WHITE, font=FONT_BOLD)
    c.setFillColor(RED)
    c.setFont(FONT_BOLD, 31)
    c.drawString(238, 290, "АНИКОМ АРЕНА")
    paragraph(c, "Единая визуальная система площадки:\nот навигации до партнёрских активаций", 238, 253, 470, 16, 22, MIST, FONT)
    c.setFillColor(STEEL)
    c.setFont(FONT, 9)
    c.drawString(62, 38, "ПРЕДЛОЖЕНИЕ ПО РАЗВИТИЮ БРЕНДА И НОСИТЕЛЕЙ")
    sm_logo(c, 806, 20, 100, 82)


def slide_02(c: canvas.Canvas) -> None:
    c.setFillColor(MIST)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    title_block(c, "01 • ИСХОДНАЯ ТОЧКА", "У арены уже есть сильная визуальная основа")
    cards = [
        (ASSETS / "reception-branding.jpg", 58, "УЗНАВАЕМЫЙ ЗНАК", "Логотип уже уверенно работает на крупных поверхностях и в интерьерных точках."),
        (ASSETS / "press-wall.jpg", 341, "БАЗОВАЯ СИСТЕМА", "Тёмно-синий фон, белая графика и повторяемые модули создают целостный образ."),
        (ASSETS / "ball-plinth.jpg", 624, "ГОТОВЫЕ АКТИВАЦИИ", "Пьедестал, пресс-волл и экран показывают потенциал бренда в событийной среде."),
    ]
    for path, x, heading, body in cards:
        rounded_card(c, x, 112, 260, 286, WHITE, HexColor("#D7E0E7"), 16)
        draw_image_cover(c, path, x + 7, 244, 246, 147, focus_y=.5)
        c.setFillColor(RED)
        c.rect(x + 18, 215, 34, 4, stroke=0, fill=1)
        c.setFillColor(INK)
        c.setFont(FONT_BOLD, 13)
        c.drawString(x + 18, 192, heading)
        paragraph(c, body, x + 18, 167, 224, 11, 15, SLATE, FONT)
    rounded_card(c, 58, 56, 826, 40, NAVY, None, 12)
    c.setFillColor(WHITE)
    c.setFont(FONT_BOLD, 12)
    c.drawCentredString(471, 71, "СЛЕДУЮЩИЙ ШАГ — СОБРАТЬ ОТДЕЛЬНЫЕ НОСИТЕЛИ В ЕДИНУЮ СИСТЕМУ")
    footer(c, 2)


def slide_03(c: canvas.Canvas) -> None:
    c.setFillColor(NAVY)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    draw_image_cover(c, ASSETS / "field-side.jpg", 0, 0, 610, 540, focus_x=.56, focus_y=.46)
    set_alpha(c, .17)
    c.setFillColor(NAVY)
    c.rect(0, 0, 610, 540, stroke=0, fill=1)
    reset_alpha(c)
    number_marker(c, 420, 304, "01", "ГЛАВНАЯ ТРИБУНА")
    number_marker(c, 270, 150, "02", "ПЕРИМЕТР ПОЛЯ")
    number_marker(c, 515, 218, "03", "ВХОД / ПОТОК")
    number_marker(c, 145, 238, "04", "СОБЫТИЙНАЯ ЗОНА")
    c.setFillColor(NAVY)
    c.rect(610, 0, 350, 540, stroke=0, fill=1)
    c.setFillColor(RED)
    c.roundRect(654, 486, 42, 5, 2.5, stroke=0, fill=1)
    c.setFillColor(STEEL)
    c.setFont(FONT_BOLD, 10)
    c.drawString(711, 481, "02 • КАРТА ВОЗМОЖНОСТЕЙ")
    paragraph(c, "Где бренд\nможет работать", 654, 442, 250, 28, 31, WHITE, FONT_BOLD)
    bullet_list(c, [
        "Фасад главной трибуны и ограждения",
        "Бровка поля и временные конструкции",
        "Медиа-башня и зона трансляции",
        "Экран и match-day графика",
        "Вход, навигация и раздевалки",
        "Пресс-зона, фототочки и партнёры",
    ], 654, 335, 255, 12, 16, MIST, RED, 7)
    c.setFillColor(STEEL)
    c.setFont(FONT_ITALIC, 10)
    c.drawString(654, 56, "Каждая точка получает роль, формат и приоритет.")
    footer(c, 3, dark=True)


def slide_04(c: canvas.Canvas) -> None:
    c.setFillColor(WHITE)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    title_block(c, "03 • КОНЦЕПЦИЯ", "Одна система — три режима работы")
    columns = [
        (58, NAVY_2, "01", "ПОСТОЯННЫЙ БРЕНД", ["фасад и вход", "навигация", "раздевалки", "медиа-башня"]),
        (341, RED_DARK, "02", "MATCH-DAY", ["экран", "бровка поля", "подиумы", "интервью-зона"]),
        (624, HexColor("#315C6C"), "03", "ПАРТНЁРЫ / СОБЫТИЯ", ["press wall", "конструкции 5×3 м", "временная навигация", "фотоактивации"]),
    ]
    for x, color, num, heading, items in columns:
        rounded_card(c, x, 145, 260, 252, color, None, 18)
        c.setFillColor(Color(1, 1, 1, alpha=.14))
        c.circle(x + 52, 350, 27, stroke=0, fill=1)
        c.setFillColor(WHITE)
        c.setFont(FONT_BOLD, 17)
        c.drawCentredString(x + 52, 344, num)
        c.setFont(FONT_BOLD, 13)
        c.drawString(x + 22, 300, heading)
        bullet_list(c, items, x + 22, 270, 210, 11, 14, MIST, WHITE, 6)
    c.setFillColor(INK)
    c.setFont(FONT_BOLD, 11)
    c.drawString(58, 105, "ПАЛИТРА И ПРИНЦИПЫ")
    swatches = [(NAVY, "DEEP NAVY"), (RED, "ARENA RED"), (WHITE, "WHITE"), (STEEL, "STEEL")]
    sx = 258
    for color, label in swatches:
        c.setFillColor(color)
        c.roundRect(sx, 86, 54, 22, 7, stroke=0, fill=1)
        c.setFillColor(SLATE)
        c.setFont(FONT, 8)
        c.drawString(sx + 62, 93, label)
        sx += 145
    paragraph(c, "Фирменный круг логотипа + линии футбольного поля + модульная сетка партнёров.", 58, 62, 800, 10, 14, SLATE, FONT)
    footer(c, 4)


def slide_05(c: canvas.Canvas) -> None:
    draw_image_cover(c, ASSETS / "stand-close.jpg", 0, 0, 620, 540, focus_y=.48)
    set_alpha(c, .78)
    c.setFillColor(NAVY)
    c.roundRect(96, 238, 428, 31, 5, stroke=0, fill=1)
    c.setFillColor(RED)
    c.roundRect(225, 310, 168, 30, 5, stroke=0, fill=1)
    c.setFillColor(NAVY)
    c.roundRect(107, 142, 406, 25, 5, stroke=0, fill=1)
    reset_alpha(c)
    arena_logo(c, 271, 300, 74, 50)
    number_marker(c, 431, 333, "01")
    number_marker(c, 527, 252, "02")
    number_marker(c, 522, 153, "03")
    number_marker(c, 309, 111, "04")
    c.setFillColor(NAVY)
    c.rect(620, 0, 340, 540, stroke=0, fill=1)
    c.setFillColor(RED)
    c.roundRect(659, 486, 38, 5, 2.5, stroke=0, fill=1)
    c.setFillColor(STEEL)
    c.setFont(FONT_BOLD, 10)
    c.drawString(711, 481, "04 • ОСНОВНОЙ ОБЪЕКТ")
    paragraph(c, "Главная трибуна\nи фасад", 659, 442, 250, 28, 31, WHITE, FONT_BOLD)
    specs = [
        ("01", "Вывеска над центральным входом", "постоянный носитель"),
        ("02", "Сменная партнёрская лента", "ограждение балкона"),
        ("03", "Брендинг зон скамеек", "матчевые и сезонные кампании"),
        ("04", "Фототочка по оси поля", "награды, команды, партнёры"),
    ]
    y = 333
    for num, head, sub in specs:
        c.setFillColor(RED)
        c.setFont(FONT_BOLD, 11)
        c.drawString(659, y, num)
        c.setFillColor(WHITE)
        c.setFont(FONT_BOLD, 11)
        c.drawString(695, y, head)
        c.setFillColor(STEEL)
        c.setFont(FONT, 9)
        c.drawString(695, y - 16, sub)
        y -= 62
    c.setFillColor(Color(1, 1, 1, alpha=.11))
    c.roundRect(650, 48, 270, 54, 12, stroke=0, fill=1)
    paragraph(c, "Схема концептуальная. Крепления и размеры — после обмеров.", 666, 78, 235, 9, 13, MIST, FONT)
    footer(c, 5, dark=True)


def slide_06(c: canvas.Canvas) -> None:
    c.setFillColor(MIST)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    title_block(c, "05 • MATCH-DAY", "Поле, медиа-башня и экран")
    data = [
        (ASSETS / "camera-tower.jpg", 58, "МЕДИА-БАШНЯ", "Облицовка глухих панелей, крупный знак, сервисная информация и съёмочный статус."),
        (ASSETS / "scoreboard-match.jpg", 341, "ЭКРАН", "Фирменная рамка, единый шаблон счёта, партнёрские модули и заставки между матчами."),
        (ASSETS / "ball-scoreboard.jpg", 624, "ПОЛЕВАЯ АКТИВАЦИЯ", "Подиумы, наградные точки, презентация мяча и мобильные конструкции на бровке."),
    ]
    for path, x, head, body in data:
        rounded_card(c, x, 85, 260, 323, WHITE, HexColor("#D5DEE5"), 16)
        draw_image_cover(c, path, x + 6, 192, 248, 210, focus_y=.52)
        c.setFillColor(RED)
        c.rect(x + 18, 166, 32, 4, stroke=0, fill=1)
        c.setFillColor(INK)
        c.setFont(FONT_BOLD, 13)
        c.drawString(x + 18, 143, head)
        paragraph(c, body, x + 18, 118, 222, 10.5, 14, SLATE, FONT)
    footer(c, 6)


def slide_07(c: canvas.Canvas) -> None:
    c.setFillColor(WHITE)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    title_block(c, "06 • ВНУТРИ АРЕНЫ", "Навигация и командные пространства")
    photo_card(c, ASSETS / "locker-room.jpg", 58, 214, 510, 190, "РАЗДЕВАЛКИ")
    photo_card(c, ASSETS / "wayfinding-entry.jpg", 58, 66, 247, 130, "ВХОД / МАРШРУТ")
    photo_card(c, ASSETS / "reception-branding.jpg", 321, 66, 247, 130, "РЕСЕПШН")
    rounded_card(c, 598, 66, 304, 338, NAVY, None, 18)
    c.setFillColor(RED)
    c.roundRect(624, 365, 36, 5, 2.5, stroke=0, fill=1)
    paragraph(c, "Единый маршрут\nбез визуального шума", 624, 337, 242, 23, 27, WHITE, FONT_BOLD)
    bullet_list(c, [
        "Крупные указатели в цветах арены",
        "Кодирование зон: поле / раздевалки / кафе / сервис",
        "Номера шкафов и командная графика",
        "Защитная плёнка и брендирование стекла",
        "Подсвеченный знак в ключевой точке входа",
    ], 624, 255, 244, 11, 15, MIST, RED, 7)
    c.setFillColor(STEEL)
    c.setFont(FONT_ITALIC, 9)
    c.drawString(624, 91, "Сначала путь посетителя — затем носители.")
    footer(c, 7)


def slide_08(c: canvas.Canvas) -> None:
    c.setFillColor(NAVY)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    title_block(c, "07 • КОНТЕНТ", "Пресс-зона и фотогеничные точки", dark=True)
    photo_card(c, ASSETS / "press-wall.jpg", 58, 83, 256, 333, "СУЩЕСТВУЮЩИЙ PRESS WALL", focus_y=.53)
    photo_card(c, ASSETS / "ball-plinth.jpg", 330, 83, 256, 333, "ПОДИУМ НА ПОЛЕ", focus_y=.48)
    rounded_card(c, 616, 83, 286, 333, NAVY_2, Color(1, 1, 1, alpha=.15), 18)
    c.setFillColor(RED)
    c.rect(640, 376, 34, 4, stroke=0, fill=1)
    c.setFillColor(WHITE)
    c.setFont(FONT_BOLD, 14)
    c.drawString(640, 350, "СОБРАТЬ МЕДИА-КИТ")
    bullet_list(c, [
        "Модульный фон 3×2,5 м",
        "Интервью-панель у выхода на поле",
        "Пьедестал для мяча и наград",
        "Мобильный знак для командного фото",
        "Партнёрские модули без переделки основы",
    ], 640, 315, 225, 11, 15, MIST, RED, 8)
    c.setFillColor(Color(1, 1, 1, alpha=.08))
    c.roundRect(636, 111, 246, 59, 12, stroke=0, fill=1)
    paragraph(c, "Кадр должен считываться как «Аником Арена» даже без подписи.", 652, 145, 214, 10, 14, WHITE, FONT_BOLD)
    footer(c, 8, dark=True)


def product_icon(c: canvas.Canvas, x: float, y: float, kind: int) -> None:
    c.setStrokeColor(WHITE)
    c.setFillColor(Color(1, 1, 1, alpha=.05))
    c.setLineWidth(2)
    if kind == 1:
        c.roundRect(x, y, 196, 118, 6, stroke=1, fill=1)
        c.line(x + 12, y, x + 4, y - 22)
        c.line(x + 184, y, x + 192, y - 22)
        c.setFillColor(RED)
        c.rect(x + 8, y + 8, 180, 8, stroke=0, fill=1)
        arena_logo(c, x + 68, y + 25, 60, 80)
    elif kind == 2:
        for off in (0, 72, 144):
            c.roundRect(x + off, y, 58, 118, 5, stroke=1, fill=1)
            c.line(x + off + 29, y, x + off + 29, y - 18)
        c.setFillColor(RED)
        c.rect(x + 6, y + 14, 190, 9, stroke=0, fill=1)
    else:
        c.roundRect(x + 10, y + 18, 74, 100, 5, stroke=1, fill=1)
        c.roundRect(x + 110, y + 18, 74, 100, 5, stroke=1, fill=1)
        c.line(x + 47, y + 18, x + 47, y - 18)
        c.line(x + 147, y + 18, x + 147, y - 18)
        c.setFillColor(RED)
        c.circle(x + 47, y + 82, 7, stroke=0, fill=1)
        c.circle(x + 147, y + 82, 7, stroke=0, fill=1)


def slide_09(c: canvas.Canvas) -> None:
    draw_image_cover(c, ASSETS / "field-front.jpg", 0, 0, PAGE_W, PAGE_H, focus_y=.48)
    set_alpha(c, .90)
    c.setFillColor(NAVY)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    reset_alpha(c)
    title_block(c, "08 • КОНСТРУКЦИИ", "Модульный комплект для матчей и событий", dark=True)
    cards = [
        (58, 1, "HERO WALL 5×3 М", "Скрытый каркас, сменное полотно, расчёт балласта после обследования."),
        (341, 2, "ПЛОСКИЕ КАРКАСЫ", "Серийные панели для партнёров, расписания, турниров и временных зон."),
        (624, 3, "НАВИГАЦИЯ / ПОДИУМЫ", "Мобильные указатели, пьедесталы и точки активации в едином стиле."),
    ]
    for x, kind, head, body in cards:
        rounded_card(c, x, 83, 260, 322, Color(.07, .17, .27, alpha=.86), Color(1, 1, 1, alpha=.16), 18)
        product_icon(c, x + 32, 231, kind)
        c.setFillColor(RED)
        c.rect(x + 22, 190, 34, 4, stroke=0, fill=1)
        c.setFillColor(WHITE)
        c.setFont(FONT_BOLD, 13)
        c.drawString(x + 22, 165, head)
        paragraph(c, body, x + 22, 138, 214, 10.5, 14, MIST, FONT)
    c.setFillColor(STEEL)
    c.setFont(FONT_ITALIC, 9)
    c.drawCentredString(480, 54, "Финальные размеры, материалы и узлы крепления определяются после замеров.")
    footer(c, 9, dark=True)


def slide_10(c: canvas.Canvas) -> None:
    c.setFillColor(MIST)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    title_block(c, "09 • ДОРОЖНАЯ КАРТА", "Приоритеты запуска")
    phases = [
        (58, "ЭТАП 1", "БЫСТРЫЕ ИЗМЕНЕНИЯ", RED, ["навигация", "фасад центрального входа", "медиа-башня", "доработка press wall"], "Быстрый рост узнаваемости"),
        (341, "ЭТАП 2", "MATCH-DAY СИСТЕМА", NAVY_3, ["экран и шаблоны", "бровка поля", "подиумы", "интервью-зона"], "Единый образ каждого матча"),
        (624, "ЭТАП 3", "ПАРТНЁРСКИЙ КИТ", GREEN, ["hero wall 5×3 м", "плоские каркасы", "мобильная навигация", "сезонные активации"], "Новые рекламные форматы"),
    ]
    for x, phase, head, color, items, effect in phases:
        rounded_card(c, x, 91, 260, 313, WHITE, HexColor("#D5DEE5"), 18)
        c.setFillColor(color)
        c.roundRect(x + 18, 354, 76, 25, 8, stroke=0, fill=1)
        c.setFillColor(WHITE)
        c.setFont(FONT_BOLD, 9)
        c.drawCentredString(x + 56, 363, phase)
        c.setFillColor(INK)
        c.setFont(FONT_BOLD, 13)
        c.drawString(x + 18, 325, head)
        bullet_list(c, items, x + 18, 289, 220, 11, 15, SLATE, color, 7)
        c.setFillColor(HexColor("#EDF2F5"))
        c.roundRect(x + 18, 114, 224, 42, 10, stroke=0, fill=1)
        c.setFillColor(color)
        c.setFont(FONT_BOLD, 9)
        c.drawString(x + 31, 131, effect.upper())
    paragraph(c, "Очередность можно менять: приоритет задают календарь матчей, партнёры и доступный бюджет.", 58, 62, 830, 10, 14, SLATE, FONT)
    footer(c, 10)


def slide_11(c: canvas.Canvas) -> None:
    draw_image_cover(c, ASSETS / "field-side.jpg", 0, 0, PAGE_W, PAGE_H, focus_y=.45)
    set_alpha(c, .87)
    c.setFillColor(NAVY)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    reset_alpha(c)
    pitch_motif(c, 605, 70, 270, 400, WHITE, .12)
    c.setFillColor(RED)
    c.roundRect(58, 484, 42, 5, 2.5, stroke=0, fill=1)
    c.setFillColor(STEEL)
    c.setFont(FONT_BOLD, 10)
    c.drawString(116, 479, "10 • СЛЕДУЮЩИЙ ШАГ")
    paragraph(c, "Перейти от идеи\nк рабочему проекту", 58, 437, 500, 35, 39, WHITE, FONT_BOLD)
    steps = [
        "Выездной аудит и обмеры",
        "Согласование зон и задач партнёров",
        "2–3 визуальные концепции ключевых точек",
        "Смета, образцы материалов и прототип",
        "Производство и поэтапный монтаж",
    ]
    y = 321
    for i, step in enumerate(steps, 1):
        c.setFillColor(RED)
        c.circle(74, y + 2, 13, stroke=0, fill=1)
        c.setFillColor(WHITE)
        c.setFont(FONT_BOLD, 9)
        c.drawCentredString(74, y - 1, str(i))
        c.setFont(FONT, 12)
        c.drawString(100, y - 3, step)
        y -= 43
    rounded_card(c, 568, 120, 320, 230, Color(.04, .12, .20, alpha=.88), Color(1, 1, 1, alpha=.16), 20)
    arena_logo(c, 598, 185, 112, 150)
    c.setFillColor(WHITE)
    c.setFont(FONT_BOLD, 19)
    c.drawString(724, 290, "НАЧАТЬ")
    c.setFillColor(RED)
    c.setFont(FONT_BOLD, 19)
    c.drawString(724, 263, "С АУДИТА")
    paragraph(c, "После замеров подготовим адресные решения, технические спецификации и расчёт.", 724, 228, 138, 9.5, 13, MIST, FONT)
    c.setFillColor(STEEL)
    c.setFont(FONT_ITALIC, 8)
    c.drawString(58, 45, "Все визуализации концептуальные. Размеры, материалы, крепления и бюджеты уточняются после обследования площадки.")
    sm_logo(c, 820, 12, 86, 70)
    footer(c, 11, dark=True)


def build_pdf() -> None:
    c = canvas.Canvas(str(OUTPUT), pagesize=(PAGE_W, PAGE_H), pageCompression=1)
    c.setTitle("Аником Арена — концепция оформления")
    c.setAuthor("SM Production")
    c.setSubject("Предложение по развитию визуальной системы спортивной площадки")
    c.setCreator("SM Production / Arena.ai")
    slides = [slide_01, slide_02, slide_03, slide_04, slide_05, slide_06, slide_07, slide_08, slide_09, slide_10, slide_11]
    for slide in slides:
        slide(c)
        c.showPage()
    c.save()


def build_preview() -> None:
    doc = pymupdf.open(OUTPUT)
    thumbs: list[Image.Image] = []
    for page in doc:
        pix = page.get_pixmap(matrix=pymupdf.Matrix(.52, .52), alpha=False)
        im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        im = ImageOps.fit(im, (480, 270), Image.Resampling.LANCZOS)
        thumbs.append(im)
    sheet = Image.new("RGB", (1440, 4 * 310), "#D7DEE5")
    font = ImageFont.truetype(str(FONTS / "DejaVuSans-Bold.ttf"), 16)
    draw = ImageDraw.Draw(sheet)
    for idx, thumb in enumerate(thumbs):
        col, row = idx % 3, idx // 3
        x, y = col * 480, row * 310
        sheet.paste(thumb, (x, y))
        draw.rectangle((x, y + 270, x + 480, y + 310), fill="#091A2B")
        draw.text((x + 16, y + 282), f"{idx + 1:02d}", fill="#F6F8FA", font=font)
    sheet.save(PREVIEW, "JPEG", quality=91, optimize=True, progressive=True)


if __name__ == "__main__":
    build_pdf()
    build_preview()
    print(OUTPUT)
    print(PREVIEW)
