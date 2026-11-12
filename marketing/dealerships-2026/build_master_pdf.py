#!/usr/bin/env python3
"""Сводный документ «Работа с автосалонами» — один PDF, две части.

Часть I  — страницы для чтения с экрана (тёмные, плотные).
Часть II — страницы для печати (белые, светлые по краске, с формами и галочками).

Каждая страница помечена бейджем «ЭКРАН» или «ПЕЧАТЬ» и имеет свой номер
внутри части (Э1…, П1…), чтобы распечатанные листы не путались с экранными.

Данные для таблиц базы читаются из CSV рядом со скриптом.

Запуск из корня репозитория:
    .venv/bin/python marketing/dealerships-2026/build_master_pdf.py
"""

from __future__ import annotations

import csv
import os
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Flowable, Frame, KeepTogether,
                                NextPageTemplate, PageBreak, PageTemplate,
                                Paragraph, Spacer, Table, TableStyle)

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
OUT = HERE / "SM-Production-avtosalony-2026.pdf"

FONT_DIR = Path("/tmp/fonts-dealer")
FONT_SRC = REPO / "banners/anikom-arena-3000x2500-concepts/source/Montserrat-Variable.ttf"

# ── палитра ─────────────────────────────────────────────────────────────────
# экран
D_BG = colors.HexColor("#0B0D10")
D_CARD = colors.HexColor("#15191F")
D_IVORY = colors.HexColor("#F2EFE7")
D_MUTED = colors.HexColor("#8B929B")
D_LINE = colors.HexColor("#2A3038")
D_ACCENT = colors.HexColor("#FF4D1C")
D_ACID = colors.HexColor("#D8FF3E")
# печать
P_PAPER = colors.white
P_INK = colors.HexColor("#12141A")
P_GREY = colors.HexColor("#6B7078")
P_RULE = colors.HexColor("#C9C9C4")
P_TINT = colors.HexColor("#F4F3EF")

PAGE_W, PAGE_H = A4
ML, MR, MT, MB = 20 * mm, 20 * mm, 18 * mm, 20 * mm
CONTENT_W = PAGE_W - ML - MR


def register_fonts() -> None:
    FONT_DIR.mkdir(parents=True, exist_ok=True)
    for name, weight in [("Regular", 400), ("Medium", 500),
                         ("SemiBold", 600), ("Bold", 700)]:
        out = FONT_DIR / f"Montserrat-{name}.ttf"
        if out.exists() and out.stat().st_size < 500_000:
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


# ── стили ───────────────────────────────────────────────────────────────────
def sty(name, **kw):
    base = dict(fontName="M", fontSize=9.4, leading=14, alignment=TA_LEFT)
    base.update(kw)
    return ParagraphStyle(name, **base)


def styles(dark: bool):
    fg = D_IVORY if dark else P_INK
    muted = D_MUTED if dark else P_GREY
    return {
        "lead": sty(f"lead{dark}", fontName="MM", fontSize=11.2, leading=17.4, textColor=fg),
        "body": sty(f"body{dark}", fontSize=9.4, leading=14.4, textColor=fg),
        "body_s": sty(f"bodys{dark}", fontSize=8.6, leading=13, textColor=fg),
        "muted": sty(f"muted{dark}", fontSize=8.2, leading=12.4, textColor=muted),
        "h2": sty(f"h2{dark}", fontName="MS", fontSize=11.6, leading=15,
                  textColor=fg, spaceBefore=6, spaceAfter=3),
        "h3": sty(f"h3{dark}", fontName="MS", fontSize=9.6, leading=13.4,
                  textColor=fg, spaceBefore=4, spaceAfter=2),
        "quote": sty(f"quote{dark}", fontName="MM", fontSize=10.2, leading=15.6, textColor=fg),
        "cell": sty(f"cell{dark}", fontSize=8.1, leading=11.6, textColor=fg),
        "cell_s": sty(f"cells{dark}", fontSize=7.5, leading=10.6, textColor=fg),
        "cell_head": sty(f"cellh{dark}", fontName="MS", fontSize=7.6, leading=10.8,
                         textColor=D_BG if dark else colors.white),
        "bullet": sty(f"bul{dark}", fontSize=9.2, leading=13.8, textColor=fg,
                      leftIndent=9, bulletIndent=0),
        "_fg": fg, "_muted": muted, "_dark": dark,
    }


S_D = styles(True)
S_P = styles(False)


def para(text, kind="body", dark=True):
    return Paragraph(text, (S_D if dark else S_P)[kind])


# ── примитивы ───────────────────────────────────────────────────────────────
class HRule(Flowable):
    def __init__(self, width=CONTENT_W, color=P_RULE, thickness=0.5, space_before=0,
                 space_after=0):
        super().__init__()
        self.width, self.color = width, color
        self.thickness = thickness
        self.height = space_before + thickness + space_after
        self.sb = space_before

    def draw(self):
        c = self.canv
        c.setStrokeColor(self.color)
        c.setLineWidth(self.thickness)
        c.line(0, self.height - self.thickness - self.sb, self.width,
               self.height - self.thickness - self.sb)


class SectionHead(Flowable):
    """Номер + название раздела, с акцентной чертой."""

    def __init__(self, number, title, subtitle="", dark=True, width=CONTENT_W):
        super().__init__()
        self.number, self.title, self.subtitle = number, title, subtitle
        self.dark, self.width = dark, width
        self.height = 30 if subtitle else 24

    def draw(self):
        c = self.canv
        fg = D_IVORY if self.dark else P_INK
        muted = D_MUTED if self.dark else P_GREY
        num_fs = 22 if len(self.number) <= 2 else 16
        c.setFont("MB", num_fs)
        c.setFillColor(D_ACCENT)
        c.drawString(0, self.height - 22, self.number)
        num_w = c.stringWidth(self.number, "MB", num_fs)
        x = num_w + 8
        c.setFont("MB", 15)
        c.setFillColor(fg)
        c.drawString(x, self.height - 21, self.title)
        if self.subtitle:
            c.setFont("M", 8.4)
            c.setFillColor(muted)
            c.drawString(x, self.height - 32, self.subtitle)


class Panel(Flowable):
    """Плашка: заливка + акцентная полоса слева + текст."""

    def __init__(self, text, dark=True, fill=None, bar=D_ACCENT, fs=9.6, pad=10,
                 width=CONTENT_W, bold=False):
        super().__init__()
        self.width, self.pad = width, pad
        self.fill = fill or (D_CARD if dark else P_TINT)
        self.bar = bar
        fg = D_IVORY if dark else P_INK
        self.para = Paragraph(text, sty("panel", fontName="MM" if bold else "M",
                                        fontSize=fs, leading=fs * 1.5, textColor=fg))
        _, self.ph = self.para.wrap(width - pad * 2 - 4, 800)
        self.height = self.ph + pad * 2

    def draw(self):
        c = self.canv
        c.setFillColor(self.fill)
        c.rect(0, 0, self.width, self.height, stroke=0, fill=1)
        c.setFillColor(self.bar)
        c.rect(0, 0, 3, self.height, stroke=0, fill=1)
        self.para.drawOn(c, self.pad + 4, self.pad)


class Badge(Flowable):
    """Крупный бейдж «ЭКРАН» / «ПЕЧАТЬ» для разделителей."""

    def __init__(self, text, dark=True):
        super().__init__()
        self.text, self.dark = text, dark
        self.width, self.height = 120, 22

    def draw(self):
        c = self.canv
        fg = D_IVORY if self.dark else P_INK
        c.setStrokeColor(fg)
        c.setLineWidth(1)
        c.rect(0, 0, self.width, self.height, stroke=1, fill=0)
        c.setFont("MB", 10)
        c.setFillColor(fg)
        c.drawCentredString(self.width / 2, 6.5, self.text)


class KPI(Flowable):
    def __init__(self, items, dark=True, width=CONTENT_W, height=44):
        super().__init__()
        self.items, self.width, self.dark, self.height = items, width, dark, height

    def draw(self):
        c = self.canv
        fg = D_IVORY if self.dark else P_INK
        muted = D_MUTED if self.dark else P_GREY
        line = D_LINE if self.dark else P_RULE
        n = len(self.items)
        col = self.width / n
        for i, (value, caption) in enumerate(self.items):
            x = i * col
            if i:
                c.setStrokeColor(line)
                c.setLineWidth(0.5)
                c.line(x, 2, x, self.height - 4)
            fs = 18.0
            while fs > 10 and c.stringWidth(value, "MB", fs) > col - 16:
                fs -= 0.5
            c.setFont("MB", fs)
            c.setFillColor(fg)
            c.drawString(x + 9, self.height - 24, value)
            c.setFont("M", 7.4)
            c.setFillColor(muted)
            for j, chunk in enumerate(_wrap2(caption, int(col / 3.9))):
                c.drawString(x + 9, self.height - 35 - j * 8.6, chunk)


def _wrap2(text, chars):
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 <= chars:
            cur = (cur + " " + w).strip()
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines[:2]


class CheckItem(Flowable):
    """Квадрат-чекбокс + текст. Рисуется, а не печатается глифом: чётко на бумаге."""

    def __init__(self, text, dark=True, box=8.4, fs=8.8, width=CONTENT_W):
        super().__init__()
        fg = D_IVORY if dark else P_INK
        self.para = Paragraph(text, sty("chk", fontSize=fs, leading=fs * 1.45, textColor=fg))
        self.pw = width - box - 8
        _, ph = self.para.wrap(self.pw, 400)
        self.height = max(box + 1, ph)
        self.box, self.width = box, width
        self.dark = dark

    def draw(self):
        c = self.canv
        fg = D_IVORY if self.dark else P_INK
        c.setStrokeColor(fg)
        c.setLineWidth(0.7)
        top = self.height - 1
        c.rect(0, top - self.box + 1, self.box, self.box, stroke=1, fill=0)
        self.para.drawOn(c, self.box + 8, top - self.height + 1)


def bullets(items, dark=True):
    return [Paragraph(f"•&nbsp;&nbsp;{t}", (S_D if dark else S_P)["bullet"]) for t in items]


def table(data, widths, dark=True, head=True, fs=8.1, zebra=True):
    st = S_D if dark else S_P
    rows = []
    for i, row in enumerate(data):
        cells = []
        for cell in row:
            if isinstance(cell, str):
                if head and i == 0:
                    cells.append(Paragraph(cell, st["cell_head"]))
                else:
                    cells.append(Paragraph(cell, st["cell_s"] if fs < 8 else st["cell"]))
            else:
                cells.append(cell)
        rows.append(cells)
    t = Table(rows, colWidths=widths, repeatRows=1 if head else 0)
    line = D_LINE if dark else P_RULE
    head_bg = D_IVORY if dark else P_INK
    zebra_bg = D_CARD if dark else colors.HexColor("#FAF9F6")
    cmds = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, line),
    ]
    if head:
        cmds += [("BACKGROUND", (0, 0), (-1, 0), head_bg),
                 ("TOPPADDING", (0, 0), (-1, 0), 5.5),
                 ("BOTTOMPADDING", (0, 0), (-1, 0), 5.5)]
    if zebra:
        start = 1 if head else 0
        for i in range(start, len(rows)):
            if (i - start) % 2 == 1:
                cmds.append(("BACKGROUND", (0, i), (-1, i), zebra_bg))
    t.setStyle(TableStyle(cmds))
    return t


def form(rows, widths, dark=False, row_h=17):
    """Пустая форма: подписи серым, поля с линией снизу."""
    st = S_D if dark else S_P
    data = []
    for label_text, _ in rows:
        data.append([Paragraph(label_text, st["muted"]), ""])
    t = Table(data, colWidths=widths, rowHeights=[row_h] * len(rows))
    line = D_LINE if dark else P_RULE
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
        ("LEFTPADDING", (0, 0), (0, -1), 0),
        ("LEFTPADDING", (1, 0), (1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LINEBELOW", (1, 0), (1, -1), 0.5, line),
    ]))
    return t


# ── данные ──────────────────────────────────────────────────────────────────
def load_prospects():
    with open(HERE / "prospects-moscow-inside-mkad.csv", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter=";"))


def load_contacts():
    with open(HERE / "public-employee-contacts.csv", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter=";"))


PROSPECTS = load_prospects()
CONTACTS = load_contacts()
N_SITES = len(PROSPECTS)
N_ACCOUNTS = len({r["account_id"] for r in PROSPECTS})
N_STAFF = len(CONTACTS)


# ── сборка ──────────────────────────────────────────────────────────────────
class DealerDoc(BaseDocTemplate):
    def __init__(self, path, **kw):
        super().__init__(str(path), pagesize=A4, leftMargin=ML, rightMargin=MR,
                         topMargin=MT, bottomMargin=MB,
                         title="SM Production — работа с автосалонами",
                         author="SM Production",
                         subject="Стратегия, скрипты, база площадок и печатные формы",
                         **kw)
        self.counts = {"screen": 0, "print": 0}
        self.totals = {"screen": 0, "print": 0}

    def _frame(self):
        return Frame(ML, MB, CONTENT_W, PAGE_H - MT - MB, id="f",
                     leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)


def _footer(c, dark, label):
    fg = D_MUTED if dark else P_GREY
    line = D_LINE if dark else P_RULE
    c.setFont("M", 7)
    c.setFillColor(fg)
    c.drawString(ML, 10.5 * mm, "SM Production · работа с автосалонами · ноябрь 2026")
    c.drawRightString(PAGE_W - MR, 10.5 * mm, label)
    c.setStrokeColor(line)
    c.setLineWidth(0.4)
    c.line(ML, 13.6 * mm, PAGE_W - MR, 13.6 * mm)


def _badge(c, text, dark):
    fg = D_MUTED if dark else P_GREY
    line = D_LINE if dark else P_RULE
    w, h = 52, 13
    x = PAGE_W - MR - w
    y = PAGE_H - MT + 6
    c.setStrokeColor(line)
    c.setLineWidth(0.5)
    c.rect(x, y, w, h, stroke=1, fill=0)
    c.setFont("MS", 6.6)
    c.setFillColor(fg)
    c.drawCentredString(x + w / 2, y + 4.4, text)


def on_cover(canv, doc):
    canv.saveState()
    canv.setFillColor(D_BG)
    canv.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    canv.setFillColor(D_ACCENT)
    canv.rect(0, 0, PAGE_W, 5 * mm, stroke=0, fill=1)
    canv.setFillColor(D_ACID)
    canv.rect(ML, PAGE_H - 42 * mm, 34 * mm, 2.4 * mm, stroke=0, fill=1)
    canv.setFillColor(D_MUTED)
    canv.setFont("M", 7.6)
    canv.drawString(ML, 24 * mm, "Внутренний документ. Не для отправки клиентам.")
    canv.drawString(ML, 20 * mm, "Собран из файлов marketing/dealerships-2026")
    canv.restoreState()


def on_screen(canv, doc):
    doc.counts["screen"] += 1
    canv.saveState()
    canv.setFillColor(D_BG)
    canv.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    canv.restoreState()
    _badge(canv, "ЭКРАН", True)
    _footer(canv, True, f"Э{doc.counts['screen']} из {doc.totals['screen'] or '—'}")


def on_print(canv, doc):
    doc.counts["print"] += 1
    _badge(canv, "ПЕЧАТЬ", False)
    _footer(canv, False, f"П{doc.counts['print']} из {doc.totals['print'] or '—'}")


def build_stream():
    story = []
    add = story.append

    # ══════════════════════════════════ ОБЛОЖКА ═════════════════════════════
    add(NextPageTemplate("screen"))
    add(Spacer(1, 62 * mm))
    add(para("SM PRODUCTION", "muted", True))
    add(Spacer(1, 7 * mm))
    add(Paragraph("Работа<br/>с автосалонами",
                  sty("t", fontName="MB", fontSize=40, leading=44, textColor=D_IVORY)))
    add(Spacer(1, 8 * mm))
    add(Paragraph("Как заходить в дилерские центры,<br/>что говорить и что печатать",
                  sty("s", fontName="M", fontSize=13, leading=19, textColor=D_MUTED)))
    add(Spacer(1, 16 * mm))
    add(Panel("Один документ, две части: <b>экран</b> — то, что меняется (стратегия, "
              "база, нормативы); <b>печать</b> — то, что держат в руках у телефона "
              "(скрипт, возражения, карточки, чек-листы).", dark=True, width=CONTENT_W * 0.9, fs=10))
    add(Spacer(1, 22 * mm))
    add(KPI([(f"{N_SITES}", "площадок в базе"),
             (f"{N_ACCOUNTS}", "аккаунтов без дублей"),
             ("30", "аккаунтов в пилоте"),
             ("90", "дней горизонт")], dark=True))
    add(PageBreak())

    # ══════════════════════════════════ КАК ПОЛЬЗОВАТЬСЯ ════════════════════
    add(SectionHead("00", "Как пользоваться", "Две части, два способа читать", dark=True))
    add(Spacer(1, 4 * mm))
    add(para("Документ намеренно разделён. На экране удобно читать длинное и то, что "
             "меняется: стратегию, базу площадок, нормативы. На бумаге удобно то, что "
             "нужно в момент действия: скрипт перед глазами, возражения под рукой, "
             "пустая карточка после звонка.", "lead", True))
    add(Spacer(1, 5 * mm))
    add(para("Оглавление", "h2", True))
    add(Spacer(1, 1 * mm))
    screen_items = [
        ("Э1", "Как пользоваться и как печатать"),
        ("Э2", "01 · Суть направления"),
        ("Э3", "02 · Идеальный клиент"),
        ("Э4", "03 · Кто принимает решение"),
        ("Э5", "04 · Три продукта входа"),
        ("Э6", "05 · Первый оффер"),
        ("Э7", "06 · Воронка и стадии"),
        ("Э8", "07 · Касания и когда звонить"),
        ("Э9", "08 · CRM"),
        ("Э10", "09 · Пилот на 30 аккаунтов"),
        ("Э11", "10 · План на четыре недели"),
        ("Э12", "11 · База: волна A"),
        ("Э13", "11 · База: волна B и аккаунты"),
        ("Э14", "12 · Публичные контакты"),
        ("Э15", "13 · Правила качества"),
        ("Э16", "14 · Где что лежит"),
    ]
    print_items = [
        ("П1", "Титул печатной части"),
        ("П2", "Как печатать: список листов"),
        ("П3", "Шпаргалка: ресепшн"),
        ("П4", "Шпаргалка: ответственный"),
        ("П5", "Шпаргалка: выход и отказы"),
        ("П6", "Возражения, шесть сценариев"),
        ("П7", "Карточка звонка № 1"),
        ("П8", "Карточка звонка № 2"),
        ("П9", "Чек-лист дня и норма"),
        ("П10", "Оценочный лист звонка"),
        ("П11", "План звонков на неделю"),
    ]
    muted = sty("tocm", fontName="M", fontSize=7.8, leading=12.2, textColor=D_MUTED)
    body = sty("tocb", fontName="M", fontSize=7.8, leading=12.2, textColor=D_IVORY)
    head = sty("toch", fontName="MS", fontSize=8.2, leading=11, textColor=D_ACID)

    def col(items, label):
        rows = [[Paragraph(label, head)]]
        for num, title in items:
            rows.append([Paragraph(f'<font color="#FF4D1C"><b>{num}</b></font>&nbsp;&nbsp;{title}',
                                   body)])
        t = Table(rows, colWidths=[CONTENT_W / 2 - 4])
        t.setStyle(TableStyle([
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 1.6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1.6),
            ("LINEBELOW", (0, 0), (-1, 0), 0.6, D_LINE),
        ]))
        return t

    toc = Table([[col(screen_items, "ЧАСТЬ I · ЭКРАН"),
                  col(print_items, "ЧАСТЬ II · ПЕЧАТЬ")]],
                colWidths=[CONTENT_W / 2, CONTENT_W / 2])
    toc.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("LINEBEFORE", (1, 0), (1, 0), 0.6, D_LINE),
        ("LEFTPADDING", (1, 0), (1, 0), 10),
    ]))
    add(toc)
    add(Spacer(1, 6 * mm))
    add(para("Как печатать", "h2", True))
    story.extend(bullets([
        "А4, <b>100&nbsp;% без масштабирования</b> — иначе поля и строки форм разъедутся.",
        "Чёрно-белая печать допустима: цвет в печатной части ничего не кодирует.",
        "Печатать только <b>вторую часть</b> — листы П1–П11. Экранные страницы "
        "на бумаге бессмысленны: там тёмный фон и мелкая графика.",
        "Карточку звонка (П7 и П8) печатать пачкой по 10–15 штук: одна карточка на звонок.",
        "Оценочный лист (П10) — по числу слушателей на разборе.",
    ], True))
    add(Spacer(1, 5 * mm))
    add(Panel("Правило нумерации: у каждой части свой счёт. Подпись «П5» — это не "
              "пятая страница файла, а пятый лист печатной части: именно так они лежат "
              "в папке после печати. Экранные подписаны так же — Э1…Э16.",
              dark=True, bar=D_ACID))
    add(PageBreak())

    # ══════════════════════════════════ 01 НАПРАВЛЕНИЕ ═════════════════════
    add(SectionHead("01", "Суть направления",
                    "Что продаём, чем это отличается от «обзвона базы»", dark=True))
    add(Spacer(1, 4 * mm))
    add(para("Цель — построить повторяемую систему, которая переводит дилерский центр "
             "от первого контакта к небольшой тестовой задаче, а затем к регулярному "
             "производству сезонных материалов, оформлению запусков моделей и "
             "обновлению пространства.", "lead", True))
    add(Spacer(1, 3 * mm))
    add(para("Главный принцип: продавать не «всё рекламное производство», а конкретный "
             "следующий проект с датой, зоной и понятным результатом. «Мы делаем "
             "оформление» — это не предложение. «У вас 12 декабря выход модели, нужен "
             "подиум, фон и фотозона» — предложение.", "body", True))
    add(Spacer(1, 6 * mm))
    add(para("Рабочая формула", "h2", True))
    add(Panel("конкретный центр&nbsp;&nbsp;→&nbsp;&nbsp;конкретный повод&nbsp;&nbsp;→&nbsp;&nbsp;"
              "разрешение на отправку&nbsp;&nbsp;→&nbsp;&nbsp;фотография зоны&nbsp;&nbsp;→&nbsp;&nbsp;"
              "предварительный расчёт&nbsp;&nbsp;→&nbsp;&nbsp;тестовый заказ&nbsp;&nbsp;→&nbsp;&nbsp;"
              "календарь повторных задач", dark=True, bar=D_ACID, fs=9.4))
    add(Spacer(1, 6 * mm))
    add(table([
        ["Параметр", "Значение"],
        ["Горизонт пилота", "90 дней"],
        ["Регион первого этапа", f"Москва и ближайшее Подмосковье · {N_SITES} площадок, "
                                 f"{N_ACCOUNTS} корпоративных аккаунтов"],
        ["Ритм", "3–5 новых аккаунтов в день плюс follow-up по начатым контактам"],
        ["Основной канал", "телефон → разрешение → письмо → повторный звонок"],
        ["Посадочная страница", "sm-production.ru/uslugi/oformlenie-avtosalonov"],
    ], widths=[46 * mm, CONTENT_W - 46 * mm], dark=True))
    add(Spacer(1, 6 * mm))
    add(para("Три вещи, которые нельзя путать", "h2", True))
    add(table([
        ["Так не работает", "Так работает"],
        ["«Обзвонить базу»", "Три конкретных звонка в день по возрастанию сложности"],
        ["Отправить прайс", "Взять фотографию зоны и дату, посчитать по ним"],
        ["Договориться о встрече", "Договориться об одном следующем шаге с датой и каналом"],
    ], widths=[CONTENT_W * 0.45, CONTENT_W * 0.55], dark=True))
    add(PageBreak())

    # ══════════════════════════════════ 02 КЛИЕНТ ══════════════════════════
    add(SectionHead("02", "Идеальный клиент", "Четыре сегмента и один оффер на каждый", dark=True))
    add(Spacer(1, 4 * mm))
    add(table([
        ["", "Сегмент", "Признаки", "Оффер"],
        ["A", "<b>Крупные дилерские группы</b>",
         "Несколько центров в Москве и области, централизованный маркетинг или закупки, "
         "регулярные сезонные кампании, презентации моделей, потребность тиражировать "
         "единое оформление по адресам",
         "Единый производственный подрядчик: спецификации по адресам, маркировка "
         "комплектов, согласованный график монтажа"],
        ["B", "<b>Отдельные активные центры</b>",
         "Локальный маркетолог может быстро запустить задачу, есть конкретная сезонная "
         "кампания, презентация или зона, которую нужно обновить",
         "Бесплатный экспресс-аудит по фотографиям, состав носителей и предварительный "
         "расчёт в течение рабочего дня"],
        ["C", "<b>Авто с пробегом и мультибренд</b>",
         "Навигация по территории, оформление зон оценки, кредита и выдачи, регулярные "
         "ценовые и сезонные коммуникации, мобильные конструкции",
         "Модульное оформление, которое обновляется без полной переделки пространства"],
        ["D", "<b>Агентства с автомобильными брендами</b>",
         "Нужен производственный партнёр white label, срочный расчёт, монтаж по ТЗ, "
         "фотоотчёт",
         "Производство и монтаж без конкуренции за клиентский аккаунт"],
    ], widths=[7 * mm, 38 * mm, CONTENT_W - 7 * mm - 38 * mm - 56 * mm, 56 * mm], dark=True))
    add(Spacer(1, 6 * mm))
    add(para("Почему приоритет именно такой", "h2", True))
    add(para("В группе одно решение открывает несколько площадок — это самый короткий "
             "путь к тиражу. Но вход в группу дольше и требовательнее. Отдельный центр "
             "закрывает сделку быстрее и даёт материал для кейса. Поэтому в базе "
             f"{N_SITES} площадок, но обращений — {N_ACCOUNTS}: сначала группа, потом "
             "пилот на одной площадке.", "body", True))
    add(Spacer(1, 5 * mm))
    add(Panel("Ошибка новичка: идти в самый крупный и самый известный центр первым. "
              "Там дольше согласование и выше требования к портфолио. Первый звонок "
              "делается туда, где спокойнее ресепшн и короче путь до маркетолога.",
              dark=True, bar=D_ACCENT))
    add(PageBreak())

    # ══════════════════════════════════ 03 КТО РЕШАЕТ ══════════════════════
    add(SectionHead("03", "Кто принимает решение",
                    "С кем говорить и с чего начинать разговор", dark=True))
    add(Spacer(1, 4 * mm))
    add(table([
        ["Роль", "Что для неё важно", "С чего начинать разговор"],
        ["Директор по маркетингу группы", "единый стандарт, сроки, масштабирование",
         "оформление нескольких центров и сезонный календарь"],
        ["Локальный маркетолог", "быстро запустить кампанию",
         "фотографии зоны → предварительный расчёт"],
        ["Директор дилерского центра", "не мешать продажам и сервису",
         "монтаж вне клиентского потока, один ответственный"],
        ["Event / BTL-менеджер", "запуск модели или клиентское событие",
         "подиум, фон, фотозона, регистрация, навигация"],
        ["АХО / эксплуатация", "безопасность, доступ, чистота, электрика",
         "обследование, защита поверхностей, график работ"],
        ["Закупки", "сравнимость предложений и документы",
         "<b>подключать последними</b> — после появления внутреннего заказчика и ТЗ"],
    ], widths=[40 * mm, 52 * mm, CONTENT_W - 92 * mm], dark=True))
    add(Spacer(1, 6 * mm))
    add(para("Правило входа", "h2", True))
    add(para("Не начинать с закупок. Сначала нужен владелец задачи из маркетинга или "
             "руководства центра: он объясняет, зачем это нужно, и он же потом "
             "защищает смету. Закупки появляются, когда задача уже есть, — иначе "
             "разговор сводится к «пришлите документы».", "body", True))
    add(Spacer(1, 5 * mm))
    add(para("Публичные имена — как ими пользоваться", "h2", True))
    add(para(f"В базе {N_STAFF} публично названных сотрудников. Имя и должность с "
             "официального сайта — это законный способ войти через человека, но не "
             "доказательство, что он отвечает за закупку. Формулировка на ресепшене: "
             "«подскажите, как правильно обратиться по оформлению зон», а не «мне нужно "
             "с ним обсудить закупку».", "body", True))
    add(Spacer(1, 5 * mm))
    add(Panel("Никогда не утверждать, что человек «курирует закупки», если это не "
              "написано на его странице. Один такой вопрос закрывает дверь надолго.",
              dark=True, bar=D_ACCENT))
    add(PageBreak())

    # ══════════════════════════════════ 04 ПРОДУКТЫ ════════════════════════
    add(SectionHead("04", "Три продукта входа",
                    "Не «всё производство», а один понятный первый проект", dark=True))
    add(Spacer(1, 4 * mm))
    add(table([
        ["Продукт", "Состав", "Когда предлагать"],
        ["<b>1. Сезонное обновление</b>",
         "Витринная графика, баннеры, Roll Up, POS, информационные стойки, напольные "
         "элементы, сменная навигация",
         "За 4–6 недель до запуска сезонной кампании: акция, праздники, смена "
         "спецпредложений"],
        ["<b>2. Презентация модели</b>",
         "Подиум, презентационный фон, фотозона, регистрация, навигация, объёмная "
         "графика, декоративный свет, монтаж",
         "После появления даты запуска продаж, клиентского вечера, тест-драйва, "
         "пресс-дня"],
        ["<b>3. Обновление пространства</b>",
         "Ресепшн, зона выдачи, стены, световые логотипы, навигация, витрины, "
         "фасадные элементы",
         "После ремонта, ребрендинга, смены стандарта марки или когда клиентская "
         "зона «болит»"],
    ], widths=[40 * mm, CONTENT_W - 40 * mm - 52 * mm, 52 * mm], dark=True))
    add(Spacer(1, 6 * mm))
    add(para("Зачем ровно три", "h2", True))
    add(para("Три продукта закрывают три разных повода, по которым дилерский центр "
             "вообще что-то заказывает: календарь, событие и состояние помещения. "
             "Любой запрос клиента раскладывается в один из них — и сразу понятно, "
             "какие вводные нужны.", "body", True))
    add(Spacer(1, 4 * mm))
    add(table([
        ["Если клиент говорит", "Это продукт", "Что спросить"],
        ["«У нас акция с 1 декабря»", "1. Сезонное обновление",
         "какие зоны задействованы, что уже есть, когда нужен монтаж"],
        ["«Выходит новая модель»", "2. Презентация модели",
         "дата, площадка внутри салона, состав зон, брендбук"],
        ["«Хотим обновить ресепшн»", "3. Обновление пространства",
         "фото, размеры, что не устраивает сейчас, кто согласует"],
        ["«Нужен подрядчик на всё»", "—", "какая задача первая и с какой датой"],
    ], widths=[46 * mm, 46 * mm, CONTENT_W - 92 * mm], dark=True))
    add(Spacer(1, 8 * mm))
    add(para("Правило одного продукта", "h2", True))
    add(Spacer(1, 2 * mm))
    add(para("На первом звонке звучит <b>один</b> продукт — тот, что совпал с поводом. "
             "Три продукта в одном разговоре читаются как «мы делаем всё» и не "
             "запоминаются. Остальные два появятся, когда центр сделает первый заказ.",
             "body", True))
    add(Spacer(1, 4 * mm))
    add(Panel("Если повод не определяется за два вопроса — это не целевой звонок. "
              "Записать дату возврата и идти дальше, а не перебирать продукты наугад.",
              dark=True, bar=D_ACID, fs=9.2))
    add(PageBreak())

    # ══════════════════════════════════ 05 ОФФЕР ═══════════════════════════
    add(SectionHead("05", "Первый оффер", "Что обещаем и что берём взамен", dark=True))
    add(Spacer(1, 4 * mm))
    add(Panel("Бесплатно посмотрим фотографии или план дилерского центра, уточним "
              "задачу и дату, предложим состав носителей и в течение рабочего дня "
              "подготовим предварительный расчёт. Если решение подходит, согласуем "
              "замер и рабочую концепцию.", dark=True, fs=11, bold=True, pad=14))
    add(Spacer(1, 5 * mm))
    add(para("Почему такой оффер работает", "h2", True))
    story.extend(bullets([
        "не требует готового технического задания — а у центра его обычно нет;",
        "не заставляет сразу согласовывать крупный бюджет;",
        "даёт конкретный следующий шаг вместо «приезжайте, покажем»;",
        "позволяет быстро понять, реальна ли задача, ещё до выезда.",
    ], True))
    add(Spacer(1, 5 * mm))
    add(para("Что получить от клиента", "h2", True))
    add(table([
        ["Вводная", "Зачем она нужна"],
        ["Фотография или видео зоны", "Понять геометрию, свет, что уже висит, где розетки"],
        ["Примерные размеры или план", "Без них любая цифра — фантазия"],
        ["Дата запуска или монтажа", "Определяет, реально ли производство"],
        ["Брендбук или макеты, если есть", "Цвет, шрифт, отступы логотипа"],
        ["Адрес и желаемое время монтажа", "Доступ, разгрузка, работа вне клиентского потока"],
    ], widths=[62 * mm, CONTENT_W - 62 * mm], dark=True))
    add(Spacer(1, 5 * mm))
    add(para("Что нельзя обещать", "h2", True))
    add(para("Окончательную цену без размеров и условий · готовую концепцию за один "
             "день · любой срок без подтверждения производства · монтаж без остановки "
             "работы до проверки доступа · точное совпадение цвета без проверки "
             "технологии · любую фасадную конструкцию без обследования · несуществующие "
             "кейсы и клиентов.", "body", True))
    add(Spacer(1, 4 * mm))
    add(Panel("Рабочая формулировка: «подтвердим после проверки задачи производством "
              "и руководителем проекта». Она не звучит как отказ и не создаёт долга.",
              dark=True, bar=D_ACID, fs=9.2))
    add(PageBreak())

    # ══════════════════════════════════ 06 ВОРОНКА ══════════════════════════
    add(SectionHead("06", "Воронка", "Одиннадцать стадий — и что должно лежать в CRM",
                    dark=True))
    add(Spacer(1, 4 * mm))
    funnel = [
        ("1", "Целевой аккаунт", "подтверждены центр, адрес, сайт, телефон"),
        ("2", "Найден ответственный", "имя, должность, рабочий контакт"),
        ("3", "Получено согласие", "человек разрешил отправить материалы"),
        ("4", "Презентация отправлена", "письмо персонализировано под центр"),
        ("5", "Содержательный разговор", "выявлена задача или месяц возврата"),
        ("6", "Получены вводные", "фото, размеры, дата или брендбук"),
        ("7", "Предварительный расчёт", "состав работ и цифра за рабочий день"),
        ("8", "Замер / подробный бриф", "выезд или видеообход зоны"),
        ("9", "Коммерческое предложение", "смета и сроки"),
        ("10", "Тестовый заказ", "одна зона или один комплект"),
        ("11", "Регулярный клиент", "согласован календарь повторных задач"),
    ]
    rows = [["№", "Стадия", "Признак перехода"]] + [[n, s, d] for n, s, d in funnel]
    add(table(rows, widths=[10 * mm, 58 * mm, CONTENT_W - 68 * mm], dark=True))
    add(Spacer(1, 5 * mm))
    add(para("Где чаще всего застревают", "h2", True))
    add(table([
        ["Стадия", "Что происходит", "Что делать"],
        ["2 → 3", "Ресепшн даёт общий адрес info@, письмо умирает в общей папке",
         "Просить имя и должность, писать лично, ссылаться на разговор"],
        ["5 → 6", "«Интересно, пришлите материалы» — и тишина",
         "Один вопрос в конце письма + касание через 2–3 дня"],
        ["6 → 7", "Вводных мало: нет размеров и даты",
         "Не считать «на глаз» — запросить фото с предметом для масштаба"],
        ["9 → 10", "Смета ушла, ответа нет",
         "Разбить смету на обязательную часть и опции, предложить пилот на одной зоне"],
    ], widths=[16 * mm, CONTENT_W * 0.46, CONTENT_W * 0.54 - 16 * mm], dark=True))
    add(PageBreak())

    # ══════════════════════════════════ 07 КАСАНИЯ ══════════════════════════
    add(SectionHead("07", "Касания", "Пять шагов на 45 дней, дальше — только новый повод",
                    dark=True))
    add(Spacer(1, 4 * mm))
    add(table([
        ["Когда", "Что делаем", "Цель"],
        ["День 0", "Изучить центр: сайт, акции, новости, бренды, выбрать один повод",
         "персонализация, без которой звонок общий"],
        ["День 1", "Звонок на официальный номер", "найти ответственного и получить "
                                                 "разрешение отправить материалы"],
        ["День 1, +30 мин", "Письмо после звонка", "закрепить договорённость, пока "
                                                   "разговор помнят"],
        ["День 3", "Повторный звонок: «получили материалы?»",
         "выяснить актуальный сценарий: сезон, модель или пространство"],
        ["День 7", "Короткое финальное письмо с одним вопросом",
         "получить дату возврата или вводные"],
        ["30–45 дней", "Новое касание — только с новым поводом",
         "не превращать контакт в спам"],
    ], widths=[26 * mm, CONTENT_W - 26 * mm - 62 * mm, 62 * mm], dark=True))
    add(Spacer(1, 6 * mm))
    add(para("Что считается новым поводом", "h2", True))
    add(para("Новая модель, смена сезона, выставка, ремонт шоурума, публикация о "
             "расширении, смена стандарта марки. Повод берётся с их сайта, а не из "
             "головы. «Ну что, надумали?» — это не повод, а напоминание о себе.",
             "body", True))
    add(Spacer(1, 5 * mm))
    add(Panel("После прямого отказа не писать и не звонить без нового повода. Один "
              "лишний звонок стоит дороже, чем весь контакт: в группе один маркетинг, "
              "и запомнят всю компанию, а не менеджера.", dark=True, bar=D_ACCENT))
    add(Spacer(1, 6 * mm))
    add(para("Когда звонить", "h2", True))
    add(table([
        ["Хорошо", "Плохо"],
        ["вторник–четверг, 10:30–12:00 и 15:00–17:00", "понедельник до обеда, пятница после 16:00"],
        ["сразу после открытия шоурума", "первый день большой акции"],
        ["за 2–3 недели до сезонной смены", "последняя неделя месяца, 30–31 декабря, майские"],
    ], widths=[CONTENT_W * 0.5, CONTENT_W * 0.5], dark=True))
    add(Spacer(1, 2 * mm))
    add(para("Логика простая: в конце месяца маркетинг закрывает отчёты, в первый день "
             "акции все на площадке, в пятницу вечером никто не хочет новых тем.",
             "muted", True))
    add(PageBreak())

    # ══════════════════════════════════ 08 CRM ══════════════════════════════
    add(SectionHead("08", "CRM", "Что заполнять, чтобы сделка не потерялась", dark=True))
    add(Spacer(1, 4 * mm))
    add(table([
        ["Группа полей", "Поля"],
        ["Аккаунт", "группа / юридическое название · дилерский центр и адрес · "
                    "автомобильные бренды · сегмент A/B/C/D · account_id"],
        ["Контакты", "официальный сайт и телефон · имя, должность, рабочий телефон "
                     "и почта · источник контакта"],
        ["Задача", "предполагаемый повод · открытая задача · дата запуска · "
                   "полученные материалы · ориентировочный бюджет, если назван"],
        ["Движение", "дата последнего и следующего контакта · разрешение на отправку · "
                     "стадия воронки · причина отказа · следующий сезонный повод"],
    ], widths=[32 * mm, CONTENT_W - 32 * mm], dark=True))
    add(Spacer(1, 6 * mm))
    add(para("Правило одного аккаунта", "h2", True))
    add(para(f"В базе {N_SITES} площадок, но {N_ACCOUNTS} аккаунтов. У AVILON, АВТОМИР, "
             "Major, РОЛЬФ и АвтоСпецЦентра несколько адресов — это <b>одна сделка</b>, "
             "площадки внутри неё. Второй звонок по другому адресу той же группы "
             "воспринимается как навязчивость: маркетинг там общий.", "body", True))
    add(Spacer(1, 5 * mm))
    add(para("Минимальная запись после звонка", "h2", True))
    add(table([
        ["Поле", "Обязательно"],
        ["Компания (группа, не площадка)", "да"],
        ["account_id из базы", "да"],
        ["Контакт: имя, должность, канал", "да"],
        ["Стадия: дозвонились / есть задача / запрошены материалы / отправлено / "
         "расчёт / отказ с датой возврата", "да"],
        ["Следующее действие: дата и что именно сделать", "да"],
        ["Заметка дословными цитатами, не пересказом", "да"],
    ], widths=[CONTENT_W - 24 * mm, 24 * mm], dark=True))
    add(Spacer(1, 4 * mm))
    add(Panel("Если в карточке меньше четырёх полей — звонка не было. Был разговор "
              "о вежливости.", dark=True, bar=D_ACID, fs=9.2))
    add(Spacer(1, 8 * mm))
    add(para("Из чего считается воронка", "h2", True))
    add(Spacer(1, 2 * mm))
    add(table([
        ["Переход", "Как считается", "Где брать данные"],
        ["Дозвон до ответственного", "есть имя и должность в карточке", "поле «кто ответил»"],
        ["Согласие на материалы", "человек разрешил отправить письмо", "стадия воронки 3"],
        ["Содержательный разговор", "названа задача или месяц возврата", "цитата клиента"],
        ["Вводные получены", "есть фото, размеры или дата", "поле «зона» и «дата»"],
        ["Расчёт отправлен", "состав и цифра ушли в срок", "поле «договорённость»"],
    ], widths=[52 * mm, CONTENT_W - 52 * mm - 60 * mm, 60 * mm], dark=True, fs=8.4))
    add(PageBreak())

    # ══════════════════════════════════ 09 KPI ══════════════════════════════
    add(SectionHead("09", "Пилот на 30 аккаунтов", "Нормативы, а не гарантии", dark=True))
    add(Spacer(1, 4 * mm))
    add(para("Состав базы пилота", "h2", True))
    add(table([
        ["Тип", "Сколько", "Что это даёт"],
        ["Крупные группы и многоцентровые компании", "10",
         "Потенциал тиража и повторных задач"],
        ["Активные отдельные центры", "10", "Быстрые сделки и материал для кейсов"],
        ["Центры автомобилей с пробегом", "5", "Навигация, зоны оценки и выдачи"],
        ["Event- и BTL-агентства с автоклиентами", "5", "White label и срочные задачи"],
    ], widths=[72 * mm, 20 * mm, CONTENT_W - 92 * mm], dark=True))
    add(Spacer(1, 6 * mm))
    add(para("Ориентир по воронке", "h2", True))
    add(table([
        ["Этап", "Цель на 30 аккаунтов"],
        ["Найден ответственный", "20–24"],
        ["Получено согласие отправить материалы", "12–18"],
        ["Содержательные повторные разговоры", "7–10"],
        ["Получены вводные (фото, размеры, дата)", "4–7"],
        ["Подготовлены расчёты", "3–5"],
        ["Тестовые заказы", "1–2"],
    ], widths=[CONTENT_W - 40 * mm, 40 * mm], dark=True))
    add(Spacer(1, 5 * mm))
    add(Panel("Главный показатель — не открытие письма и не количество звонков, а "
              "полученные вводные, сделанный расчёт и согласованный следующий шаг. "
              "После двух недель сравнить конверсию трёх офферов и оставить сильнейший.",
              dark=True, bar=D_ACCENT))
    add(Spacer(1, 4 * mm))
    add(para("Дневная норма на три звонка: 2 дозвона до ответственного · 3 заполненные "
             "карточки из 3 · 1 согласие на материалы · 1 фото или дата (иногда ноль) · "
             "1–2 правки в скрипт по итогам.", "muted", True))
    add(Spacer(1, 8 * mm))
    add(para("Три цифры, которые решают судьбу пилота", "h2", True))
    add(Spacer(1, 2 * mm))
    add(table([
        ["Цифра", "Как считать", "Что означает на выходе"],
        ["Дозвон → согласие", "согласия ÷ дозвоны", "ниже 50 % — проблема в первой фразе"],
        ["Согласие → вводные", "вводные ÷ согласия", "ниже 30 % — письмо не доходит до нужного человека"],
        ["Вводные → расчёт", "расчёты ÷ вводные", "ниже 60 % — расчёт выходит дольше обещанного дня"],
    ], widths=[46 * mm, 40 * mm, CONTENT_W - 86 * mm], dark=True, fs=8.6))
    add(Spacer(1, 5 * mm))
    add(para("Пилот удался, если к 30-му дню есть хотя бы один тестовый заказ, понятная "
             "цена входа и повторяемый скрипт — не 30 разговоров, а 30 ответов на вопрос "
             "«что дальше».", "muted", True))
    add(PageBreak())

    # ══════════════════════════════════ 10 ПЛАН ═════════════════════════════
    add(SectionHead("10", "План на четыре недели", "Что происходит каждую неделю", dark=True))
    add(Spacer(1, 4 * mm))
    add(table([
        ["Неделя", "Задачи", "Результат к концу недели"],
        ["1", "Опубликовать посадочную страницу · проверить презентацию и контакты · "
              "подготовить CRM · собрать первые 30 аккаунтов · написать персонализации "
              "для первой десятки",
         "Есть страница, база и первая десятка с готовыми персональными строками"],
        ["2", "3–5 новых контактов в день · фиксировать все возражения · подготовить "
              "первые экспресс-аудиты · проверить скорость ответа менеджера",
         "Первые 10–15 контактов и список реальных возражений"],
        ["3", "Продолжить первичные контакты · провести повторные звонки · выделить "
              "сценарий с лучшим откликом · сделать один отраслевой пост или чек-лист",
         "Понятно, какой из трёх офферов даёт разговор, а не вежливость"],
        ["4", "Завершить пилотную волну · посчитать конверсии · разобрать причины "
              "отказов · скорректировать презентацию и первое письмо · подготовить "
              "вторую волну 30–50 аккаунтов",
         "Цифры по воронке и решение: масштабировать или менять оффер"],
    ], widths=[18 * mm, CONTENT_W - 18 * mm - 62 * mm, 62 * mm], dark=True))
    add(Spacer(1, 6 * mm))
    add(para("Как понять, что пора масштабировать", "h2", True))
    story.extend(bullets([
        "есть хотя бы один тестовый заказ и понятная экономика проекта;",
        "менеджеры успевают отвечать в тот же день;",
        "расчёты выходят в обещанный рабочий день;",
        "возражения повторяются и уже есть готовые ответы;",
        "база второй волны собрана заранее — иначе после первой недели наступит пауза.",
    ], True))
    add(Spacer(1, 5 * mm))
    add(Panel("Не масштабировать, если проблема в первом экране страницы, скорости "
              "ответа или качестве расчёта. Больше звонков не лечат эти дыры — они "
              "делают их заметнее.", dark=True, bar=D_ACID, fs=9.2))
    add(Spacer(1, 8 * mm))
    add(para("Если неделя провалена", "h2", True))
    add(Spacer(1, 2 * mm))
    add(para("Провал — это не мало звонков, а отсутствие данных. Три звонка, после "
             "которых нельзя заполнить карточку, стоят дешевле одного разговора с "
             "записанной задачей, датой и именем.", "body", True))
    add(Spacer(1, 4 * mm))
    add(table([
        ["Что случилось", "Что делать на следующей неделе"],
        ["Меньше 10 дозвонов за неделю", "Сузить базу до 10 аккаунтов и звонить в 10–12 и 15–17"],
        ["Дозвоны есть, согласий нет", "Переписать первую фразу: в ней должен быть повод и вопрос"],
        ["Согласия есть, расчётов нет", "Спрашивать дату и зону прямо на звонке, не в письме"],
        ["Расчёты есть, ответов нет", "Звонить по расчёту через 2 дня, а не ждать ответа на письмо"],
    ], widths=[CONTENT_W * 0.36, CONTENT_W * 0.64], dark=True, fs=8.6))
    add(PageBreak())

    # ══════════════════════════════════ 11 БАЗА 1 ═══════════════════════════
    add(SectionHead("11", "База: 15 площадок", "Волна A — восемь аккаунтов первой очереди",
                    dark=True))
    add(Spacer(1, 4 * mm))
    add(para("Все адреса — внутри МКАД. Волна A — первая очередь, B — вторая. "
             "Номер — коммерческая приоритизация SM Production, а не рейтинг дилеров.",
             "muted", True))
    add(Spacer(1, 3 * mm))
    wave_a = [r for r in PROSPECTS if r["wave"] == "A"]
    rows = [["№", "Группа / площадка", "Адрес", "Телефон"]]
    for r in wave_a:
        rows.append([r["rank"], f"<b>{r['group']}</b><br/>{r['location']}",
                     r["address"].replace("Москва, ", ""), r["public_phone"]])
    add(table(rows, widths=[8 * mm, 46 * mm, CONTENT_W - 8 * mm - 46 * mm - 34 * mm, 34 * mm],
              dark=True))
    add(Spacer(1, 5 * mm))
    add(para("Почему эти — первыми", "h2", True))
    add(para("AVILON — премиальная мультибрендовая среда и высокие требования к "
             "исполнению. БорисХоф — много брендов и форматов в нескольких строениях "
             "одного адреса. АВТОМИР Крылатское — самая насыщенная по брендам городская "
             "площадка. Major Строгино — премиальные, китайские и EV-бренды. "
             "РОЛЬФ Центр — большой мультибрендовый центр с прямой функцией "
             "«написать директору».", "body", True))
    add(Spacer(1, 4 * mm))
    add(Panel("Телефоны публичные, но могли измениться: перед звонком открыть сайт "
              "центра и сверить номер. Это 20 секунд, которые экономят звонок.",
              dark=True, bar=D_ACCENT, fs=9))
    add(PageBreak())

    # ══════════════════════════════════ 11 БАЗА 2 ═══════════════════════════
    add(SectionHead("11", "База: волна B", "Вторая очередь и правило одного аккаунта",
                    dark=True))
    add(Spacer(1, 4 * mm))
    wave_b = [r for r in PROSPECTS if r["wave"] == "B"]
    rows = [["№", "Группа / площадка", "Адрес", "Телефон"]]
    for r in wave_b:
        rows.append([r["rank"], f"<b>{r['group']}</b><br/>{r['location']}",
                     r["address"].replace("Москва, ", ""), r["public_phone"]])
    add(table(rows, widths=[8 * mm, 46 * mm, CONTENT_W - 8 * mm - 46 * mm - 34 * mm, 34 * mm],
              dark=True))
    add(Spacer(1, 6 * mm))
    add(para(f"{N_ACCOUNTS} аккаунтов: где нельзя звонить дважды", "h2", True))
    add(table([
        ["Аккаунт", "Площадки в базе", "Как обращаться"],
        ["AVILON", "Волгоградский", "Один звонок в группу, затем ответственный за кластер"],
        ["БорисХоф", "Сити / Центр", "Один звонок в маркетинг группы, пилот на Магистральной"],
        ["АВТОМИР", "Крылатское + Дмитровка", "Один контакт с управлением маркетинга"],
        ["Major", "Строгино + Тушино", "Один контакт с центральным маркетингом"],
        ["РОЛЬФ", "Центр + Сити", "Начать с РОЛЬФ Центр, Сити — второй объект тиража"],
        ["АвтоСпецЦентр", "Каширка + Дубровка", "Один звонок на общий номер"],
        ["Others (5)", "по одной", "Один аккаунт — один контакт"],
    ], widths=[36 * mm, 40 * mm, CONTENT_W - 76 * mm], dark=True))
    add(Spacer(1, 4 * mm))
    add(Panel("Правило: один account_id — одна сделка. Площадки живут внутри неё. "
              "Второй звонок по соседнему адресу той же группы — минус к репутации, "
              "а не плюс к охвату.", dark=True, bar=D_ACID, fs=9.2))
    add(PageBreak())

    # ══════════════════════════════════ 12 КОНТАКТЫ ═════════════════════════
    add(SectionHead("12", "Публичные контакты", "Кого называть по имени и как", dark=True))
    add(Spacer(1, 4 * mm))
    priority = [r for r in CONTACTS if r["contact_type"] in
                ("Первичный профильный контакт", "Локальный руководитель",
                 "Локальный операционный контакт", "Маршрутизация на площадке",
                 "Локальная маршрутизация")][:10]
    add(para(f"В таблице — {len(priority)} записей из {N_STAFF}: те, где на сайте "
             "опубликованы имя и должность. Только рабочие каналы: персональные "
             "адреса не угадывались, частные телефоны не собирались.",
             "muted", True))
    add(Spacer(1, 3 * mm))
    rows = [["Группа", "Сотрудник", "Опубликованная роль", "Канал"]]
    for r in priority:
        rows.append([r["group"], f"<b>{r['person']}</b>",
                     f"{r['role']}<br/><font size=6.6>{r['scope']}</font>",
                     r["public_phone"]])
    add(table(rows, widths=[29 * mm, 31 * mm, CONTENT_W - 29 * mm - 31 * mm - 33 * mm, 33 * mm],
              dark=True, fs=7.6))
    add(Spacer(1, 5 * mm))
    add(para("Четыре правила обращения по имени", "h2", True))
    story.extend(bullets([
        "Имя — для входа, а не для давления: «соедините с …» звучит профессиональнее, "
        "чем «с кем можно обсудить сотрудничество».",
        "Не утверждать, что человек отвечает за закупку, если этого нет на его странице.",
        "PR- и коммуникационные сотрудники — только маршрут, не бюджет.",
        "Любое имя проверять на официальном сайте перед звонком: люди меняются.",
    ], True))
    add(Spacer(1, 3 * mm))
    add(para("Полные таблицы — в файлах prospects-moscow-inside-mkad.csv и "
             "public-employee-contacts.csv: там указаны источник по каждому контакту "
             "и дата проверки (6 ноября 2026).", "muted", True))
    add(PageBreak())

    # ══════════════════════════════════ 13 ПРАВИЛА ══════════════════════════
    add(SectionHead("13", "Правила качества", "Что нельзя делать ни при каких KPI", dark=True))
    add(Spacer(1, 4 * mm))
    add(table([
        ["Нельзя", "Почему"],
        ["Массовая безличная рассылка", "Это не outbound, а спам; хуже конверсия и риск блокировок"],
        ["Использовать непубличные контакты", "Персональные данные и приватность"],
        ["Писать повторно после прямого отказа", "Один лишний контакт закрывает всю группу"],
        ["Выдумывать кейсы, клиентов, показатели", "Проверяется в два клика и стоит репутации"],
        ["Выдавать концепт-визуализации за фото объекта", "Подписывать: это концепция"],
        ["Обещать сроки до проверки загрузки производства", "Сорванный срок дороже потерянной сделки"],
        ["Контакт без повода и следующего шага", "«Просто напомнить» — не повод"],
    ], widths=[CONTENT_W * 0.4, CONTENT_W * 0.6], dark=True))
    add(Spacer(1, 6 * mm))
    add(para("Юридическая оговорка", "h2", True))
    add(para("Перед масштабированием рассылки проверить механику с юристом на "
             "соответствие закону о рекламе и требованиям к обработке персональных "
             "данных. Холодный звонок на опубликованный рабочий номер — это одно; "
             "автоматическая рассылка по базе — другое.", "body", True))
    add(Spacer(1, 5 * mm))
    add(Panel("Проверка перед каждым контактом: есть ли конкретный повод, есть ли "
              "следующий шаг, не обещаю ли я того, что не подтвердило производство.",
              dark=True, bar=D_ACID, fs=9.2))
    add(Spacer(1, 8 * mm))
    add(para("Красные флаги в переписке", "h2", True))
    add(Spacer(1, 2 * mm))
    add(para("Письмо лучше не отправлять, если сработал хотя бы один пункт.",
             "muted", True))
    add(Spacer(1, 3 * mm))
    add(table([
        ["Флаг", "Что с ним делать"],
        ["Нет имени получателя и названия центра", "Письмо в общий ящик — удалить, найти человека"],
        ["Нет одного конкретного повода", "Вернуться к базе: акция, модель, ремонт"],
        ["Обещана цена или срок без вводных", "Заменить на «расчёт за рабочий день после фото»"],
        ["Вложение тяжелее 5 МБ", "Ссылка на PDF + два скриншота в теле письма"],
        ["Нет даты следующего шага", "Поставить дату и канал в CRM до отправки"],
    ], widths=[CONTENT_W * 0.42, CONTENT_W * 0.58], dark=True, fs=8.4))
    add(PageBreak())

    # ══════════════════════════════════ 14 НАВИГАЦИЯ ════════════════════════
    add(SectionHead("14", "Где что лежит", "Файлы, из которых собран этот документ",
                    dark=True))
    add(Spacer(1, 4 * mm))
    add(table([
        ["Файл", "Что внутри"],
        ["acquisition-strategy.md", "Сегментация, офферы, воронка, пилот, KPI, план на 4 недели"],
        ["outreach-templates.md", "Письма, темы, follow-up, персонализация, ответы на возражения"],
        ["manager-kit/manager-guide.md", "Памятка менеджера: продукты, квалификация, "
                                         "передача в производство, CRM, чек-лист"],
        ["first-call/*.md", "Пакет первого звонка: три звонка, сценарий по гейтам, "
                            "разбор с командой, письмо после"],
        ["prospects-moscow-inside-mkad.csv", f"{N_SITES} площадок, {N_ACCOUNTS} аккаунтов, "
                                             "для импорта в CRM"],
        ["public-employee-contacts.csv", f"{N_STAFF} публичных контактов с источниками"],
        ["SM-Production-dealership-prospects-Moscow-2026.pdf", "38-страничный отчёт по базе "
                                                               "с карточками площадок"],
        ["first-call/first-call-shpargalka.pdf", "7 страниц шпаргалки — печатная версия "
                                                 "части II"],
        ["manager-kit/SM-Production-dealership-manager-playbook.pdf", "Памятка менеджера в PDF"],
        ["presentations/dealerships-2026/…-proposal-2026.pdf", "Презентация для клиента"],
        ["website/content/services/oformlenie-avtosalonov/", "Контент страницы "
                                                             "/uslugi/oformlenie-avtosalonov"],
    ], widths=[62 * mm, CONTENT_W - 62 * mm], dark=True, fs=7.6))
    add(Spacer(1, 6 * mm))
    add(para("Что обновлять в этом документе", "h2", True))
    add(para("База площадок и контакты читаются из CSV — после правки таблиц документ "
             "пересобирается одной командой. Стратегию и нормативы нужно править "
             "вручную, когда меняется оффер или экономика.", "body", True))
    add(Spacer(1, 3 * mm))
    add(para("Сборка: .venv/bin/python marketing/dealerships-2026/build_master_pdf.py",
             "muted", True))

    # ══════════════════════════════════ ЧАСТЬ II ═════════════════════════════
    add(NextPageTemplate("print"))
    add(PageBreak())

    # ── П1: титул печатной части
    add(Spacer(1, 34 * mm))
    add(Badge("ПЕЧАТЬ", dark=False))
    add(Spacer(1, 8 * mm))
    add(Paragraph("Часть II.<br/>Одиннадцать листов для печати",
                  sty("pt", fontName="MB", fontSize=24, leading=30, textColor=P_INK)))
    add(Spacer(1, 7 * mm))
    add(para("Эти страницы сделаны так, чтобы их было не жалко исписать и удобно "
             "держать в руках: белый фон, крупный текст, поля для записи, чекбоксы, "
             "которые видно после чёрно-белой печати.", dark=False, kind="lead"))
    add(Spacer(1, 6 * mm))
    add(para("Внутри — скрипт по трём гейтам, шесть возражений с ответами, карточка "
             "звонка, чек-лист дня, оценочный лист и план на неделю. Всё остальное — "
             "стратегия, база и нормативы — в экранной части: на бумаге это не нужно.",
             dark=False, kind="lead"))
    add(Spacer(1, 8 * mm))
    add(Panel("Зачем печатать вообще: на звонке человек не смотрит в экран. Скрипт "
              "должен лежать перед глазами, карточка — быть под рукой, а возражения — "
              "на одном листе, а не в трёх файлах.", dark=False, bar=P_INK, fs=9.4))
    add(Spacer(1, 8 * mm))
    add(para("Порядок работы с листами", "h3", False))
    add(Spacer(1, 2 * mm))
    add(table([
        ["Когда", "Что под рукой", "Лист"],
        ["Перед первым звонком дня", "Скрипт ресепшн → ответственный", "П3, П4"],
        ["Во время разговора", "Выход из отказа и фразы-убийцы", "П5"],
        ["Как только положил трубку", "Карточка звонка: 11 полей, 5 минут", "П7, П8"],
        ["Если сопротивляются", "Шесть возражений со схемой ответа", "П6"],
        ["В конце дня", "Чек-лист и норма дня", "П9"],
        ["В пятницу", "Разбор звонков и план на неделю", "П10, П11"],
    ], widths=[56 * mm, CONTENT_W - 56 * mm - 30 * mm, 30 * mm], dark=False, fs=8.4))
    add(PageBreak())

    # ── П2: как печатать
    add(print_head("П2", "Как печатать", "Одиннадцать листов: что и в каком количестве"))
    add(Spacer(1, 4 * mm))
    add(table([
        ["Лист", "Что это", "Сколько печатать"],
        ["П1", "Титул печатной части", "1"],
        ["П2", "Этот лист: список и правила печати", "1"],
        ["П3", "Шпаргалка: ресепшн — как пройти первый гейт", "1"],
        ["П4", "Шпаргалка: ответственный — вопрос, уточнение, шаг", "1"],
        ["П5", "Шпаргалка: выход, отказы, фразы-убийцы", "1"],
        ["П6", "Возражения — шесть сценариев с ответами", "1"],
        ["П7", "Карточка звонка — первый разговор дня", "10–15 копий"],
        ["П8", "Карточка звонка — второй разговор дня", "10–15 копий"],
        ["П9", "Чек-лист дня и дневная норма", "1"],
        ["П10", "Оценочный лист звонка — 12 критериев", "по числу слушателей"],
        ["П11", "План звонков на неделю — 15 строк", "1"],
    ], widths=[16 * mm, CONTENT_W - 16 * mm - 40 * mm, 40 * mm], dark=False, fs=8.2))
    add(Spacer(1, 6 * mm))
    add(para("Правила печати", "h3", False))
    add(Spacer(1, 1 * mm))
    story.extend([CheckItem(t, dark=False) for t in [
        "А4, масштаб 100 % — не «по размеру страницы», иначе строки форм разъедутся",
        "Чёрно-белая печать подходит: цвет в печатной части ничего не кодирует",
        "Односторонняя печать: на обороте удобно писать заметки по звонку",
        "Карточки П7 и П8 печатать пачкой на неделю вперёд, а не по одной",
        "Шпаргалки П3–П5 держать в прозрачном файле рядом с телефоном",
        "Оценочный лист П10 — по числу людей на разборе плюс один запасной",
    ]])
    add(Spacer(1, 6 * mm))
    add(Panel("Экранную часть (Э1–Э17) печатать не нужно: тёмный фон съест картридж, "
              "а мелкая графика станет серой кашей.", dark=False, bar=P_INK, fs=9))
    add(PageBreak())

    # ══════════════════════════════════ П2 РЕСЕПШН ══════════════════════════
    add(print_head("П3", "Гейт 1. Ресепшн", "30–60 секунд. Цель — имя и должность, "
                                            "больше ничего"))
    add(Spacer(1, 4 * mm))
    add(print_script(
        "Добрый день! Подскажите, пожалуйста, кто у вас отвечает за оформление салона — "
        "сезонные материалы, презентации моделей?"))
    add(Spacer(1, 3 * mm))
    add(para("Почему так: вопрос про «оформление салона» понятен любому администратору. "
             "«Кто отвечает за маркетинг» — тоже работает, но чаще приводит к общему "
             "отделу. «С кем можно обсудить сотрудничество» — почти гарантированный "
             "отказ: звучит как продажа.", dark=False, kind="muted"))
    add(Spacer(1, 6 * mm))
    add(print_pair("«А что вы предлагаете?»",
                   "Мы московское производство: печатаем сезонные материалы, делаем "
                   "навигацию, оформление ресепшн и зон выдачи, конструкции для "
                   "запусков моделей. Хочу коротко понять, есть ли у вас такая задача, "
                   "и если да — отправить материалы тому, кто её ведёт."))
    add(print_pair("«Пришлите на почту»",
                   "Обязательно пришлю. Подскажите, на чьё имя адресовать, чтобы "
                   "письмо попало к нужному человеку, а не в общую папку?"))
    add(print_pair("«Соединяю» — но неясно с кем",
                   "Спасибо! Уточню, как вас зовут и как правильно представить — "
                   "чтобы не звонить вслепую."))
    add(print_pair("Не соединяют",
                   "Подскажите, пожалуйста, имя и должность человека, который "
                   "принимает решение по оформлению. Я напишу письмо и сошлюсь на вас."))
    add(Spacer(1, 6 * mm))
    add(Panel("«Хорошо, пришлю» — и звонок закончен: письмо уйдёт в info@ и умрёт. "
              "Просим имя и пишем сами.", dark=False, bar=P_INK, fs=9))
    add(PageBreak())

    # ══════════════════════════════════ П3 ОТВЕТСТВЕННЫЙ ════════════════════
    add(print_head("П4", "Гейт 2. Ответственный", "2–3 минуты. Порядок важен: "
                                                   "сначала вопрос, потом рассказ"))
    add(Spacer(1, 4 * mm))
    add(para("Шаг 1. Кто вы и почему сейчас — 20 секунд", "h3", False))
    add(print_script("[Имя], добрый день! Меня зовут [ваше имя], SM Production. Мы "
                     "производим оформление для дилерских центров: сезонные материалы, "
                     "навигацию, зоны выдачи, конструкции под запуск модели. "
                     "Производство своё, в Москве. Звоню не с предложением что-то "
                     "купить — хочу понять, есть ли у вас задача на ближайшие два-три "
                     "месяца, и если есть, предложить один конкретный следующий шаг."))
    add(Spacer(1, 4 * mm))
    add(para("Шаг 2. Вопрос — 30 секунд, дальше молчать и записывать", "h3", False))
    add(print_script("Что у вас сейчас вероятнее: сезонное обновление, запуск модели "
                     "или переделка зон — ресепшн, выдача?"))
    add(Spacer(1, 2 * mm))
    add(para("Если «ничего»: «Понял. А в каком месяце у вас обычно начинается "
             "подготовка — чтобы я вернулся вовремя, а не наугад?»", dark=False,
             kind="body"))
    add(Spacer(1, 4 * mm))
    add(para("Шаг 3. Уточнение — по одному вопросу, не списком", "h3", False))
    add(Spacer(1, 1 * mm))
    add(print_questions(["Какая зона?", "Когда должно стоять?",
                         "Кто ещё участвует в решении?",
                         "Что было в прошлый раз — и что в нём не устроило?"]))
    add(Spacer(1, 2 * mm))
    add(para("Последний вопрос — самый ценный: там звучит, за что они готовы платить. "
             "Записывать их формулировкой: она пойдёт в письмо и в смету.", dark=False,
             kind="muted"))
    add(Spacer(1, 4 * mm))
    add(para("Шаг 4. Один следующий шаг — 30 секунд", "h3", False))
    add(print_script("Тогда предлагаю так: вы присылаете фотографии зоны и примерные "
                     "размеры, я в течение рабочего дня возвращаюсь с составом и "
                     "предварительным расчётом. Дизайн и точную смету подтвердим после "
                     "брифа. Если цифра устроит — обсуждаем монтаж."))
    add(Spacer(1, 3 * mm))
    add(para("Шаг 5. Договорённость — 20 секунд", "h3", False))
    add(print_script("Когда удобнее прислать фото — сегодня или завтра? И на какой "
                     "канал: почта, мессенджер?"))
    add(PageBreak())

    # ══════════════════════════════════ П4 ВЫХОД ════════════════════════════
    add(print_head("П5", "Гейт 3. Выход", "Даже отказ должен дать дату"))
    add(Spacer(1, 4 * mm))
    add(print_pair("«Нам это не нужно»",
                   "Понял. Тогда один вопрос, чтобы не звонить зря: в каком месяце у "
                   "вас начинается подготовка к следующему сезону? Запишу и не буду "
                   "беспокоить раньше."))
    add(print_pair("«У нас всё есть»",
                   "Это нормально, менять подрядчика никто не предлагает. Один вопрос: "
                   "что вы делаете, когда подрядчик не успевает к дате или нужна "
                   "нестандартная конструкция? Если такой ситуации не было — отлично. "
                   "Если была — можем быть вторым производством. Прислать материалы, "
                   "чтобы были под рукой?"))
    add(print_pair("Разговор уводят в сторону",
                   "Простите, я вас перебью на секунду — чтобы не тратить ваше время: "
                   "мне важно понять только одно, есть ли задача на ближайшие месяцы. "
                   "Если нет, я не буду занимать."))
    add(Spacer(1, 6 * mm))
    add(para("Фразы-убийцы — не говорить никогда", "h3", False))
    add(table([
        ["Не так", "Почему"],
        ["«Хотел бы предложить сотрудничество»", "ноль информации, мгновенный отказ"],
        ["«Мы предлагаем полный комплекс услуг»", "так говорят все, слушать нечего"],
        ["«Есть минутка?»", "даёт право сказать «нет» до объяснения"],
        ["«У нас самые низкие цены»", "неправда и сразу недоверие"],
        ["«Давайте я приеду и всё расскажу»", "встреча без повода — отказ"],
    ], widths=[CONTENT_W * 0.46, CONTENT_W * 0.54], dark=False, fs=8.4))
    add(Spacer(1, 7 * mm))
    add(para("Пять вопросов после звонка", "h3", False))
    add(para("Если не можешь ответить — звонка не было.", dark=False, kind="muted"))
    add(Spacer(1, 2 * mm))
    add(print_questions(["Как зовут человека и какова его роль?",
                         "Какая задача прозвучала его словами?",
                         "Какая дата?",
                         "Кто ещё участвует в решении?",
                         "Что я обещал прислать и когда?"]))
    add(PageBreak())

    # ══════════════════════════════════ П5 ВОЗРАЖЕНИЯ ═══════════════════════
    add(print_head("П6", "Возражения", "Шесть сценариев, которые звучат чаще всего"))
    add(Spacer(1, 3 * mm))
    objections = [
        ("У нас есть свой подрядчик",
         "Понимаю. Мы не предлагаем менять проверенного партнёра без причины. Можем "
         "остаться резервным производством для срочной задачи, нестандартной "
         "конструкции или параллельного монтажа. Можно отправить короткую презентацию, "
         "чтобы контакт был под рукой?"),
        ("Сейчас ничего не нужно",
         "Подскажите, в каком месяце обычно начинается подготовка к следующей сезонной "
         "кампании? Я зафиксирую дату и не буду писать раньше."),
        ("Пришлите прайс",
         "Для баннеров и типовых носителей можем дать базовые ставки, но комплексное "
         "оформление зависит от размеров, материалов и монтажа. Если пришлёте фото и "
         "примерный формат, расчёт будет точнее обычного прайса."),
        ("Нужен тендер",
         "Готовы рассчитать по вашему техническому заданию. Подскажите, какие документы "
         "и формат сметы нужны для допуска? Если ТЗ ещё формируется, можем помочь "
         "уточнить состав конструкций и производственные параметры."),
        ("Слишком дорого",
         "Давайте разделим смету на обязательную часть и опции. Часто можно сохранить "
         "визуальную задачу, изменив материал, конструктив или способ монтажа. Какие "
         "позиции для вас критичны?"),
        ("Нет готового макета",
         "Это не проблема. Для первого шага достаточно фотографии зоны, размеров и "
         "брендбука. Сначала предложим состав решения, а срок дизайна подтвердим после "
         "брифа."),
    ]
    for title, answer in objections:
        add(print_pair(f"«{title}»", answer, gap=5))
    add(Spacer(1, 4 * mm))
    add(para("Схема ответа на любое возражение", "h3", False))
    add(Spacer(1, 1.5 * mm))
    add(para("Согласие → уточнение → факт → следующий шаг. Без согласия любой ответ "
             "звучит как спор; без уточнения — как заготовка; без шага — разговор "
             "заканчивается ничем.", dark=False, kind="muted"))
    add(Spacer(1, 2 * mm))
    add(table([
        ["Шаг", "Что сказать", "Чего не делать"],
        ["Согласие", "«Понимаю», «логично», «так и бывает»", "Спорить и оправдываться"],
        ["Уточнение", "«А что именно смущает: срок, бюджет или согласование?»", "Отвечать на всё сразу"],
        ["Факт", "Один конкретный: срок, материал, пример работы", "Обещать цену без данных"],
        ["Шаг", "«Пришлю расчёт в среду — на этот адрес?»", "Оставлять «на связи»"],
    ], widths=[26 * mm, CONTENT_W - 26 * mm - 58 * mm, 58 * mm], dark=False, fs=8.2))
    add(PageBreak())

    # ══════════════════════════════════ П6 КАРТОЧКИ ═════════════════════════
    add(print_head("П7", "Карточка звонка",
                   "Две карточки на лист: один разговор — одна карточка, пять минут"))
    add(Spacer(1, 4 * mm))
    for n in (1, 2):
        story.extend(call_card(dark=False, row_h=9.6, caption=f"Карточка {n} · первый разговор"))
        if n == 1:
            add(Spacer(1, 7 * mm))
    add(PageBreak())

    add(print_head("П8", "Карточка звонка",
                   "Второй разговор дня. Если карточек не хватило — печатайте ещё один лист"))
    add(Spacer(1, 4 * mm))
    for n in (3, 4):
        story.extend(call_card(dark=False, row_h=9.6, caption=f"Карточка {n} · второй разговор"))
        if n == 3:
            add(Spacer(1, 7 * mm))
    add(PageBreak())

    # ══════════════════════════════════ П7 ЧЕК-ЛИСТ ═════════════════════════
    add(print_head("П9", "Чек-лист дня", "Что сделать до, во время и после"))
    add(Spacer(1, 4 * mm))
    add(para("До первого звонка", "h3", False))
    add(Spacer(1, 1 * mm))
    story.extend([CheckItem(t, dark=False) for t in [
        "Посмотреть задачи и follow-up на сегодня",
        "Проверить готовность презентации и рабочей ссылки",
        "Выбрать 3–5 новых аккаунтов из базы",
        "По каждому: сайт, акции, бренды, один повод — выписать персональную строку",
        "Открыть карточки CRM и распечатать карточки звонков",
    ]])
    add(Spacer(1, 5 * mm))
    add(para("После каждого контакта", "h3", False))
    add(Spacer(1, 1 * mm))
    story.extend([CheckItem(t, dark=False) for t in [
        "Записать результат в CRM",
        "Указать следующий шаг и дату",
        "Сохранить разрешение на отправку",
        "Зафиксировать открытый сценарий: сезон / модель / пространство",
        "Добавить причину отказа, если она названа",
        "Отправить письмо в течение 30 минут",
    ]])
    add(Spacer(1, 5 * mm))
    add(para("В конце дня", "h3", False))
    add(Spacer(1, 1 * mm))
    story.extend([CheckItem(t, dark=False) for t in [
        "Все обещанные письма отправлены",
        "Полученные вводные переданы в расчёт",
        "Список звонков на завтра готов",
        "Отмечены повторяющиеся возражения",
    ]])
    add(Spacer(1, 7 * mm))
    add(para("Норма одного дня на три звонка", "h3", False))
    add(Spacer(1, 1 * mm))
    add(table([
        ["Показатель", "Норма"],
        ["Дозвон до ответственного", "2 из 3"],
        ["Заполненных карточек", "3 из 3"],
        ["Согласие на материалы", "1 из 3"],
        ["Фото зоны или дата", "1 из 3, иногда ноль"],
        ["Правок в скрипт по итогам", "1–2 в неделю"],
        ["Сделка", "ноль — и это нормально"],
    ], widths=[CONTENT_W - 40 * mm, 40 * mm], dark=False, fs=8.6))
    add(Spacer(1, 6 * mm))
    add(para("Если норма не выполняется три дня подряд", "h3", False))
    add(Spacer(1, 1.5 * mm))
    story.extend([CheckItem(t, dark=False) for t in [
        "Дозвонов меньше 2 из 3 — проверить часы звонков и базу номеров, а не скрипт",
        "Карточек меньше 3 из 3 — упростить карточку до пяти полей на время",
        "Согласий нет совсем — переписать первую фразу, а не увеличивать количество",
        "Фото и дат нет — на звонке не прозвучал один конкретный повод",
    ]])
    add(Spacer(1, 4 * mm))
    add(Panel("Правило разбора: смотреть не на количество звонков, а на то, где "
              "обрывается цепочка. Три звонка с плохим скриптом не лечат цифры — "
              "они их портят.", dark=False, bar=P_INK, fs=9))
    add(PageBreak())

    # ══════════════════════════════════ П8 ОЦЕНКА ═══════════════════════════
    add(print_head("П10", "Оценочный лист", "12 критериев, 0–2 балла. Максимум 24, "
                                           "проходной 16"))
    add(Spacer(1, 3 * mm))
    add(form([("Дата", ""), ("Кто звонил", ""), ("Центр", "")],
             [26 * mm, CONTENT_W - 26 * mm], dark=False, row_h=18))
    add(Spacer(1, 5 * mm))
    criteria = [
        "Назвал себя и компанию в первые 10 секунд",
        "Сказал, что производит, а не «предлагает услуги»",
        "Задал вопрос о задаче раньше, чем рассказал о себе",
        "Выслушал до конца, не перебил",
        "Уточнил зону",
        "Уточнил дату",
        "Уточнил, кто участвует в решении",
        "Предложил один конкретный следующий шаг",
        "Договорился о дате и канале",
        "Не обещал цену и срок без данных",
        "Записал формулировки клиента дословно",
        "Отправил письмо в течение 30 минут",
    ]
    rows = [["№", "Критерий", "0", "1", "2"]]
    for i, c in enumerate(criteria, 1):
        rows.append([str(i), c, "", "", ""])
    t = Table(rows, colWidths=[10 * mm, CONTENT_W - 10 * mm - 36 * mm, 12 * mm, 12 * mm, 12 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), P_INK),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONT", (0, 0), (-1, 0), "MS", 7.6),
        ("FONT", (0, 1), (-1, -1), "M", 8.4),
        ("TEXTCOLOR", (0, 1), (-1, -1), P_INK),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("ALIGN", (2, 0), (-1, -1), "CENTER"),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, P_RULE),
        ("BOX", (2, 1), (4, -1), 0.5, P_RULE),
        ("INNERGRID", (2, 1), (4, -1), 0.4, P_RULE),
    ]))
    add(t)
    add(Spacer(1, 6 * mm))
    add(table([
        ["Итого", "Что делать"],
        ["16–24", "Можно звонить по базе самостоятельно"],
        ["10–15", "Ещё три раза в ролевой игре, потом на живых"],
        ["меньше 10", "Проблема в структуре, а не в человеке: вернуться к гейтам"],
    ], widths=[24 * mm, CONTENT_W - 24 * mm], dark=False, fs=8.6))
    add(PageBreak())

    # ══════════════════════════════════ П9 НЕДЕЛЯ ═══════════════════════════
    add(print_head("П11", "План звонков на неделю", "Три звонка в день, пять дней"))
    add(Spacer(1, 3 * mm))
    add(para("Заполнять заранее: центр, номер, повод, кто отвечает. После звонка — "
             "результат и следующий шаг. Пятница — день разбора, а не новых звонков.",
             dark=False, kind="muted"))
    add(Spacer(1, 4 * mm))
    rows = [["День", "Центр и телефон", "Повод", "Результат", "Следующий шаг"]]
    days = ["Пн", "Вт", "Ср", "Чт", "Пт"]
    for d in days:
        for _ in range(3):
            rows.append([d, "", "", "", ""])
    t = Table(rows, colWidths=[12 * mm, 52 * mm, 40 * mm, 38 * mm, CONTENT_W - 142 * mm],
              rowHeights=[8 * mm] + [11.2 * mm] * 15, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), P_INK),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONT", (0, 0), (-1, 0), "MS", 7.4),
        ("FONT", (0, 1), (-1, -1), "M", 7.4),
        ("TEXTCOLOR", (0, 1), (-1, -1), P_INK),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, 0), (-1, -1), 0.45, P_RULE),
        ("LINEBEFORE", (1, 0), (-1, -1), 0.45, P_RULE),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    add(t)
    add(Spacer(1, 4 * mm))
    add(para("Итоги недели", "h3", False))
    add(form([("Звонков сделано / дозвонов", ""),
              ("Согласий на материалы / фото или дат", ""),
              ("Правок в скрипт", "")],
             [66 * mm, CONTENT_W - 66 * mm], dark=False, row_h=15))

    return story


# ── печатные блоки ──────────────────────────────────────────────────────────
def print_head(number, title, subtitle):
    return KeepTogether([
        SectionHead(number, title, subtitle, dark=False),
    ])


def print_script(text):
    t = Table([[Paragraph(text, sty("sc", fontName="MM", fontSize=10.2, leading=15.6,
                                    textColor=P_INK))]],
              colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), P_TINT),
        ("LINEBEFORE", (0, 0), (0, -1), 2.4, P_INK),
        ("LEFTPADDING", (0, 0), (-1, -1), 11),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    return t


def print_pair(title, answer, gap=4):
    return KeepTogether([
        Paragraph(title, sty("pt2", fontName="MS", fontSize=9.4, leading=13,
                             textColor=P_INK, spaceBefore=gap)),
        Spacer(1, 1 * mm),
        Table([[Paragraph(answer, sty("pa", fontName="M", fontSize=9, leading=13.6,
                                      textColor=P_GREY))]],
              colWidths=[CONTENT_W],
              style=[("LEFTPADDING", (0, 0), (-1, -1), 8),
                     ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                     ("TOPPADDING", (0, 0), (-1, -1), 0),
                     ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                     ("LINEBEFORE", (0, 0), (0, -1), 1.2, P_RULE)]),
        Spacer(1, 2 * mm),
    ])


def print_questions(items):
    rows = [[Paragraph(f"<b>{i}.</b>", sty("q", fontName="M", fontSize=9, textColor=P_INK)),
             Paragraph(q, sty("q2", fontName="MM", fontSize=9.4, leading=13.4, textColor=P_INK))]
            for i, q in enumerate(items, 1)]
    t = Table(rows, colWidths=[7 * mm, CONTENT_W - 7 * mm])
    t.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return t


def call_card(dark=False, row_h=8.0, caption=""):
    fields = [
        ("Дата и время", ""),
        ("Центр и account_id", ""),
        ("Кто ответил: имя, должность", ""),
        ("Как прошёл ресепшн", "соединили / дали имя / отправили на почту / отказ"),
        ("Задача словами клиента", "дословно, в кавычках"),
        ("Зона", "ресепшн / выдача / вход / сервис / витрина"),
        ("Дата", "месяц или день"),
        ("Кто участвует в решении", ""),
        ("Что было в прошлый раз", ""),
        ("Договорённость", "что прислать, когда, по какому каналу"),
        ("Следующий шаг", "дата и действие"),
    ]
    data = []
    for label_text, hint in fields:
        right = Paragraph(f"<font color='#B4B4AE'>{hint}</font>" if hint else "&nbsp;",
                          sty("hintc", fontName="M", fontSize=7.2, textColor=P_GREY))
        data.append([Paragraph(label_text, sty("fl", fontName="M", fontSize=7.6,
                                               leading=10.4, textColor=P_GREY)), right])
    t = Table(data, colWidths=[52 * mm, CONTENT_W - 52 * mm],
              rowHeights=[row_h * mm] * len(fields))
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (1, 0), (1, -1), 6),
        ("LINEBELOW", (1, 0), (1, -1), 0.5, P_RULE),
    ]))
    if not caption:
        return t
    cap = Table([[Paragraph(caption, sty("cap", fontName="MB", fontSize=7.4,
                                         textColor=P_GREY)),
                  Paragraph("дописать сразу, пока помнишь", sty("cap2", fontName="M",
                                                                fontSize=7.2,
                                                                textColor=P_RULE))]],
                colWidths=[CONTENT_W / 2, CONTENT_W / 2])
    cap.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("LINEBELOW", (0, 0), (-1, 0), 0.4, P_RULE),
    ]))
    return [cap, Spacer(1, 2 * mm), t]


# ── сборка в два прохода ────────────────────────────────────────────────────
def make_doc(path, totals):
    doc = DealerDoc(path)
    doc.totals = totals
    frame = Frame(ML, MB, CONTENT_W, PAGE_H - MT - MB, id="f",
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates([
        PageTemplate(id="cover", frames=[frame], onPage=on_cover),
        PageTemplate(id="screen", frames=[frame], onPage=on_screen),
        PageTemplate(id="print", frames=[frame], onPage=on_print),
    ])
    doc.build(build_stream())
    return doc.counts


def main() -> None:
    probe = OUT.with_suffix(".probe.pdf")
    counts = make_doc(probe, {"screen": 0, "print": 0})
    os.remove(probe)
    make_doc(OUT, counts)
    size = OUT.stat().st_size // 1024
    print(f"  {OUT.name}: {size} КБ · экранных {counts['screen']}, печатных {counts['print']}")


if __name__ == "__main__":
    main()
