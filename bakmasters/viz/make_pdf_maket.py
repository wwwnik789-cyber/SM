#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PDF с макетом страницы: каждый блок на отдельной странице A4 + общий вид."""
import os
import sys

from PIL import Image

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from md2pdf import ACC, INK, LINE, MUTED, SAND  # noqa: E402

MAKET = os.path.join(HERE, 'MAKET-stranicy.jpg')
OUT = os.path.join(HERE, 'PDF-3-maket-stranicy.pdf')
FROM_DOCS = os.path.abspath(os.path.join(HERE, '..', '..', 'docs',
                                         'SM-BAKMASTERS-sotrudnichestvo.zip'))

# карта блоков из maket-blocks.json (пишется make_maket.py)
import json

_NAMES = {
    '2': 'Шесть причин отдать изделие нам',
    '3': 'Что можно включить в проект',
    '4': 'Поверхности и свет',
    '5': 'Материалы и палитра',
    '6': 'Шесть шагов работы над проектом',
    '7': 'Что нужно прислать',
    '8': 'Партнёрские условия',
    '9': 'Три формата работы',
    '10': 'Проекты',
    '11': 'Другим направлениям',
    '12': 'Вопросы и ответы',
    '13': 'Форма заявки',
}
_ELEMS = {
    '2': 'T-cards · сетка 3 × 2',
    '3': 'T-table · 3 колонки',
    '4': 'T-cards ×4 + таблица + 3 фото',
    '5': 'T-two-columns + фото образцов',
    '6': 'T-timeline · вертикальный',
    '7': 'T-two-columns · чек-лист',
    '8': 'T-cards ×3 · главный коммерческий блок',
    '9': 'T-cards ×3',
    '10': 'T-gallery · 6 плиток',
    '11': 'T-cards ×4 · мелкий текст',
    '12': 'T-accordion + FAQPage',
    '13': 'T-form · 9 полей',
}

_map = json.load(open(os.path.join(HERE, 'maket-blocks.json'), encoding='utf-8'))
H_PX = _map['height']

BLOCKS = [(0, _map['blocks'][0]['y0'], 'Обложка', 'T-cover · фото на всю ширину, скрим 40 %')]
def _final_screen_y(top_px):
    """Блок 13 = форма + финальный экран. Ищем первую строку, тёмную от края до края."""
    from PIL import Image as _I
    im = _I.open(MAKET).convert('RGB')
    W, H = im.size
    xs = (6, 14, W - 14, W - 6)
    for y in range(top_px, H):
        if all(sum(im.getpixel((x, y))) < 300 for x in xs):
            return y
    return H


for b in _map['blocks']:
    if b['num'] == '13':
        mid = _final_screen_y(b['y0'])
        BLOCKS.append((b['y0'], mid, _NAMES['13'], _ELEMS['13']))
        BLOCKS.append((mid, b['y1'], 'Финальный экран', 'T-cover · тёмный фон #23201D'))
        break
    BLOCKS.append((b['y0'], b['y1'], _NAMES.get(b['num'], b['name']), _ELEMS.get(b['num'], b['elem'])))


def main():
    im = Image.open(MAKET).convert('RGB')
    W, H = im.size
    print('макет:', W, H)

    c = canvas.Canvas(OUT, pagesize=A4)
    pw, ph = A4
    m = 18 * mm

    # ---------- страница 1: обзор в три колонки (альбомная) ----------
    from reportlab.lib.pagesizes import landscape
    ow, oh = landscape(A4)
    c.setPageSize((ow, oh))
    c.setFillColor(SAND)
    c.rect(0, 0, ow, oh, fill=1, stroke=0)
    c.setFillColor(INK)
    c.setFont('M-800', 19)
    c.drawString(m, oh - 20 * mm, 'Макет страницы «Сотрудничество» — обзор')
    c.setFillColor(MUTED)
    c.setFont('M-400', 9)
    c.drawString(m, oh - 26 * mm,
                 'Слева направо сверху вниз: 13 блоков. Номера соответствуют подробным страницам дальше.')

    cols, gap = 3, 10 * mm
    colw = (ow - 2 * m - gap * (cols - 1)) / cols
    top = oh - 33 * mm
    bottom = 12 * mm
    maxh = top - bottom
    # высота одной колонки в пикселях макета
    col_px = H / cols
    k = min(colw / W, maxh / col_px)
    imgw = int(W * k)
    for ci in range(cols):
        y_from = int(ci * col_px)
        y_to = int(min(H, (ci + 1) * col_px))
        part = im.crop((0, y_from, W, y_to))
        ph_px = part.height
        pw_px = part.width
        dh = int(ph_px * k)
        x = m + ci * (colw + gap) + (colw - imgw) / 2
        tmp = '/tmp/_ov%d.png' % ci
        part.resize((imgw, dh), Image.LANCZOS).save(tmp)
        c.drawImage(tmp, x, top - dh, imgw, dh)
        # рамка колонки
        c.setStrokeColor(LINE)
        c.setLineWidth(0.5)
        c.rect(x, top - dh, imgw, dh, fill=0, stroke=1)
        # номера блоков
        c.setFont('M-700', 7)
        for i, (y0, y1, name, el) in enumerate(BLOCKS):
            if y0 >= y_from and y0 < y_to:
                ny = top - (y0 - y_from) * k
                c.setFillColor(ACC)
                c.drawString(x - 11, ny - 7, str(i + 1))
    c.setFillColor(MUTED)
    c.setFont('M-400', 7.5)
    c.drawString(m, 6 * mm, 'BAK MASTERS · пакет для сборки в Tilda · 27.10.2026')
    c.showPage()
    c.setPageSize(A4)

    # ---------- страницы 2..N: блоки по отдельности ----------
    for i, (y0, y1, name, el) in enumerate(BLOCKS):
        crop = im.crop((0, y0, W, min(y1, H)))
        # шапка
        c.setFillColor(SAND)
        c.rect(0, ph - 30 * mm, pw, 30 * mm, fill=1, stroke=0)
        c.setFillColor(ACC)
        c.setFont('M-700', 9)
        c.drawString(m, ph - 16 * mm, 'БЛОК %d' % (i + 1))
        c.setFillColor(INK)
        c.setFont('M-800', 14)
        c.drawString(m, ph - 23 * mm, name)
        c.setFillColor(MUTED)
        c.setFont('M-400', 8.5)
        c.drawRightString(pw - m, ph - 23 * mm, el)

        aw, ah = pw - 2 * m, ph - 30 * mm - 22 * mm
        kk = aw / crop.width          # по ширине страницы
        cw, ch = int(crop.width * kk), int(crop.height * kk)
        if ch > ah:                    # если не влезает по высоте — уменьшаем
            kk = ah / crop.height
            cw, ch = int(crop.width * kk), int(crop.height * kk)
        p = '/tmp/_blk%d.png' % i
        crop.resize((cw, ch), Image.LANCZOS).save(p)
        c.drawImage(p, m, ph - 30 * mm - 6 * mm - ch, cw, ch)

        c.setFillColor(MUTED)
        c.setFont('M-400', 7.5)
        c.drawString(m, 10 * mm, 'фрагмент макета · px %d–%d из %d' % (y0, y1, H))
        c.drawRightString(pw - m, 10 * mm, 'стр. %d' % (i + 2))
        c.showPage()

    c.save()
    print('готово:', OUT)


if __name__ == '__main__':
    main()
