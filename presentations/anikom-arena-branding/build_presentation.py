#!/usr/bin/env python3
"""Build a concrete Anikom Arena proposal: placements, designs and specifications."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pymupdf
from PIL import Image, ImageOps, ImageDraw, ImageFont
from reportlab.lib.colors import Color, HexColor
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from build_concept_assets import build as build_concept_assets

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
CONCEPTS = ROOT / "concepts"
FONTS = ROOT / "fonts"
OUTPUT = ROOT / "Anikom-Arena-branding-concept.pdf"
PREVIEW = ROOT / "presentation-preview.jpg"

PAGE_W, PAGE_H = 960, 540
TOTAL_SLIDES = 11

NAVY = HexColor("#091A2B")
NAVY_2 = HexColor("#102B45")
NAVY_3 = HexColor("#173B59")
RED = HexColor("#D94B43")
RED_DARK = HexColor("#A42F35")
WHITE = HexColor("#F6F8FA")
MIST = HexColor("#E7EDF2")
STEEL = HexColor("#A8B5C2")
SLATE = HexColor("#5E7081")
INK = HexColor("#172330")
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


def draw_image_cover(c: canvas.Canvas, path: Path, x: float, y: float, w: float, h: float, focus_x=.5, focus_y=.5) -> None:
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


def lines_for(text: str, font_name: str, size: float, max_width: float) -> list[str]:
    out: list[str] = []
    for para in text.split("\n"):
        words = para.split()
        if not words:
            out.append("")
            continue
        line = words[0]
        for word in words[1:]:
            test = f"{line} {word}"
            if pdfmetrics.stringWidth(test, font_name, size) <= max_width:
                line = test
            else:
                out.append(line)
                line = word
        out.append(line)
    return out


def paragraph(c: canvas.Canvas, text: str, x: float, top: float, max_width: float, size=13, leading=None, color=INK, font_name=FONT) -> float:
    leading = leading or size * 1.35
    c.setFillColor(color)
    c.setFont(font_name, size)
    y = top
    for line in lines_for(text, font_name, size, max_width):
        c.drawString(x, y, line)
        y -= leading
    return y


def bullets(c: canvas.Canvas, items: Iterable[str], x: float, top: float, width: float, size=11, color=INK, dot=RED, leading=15, gap=7) -> float:
    y = top
    for item in items:
        rows = lines_for(item, FONT, size, width - 20)
        c.setFillColor(dot)
        c.circle(x + 3, y + 3, 3, stroke=0, fill=1)
        c.setFillColor(color)
        c.setFont(FONT, size)
        for i, row in enumerate(rows):
            c.drawString(x + 16, y - i * leading, row)
        y -= len(rows) * leading + gap
    return y


def card(c: canvas.Canvas, x: float, y: float, w: float, h: float, fill=WHITE, stroke=None, radius=16, alpha=1) -> None:
    set_alpha(c, alpha, alpha)
    c.setFillColor(fill)
    if stroke:
        c.setStrokeColor(stroke)
        c.setLineWidth(1)
    c.roundRect(x, y, w, h, radius, stroke=1 if stroke else 0, fill=1)
    reset_alpha(c)


def title(c: canvas.Canvas, kicker: str, heading: str, dark=False, size=28) -> None:
    fg = WHITE if dark else INK
    muted = STEEL if dark else SLATE
    c.setFillColor(RED)
    c.roundRect(58, 486, 34, 5, 2.5, stroke=0, fill=1)
    c.setFillColor(muted)
    c.setFont(FONT_BOLD, 10)
    c.drawString(104, 481, kicker.upper())
    paragraph(c, heading, 58, 450, 842, size, size * 1.12, fg, FONT_BOLD)


def footer(c: canvas.Canvas, number: int, dark=False) -> None:
    c.setStrokeColor(Color(1, 1, 1, alpha=.18) if dark else HexColor("#D8E0E6"))
    c.line(58, 28, 902, 28)
    c.setFillColor(Color(1, 1, 1, alpha=.58) if dark else SLATE)
    c.setFont(FONT, 8)
    c.drawString(58, 14, "АНИКОМ АРЕНА • ПРЕДЛОЖЕНИЕ ПО ОФОРМЛЕНИЮ")
    c.drawRightString(902, 14, f"{number:02d} / {TOTAL_SLIDES:02d}")


def arena_logo(c: canvas.Canvas, x: float, y: float, w: float, h: float) -> None:
    draw_image_contain(c, ASSETS / "anikom-arena-logo.png", x, y, w, h)


def sm_logo(c: canvas.Canvas, x: float, y: float, w: float, h: float) -> None:
    draw_image_contain(c, ASSETS / "sm-production-logo.png", x, y, w, h)


def photo(c: canvas.Canvas, path: Path, x: float, y: float, w: float, h: float, label: str | None = None, focus_y=.5) -> None:
    card(c, x, y, w, h, WHITE, HexColor("#D3DDE5"), 12)
    draw_image_cover(c, path, x + 5, y + 5, w - 10, h - 10, focus_y=focus_y)
    if label:
        set_alpha(c, .9)
        c.setFillColor(NAVY)
        tw = pdfmetrics.stringWidth(label, FONT_BOLD, 8.5) + 20
        c.roundRect(x + 13, y + 13, tw, 22, 7, stroke=0, fill=1)
        reset_alpha(c)
        c.setFillColor(WHITE)
        c.setFont(FONT_BOLD, 8.5)
        c.drawString(x + 23, y + 21, label.upper())


def slide_01(c: canvas.Canvas) -> None:
    draw_image_cover(c, ASSETS / "field-front.jpg", 0, 0, PAGE_W, PAGE_H, focus_y=.46)
    set_alpha(c, .82)
    c.setFillColor(NAVY)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    reset_alpha(c)
    c.saveState()
    set_alpha(c, .92)
    c.setFillColor(RED)
    c.transform(1, 0, -.2, 1, 0, 0)
    c.rect(-80, 0, 300, PAGE_H, stroke=0, fill=1)
    c.restoreState()
    reset_alpha(c)
    arena_logo(c, 55, 320, 130, 180)
    c.setFillColor(RED)
    c.roundRect(240, 447, 54, 7, 3, stroke=0, fill=1)
    c.setFillColor(STEEL)
    c.setFont(FONT_BOLD, 10)
    c.drawString(310, 445, "ПЕРЕРАБОТАННОЕ ПРЕДЛОЖЕНИЕ • 2026")
    paragraph(c, "КОНКРЕТНЫЕ РЕШЕНИЯ\nДЛЯ ОФОРМЛЕНИЯ", 240, 397, 600, 39, 43, WHITE, FONT_BOLD)
    c.setFillColor(RED)
    c.setFont(FONT_BOLD, 29)
    c.drawString(240, 285, "АНИКОМ АРЕНЫ")
    paragraph(c, "Телебашня • плоские каркасы • пресс-воллы\nГотовые эскизы и схема размещения", 240, 247, 520, 15, 21, MIST, FONT)
    c.setFillColor(STEEL)
    c.setFont(FONT, 9)
    c.drawString(58, 35, "ПРЕДЛОЖЕНИЕ ДЛЯ ОБСУЖДЕНИЯ И ПОСЛЕДУЮЩИХ ОБМЕРОВ")


def slide_02(c: canvas.Canvas) -> None:
    c.setFillColor(MIST)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    title(c, "01 • СОСТАВ ПРЕДЛОЖЕНИЯ", "Что именно предлагаем изготовить")
    data = [
        (58, "01", "1 БАННЕР", "ТЕЛЕБАШНЯ", "Эскиз, вид на месте и подготовка полотна после обмера."),
        (270, "02", "4 ЗОНЫ", "ПЛОСКИЕ КАРКАСЫ", "Балконная лента, два нижних модуля и центральный вход."),
        (482, "03", "2 ШТУКИ", "ПРЕСС-ВОЛЛЫ", "Партнёрский и матчевый фон размером 3000×2500 мм."),
        (694, "04", "1 ВАРИАНТ", "ФОТОЗОНА 5×3 М", "Скрытый каркас, сменное полотно и расчёт утяжеления."),
    ]
    for x, num, qty, head, body in data:
        card(c, x, 128, 190, 273, WHITE, HexColor("#D4DEE6"), 17)
        c.setFillColor(RED)
        c.circle(x + 28, 365, 16, stroke=0, fill=1)
        c.setFillColor(WHITE)
        c.setFont(FONT_BOLD, 10)
        c.drawCentredString(x + 28, 361, num)
        c.setFillColor(NAVY)
        c.setFont(FONT_BOLD, 22)
        c.drawString(x + 18, 321, qty)
        c.setFillColor(RED)
        c.setFont(FONT_BOLD, 11)
        c.drawString(x + 18, 294, head)
        c.setFillColor(HexColor("#EAF0F4"))
        c.roundRect(x + 18, 228, 154, 48, 10, stroke=0, fill=1)
        paragraph(c, body, x + 18, 203, 154, 10, 14, SLATE, FONT)
    card(c, 58, 66, 826, 42, NAVY, None, 12)
    c.setFillColor(WHITE)
    c.setFont(FONT_BOLD, 11)
    c.drawCentredString(471, 81, "ПРЕДВАРИТЕЛЬНО: 8 НОСИТЕЛЕЙ / 4 ТИПА КОНСТРУКЦИЙ / ЕДИНЫЙ ВНЕШНИЙ ВИД")
    footer(c, 2)


def slide_03(c: canvas.Canvas) -> None:
    c.setFillColor(WHITE)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    title(c, "02 • СХЕМА РАЗМЕЩЕНИЯ", "Где устанавливаются все носители", size=27)
    photo(c, CONCEPTS / "flat-frame-placement-map.jpg", 58, 91, 596, 326, "ГЛАВНАЯ ТРИБУНА", .5)
    card(c, 675, 91, 227, 326, NAVY, None, 16)
    rows = [
        ("К1", "Балконная линия", "несколько секций"),
        ("К2", "Нижний левый", "одна рамка"),
        ("К3", "Нижний правый", "одна рамка"),
        ("К4", "Центральный вход", "одна рамка"),
        ("Б1", "Телебашня", "одно полотно"),
    ]
    y = 379
    for code, place, count in rows:
        c.setFillColor(RED)
        c.roundRect(695, y - 4, 34, 24, 7, stroke=0, fill=1)
        c.setFillColor(WHITE)
        c.setFont(FONT_BOLD, 9)
        c.drawCentredString(712, y + 4, code)
        c.setFont(FONT_BOLD, 10.5)
        c.drawString(741, y + 7, place)
        c.setFillColor(STEEL)
        c.setFont(FONT, 8.5)
        c.drawString(741, y - 7, count)
        y -= 53
    c.setFillColor(Color(1, 1, 1, alpha=.1))
    c.roundRect(692, 108, 193, 54, 11, stroke=0, fill=1)
    paragraph(c, "Размеры, деление рамок и точки крепления уточняются на месте.", 705, 143, 166, 8.5, 12, MIST, FONT)
    footer(c, 3)


def slide_04(c: canvas.Canvas) -> None:
    c.setFillColor(MIST)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    title(c, "03 • УСТРОЙСТВО РАМКИ", "Полотно зажато по всему краю", size=27)
    card(c, 58, 105, 244, 314, NAVY, None, 16)
    c.setFillColor(RED)
    c.rect(76, 384, 34, 4, stroke=0, fill=1)
    c.setFillColor(WHITE)
    c.setFont(FONT_BOLD, 12)
    c.drawString(122, 380, "ЧЕТЫРЕ ЧАСТИ")
    parts = [
        ("1", "Печатное полотно", "плотная баннерная ткань с запасом по краям"),
        ("2", "Прижимные планки", "удерживают край по всему периметру"),
        ("3", "Плоская рамка", "металлическая основа по размеру зоны"),
        ("4", "Скрытые зажимы", "крепят рамку к существующему ограждению"),
    ]
    y = 343
    for num, head, body in parts:
        c.setFillColor(RED)
        c.circle(83, y + 2, 12, stroke=0, fill=1)
        c.setFillColor(WHITE)
        c.setFont(FONT_BOLD, 9)
        c.drawCentredString(83, y - 1, num)
        c.setFont(FONT_BOLD, 9.5)
        c.drawString(105, y + 5, head)
        paragraph(c, body, 105, y - 10, 172, 8.3, 11, STEEL, FONT)
        y -= 65
    card(c, 322, 105, 580, 314, WHITE, HexColor("#D3DDE5"), 14)
    draw_image_contain(c, CONCEPTS / "flat-frame-construction.png", 333, 116, 558, 292)
    c.setFillColor(RED)
    c.setFont(FONT_BOLD, 10)
    c.drawCentredString(480, 73, "ЛИЦЕВАЯ СТОРОНА — РОВНАЯ")
    c.setFillColor(INK)
    c.drawCentredString(714, 73, "НЕТ ВИДИМЫХ ШНУРОВ И ОТВЕРСТИЙ")
    footer(c, 4)


def slide_05(c: canvas.Canvas) -> None:
    c.setFillColor(NAVY)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    title(c, "04 • К1", "Балконная линия: деление по стойкам", dark=True, size=27)
    photo(c, ASSETS / "stand-close.jpg", 500, 199, 402, 222, "МЕСТО УСТАНОВКИ", .5)
    card(c, 58, 199, 414, 222, NAVY_2, Color(1, 1, 1, alpha=.13), 15)
    paragraph(c, "Длинная полоса собирается из отдельных рамок. Границы рамок совпадают со стойками ограждения, поэтому вся линия выглядит цельной.", 78, 384, 372, 12, 17, WHITE, FONT_BOLD)
    bullets(c, [
        "каждая рамка крепится за ограждением скрытыми зажимами",
        "рисунок продолжается с одной секции на другую",
        "стыки полотен находятся на осях стоек",
        "проход и верх ограждения остаются свободными",
    ], 78, 305, 365, 9.5, MIST, RED, 13, 5)
    card(c, 58, 72, 844, 103, NAVY_2, Color(1, 1, 1, alpha=.13), 13)
    draw_image_contain(c, CONCEPTS / "flat-frame-banner-1.png", 76, 87, 480, 73)
    c.setFillColor(WHITE)
    c.setFont(FONT_BOLD, 10.5)
    c.drawString(584, 144, "ПЕРЕД ИЗГОТОВЛЕНИЕМ")
    paragraph(c, "Замеряем общую длину, высоту, шаг стоек и расстояние до прохода. После этого назначаем размер каждой рамки и место каждого зажима.", 584, 122, 292, 9, 12, STEEL, FONT)
    footer(c, 5, dark=True)


def slide_06(c: canvas.Canvas) -> None:
    c.setFillColor(WHITE)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    title(c, "05 • К2–К4", "Нижние модули и центральный вход", size=27)
    card(c, 58, 108, 404, 305, NAVY, None, 15)
    c.setFillColor(RED)
    c.roundRect(76, 374, 132, 24, 7, stroke=0, fill=1)
    c.setFillColor(WHITE)
    c.setFont(FONT_BOLD, 9)
    c.drawCentredString(142, 382, "К2–К3 • 2 ШТУКИ")
    draw_image_contain(c, CONCEPTS / "flat-frame-banner-2.png", 76, 272, 368, 82)
    paragraph(c, "Два одинаковых прямоугольных модуля", 76, 246, 356, 12, 15, WHITE, FONT_BOLD)
    bullets(c, [
        "рамка повторяет границы секции",
        "полотно зажато планками по всему краю",
        "зажимы расположены с обратной стороны",
        "обе части печатаются по одному размеру",
    ], 76, 213, 350, 9.5, MIST, RED, 13, 5)

    card(c, 498, 108, 404, 305, HexColor("#F0F4F7"), HexColor("#D3DDE5"), 15)
    c.setFillColor(RED)
    c.roundRect(516, 374, 116, 24, 7, stroke=0, fill=1)
    c.setFillColor(WHITE)
    c.setFont(FONT_BOLD, 9)
    c.drawCentredString(574, 382, "К4 • 1 ШТУКА")
    draw_image_contain(c, CONCEPTS / "flat-frame-banner-3.png", 516, 272, 368, 82)
    paragraph(c, "Горизонтальный носитель над входом", 516, 246, 356, 12, 15, INK, FONT_BOLD)
    bullets(c, [
        "рамка не перекрывает проход и указатели",
        "рисунок центрируется относительно входа",
        "крепление выполняется к существующим стойкам",
        "высота уточняется после проверки на месте",
    ], 516, 213, 350, 9.5, SLATE, RED, 13, 5)
    c.setFillColor(RED)
    c.setFont(FONT_BOLD, 10)
    c.drawCentredString(480, 73, "ДЛЯ К2–К4 ПРИМЕНЯЕТСЯ ОДИН ПРИНЦИП: ПЛАНКИ ПО КРАЮ И СКРЫТЫЕ ЗАЖИМЫ")
    footer(c, 6)


def slide_07(c: canvas.Canvas) -> None:
    c.setFillColor(NAVY)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    title(c, "06 • Б1", "Баннер для телебашни", dark=True)
    photo(c, CONCEPTS / "tower-banner-mockup.jpg", 58, 77, 434, 350, "ВИД НА МЕСТЕ", .53)
    card(c, 515, 253, 387, 174, NAVY_2, Color(1, 1, 1, alpha=.14), 14)
    draw_image_contain(c, CONCEPTS / "tower-banner-artwork.png", 528, 266, 361, 148)
    c.setFillColor(RED)
    c.rect(515, 232, 42, 5, stroke=0, fill=1)
    c.setFillColor(WHITE)
    c.setFont(FONT_BOLD, 12)
    c.drawString(570, 228, "КАК ИЗГОТАВЛИВАЕМ")
    bullets(c, [
        "плотная матовая баннерная ткань",
        "печать красками, устойчивыми к солнцу и осадкам",
        "край полотна зажат планками на плоской рамке",
        "размер, стыки и крепления — после обмера панели",
    ], 525, 201, 365, 10, MIST, RED, 13, 5)
    c.setFillColor(Color(1, 1, 1, alpha=.09))
    c.roundRect(515, 70, 387, 38, 10, stroke=0, fill=1)
    c.setFillColor(STEEL)
    c.setFont(FONT_BOLD, 8.5)
    c.drawString(532, 84, "НА МЕСТЕ: ШИРИНА, ВЫСОТА, ОПОРА, ДОСТУП И ВЕТРОВАЯ НАГРУЗКА")
    footer(c, 7, dark=True)


def slide_08(c: canvas.Canvas) -> None:
    c.setFillColor(MIST)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    title(c, "07 • Ф1–Ф2", "Два дополнительных пресс-волла")
    card(c, 58, 106, 405, 304, WHITE, HexColor("#D4DEE6"), 15)
    draw_image_contain(c, CONCEPTS / "presswall-partner-3000x2500.png", 71, 176, 379, 222)
    c.setFillColor(NAVY)
    c.setFont(FONT_BOLD, 13)
    c.drawString(76, 148, "Ф1 • ПАРТНЁРСКИЙ • 3000×2500 ММ")
    paragraph(c, "Повторяемый знак арены и сменные места для партнёров.", 76, 128, 350, 9.5, 13, SLATE, FONT)
    card(c, 479, 106, 405, 304, WHITE, HexColor("#D4DEE6"), 15)
    draw_image_contain(c, CONCEPTS / "presswall-matchday-3000x2500.png", 492, 176, 379, 222)
    c.setFillColor(NAVY)
    c.setFont(FONT_BOLD, 13)
    c.drawString(497, 148, "Ф2 • МАТЧЕВЫЙ • 3000×2500 ММ")
    paragraph(c, "Крупный знак, места команд и чистый фон для интервью.", 497, 128, 350, 9.5, 13, SLATE, FONT)
    card(c, 58, 58, 826, 32, NAVY, None, 9)
    c.setFillColor(WHITE)
    c.setFont(FONT_BOLD, 9)
    c.drawCentredString(471, 69, "НЕПРОСВЕЧИВАЮЩЕЕ ПОЛОТНО • РАЗБОРНАЯ ОСНОВА • СМЕННАЯ ПЕЧАТЬ")
    footer(c, 8)


def slide_09(c: canvas.Canvas) -> None:
    c.setFillColor(WHITE)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    title(c, "08 • Ф3 • ДОПОЛНИТЕЛЬНЫЙ ВАРИАНТ", "Фотозона 5000×3000 мм")
    card(c, 58, 107, 574, 301, NAVY, None, 15)
    draw_image_contain(c, CONCEPTS / "photozone-hero-5000x3000.png", 70, 119, 550, 277)
    photo(c, ASSETS / "reception-branding.jpg", 654, 214, 248, 194, "ФИРМЕННЫЙ СТИЛЬ НА АРЕНЕ", .5)
    card(c, 654, 107, 248, 92, NAVY, None, 13)
    c.setFillColor(WHITE)
    c.setFont(FONT_BOLD, 11)
    c.drawString(670, 174, "СОСТАВ")
    bullets(c, [
        "закрытая основа глубиной до 500 мм",
        "сменное полотно",
        "груз по расчёту",
    ], 670, 152, 210, 9, MIST, RED, 11, 3)
    paragraph(c, "Для награждения, командного фото, представления партнёров и мяча.", 58, 82, 560, 10, 14, SLATE, FONT)
    footer(c, 9)


def slide_10(c: canvas.Canvas) -> None:
    c.setFillColor(MIST)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    title(c, "09 • ВЫПОЛНЕННЫЕ ПРОЕКТЫ", "Примеры наших работ")
    examples = [
        (ASSETS / "our-work-hidden-frame.jpg", 58, 249, "ЗАКРЫТАЯ ОСНОВА 5×3 М", "Полотно и рассчитанный груз"),
        (ASSETS / "our-work-flat-frames.jpg", 482, 249, "ПЛОСКИЕ КАРКАСЫ", "Информационные панели"),
        (ASSETS / "our-work-photozone.jpg", 58, 66, "СПОРТИВНАЯ ФОТОЗОНА", "Объёмный декор и искусственный газон"),
        (ASSETS / "our-work-navigation.jpg", 482, 66, "ПЕРЕНОСНЫЕ УКАЗАТЕЛИ", "Устойчивые основания"),
    ]
    for path, x, y, head, sub in examples:
        card(c, x, y, 402, 164, WHITE, HexColor("#D3DDE5"), 13)
        draw_image_cover(c, path, x + 6, y + 6, 220, 152, focus_y=.5)
        c.setFillColor(RED)
        c.rect(x + 244, y + 119, 34, 4, stroke=0, fill=1)
        c.setFillColor(INK)
        c.setFont(FONT_BOLD, 11)
        c.drawString(x + 244, y + 96, head)
        paragraph(c, sub, x + 244, y + 70, 140, 9.5, 13, SLATE, FONT)
    footer(c, 10)


def table_cell(c: canvas.Canvas, x: float, y: float, w: float, h: float, text: str, font_size=8.5, bold=False, fill=None, color=INK) -> None:
    if fill:
        c.setFillColor(fill)
        c.rect(x, y, w, h, stroke=0, fill=1)
    c.setStrokeColor(HexColor("#D4DEE6"))
    c.rect(x, y, w, h, stroke=1, fill=0)
    paragraph(c, text, x + 7, y + h - 14, w - 14, font_size, font_size * 1.25, color, FONT_BOLD if bold else FONT)


def slide_11(c: canvas.Canvas) -> None:
    c.setFillColor(WHITE)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    title(c, "10 • ИТОГОВЫЙ СОСТАВ", "Что войдёт в расчёт после обмера", size=26)
    x0 = 58
    widths = [52, 216, 48, 106, 158]
    headers = ["КОД", "НОСИТЕЛЬ", "КОЛ.", "РАЗМЕР", "РЕШЕНИЕ"]
    xx = x0
    for w, head in zip(widths, headers):
        table_cell(c, xx, 370, w, 34, head, 8, True, NAVY, WHITE)
        xx += w
    rows = [
        ("Б1", "Баннер телебашни", "1", "по обмеру", "полотно, планки, рамка"),
        ("К1", "Балконная линия", "1", "по обмеру", "секционные плоские рамки"),
        ("К2–К3", "Нижние модули", "2", "по обмеру", "полотно, планки, рамка"),
        ("К4", "Центральный вход", "1", "по обмеру", "плоская рамка"),
        ("Ф1–Ф2", "Доп. пресс-воллы", "2", "3000×2500", "полотно и разборная основа"),
        ("Ф3", "Доп. фотозона", "1", "5000×3000", "закрытая основа и груз"),
    ]
    y = 331
    for ridx, row in enumerate(rows):
        xx = x0
        fill = HexColor("#F3F6F8") if ridx % 2 == 0 else WHITE
        for w, value in zip(widths, row):
            table_cell(c, xx, y, w, 39, value, 8.2, False, fill, INK)
            xx += w
        y -= 39
    card(c, 658, 111, 244, 293, NAVY, None, 16)
    c.setFillColor(RED)
    c.rect(676, 367, 34, 4, stroke=0, fill=1)
    c.setFillColor(WHITE)
    c.setFont(FONT_BOLD, 12)
    c.drawString(722, 363, "ЧТО НУЖНО ЗАМЕРИТЬ")
    bullets(c, [
        "ширину и высоту всех зон",
        "шаг стоек ограждения",
        "доступные места для зажимов",
        "расстояние до проходов",
        "условия на открытом воздухе",
        "время для установки",
    ], 676, 330, 202, 10, MIST, RED, 13, 5)
    c.setFillColor(Color(1, 1, 1, alpha=.1))
    c.roundRect(674, 139, 212, 54, 10, stroke=0, fill=1)
    paragraph(c, "После обмера: точные размеры, рабочие макеты и стоимость.", 688, 171, 184, 9, 12, WHITE, FONT_BOLD)
    footer(c, 11)


def build_pdf() -> None:
    build_concept_assets()
    c = canvas.Canvas(str(OUTPUT), pagesize=(PAGE_W, PAGE_H), pageCompression=1)
    c.setTitle("Аником Арена — конкретные решения по оформлению")
    c.setAuthor("SM Production")
    c.setSubject("Телебашня, плоские каркасы, пресс-воллы и примеры работ")
    c.setCreator("SM Production")
    for slide in (slide_01, slide_02, slide_03, slide_04, slide_05, slide_06, slide_07, slide_08, slide_09, slide_10, slide_11):
        slide(c)
        c.showPage()
    c.save()


def build_preview() -> None:
    doc = pymupdf.open(OUTPUT)
    thumbs: list[Image.Image] = []
    for page in doc:
        pix = page.get_pixmap(matrix=pymupdf.Matrix(.52, .52), alpha=False)
        im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        thumbs.append(ImageOps.fit(im, (480, 270), Image.Resampling.LANCZOS))
    rows = (len(thumbs) + 2) // 3
    sheet = Image.new("RGB", (1440, rows * 310), "#D7DEE5")
    fnt = ImageFont.truetype(str(FONTS / "DejaVuSans-Bold.ttf"), 16)
    draw = ImageDraw.Draw(sheet)
    for idx, thumb in enumerate(thumbs):
        x, y = (idx % 3) * 480, (idx // 3) * 310
        sheet.paste(thumb, (x, y))
        draw.rectangle((x, y + 270, x + 480, y + 310), fill="#091A2B")
        draw.text((x + 16, y + 282), f"{idx + 1:02d}", fill="#F6F8FA", font=fnt)
    sheet.save(PREVIEW, "JPEG", quality=91, optimize=True, progressive=True)


if __name__ == "__main__":
    build_pdf()
    build_preview()
    print(OUTPUT)
    print(PREVIEW)
