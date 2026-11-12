#!/usr/bin/env python3
"""Обучающие наклейки для дома: 30 предметов, русское название + английский перевод.

Что делает скрипт:
  * рисует 30 наклеек векторно (иконка + «Стол» / «Table»);
  * верстает печатные листы A4 по 12 наклеек (шаг 60 мм, наклейка 47 мм);
  * добавляет контур реза — малиновая линия 0,35 pt по внешнему контуру
    с запасом 0,8 мм под рез;
  * собирает отдельную страницу «только контуры» для проверки и резки;
  * печатает сводную таблицу слов по комнатам.

Печать: A4, 100 %, без масштабирования. Материал — белая виниловая плёнка.

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
SHEET_TOP_WASTE = 4 * mm

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
    """Смешать два цвета: t=0 → c1, t=1 → c2."""
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
}
PALETTE = {k: {kk: colors.HexColor(vv) for kk, vv in v.items()} for k, v in PALETTE.items()}


# ── примитивы рисования ─────────────────────────────────────────────────────
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


# ── иконки: система координат 100×100, центр (0, 0) ─────────────────────────
def i_table(c, ink, acc):
    rr(c, -42, 10, 42, 21, 3)
    rr(c, -34, -38, -26, 12, 3)
    rr(c, 26, -38, 34, 12, 3)
    ln(c, -26, -24, 26, -24)


def i_chair(c, ink, acc):
    rr(c, -36, 0, -26, 40, 5)
    rr(c, -36, -8, 28, 1, 4)
    rr(c, 19, -38, 27, -6, 3)
    rr(c, -36, -38, -28, -6, 3)
    setup_ink(c, acc, 3.4)
    ln(c, -31, 30, 8, 30)          # перекладина спинки
    setup_ink(c, ink)


def i_bed(c, ink, acc):
    rr(c, -42, -6, -33, 40, 4)
    rr(c, -33, -6, 34, 13, 5)
    rr(c, -29, 4, -11, 12, 3)
    rr(c, -30, -38, -22, -6, 2)
    rr(c, 24, -38, 32, -6, 2)
    setup_ink(c, acc, 3.4)
    ln(c, 18, -1, 32, -1)
    setup_ink(c, ink)


def i_sofa(c, ink, acc):
    rr(c, -36, 2, 36, 26, 8)
    rr(c, -44, -12, -32, 20, 6)
    rr(c, 32, -12, 44, 20, 6)
    rr(c, -34, -12, 34, 2, 4)
    rr(c, -30, -38, -24, -12, 2)
    rr(c, 24, -38, 30, -12, 2)
    setup_ink(c, acc, 3.4)
    ln(c, -24, 20, 24, 20)
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
    rr(c, -40, 6, 40, 13, 2)
    rr(c, -40, -34, 40, -27, 2)
    books = [(-32, 22, 8), (-22, 30, 7), (-13, 26, 9), (-2, 34, 7), (7, 24, 8)]
    for x, h, w in books:
        rr(c, x, 13, x + w, 13 + h, 1)
    setup_ink(c, acc, 3.4)
    ln(c, 0, 13, 0, 40)
    setup_ink(c, ink)


def i_fridge(c, ink, acc):
    rr(c, -26, -42, 26, 42, 7)
    ln(c, -26, 16, 26, 16)
    setup_ink(c, acc, 4.4)
    ln(c, 18, 22, 18, 34)
    ln(c, 18, -1, 18, 11)
    setup_ink(c, ink)


def i_stove(c, ink, acc):
    rr(c, -34, -36, 34, 34, 5)
    ln(c, -34, 14, 34, 14)
    for x in (-17, 0, 17):
        circ(c, x, 27, 6.5)
    rr(c, -26, -30, 26, 2, 4)
    setup_ink(c, acc, 4.4)
    ln(c, -20, -6, 20, -6)
    setup_ink(c, ink)


def i_kettle(c, ink, acc):
    rr(c, -22, -28, 22, 10, 9)
    p = c.beginPath()
    p.moveTo(17, 4); p.lineTo(33, 19); p.lineTo(38, 12); p.lineTo(22, -4)
    p.close()
    c.drawPath(p, stroke=1, fill=0)
    p2 = c.beginPath()
    p2.moveTo(-20, 4)
    p2.curveTo(-38, 2, -34, -22, -12, -24)
    c.drawPath(p2, stroke=1, fill=0)
    ln(c, -18, 10, 18, 10)
    setup_ink(c, acc, 4)
    circ(c, 0, 15, 3.4)
    setup_ink(c, ink)


def i_tv(c, ink, acc):
    rr(c, -40, -14, 40, 32, 6)
    rr(c, -6, -24, 6, -14, 2)
    rr(c, -24, -31, 24, -24, 3)
    setup_ink(c, acc, 3.4)
    ln(c, -32, 24, -18, 24)
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


def i_window(c, ink, acc):
    rr(c, -32, -36, 32, 36, 2)
    ln(c, -32, 0, 32, 0)
    ln(c, 0, -36, 0, 36)
    setup_ink(c, acc, 3.4)
    circ(c, -16, 18, 6)                        # солнце в стекле
    for a in range(0, 360, 45):
        x1 = -16 + 10 * math.cos(math.radians(a))
        y1 = 18 + 10 * math.sin(math.radians(a))
        x2 = -16 + 13 * math.cos(math.radians(a))
        y2 = 18 + 13 * math.sin(math.radians(a))
        ln(c, x1, y1, x2, y2)
    setup_ink(c, ink)


def i_door(c, ink, acc):
    setup_ink(c, ink, 4.8)
    rr(c, -26, -34, 26, 40, 2)          # полотно
    setup_ink(c, ink, 3.2)
    rr(c, -17, 2, 17, 31, 2)            # одна высокая филёнка
    rr(c, -17, -26, 17, -6, 2)          # нижняя филёнка
    setup_ink(c, acc, 5.2)
    circ(c, 17, -4, 3.4, fill=1)        # ручка
    setup_ink(c, acc, 4)
    ln(c, -42, -34, 42, -34)            # пол


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
    rr(c, -32, -16, 32, 8, 9)
    circ(c, 0, -4, 3.2)
    setup_ink(c, acc, 4)
    ln(c, 0, 8, 0, 28)
    ln(c, 0, 28, 14, 28)
    ln(c, 14, 28, 14, 20)
    setup_ink(c, ink)


def i_shower(c, ink, acc):
    poly(c, [(-18, 34), (18, 34), (12, 18), (-12, 18)])
    ln(c, 0, 34, 0, 42)
    for x in (-9, -3, 3, 9):
        setup_ink(c, acc, 4.4)
        ln(c, x, 10, x, 2)
    setup_ink(c, acc, 4.4)
    ln(c, -14, -6, -14, -12)
    ln(c, 1, -10, 1, -18)
    ln(c, 12, -4, 12, -9)
    setup_ink(c, ink)


def i_toilet(c, ink, acc):
    rr(c, -15, 12, 15, 40, 4)                 # бак
    setup_ink(c, acc, 4)
    ln(c, -8, 34, 8, 34)                       # кнопка
    # чаша
    setup_ink(c, ink, 5.2)
    p = c.beginPath()
    p.moveTo(-26, 8)
    p.curveTo(-26, -18, -14, -34, 0, -34)
    p.curveTo(14, -34, 26, -18, 26, 8)
    p.close()
    c.drawPath(p, stroke=1, fill=0)
    setup_ink(c, acc, 3.4)
    ln(c, -26, 8, 26, 8)
    c.ellipse(-11, -18, 11, 2, stroke=1, fill=0)   # слив


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


def i_rug(c, ink, acc):
    rr(c, -40, -27, 40, 27, 6)
    setup_ink(c, acc, 3.2)
    rr(c, -31, -18, 31, 18, 3)
    for y in (-12, 0, 12):
        ln(c, -20, y, 20, y)
    setup_ink(c, ink)


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


def i_stairs(c, ink, acc):
    # четыре ступени контуром: подъём слева-вниз, справа-вверх
    w, h = 19, 19
    x0, y0 = -38, -34
    for i in range(4):
        setup_ink(c, ink, 4.2)
        c.rect(x0 + i * w, y0, w, (i + 1) * h, stroke=1, fill=0)
    # линия пола
    setup_ink(c, acc, 3.6)
    ln(c, -44, -34, 44, -34)


def i_pillow(c, ink, acc):
    rr(c, -31, -24, 31, 24, 12)
    setup_ink(c, acc, 3.2)
    for sx in (-1, 1):
        p = c.beginPath()
        p.moveTo(sx * 22, 16)
        p.curveTo(sx * 12, 10, sx * 12, -10, sx * 22, -16)
        c.drawPath(p, stroke=1, fill=0)
    setup_ink(c, ink)


def i_towel(c, ink, acc):
    rr(c, -24, -32, 24, 26, 3)
    ln(c, -24, 10, 24, 10)
    for x in (-24, 24):
        c.arc(x - 5, 22, x + 5, 32, 0, 180)
    setup_ink(c, acc, 3)
    ln(c, -20, -8, 20, -8)
    ln(c, -20, -16, 20, -16)
    setup_ink(c, ink)



def i_dresser(c, ink, acc):
    rr(c, -30, -38, 30, 34, 4)
    for y in (12, -6, -22):
        ln(c, -30, y, 30, y)
        setup_ink(c, acc, 4)
        ln(c, -6, y - 7, 6, y - 7)
        setup_ink(c, ink)


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


def i_tap(c, ink, acc):
    c.setLineWidth(7.5)
    p = c.beginPath()
    p.moveTo(-14, -34)
    p.lineTo(-14, 10)
    p.curveTo(-14, 26, 14, 26, 14, 10)
    p.lineTo(14, 2)
    c.drawPath(p, stroke=1, fill=0)
    setup_ink(c, ink, 7.5)
    p2 = c.beginPath()
    p2.moveTo(-14, -34)
    p2.lineTo(-14, 10)
    p2.curveTo(-14, 26, 14, 26, 14, 10)
    p2.lineTo(14, 2)
    c.drawPath(p2, stroke=1, fill=0)
    rr(c, -26, -40, -2, -32, 3)
    setup_ink(c, acc, 3.6)
    ln(c, -8, -2, -8, -14)
    setup_ink(c, ink)


def i_radiator(c, ink, acc):
    rr(c, -40, -22, 40, 22, 5)
    for x in (-30, -18, -6, 6, 18, 30):
        ln(c, x, -22, x, 22)
    setup_ink(c, acc, 4)
    ln(c, -38, 0, 38, 0)
    setup_ink(c, ink)


def i_stool(c, ink, acc):
    c.ellipse(-26, 16, 26, 34, stroke=1, fill=0)
    ln(c, -18, 16, -26, -38)
    ln(c, 18, 16, 26, -38)
    ln(c, -22, 20, 22, 20)
    setup_ink(c, acc, 4)
    ln(c, -20, -14, 20, -14)
    setup_ink(c, ink)


# ── список предметов ────────────────────────────────────────────────────────
ITEMS = [
    # мебель
    ("Стол", "Table", "furniture", i_table),
    ("Стул", "Chair", "furniture", i_chair),
    ("Кровать", "Bed", "furniture", i_bed),
    ("Диван", "Sofa", "furniture", i_sofa),
    ("Шкаф", "Wardrobe", "furniture", i_wardrobe),
    ("Полка", "Shelf", "furniture", i_shelf),
    # техника
    ("Холодильник", "Fridge", "appliance", i_fridge),
    ("Плита", "Stove", "appliance", i_stove),
    ("Чайник", "Kettle", "appliance", i_kettle),
    ("Телевизор", "TV", "appliance", i_tv),
    ("Стиральная машина", "Washing machine", "appliance", i_washer),
    ("Лампа", "Lamp", "appliance", i_lamp),
    # дом
    ("Окно", "Window", "house", i_window),
    ("Дверь", "Door", "house", i_door),
    ("Лестница", "Stairs", "house", i_stairs),
    ("Коврик", "Rug", "house", i_rug),
    ("Корзина", "Basket", "house", i_basket),
    ("Цветок", "Plant", "house", i_plant),
    # ванная
    ("Зеркало", "Mirror", "bath", i_mirror),
    ("Ванна", "Bathtub", "bath", i_bath),
    ("Раковина", "Sink", "bath", i_sink),
    ("Душ", "Shower", "bath", i_shower),
    ("Унитаз", "Toilet", "bath", i_toilet),
    ("Полотенце", "Towel", "bath", i_towel),
    # кухня
    ("Чашка", "Cup", "kitchen", i_cup),
    ("Тарелка", "Plate", "kitchen", i_plate),
    ("Ложка", "Spoon", "kitchen", i_spoon),
    ("Кастрюля", "Pot", "kitchen", i_pot),
    # комната
    ("Часы", "Clock", "room", i_clock),
    ("Подушка", "Pillow", "room", i_pillow),
    # мебель и дом — вторая половина набора
    ("Комод", "Dresser", "furniture", i_dresser),
    ("Табурет", "Stool", "furniture", i_stool),
    ("Выключатель", "Light switch", "house", i_switch),
    ("Розетка", "Socket", "house", i_socket),
    ("Кран", "Tap", "bath", i_tap),
    ("Батарея", "Radiator", "house", i_radiator),
]

ROOMS = {
    "Кухня": ["Холодильник", "Плита", "Чайник", "Чашка", "Тарелка", "Ложка", "Кастрюля", "Полотенце"],
    "Гостиная": ["Стол", "Стул", "Диван", "Телевизор", "Полка", "Лампа", "Коврик", "Часы", "Цветок", "Корзина"],
    "Спальня": ["Кровать", "Шкаф", "Подушка", "Лампа"],
    "Прихожая": ["Дверь", "Зеркало", "Корзина", "Лестница"],
    "Ванная": ["Раковина", "Душ", "Ванна", "Унитаз", "Полотенце", "Зеркало"],
    "Везде": ["Окно", "Дверь", "Выключатель", "Розетка", "Батарея"],
}


# ── отрисовка одной наклейки ────────────────────────────────────────────────
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


def draw_sticker(c: canvas.Canvas, cx, cy, item, show_cut=True):
    ru, en, cat, icon = item
    pal = PALETTE[cat]
    tint, ink, acc = pal["tint"], pal["ink"], pal["accent"]

    # 1. тело наклейки — с вылетом за линию реза
    c.saveState()
    p = scallop_path(c, cx, cy, R_BLEED)
    c.setFillColor(tint)
    c.setStrokeColor(tint)
    c.setLineWidth(0.5)
    c.drawPath(p, stroke=1, fill=1)

    # 2. светлое ядро под текст — мягкий объём
    core = scallop_path(c, cx, cy, R_BLEED * 0.72, amp=LOBE_AMP * 0.72, lobes=LOBE_N)
    c.setFillColor(mix(tint, colors.white, 0.55))
    c.setStrokeColor(mix(tint, colors.white, 0.55))
    c.drawPath(core, stroke=0, fill=1)

    # 3. внутреннее кольцо
    c.setStrokeColor(mix(acc, colors.white, 0.45))
    c.setLineWidth(0.55)
    c.drawPath(scallop_path(c, cx, cy, R_RING), stroke=1, fill=0)

    # 4. иконка
    c.saveState()
    c.translate(cx, cy + 6.2 * mm)
    s = 19.5 * mm / 100
    c.scale(s, s)
    setup_ink(c, ink, 5.2)
    icon(c, ink, acc)
    c.restoreState()

    # 5. подписи
    max_w = 2 * math.sqrt(max(R_CUT ** 2 - (11 * mm) ** 2, 1)) - 7 * mm
    ru_size = fit_size(ru, "MB", 11.2, 6.6, max_w)
    en_size = fit_size(en, "MS", 7.6, 5.6, max_w)
    c.setFillColor(ink)
    c.setFont("MB", ru_size)
    c.drawCentredString(cx, cy - 8.6 * mm, ru)
    c.setFillColor(mix(ink, colors.white, 0.42))
    c.setFont("MS", en_size)
    c.drawCentredString(cx, cy - 13.9 * mm, en.upper())

    # 6. контур реза
    if show_cut:
        c.setStrokeColor(CUT_COLOR)
        c.setLineWidth(0.35)
        c.drawPath(scallop_path(c, cx, cy, R_CUT), stroke=1, fill=0)
    c.restoreState()


def fit_size(text: str, font: str, start: float, floor: float, max_w: float) -> float:
    size = start
    while size > floor and pdfmetrics.stringWidth(text, font, size) > max_w:
        size -= 0.2
    return round(size, 1)


# ── страницы ────────────────────────────────────────────────────────────────
def page_cover(c: canvas.Canvas):
    c.setFillColor(colors.HexColor("#12100E"))
    c.rect(0, 0, PW, PH, stroke=0, fill=1)

    # три живые наклейки сверху
    samples = [ITEMS[0], ITEMS[6], ITEMS[18]]
    xs = [PW * 0.24, PW * 0.5, PW * 0.76]
    for x, it in zip(xs, samples):
        draw_sticker(c, x, PH - 48 * mm, it, show_cut=False)

    c.setFillColor(colors.HexColor("#E9A552"))
    c.setFont("MS", 8.4)
    c.drawString(20 * mm, PH - 86 * mm, "SM PRODUCTION · ОБУЧАЮЩИЕ НАКЛЕЙКИ · 2026")

    c.setFillColor(colors.HexColor("#F4EFE6"))
    c.setFont("MB", 26)
    c.drawString(20 * mm, PH - 99 * mm, "Дом говорит по-русски")
    c.drawString(20 * mm, PH - 112 * mm, "и по-английски")

    c.setFillColor(colors.HexColor("#B8AFA2"))
    c.setFont("M", 9.4)
    c.drawString(20 * mm, PH - 124 * mm,
                 "36 наклеек на предметы дома: русское слово и английский перевод.")
    c.drawString(20 * mm, PH - 130 * mm,
                 "Клеим на стол, холодильник, окно, дверь, зеркало — ребёнок читает слово там, где стоит предмет.")

    # KPI
    items = [("36", "наклеек"), ("47", "мм"), ("2", "языка"), ("A4", "3 листа")]
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

    # инструкция
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
        yy -= 5 * mm + len(lines) * 4.4 * mm + 7 * mm

    # легенда контура
    c.setFillColor(colors.HexColor("#1B1916"))
    c.rect(20 * mm, 42 * mm, PW - 40 * mm, 25 * mm, stroke=0, fill=1)
    c.setStrokeColor(CUT_COLOR)
    c.setLineWidth(0.9)
    c.line(26 * mm, 55 * mm, 44 * mm, 55 * mm)
    c.setFillColor(colors.HexColor("#F4EFE6"))
    c.setFont("MS", 8.6)
    c.drawString(49 * mm, 56 * mm, "Малиновая линия — контур реза (100 % magenta)")
    c.setFillColor(colors.HexColor("#8E877C"))
    c.setFont("M", 7.8)
    c.drawString(49 * mm, 51.5 * mm, "Краска выходит за контур на 0,8 мм — после реза не будет белого ободка.")
    c.drawString(49 * mm, 47.5 * mm, "Предпоследняя страница — только контуры: удобно отдать на плоттер отдельно.")

    c.setFillColor(colors.HexColor("#6F6A62"))
    c.setFont("M", 7)
    c.drawString(20 * mm, 16 * mm, "Набор обучающих наклеек «Дом» · SM Production · иллюстрации векторные, "
                                    "подходят для печати и резки")

    c.setFillColor(colors.HexColor("#FF4D1C"))
    c.rect(0, 0, PW, 3 * mm, stroke=0, fill=1)


def page_sheet(c: canvas.Canvas, batch, page_label):
    c.setFillColor(PAPER)
    c.rect(0, 0, PW, PH, stroke=0, fill=1)

    grid_w = COLS * PITCH
    x0 = (PW - grid_w) / 2 + PITCH / 2
    y_top = PH - 26 * mm
    for idx, item in enumerate(batch):
        r, col = divmod(idx, COLS)
        cx = x0 + col * PITCH
        cy = y_top - r * PITCH
        draw_sticker(c, cx, cy, item, show_cut=True)


def page_cut_only(c: canvas.Canvas, batch, first_label: str):
    c.setFillColor(PAPER)
    c.rect(0, 0, PW, PH, stroke=0, fill=1)

    c.setFillColor(colors.HexColor("#7A7A7A"))
    c.setFont("M", 7)
    c.drawString(20 * mm, PH - 14 * mm,
                 f"Контуры реза · {first_label} · масштаб 1:1 · тонкая малиновая линия = рез")

    grid_w = COLS * PITCH
    x0 = (PW - grid_w) / 2 + PITCH / 2
    y_top = PH - 40 * mm
    c.setStrokeColor(CUT_COLOR)
    c.setLineWidth(0.35)
    for idx, item in enumerate(batch):
        r, col = divmod(idx, COLS)
        cx = x0 + col * PITCH
        cy = y_top - r * PITCH
        c.drawPath(scallop_path(c, cx, cy, R_CUT), stroke=1, fill=0)
        c.setFillColor(colors.HexColor("#9A9A9A"))
        c.setFont("M", 5.6)
        c.drawCentredString(cx, cy - 1.6 * mm, f"{item[0]} · {item[1]}")


def page_words(c: canvas.Canvas):
    c.setFillColor(PAPER)
    c.rect(0, 0, PW, PH, stroke=0, fill=1)

    c.setFillColor(INK)
    c.setFont("MB", 20)
    c.drawString(20 * mm, PH - 28 * mm, "Слова по комнатам")
    c.setFillColor(colors.HexColor("#7A756C"))
    c.setFont("M", 9)
    c.drawString(20 * mm, PH - 35 * mm,
                 "План расклейки: начните с одной комнаты — 6–8 наклеек, чтобы не перегрузить ребёнка.")

    by_ru = {ru: (ru, en) for ru, en, _, _ in ITEMS}
    col_w = (PW - 40 * mm) / 2
    y = PH - 48 * mm
    for i, (room, words) in enumerate(ROOMS.items()):
        col = i % 2
        if col == 0 and i:
            y -= 0
        x = 20 * mm + col * col_w
        yy = y
        c.setFillColor(colors.HexColor("#C9752B"))
        c.setFont("MS", 10)
        c.drawString(x, yy, room.upper())
        yy -= 7 * mm
        for w in words:
            if w not in by_ru:
                continue
            ru, en = by_ru[w]
            c.setFillColor(INK)
            c.setFont("MM", 9)
            c.drawString(x, yy, ru)
            c.setFillColor(colors.HexColor("#8E877C"))
            c.setFont("M", 8)
            c.drawRightString(x + col_w - 12 * mm, yy, en)
            c.setStrokeColor(colors.HexColor("#E4DFD6"))
            c.setLineWidth(0.4)
            c.line(x, yy - 2.2 * mm, x + col_w - 12 * mm, yy - 2.2 * mm)
            yy -= 7 * mm
        if col == 1:
            y = yy - 8 * mm
    # левая колонка может быть длиннее — добиваем отступ
    c.setFillColor(colors.HexColor("#7A756C"))
    c.setFont("M", 7.6)
    c.drawString(20 * mm, 20 * mm,
                 "Совет: проговаривайте пару «Стол — Table» и просите ребёнка показать предмет. "
                 "Через неделю меняйте порядок вопросов.")

    c.setStrokeColor(colors.HexColor("#E4DFD6"))
    c.setLineWidth(0.5)
    c.line(20 * mm, 26 * mm, PW - 20 * mm, 26 * mm)


def main() -> None:
    c = canvas.Canvas(str(OUT), pagesize=A4)
    c.setTitle("SM Production — обучающие наклейки для дома, RU + EN")
    c.setAuthor("SM Production")

    page_cover(c)
    c.showPage()

    for start in range(0, len(ITEMS), COLS * ROWS):
        page_sheet(c, ITEMS[start:start + COLS * ROWS], start)
        c.showPage()

    for start in range(0, len(ITEMS), COLS * ROWS):
        batch = ITEMS[start:start + COLS * ROWS]
        page_cut_only(c, batch, f"{start + 1}–{start + len(batch)} из {len(ITEMS)}")
        c.showPage()

    page_words(c)
    c.showPage()

    c.save()
    print(f"  {OUT.name}: {OUT.stat().st_size // 1024} КБ")


if __name__ == "__main__":
    main()
