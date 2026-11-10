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
TOTAL_SLIDES = 9

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
    paragraph(c, "Телебашня • плоские каркасы • пресс-воллы\nГотовые макеты и схема размещения", 240, 247, 520, 15, 21, MIST, FONT)
    c.setFillColor(STEEL)
    c.setFont(FONT, 9)
    c.drawString(58, 35, "КОНЦЕПТ ДЛЯ ОБСУЖДЕНИЯ И ПОСЛЕДУЮЩИХ ОБМЕРОВ")
    sm_logo(c, 810, 18, 98, 80)


def slide_02(c: canvas.Canvas) -> None:
    c.setFillColor(MIST)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    title(c, "01 • СОСТАВ ПРЕДЛОЖЕНИЯ", "Что именно предлагаем изготовить")
    data = [
        (58, "01", "1 БАННЕР", "ТЕЛЕБАШНЯ", "Макет, фотопривязка и подготовка полотна после обмера."),
        (270, "02", "4 ЗОНЫ", "ПЛОСКИЕ КАРКАСЫ", "Балконная лента, два нижних модуля и центральный вход."),
        (482, "03", "2 ШТУКИ", "ПРЕСС-ВОЛЛЫ", "Партнёрский и match-day, рекомендуемый формат 3000×2500 мм."),
        (694, "04", "1 ОПЦИЯ", "ФОТОЗОНА 5×3 М", "Скрытый каркас, сменное полотно и расчёт утяжеления."),
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
    c.drawCentredString(471, 81, "ПРЕДВАРИТЕЛЬНО: 8 НОСИТЕЛЕЙ / 4 ТИПА КОНСТРУКЦИЙ / 1 СИСТЕМА МАКЕТОВ")
    footer(c, 2)


def slide_03(c: canvas.Canvas) -> None:
    c.setFillColor(WHITE)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    title(c, "02 • ПРИВЯЗКА", "Места для баннеров на плоских каркасах", size=27)
    photo(c, CONCEPTS / "flat-frame-placement-map.jpg", 58, 91, 596, 326, "СХЕМА НА ГЛАВНОЙ ТРИБУНЕ", .5)
    card(c, 675, 91, 227, 326, NAVY, None, 16)
    rows = [
        ("F1", "Балконная лента", "1 длинный модуль"),
        ("F2", "Нижний левый", "1 модуль"),
        ("F3", "Нижний правый", "1 модуль"),
        ("F4", "Центральный вход", "1 модуль / вывеска"),
        ("T1", "Телебашня", "1 фронтальный баннер"),
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
    paragraph(c, "Все размеры — только после обмера существующих ограждений.", 705, 141, 166, 8.5, 12, MIST, FONT)
    footer(c, 3)


def slide_04(c: canvas.Canvas) -> None:
    c.setFillColor(NAVY)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    title(c, "03 • T1", "Баннер для телебашни", dark=True)
    photo(c, CONCEPTS / "tower-banner-mockup.jpg", 58, 77, 434, 350, "ФОТОПРИВЯЗКА", .53)
    card(c, 515, 253, 387, 174, NAVY_2, Color(1, 1, 1, alpha=.14), 14)
    draw_image_contain(c, CONCEPTS / "tower-banner-artwork.png", 528, 266, 361, 148)
    c.setFillColor(RED)
    c.rect(515, 232, 42, 5, stroke=0, fill=1)
    c.setFillColor(WHITE)
    c.setFont(FONT_BOLD, 12)
    c.drawString(570, 228, "РЕКОМЕНДУЕМАЯ КОМПЛЕКТАЦИЯ")
    bullets(c, [
        "Матовый banner frontlit 440–510 г/м², полноцветная UV/latex печать",
        "Натяжение на плоский каркас; кромка и люверсы — после выбора узла",
        "Для открытой ветровой зоны вместо frontlit рассмотреть mesh",
        "Размер, стыки и отступы уточнить по фронтальной панели башни",
    ], 525, 201, 365, 10, MIST, RED, 13, 5)
    c.setFillColor(Color(1, 1, 1, alpha=.09))
    c.roundRect(515, 70, 387, 38, 10, stroke=0, fill=1)
    c.setFillColor(STEEL)
    c.setFont(FONT_BOLD, 9)
    c.drawString(532, 84, "К ВЫЕЗДУ: ШИРИНА × ВЫСОТА, ТОЧКИ КРЕПЛЕНИЯ, ВЕТРОВАЯ ЗОНА")
    footer(c, 4, dark=True)


def slide_05(c: canvas.Canvas) -> None:
    c.setFillColor(MIST)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    title(c, "04 • P1 / P2", "Два дополнительных пресс-волла")
    card(c, 58, 106, 405, 304, WHITE, HexColor("#D4DEE6"), 15)
    draw_image_contain(c, CONCEPTS / "presswall-partner-3000x2500.png", 71, 176, 379, 222)
    c.setFillColor(NAVY)
    c.setFont(FONT_BOLD, 13)
    c.drawString(76, 148, "P1 • ПАРТНЁРСКИЙ • 3000×2500 ММ")
    paragraph(c, "Повторяемый модуль логотипа арены + сменные блоки партнёров.", 76, 128, 350, 9.5, 13, SLATE, FONT)
    card(c, 479, 106, 405, 304, WHITE, HexColor("#D4DEE6"), 15)
    draw_image_contain(c, CONCEPTS / "presswall-matchday-3000x2500.png", 492, 176, 379, 222)
    c.setFillColor(NAVY)
    c.setFont(FONT_BOLD, 13)
    c.drawString(497, 148, "P2 • MATCH-DAY • 3000×2500 ММ")
    paragraph(c, "Центральный знак, зона команд и крупная надпись для интервью.", 497, 128, 350, 9.5, 13, SLATE, FONT)
    card(c, 58, 58, 826, 32, NAVY, None, 9)
    c.setFillColor(WHITE)
    c.setFont(FONT_BOLD, 9)
    c.drawCentredString(471, 69, "ПОЛОТНО BLACKOUT / ТРУБНЫЙ ИЛИ СКРЫТЫЙ КАРКАС / СМЕННАЯ ПЕЧАТЬ БЕЗ ЗАМЕНЫ ОСНОВЫ")
    footer(c, 5)


def slide_06(c: canvas.Canvas) -> None:
    c.setFillColor(WHITE)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    title(c, "05 • P3", "Дополнительная фотозона 5000×3000 мм")
    card(c, 58, 107, 574, 301, NAVY, None, 15)
    draw_image_contain(c, CONCEPTS / "photozone-hero-5000x3000.png", 70, 119, 550, 277)
    photo(c, ASSETS / "press-wall.jpg", 654, 214, 248, 194, "СУЩЕСТВУЮЩАЯ ТОЧКА", .5)
    card(c, 654, 107, 248, 92, NAVY, None, 13)
    c.setFillColor(WHITE)
    c.setFont(FONT_BOLD, 11)
    c.drawString(670, 174, "КОМПЛЕКТАЦИЯ")
    bullets(c, [
        "скрытый каркас глубиной до 500 мм",
        "сменное полотно",
        "утяжеление по расчёту",
    ], 670, 152, 210, 9, MIST, RED, 11, 3)
    paragraph(c, "Назначение: награждение, командное фото, презентация партнёров и мяча.", 58, 82, 560, 10, 14, SLATE, FONT)
    footer(c, 6)


def slide_07(c: canvas.Canvas) -> None:
    c.setFillColor(NAVY)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    title(c, "06 • F1–F4", "Три типа полотен для плоских каркасов", dark=True)
    items = [
        (CONCEPTS / "flat-frame-banner-1.png", "ПОСТОЯННАЯ ФИРМЕННАЯ ЛЕНТА", "логотип арены, без дат и партнёров"),
        (CONCEPTS / "flat-frame-banner-2.png", "ПАРТНЁРСКАЯ ЛИНИЯ", "сменные логотипы на сезон или турнир"),
        (CONCEPTS / "flat-frame-banner-3.png", "СОБЫТИЙНОЕ ПОЛОТНО", "турнир, расписание, счёт, навигация"),
    ]
    y = 330
    for path, head, sub in items:
        card(c, 58, y, 570, 85, NAVY_2, Color(1, 1, 1, alpha=.12), 11)
        draw_image_contain(c, path, 69, y + 10, 548, 65)
        c.setFillColor(WHITE)
        c.setFont(FONT_BOLD, 11)
        c.drawString(654, y + 48, head)
        c.setFillColor(STEEL)
        c.setFont(FONT, 9)
        c.drawString(654, y + 28, sub)
        y -= 105
    card(c, 648, 83, 254, 116, NAVY_2, Color(1, 1, 1, alpha=.12), 13)
    c.setFillColor(RED)
    c.rect(664, 170, 34, 4, stroke=0, fill=1)
    c.setFillColor(WHITE)
    c.setFont(FONT_BOLD, 11)
    c.drawString(710, 166, "ПРОИЗВОДСТВО")
    bullets(c, [
        "баннер или mesh по ветровой зоне",
        "плоский окрашенный каркас",
        "сменное полотно на шнуровке",
    ], 664, 142, 220, 9, MIST, RED, 11, 3)
    footer(c, 7, dark=True)


def slide_08(c: canvas.Canvas) -> None:
    c.setFillColor(MIST)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    title(c, "07 • РЕАЛИЗОВАНО SM PRODUCTION", "Примеры наших работ")
    examples = [
        (ASSETS / "our-work-hidden-frame.jpg", 58, 249, "СКРЫТЫЙ КАРКАС 5×3 М", "Полотно + утяжеление"),
        (ASSETS / "our-work-flat-frames.jpg", 482, 249, "ПЛОСКИЕ КАРКАСЫ", "Информационные панели"),
        (ASSETS / "our-work-photozone.jpg", 58, 66, "СПОРТИВНАЯ ФОТОЗОНА", "Объёмный декор и искусственный газон"),
        (ASSETS / "our-work-navigation.jpg", 482, 66, "МОБИЛЬНАЯ НАВИГАЦИЯ", "Указатели на устойчивых основаниях"),
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
    footer(c, 8)


def table_cell(c: canvas.Canvas, x: float, y: float, w: float, h: float, text: str, font_size=8.5, bold=False, fill=None, color=INK) -> None:
    if fill:
        c.setFillColor(fill)
        c.rect(x, y, w, h, stroke=0, fill=1)
    c.setStrokeColor(HexColor("#D4DEE6"))
    c.rect(x, y, w, h, stroke=1, fill=0)
    paragraph(c, text, x + 7, y + h - 14, w - 14, font_size, font_size * 1.25, color, FONT_BOLD if bold else FONT)


def slide_09(c: canvas.Canvas) -> None:
    c.setFillColor(WHITE)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    title(c, "08 • КОМПЛЕКТАЦИЯ", "Предварительная ведомость и данные для расчёта", size=26)
    x0, y0 = 58, 111
    widths = [48, 230, 48, 112, 142]
    headers = ["ID", "НОСИТЕЛЬ", "КОЛ.", "РАЗМЕР", "МАТЕРИАЛ / ОСНОВА"]
    xx = x0
    for w, head in zip(widths, headers):
        table_cell(c, xx, 370, w, 34, head, 8, True, NAVY, WHITE)
        xx += w
    rows = [
        ("T1", "Баннер телебашни", "1", "по обмеру", "frontlit / mesh + каркас"),
        ("F1", "Балконная лента", "1", "по обмеру", "баннер / mesh"),
        ("F2–F3", "Нижние модули", "2", "по обмеру", "баннер + плоский каркас"),
        ("F4", "Центральный вход", "1", "по обмеру", "баннер или листовой носитель"),
        ("P1–P2", "Доп. пресс-воллы", "2", "3000×2500", "blackout + сборный каркас"),
        ("P3", "Hero photozone", "опция", "5000×3000", "скрытый каркас + балласт"),
    ]
    y = 331
    for ridx, row in enumerate(rows):
        xx = x0
        fill = HexColor("#F3F6F8") if ridx % 2 == 0 else WHITE
        for w, value in zip(widths, row):
            table_cell(c, xx, y, w, 39, value, 8.2, ridx == 0 and False, fill, INK)
            xx += w
        y -= 39
    card(c, 658, 111, 244, 293, NAVY, None, 16)
    c.setFillColor(RED)
    c.rect(676, 367, 34, 4, stroke=0, fill=1)
    c.setFillColor(WHITE)
    c.setFont(FONT_BOLD, 12)
    c.drawString(722, 363, "ДЛЯ ТОЧНОЙ СМЕТЫ")
    bullets(c, [
        "обмеры всех пяти зон",
        "допустимые точки крепления",
        "информация по ветровой нагрузке",
        "логотипы партнёров в векторе",
        "даты ближайших матчей и событий",
        "требования к монтажному времени",
    ], 676, 330, 202, 10, MIST, RED, 13, 5)
    c.setFillColor(Color(1, 1, 1, alpha=.1))
    c.roundRect(674, 139, 212, 54, 10, stroke=0, fill=1)
    paragraph(c, "После обмеров: финальные макеты, техспецификация и смета.", 688, 171, 184, 9, 12, WHITE, FONT_BOLD)
    footer(c, 9)


def build_pdf() -> None:
    build_concept_assets()
    c = canvas.Canvas(str(OUTPUT), pagesize=(PAGE_W, PAGE_H), pageCompression=1)
    c.setTitle("Аником Арена — конкретные решения по оформлению")
    c.setAuthor("SM Production")
    c.setSubject("Телебашня, плоские каркасы, пресс-воллы и примеры работ")
    c.setCreator("SM Production / Arena.ai")
    for slide in (slide_01, slide_02, slide_03, slide_04, slide_05, slide_06, slide_07, slide_08, slide_09):
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
    sheet = Image.new("RGB", (1440, 3 * 310), "#D7DEE5")
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
