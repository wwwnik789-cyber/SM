#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Презентация линейки комбинированной мебели для дизайнеров — A4 альбомная."""
import os

from PIL import Image as PILImage
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, '..', '..', 'docs', 'ca-avtosalony', '02_prezentaciya', 'fonts')
OUT = os.path.join(HERE, 'SM-BAKMASTERS-Mebel-prezentaciya.pdf')

SAND = (0xF6 / 255, 0xF1 / 255, 0xE9 / 255)
CARD = (1, 1, 1)
INK = (0x2B / 255, 0x26 / 255, 0x21 / 255)
MUTED = (0x7A / 255, 0x6F / 255, 0x63 / 255)
ACC = (0x2F / 255, 0x6F / 255, 0x6B / 255)
LINE = (0xE4 / 255, 0xDB / 255, 0xCD / 255)
DARK = (0x23 / 255, 0x20 / 255, 0x1D / 255)

pdfmetrics.registerFont(TTFont('M-400', os.path.join(FONTS, 'Manrope-400.ttf')))
pdfmetrics.registerFont(TTFont('M-600', os.path.join(FONTS, 'Manrope-600.ttf')))
pdfmetrics.registerFont(TTFont('M-700', os.path.join(FONTS, 'Manrope-700.ttf')))
pdfmetrics.registerFont(TTFont('M-800', os.path.join(FONTS, 'Manrope-800.ttf')))

# (фото, код, название, короткая строка, [характеристики], цена)
ITEMS = [
    ('foto-01-obedennyj.jpg', '1.1', 'Обеденный стол «Река»',
     'Дуб 40 мм и смола-река на чёрном металлокаркасе. Размер под комнату.',
     [('Габариты', '1600 × 900 × 750 мм'), ('Материалы', 'дуб 40 мм, эпоксидная смола, сталь 40×40'),
      ('Покрытие', 'масло-воск, порошковая покраска'), ('Вес', '58 кг'), ('Разборный', 'да, 2 коробки')],
     '95 000–150 000 ₽'),
    ('foto-07-konsol.jpg', '1.2', 'Консоль в прихожую',
     'Глубина 350 мм: проходит там, где обычная консоль уже мешает.',
     [('Габариты', '1100 × 350 × 820 мм'), ('Материалы', 'дуб 40 мм, сталь 20×20'),
      ('Полка', 'дуб 30 мм'), ('Вес', '26 кг')],
     '45 000–70 000 ₽'),
    ('foto-02-kamen.jpg', '1.3', 'Барный стол с камнем',
     'Дуб и травертин 20 мм на высоте 1050 — под барные стулья.',
     [('Габариты', '1200 × 600 × 1050 мм'), ('Материалы', 'дуб 40 мм, травертин 20 мм на подложке'),
      ('Каркас', 'сталь 40×40, пятки ±8 мм'), ('Вес', '42 кг')],
     '70 000–110 000 ₽'),
    ('foto-03-zhurnalnyj.jpg', '2.1', 'Журнальный круглый',
     'Круг Ø 700 на обруче из полосы — тонкая линия вместо массивных ножек.',
     [('Габариты', 'Ø 700 × 450 мм'), ('Материалы', 'дуб 30–40 мм, полоса 40×8'),
      ('Опция', 'Ø 800 по запросу'), ('Вес', '22 кг')],
     '38 000–60 000 ₽'),
    ('foto-04-pristavnoj.jpg', '2.2', 'Приставной C-столик',
     'Заходит под диван: столешница над коленями, стойка сбоку.',
     [('Габариты', '450 × 350 × 650 мм'), ('Материалы', 'дуб 30 мм, сталь 20×20'),
      ('Вес', '10 кг — переносится одной рукой')],
     '25 000–40 000 ₽'),
    ('foto-10-oniks.jpg', '2.3', 'Приставной с ониксом',
     'Оникс 20 мм просвечивает: с LED снизу камень светится изнутри.',
     [('Габариты', '500 × 400 × 550 мм'), ('Материалы', 'оникс 20 мм, дуб-подложка, сталь 20×20'),
      ('Подсветка', 'опция, LED снизу'), ('Вес', '14 кг')],
     '55 000–90 000 ₽'),
    ('foto-05-prikrovatnaya.jpg', '3.1', 'Прикроватная тумба',
     'Дуб и металлическая рама: всё, что нужно, на виду.',
     [('Габариты', '450 × 400 × 550 мм'), ('Материалы', 'дуб 30 мм, сталь 20×20, сетка'),
      ('Высота', 'под кровать с матрасом 500–550 мм'), ('Вес', '16 кг')],
     '28 000–45 000 ₽'),
    ('foto-06-noutbuk.jpg', '4.1', 'Столик для ноутбука с охлаждением',
     'Два тихих вентилятора дуют в днище ноутбука. Провода не видно.',
     [('Габариты', '700 × 450, высота 620–760 мм'), ('Вентиляторы', '2 × 120 мм, ≤ 22 дБ'),
      ('Питание', 'USB-C PD 5–12 В, до 3 Вт'), ('Наклон', '0–12°'), ('Вес', '12 кг')],
     '45 000–70 000 ₽'),
    ('foto-08-materialy.jpg', '—', 'Материалы линейки',
     'Дуб, смола, травертин, оникс, сталь с порошковой покраской, латунь.',
     [('Дерево', 'дуб, ясень, каповый тополь, абрикос'), ('Смола', 'прозрачная, молочная, чёрная, бирюза, охра, сизая'),
      ('Камень', 'оникс, травертин, мрамор, кварцит 20 мм'), ('Металл', '20×20, 40×40, полоса 40×8')],
     'палитра на выбор'),
    ('foto-09-uzel.jpg', '—', 'Узлы, которые решают качество',
     'То, чего не видно на фото каталога, но чувствуется через год.',
     [('Крепление', 'овальные отверстия: дерево ходит, болт не рвёт'), ('Прокладка', 'EVA 2 мм — металл не звенит'),
      ('Регулировка', 'пятки ±8 мм на неровный пол'), ('Разборность', '4–6 болтов, плоская упаковка'),
      ('Скругления', 'радиус 6–8 мм по металлу'), ('Камень', 'подложка 12 мм, эпоксидный клей')],
     ''),
]

OTHER = [
    ('3.2', 'Тумба с ящиком', '450 × 400 × 500', '38 000–58 000 ₽'),
    ('3.3', 'Узкая тумба', '350 × 350 × 600', '24 000–38 000 ₽'),
    ('4.2', 'Столик наколенный', '650 × 420, наклон 0–15°', '18 000–30 000 ₽'),
    ('4.3', 'Стол рабочий с вентиляцией', '1200 × 600 × 750', '85 000–130 000 ₽'),
]


def wrap(text, font, size, maxw):
    words = text.split()
    lines, cur = [], ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if pdfmetrics.stringWidth(t, font, size) <= maxw:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def main():
    c = canvas.Canvas(OUT, pagesize=landscape(A4))
    pw, ph = landscape(A4)
    m = 16 * mm

    # ---------------- обложка ----------------
    cover = os.path.join(HERE, 'img', 'foto-01-obedennyj.jpg')
    im = PILImage.open(cover).convert('RGB')
    tw, th = pw, ph
    ratio = max(tw / im.width, th / im.height)
    im = im.resize((int(im.width * ratio) + 1, int(im.height * ratio) + 1), PILImage.LANCZOS)
    left = (im.width - tw) // 2
    top = (im.height - ph) // 2
    im = im.crop((left, top, left + tw, top + ph))
    c.drawImage(ImageReader(im), 0, 0, tw, ph)

    # скрим
    c.setFillColorRGB(0.07, 0.06, 0.05, alpha=0.55)
    c.rect(0, 0, pw, ph, fill=1, stroke=0)
    c.setFillAlpha(1)
    c.setStrokeAlpha(1)

    c.setFillColorRGB(1, 1, 1)
    c.setFont('M-600', 10)
    c.drawString(m, ph - 24 * mm, 'BAK MASTERS  ·  BAK HOME')

    c.setFont('M-800', 40)
    c.drawString(m, ph - 46 * mm, 'Комбинированная мебель')
    c.drawString(m, ph - 60 * mm, 'для дома')
    c.setFont('M-400', 14)
    c.setFillColorRGB(0.93, 0.91, 0.88)
    c.drawString(m, ph - 74 * mm, 'Дуб · смола · природный камень · металлокаркас с порошковой покраской')
    c.setFont('M-600', 11)
    c.drawString(m, ph - 88 * mm, '12 позиций · 4 группы · для дизайнеров интерьера и частных клиентов')
    c.setFont('M-400', 9.5)
    c.setFillColorRGB(0.82, 0.79, 0.75)
    c.drawString(m, 20 * mm, 'Москва · доставка по России · октябрь 2026')
    c.showPage()

    # ---------------- страницы позиций ----------------
    for idx, (photo, code, name, lead, specs, price) in enumerate(ITEMS):
        c.setFillColor(SAND)
        c.rect(0, 0, pw, ph, fill=1, stroke=0)

        path = os.path.join(HERE, 'img', photo)
        im = PILImage.open(path).convert('RGB')
        box_w = pw * 0.52 - m
        box_h = ph - 2 * m
        ratio = max(box_w / im.width, box_h / im.height)
        im = im.resize((int(im.width * ratio) + 1, int(im.height * ratio) + 1), PILImage.LANCZOS)
        l = (im.width - box_w) / 2
        t = (im.height - box_h) / 2
        im = im.crop((int(l), int(t), int(l + box_w), int(t + box_h)))
        c.drawImage(ImageReader(im), m, m, box_w, box_h)

        tx = pw * 0.52 + 6 * mm
        tw_ = pw - tx - m
        y = ph - m - 26 * mm

        if code != '—':
            c.setFillColor(ACC)
            c.setFont('M-700', 9)
            c.drawString(tx, y + 16 * mm, 'ПОЗИЦИЯ ' + code)
        c.setFillColor(INK)
        c.setFont('M-800', 25)
        for line in wrap(name, 'M-800', 25, tw_)[:3]:
            c.drawString(tx, y, line)
            y -= 11 * mm
        y -= 2 * mm

        c.setFillColor(MUTED)
        c.setFont('M-400', 11.5)
        for line in wrap(lead, 'M-400', 11.5, tw_):
            c.drawString(tx, y, line)
            y -= 6.5 * mm
        y -= 6 * mm

        c.setStrokeColor(LINE)
        c.setLineWidth(0.7)
        c.line(tx, y + 3 * mm, pw - m, y + 3 * mm)
        y -= 3 * mm

        for k, v in specs:
            c.setFillColor(MUTED)
            c.setFont('M-600', 9)
            c.drawString(tx, y, k)
            c.setFillColor(INK)
            c.setFont('M-400', 10.5)
            for i, line in enumerate(wrap(v, 'M-400', 10.5, tw_ - 44 * mm)):
                c.drawString(tx + 44 * mm, y, line)
                if i < len(wrap(v, 'M-400', 10.5, tw_ - 44 * mm)) - 1:
                    y -= 5 * mm
            y -= 8.2 * mm

        if price:
            y -= 4 * mm
            c.setFillColor(ACC)
            c.setFont('M-700', 13)
            c.drawString(tx, y, price)
            c.setFillColor(MUTED)
            c.setFont('M-400', 8.5)
            c.drawString(tx, y - 6 * mm, 'ориентир, подтверждается после замера')

        c.setFillColor(MUTED)
        c.setFont('M-400', 8)
        c.drawString(m, 8 * mm, 'BAK MASTERS · BAK HOME · комбинированная мебель для дома')
        c.drawRightString(pw - m, 8 * mm, 'стр. %d из %d' % (idx + 2, len(ITEMS) + 3))
        c.showPage()

    # ---------------- таблица остальных позиций ----------------
    c.setFillColor(SAND)
    c.rect(0, 0, pw, ph, fill=1, stroke=0)
    c.setFillColor(ACC)
    c.setFont('M-700', 9)
    c.drawString(m, ph - m - 8 * mm, 'ПОЛНЫЙ СПИСОК')
    c.setFillColor(INK)
    c.setFont('M-800', 24)
    c.drawString(m, ph - m - 20 * mm, 'Ещё четыре позиции линейки')
    c.setFillColor(MUTED)
    c.setFont('M-400', 11)
    c.drawString(m, ph - m - 28 * mm, 'Показаны на предыдущих страницах не все — вот остальное, чтобы линейка читалась целиком.')

    rows = [('Группа', 'Позиция', 'Габариты', 'Цена, ориентир')]
    rows += [('3. Прикроватные', o[1], o[2], o[3]) for o in OTHER if o[0].startswith('3')]
    rows += [('4. Для работы', o[1], o[2], o[3]) for o in OTHER if o[0].startswith('4')]

    y = ph - m - 42 * mm
    colx = [m, m + 60 * mm, m + 140 * mm, m + 200 * mm]
    c.setFillColorRGB(0xEE / 255, 0xE7 / 255, 0xDB / 255)
    c.rect(m, y, pw - 2 * m, 10 * mm, fill=1, stroke=0)
    c.setFillColor(MUTED)
    c.setFont('M-700', 9)
    for i, h in enumerate(rows[0]):
        c.drawString(colx[i], y + 3.5 * mm, h)
    y -= 10 * mm
    for ri, row in enumerate(rows[1:]):
        if ri % 2 == 0:
            c.setFillColorRGB(1, 1, 1)
            c.rect(m, y, pw - 2 * m, 11 * mm, fill=1, stroke=0)
        for ci, val in enumerate(row):
            c.setFillColor(MUTED if ci == 0 else INK)
            c.setFont('M-400' if ci != 3 else 'M-600', 10)
            c.drawString(colx[ci], y + 4 * mm, val)
        c.setStrokeColor(LINE)
        c.setLineWidth(0.5)
        c.line(m, y, pw - m, y)
        y -= 11 * mm

    c.setFillColor(MUTED)
    c.setFont('M-400', 9)
    note = ('Цены — ориентиры по Москве на октябрь 2026, подтверждаются после замера и выбора материала. '
            'Срок изготовления 20–35 дней, камень добавляет 5–7 дней.')
    for line in wrap(note, 'M-400', 9, pw - 2 * m):
        c.drawString(m, y - 2 * mm, line)
        y -= 5 * mm
    c.drawString(m, 8 * mm, 'BAK MASTERS · BAK HOME · комбинированная мебель для дома')
    c.drawRightString(pw - m, 8 * mm, 'стр. %d из %d' % (len(ITEMS) + 2, len(ITEMS) + 3))
    c.showPage()

    # ---------------- финальная страница ----------------
    c.setFillColor(DARK)
    c.rect(0, 0, pw, ph, fill=1, stroke=0)
    c.setFillColorRGB(1, 1, 1)
    c.setFont('M-800', 30)
    c.drawString(m, ph - m - 30 * mm, 'Что нужно, чтобы посчитать')
    c.setFillColorRGB(0.85, 0.82, 0.79)
    c.setFont('M-400', 12.5)
    left_col = [
        '1. План или эскиз с размерами, можно от руки.',
        '2. Материал: дуб, ясень или слэб; камень — если нужен.',
        '3. Оттенок смолы и цвет металла по палитре.',
        '4. Срок сдачи объекта и бюджет, в который нужно попасть.',
        '5. Фото интерьера или референс — чтобы попасть в контекст.',
    ]
    y = ph - m - 44 * mm
    for line in left_col:
        for i, l in enumerate(wrap(line, 'M-400', 12.5, 120 * mm)):
            c.drawString(m, y, l)
            y -= 7 * mm
        y -= 2 * mm

    c.setFillColor(ACC)
    c.setFont('M-700', 12)
    c.drawString(pw * 0.58, ph - m - 44 * mm, 'Расчёт — в течение рабочего дня')  # влезает в одну строку
    c.setFillColorRGB(0.85, 0.82, 0.79)
    c.setFont('M-400', 11.5)
    rx = pw * 0.58
    rw = pw - rx - m
    lines = ['Присылайте чертёж в WhatsApp или на почту.',
             'Ответим цифрами: стоимость, срок, что технологически возможно.']
    yy = ph - m - 54 * mm
    for l in lines:
        for part in wrap(l, 'M-400', 11.5, rw):
            c.drawString(rx, yy, part)
            yy -= 7 * mm

    c.setFillColorRGB(1, 1, 1)
    c.setFont('M-700', 15)
    c.drawString(pw * 0.58, ph - m - 92 * mm, '+7 (926) 160-91-10')
    c.setFont('M-400', 12)
    c.setFillColorRGB(0.85, 0.82, 0.79)
    c.drawString(pw * 0.58, ph - m - 100 * mm, 'bak.masters@yandex.ru  ·  bakmasters.su')

    c.setFillColorRGB(0.55, 0.52, 0.48)
    c.setFont('M-400', 8.5)
    c.drawString(m, 16 * mm, 'ИП Бабаева Кристина Горхмазовна · ИНН 572501343152 · ОГРНИП 322574900004165')
    c.showPage()

    c.save()
    print('готово:', OUT, os.path.getsize(OUT), 'Б')


if __name__ == '__main__':
    main()
