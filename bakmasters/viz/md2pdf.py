#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Markdown → PDF для документов BAK MASTERS.

Поддержка: заголовки (#..###), абзацы, **жирный**, `код`, ```блоки```,
таблицы, списки (- и 1.), цитаты (>), горизонтальные линии (---).
Шрифты: Manrope (кириллица) + DejaVu для символа ⚠ и моноширинного кода.
"""
import os
import re
import sys

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, KeepTogether,
                                PageTemplate, Paragraph, Spacer, Table,
                                TableStyle)
from reportlab.platypus.flowables import HRFlowable
from reportlab.platypus.tableofcontents import TableOfContents

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.abspath(os.path.join(
    HERE, '..', '..', 'docs', 'ca-avtosalony', '02_prezentaciya', 'fonts'))
DEJAVU = '/usr/share/fonts/truetype/dejavu/'

INK = colors.HexColor('#2B2621')
MUTED = colors.HexColor('#7A6F63')
ACC = colors.HexColor('#2F6F6B')
SAND = colors.HexColor('#F6F1E9')
LINE = colors.HexColor('#E4DBCD')
DARK = colors.HexColor('#23201D')

# ---------- шрифты ----------
pdfmetrics.registerFont(TTFont('M-400', os.path.join(FONTS, 'Manrope-400.ttf')))
pdfmetrics.registerFont(TTFont('M-500', os.path.join(FONTS, 'Manrope-500.ttf')))
pdfmetrics.registerFont(TTFont('M-600', os.path.join(FONTS, 'Manrope-600.ttf')))
pdfmetrics.registerFont(TTFont('M-700', os.path.join(FONTS, 'Manrope-700.ttf')))
pdfmetrics.registerFont(TTFont('M-800', os.path.join(FONTS, 'Manrope-800.ttf')))
pdfmetrics.registerFont(TTFont('Sym', DEJAVU + 'DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('Mono', DEJAVU + 'DejaVuSansMono.ttf'))
pdfmetrics.registerFontFamily('M-400', normal='M-400', bold='M-700',
                              italic='M-400', boldItalic='M-700')

# ---------- стили ----------
S = {}
S['body'] = ParagraphStyle('body', fontName='M-400', fontSize=10, leading=15.5,
                           textColor=INK, spaceAfter=7, alignment=TA_LEFT)
S['h1'] = ParagraphStyle('h1', fontName='M-800', fontSize=19, leading=24,
                         textColor=INK, spaceBefore=0, spaceAfter=12)
S['block'] = ParagraphStyle('block', fontName='M-800', fontSize=14.5, leading=19,
                            textColor=ACC, spaceBefore=20, spaceAfter=9)
S['h2'] = ParagraphStyle('h2', fontName='M-800', fontSize=15, leading=20,
                         textColor=ACC, spaceBefore=16, spaceAfter=8)
S['h3'] = ParagraphStyle('h3', fontName='M-700', fontSize=12, leading=16,
                         textColor=INK, spaceBefore=12, spaceAfter=6)
S['h4'] = ParagraphStyle('h4', fontName='M-700', fontSize=10.5, leading=14,
                         textColor=INK, spaceBefore=10, spaceAfter=4)
S['bullet'] = ParagraphStyle('bullet', parent=S['body'], leftIndent=16,
                             bulletIndent=2, spaceAfter=4, leading=14.5)
S['quote'] = ParagraphStyle('quote', parent=S['body'], leftIndent=10,
                            textColor=MUTED, fontSize=9.5, leading=14.5)
S['code'] = ParagraphStyle('code', fontName='Mono', fontSize=8.2, leading=11.5,
                           textColor=INK, spaceAfter=0)
S['small'] = ParagraphStyle('small', fontName='M-400', fontSize=8.5, leading=12,
                            textColor=MUTED)
S['cover_t'] = ParagraphStyle('cover_t', fontName='M-800', fontSize=30,
                              leading=36, textColor=INK)
S['cover_s'] = ParagraphStyle('cover_s', fontName='M-400', fontSize=12,
                              leading=18, textColor=MUTED)
S['toc1'] = ParagraphStyle('toc1', fontName='M-700', fontSize=10.5, leading=17,
                           textColor=INK, leftIndent=0)
S['toc2'] = ParagraphStyle('toc2', fontName='M-400', fontSize=9.5, leading=15,
                           textColor=MUTED, leftIndent=14)
S['cell'] = ParagraphStyle('cell', fontName='M-400', fontSize=8.8, leading=12,
                           textColor=INK)
S['cellh'] = ParagraphStyle('cellh', fontName='M-700', fontSize=8.6, leading=12,
                            textColor=MUTED)


def esc(t):
    return t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def inline(text):
    """инлайн-разметка → теги ReportLab"""
    t = esc(text)
    t = t.replace('\x00', '<br/>')          # служебный токен → перенос строки
    t = re.sub(r'`([^`]+)`', r'<font name="Mono" size="8.6">\1</font>', t)
    t = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', t)
    t = t.replace('⚠️', '<font name="Sym">⚠</font>')
    t = t.replace('⚠', '<font name="Sym">⚠</font>')
    return t


def is_table_row(line):
    return line.strip().startswith('|') and line.strip().endswith('|')


def split_row(line):
    cells = line.strip().strip('|').split('|')
    return [c.strip() for c in cells]


def make_table(rows, avail):
    head, body = rows[0], rows[1:]
    ncol = len(head)
    data = [[Paragraph(inline(c), S['cellh']) for c in head]]
    for r in body:
        r = (r + [''] * ncol)[:ncol]
        data.append([Paragraph(inline(c), S['cell']) for c in r])

    # ширины: средняя длина + самое длинное слово в колонке (чтобы имена файлов не рвались)
    lens = []
    for j in range(ncol):
        cells = [head[j]] + [r[j] for r in body]
        avg = sum(len(c) for c in cells) / max(len(cells), 1)
        longest = max([len(w) for c in cells for w in c.split()] + [1])
        lens.append(max(avg * 0.62, longest * 1.12, 8))
    total = sum(lens)
    widths = [max(avail * l / total, avail * 0.10) for l in lens]
    k = avail / sum(widths)
    widths = [w * k for w in widths]

    tbl = Table(data, colWidths=widths, repeatRows=1, hAlign='LEFT')
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), SAND),
        ('LINEBELOW', (0, 0), (-1, -1), 0.4, LINE),
        ('LINEABOVE', (0, 0), (-1, 0), 0.4, LINE),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    return tbl


def parse(md_text, avail):
    """markdown → список flowable"""
    out = []
    lines = md_text.split('\n')
    i = 0
    while i < len(lines):
        raw = lines[i]
        line = raw.rstrip()
        s = line.strip()

        if not s:
            i += 1
            continue

        # горизонтальная линия
        if re.fullmatch(r'-{3,}', s):
            out.append(Spacer(1, 4))
            out.append(HRFlowable(width='100%', thickness=0.6, color=LINE,
                                  spaceBefore=2, spaceAfter=8))
            i += 1
            continue

        # код-блок
        if s.startswith('```'):
            i += 1
            buf = []
            while i < len(lines) and not lines[i].strip().startswith('```'):
                buf.append(lines[i])
                i += 1
            i += 1
            txt = '<br/>'.join(
                esc(b.replace('\t', '    ')).replace('  ', ' &nbsp;')
                if b.strip() else '&nbsp;' for b in buf)
            p = Paragraph(txt, S['code'])
            box = Table([[p]], colWidths=[avail], hAlign='LEFT')
            box.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F2EEE7')),
                ('BOX', (0, 0), (-1, -1), 0.4, LINE),
                ('LEFTPADDING', (0, 0), (-1, -1), 9),
                ('RIGHTPADDING', (0, 0), (-1, -1), 9),
                ('TOPPADDING', (0, 0), (-1, -1), 7),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
            ]))
            out.append(Spacer(1, 3))
            out.append(box)
            out.append(Spacer(1, 9))
            continue

        # заголовки
        m = re.match(r'^(#{1,4})\s+(.*)$', s)
        if m:
            lvl = len(m.group(1))
            txt = m.group(2).strip()
            is_block = txt.upper().startswith('БЛОК')
            style = S['block'] if is_block else S['h%d' % lvl]
            p = Paragraph(inline(txt), style)
            p._toc = (lvl, re.sub(r'[*`]', '', txt))
            out.append(p)
            i += 1
            continue

        # таблица
        if is_table_row(s) and i + 1 < len(lines) and \
                re.fullmatch(r'\|[\s:|-]+\|', lines[i + 1].strip()):
            rows = [split_row(s)]
            i += 2
            while i < len(lines) and is_table_row(lines[i]):
                rows.append(split_row(lines[i]))
                i += 1
            out.append(Spacer(1, 3))
            out.append(make_table(rows, avail))
            out.append(Spacer(1, 9))
            continue

        # цитата
        if s.startswith('>'):
            buf = []
            while i < len(lines) and lines[i].strip().startswith('>'):
                buf.append(lines[i].strip().lstrip('>').strip())
                i += 1
            txt = '<br/>'.join(inline(b) for b in buf if b)
            q = Table([[Paragraph(txt, S['quote'])]], colWidths=[avail], hAlign='LEFT')
            q.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#EFEAE1')),
                ('LINEBEFORE', (0, 0), (0, -1), 2.4, ACC),
                ('LEFTPADDING', (0, 0), (-1, -1), 11),
                ('RIGHTPADDING', (0, 0), (-1, -1), 11),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            out.append(Spacer(1, 3))
            out.append(q)
            out.append(Spacer(1, 9))
            continue

        # списки (с переносом строк-продолжений, начинающихся с отступа)
        def _cont(j):
            """строки-продолжения пункта списка: с отступом и не новый пункт"""
            parts = []
            while j < len(lines):
                nxt = lines[j]
                if not nxt.strip():
                    break
                if not nxt.startswith(('  ', '\t')):
                    break
                st = nxt.strip()
                if re.match(r'^([-*]|\d+\.)\s+', st) or st.startswith(('#', '|', '>', '```')):
                    break
                parts.append(st)
                j += 1
            return ' '.join(parts), j

        if re.match(r'^[-*]\s+', s):
            txt = re.sub(r'^[-*]\s+', '', s)
            more, i = _cont(i + 1)
            if more:
                txt = txt + ' ' + more
            out.append(Paragraph(inline(txt), S['bullet'], bulletText='•'))
            continue
        if re.match(r'^\d+\.\s+', s):
            num = re.match(r'^(\d+)\.', s).group(1)
            txt = re.sub(r'^\d+\.\s+', '', s)
            more, i = _cont(i + 1)
            if more:
                txt = txt + ' ' + more
            out.append(Paragraph(inline(txt), S['bullet'], bulletText='%s.' % num))
            continue

        # абзац (склеиваем до пустой строки)
        buf = [s]
        i += 1
        while i < len(lines):
            nxt = lines[i].strip()
            if (not nxt or nxt.startswith('#') or nxt.startswith('>')
                    or nxt.startswith('```') or is_table_row(nxt)
                    or re.match(r'^[-*]\s+', nxt) or re.match(r'^\d+\.\s+', nxt)
                    or re.fullmatch(r'-{3,}', nxt)):
                break
            buf.append(nxt)
            i += 1
        # строки-метки («**Кнопка 1:** …») не склеиваем в один абзац — разделяем переносом
        label = re.compile(r'^\*\*[^*]+:?\*\*')
        parts = [buf[0]]
        for nxt in buf[1:]:
            if label.match(nxt) and label.match(parts[-1]):
                parts[-1] = parts[-1] + '\x00' + nxt
            else:
                parts[-1] = parts[-1] + ' ' + nxt
        out.append(Paragraph(inline(parts[0]), S['body']))
    return out


class Doc(BaseDocTemplate):
    """документ с колонтитулом, нумерацией и закладками"""

    def __init__(self, filename, header='BAK MASTERS', **kw):
        self.header = header
        self._last_level = -1
        BaseDocTemplate.__init__(
            self, filename, pagesize=A4,
            leftMargin=20 * mm, rightMargin=20 * mm,
            topMargin=24 * mm, bottomMargin=18 * mm,
            title=kw.pop('title', 'BAK MASTERS'),
            author='BAK MASTERS', **kw)
        frame = Frame(self.leftMargin, self.bottomMargin,
                      self.width, self.height, id='n')
        self.addPageTemplates([PageTemplate(id='p', frames=[frame],
                                            onPage=self._deco)])

    def _deco(self, canv, doc):
        if doc.page == 1:
            return
        canv.saveState()
        canv.setFont('M-400', 7.5)
        canv.setFillColor(MUTED)
        canv.drawString(20 * mm, A4[1] - 13 * mm, self.header)
        canv.drawRightString(A4[0] - 20 * mm, A4[1] - 13 * mm, 'bakmasters.su')
        canv.setStrokeColor(LINE)
        canv.setLineWidth(0.4)
        canv.line(20 * mm, A4[1] - 15 * mm, A4[0] - 20 * mm, A4[1] - 15 * mm)
        canv.setFont('M-400', 8)
        canv.setFillColor(MUTED)
        canv.drawCentredString(A4[0] / 2, 11 * mm, str(doc.page))
        canv.restoreState()

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and hasattr(flowable, '_toc'):
            lvl, txt = flowable._toc
            if lvl > 3:
                return
            key = 'bk%d' % id(flowable)
            self.canv.bookmarkPage(key)
            want = max(0, lvl - 1)
            level = min(want, self._last_level + 1)   # без прыжков через уровень
            self._last_level = level
            self.canv.addOutlineEntry(txt, key, level=level, closed=level > 0)
            try:
                self.notify('TOCEntry', (lvl, txt, self.page))
            except Exception:
                pass


def cover_flowables(title, subtitle, meta, avail):
    fl = [Spacer(1, 60 * mm)]
    bar = Table([['']], colWidths=[36], rowHeights=[5])
    bar.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), ACC)]))
    fl.append(bar)
    fl.append(Spacer(1, 8))
    fl.append(Paragraph(esc(title), S['cover_t']))
    fl.append(Spacer(1, 6))
    if subtitle:
        fl.append(Paragraph(esc(subtitle), S['cover_s']))
    fl.append(Spacer(1, 14 * mm))
    for m in meta:
        fl.append(Paragraph(esc(m), S['cover_s']))
    return fl


def build(md_paths, pdf_path, title, subtitle='', meta=None, toc=False,
          header='BAK MASTERS', drop_first_h1=True):
    """md_paths: список путей (объединяются в один PDF)"""
    doc = Doc(pdf_path, header=header, title=title)
    avail = doc.width
    story = cover_flowables(title, subtitle, meta or [], avail)
    story.append(Spacer(1, 10))
    if toc:
        story.append(HRFlowable(width='100%', thickness=0.6, color=LINE,
                                spaceBefore=6, spaceAfter=12))
        story.append(Paragraph('Содержание', S['h2']))
        t = TableOfContents()
        t.levelStyles = [S['toc1'], S['toc2'], S['toc2']]
        t.dotsMinLevel = 0
        story.append(t)
        from reportlab.platypus import PageBreak
        story.append(PageBreak())

    for n, md in enumerate(md_paths):
        txt = open(md, encoding='utf-8').read()
        if n == 0 and drop_first_h1:
            txt = re.sub(r'^#\s+[^\n]*\n', '', txt, count=1)
        if n > 0 and not toc:
            from reportlab.platypus import PageBreak
            story.append(PageBreak())
        story.extend(parse(txt, avail))

    if toc:
        doc.multiBuild(story)
    else:
        doc.build(story)
    return pdf_path


if __name__ == '__main__':
    print('модуль, запускать через sobiraem-pdf.py')
