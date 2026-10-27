#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Собирает PDF «Инженерия столика для ноутбука» из markdown через viz/md2pdf.py."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'viz'))

import md2pdf  # noqa: E402

MD = os.path.join(HERE, '04-STOLIK-noutbuk-inzheneriya.md')
PDF = os.path.join(HERE, 'SM-BAKMASTERS-Stolik-inzheneriya.pdf')

TITLE = 'Столик для ноутбука\nна диване и кровати'
SUBTITLE = 'Инженерия: механизмы, обдув, зарядка телефона, испытания'
META = [
    'Техническая проработка позиций 4.1 и 4.2 линейки BAK HOME',
    'ИП Бабаева К. Г. · BAK MASTERS · bakmasters.su',
    'Расчёты узлов, спецификация, протокол испытаний, план прототипа',
    'Октябрь 2026',
]


def build():
    from reportlab.platypus import HRFlowable, PageBreak, Paragraph
    from reportlab.platypus.tableofcontents import TableOfContents
    from md2pdf import ACC, LINE, S, Doc, cover_flowables, parse

    doc = md2pdf.Doc(PDF, header='BAK MASTERS', title=TITLE)
    avail = doc.width
    story = cover_flowables(TITLE, SUBTITLE, META, avail)
    story.append(PageBreak())
    t = TableOfContents()
    t.levelStyles = [S['toc1'], S['toc2'], S['toc2']]
    t.dotsMinLevel = 0
    story.append(Paragraph('Содержание', S['h1']))
    story.append(HRFlowable(width='100%', thickness=0.6, color=LINE,
                            spaceBefore=2, spaceAfter=10))
    story.append(t)
    story.append(PageBreak())

    txt = open(MD, encoding='utf-8').read()
    import re
    txt = re.sub(r'^#\s+[^\n]*\n', '', txt, count=1)
    story.extend(parse(txt, avail))

    # пустая страница после оглавления не нужна, если далее идёт текст
    doc.multiBuild(story)


def main():
    build()
    print('готово:', PDF, os.path.getsize(PDF), 'Б')


if __name__ == '__main__':
    main()
