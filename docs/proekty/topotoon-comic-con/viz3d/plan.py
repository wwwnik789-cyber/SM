#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
План стенда сверху 9,00 × 5,04 м — схема раскладки зон.

Рендерер для вида сверху не годится: ламельный потолок закрывает всё.
Поэтому план рисуется 2D — как чертёж, с размерами, осями столбов и подписями
зон. Стиль тот же: тёмный лист, лайм для контура, белый для текста.
"""
import os
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(BASE, "..", "..", "..", "ca-avtosalony", "02_prezentaciya", "fonts")

W_M, D_M = 9.00, 5.04                    # габариты по модели
PX = 150                                  # пикселей на метр
MARGIN_L = 210
MARGIN_R = 210
MARGIN_T = 210
MARGIN_B = 210
CV_W = int(W_M * PX + MARGIN_L + MARGIN_R)
CV_H = int(D_M * PX + MARGIN_T + MARGIN_B)

LIME = (204, 240, 36)
VIOLET = (144, 96, 252)
BG = (13, 14, 18)
INK = (238, 238, 232)
GREY = (120, 124, 136)


def font(size, w="700"):
    name = {"800": "Unbounded-800.ttf", "700": "Unbounded-700.ttf",
            "400": "Unbounded-400.ttf"}[w]
    return ImageFont.truetype(os.path.join(FONTS, name), size)


def man(size, w="600"):
    return ImageFont.truetype(os.path.join(FONTS, f"Manrope-{w}.ttf"), size)


def xy(x, y):
    """Метры плана → пиксели холста. y = 0 — линия фронта (низ листа)."""
    return (MARGIN_L + x * PX, MARGIN_T + (D_M - y) * PX)


class Plan:
    def __init__(self):
        self.im = Image.new("RGB", (CV_W, CV_H), BG)
        self.d = ImageDraw.Draw(self.im)

    def rect(self, x0, y0, x1, y1, fill=None, outline=None, width=3):
        a = xy(x0, y1)
        b = xy(x1, y0)
        self.d.rectangle([a[0], a[1], b[0], b[1]], fill=fill, outline=outline, width=width)

    def post(self, x, y):
        self.rect(x - 0.05, y - 0.05, x + 0.05, y + 0.05, fill=(178, 183, 194))

    def circle(self, x, y, r, fill=None, outline=None, width=2):
        cx, cy = xy(x, y)
        rr = r * PX
        self.d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=fill,
                       outline=outline, width=width)

    def label(self, x, y, text, size=26, color=INK, anchor="mm"):
        self.d.text(xy(x, y), text, font=man(size, "700"), fill=color, anchor=anchor)

    def dim_h(self, x0, x1, y_off, text):
        """Горизонтальный размер под листом."""
        a = xy(x0, 0)
        b = xy(x1, 0)
        yy = a[1] + y_off
        self.d.line([a[0], yy, b[0], yy], fill=GREY, width=2)
        for xp in (a[0], b[0]):
            self.d.line([xp, yy - 10, xp, yy + 10], fill=GREY, width=2)
        self.d.text(((a[0] + b[0]) / 2, yy + 22), text, font=man(30, "700"),
                    fill=INK, anchor="mt")

    def dim_v(self, y0, y1, x, text, off=112):
        """Вертикальный размер слева от листа, подпись горизонтально."""
        a = xy(x, y0)
        b = xy(x, y1)
        xx = a[0] - off
        self.d.line([xx, min(a[1], b[1]), xx, max(a[1], b[1])], fill=GREY, width=2)
        for yp in (a[1], b[1]):
            self.d.line([xx - 10, yp, xx + 10, yp], fill=GREY, width=2)
        cy = int((min(a[1], b[1]) + max(a[1], b[1])) / 2)
        self.d.text((xx + 18, cy), text, font=man(29, "700"), fill=INK, anchor="lm")


def build():
    p = Plan()

    # подиум
    p.rect(0, 0, W_M, D_M, fill=(22, 23, 29), outline=LIME, width=5)

    # глухие стены: задняя 9 м и левая 5,04 м — под баннеры с брендингом
    p.d.line([xy(0, D_M), xy(W_M, D_M)], fill=LIME, width=12)
    p.d.line([xy(0, 0), xy(0, D_M)], fill=LIME, width=12)

    # 11 столбов по модели: 10 по краям + 1 внутренний
    for (x, y) in [(0, 0), (3, 0), (6, 0), (9, 0),
                   (0, 2.52), (9, 2.52),
                   (0, D_M), (3, D_M), (6, D_M), (9, D_M), (4.5, 2.52)]:
        p.post(x, y)

    # ---- зоны
    p.rect(0.12, 0.95, 0.53, 3.50, fill=(48, 44, 72), outline=VIOLET, width=2)
    p.label(0.33, 3.86, "ВЕБТУНЫ", 18, VIOLET)

    p.rect(1.10, 3.60, 3.45, 4.98, fill=(34, 34, 44), outline=LIME, width=2)
    p.label(2.28, 4.64, "АНИМЕ-ЛАУНЖ", 21, LIME)
    for (cx, cy) in ((1.55, 4.25), (2.45, 4.25), (1.55, 3.62), (2.45, 3.62)):
        p.circle(cx, cy, 0.28, fill=(70, 66, 100), outline=VIOLET, width=2)

    p.rect(3.65, 3.60, 5.35, 4.98, fill=(40, 40, 52), outline=LIME, width=2)
    p.label(4.50, 4.74, "ПОСТЕРЫ", 20, INK)

    p.rect(2.35, 2.05, 4.35, 2.55, fill=(56, 58, 68), outline=INK, width=2)
    p.label(3.35, 2.30, "КАССА", 22, INK)

    p.rect(8.28, 1.69, 8.92, 2.87, fill=(60, 70, 40), outline=LIME, width=2)
    p.label(8.60, 1.34, "ГАЧА", 18, LIME)

    p.rect(7.55, 3.35, 8.98, 4.98, fill=(20, 20, 25), outline=GREY, width=2)
    p.label(8.26, 4.16, "КЛАДОВАЯ", 17, GREY)

    p.rect(7.93, 2.51, 8.77, 3.19, fill=(30, 46, 38), outline=LIME, width=2)
    p.label(8.35, 2.85, "БУДКА", 17, INK)

    p.rect(5.05, 4.10, 5.95, 4.58, fill=(52, 54, 62), outline=GREY, width=2)
    p.label(5.50, 3.86, "тележка", 13, GREY)

    p.circle(1.15, 1.65, 0.24, outline=GREY, width=2)
    p.label(1.62, 1.65, "вертушка", 13, GREY, "lm")

    for i in range(3):
        p.circle(0.98, 1.35 + i * 0.55, 0.16, outline=LIME, width=2)

    # вход по центру фронта
    p.d.line([xy(3.3, 0), xy(5.7, 0)], fill=VIOLET, width=12)
    p.label(4.5, -0.30, "ВХОД", 23, VIOLET)

    # размеры
    p.dim_h(0, W_M, 120, "9 000 мм")
    p.dim_v(0, D_M, 0.0, "5 040 мм", off=150)

    # оси столбов
    for x in (0, 3, 6, 9):
        p.label(x, D_M + 0.34, f"{int(x*1000)}", 16, GREY)

    # штамп
    p.d.text((MARGIN_L, 40), "TOPOTOON × COMIC CON  ·  ПЛАН 9,00 × 5,04 м",
             font=font(40), fill=INK)
    p.d.text((MARGIN_L, 96), "11 столбов 100×100 · столбы 3 000 · обвязка 3 240 · подиум 50 мм",
             font=man(28, "500"), fill=GREY)
    p.d.text((CV_W - MARGIN_R, 96), "SM-Production · 27.10.2026 · вид сверху",
             font=man(24, "600"), fill=GREY, anchor="ra")

    out = os.path.join(BASE, "..", "renders3d", "07-plan.png")
    p.im.save(out, optimize=True)
    print("  готов 07-plan.png", p.im.size)


if __name__ == "__main__":
    build()
