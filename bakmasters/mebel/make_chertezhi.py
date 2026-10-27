#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Чертежи столика для ноутбука: план, разрез, механизм наклона, электрика, вариант «Кровать».

Все размеры в миллиметрах, на листе пересчитываются через масштаб.
"""
import os

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, '..', '..', 'docs', 'ca-avtosalony', '02_prezentaciya', 'fonts')
OUT = os.path.join(HERE, 'chertezhi-stolika.pdf')

INK = (0x2B / 255, 0x26 / 255, 0x21 / 255)
MUTED = (0x7A / 255, 0x6F / 255, 0x63 / 255)
ACC = (0x2F / 255, 0x6F / 255, 0x6B / 255)
LIGHT = (0.86, 0.83, 0.78)
PAPER = (0.995, 0.988, 0.972)
HATCH = (0.72, 0.69, 0.64)

pdfmetrics.registerFont(TTFont('M-400', os.path.join(FONTS, 'Manrope-400.ttf')))
pdfmetrics.registerFont(TTFont('M-600', os.path.join(FONTS, 'Manrope-600.ttf')))
pdfmetrics.registerFont(TTFont('M-700', os.path.join(FONTS, 'Manrope-700.ttf')))
pdfmetrics.registerFont(TTFont('M-800', os.path.join(FONTS, 'Manrope-800.ttf')))

PW, PH = landscape(A4)
TOTAL = 5


def X(v):
    return v * mm


class Sheet:
    def __init__(self, c, num, title, subtitle='', scale_txt=''):
        self.c = c
        self.num = num
        c.setFillColor(PAPER)
        c.rect(0, 0, PW, PH, fill=1, stroke=0)
        # рамка листа
        c.setStrokeColor(LIGHT)
        c.setLineWidth(0.8)
        c.rect(8 * mm, 8 * mm, PW - 16 * mm, PH - 16 * mm, fill=0, stroke=1)

        c.setFillColor(ACC)
        c.setFont('M-700', 7.5)
        c.drawString(13 * mm, PH - 15 * mm, 'BAK MASTERS  ·  BAK HOME  ·  СТОЛИК ДЛЯ НОУТБУКА')
        c.setFillColor(INK)
        c.setFont('M-800', 15)
        c.drawString(13 * mm, PH - 23 * mm, title)
        if subtitle:
            c.setFillColor(MUTED)
            c.setFont('M-400', 8)
            c.drawString(13 * mm, PH - 28.5 * mm, subtitle)

        # штамп справа
        c.setStrokeColor(LIGHT)
        c.setLineWidth(0.6)
        c.line(PW - 78 * mm, PH - 32 * mm, PW - 13 * mm, PH - 32 * mm)
        if scale_txt:
            c.setFillColor(MUTED)
            c.setFont('M-600', 7)
            c.drawRightString(PW - 13 * mm, PH - 29.5 * mm, scale_txt)
        c.setFillColor(MUTED)
        c.setFont('M-400', 6.5)
        c.drawRightString(PW - 13 * mm, PH - 36 * mm, 'размеры в мм · октябрь 2026')
        c.drawRightString(PW - 13 * mm, PH - 40 * mm, 'лист %d из %d' % (num, TOTAL))

    # ---------- примитивы ----------
    def line(self, x1, y1, x2, y2, w=0.4, color=INK, dash=None):
        c = self.c
        c.setStrokeColor(color)
        c.setLineWidth(w)
        if dash:
            c.setDash(dash, 2)
        c.line(X(x1), X(y1), X(x2), X(y2))
        c.setDash([], 0)

    def rect(self, x, y, w, h, lw=0.4, color=INK, fill=None, dash=None, r=0):
        c = self.c
        c.setStrokeColor(color)
        c.setLineWidth(lw)
        if dash:
            c.setDash(dash, 2)
        if fill:
            c.setFillColor(fill)
        if r:
            c.roundRect(X(x), X(y), X(w), X(h), X(r), fill=1 if fill else 0, stroke=1)
        else:
            c.rect(X(x), X(y), X(w), X(h), fill=1 if fill else 0, stroke=1)
        c.setDash([], 0)

    def text(self, x, y, s, size=7, font='M-400', color=INK, anchor='left', angle=0):
        c = self.c
        c.setFillColor(color)
        c.setFont(font, size)
        if angle:
            c.saveState()
            c.translate(X(x), X(y))
            c.rotate(angle)
            if anchor == 'center':
                c.drawCentredString(0, 0, s)
            else:
                c.drawString(0, 0, s)
            c.restoreState()
        elif anchor == 'center':
            c.drawCentredString(X(x), X(y), s)
        elif anchor == 'right':
            c.drawRightString(X(x), X(y), s)
        else:
            c.drawString(X(x), X(y), s)

    def _arrow_head(self, x, y, dx, dy, size=1.6, color=INK):
        c = self.c
        import math
        ang = math.atan2(dy, dx)
        for a in (ang + 2.6, ang - 2.6):
            c.setStrokeColor(color)
            c.setLineWidth(0.5)
            c.line(X(x), X(y), X(x + size * math.cos(a)), X(y + size * math.sin(a)))

    def dim_h(self, x1, x2, y, label, off=6, size=6.5):
        c = self.c
        self.line(x1, y, x2, y, 0.35, MUTED)
        self.line(x1, y - 1.2, x1, y + 1.2, 0.35, MUTED)
        self.line(x2, y - 1.2, x2, y + 1.2, 0.35, MUTED)
        self._arrow_head(x1, y, -1, 0, color=MUTED)
        self._arrow_head(x2, y, 1, 0, color=MUTED)
        self.text((x1 + x2) / 2, y + 1.8, label, size, 'M-600', MUTED, 'center')

    def dim_v(self, y1, y2, x, label, size=6.5):
        self.line(x, y1, x, y2, 0.35, MUTED)
        self.line(x - 1.2, y1, x + 1.2, y1, 0.35, MUTED)
        self.line(x - 1.2, y2, x + 1.2, y2, 0.35, MUTED)
        self._arrow_head(x, y1, 0, -1, color=MUTED)
        self._arrow_head(x, y2, 0, 1, color=MUTED)
        c = self.c
        c.saveState()
        c.translate(X(x - 1.8), X((y1 + y2) / 2))
        c.rotate(90)
        c.setFillColor(MUTED)
        c.setFont('M-600', size)
        c.drawCentredString(0, 0, label)
        c.restoreState()

    def leader(self, px, py, tx, ty, num, side='left'):
        """выноска: точка на детали → номер в кружке → текст рядом"""
        self.line(px, py, tx, ty, 0.35, ACC)
        c = self.c
        c.setFillColor(ACC)
        c.circle(X(tx), X(ty), X(2.6), fill=1, stroke=0)
        c.setFillColor(PAPER)
        c.setFont('M-700', 6)
        c.drawCentredString(X(tx), X(ty) - 2.1, str(num))

    def hatch(self, x, y, w, h, step=2.2):
        c = self.c
        c.saveState()
        p = c.beginPath()
        p.rect(X(x), X(y), X(w), X(h))
        c.clipPath(p, stroke=0, fill=0)
        c.setStrokeColor(HATCH)
        c.setLineWidth(0.25)
        d = x + y
        yy = y - w
        while yy < y + h + w:
            c.line(X(yy + d), X(y), X(yy + d + h), X(y + h))
            yy += step
        c.restoreState()

    def wrap_text(self, x, y, text, size=6.4, font='M-400', color=MUTED, maxw=80, lead=8.6):
        words = text.split()
        line = ''
        c = self.c
        for w in words:
            t = (line + ' ' + w).strip()
            if pdfmetrics.stringWidth(t, font, size) <= maxw * mm:
                line = t
            else:
                c.setFillColor(color)
                c.setFont(font, size)
                c.drawString(X(x), y, line)
                y -= lead
                line = w
        if line:
            c.setFillColor(color)
            c.setFont(font, size)
            c.drawString(X(x), y, line)
            y -= lead
        return y

    def end(self):
        self.c.showPage()


def disc(s, cx, cy, r, lw=0.4, color=INK, fill=None, dash=None):
    c = s.c
    c.setStrokeColor(color)
    c.setLineWidth(lw)
    if dash:
        c.setDash(dash, 2)
    if fill:
        c.setFillColor(fill)
    c.circle(X(cx), X(cy), X(r), fill=1 if fill else 0, stroke=1)
    c.setDash([], 0)


def arrow_curved(s, pts, color=ACC, w=0.9):
    c = s.c
    c.setStrokeColor(color)
    c.setLineWidth(w)
    p = c.beginPath()
    p.moveTo(X(pts[0][0]), X(pts[0][1]))
    for i in range(1, len(pts) - 1, 2):
        x2, y2 = pts[i]
        x3, y3 = pts[i + 1]
        p.curveTo(X(x2), X(y2), X(x3), X(y3), X(x3), X(y3))
    c.drawPath(p, stroke=1, fill=0)
    if len(pts) >= 2:
        (x1, y1), (x2, y2) = pts[-2], pts[-1]
        s._arrow_head(x2, y2, x2 - x1, y2 - y1, 2.0, color)


# ============================ ЛИСТ 1. ПЛАН ============================
def sheet1(c):
    s = Sheet(c, 1, 'План: столешница 700 × 450',
              'Вентиляционные площадки, паз под телефон, катушка Qi, скрытая лапа',
              '1 : 4,5')
    k = 0.19
    W, D = 450 * k, 700 * k
    ox, oy = 40, 86
    L = ox + D

    s.rect(ox, oy, D, W, 0.7, INK, fill=(0.965, 0.945, 0.915))

    # лапа под диваном
    s.rect(L - 40 * k, oy + 25 * k, 40 * k, 400 * k, 0.4, MUTED, dash=[2, 2])
    s.rect(L - 450 * k, oy + 205 * k, 410 * k, 40 * k, 0.4, MUTED, dash=[2, 2])
    s.rect(L - 40 * k, oy + 205 * k, 40 * k, 40 * k, 0.7, ACC, fill=(0.86, 0.92, 0.90))

    # зоны обдува
    for cx in (330, 470):
        zx = ox + cx * k
        zy = oy + 175 * k
        s.rect(zx, zy, 120 * k, 100 * k, 0.4, ACC, dash=[1.5, 1.5])
        for i in range(10):
            sx = zx + (4 + i * 12) * k
            s.rect(sx, zy + 20 * k, 4 * k, 60 * k, 0.3, INK, fill=INK)

    disc(s, ox + 610 * k, oy + 90 * k, 45 * k, 0.45, INK, fill=(0.93, 0.90, 0.84))
    disc(s, ox + 610 * k, oy + 90 * k, 32 * k, 0.3, MUTED)

    s.rect(ox + 70 * k, oy + 60 * k, 100 * k, 13 * k, 0.5, INK, fill=(0.88, 0.85, 0.80))

    s.line(ox + 590 * k, oy + 225 * k, L - 45 * k, oy + 225 * k, 0.45, ACC, dash=[1.2, 1.2])
    s.line(ox + 450 * k, oy + 225 * k, ox + 470 * k, oy + 225 * k, 0.45, ACC, dash=[1.2, 1.2])

    # размеры под планом
    s.dim_h(ox, L, oy - 26, '700')
    s.dim_h(ox, ox + 70 * k, oy - 34, '70')
    s.dim_h(ox + 330 * k, ox + 450 * k, oy - 18, '120')
    s.dim_h(L - 450 * k, L, oy - 42, 'лапа 450 (уходит под диван)', 6)
    s.dim_v(oy, oy + W, ox - 10, '450')

    # подписи на плане
    s.text(ox + 335 * k, oy + 150 * k, 'зона 1', 6.2, 'M-600', ACC)
    s.text(ox + 475 * k, oy + 150 * k, 'зона 2', 6.2, 'M-600', ACC)
    s.text(ox + 30 * k, oy + 82 * k, 'паз', 6.2, 'M-600', INK)
    s.text(ox + 570 * k, oy + 60 * k, 'Qi', 6.4, 'M-700', INK)
    s.text(L - 36 * k, oy + 250 * k, 'стойка', 5.8, 'M-600', ACC)

    # выноски
    s.leader(ox + 390 * k, oy + 275 * k, ox + 330 * k, oy + W + 22, 1)
    s.leader(ox + 120 * k, oy + 66 * k, ox + 120 * k, oy + 150 * k, 2)
    s.leader(ox + 610 * k, oy + 90 * k, ox + 600 * k, oy - 12, 3)
    s.leader(ox + 560 * k, oy + 225 * k, ox + 640 * k, oy + 330 * k, 4)

    # ---- правая колонка: легенда ----
    lx = 208
    ly = PH - 56 * mm
    c.setFillColor(INK)
    c.setFont('M-700', 8)
    c.drawString(X(lx), ly, 'Обозначения')
    items = [
        ('1', 'Зона обдува 2 × (120 × 100), щели 4 × 60, шаг 12'),
        ('2', 'Паз под телефон 100 × 13, 65°, силикон 2 мм'),
        ('3', 'Катушка Qi Ø90, дерево над катушкой 3 мм'),
        ('4', 'Кабель-канал в пазу 6 × 4 мм, вывод в стойку'),
    ]
    yy = ly - 20
    for num, txt in items:
        c.setFillColor(ACC)
        c.circle(X(lx + 1.8), yy + 2.0, X(2.2), fill=1, stroke=0)
        c.setFillColor(PAPER)
        c.setFont('M-700', 5.6)
        c.drawCentredString(X(lx + 1.8), yy - 0.4, num)
        s.wrap_text(lx + 6, yy, txt, 6.3, 'M-400', MUTED, maxw=76, lead=8.4)
        yy -= 23

    # ---- правая колонка: расчёт ----
    y2 = yy - 14
    c.setFillColor(ACC)
    c.setFont('M-700', 7.4)
    c.drawString(X(lx), y2, 'Почему щели не мешают потоку')
    y2 = s.wrap_text(lx, y2 - 16,
                     'Живое сечение 48 см². При расходе 40 м³/ч скорость в щелях '
                     '2,3 м/с, перепад давления 4,8 Па — для вентилятора это ничто. '
                     'Ограничивает поток решётка забора самого ноутбука, а не столешница.',
                     6.3, 'M-400', MUTED, maxw=76, lead=8.6)

    y2 -= 14
    c.setFillColor(ACC)
    c.setFont('M-700', 7.4)
    c.drawString(X(lx), y2, 'Почему зоны смещены назад')
    s.wrap_text(lx, y2 - 16,
                'Поток дует вверх, в днище. Если поставить зоны по центру столешницы, '
                'они окажутся под запястьями, а ноутбук сдвинут назад — обдув уйдёт мимо. '
                'Задняя треть совпадает с зоной вентиляции у 15–17 дюймовых корпусов.',
                6.3, 'M-400', MUTED, maxw=76, lead=8.6)
    s.end()


# ============================ ЛИСТ 2. РАЗРЕЗ ============================
def sheet2(c):
    s = Sheet(c, 2, 'Разрез по оси столика: обдув и высота',
              'Показан зазор под ноутбуком, карман вентилятора, кабель-канал и телескоп',
              '1 : 5')
    ox, oy = 34, 46
    k = 0.155
    # координаты в мм модели
    H = 700          # высота столешницы
    TH = 30          # толщина
    floor = 0

    # пол
    s.line(ox - 6, oy, ox + 720 * k + 10, oy, 0.7, MUTED)
    s.hatch(ox - 6, oy - 3, 720 * k + 16, 3)

    # столешница
    s.rect(ox, oy + (H - TH) * k, 700 * k, TH * k, 0.7, INK, fill=(0.95, 0.92, 0.88))
    s.hatch(ox, oy + (H - TH) * k, 700 * k, TH * k)

    # карман вентилятора (27 мм снизу) и вентилятор 25
    px = ox + 370 * k
    s.rect(px, oy + (H - TH - 27) * k, 100 * k, 27 * k, 0.4, MUTED, fill=(0.99, 0.99, 0.99))
    s.rect(px + 2 * k, oy + (H - TH - 27 + 2) * k, 96 * k, 25 * k, 0.45, ACC,
           fill=(0.86, 0.92, 0.90))
    # щели в столешнице
    for gx in (400, 430, 460):
        s.rect(ox + gx * k, oy + (H - TH) * k, 4 * k, TH * k, 0.3, PAPER, fill=PAPER)

    # ноутбук с зазором 10
    lap_y = oy + (H + 10) * k
    s.rect(ox + 250 * k, lap_y, 230 * k, 15 * k, 0.6, INK, fill=(0.90, 0.90, 0.90))
    s.text(ox + 365 * k, lap_y + 5 * k, 'ноутбук 16", 2,5 кг', 6, 'M-600', INK, 'center')
    s.dim_v(oy + (H + 0) * k, oy + (H + 10) * k, ox + 240 * k, '10')

    # стойка
    s.rect(ox + 660 * k, oy, 30 * k, (H - TH) * k, 0.6, INK, fill=(0.93, 0.93, 0.93))
    s.rect(ox + 665 * k, oy, 25 * k, (H - TH - 20) * k, 0.4, MUTED)
    # лапа
    s.rect(ox + 250 * k, oy, 440 * k, 30 * k, 0.6, INK, fill=(0.93, 0.93, 0.93))
    s.rect(ox + 250 * k, oy - 8, 60 * k, 8, 0.4, INK, fill=(0.80, 0.80, 0.80))

    # стрелки воздуха
    arrow_curved(s, [(ox + 405 * k, oy + (H - TH - 26) * k),
                     (ox + 400 * k, oy + (H - 6) * k),
                     (ox + 402 * k, oy + (H + 4) * k)])
    arrow_curved(s, [(ox + 425 * k, oy + (H - TH - 26) * k),
                     (ox + 432 * k, oy + (H - 6) * k),
                     (ox + 430 * k, oy + (H + 4) * k)])
    arrow_curved(s, [(ox + 450 * k, oy + (H - TH - 26) * k),
                     (ox + 462 * k, oy + (H - 6) * k),
                     (ox + 460 * k, oy + (H + 4) * k)])
    s.text(ox + 150 * k, oy + (H + 26) * k, 'поток в днище ноутбука', 7, 'M-700', ACC)

    # размеры
    s.dim_h(ox, ox + 700 * k, oy - 16, '700')
    s.dim_h(ox, ox + 250 * k, oy + 40 * k, '250 (вылет за ось)', 6)
    s.dim_v(oy, oy + H * k, ox - 8, '620–760')
    s.dim_v(oy + (H - TH) * k, oy + H * k, ox + 720 * k, '30')

    # выноски
    s.leader(ox + 430 * k, oy + (H - TH - 14) * k, ox + 250 * k, oy + (H - TH - 70) * k, 1)
    s.leader(ox + 404 * k, oy + (H - 15) * k, ox + 640 * k, oy + (H + 40) * k, 2)
    s.leader(ox + 676 * k, oy + 300 * k, ox + 620 * k, oy + 430 * k, 3)
    s.leader(ox + 300 * k, oy + 15 * k, ox + 170 * k, oy + 110 * k, 4)

    lx = 196
    ly = PH - 52 * mm
    c.setFillColor(INK)
    c.setFont('M-700', 8)
    c.drawString(X(lx), ly, 'Что на разрезе')
    rows = [
        ('1', 'Карман 27 мм снизу: вентилятор 25 мм + прокладка 2 мм.'),
        ('', 'Сверху остаётся 3 мм массива — не проваливается, не гудит.'),
        ('2', 'Щели 4 × 60: воздух выходит ровно под решётку ноутбука.'),
        ('3', 'Телескоп 30×30 / 25×25 + втулка POM: люфт убирается полностью.'),
        ('4', 'Лапа 450 мм с балластом 3,5 кг: держит 16 кг на краю.'),
    ]
    yy = ly - 6 * mm
    for num, txt in rows:
        if num:
            c.setFillColor(ACC)
            c.circle(X(lx + 1.8), X(yy / mm) + 2.0, X(2.2), fill=1, stroke=0)
            c.setFillColor(PAPER)
            c.setFont('M-700', 5.6)
            c.drawCentredString(X(lx + 1.8), X(yy / mm) - 0.4, num)
        c.setFillColor(MUTED)
        c.setFont('M-400', 6.5)
        c.drawString(X(lx + 6), yy, txt)
        yy -= 6.2 * mm
    s.end()


# ============================ ЛИСТ 3. НАКЛОН ============================
def sheet3(c):
    s = Sheet(c, 3, 'Механизм наклона: шарнир и зубчатые упоры',
              'Положения 0° / 4° / 8° / 12°, нагрузка на упор 104 Н (10,6 кг)', '1 : 3')
    k = 0.44
    import math
    ox, oy = 34, 176      # ось шарнира
    px, py = ox + 13 * k, oy

    # стойка
    s.rect(ox, oy - 150 * k, 26 * k, 150 * k, 0.6, INK, fill=(0.93, 0.93, 0.93))
    s.text(ox + 3, oy - 152 * k, 'стойка', 6.4, 'M-600', MUTED)

    # положения
    for ang, col, lw in [(0, (0.86, 0.83, 0.78), 0.5), (4, (0.86, 0.83, 0.78), 0.5),
                         (8, (0.70, 0.66, 0.60), 0.6), (12, INK, 0.9)]:
        a = math.radians(ang)
        L = 250 * k
        # плита толщиной 30 мм: две параллельные линии со смещением по нормали
        nx, ny = -math.sin(a), -math.cos(a)
        t = 30 * k
        s.line(px, py, px + L * math.cos(a), py - L * math.sin(a), lw, col)
        s.line(px + nx * t, py + ny * t, px + L * math.cos(a) + nx * t,
               py - L * math.sin(a) + ny * t, lw * 0.8, col)
        x2 = px + L * math.cos(a)
        y2 = py - L * math.sin(a)
        s.text(x2 + 2, y2 - 1, '%d°' % ang, 6.6,
               'M-600' if ang == 12 else 'M-400', INK if ang == 12 else MUTED)
    s.text(px + 250 * k, py - 26, 'плита 30 мм', 5.8, 'M-400', MUTED)

    # дуга угла
    s.c.setStrokeColor(ACC)
    s.c.setLineWidth(0.6)
    s.c.arc(X(px - 30 * k), X(py - 30 * k), X(px + 30 * k), X(py + 30 * k), 0, 12)

    # упор и зубья на стойке
    ux = px + 82 * k
    s.line(ux, py - 6, ux + 3, py - 96 * k, 1.2, ACC)
    for i in range(4):
        gy = py - 30 * k - i * 18 * k
        s.line(ox + 20 * k, gy, ox + 28 * k, gy - 5, 0.9, INK)
    s.text(ux + 4, py - 104 * k, 'упор', 6.6, 'M-600', ACC)
    s.text(ox + 30 * k, py - 26 * k, 'зубья, 4 положения', 6, 'M-400', MUTED)

    # щиток
    s.c.setFillColorRGB(0.85, 0.90, 0.89)
    s.c.setStrokeColor(ACC)
    s.c.setLineWidth(0.4)
    s.c.setDash([1.2, 1.2], 0)
    s.c.rect(X(ux - 2), X(py - 30 * k), X(22 * k), X(13 * k), fill=1, stroke=1)
    s.c.setDash([], 0)
    s.text(ux + 1, py - 25 * k, 'щиток', 5.6, 'M-400', ACC)

    # ---- узел А крупно (под схемой) ----
    ax, ay = 36, 34
    s.text(ax - 2, ay + 62, 'Узел А (1 : 1): шарнир в сборе', 6.8, 'M-700', INK)
    # плита
    s.rect(ax, ay + 32, 76, 24, 0.6, INK, fill=(0.95, 0.92, 0.88))
    s.text(ax + 3, ay + 40, 'плита 30 мм', 5.4, 'M-400', MUTED)
    # серьга в кармане плиты
    s.rect(ax + 34, ay + 20, 22, 12, 0.5, ACC, fill=(0.86, 0.92, 0.90))
    s.text(ax + 58, ay + 23, 'серьга', 5.4, 'M-400', MUTED)
    # ось
    s.rect(ax + 40, ay + 2, 9, 54, 0.5, INK, fill=(0.90, 0.90, 0.90))
    # гайка
    s.rect(ax + 37, ay + 56, 15, 5, 0.4, INK, fill=(0.78, 0.78, 0.78))
    s.text(ax + 54, ay + 57, 'гайка М10', 5.2, 'M-400', MUTED)
    # шайбы
    s.rect(ax + 34, ay + 46, 21, 3, 0.35, MUTED, fill=(0.95, 0.95, 0.95))
    s.text(ax + 58, ay + 46, 'шайба нейлон', 5.2, 'M-400', MUTED)
    # втулка
    s.rect(ax + 38, ay + 10, 13, 8, 0.35, ACC, fill=(0.90, 0.95, 0.94))
    s.text(ax + 54, ay + 11, 'втулка POM', 5.2, 'M-400', ACC)
    # упор
    s.line(ax + 2, ay + 36, ax + 33, ay + 22, 1.2, ACC)
    s.text(ax + 2, ay + 26, 'упор в зуб', 5.4, 'M-600', ACC)
    s.text(ax + 30, ay - 8, 'ось Ø10, затяжка к гайке — без люфта', 5.2, 'M-400', MUTED)
    # ---- правая колонка ----
    lx = 178
    ly = PH - 52 * mm
    c.setFillColor(INK)
    c.setFont('M-700', 8.4)
    c.drawString(X(lx), ly, 'Почему так, а не фрикцион')
    lines = [
        'Момент на шарнире: 9,1 кг · 9,81 · 0,35 м = 31 Н·м.',
        'Фрикционный шарнир столько не держит — проворачивается.',
        'Здесь момент держит геометрия: упор упирается в зуб,',
        'нагрузка на каждую из двух стоек всего 104 Н (10,6 кг).',
        '',
        'Смена положения: приподнять столешницу на 10 мм,',
        'перевести на нужный угол и опустить в следующий зуб.',
        'Случайно не переставишь, ребёнок не сложат.',
        '',
        'Зона между столешницей и упором закрыта щитком.',
    ]
    yy = ly - 18
    for txt in lines:
        c.setFillColor(MUTED)
        c.setFont('M-400', 6.6)
        c.drawString(X(lx), yy, txt)
        yy -= 8.6

    yy -= 14
    c.setFillColor(INK)
    c.setFont('M-700', 7.4)
    c.drawString(X(lx), yy, 'Допуски и материалы')
    c.setFillColor(MUTED)
    c.setFont('M-400', 6.5)
    for i, txt in enumerate(['отверстие под ось Ø10,2, шайбы нейлоновые',
                             'зубья: шаг ±0,3 мм, закалка или нерж.',
                             'швы зачищены в зоне хода упора',
                             'пружина возврата не нужна: держит вес']):
        c.drawString(X(lx), yy - 16 - i * 8.4, txt)
    s.end()


# ============================ ЛИСТ 4. ЭЛЕКТРИКА ============================
def sheet4(c):
    s = Sheet(c, 4, 'Электрика и зарядка: схема',
              'Один вход USB-C PD питает и вентиляторы, и беспроводную зарядку телефона')

    def box(x, y, w, h, title, sub='', fill=(1, 1, 1), color=INK, tsize=7.2):
        s.rect(x, y, w, h, 0.6, color, fill=fill, r=1.2)
        s.text(x + 3, y + h - 6.0, title, tsize, 'M-700', INK)
        if sub:
            s.text(x + 3, y + 2.8, sub, 5.7, 'M-400', MUTED)

    def flow(x1, y1, x2, y2, label=''):
        s.line(x1, y1, x2, y2, 0.9, ACC)
        s._arrow_head(x2, y2, x2 - x1, y2 - y1, 2.0, ACC)
        if label:
            s.text((x1 + x2) / 2 + 1.5, (y1 + y2) / 2 - 0.5, label, 5.5, 'M-400', MUTED)

    R, H = 118, 20
    box(20, R, 50, H, 'USB-C PD', '20 В, 30–45 Вт', (0.96, 0.94, 0.91))
    box(82, R, 50, H, 'Защита', 'предохр. 2 А, TVS')
    box(144, R, 50, H, 'Триггер PD', 'фиксированный 20 В')
    box(206, R, 54, H, 'Шина 12 В', 'общая', (0.86, 0.92, 0.90))
    flow(70, R + 10, 82, R + 10)
    flow(132, R + 10, 144, R + 10)
    flow(194, R + 10, 206, R + 10)

    # вверх: Qi
    box(206, R + 34, 54, 22, 'Qi 15 Вт', 'катушка Ø55 · FOD', (0.93, 0.95, 0.90))
    flow(233, R + 20, 233, R + 34)

    # вниз: обдув
    box(206, R - 42, 54, 20, 'DC-DC 5 В', 'до 2 А', (0.93, 0.95, 0.90))
    flow(233, R, 233, R - 22)
    s.text(237, R - 14, '12 → 5 В', 5.5, 'M-400', MUTED)
    box(206, R - 80, 54, 20, 'Контроллер', '3 скорости, кнопка')
    flow(233, R - 42, 233, R - 60)
    box(124, R - 80, 68, 20, '2 вентилятора', '120 мм, 5 В, 0,55 Вт')
    flow(206, R - 70, 192, R - 70)

    # бюджет
    c.setFillColor(ACC)
    c.setFont('M-700', 7.4)
    c.drawString(X(20), X(R - 34), 'Бюджет мощности')
    c.setFillColor(MUTED)
    c.setFont('M-400', 6.4)
    for i, t in enumerate([
            'Вентиляторы 2 × 0,55 = 1,1 Вт, контроллер 0,3 Вт, Qi до 12 Вт.',
            'На выходе до 13,5 Вт; от адаптера при КПД 85 % — до 16 Вт.',
            'Адаптер: USB-C PD 30 Вт. 45 Вт — если заряжать телефон',
            'по проводу одновременно с Qi и обдувом.']):
        c.drawString(X(20), X(R - 40 - i * 4.5), t)

    # правила — две колонки внизу
    c.setFillColor(ACC)
    c.setFont('M-700', 7.4)
    c.drawString(X(20), X(36), 'Правила монтажа')
    left = [
        'Катушка и стальной каркас: зазор ≥ 10 мм, иначе металл греется вихревыми токами.',
        'Дерево над катушкой 3 мм: на 5 мм КПД падает до 65 %, на 8 мм мощности почти нет.',
        'Армирующее кольцо из фанеры 3 мм вокруг кармана: тонкий слой без него ломается.',
    ]
    right = [
        'Кабель в пазу 6 × 4 мм, в стойку — через резиновую втулку, гнездо утоплено на 3 мм.',
        'Разгрузка натяжения: 10 кг на кабель не доходят до платы. Отсек IP20, у задней кромки.',
    ]
    c.setFillColor(MUTED)
    c.setFont('M-400', 6.2)
    for i, t in enumerate(left):
        c.drawString(X(20), X(30 - i * 5.4), '· ' + t)
    for i, t in enumerate(right):
        c.drawString(X(152), X(30 - i * 5.4), '· ' + t)

    c.setFillColor(MUTED)
    c.setFont('M-600', 6.2)
    c.drawString(X(20), X(11), 'Сертификация: уточнить ТР ТС 004/2011 и 020/2011 — '
                               'зависит от того, входит ли адаптер в комплект.')
    s.end()


# ============================ ЛИСТ 5. КРОВАТЬ ============================
def sheet5(c):
    s = Sheet(c, 5, 'Вариант «Кровать»: трай на четырёх ногах',
              'С-каркас на матрас не ставится: узкая пятка тонет, столик заваливается',
              '1 : 6')
    k = 0.17
    ox, oy = 24, 42          # пол
    H, TH = 760, 25

    # ---- вид сбоку ----
    s.line(ox - 4, oy, ox + 700 * k + 12, oy, 0.7, MUTED)
    s.hatch(ox - 4, oy - 3, 700 * k + 16, 3)

    # ноги
    for lx in (110, 590):
        s.rect(ox + lx * k, oy + 70 * k, 22 * k, (H - TH - 70) * k, 0.6, INK,
               fill=(0.93, 0.93, 0.93))
        # пятка 200 × 70
        s.rect(ox + (lx - 89) * k, oy, 200 * k, 70 * k, 0.5, INK, fill=(0.80, 0.80, 0.80))

    # столешница
    s.rect(ox, oy + (H - TH) * k, 700 * k, TH * k, 0.7, INK, fill=(0.95, 0.92, 0.88))
    s.hatch(ox, oy + (H - TH) * k, 700 * k, TH * k)

    # бортик
    s.line(ox, oy + (H - TH) * k, ox, oy + (H + 8) * k, 1.2, ACC)
    s.line(ox, oy + (H + 8) * k, ox + 8 * k, oy + (H + 8) * k, 1.2, ACC)
    s.text(ox + 1.5, oy + (H + 12) * k, 'бортик 8', 6, 'M-600', ACC)

    # размеры
    s.dim_h(ox, ox + 700 * k, oy - 14, '700')
    s.dim_h(ox + (110 - 89) * k, ox + (110 + 111) * k, oy - 6, '200', 6)
    s.dim_v(oy, oy + H * k, ox - 9, '700–800')
    s.dim_v(oy + (H - TH) * k, oy + H * k, ox + 700 * k + 6, '25')

    # ---- план сверху справа ----
    kp = 0.135
    px, py = 168, 126
    s.rect(px, py, 700 * kp, 450 * kp, 0.7, INK, fill=(0.965, 0.945, 0.915))
    for lx, ly in ((99, 70), (579, 70), (99, 358), (579, 358)):
        s.rect(px + lx * kp, py + ly * kp, 22 * kp, 22 * kp, 0.4, INK, fill=(0.80, 0.80, 0.80))
    s.text(px, py + 450 * kp + 5, 'план: ноги по углам, отступ 110 × 70 мм', 6.2, 'M-600', MUTED)
    s.dim_h(px, px + 700 * kp, py - 7, '700')
    s.dim_v(py, py + 450 * kp, px - 7, '450')

    # ---- сравнение ----
    tx, ty = 168, 112
    c.setFillColor(INK)
    c.setFont('M-700', 7.4)
    c.drawString(X(tx), X(ty), 'Чем «Кровать» отличается от «Софы»')
    rows = [
        ('Опора', '4 складные ноги', '1 стойка + лапа'),
        ('Пятки', '200 × 70, силикон 3 мм', '40 × 450, балласт 3,5 кг'),
        ('Бортик', '8 мм по трём сторонам', 'нет'),
        ('Вес', '≤ 7,5 кг', '12,8 кг'),
        ('Нагрузка', '10 кг', '8 кг, на край 16 кг'),
        ('Складывается', 'чехол 700×450×75', 'не складывается'),
    ]
    cx = [tx, tx + 34, tx + 88]
    yy = ty - 6
    c.setFillColor(MUTED)
    c.setFont('M-700', 6.1)
    for i, hh in enumerate(['', 'Кровать', 'Софа']):
        c.drawString(X(cx[i]), X(yy), hh)
    yy -= 5
    for r in rows:
        for i, v in enumerate(r):
            c.setFillColor(MUTED if i == 0 else INK)
            c.setFont('M-400' if i == 0 else 'M-600', 6.1)
            c.drawString(X(cx[i]), X(yy), v)
        yy -= 5.2

    # ---- почему широкие пятки ----
    c.setFillColor(ACC)
    c.setFont('M-700', 7.2)
    c.drawString(X(tx), X(yy - 5), 'Почему пятки широкие')
    c.setFillColor(MUTED)
    c.setFont('M-400', 6.2)
    for i, t in enumerate([
            'Узкая ножка тонет в матрасе, столик перекашивается и опрокидывает чашку.',
            'Пятка 200 × 70 с силиконом 3 мм распределяет 10 кг так, что матрас',
            'проминается на 4–6 мм, а не на 40. Проверять на мягком матрасе.',
    ]):
        c.drawString(X(tx), X(yy - 10 - i * 4.6), t)

    # ---- сноска слева ----
    c.setFillColor(MUTED)
    c.setFont('M-400', 6.2)
    c.drawString(X(24), X(19), 'Наклон у «Кровати» не делаем: на мягком матрасе плита и так под углом.')
    c.drawString(X(24), X(14), 'Вместо него — бортик 8 мм, чтобы телефон и чашка не съезжали.')
    s.end()


def main():
    c = canvas.Canvas(OUT, pagesize=landscape(A4))
    sheet1(c)
    sheet2(c)
    sheet3(c)
    sheet4(c)
    sheet5(c)
    c.save()
    print('готово:', OUT, os.path.getsize(OUT), 'Б')


if __name__ == '__main__':
    main()
