#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Дополнительные визуализации по автосалонам: обзорный лист + README."""
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, '..', '02_prezentaciya', 'fonts')

ACC = (255, 77, 28)
BG = (18, 18, 20)

CARDS = [
    ('08-01-vydacha.jpg', 'Зона выдачи',
     'Подиум, световой портал с оранжевой линией, вручение ключей'),
    ('08-02-fasad.jpg', 'Фасад',
     'Пустая графитовая полоса под вывеску, световая линия, входная группа'),
    ('08-03-servisnaya-priemnka.jpg', 'Сервисная приёмка',
     'Стойка с оранжевой линией, стекло в цех, пустая световая панель'),
    ('08-04-lounge.jpg', 'Зона ожидания',
     'Рейка из дуба с подсветкой, диваны, кофе-поинт, пустая панель'),
    ('08-05-kabinet-sdelki.jpg', 'Кабинет сделки',
     'Стеклянная переговорная, пустая панель в рамке, оранжевая вставка'),
    ('08-06-test-drajv.jpg', 'Тест-драйв',
     'Навес у входа, пустая полоса над фасадом, пилон маршрута'),
    ('08-07-detskaya-zona.jpg', 'Детская зона',
     'Пустая световая панель, дубовые полки, мягкий свет'),
    ('08-08-parkovka.jpg', 'Парковка и въезд',
     'Три пилона с пустыми панелями, арка въезда, входная группа'),
]


def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size)


def cover(im, w, h):
    im = im.convert('RGB')
    sw, sh = im.size
    k = max(w / sw, h / sh)
    im = im.resize((max(1, int(sw * k)), max(1, int(sh * k))), Image.LANCZOS)
    sw, sh = im.size
    return im.crop(((sw - w) // 2, (sh - h) // 2, (sw - w) // 2 + w, (sh - h) // 2 + h))


def main():
    have = [(f, t, d) for f, t, d in CARDS
            if os.path.exists(os.path.join(HERE, f))]

    cols = 4
    cell_w, cell_h = 620, 348
    pad, gap = 56, 24
    rows = (len(have) + cols - 1) // cols
    head = 150
    w = pad * 2 + cols * cell_w + (cols - 1) * gap
    h = head + rows * (cell_h + 74) + pad

    canvas = Image.new('RGB', (w, h), BG)
    d = ImageDraw.Draw(canvas)

    d.rectangle([pad, pad + 10, pad + 10, pad + 58], fill=ACC)
    d.text((pad + 26, pad + 6), 'Автосалоны · дополнительные визуализации',
           font=font('Manrope-800.ttf', 40), fill=(255, 255, 255))
    d.text((pad + 26, pad + 66),
           'Зоны, которых не было в первой серии: выдача, фасад, сервис, лаунж, '
           'кабинет сделки, тест-драйв, детская, парковка',
           font=font('Manrope-500.ttf', 21), fill=(150, 150, 156))

    for i, (f, title, desc) in enumerate(have):
        col, row = i % cols, i // cols
        x = pad + col * (cell_w + gap)
        y = head + row * (cell_h + 74)
        canvas.paste(cover(Image.open(os.path.join(HERE, f)), cell_w, cell_h), (x, y))
        d.text((x, y + cell_h + 12), title, font=font('Manrope-700.ttf', 25),
               fill=(255, 255, 255))
        # описание в две строки
        words, line, lines = desc.split(), '', []
        for word in words:
            t = (line + ' ' + word).strip()
            if d.textlength(t, font=font('Manrope-400.ttf', 19)) <= cell_w:
                line = t
            else:
                lines.append(line)
                line = word
        lines.append(line)
        for j, ln in enumerate(lines[:2]):
            d.text((x, y + cell_h + 44 + j * 22), ln,
                   font=font('Manrope-400.ttf', 19), fill=(150, 150, 156))

    out = os.path.join(HERE, 'preview.jpg')
    canvas.save(out, 'JPEG', quality=92, optimize=True)
    print('обзор:', out, canvas.size, len(have), 'кадров')


if __name__ == '__main__':
    main()
