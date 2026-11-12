#!/usr/bin/env python3
"""Обучающие наклейки для дома: 60 предметов, английское слово первым.

На наклейке сверху — английское название жирным, под ним русское.
Иконка векторная, контур реза — малиновая линия с вылетом краски 0,8 мм.

Что в PDF:
  * обложка с инструкцией и легендой контура;
  * 5 печатных листов A4 по 12 наклеек;
  * 5 листов только с контурами реза (для плоттера);
  * страница слов по комнатам.

Запуск из корня репозитория:
    .venv/bin/python production/home-stickers-bilingual/build_stickers.py
"""

from __future__ import annotations

import math
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
OUT = HERE / "SM-Production-home-stickers-bilingual.pdf"

FONT_DIR = Path("/tmp/fonts-stickers")
FONT_SRC = REPO / "banners/anikom-arena-3000x2500-concepts/source/Montserrat-Variable.ttf"

# ── геометрия ───────────────────────────────────────────────────────────────
PW, PH = A4
R_CUT = 23.5 * mm          # радиус по линии реза
R_BLEED = 24.3 * mm        # вылет краски за рез
R_RING = 20.0 * mm         # внутреннее кольцо
LOBE_N = 22                # число «лепестков» фестона
LOBE_AMP = 1.05 * mm       # амплитуда фестона
PITCH = 60 * mm            # шаг сетки
COLS, ROWS = 3, 4
PER_SHEET = COLS * ROWS

CUT_COLOR = colors.HexColor("#FF00FF")   # 100 % magenta — контур реза
INK = colors.HexColor("#1B1A18")
PAPER = colors.white


# ── шрифты ──────────────────────────────────────────────────────────────────
def register_fonts() -> None:
    FONT_DIR.mkdir(parents=True, exist_ok=True)
    for name, weight in [("Regular", 400), ("Medium", 500),
                         ("SemiBold", 600), ("Bold", 700)]:
        out = FONT_DIR / f"Montserrat-{name}.ttf"
        if out.exists() and out.stat().st_size > 500_000:
            continue
        from fontTools.ttLib import TTFont as FTFont
        from fontTools.varLib.instancer import instantiateVariableFont
        static = instantiateVariableFont(FTFont(str(FONT_SRC)), {"wght": weight},
                                         updateFontNames=True)
        static.save(str(out))
    for alias, suffix in [("M", "Regular"), ("MM", "Medium"),
                          ("MS", "SemiBold"), ("MB", "Bold")]:
        pdfmetrics.registerFont(TTFont(alias, str(FONT_DIR / f"Montserrat-{suffix}.ttf")))


register_fonts()


def mix(c1: colors.Color, c2: colors.Color, t: float) -> colors.Color:
    return colors.Color(c1.red + (c2.red - c1.red) * t,
                        c1.green + (c2.green - c1.green) * t,
                        c1.blue + (c2.blue - c1.blue) * t)


# ── палитра по группам ──────────────────────────────────────────────────────
PALETTE = {
    "furniture": dict(tint="#FBEFE3", ink="#3A2A1E", accent="#DE8B44"),
    "appliance": dict(tint="#EAF1FA", ink="#1D2733", accent="#4A88C7"),
    "house":     dict(tint="#EBF4EC", ink="#1F2C22", accent="#57A068"),
    "bath":      dict(tint="#E6F4F5", ink="#153033", accent="#38A0A8"),
    "kitchen":   dict(tint="#FBF2E0", ink="#332819", accent="#D29230"),
    "room":      dict(tint="#F0ECF9", ink="#28223D", accent="#8575CB"),
    "school":    dict(tint="#FCE7F0", ink="#33202B", accent="#C25A85"),
}
PALETTE = {k: {kk: colors.HexColor(vv) for kk, vv in v.items()} for k, v in PALETTE.items()}


# ── примитивы ───────────────────────────────────────────────────────────────
def setup_ink(c: canvas.Canvas, color, lw: float = 5.2) -> None:
    c.setStrokeColor(color)
    c.setFillColor(color)
    c.setLineWidth(lw)
    c.setLineCap(1)
    c.setLineJoin(1)


def rr(c, x0, y0, x1, y1, r=0, fill=0):
    if r:
        c.roundRect(x0, y0, x1 - x0, y1 - y0, r, stroke=1, fill=fill)
    else:
        c.rect(x0, y0, x1 - x0, y1 - y0, stroke=1, fill=fill)


def ln(c, x0, y0, x1, y1):
    c.line(x0, y0, x1, y1)


def circ(c, x, y, r, fill=0):
    c.circle(x, y, r, stroke=1, fill=fill)


def poly(c, pts, close=True, fill=0):
    p = c.beginPath()
    p.moveTo(*pts[0])
    for pt in pts[1:]:
        p.lineTo(*pt)
    if close:
        p.close()
    c.drawPath(p, stroke=1, fill=fill)


def curve(c, pts):
    """Кривая по опорным точкам (Catmull-Rom → кубические Безье)."""
    p = c.beginPath()
    p.moveTo(*pts[0])
    for i in range(len(pts) - 1):
        x0, y0 = pts[i]
        x1, y1 = pts[i + 1]
        p.curveTo(x0, y0, x1, y1, x1, y1)
    c.drawPath(p, stroke=1, fill=0)


# ── иконки: система координат 100×100, центр (0, 0) ─────────────────────────
# мебель
def i_table(c, ink, acc):
    rr(c, -42, 10, 42, 21, 3)
    rr(c, -34, -38, -26, 12, 3)
    rr(c, 26, -38, 34, 12, 3)
    ln(c, -26, -24, 26, -24)


def i_chair(c, ink, acc):
    rr(c, -23, 9, 23, 38, 6)            # спинка
    rr(c, -28, -2, 28, 9, 3)            # сиденье
    ln(c, -22, -2, -30, -38)            # ножки
    ln(c, 22, -2, 30, -38)
    setup_ink(c, acc, 3.6)
    ln(c, -27, -19, 27, -19)            # проножка


def i_armchair(c, ink, acc):
    rr(c, -34, -4, 34, 36, 13)
    rr(c, -44, -20, -30, 14, 8)
    rr(c, 30, -20, 44, 14, 8)
    rr(c, -32, -22, 32, -4, 5)
    setup_ink(c, ink, 4.2)
    ln(c, -26, -22, -26, -34)
    ln(c, 26, -22, 26, -34)
    setup_ink(c, acc, 2.8)
    ln(c, -24, 22, 24, 22)


def i_bed(c, ink, acc):
    rr(c, -42, -18, -33, 32, 5)         # изголовье
    rr(c, -33, -12, 40, 8, 3)           # каркас
    rr(c, -33, 8, 40, 18, 5)            # матрас
    rr(c, -28, 18, 2, 27, 4)            # подушка
    rr(c, 6, 18, 40, 25, 4)             # одеяло
    rr(c, 36, -16, 41, 8, 2)            # изножье
    ln(c, -29, -12, -29, -20)
    ln(c, 34, -12, 34, -20)


def i_sofa(c, ink, acc):
    rr(c, -36, 2, 36, 26, 8)
    rr(c, -44, -12, -32, 20, 6)
    rr(c, 32, -12, 44, 20, 6)
    rr(c, -34, -12, 34, 2, 4)
    rr(c, -30, -38, -24, -12, 2)
    rr(c, 24, -38, 30, -12, 2)
    setup_ink(c, acc, 2.6)
    ln(c, -12, 14, -12, 26)                # стык подушек
    ln(c, 12, 14, 12, 26)
    setup_ink(c, ink)


def i_wardrobe(c, ink, acc):
    rr(c, -30, -38, 30, 38, 4)
    ln(c, 0, -38, 0, 38)
    setup_ink(c, acc, 4.2)
    ln(c, -5, -3, -5, 9)
    ln(c, 5, -3, 5, 9)
    setup_ink(c, ink)
    rr(c, -22, 20, -7, 30, 2)
    rr(c, 7, 20, 22, 30, 2)


def i_shelf(c, ink, acc):
    rr(c, -38, -38, -32, 38, 2)         # стойки
    rr(c, 32, -38, 38, 38, 2)
    rr(c, -38, 6, 38, 12, 1)            # полки
    rr(c, -38, -16, 38, -10, 1)
    rr(c, -38, -38, 38, -32, 1)
    for x, h, w in [(-27, 17, 8), (-18, 24, 7), (-10, 20, 8), (0, 26, 7), (9, 15, 8)]:
        rr(c, x, 12, x + w, 12 + h, 1)  # книги
    setup_ink(c, acc, 2.2)
    rr(c, -18, 12, -11, 36, 1, fill=1)  # цветной корешок
    setup_ink(c, ink)


def i_dresser(c, ink, acc):
    rr(c, -30, -38, 30, 34, 4)
    for y in (12, -6, -22):
        ln(c, -30, y, 30, y)
        setup_ink(c, acc, 4)
        ln(c, -7, y - 7, 7, y - 7)
        setup_ink(c, ink)


def i_nightstand(c, ink, acc):
    rr(c, -26, -30, 26, 32, 4)
    setup_ink(c, acc, 2.8)
    ln(c, -26, 2, 26, 2)
    ln(c, -26, 18, 26, 18)
    setup_ink(c, ink, 3)
    circ(c, 0, 10, 2.4, fill=1)
    circ(c, 0, 25, 2.4, fill=1)
    setup_ink(c, ink, 4.4)
    ln(c, -20, -30, -20, -38)
    ln(c, 20, -30, 20, -38)


def i_stool(c, ink, acc):
    c.ellipse(-26, 16, 26, 34, stroke=1, fill=0)
    ln(c, -18, 16, -26, -38)
    ln(c, 18, 16, 26, -38)
    ln(c, -22, 20, 22, 20)
    setup_ink(c, acc, 4)
    ln(c, -20, -14, 20, -14)
    setup_ink(c, ink)


def shoe(c, x, y, w=34, h=18, fill=0):
    """Ботинок в профиль: высокий задник слева, низкий носок справа."""
    p = c.beginPath()
    p.moveTo(x, y)
    p.lineTo(x + w * 0.58, y)
    p.curveTo(x + w * 0.84, y, x + w, y + h * 0.16, x + w, y + h * 0.38)
    p.lineTo(x + w * 0.72, y + h * 0.5)
    p.curveTo(x + w * 0.5, y + h * 0.62, x + w * 0.4, y + h, x + w * 0.22, y + h)
    p.lineTo(x, y + h)
    p.close()
    c.drawPath(p, stroke=1, fill=fill)


def i_shoerack(c, ink, acc):
    rr(c, -36, -40, -31, 34, 2)             # стойки
    rr(c, 31, -40, 36, 34, 2)
    setup_ink(c, ink, 3.4)
    ln(c, -36, 34, 36, 34)                  # полки
    ln(c, -36, 2, 36, 2)
    ln(c, -36, -26, 36, -26)
    setup_ink(c, acc, 1)
    shoe(c, -32, 34, w=32, h=16, fill=1)
    shoe(c, 2, 34, w=32, h=16, fill=1)
    shoe(c, -32, 2, w=32, h=16, fill=1)
    shoe(c, 2, 2, w=32, h=16, fill=1)
    shoe(c, -32, -26, w=32, h=16, fill=1)
    shoe(c, 2, -26, w=32, h=16, fill=1)


def i_hanger(c, ink, acc):
    p = c.beginPath()
    p.moveTo(0, 36)
    p.curveTo(-11, 36, -11, 24, 0, 24)
    c.drawPath(p, stroke=1, fill=0)
    ln(c, 0, 24, 0, 14)
    poly(c, [(0, 14), (-38, -14), (-38, -20), (0, 4), (38, -20), (38, -14)], close=True)
    setup_ink(c, acc, 3)
    ln(c, -26, -26, 26, -26)
    ln(c, -26, -26, -38, -20)
    ln(c, 26, -26, 38, -20)
    setup_ink(c, ink)


# техника
def i_fridge(c, ink, acc):
    rr(c, -26, -42, 26, 42, 7)
    ln(c, -26, 16, 26, 16)
    setup_ink(c, acc, 4.4)
    ln(c, 18, 22, 18, 34)
    ln(c, 18, -1, 18, 11)
    setup_ink(c, ink)


def i_stove(c, ink, acc):
    # плита сверху: четыре конфорки
    rr(c, -34, -34, 34, 34, 5)
    for x in (-17, 17):
        for y in (-17, 17):
            circ(c, x, y, 12)
            setup_ink(c, acc, 3)
            circ(c, x, y, 5)
            setup_ink(c, ink, 4.6)


def i_oven(c, ink, acc):
    rr(c, -38, -34, 38, 34, 5)
    setup_ink(c, ink, 3)
    ln(c, -38, 12, 38, 12)                 # разделитель панели
    for x in (-24, 0, 24):                 # крутилки
        circ(c, x, 24, 5.4)
    rr(c, -30, -28, 30, 4, 3)              # дверца
    setup_ink(c, acc, 3)
    rr(c, -24, -20, 24, -4, 2)             # окно дверцы
    setup_ink(c, acc, 5)                   # ручка
    ln(c, -30, 6, 30, 6)
    setup_ink(c, ink)


def i_microwave(c, ink, acc):
    rr(c, -40, -24, 40, 26, 4)             # корпус
    rr(c, -35, -18, 16, 20, 2)             # дверца
    setup_ink(c, acc, 3)
    rr(c, -29, -12, 10, 14, 1)             # стекло
    setup_ink(c, ink, 7)
    ln(c, 22, -12, 22, 14)                 # ручка
    setup_ink(c, acc, 2.8)
    for y in (13, 5, -3, -11):             # кнопки
        circ(c, 31, y, 2.4, fill=1)
    setup_ink(c, ink)
    ln(c, -32, -24, -32, -29)              # ножки
    ln(c, 32, -24, 32, -29)


def i_kettle(c, ink, acc):
    p = c.beginPath()                       # округлый корпус
    p.moveTo(-22, -8)
    p.curveTo(-22, -24, -12, -30, 0, -30)
    p.curveTo(12, -30, 22, -24, 22, -8)
    p.curveTo(22, 0, 18, 6, 12, 8)
    p.lineTo(-12, 8)
    p.curveTo(-18, 6, -22, 0, -22, -8)
    p.close()
    c.drawPath(p, stroke=1, fill=0)
    ln(c, -12, 8, 12, 8)                    # крышка
    p2 = c.beginPath()                      # короткий широкий носик
    p2.moveTo(17, -7)
    p2.lineTo(35, 6)
    p2.lineTo(39, -1)
    p2.lineTo(21, -18)
    p2.close()
    c.drawPath(p2, stroke=1, fill=0)
    c.arc(-19, -16, 19, 36, 0, 180)         # ручка
    setup_ink(c, acc, 3.4)
    circ(c, 0, 13, 3.6)                     # кнопка крышки
    setup_ink(c, ink)


def i_tv(c, ink, acc):
    rr(c, -40, -14, 40, 32, 6)
    rr(c, -6, -24, 6, -14, 2)
    rr(c, -24, -31, 24, -24, 3)
    setup_ink(c, acc, 3.4)
    ln(c, -32, 24, -18, 24)
    setup_ink(c, ink)


def i_computer(c, ink, acc):
    rr(c, -38, -2, 38, 34, 4)              # монитор
    setup_ink(c, acc, 2.6)
    rr(c, -31, 5, 31, 26, 1)               # экран
    setup_ink(c, ink, 4.6)
    ln(c, 0, -2, 0, -11)                   # ножка
    rr(c, -14, -19, 14, -11, 3)            # подставка
    rr(c, -38, -36, 24, -25, 2)            # клавиатура
    setup_ink(c, acc, 2.2)
    for y in (-28, -31, -34):
        ln(c, -34, y, 20, y)               # ряды клавиш
    c.ellipse(27, -38, 39, -26, stroke=1, fill=0)   # мышь
    ln(c, 33, -32, 33, -28)
    setup_ink(c, ink)


def i_speaker(c, ink, acc):
    rr(c, -27, -40, 27, 40, 5)             # корпус
    circ(c, 0, -14, 16)                    # вуфер
    setup_ink(c, acc, 3)
    circ(c, 0, -14, 7)
    setup_ink(c, ink, 4)
    circ(c, 0, 18, 8)                      # твитер
    setup_ink(c, acc, 2.4)
    circ(c, 0, 18, 3)
    setup_ink(c, ink, 3.2)
    ln(c, -13, 33, 13, 33)                 # верхняя панель
    ln(c, -20, -40, -20, -44)              # ножки
    ln(c, 20, -40, 20, -44)
    setup_ink(c, ink)


def i_washer(c, ink, acc):
    rr(c, -28, -38, 28, 36, 6)
    ln(c, -28, 18, 28, 18)
    circ(c, 0, -8, 17)
    circ(c, 0, -8, 11)
    setup_ink(c, acc, 4)
    circ(c, -14, 27, 3.6)
    ln(c, 2, 27, 18, 27)
    setup_ink(c, ink)


def i_lamp(c, ink, acc):
    poly(c, [(-27, 10), (27, 10), (16, 34), (-16, 34)])
    ln(c, 0, -18, 0, 10)
    c.ellipse(-21, -30, 21, -18, stroke=1, fill=0)
    setup_ink(c, acc, 3.4)
    ln(c, -12, 18, 12, 18)
    setup_ink(c, ink)


# дом
def i_window(c, ink, acc):
    rr(c, -32, -36, 32, 36, 2)
    ln(c, -32, 0, 32, 0)
    ln(c, 0, -36, 0, 36)
    setup_ink(c, acc, 3.2)
    circ(c, -16, 18, 6)
    for a in range(0, 360, 45):
        x1 = -16 + 10 * math.cos(math.radians(a))
        y1 = 18 + 10 * math.sin(math.radians(a))
        x2 = -16 + 13 * math.cos(math.radians(a))
        y2 = 18 + 13 * math.sin(math.radians(a))
        ln(c, x1, y1, x2, y2)
    setup_ink(c, ink)


def i_windowsill(c, ink, acc):
    rr(c, -30, 18, 30, 42, 2)               # окно
    ln(c, -30, 30, 30, 30)                  # горбыль
    ln(c, 0, 18, 0, 42)
    setup_ink(c, acc, 1)
    rr(c, -42, 8, 42, 18, 2, fill=1)        # доска подоконника
    setup_ink(c, ink, 2.6)
    ln(c, -42, 8, 42, 8)                    # кромка доски
    setup_ink(c, ink, 2)
    ln(c, -34, 8, -34, -6)                  # стена под подоконником
    ln(c, 34, 8, 34, -6)
    setup_ink(c, acc, 2)
    ln(c, -34, -6, 34, -6)


def i_door(c, ink, acc):
    rr(c, -34, -32, 34, 40, 2)             # коробка
    rr(c, -29, -28, 29, 36, 2)             # полотно
    rr(c, -18, 4, 18, 26, 2)               # филёнка
    setup_ink(c, acc, 6)                   # ручка
    circ(c, 21, 0, 3.8, fill=1)
    setup_ink(c, acc, 3.4)
    ln(c, -44, -32, 44, -32)               # порог


def i_curtain(c, ink, acc):
    setup_ink(c, ink, 4.4)
    ln(c, -42, 36, 42, 36)                 # карниз
    circ(c, -42, 36, 3.2, fill=1)
    circ(c, 42, 36, 3.2, fill=1)
    setup_ink(c, ink, 4.4)
    for s in (-1, 1):
        p = c.beginPath()
        p.moveTo(s * 34, 36)
        p.lineTo(s * 8, 36)
        p.lineTo(s * 8, -20)
        p.curveTo(s * 18, -32, s * 26, -14, s * 34, -26)
        p.close()
        c.drawPath(p, stroke=1, fill=0)
    setup_ink(c, acc, 2.6)
    for s in (-1, 1):
        ln(c, s * 21, 34, s * 21, -24)


def i_stairs(c, ink, acc):
    w, h = 19, 19
    x0, y0 = -38, -34
    for i in range(4):
        setup_ink(c, ink, 4.2)
        c.rect(x0 + i * w, y0, w, (i + 1) * h, stroke=1, fill=0)
    setup_ink(c, acc, 3.6)
    ln(c, -44, -34, 44, -34)


def i_rug(c, ink, acc):
    rr(c, -33, -26, 33, 26, 4)
    setup_ink(c, acc, 2.4)
    rr(c, -25, -18, 25, 18, 2)              # кайма
    for x in (-13, 0, 13):                  # ромбы
        poly(c, [(x, 11), (x + 6, 0), (x, -11), (x - 6, 0)])
    setup_ink(c, ink, 2.4)
    for y in range(-24, 25, 4):             # бахрома
        ln(c, -41, y, -34, y)
        ln(c, 34, y, 41, y)


def i_basket(c, ink, acc):
    poly(c, [(-28, -34), (28, -34), (22, 4), (-22, 4)])
    p = c.beginPath()
    p.moveTo(-22, 4)
    p.curveTo(-20, 30, 20, 30, 22, 4)
    c.drawPath(p, stroke=1, fill=0)
    setup_ink(c, acc, 3.2)
    for x in (-12, 0, 12):
        ln(c, x, -30, x * 0.85, 1)
    ln(c, -26, -18, 26, -18)
    setup_ink(c, ink)


def i_plant(c, ink, acc):
    poly(c, [(-19, -40), (19, -40), (15, -14), (-15, -14)])
    setup_ink(c, ink, 4.6)
    ln(c, 0, -14, 0, 20)
    for ang, cy_ in [(-58, -2), (58, -2), (-30, 16), (30, 16)]:
        c.saveState()
        c.translate(0, cy_)
        c.rotate(ang)
        c.setFillColor(acc)
        c.setStrokeColor(acc)
        c.setLineWidth(0.6)
        c.ellipse(-6, 2, 6, 30, stroke=1, fill=1)
        c.restoreState()
    setup_ink(c, acc, 3.2)
    ln(c, -15, -22, 15, -22)


def i_switch(c, ink, acc):
    rr(c, -26, -30, 26, 30, 6)
    setup_ink(c, acc, 5)
    rr(c, -12, -14, 12, 16, 4)
    setup_ink(c, acc, 4)
    ln(c, 0, -14, 0, 16)
    setup_ink(c, ink)
    circ(c, -22, 25, 2.2, fill=1)
    circ(c, 22, 25, 2.2, fill=1)


def i_socket(c, ink, acc):
    rr(c, -28, -28, 28, 28, 10)
    setup_ink(c, acc, 5)
    circ(c, -8, 4, 4.4, fill=1)
    circ(c, 8, 4, 4.4, fill=1)
    ln(c, -11, -12, 11, -12)
    setup_ink(c, ink)


def i_radiator(c, ink, acc):
    rr(c, -40, -22, 40, 22, 5)
    for x in (-30, -18, -6, 6, 18, 30):
        ln(c, x, -22, x, 22)
    setup_ink(c, acc, 4)
    ln(c, -38, 0, 38, 0)
    setup_ink(c, ink)


def i_floor(c, ink, acc):
    rr(c, -42, 26, 42, 40, 2)               # стена
    rr(c, -42, -40, 42, 26, 2)              # пол
    setup_ink(c, acc, 2.6)
    for y in (8, -12, -32):                 # стыки досок
        ln(c, -42, y, 42, y)
    for x, y0, y1 in [(-24, -40, -12), (6, -40, -12), (-8, -12, 8),
                      (22, -12, 8), (-30, 8, 26), (12, 8, 26)]:
        ln(c, x, y0, x, y1)                 # торцы досок
    setup_ink(c, ink, 4)
    ln(c, -42, 26, 42, 26)                  # плинтус
    setup_ink(c, acc, 2.6)
    ln(c, -42, 21, 42, 21)


# ванная
def i_mirror(c, ink, acc):
    c.ellipse(-26, -36, 26, 36, stroke=1, fill=0)
    setup_ink(c, acc, 3.2)
    c.ellipse(-19, -29, 19, 29, stroke=1, fill=0)
    ln(c, -12, 16, -2, 26)
    ln(c, -12, 4, 4, 20)
    setup_ink(c, ink)


def i_bath(c, ink, acc):
    rr(c, -40, -16, 40, 14, 14)
    ln(c, -40, 6, 40, 6)
    rr(c, -30, -30, -24, -16, 2)
    rr(c, 24, -30, 30, -16, 2)
    setup_ink(c, acc, 4)
    ln(c, 28, 14, 28, 30)
    ln(c, 28, 30, 14, 30)
    setup_ink(c, ink)


def i_sink(c, ink, acc):
    rr(c, -34, -8, 34, 10, 9)               # чаша
    setup_ink(c, acc, 2.8)
    rr(c, -27, -3, 27, 6, 5)                # внутренняя чаша
    setup_ink(c, ink, 4)
    ln(c, 0, 10, 0, 30)                     # стойка крана
    ln(c, 0, 30, 16, 30)
    ln(c, 16, 30, 16, 21)
    setup_ink(c, ink, 3.2)
    poly(c, [(-11, -8), (11, -8), (7, -38), (-7, -38)])     # пьедестал


def i_shower(c, ink, acc):
    ln(c, 30, 42, 30, 32)                   # труба
    ln(c, 30, 32, 6, 32)
    ln(c, 6, 32, 6, 30)
    poly(c, [(-13, 30), (13, 30), (20, 22), (-20, 22)])     # лейка
    ln(c, -20, 20, 20, 20)
    setup_ink(c, acc, 4.2)                  # струи
    for x in (-12, -4, 4, 12):
        ln(c, x, 13, x, 3)
    ln(c, -8, 0, -8, -9)
    ln(c, 6, -2, 6, -13)
    ln(c, 15, 6, 15, -2)
    setup_ink(c, ink)


def i_toilet(c, ink, acc):
    rr(c, -17, 8, 17, 40, 4)                # бачок
    ln(c, -17, 32, 17, 32)
    setup_ink(c, acc, 3.6)
    circ(c, 0, 25, 3.2)                     # кнопка
    setup_ink(c, ink, 5)
    rr(c, -26, -20, 26, 8, 9)               # чаша
    setup_ink(c, acc, 2.8)
    rr(c, -19, -15, 19, 2, 8)               # сиденье
    setup_ink(c, ink, 4)
    poly(c, [(-12, -20), (12, -20), (8, -38), (-8, -38)])   # основание


def i_tap(c, ink, acc):
    setup_ink(c, ink, 8)
    p = c.beginPath()                       # гусак
    p.moveTo(-6, -26)
    p.lineTo(-6, 18)
    p.curveTo(-6, 36, 20, 36, 20, 18)
    c.drawPath(p, stroke=1, fill=0)
    setup_ink(c, ink, 4)
    rr(c, -18, -38, 18, -26, 4)             # основание
    ln(c, -16, -14, -12, -2)                # рычаг
    setup_ink(c, acc, 3.4)
    p2 = c.beginPath()                      # капля
    p2.moveTo(20, 8)
    p2.curveTo(27, 3, 25, -8, 20, -8)
    p2.curveTo(15, -8, 13, 3, 20, 8)
    p2.close()
    c.drawPath(p2, stroke=1, fill=0)
    setup_ink(c, ink)


def i_toothbrush(c, ink, acc):
    c.saveState()
    c.rotate(-16)
    rr(c, -6, -36, 6, 14, 6)               # ручка
    rr(c, -9, 14, 9, 30, 5)                # головка
    setup_ink(c, acc, 3.2)
    for x in (-6.4, -2.2, 2.2, 6.4):
        ln(c, x, 30, x, 38)                # щетина
    setup_ink(c, ink, 3)
    ln(c, -6, 6, 6, 6)                     # воротничок
    ln(c, -6, 0, 6, 0)
    c.restoreState()


def i_soap(c, ink, acc):
    rr(c, -34, -26, 34, 2, 11)             # брусок
    setup_ink(c, acc, 2.6)
    c.ellipse(-16, -19, 16, -5, stroke=1, fill=0)
    circ(c, 24, 16, 7)                     # пузыри
    circ(c, 8, 30, 4.4)
    circ(c, 32, 32, 3.2)
    setup_ink(c, ink)


def i_towel(c, ink, acc):
    ln(c, -44, 34, -26, 34)                 # штанга по бокам
    ln(c, 26, 34, 44, 34)
    circ(c, -44, 34, 3, fill=1)
    circ(c, 44, 34, 3, fill=1)
    p = c.beginPath()                       # полотенце с волнистым низом
    p.moveTo(-28, 40)
    p.lineTo(28, 40)
    p.lineTo(28, -26)
    p.curveTo(20, -34, 12, -26, 4, -32)
    p.curveTo(-4, -38, -14, -30, -22, -34)
    p.curveTo(-26, -36, -28, -32, -28, -26)
    p.close()
    c.drawPath(p, stroke=1, fill=0)
    setup_ink(c, acc, 2.8)
    ln(c, -28, 30, 28, 30)                  # сгиб через штангу
    ln(c, -10, 28, -10, -26)                # складки
    ln(c, 10, 28, 10, -24)
    setup_ink(c, ink, 2.2)
    ln(c, -26, -22, 26, -22)                # кромка


# кухня
def i_cup(c, ink, acc):
    rr(c, -20, -22, 14, 18, 6)
    p = c.beginPath()
    p.moveTo(14, 10)
    p.curveTo(32, 8, 32, -14, 14, -14)
    c.drawPath(p, stroke=1, fill=0)
    setup_ink(c, acc, 4)
    ln(c, -14, 6, 8, 6)
    setup_ink(c, ink)


def i_plate(c, ink, acc):
    circ(c, 0, 0, 33)
    setup_ink(c, acc, 3.4)
    circ(c, 0, 0, 23)
    setup_ink(c, acc, 2)
    circ(c, 0, 0, 19)
    setup_ink(c, ink)


def i_spoon(c, ink, acc):
    c.ellipse(-13, 10, 13, 44, stroke=1, fill=0)
    setup_ink(c, ink, 8.4)
    ln(c, 0, 12, 0, -34)
    setup_ink(c, acc, 3.4)
    c.ellipse(-8, 16, 8, 38, stroke=1, fill=0)


def i_pot(c, ink, acc):
    rr(c, -28, -26, 28, 10, 5)
    ln(c, -32, 10, 32, 10)
    rr(c, -40, 0, -28, 8, 2)
    rr(c, 28, 0, 40, 8, 2)
    setup_ink(c, acc, 4)
    circ(c, 0, 17, 4)
    setup_ink(c, ink)


def i_vase(c, ink, acc):
    p = c.beginPath()                       # корпус: узкое горло, широкое тело, дно
    p.moveTo(-12, 26)
    p.curveTo(-12, 14, -25, 8, -25, -10)
    p.curveTo(-25, -27, -19, -36, -13, -36)
    p.lineTo(13, -36)
    p.curveTo(19, -36, 25, -27, 25, -10)
    p.curveTo(25, 8, 12, 14, 12, 26)
    p.close()
    c.drawPath(p, stroke=1, fill=0)
    c.ellipse(-16, 24, 16, 32, stroke=1, fill=0)   # венчик
    setup_ink(c, acc, 3)
    ln(c, -23, -8, 23, -8)                  # декоративный поясок
    setup_ink(c, ink, 3)
    ln(c, -18, -31, 18, -31)                # дно


# комната
def i_clock(c, ink, acc):
    circ(c, 0, 0, 33)
    for a in (90, 0, 270, 180):
        x1 = 26 * math.cos(math.radians(a))
        y1 = 26 * math.sin(math.radians(a))
        x2 = 31 * math.cos(math.radians(a))
        y2 = 31 * math.sin(math.radians(a))
        ln(c, x1, y1, x2, y2)
    setup_ink(c, acc, 4.4)
    ln(c, 0, 0, 0, 19)
    ln(c, 0, 0, 13, -11)
    setup_ink(c, ink)
    circ(c, 0, 0, 2.6, fill=1)


def i_pillow(c, ink, acc):
    rr(c, -31, -24, 31, 24, 12)
    setup_ink(c, acc, 3.2)
    for sx in (-1, 1):
        p = c.beginPath()
        p.moveTo(sx * 22, 16)
        p.curveTo(sx * 12, 10, sx * 12, -10, sx * 22, -16)
        c.drawPath(p, stroke=1, fill=0)
    setup_ink(c, ink)


def i_jewelry(c, ink, acc):
    rr(c, -34, -30, 34, 10, 4)             # корпус
    p = c.beginPath()
    p.moveTo(-34, 10)
    p.curveTo(-34, 36, 34, 36, 34, 10)     # крышка
    c.drawPath(p, stroke=1, fill=0)
    setup_ink(c, acc, 2.8)
    ln(c, -34, 10, 34, 10)
    setup_ink(c, ink, 3.4)
    rr(c, -6, 0, 6, 14, 2)                 # замок
    setup_ink(c, acc, 2.6)
    circ(c, 0, 7, 1.8, fill=1)
    setup_ink(c, ink)


def i_piggy(c, ink, acc):
    c.ellipse(-32, -26, 26, 18, stroke=1, fill=0)   # тело
    rr(c, 22, -14, 36, 0, 4)                        # пятачок
    poly(c, [(4, 16), (16, 16), (12, 30)], close=True)   # ухо
    circ(c, 12, 4, 2.4, fill=1)                     # глаз
    setup_ink(c, ink, 5)
    ln(c, -20, -26, -20, -34)
    ln(c, -4, -26, -4, -32)
    ln(c, 14, -26, 14, -34)
    setup_ink(c, acc, 3)
    c.arc(-48, -24, -30, -6, 270, 180)              # хвост
    ln(c, -12, 14, 4, 14)                           # прорезь
    c.ellipse(-4, 18, 8, 34, stroke=1, fill=0)      # монета
    setup_ink(c, ink)


def i_slippers(c, ink, acc):
    c.saveState()
    c.translate(-2, -4)
    shoe(c, -30, -12, w=60, h=30, fill=0)   # крупный тапочек в профиль
    setup_ink(c, acc, 4.6)                  # ремешок
    c.arc(-4, -2, 18, 22, 0, 180)
    setup_ink(c, ink, 3.4)
    ln(c, -30, -12, 27, -12)                # подошва
    c.restoreState()


# школа
def i_backpack(c, ink, acc):
    rr(c, -24, -36, 24, 26, 15)             # корпус
    setup_ink(c, ink, 3.6)
    c.arc(-8, 22, 8, 36, 0, 180)            # ручка
    setup_ink(c, ink, 3)
    ln(c, -24, 12, 24, 12)                  # молния
    rr(c, -18, -30, 18, -4, 9)              # карман
    setup_ink(c, acc, 2.6)
    ln(c, -16, -15, 16, -15)                # молния кармана
    ln(c, 11, -15, 11, -21)
    setup_ink(c, ink, 2.6)
    for x in (-30, 30):                     # лямки по бокам
        p = c.beginPath()
        p.moveTo(x, 20)
        p.curveTo(x + 6 if x > 0 else x - 6, 0, x + 6 if x > 0 else x - 6, -20, x, -34)
        c.drawPath(p, stroke=1, fill=0)


def i_pencilcase(c, ink, acc):
    p = c.beginPath()                       # полуоткрытый пенал
    p.moveTo(-38, 2)
    p.lineTo(-38, -18)
    p.curveTo(-38, -28, -28, -32, -16, -32)
    p.lineTo(22, -32)
    p.curveTo(34, -32, 40, -24, 40, -12)
    p.lineTo(40, 2)
    p.curveTo(40, 9, 32, 9, 20, 9)
    p.lineTo(-18, 9)
    p.curveTo(-30, 9, -38, 9, -38, 2)
    p.close()
    c.drawPath(p, stroke=1, fill=0)
    setup_ink(c, acc, 2.6)
    ln(c, -35, 0, 37, 0)                    # молния
    ln(c, 30, 0, 30, 7)                     # бегунок
    setup_ink(c, ink, 4)
    ln(c, -30, 9, -34, 24)                  # карандаши
    ln(c, -21, 9, -19, 30)
    setup_ink(c, ink, 3)
    poly(c, [(-35.6, 23), (-29.4, 23), (-32.5, 32)], close=True, fill=1)
    poly(c, [(-20.5, 29), (-17.5, 29.5), (-19, 37)], close=True, fill=1)


def i_notebook(c, ink, acc):
    rr(c, -26, -36, 26, 36, 3)
    setup_ink(c, acc, 3.4)
    for y in range(-30, 36, 9):            # пружина
        ln(c, -33, y, -19, y)
    setup_ink(c, ink, 2.4)
    for y in range(-22, 26, 9):            # линии
        ln(c, -12, y, 18, y)


def i_textbook(c, ink, acc):
    rr(c, -30, -34, 24, 34, 3)             # обложка
    c.rect(-36, -34, 6, 68, stroke=1, fill=0)   # корешок
    setup_ink(c, acc, 3)
    ln(c, -6, -18, 14, -18)
    ln(c, -6, -8, 8, -8)
    setup_ink(c, ink)
    poly(c, [(4, 34), (14, 34), (14, 14), (9, 19), (4, 14)], close=True)   # закладка


def i_book(c, ink, acc):
    p = c.beginPath()
    p.moveTo(0, -24)
    p.curveTo(-14, -32, -30, -32, -40, -24)
    p.lineTo(-40, 24)
    p.curveTo(-30, 16, -14, 16, 0, 24)
    p.curveTo(14, 16, 30, 16, 40, 24)
    p.lineTo(40, -24)
    p.curveTo(30, -32, 14, -32, 0, -24)
    p.close()
    c.drawPath(p, stroke=1, fill=0)
    setup_ink(c, acc, 2.4)
    ln(c, 0, -24, 0, 24)
    for y in (-12, -2, 8, 18):
        ln(c, -32, y, -8, y - 4)
        ln(c, 8, y - 4, 32, y)
    setup_ink(c, ink)


def i_pencil(c, ink, acc):
    c.saveState()
    c.rotate(34)
    rr(c, -34, -8, 22, 8, 2)               # корпус
    poly(c, [(22, -8), (40, 0), (22, 8)])  # остриё
    setup_ink(c, acc, 3)
    poly(c, [(33, -3.5), (40, 0), (33, 3.5)], close=True, fill=1)   # грифель
    setup_ink(c, acc, 3)
    ln(c, -34, -8, -34, 8)
    ln(c, -26, -8, -26, 8)
    setup_ink(c, ink)
    c.restoreState()


def i_ruler(c, ink, acc):
    rr(c, -40, -13, 40, 13, 2)
    setup_ink(c, acc, 2.4)
    for i, x in enumerate(range(-32, 33, 10)):
        ln(c, x, 13, x, 13 - (7 if i % 2 == 0 else 4))
    circ(c, -35, 0, 2.8)                    # отверстие подвеса
    setup_ink(c, ink)


# ── список предметов: (русское, английское, группа, иконка) ─────────────────
ITEMS = [
    # мебель
    ("Стол", "Table", "furniture", i_table),
    ("Стул", "Chair", "furniture", i_chair),
    ("Кресло", "Armchair", "furniture", i_armchair),
    ("Кровать", "Bed", "furniture", i_bed),
    ("Диван", "Sofa", "furniture", i_sofa),
    ("Шкаф", "Wardrobe", "furniture", i_wardrobe),
    ("Полка", "Shelf", "furniture", i_shelf),
    ("Комод", "Dresser", "furniture", i_dresser),
    ("Тумбочка", "Nightstand", "furniture", i_nightstand),
    ("Табурет", "Stool", "furniture", i_stool),
    ("Обувница", "Shoe rack", "furniture", i_shoerack),
    ("Вешалка", "Hanger", "furniture", i_hanger),
    # техника
    ("Холодильник", "Fridge", "appliance", i_fridge),
    ("Плита", "Stove", "appliance", i_stove),
    ("Духовка", "Oven", "appliance", i_oven),
    ("Микроволновка", "Microwave", "appliance", i_microwave),
    ("Чайник", "Kettle", "appliance", i_kettle),
    ("Телевизор", "TV", "appliance", i_tv),
    ("Компьютер", "Computer", "appliance", i_computer),
    ("Колонка", "Speaker", "appliance", i_speaker),
    ("Стиральная машина", "Washing machine", "appliance", i_washer),
    ("Лампа", "Lamp", "appliance", i_lamp),
    # дом
    ("Окно", "Window", "house", i_window),
    ("Подоконник", "Windowsill", "house", i_windowsill),
    ("Дверь", "Door", "house", i_door),
    ("Занавеска", "Curtain", "house", i_curtain),
    ("Лестница", "Stairs", "house", i_stairs),
    ("Коврик", "Rug", "house", i_rug),
    ("Корзина", "Basket", "house", i_basket),
    ("Цветок", "Plant", "house", i_plant),
    ("Выключатель", "Light switch", "house", i_switch),
    ("Розетка", "Socket", "house", i_socket),
    ("Батарея", "Radiator", "house", i_radiator),
    ("Пол", "Floor", "house", i_floor),
    # ванная
    ("Зеркало", "Mirror", "bath", i_mirror),
    ("Ванна", "Bathtub", "bath", i_bath),
    ("Раковина", "Sink", "bath", i_sink),
    ("Душ", "Shower", "bath", i_shower),
    ("Унитаз", "Toilet", "bath", i_toilet),
    ("Кран", "Tap", "bath", i_tap),
    ("Зубная щётка", "Toothbrush", "bath", i_toothbrush),
    ("Мыло", "Soap", "bath", i_soap),
    ("Полотенце", "Towel", "bath", i_towel),
    # кухня
    ("Чашка", "Cup", "kitchen", i_cup),
    ("Тарелка", "Plate", "kitchen", i_plate),
    ("Ложка", "Spoon", "kitchen", i_spoon),
    ("Кастрюля", "Pot", "kitchen", i_pot),
    ("Ваза", "Vase", "kitchen", i_vase),
    # комната
    ("Часы", "Clock", "room", i_clock),
    ("Подушка", "Pillow", "room", i_pillow),
    ("Шкатулка", "Jewelry box", "room", i_jewelry),
    ("Копилка", "Piggy bank", "room", i_piggy),
    ("Тапочки", "Slippers", "room", i_slippers),
    # школа
    ("Рюкзак", "Backpack", "school", i_backpack),
    ("Пенал", "Pencil case", "school", i_pencilcase),
    ("Тетрадь", "Notebook", "school", i_notebook),
    ("Учебник", "Textbook", "school", i_textbook),
    ("Книга", "Book", "school", i_book),
    ("Карандаш", "Pencil", "school", i_pencil),
    ("Линейка", "Ruler", "school", i_ruler),
]

ROOMS = {
    "Кухня": ["Холодильник", "Плита", "Духовка", "Микроволновка", "Чайник",
              "Чашка", "Тарелка", "Ложка", "Кастрюля", "Полотенце"],
    "Гостиная": ["Стол", "Стул", "Табурет", "Кресло", "Диван", "Телевизор",
                 "Полка", "Лампа", "Коврик", "Часы", "Цветок", "Корзина", "Ваза"],
    "Спальня": ["Кровать", "Шкаф", "Комод", "Подушка", "Тумбочка", "Тапочки"],
    "Прихожая": ["Дверь", "Зеркало", "Обувница", "Вешалка", "Лестница"],
    "Ванная": ["Раковина", "Душ", "Ванна", "Унитаз", "Кран",
               "Зубная щётка", "Мыло", "Стиральная машина"],
    "Детская": ["Рюкзак", "Пенал", "Тетрадь", "Учебник", "Книга",
                "Карандаш", "Линейка", "Компьютер", "Колонка", "Шкатулка", "Копилка"],
    "Везде": ["Окно", "Подоконник", "Занавеска", "Выключатель", "Розетка",
              "Батарея", "Пол"],
}


# ── отрисовка наклейки ──────────────────────────────────────────────────────
def scallop_path(c: canvas.Canvas, cx, cy, r, amp=LOBE_AMP, lobes=LOBE_N, steps=None):
    steps = steps or lobes * 14
    p = c.beginPath()
    for i in range(steps + 1):
        a = 2 * math.pi * i / steps
        rr_ = r + amp * math.cos(lobes * a)
        x = cx + rr_ * math.cos(a)
        y = cy + rr_ * math.sin(a)
        if i == 0:
            p.moveTo(x, y)
        else:
            p.lineTo(x, y)
    p.close()
    return p


def fit_size(text: str, font: str, start: float, floor: float, max_w: float) -> float:
    size = start
    while size > floor and pdfmetrics.stringWidth(text, font, size) > max_w:
        size -= 0.2
    return round(size, 1)


def draw_sticker(c: canvas.Canvas, cx, cy, item, show_cut=True):
    ru, en, cat, icon = item
    pal = PALETTE[cat]
    tint, ink, acc = pal["tint"], pal["ink"], pal["accent"]

    c.saveState()
    # тело наклейки с вылетом за линию реза
    p = scallop_path(c, cx, cy, R_BLEED)
    c.setFillColor(tint)
    c.setStrokeColor(tint)
    c.setLineWidth(0.5)
    c.drawPath(p, stroke=1, fill=1)

    # светлое ядро под текст
    core = scallop_path(c, cx, cy, R_BLEED * 0.72, amp=LOBE_AMP * 0.72, lobes=LOBE_N)
    c.setFillColor(mix(tint, colors.white, 0.55))
    c.setStrokeColor(mix(tint, colors.white, 0.55))
    c.drawPath(core, stroke=0, fill=1)

    # внутреннее кольцо
    c.setStrokeColor(mix(acc, colors.white, 0.45))
    c.setLineWidth(0.55)
    c.drawPath(scallop_path(c, cx, cy, R_RING), stroke=1, fill=0)

    # иконка
    c.saveState()
    c.translate(cx, cy + 7.4 * mm)
    s = 18.6 * mm / 100
    c.scale(s, s)
    setup_ink(c, ink, 5.2)
    icon(c, ink, acc)
    c.restoreState()

    # подписи: английское первым и жирным, русское под ним
    en_size = fit_size(en, "MB", 11.2, 6.0, 33 * mm)
    ru_size = fit_size(ru, "MM", 7.8, 5.2, 30 * mm)
    c.setFillColor(ink)
    c.setFont("MB", en_size)
    c.drawCentredString(cx, cy - 6.6 * mm, en)
    c.setFillColor(mix(ink, colors.white, 0.45))
    c.setFont("MM", ru_size)
    c.drawCentredString(cx, cy - 12.2 * mm, ru)

    # контур реза
    if show_cut:
        c.setStrokeColor(CUT_COLOR)
        c.setLineWidth(0.35)
        c.drawPath(scallop_path(c, cx, cy, R_CUT), stroke=1, fill=0)
    c.restoreState()


# ── страницы ────────────────────────────────────────────────────────────────
def n_sheets() -> int:
    return (len(ITEMS) + PER_SHEET - 1) // PER_SHEET


def plural(n: int, forms=("лист", "листа", "листов")) -> str:
    if n % 10 == 1 and n % 100 != 11:
        return forms[0]
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return forms[1]
    return forms[2]


def page_cover(c: canvas.Canvas):
    c.setFillColor(colors.HexColor("#12100E"))
    c.rect(0, 0, PW, PH, stroke=0, fill=1)

    by_ru = {ru: item for item in ITEMS for ru in [item[0]]}
    samples = [by_ru["Стол"], by_ru["Холодильник"], by_ru["Компьютер"]]
    xs = [PW * 0.24, PW * 0.5, PW * 0.76]
    for x, it in zip(xs, samples):
        draw_sticker(c, x, PH - 48 * mm, it, show_cut=False)

    c.setFillColor(colors.HexColor("#E9A552"))
    c.setFont("MS", 8.4)
    c.drawString(20 * mm, PH - 86 * mm, "SM PRODUCTION · ОБУЧАЮЩИЕ НАКЛЕЙКИ · 2026")

    c.setFillColor(colors.HexColor("#F4EFE6"))
    c.setFont("MB", 26)
    c.drawString(20 * mm, PH - 99 * mm, "Дом говорит по-английски")
    c.drawString(20 * mm, PH - 112 * mm, "и по-русски")

    c.setFillColor(colors.HexColor("#B8AFA2"))
    c.setFont("M", 9.4)
    c.drawString(20 * mm, PH - 124 * mm,
                 f"{len(ITEMS)} наклеек на предметы дома: английское слово сверху, русское под ним.")
    c.drawString(20 * mm, PH - 130 * mm,
                 "Клеим на стол, холодильник, окно, дверь, зеркало — ребёнок читает слово там, где стоит предмет.")

    items = [(str(len(ITEMS)), "наклеек"), ("47", "мм"), ("2", "языка"),
             ("A4", f"{n_sheets()} {plural(n_sheets())}")]
    y = PH - 152 * mm
    col = (PW - 40 * mm) / 4
    c.setStrokeColor(colors.HexColor("#2E2A25"))
    c.setLineWidth(0.5)
    c.line(20 * mm, y + 13 * mm, PW - 20 * mm, y + 13 * mm)
    for i, (v, l) in enumerate(items):
        x = 20 * mm + i * col
        c.setFillColor(colors.HexColor("#F4EFE6"))
        c.setFont("MB", 22)
        c.drawString(x, y + 2 * mm, v)
        c.setFillColor(colors.HexColor("#8E877C"))
        c.setFont("M", 7.8)
        c.drawString(x, y - 4 * mm, l)

    steps = [
        ("1", "Печать", "A4, 100 %, без «по размеру страницы». Белая виниловая плёнка или самоклейка."),
        ("2", "Рез", "По малиновой линии. Вручную — ножницами по контуру, на плоттере — как контур реза (CutContour)."),
        ("3", "Покрытие", "Матовая ламинация держит воду и мытьё. Без неё — только сухая комната."),
        ("4", "Наклейка", "Обезжирить поверхность, прижать от центра к краям, разгладить."),
    ]
    yy = PH - 170 * mm
    for num, title, text in steps:
        c.setFillColor(colors.HexColor("#E9A552"))
        c.setFont("MB", 12)
        c.drawString(20 * mm, yy, num)
        c.setFillColor(colors.HexColor("#F4EFE6"))
        c.setFont("MS", 10)
        c.drawString(30 * mm, yy, title)
        c.setFillColor(colors.HexColor("#8E877C"))
        c.setFont("M", 8.4)
        words, line, lines = text.split(), "", []
        for w in words:
            probe = (line + " " + w).strip()
            if pdfmetrics.stringWidth(probe, "M", 8.4) > PW - 30 * mm - 20 * mm:
                lines.append(line)
                line = w
            else:
                line = probe
        lines.append(line)
        for k, L in enumerate(lines):
            c.drawString(30 * mm, yy - 5 * mm - k * 4.4 * mm, L)
        yy -= 5 * mm + len(lines) * 4.4 * mm + 4.5 * mm

    c.setFillColor(colors.HexColor("#1B1916"))
    c.rect(20 * mm, 34 * mm, PW - 40 * mm, 24 * mm, stroke=0, fill=1)
    c.setStrokeColor(CUT_COLOR)
    c.setLineWidth(0.9)
    c.line(26 * mm, 46 * mm, 44 * mm, 46 * mm)
    c.setFillColor(colors.HexColor("#F4EFE6"))
    c.setFont("MS", 8.6)
    c.drawString(49 * mm, 47 * mm, "Малиновая линия — контур реза (100 % magenta)")
    c.setFillColor(colors.HexColor("#8E877C"))
    c.setFont("M", 7.8)
    c.drawString(49 * mm, 42.5 * mm, "Краска выходит за контур на 0,8 мм — после реза не будет белого ободка.")
    c.drawString(49 * mm, 38.5 * mm, "После печатных листов идут такие же листы только с контурами — для плоттера.")

    c.setFillColor(colors.HexColor("#6F6A62"))
    c.setFont("M", 7)
    c.drawString(20 * mm, 16 * mm, "Набор обучающих наклеек «Дом» · SM Production · иллюстрации векторные, "
                                    "подходят для печати и резки")

    c.setFillColor(colors.HexColor("#FF4D1C"))
    c.rect(0, 0, PW, 3 * mm, stroke=0, fill=1)


def page_sheet(c: canvas.Canvas, batch):
    c.setFillColor(PAPER)
    c.rect(0, 0, PW, PH, stroke=0, fill=1)

    grid_w = COLS * PITCH
    x0 = (PW - grid_w) / 2 + PITCH / 2
    y_top = PH / 2 + (ROWS - 1) * PITCH / 2      # сетка по центру листа
    for idx, item in enumerate(batch):
        r, col = divmod(idx, COLS)
        cx = x0 + col * PITCH
        cy = y_top - r * PITCH
        draw_sticker(c, cx, cy, item, show_cut=True)


def page_cut_only(c: canvas.Canvas, batch, label: str):
    c.setFillColor(PAPER)
    c.rect(0, 0, PW, PH, stroke=0, fill=1)

    c.setFillColor(colors.HexColor("#7A7A7A"))
    c.setFont("M", 7)
    c.drawString(20 * mm, PH - 14 * mm,
                 f"Контуры реза · {label} · масштаб 1:1 · тонкая малиновая линия = рез")

    grid_w = COLS * PITCH
    x0 = (PW - grid_w) / 2 + PITCH / 2
    y_top = (PH - 12 * mm) / 2 + (ROWS - 1) * PITCH / 2
    c.setStrokeColor(CUT_COLOR)
    c.setLineWidth(0.35)
    for idx, item in enumerate(batch):
        r, col = divmod(idx, COLS)
        cx = x0 + col * PITCH
        cy = y_top - r * PITCH
        c.drawPath(scallop_path(c, cx, cy, R_CUT), stroke=1, fill=0)
        c.setFillColor(colors.HexColor("#9A9A9A"))
        c.setFont("M", 5.4)
        c.drawCentredString(cx, cy - 1.6 * mm, f"{item[0]} · {item[1]}")


def page_words(c: canvas.Canvas):
    c.setFillColor(PAPER)
    c.rect(0, 0, PW, PH, stroke=0, fill=1)

    c.setFillColor(INK)
    c.setFont("MB", 22)
    c.drawString(20 * mm, PH - 28 * mm, "Слова по комнатам")
    c.setFillColor(colors.HexColor("#7A756C"))
    c.setFont("M", 9.2)
    intro = ("План расклейки: начните с одной комнаты — 6–8 наклеек, чтобы не перегрузить "
             "ребёнка. English — сверху, по-русски — под ним.")
    words, line, lines = intro.split(), "", []
    for w in words:
        probe = (line + " " + w).strip()
        if pdfmetrics.stringWidth(probe, "M", 9.2) > PW - 40 * mm:
            lines.append(line)
            line = w
        else:
            line = probe
    lines.append(line)
    for k, L in enumerate(lines):
        c.drawString(20 * mm, PH - 35 * mm - k * 4.6 * mm, L)

    by_ru = {ru: (ru, en) for ru, en, _, _ in ITEMS}
    seen: set[str] = set()
    rooms: list[tuple[str, list[str]]] = []
    for room, words_ in ROOMS.items():
        uniq = [w for w in words_ if w in by_ru and w not in seen]
        seen.update(uniq)
        if uniq:
            rooms.append((room, uniq))

    # раскладываем комнаты по трём колонкам, выравнивая высоту
    cols: list[list[tuple[str, list[str]]]] = [[], [], []]
    heights = [0.0, 0.0, 0.0]
    for room, words_ in rooms:
        idx = heights.index(min(heights))
        cols[idx].append((room, words_))
        heights[idx] += len(words_) + 2.2

    col_w = (PW - 40 * mm) / 3
    row_h = 6.0 * mm
    y_start = PH - 52 * mm
    min_y = PH
    for ci, col_rooms in enumerate(cols):
        x = 20 * mm + ci * col_w
        y = y_start
        for room, words_ in col_rooms:
            c.setFillColor(colors.HexColor("#C4587F"))
            c.setFont("MS", 9.4)
            c.drawString(x, y, room.upper())
            c.setFillColor(colors.HexColor("#B9AFA5"))
            c.setFont("M", 7.6)
            c.drawRightString(x + col_w - 10 * mm, y, f"{len(words_)}")
            c.setStrokeColor(colors.HexColor("#DCC9D2"))
            c.setLineWidth(0.5)
            c.line(x, y - 2.2 * mm, x + col_w - 10 * mm, y - 2.2 * mm)
            y -= 8.4 * mm
            for ru in words_:
                ru_, en_ = by_ru[ru]
                w_en = pdfmetrics.stringWidth(en_, "MB", 9.4)
                w_ru = pdfmetrics.stringWidth(ru_, "M", 8.2)
                avail = col_w - 14 * mm
                k = min(1.0, avail / max(w_en + w_ru, 1))
                c.setFillColor(INK)
                c.setFont("MB", 9.4 * k)
                c.drawString(x, y, en_)
                c.setFillColor(colors.HexColor("#8E877C"))
                c.setFont("M", 8.2 * k)
                c.drawRightString(x + col_w - 10 * mm, y, ru_)
                c.setStrokeColor(colors.HexColor("#EDE9E2"))
                c.setLineWidth(0.3)
                c.line(x, y - 2.3 * mm, x + col_w - 10 * mm, y - 2.3 * mm)
                y -= row_h
            y -= 4.6 * mm
        min_y = min(min_y, y)

    gy = min_y - 12 * mm
    if gy >= 56 * mm:          # блок рисуем только если есть место под колонками
        # три игры — заполняем низ листа и добавляем пользу
        gy = min_y - 12 * mm
        c.setStrokeColor(colors.HexColor("#E4DFD6"))
        c.setLineWidth(0.5)
        c.line(20 * mm, gy + 10 * mm, PW - 20 * mm, gy + 10 * mm)
        c.setFillColor(INK)
        c.setFont("MS", 9.6)
        c.drawString(20 * mm, gy, "ТРИ ИГРЫ С НАКЛЕЙКАМИ")

        games = [
            ("Что это?", "Показывайте на предмет и спрашивайте «What is it?». Ребёнок читает "
                         "английское слово на наклейке и повторяет русское."),
            ("Найди и приклей", "Дайте ребёнку 3–5 наклеек и попросите найти предметы в комнате. "
                                "Проговаривайте слово вслух, пока клеите."),
            ("Охота за словами", "Называйте слово по-английски — ребёнок бежит к предмету. "
                                 "Потом меняетесь ролями."),
        ]
        gw = (PW - 40 * mm) / 3
        for i, (title, text) in enumerate(games):
            x = 20 * mm + i * gw
            c.setFillColor(colors.HexColor("#C4587F"))
            c.setFont("MB", 8.8)
            c.drawString(x, gy - 9 * mm, f"{i + 1}. {title}")
            c.setFillColor(colors.HexColor("#7A756C"))
            c.setFont("M", 7.6)
            words, line, lines = text.split(), "", []
            for w in words:
                probe = (line + " " + w).strip()
                if pdfmetrics.stringWidth(probe, "M", 7.6) > gw - 12 * mm:
                    lines.append(line)
                    line = w
                else:
                    line = probe
            lines.append(line)
            for k, L in enumerate(lines):
                c.drawString(x, gy - 15 * mm - k * 4 * mm, L)
            # вертикальные разделители
            if i:
                c.setStrokeColor(colors.HexColor("#EDE9E2"))
                c.setLineWidth(0.4)
                c.line(x - 4 * mm, gy + 6 * mm, x - 4 * mm, gy - 26 * mm)

    c.setFillColor(colors.HexColor("#7A756C"))
    c.setFont("M", 8)
    c.drawString(20 * mm, 20 * mm,
                 "Печать A4 · 100 % · рез по малиновому контуру · матовая ламинация для влажных комнат")


def main() -> None:
    c = canvas.Canvas(str(OUT), pagesize=A4)
    c.setTitle("SM Production — обучающие наклейки для дома, EN + RU")
    c.setAuthor("SM Production")

    page_cover(c)
    c.showPage()

    for start in range(0, len(ITEMS), PER_SHEET):
        page_sheet(c, ITEMS[start:start + PER_SHEET])
        c.showPage()

    for start in range(0, len(ITEMS), PER_SHEET):
        batch = ITEMS[start:start + PER_SHEET]
        page_cut_only(c, batch, f"{start + 1}–{start + len(batch)} из {len(ITEMS)}")
        c.showPage()

    page_words(c)
    c.showPage()

    c.save()
    print(f"  {OUT.name}: {OUT.stat().st_size // 1024} КБ · предметов {len(ITEMS)} · "
          f"листов {n_sheets()} + {n_sheets()} контурных")


if __name__ == "__main__":
    main()
