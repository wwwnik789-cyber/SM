#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Презентация «Столики для ноутбука» — A4 альбомная, для дизайнеров и клиентов."""
import os

from PIL import Image as PILImage
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(HERE, 'img')
FONTS = os.path.join(HERE, '..', '..', 'docs', 'ca-avtosalony', '02_prezentaciya', 'fonts')
OUT = os.path.join(HERE, 'SM-BAKMASTERS-Stoliki-dlya-noutbuka.pdf')

SAND = (0xF6 / 255, 0xF1 / 255, 0xE9 / 255)
WHITE = (1, 1, 1)
INK = (0x2B / 255, 0x26 / 255, 0x21 / 255)
MUTED = (0x7A / 255, 0x6F / 255, 0x63 / 255)
ACC = (0x2F / 255, 0x6F / 255, 0x6B / 255)
LINE = (0xE4 / 255, 0xDB / 255, 0xCD / 255)
DARK = (0x23 / 255, 0x20 / 255, 0x1D / 255)
SOFT = (0xEE / 255, 0xE7 / 255, 0xDB / 255)

pdfmetrics.registerFont(TTFont('M-400', os.path.join(FONTS, 'Manrope-400.ttf')))
pdfmetrics.registerFont(TTFont('M-600', os.path.join(FONTS, 'Manrope-600.ttf')))
pdfmetrics.registerFont(TTFont('M-700', os.path.join(FONTS, 'Manrope-700.ttf')))
pdfmetrics.registerFont(TTFont('M-800', os.path.join(FONTS, 'Manrope-800.ttf')))

PW, PH = landscape(A4)
M = 16 * mm
TOTAL = 10
PT = 0.3528 * mm          # 1 пункт в миллиметрах


def wrap(text, size, font='M-400', maxw=None):
    if maxw is None:
        maxw = PW - 2 * M
    words = text.split()
    out, cur = [], ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if pdfmetrics.stringWidth(t, font, size) <= maxw:
            cur = t
        else:
            if cur:
                out.append(cur)
            cur = w
    if cur:
        out.append(cur)
    return out


def text_block(c, x, y, text, size=11, font='M-400', color=INK, maxw=None, lead=None):
    lead = lead or size * PT * 1.42
    for line in wrap(text, size, font, maxw):
        c.setFillColor(color)
        c.setFont(font, size)
        c.drawString(x, y, line)
        y -= lead
    return y


def cover_image(c, path, x, y, w, h):
    im = PILImage.open(path).convert('RGB')
    ratio = max(w / im.width, h / im.height)
    im = im.resize((int(im.width * ratio) + 1, int(im.height * ratio) + 1), PILImage.LANCZOS)
    left = (im.width - w) / 2
    top = (im.height - h) / 2
    im = im.crop((int(left), int(top), int(left + w), int(top + h)))
    c.drawImage(ImageReader(im), x, y, w, h)


def footer(c, num, label='BAK MASTERS · столики для ноутбука', right_x=None, dark=False):
    col = (0.62, 0.59, 0.55) if dark else MUTED
    c.setFillColorRGB(*col)
    c.setFont('M-400', 8)
    c.drawString(M, 9 * mm, label)
    c.drawRightString((right_x if right_x else PW - M), 9 * mm, 'стр. %d из %d' % (num, TOTAL))


LOG_W, LOG_H = 1658, 868          # пропорции обрезанного логотипа


def logo(c, x, top, width=36 * mm, white=False):
    """рисует логотип, возвращает y под ним"""
    h = width * LOG_H / LOG_W
    path = os.path.join(IMG, 'logo-white.png' if white else 'logo-ink.png')
    c.drawImage(path, x, top - h, width, h, mask='auto')
    return top - h


def page_head(c, x, top, eb, white=False, width=36 * mm, eb_size=9):
    """логотип + надзаголовок; возвращает y, с которого начинать заголовок"""
    y = logo(c, x, top, width=width, white=white)
    y -= 11 * mm
    c.setFillColor(ACC if not white else (0.36, 0.78, 0.74))
    c.setFont('M-700', eb_size)
    c.drawString(x, y, eb.upper())
    return y - 7 * mm


def eyebrow(c, x, y, text):
    c.setFillColor(ACC)
    c.setFont('M-700', 9)
    c.drawString(x, y, text.upper())


def big_title(c, x, y, text, size=26, color=INK, maxw=None):
    for line in wrap(text, size, 'M-800', maxw):
        c.setFillColor(color)
        c.setFont('M-800', size)
        c.drawString(x, y, line)
        y -= size * PT * 1.16
    return y - size * PT * 0.35


def spec_rows(c, x, y, rows, maxw, label_w=42 * mm, gap=8.0 * mm, size=10.5):
    for k, v in rows:
        c.setFillColor(MUTED)
        c.setFont('M-600', 8.8)
        c.drawString(x, y, k)
        yy = y
        parts = wrap(v, size, 'M-400', maxw - label_w)
        for i, line in enumerate(parts):
            c.setFillColor(INK)
            c.setFont('M-400', size)
            c.drawString(x + label_w, yy, line)
            if i < len(parts) - 1:
                yy -= size * PT * 1.35
        y = yy - gap
    return y


def main():
    c = canvas.Canvas(OUT, pagesize=landscape(A4))
    page = 1

    # ================= 1. ОБЛОЖКА =================
    cover_image(c, os.path.join(IMG, 'nb-hero.jpg'), 0, 0, PW, PH)
    c.setFillColorRGB(0.08, 0.07, 0.06, alpha=0.58)
    c.rect(0, 0, PW, PH, fill=1, stroke=0)
    c.setFillAlpha(1)
    c.setStrokeAlpha(1)

    yb = logo(c, M, PH - M - 2 * mm, width=58 * mm, white=True)
    c.setFillColorRGB(0.72, 0.90, 0.87)
    c.setFont('M-700', 9.5)
    c.drawString(M, yb - 9 * mm, 'BAK HOME  ·  КОМБИНИРОВАННАЯ МЕБЕЛЬ ДЛЯ ДОМА')

    yb -= 32 * mm
    c.setFillColorRGB(1, 1, 1)
    c.setFont('M-800', 40)
    c.drawString(M, yb, 'Столики для ноутбука')
    c.setFont('M-400', 15)
    c.setFillColorRGB(0.94, 0.92, 0.89)
    c.drawString(M, yb - 9 * mm, 'Дерево, металл и тихое охлаждение')
    c.setFillColorRGB(0.86, 0.83, 0.79)
    c.setFont('M-400', 11.5)
    c.drawString(M, yb - 20 * mm, 'Три модели · шесть опций · проводов не видно')

    # три миниатюры
    thumbs = [('nb-hero.jpg', '4.1  Приставной'), ('nb-nakolennyj.jpg', '4.2  Наколенный'),
              ('nb-rabochij.jpg', '4.3  Рабочий стол')]
    tw, th = 62 * mm, 40 * mm
    for i, (fn, cap) in enumerate(thumbs):
        x = M + i * (tw + 6 * mm)
        y = 34 * mm
        cover_image(c, os.path.join(IMG, fn), x, y, tw, th)
        c.setFillColorRGB(1, 1, 1)
        c.setFont('M-600', 8.5)
        c.drawString(x, y - 6 * mm, cap)

    c.setFillColorRGB(0.72, 0.69, 0.65)
    c.setFont('M-400', 8.5)
    c.drawString(M, 12 * mm, 'Москва · доставка по России · октябрь 2026')
    c.showPage()
    page += 1

    # ================= 2. ЗАЧЕМ =================
    c.setFillColor(SAND)
    c.rect(0, 0, PW, PH, fill=1, stroke=0)
    cover_image(c, os.path.join(IMG, 'nb-obduv.jpg'), PW * 0.56, 0, PW * 0.44, PH)

    x = M
    y = page_head(c, x, PH - M, 'задача', width=38 * mm)
    y = big_title(c, x, y - 3 * mm, 'Ноутбук греется, и это слышно', size=27, maxw=PW * 0.47)
    y -= 2 * mm
    y = text_block(c, x, y, 'На коленях, на диване, на подоконнике — ноутбук всегда стоит там, '
                            'где нет продува. Вентилятор выходит на максимум, корпус горячий, '
                            'через час работы слышен только гул.',
                   size=11, color=MUTED, maxw=PW * 0.5)
    y -= 8 * mm

    points = [
        ('1', 'Дуем снизу, куда и должен идти воздух',
         'В днище ноутбука — решётки забора. Столик подаёт воздух именно туда, а не в крышку.'),
        ('2', 'Холоднее на 8–12 °C под нагрузкой',
         'Процессор реже уходит в троттлинг, вентилятор ноутбука перестаёт работать на максимуме.'),
        ('3', 'Тише, чем холодильник',
         'Два вентилятора 120 мм на гидродинамическом подшипнике, ≤ 22 дБ на средней скорости.'),
    ]
    for num, head, body in points:
        c.setFillColor(ACC)
        c.setFont('M-800', 15)
        c.drawString(x, y, num)
        c.setFillColor(INK)
        c.setFont('M-700', 11.5)
        c.drawString(x + 9 * mm, y, head)
        text_block(c, x + 9 * mm, y - 6.5 * mm, body, size=9.8, color=MUTED, maxw=PW * 0.5 - 9 * mm)
        y -= 27 * mm
    footer(c, page, right_x=PW * 0.5 - 2 * mm)
    c.showPage()
    page += 1

    # ================= 3. МОДЕЛЬ 4.1 =================
    c.setFillColor(SAND)
    c.rect(0, 0, PW, PH, fill=1, stroke=0)
    img_w = PW * 0.53 - M
    cover_image(c, os.path.join(IMG, 'nb-hero.jpg'), M, M, img_w, PH - 2 * M)

    tx = PW * 0.53 + 6 * mm
    tw_ = PW - tx - M
    y = page_head(c, tx, PH - M, 'флагман · позиция 4.1', width=38 * mm)
    y = big_title(c, tx, y - 1 * mm, 'Приставной столик', size=26, maxw=tw_)
    y -= 1 * mm
    y = text_block(c, tx, y, 'Встаёт к дивану или креслу: столешница заходит над коленями, '
                            'стойка уходит за сиденье.', size=11, color=MUTED, maxw=tw_)
    y -= 7 * mm
    c.setStrokeColor(LINE)
    c.setLineWidth(0.7)
    c.line(tx, y + 3 * mm, PW - M, y + 3 * mm)
    y -= 2 * mm
    y = spec_rows(c, tx, y, [
        ('Габариты', '700 × 450 мм'),
        ('Высота', '620–760 мм, регулировка'),
        ('Столешница', 'дуб 30 мм, щели 4 × 60 мм'),
        ('Каркас', 'сталь 40×40, порошковая покраска'),
        ('Вентиляторы', '2 × 120 мм, 600–1200 об/мин, ≤ 22 дБ'),
        ('Питание', 'USB-C PD, 5–12 В, до 3 Вт'),
        ('Наклон', '0–12°'),
        ('Вес', '12 кг, разбирается на 4 болтах'),
    ], maxw=tw_)
    c.setFillColor(ACC)
    c.setFont('M-700', 13)
    c.drawString(tx, y - 2 * mm, '45 000–70 000 ₽')
    c.setFillColor(MUTED)
    c.setFont('M-400', 8.5)
    c.drawString(tx, y - 8 * mm, 'срок 20–30 дней · ориентир, подтверждается после замера')
    footer(c, page)
    c.showPage()
    page += 1

    # ================= 4. КАК РАБОТАЕТ ОБДУВ =================
    c.setFillColor(DARK)
    c.rect(0, 0, PW, PH, fill=1, stroke=0)
    cover_image(c, os.path.join(IMG, 'nb-obduv.jpg'), PW * 0.42, 0, PW * 0.58, PH)

    x = M
    y = page_head(c, x, PH - M, 'конструкция обдува', white=True, width=38 * mm)
    y = big_title(c, x, y - 1 * mm, 'Свет и воздух идут сквозь дерево',
                  size=24, color=WHITE, maxw=PW * 0.38)
    y -= 4 * mm
    y = text_block(c, x, y, 'Щели фрезерованы в столешнице — это не декор, а канал. '
                            'Изнутри стоит рампа с вентиляторами, поток выходит ровно '
                            'в решётки днища ноутбука.',
                   size=10.5, color=(0.82, 0.79, 0.75), maxw=PW * 0.37)
    y -= 8 * mm
    for head, body in [
        ('Зоны обдува', 'две площадки 120 × 120 мм, смещены к задней трети'),
        ('Щели', '4 × 60 мм, шаг 12 мм — чистятся щёткой'),
        ('Демпферы', 'силикон: столешница не вибрирует'),
        ('Провод', 'в пазу под столешницей, дальше — в ноге'),
    ]:
        c.setFillColor(WHITE)
        c.setFont('M-700', 10.5)
        c.drawString(x, y, head)
        c.setFillColor((0.78, 0.75, 0.71))
        yy = y
        for line in wrap(body, 9.2, 'M-400', PW * 0.36 - 34 * mm):
            c.setFont('M-400', 9.2)
            c.drawString(x + 34 * mm, yy, line)
            yy -= 4.6 * mm
        y = min(yy, y - 8.5 * mm) - 1.5 * mm
    footer(c, page, right_x=PW * 0.38, dark=True)
    c.showPage()
    page += 1

    # ================= 5. МОДЕЛЬ 4.2 =================
    c.setFillColor(SAND)
    c.rect(0, 0, PW, PH, fill=1, stroke=0)
    cover_image(c, os.path.join(IMG, 'nb-nakolennyj.jpg'), M, M, img_w, PH - 2 * M)
    y = page_head(c, tx, PH - M, 'позиция 4.2', width=38 * mm)
    y = big_title(c, tx, y - 1 * mm, 'Наколенный столик', size=26, maxw=tw_)
    y -= 1 * mm
    y = text_block(c, tx, y, 'Диван, кровать, кресло. Складывается за десять секунд '
                            'и уезжает за спинку.', size=11, color=MUTED, maxw=tw_)
    y -= 7 * mm
    c.setStrokeColor(LINE)
    c.line(tx, y + 3 * mm, PW - M, y + 3 * mm)
    y -= 2 * mm
    y = spec_rows(c, tx, y, [
        ('Габариты', '650 × 420 мм'),
        ('Столешница', 'дуб 22 мм, щели обдува'),
        ('Каркас', 'сталь, порошковая покраска'),
        ('Наклон', '0–15°, фиксация барашками'),
        ('Вентиляторы', '2 × 80 мм, питание USB-C'),
        ('Вес', '6 кг'),
    ], maxw=tw_)
    c.setFillColor(ACC)
    c.setFont('M-700', 13)
    c.drawString(tx, y - 2 * mm, '18 000–30 000 ₽')
    c.setFillColor(MUTED)
    c.setFont('M-400', 8.5)
    c.drawString(tx, y - 8 * mm, 'срок 15–20 дней · складывается, убирается в шкаф')
    footer(c, page)
    c.showPage()
    page += 1

    # ================= 6. МОДЕЛЬ 4.3 =================
    c.setFillColor(SAND)
    c.rect(0, 0, PW, PH, fill=1, stroke=0)
    cover_image(c, os.path.join(IMG, 'nb-rabochij.jpg'), M, M, img_w, PH - 2 * M)
    y = page_head(c, tx, PH - M, 'позиция 4.3', width=38 * mm)
    y = big_title(c, tx, y - 1 * mm, 'Рабочий стол', size=26, maxw=tw_)
    y -= 1 * mm
    y = text_block(c, tx, y, 'Кабинетный стол, в котором спрятано всё, что обычно '
                            'лежит проводами.', size=11, color=MUTED, maxw=tw_)
    y -= 7 * mm
    c.setStrokeColor(LINE)
    c.line(tx, y + 3 * mm, PW - M, y + 3 * mm)
    y -= 2 * mm
    y = spec_rows(c, tx, y, [
        ('Габариты', '1200 × 600 × 750 мм'),
        ('Столешница', 'дуб 40 мм'),
        ('Каркас', 'сталь 40×40, разборный'),
        ('Вентиляторы', '4 × 120 мм в задней трети'),
        ('Электрика', 'Qi-зарядка, USB-хаб, кабель-канал'),
        ('Вес', '38 кг'),
    ], maxw=tw_)
    c.setFillColor(ACC)
    c.setFont('M-700', 13)
    c.drawString(tx, y - 2 * mm, '85 000–130 000 ₽')
    c.setFillColor(MUTED)
    c.setFont('M-400', 8.5)
    c.drawString(tx, y - 8 * mm, 'срок 25–35 дней · кабель-канал с крышкой из того же дуба')
    footer(c, page)
    c.showPage()
    page += 1

    # ================= 7. ОПЦИИ С ФОТО =================
    c.setFillColor(SAND)
    c.rect(0, 0, PW, PH, fill=1, stroke=0)
    y = page_head(c, M, PH - M, 'опции', width=38 * mm)
    y = big_title(c, M, y - 1 * mm, 'Что добавляют к базе', size=24)
    c.setFillColor(MUTED)
    c.setFont('M-400', 10)
    c.drawString(M, y + 1 * mm,
                 'Опции дают 20–30 % к чеку почти без роста трудозатрат — их стоит предлагать всегда.')

    opts = [
        ('nb-opt-qi.jpg', 'Беспроводная зарядка Qi', 'врезана заподлицо в столешницу', '+6 000–9 000 ₽'),
        ('nb-opt-led.jpg', 'LED-линия под столешницей', 'вечерний свет, читается как «дорого»', '+4 000–7 000 ₽'),
        ('nb-opt-kryuchok.jpg', 'Крючок для наушников', 'латунь, под столешницей, не виден сверху',
         '+1 500 ₽'),
    ]
    cw = (PW - 2 * M - 2 * 8 * mm) / 3
    ch = 55 * mm
    top = y - 6 * mm
    for i, (fn, name, desc, price) in enumerate(opts):
        x = M + i * (cw + 8 * mm)
        cover_image(c, os.path.join(IMG, fn), x, top - ch, cw, ch)
        c.setFillColor(INK)
        c.setFont('M-700', 12)
        c.drawString(x, top - ch - 8 * mm, name)
        text_block(c, x, top - ch - 14 * mm, desc, size=9.5, color=MUTED, maxw=cw)
        c.setFillColor(ACC)
        c.setFont('M-700', 12)
        c.drawString(x, top - ch - 24 * mm, price)

    y = top - ch - 38 * mm
    c.setStrokeColor(LINE)
    c.line(M, y, PW - M, y)
    c.setFillColor(MUTED)
    c.setFont('M-400', 9.5)
    c.drawString(M, y - 10 * mm,
                 'Все опции ставятся на любую из трёх моделей. Зарядка и подсветка питаются от того же '
                 'USB-C, что и вентиляторы — отдельной розетки не нужно.')
    footer(c, page)
    c.showPage()
    page += 1

    # ================= 8. ТАБЛИЦА ОПЦИЙ =================
    c.setFillColor(SAND)
    c.rect(0, 0, PW, PH, fill=1, stroke=0)
    page_head(c, M, PH - M, 'полный список', width=38 * mm)
    big_title(c, M, PH - M - 38 * mm, 'Шесть опций и наценки', size=24)

    rows = [
        ('Опция', 'Что даёт', 'Наценка', 'Кому'),
        ('Зарядка Qi', 'телефон кладётся на стол и заряжается', '+6 000–9 000 ₽', 'всем, у кого телефон на столе'),
        ('Подставка под телефон', 'паз под наклон, телефон стоит вертикально', '+2 500 ₽', 'дёшево и часто берут'),
        ('Крючок для наушников', 'латунный, под столешницей', '+1 500 ₽', 'приятная мелочь'),
        ('LED-линия', 'свет под столешницей, вечером', '+4 000–7 000 ₽', 'гостиная, спальня'),
        ('Камень в зоне обдува', 'оникс или травертин вместо дерева', '+18 000 ₽', 'топовая версия'),
        ('Чехол из плотной ткани', 'хранение и перевозка', '+3 500 ₽', 'складной модели 4.2'),
    ]
    y = PH - M - 52 * mm
    colx = [M, M + 58 * mm, M + 132 * mm, M + 186 * mm]
    c.setFillColor(SOFT)
    c.rect(M, y, PW - 2 * M, 10 * mm, fill=1, stroke=0)
    c.setFillColor(MUTED)
    c.setFont('M-700', 9)
    for i, h in enumerate(rows[0]):
        c.drawString(colx[i], y + 3.5 * mm, h)
    y -= 10 * mm
    for ri, row in enumerate(rows[1:]):
        if ri % 2 == 0:
            c.setFillColor(WHITE)
            c.rect(M, y, PW - 2 * M, 13 * mm, fill=1, stroke=0)
        c.setFillColor(INK)
        c.setFont('M-600', 10)
        c.drawString(colx[0], y + 4.5 * mm, row[0])
        c.setFillColor(MUTED)
        c.setFont('M-400', 9.5)
        c.drawString(colx[1], y + 4.5 * mm, row[1])
        c.setFillColor(ACC)
        c.setFont('M-700', 10)
        c.drawString(colx[2], y + 4.5 * mm, row[2])
        c.setFillColor(MUTED)
        c.setFont('M-400', 9.2)
        c.drawString(colx[3], y + 4.5 * mm, row[3])
        c.setStrokeColor(LINE)
        c.setLineWidth(0.5)
        c.line(M, y, PW - M, y)
        y -= 13 * mm

    text_block(c, M, y - 6 * mm,
               'Наценки — ориентиры, их нужно подтвердить у мастера. Правило продажи: '
               'базовая позиция продаётся по цене, опции добавляют 20–30 % к чеку.',
               size=9.5, color=MUTED)
    footer(c, page)
    c.showPage()
    page += 1

    # ================= 9. СРАВНЕНИЕ =================
    c.setFillColor(SAND)
    c.rect(0, 0, PW, PH, fill=1, stroke=0)
    page_head(c, M, PH - M, 'сравнение', width=38 * mm)
    big_title(c, M, PH - M - 38 * mm, 'Три модели рядом', size=24)

    cols = [
        ('4.1  Приставной', 'nb-hero.jpg', ['700 × 450 мм', '620–760 мм', '2 × 120 мм', '0–12°',
                                            '12 кг', '45 000–70 000 ₽'], 'диван и кресло'),
        ('4.2  Наколенный', 'nb-nakolennyj.jpg', ['650 × 420 мм', 'на коленях', '2 × 80 мм', '0–15°',
                                                  '6 кг', '18 000–30 000 ₽'], 'диван, кровать, дорога'),
        ('4.3  Рабочий стол', 'nb-rabochij.jpg', ['1200 × 600 × 750 мм', '750 мм', '4 × 120 мм', '—',
                                                  '38 кг', '85 000–130 000 ₽'], 'кабинет, постоянное место'),
    ]
    cw = (PW - 2 * M - 2 * 7 * mm) / 3
    top = PH - M - 48 * mm
    chh = 46 * mm
    rows_lbl = ['Габариты', 'Высота', 'Вентиляторы', 'Наклон', 'Вес', 'Цена']
    for i, (title, fn, vals, where) in enumerate(cols):
        x = M + i * (cw + 7 * mm)
        cover_image(c, os.path.join(IMG, fn), x, top - chh, cw, chh)
        c.setFillColor(INK)
        c.setFont('M-700', 12.5)
        c.drawString(x, top - chh - 8 * mm, title)
        c.setFillColor(ACC)
        c.setFont('M-400', 9.5)
        c.drawString(x, top - chh - 13.5 * mm, where)
        yy = top - chh - 22 * mm
        for lbl, val in zip(rows_lbl, vals):
            c.setFillColor(MUTED)
            c.setFont('M-400', 8.5)
            c.drawString(x, yy, lbl)
            c.setFillColor(INK if lbl != 'Цена' else ACC)
            c.setFont('M-700' if lbl == 'Цена' else 'M-600', 10)
            c.drawString(x + 27 * mm, yy, val)
            yy -= 7.5 * mm
    footer(c, page)
    c.showPage()
    page += 1

    # ================= 10. КОНТАКТЫ =================
    c.setFillColor(DARK)
    c.rect(0, 0, PW, PH, fill=1, stroke=0)

    # фото слева с мягким затемнением
    cover_image(c, os.path.join(IMG, 'nb-hero.jpg'), 0, 0, PW * 0.36, PH)
    c.setFillColorRGB(0.09, 0.08, 0.07, alpha=0.62)
    c.rect(0, 0, PW * 0.36, PH, fill=1, stroke=0)
    c.setFillAlpha(1)
    c.setStrokeAlpha(1)

    # мягкая растяжка на стыке фото и фона
    for i in range(24):
        a = 0.62 * (1 - i / 23.0)
        c.setFillColorRGB(0.09, 0.08, 0.07, alpha=a)
        c.rect(PW * 0.36 + i * 1.1 * mm, 0, 1.4 * mm, PH, fill=1, stroke=0)
    c.setFillAlpha(1)

    x = PW * 0.36 + 12 * mm
    right = PW - M

    # логотип
    yb = logo(c, x, PH - M - 2 * mm, width=54 * mm, white=True)

    c.setFillColorRGB(0.36, 0.78, 0.74)
    c.setFont('M-700', 9.5)
    c.drawString(x, yb - 8 * mm, 'СВЯЗАТЬСЯ')

    c.setFillColor(WHITE)
    c.setFont('M-800', 31)
    c.drawString(x, yb - 21 * mm, 'Обсудим ваш столик')
    c.setFillColor((0.80, 0.77, 0.73))
    c.setFont('M-400', 11)
    c.drawString(x, yb - 28.5 * mm, 'Ответим цифрами: стоимость, срок и что технологически возможно.')
    c.drawString(x, yb - 34 * mm, 'Расчёт — в течение рабочего дня, без брифа на десять страниц.')

    # ---- плашки контактов 2 × 2 ----
    cards = [
        ('WHATSAPP', '+7 (926) 160-91-10', 'написать в один тап'),
        ('ТЕЛЕФОН', '+7 (926) 160-91-10', 'ПН–ПТ, 10:00–18:00'),
        ('ПОЧТА', 'bak.masters@yandex.ru', 'чертежи, референсы, ТЗ'),
        ('САЙТ', 'bakmasters.su', 'каталог и другие линейки'),
    ]
    gw = right - x
    qr_w = 36 * mm
    card_area_w = gw - qr_w - 8 * mm
    cwid = (card_area_w - 5 * mm) / 2
    chei = 25 * mm
    ctop = yb - 45 * mm
    for i, (label, value, hint) in enumerate(cards):
        cx = x + (i % 2) * (cwid + 5 * mm)
        cy = ctop - (i // 2) * (chei + 5 * mm) - chei
        c.setFillColorRGB(0.155, 0.140, 0.128)
        c.setStrokeColorRGB(0.30, 0.28, 0.25)
        c.setLineWidth(0.6)
        c.roundRect(cx, cy, cwid, chei, 3 * mm, fill=1, stroke=1)
        c.setFillColorRGB(0.36, 0.78, 0.74)
        c.setFont('M-700', 7.2)
        c.drawString(cx + 5 * mm, cy + chei - 7 * mm, label)
        c.setFillColor(WHITE)
        c.setFont('M-700', 12.5)
        c.drawString(cx + 5 * mm, cy + 9.5 * mm, value)
        c.setFillColor((0.62, 0.59, 0.55))
        c.setFont('M-400', 7.8)
        c.drawString(cx + 5 * mm, cy + 4.5 * mm, hint)

    # ---- QR на WhatsApp ----
    try:
        import qrcode
        qr = qrcode.QRCode(box_size=10, border=0)
        qr.add_data('https://wa.me/79261609110')
        qr.make(fit=True)
        qimg = qr.make_image(fill_color='#23201D', back_color='white').convert('RGB')
        qpath = '/tmp/_qr_wa.png'
        qimg.save(qpath)
        qx = right - qr_w
        qy = ctop - 2 * qr_w - 5 * mm
        c.setFillColor(WHITE)
        c.roundRect(qx - 2.5 * mm, qy - 2.5 * mm, qr_w + 5 * mm, qr_w + 5 * mm, 2.5 * mm,
                    fill=1, stroke=0)
        c.drawImage(qpath, qx, qy, qr_w, qr_w)
        c.setFillColor((0.62, 0.59, 0.55))
        c.setFont('M-400', 7.4)
        c.drawCentredString(qx + qr_w / 2, qy - 8 * mm, 'Наведите камеру —')
        c.drawCentredString(qx + qr_w / 2, qy - 12 * mm, 'откроется WhatsApp')
    except Exception as e:
        print('QR пропущен:', e)

    # ---- нижняя строка реквизитов ----
    c.setStrokeColorRGB(0.26, 0.24, 0.22)
    c.setLineWidth(0.6)
    c.line(x, 26 * mm, right, 26 * mm)
    c.setFillColor((0.60, 0.57, 0.53))
    c.setFont('M-400', 8.2)
    c.drawString(x, 20 * mm, 'ИП Бабаева Кристина Горхмазовна  ·  ИНН 572501343152  ·  ОГРНИП 322574900004165')
    c.drawString(x, 15.5 * mm, 'Москва  ·  доставка по России  ·  BAK HOME — комбинированная мебель для дома')

    footer(c, page, right_x=right, dark=True)
    c.showPage()

    c.save()
    print('готово:', OUT, os.path.getsize(OUT), 'Б')


if __name__ == '__main__':
    main()
