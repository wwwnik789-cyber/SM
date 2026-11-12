#!/usr/bin/env python3
"""SLAB & LIGHT — сводный PDF направления «столешницы из слебов со светом».

16 страниц: позиционирование, линейка, шесть концептов, технология, свет,
клиенты, партнёры, экономика, возражения, план на 90 дней и страница сайта.

Изображения в assets/ — концепт-визуализации. На каждой странице с картинкой
стоит подпись «концепт», чтобы их нельзя было принять за фотографии работ.

Запуск из корня репозитория:
    .venv/bin/python marketing/wood-countertops-2026/build_pdf.py
"""

from __future__ import annotations

import os
from pathlib import Path

from PIL import Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Flowable, Frame,
                                NextPageTemplate, PageBreak, PageTemplate,
                                Paragraph, Spacer, Table, TableStyle)

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ASSETS = HERE / "assets"
OUT = HERE / "SM-Production-slab-light-2026.pdf"

FONT_DIR = Path("/tmp/fonts-slab")
FONT_SRC = REPO / "banners/anikom-arena-3000x2500-concepts/source/Montserrat-Variable.ttf"
CROP_DIR = Path("/tmp/pdfcrop-slab")

# ── палитра ─────────────────────────────────────────────────────────────────
BG = colors.HexColor("#12100E")          # тёплый почти чёрный
CARD = colors.HexColor("#1D1915")
IVORY = colors.HexColor("#F4EFE6")
MUTED = colors.HexColor("#9C9287")
LINE = colors.HexColor("#302A24")
ORANGE = colors.HexColor("#FF4D1C")
AMBER = colors.HexColor("#E9A552")
WOOD = colors.HexColor("#B9814A")

PAGE_W, PAGE_H = A4
ML, MR, MT, MB = 19 * mm, 19 * mm, 16 * mm, 18 * mm
CONTENT_W = PAGE_W - ML - MR


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


def sty(name, **kw):
    base = dict(fontName="M", fontSize=9.3, leading=14.2, alignment=TA_LEFT,
                textColor=IVORY)
    base.update(kw)
    return ParagraphStyle(name, **base)


S = {
    "lead": sty("lead", fontName="MM", fontSize=11.4, leading=17.6, textColor=IVORY),
    "body": sty("body", fontSize=9.3, leading=14.4),
    "small": sty("small", fontSize=8.4, leading=12.6),
    "muted": sty("muted", fontSize=8.2, leading=12.4, textColor=MUTED),
    "h2": sty("h2", fontName="MS", fontSize=12.2, leading=15.6, spaceBefore=5, spaceAfter=2),
    "h3": sty("h3", fontName="MS", fontSize=9.9, leading=13.6, spaceBefore=3, spaceAfter=2),
    "cell": sty("cell", fontSize=8.1, leading=11.7),
    "cell_s": sty("cells", fontSize=7.5, leading=10.8),
    "head": sty("head", fontName="MS", fontSize=7.6, leading=10.8, textColor=BG),
    "quote": sty("quote", fontName="MM", fontSize=10.1, leading=15.8),
    "bullet": sty("bullet", fontSize=9.1, leading=13.9, leftIndent=9),
    "imgcap": sty("imgcap", fontSize=7.1, leading=9.6, textColor=MUTED),
}


def P(text, kind="body"):
    return Paragraph(text, S[kind])


# ── утилиты изображений ─────────────────────────────────────────────────────
def _prep_image(path: Path, ratio: float) -> Path:
    """Обрезать под нужное соотношение и уменьшить, положив результат в /tmp."""
    CROP_DIR.mkdir(parents=True, exist_ok=True)
    tag = f"{path.stem}-{ratio:.3f}.jpg"
    out = CROP_DIR / tag
    if out.exists():
        return out
    im = Image.open(path).convert("RGB")
    w, h = im.size
    target = ratio
    if w / h > target:
        new_w = int(h * target)
        left = (w - new_w) // 2
        im = im.crop((left, 0, left + new_w, h))
    else:
        new_h = int(w / target)
        top = (h - new_h) // 2
        im = im.crop((0, top, w, top + new_h))
    if im.width > 1600:
        im = im.resize((1600, int(1600 * im.height / im.width)), Image.LANCZOS)
    im.save(out, "JPEG", quality=84, optimize=True)
    return out


class Pic(Flowable):
    """Изображение с обрезкой по размеру и опциональной подписью-плашкой."""

    def __init__(self, name, width, height, radius=3, caption=None, badge=True,
                 badge_text="КОНЦЕПТ"):
        super().__init__()
        self.path = _prep_image(ASSETS / name, width / height)
        self.width, self.height = width, height
        self.radius = radius
        self.caption = caption
        self.badge = badge
        self.badge_text = badge_text

    def wrap(self, aw, ah):
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.saveState()
        p = c.beginPath()
        p.roundRect(0, 0, self.width, self.height, self.radius * mm)
        c.clipPath(p, stroke=0, fill=0)
        c.drawImage(str(self.path), 0, 0, self.width, self.height,
                    preserveAspectRatio=False, mask=None)
        # лёгкое затемнение снизу под подпись
        c.setFillAlpha(0.55)
        c.setFillColor(colors.black)
        c.rect(0, 0, self.width, 9 * mm, stroke=0, fill=1)
        c.setFillAlpha(1)
        c.setStrokeColor(LINE)
        c.setLineWidth(0.5)
        c.roundRect(0, 0, self.width, self.height, self.radius * mm, stroke=1, fill=0)
        c.restoreState()
        if self.caption:
            c.setFont("M", 7)
            c.setFillColor(colors.HexColor("#D9D2C7"))
            c.drawString(4 * mm, 3.2 * mm, self.caption)
        if self.badge:
            c.setFont("MS", 6.4)
            c.setFillColor(AMBER)
            c.drawRightString(self.width - 4 * mm, 3.2 * mm, self.badge_text)


# ── примитивы ───────────────────────────────────────────────────────────────
def hrule(color=LINE, width=0.6, space_before=3, space_after=3):
    t = Table([[""]], colWidths=[CONTENT_W], rowHeights=[0.1])
    t.setStyle(TableStyle([("LINEABOVE", (0, 0), (-1, 0), width, color),
                           ("TOPPADDING", (0, 0), (-1, -1), 0),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 0)]))
    return [Spacer(1, space_before), t, Spacer(1, space_after)]


def section_head(num, title, sub=""):
    rows = [[Paragraph(f'<font color="#FF4D1C"><b>{num}</b></font>', sty(
        "num", fontName="MB", fontSize=22, leading=24, textColor=ORANGE)),
        Paragraph(title, sty("title", fontName="MB", fontSize=19, leading=22, textColor=IVORY))]]
    t = Table(rows, colWidths=[16 * mm, CONTENT_W - 16 * mm])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    out = [t]
    if sub:
        out.append(Spacer(1, 1.6 * mm))
        out.append(Paragraph(sub, sty("sub", fontName="M", fontSize=8.8, leading=12.6,
                                      textColor=MUTED)))
    out.append(Spacer(1, 4 * mm))
    return out


def table(rows, widths, fs=8.2, head=True, zebra=True, first_col_bold=False,
          right_cols=()):
    data = []
    for i, row in enumerate(rows):
        line = []
        for j, cell in enumerate(row):
            if isinstance(cell, str):
                if i == 0 and head:
                    st = sty(f"h{fs}", fontName="MS", fontSize=fs - 0.5, leading=fs + 3,
                             textColor=BG)
                else:
                    st = sty(f"c{fs}{j}", fontSize=fs, leading=fs + 3.6, textColor=IVORY,
                             fontName="MM" if (first_col_bold and j == 0) else "M")
                line.append(Paragraph(cell, st))
            else:
                line.append(cell)
        data.append(line)
    t = Table(data, colWidths=widths, repeatRows=1 if head else 0)
    cmds = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4.2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4.2),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, LINE),
    ]
    if head:
        cmds += [("BACKGROUND", (0, 0), (-1, 0), IVORY),
                 ("TEXTCOLOR", (0, 0), (-1, 0), BG)]
    if zebra:
        for i in range(1 if head else 0, len(rows)):
            if i % 2 == (0 if head else 1):
                cmds.append(("BACKGROUND", (0, i), (-1, i), CARD))
    for col in right_cols:
        cmds.append(("ALIGN", (col, 0), (col, -1), "RIGHT"))
    t.setStyle(TableStyle(cmds))
    return t


def bullets(items, kind="bullet", color=ORANGE):
    out = []
    for it in items:
        out.append(Paragraph(it, S[kind].clone(
            f"b{id(it)}", bulletText="—",
            bulletColor=color, bulletFontName="MS", bulletFontSize=S[kind].fontSize)))
    return out


def panel(text, bar=AMBER, fs=9.4, pad=9):
    t = Table([[Paragraph(text, sty("pan", fontName="MM", fontSize=fs,
                                    leading=fs * 1.55, textColor=IVORY))]],
              colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CARD),
        ("LINEBEFORE", (0, 0), (0, -1), 2.4, bar),
        ("LEFTPADDING", (0, 0), (-1, -1), pad),
        ("RIGHTPADDING", (0, 0), (-1, -1), pad),
        ("TOPPADDING", (0, 0), (-1, -1), pad - 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), pad - 1),
    ]))
    return t


def kpi(items, width=None):
    """items: [(значение, подпись), ...]"""
    cells = []
    for value, label in items:
        cells.append(Paragraph(
            f'<font size="17" name="MB" color="#F4EFE6">{value}</font><br/>'
            f'<font size="7.4" color="#9C9287">{label}</font>',
            sty("kpi", fontSize=7.4, leading=10)))
    w = width or CONTENT_W
    t = Table([cells], colWidths=[w / len(cells)] * len(cells))
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("LINEBEFORE", (0, 0), (-1, -1), 0.5, LINE),
        ("LEFTPADDING", (0, 0), (0, -1), 6),
    ]))
    return t


def concept_block(img, title, lines, spec, img_w=None, img_h=66 * mm):
    """Картинка + описание + строка параметров в две колонки."""
    pic = Pic(img, img_w or CONTENT_W * 0.52, img_h,
              caption="Концепт-визуализация")
    text_col = [
        Paragraph(title, sty("ct", fontName="MB", fontSize=12.4, leading=15,
                             textColor=IVORY)),
        Spacer(1, 2 * mm),
    ]
    for ln in lines:
        text_col.append(Paragraph(ln, sty("cl", fontSize=8.4, leading=12.8, textColor=IVORY)))
        text_col.append(Spacer(1, 1.2 * mm))
    text_col.append(Spacer(1, 1.4 * mm))
    for label, value in spec:
        text_col.append(Paragraph(
            f'<font color="#9C9287">{label}</font>  {value}',
            sty("cs", fontSize=7.6, leading=10.6, textColor=IVORY)))
    tw = CONTENT_W - pic.width - 6 * mm
    cell = Table([[pic, text_col]], colWidths=[pic.width, tw])
    cell.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (1, 0), 6),
        ("LEFTPADDING", (0, 0), (0, 0), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return cell


# ── страницы ────────────────────────────────────────────────────────────────
def on_cover(c, doc):
    """Обложка: фото на всю ширину сверху, тёмный блок с текстом снизу."""
    hero_h = PAGE_H * 0.62
    c.saveState()
    p = c.beginPath()
    p.rect(0, PAGE_H - hero_h, PAGE_W, hero_h)
    c.clipPath(p, stroke=0, fill=0)
    c.drawImage(str(_prep_image(ASSETS / "concept-river.jpg", PAGE_W / hero_h)),
                0, PAGE_H - hero_h, PAGE_W, hero_h)
    c.restoreState()

    # градиентная «шторка»: низ фото плавно уходит в фон
    steps = 70
    fade_h = 46 * mm
    band = fade_h / steps
    c.setFillColor(BG)
    for i in range(steps):
        alpha = (1 - i / steps) ** 1.5
        c.setFillAlpha(alpha)
        c.rect(0, PAGE_H - hero_h + i * band, PAGE_W, band + 0.9, stroke=0, fill=1)
    c.setFillAlpha(1)

    c.setFillColor(BG)
    c.rect(0, 0, PAGE_W, PAGE_H - hero_h + 0.5, stroke=0, fill=1)

    c.setFillColor(AMBER)
    c.rect(ML, PAGE_H - hero_h + 26 * mm, 34 * mm, 1.4 * mm, stroke=0, fill=1)

    c.setFillColor(MUTED)
    c.setFont("MS", 7.6)
    c.drawString(ML, PAGE_H - hero_h + 21 * mm, "SM PRODUCTION · НОВОЕ НАПРАВЛЕНИЕ · 2026")

    c.setFillColor(IVORY)
    c.setFont("MB", 38)
    c.drawString(ML, PAGE_H - hero_h + 8 * mm, "SLAB & LIGHT")

    c.setFillColor(IVORY)
    c.setFont("MM", 14)
    c.drawString(ML, PAGE_H - hero_h - 3 * mm, "Столешницы из слебов со светом изнутри")

    c.setFillColor(MUTED)
    c.setFont("M", 9.2)
    c.drawString(ML, PAGE_H - hero_h - 11 * mm,
                 "Соединяем столярное и рекламное производство: дерево, смола,")
    c.drawString(ML, PAGE_H - hero_h - 16.5 * mm,
                 "фрезеровка на ЧПУ и встроенная подсветка — в одном изделии.")

    # нижняя полоса с KPI
    y = 46 * mm
    c.setStrokeColor(LINE)
    c.setLineWidth(0.5)
    c.line(ML, y + 12 * mm, PAGE_W - MR, y + 12 * mm)
    items = [("6", "концептов"), ("4", "продукта"), ("2", "производства"),
             ("90", "дней до первых сделок")]
    col = (PAGE_W - ML - MR) / len(items)
    for i, (v, l) in enumerate(items):
        x = ML + i * col
        c.setFillColor(IVORY)
        c.setFont("MB", 19)
        c.drawString(x, y + 2 * mm, v)
        c.setFillColor(MUTED)
        c.setFont("M", 7.6)
        c.drawString(x, y - 3 * mm, l)

    c.setFillColor(MUTED)
    c.setFont("M", 7.2)
    c.drawString(ML, 18 * mm, "Внутренний документ направления. Изображения — концепт-визуализации, "
                              "не фотографии выполненных работ.")
    c.setFillColor(ORANGE)
    c.rect(0, 0, PAGE_W, 3 * mm, stroke=0, fill=1)


def on_page(c, doc):
    c.setFillColor(BG)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    c.setFont("M", 7)
    c.setFillColor(MUTED)
    c.drawString(ML, 10.5 * mm, "SM Production · SLAB & LIGHT · столешницы из слебов со светом")
    c.drawRightString(PAGE_W - MR, 10.5 * mm, f"стр. {doc.page} из {TOTAL_PAGES}")
    c.setStrokeColor(LINE)
    c.setLineWidth(0.4)
    c.line(ML, 13.6 * mm, PAGE_W - MR, 13.6 * mm)


TOTAL_PAGES = 17  # уточняется автоматически при сборке


def build_story():
    s = []

    # ═══════════════════════ 00. СОДЕРЖАНИЕ ═══════════════════════
    s += section_head("00", "Что внутри", "Один документ направления: продукт, технология, клиенты, деньги, план")
    s.append(P("Это не каталог столешниц. Это рабочая папка направления, которая нужна, чтобы "
               "запустить его за квартал: понять, что продаём, показать концепты, найти клиентов "
               "и посчитать экономику до первого заказа.", "lead"))
    s.append(Spacer(1, 4 * mm))
    left = [
        ("01", "Что мы продаём"), ("02", "Стык двух производств"),
        ("03", "Линейка продуктов"), ("04–06", "Шесть концептов"),
        ("07", "Технология: слеб и смола"), ("08", "ЧПУ и свет"),
    ]
    right = [
        ("09", "Клиенты и ЛПР"), ("10", "Где искать и как скорить"),
        ("11", "Партнёры-дизайнеры"), ("12", "Экономика и смета"),
        ("13", "Возражения"), ("14", "План на 90 дней"),
    ]
    def toc_col(items):
        rows = []
        for num, title in items:
            rows.append([Paragraph(f'<font color="#FF4D1C"><b>{num}</b></font>',
                                   sty("tn", fontName="MB", fontSize=8.6, leading=13)),
                         Paragraph(title, sty("tt", fontSize=8.6, leading=13, textColor=IVORY))])
        t = Table(rows, colWidths=[14 * mm, CONTENT_W / 2 - 18 * mm])
        t.setStyle(TableStyle([
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 2.4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2.4),
            ("LINEBELOW", (0, 0), (-1, -2), 0.3, LINE),
        ]))
        return t
    toc = Table([[toc_col(left), toc_col(right)]],
                colWidths=[CONTENT_W / 2, CONTENT_W / 2])
    toc.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (0, 0), 0),
        ("LEFTPADDING", (1, 0), (1, 0), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("LINEBEFORE", (1, 0), (1, 0), 0.4, LINE),
    ]))
    s.append(toc)
    s.append(Spacer(1, 7 * mm))
    s.append(kpi([("6", "концептов в каталоге"), ("4", "продукта в линейке"),
                  ("5", "сегментов клиентов"), ("200", "контактов за квартал"),
                  ("2–3", "сделки в первые 90 дней")]))
    s.append(Spacer(1, 7 * mm))
    s.append(P("Три правила этого документа", "h2"))
    s += bullets([
        "Никаких выдуманных кейсов, клиентов и цен: только то, что можно проверить.",
        "Все изображения — концепт-визуализации. Так и подписываем, пока нет фото объекта.",
        "Каждая цифра в смете считается по формуле из раздела 12, а не «на глаз».",
    ])
    s.append(Spacer(1, 4 * mm))
    s.append(panel("Если нужно быстро: раздел 01 — что продаём, раздел 04 — что показывать, "
                   "раздел 10 — куда идти, раздел 14 — что делать на этой неделе.", fs=9.2))
    s.append(PageBreak())

    # ═══════════════════════ 01. ЧТО ПРОДАЁМ ═══════════════════════
    s += section_head("01", "Что мы продаём",
                      "Не квадратные метры, а поверхность, которая работает на впечатление")
    s.append(P("Столешница из слеба — мебельный продукт. Столешница, в которой есть рисунок, "
               "залитый смолой, и свет внутри, — объект: центр зала, первое впечатление на "
               "ресепшн, кадр, который гость выкладывает сам.", "lead"))
    s.append(Spacer(1, 4 * mm))
    s.append(P("Клиент покупает не доску, а одно из четырёх:", "h3"))
    s += bullets([
        "центр зала, к которому идут фотографироваться;",
        "ресепшн, который говорит о бренде раньше администратора;",
        "переговорный стол, который показывает уровень компании;",
        "предмет, которого нет у конкурента.",
    ])
    s.append(Spacer(1, 5 * mm))
    s.append(table([
        ["Так продают мебель", "Так продаём мы"],
        ["«Столешница из массива, 40 мм, орех»", "«Стойка, которая светится изнутри и работает в кадре»"],
        ["Цена за м² и сравнение по прайсу", "Расчёт по месту, рисунку и схеме света"],
        ["Каталог из 200 позиций", "Шесть концептов + кастом под место"],
        ["Доставка и сборка", "Эскиз, производство, монтаж, пусконаладка света, гарантия"],
        ["Подрядчик по дереву", "Один контур: дерево + ЧПУ + свет + бренд + монтаж"],
    ], widths=[CONTENT_W * 0.42, CONTENT_W * 0.58], fs=8.2))
    s.append(Spacer(1, 5 * mm))
    s.append(P("Три обязательных элемента в любом описании", "h2"))
    s.append(Spacer(1, 1.5 * mm))
    cols = [("Цельный слеб", "Не шпон и не ЛДСП: массив с живой кромкой, сушкой и стабилизацией."),
            ("Свет внутри", "Не накладная лента: канал, профиль, драйвер и сценарии."),
            ("Своё производство", "Столярка и рекламный цех в одном контуре, монтаж — наш.")]
    t = Table([[Paragraph(f'<font name="MS" size="8.8" color="#E9A552">{t}</font><br/>'
                          f'<font size="7.6" color="#C9C1B5">{d}</font>',
                          sty("ccc", fontSize=7.6, leading=11.4, textColor=IVORY))
                for t, d in cols]], colWidths=[CONTENT_W / 3] * 3)
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("BACKGROUND", (0, 0), (-1, -1), CARD),
        ("LINEBEFORE", (0, 0), (-1, -1), 1.6, AMBER),
        ("LINEAFTER", (1, 0), (1, 0), 3, BG),
        ("LINEAFTER", (2, 0), (2, 0), 3, BG),
    ]))
    s.append(t)
    s.append(Spacer(1, 5 * mm))
    s.append(panel("Формулировка для любого канала: «Делаем столешницы из цельного дерева "
                   "со смолой и встроенным светом — от эскиза до монтажа, на своём "
                   "производстве в Москве».", fs=9.4))
    s.append(PageBreak())

    # ═══════════════════════ 02. СТЫК ═══════════════════════
    s += section_head("02", "Стык двух производств",
                      "Почему это сложно скопировать: нужны и столярка, и рекламный цех")
    s.append(P("Мебельщик умеет дерево и смолу, но свет для него — «приклеить ленту снизу». "
               "Рекламщик умеет ЧПУ, акрил и свет, но не умеет слебы, сушку и финиш. "
               "Мы закрываем обе половины.", "lead"))
    s.append(Spacer(1, 4 * mm))
    s.append(table([
        ["Что нужно", "Мебельный цех", "Рекламный цех", "SM Production"],
        ["Слебы, сушка, стабилизация", "да", "нет", "да"],
        ["Заливка смолой, шлифовка, финиш", "да", "нет", "да"],
        ["ЧПУ-фрезеровка и гравировка", "частично", "да", "да"],
        ["Акрил, светопроводящие вставки", "нет", "да", "да"],
        ["Светодиодные сборки, драйверы", "нет", "да", "да"],
        ["Печать, брендинг, логотипы", "нет", "да", "да"],
        ["Монтаж на действующем объекте", "иногда", "да", "да"],
    ], widths=[CONTENT_W * 0.40, CONTENT_W * 0.17, CONTENT_W * 0.16, CONTENT_W * 0.27], fs=8.2))
    s.append(Spacer(1, 6 * mm))
    s.append(P("Что даёт стык", "h2"))
    s.append(Spacer(1, 1.5 * mm))
    two = [("Скорость", "Слеб и свет делаются в одном графике, без пересылки между подрядчиками."),
           ("Ответственность", "Один договор и один человек, который отвечает за результат."),
           ("Маржа", "Свет, ЧПУ и брендинг — наши, а не закупка у третьей стороны."),
           ("Сложность", "Берём задачи, которые мебельщик не умеет, а рекламщик боится.")]
    rows = []
    for i in range(0, len(two), 2):
        rows.append([Paragraph(f'<font name="MS" color="#F4EFE6">{two[i][0]}</font><br/>'
                               f'<font size="7.4" color="#BDB4A8">{two[i][1]}</font>',
                               sty("aa", fontSize=7.4, leading=11)),
                     Paragraph(f'<font name="MS" color="#F4EFE6">{two[i+1][0]}</font><br/>'
                               f'<font size="7.4" color="#BDB4A8">{two[i+1][1]}</font>',
                               sty("bb", fontSize=7.4, leading=11))])
    t = Table(rows, colWidths=[CONTENT_W / 2] * 2)
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, -1), 0.3, LINE),
    ]))
    s.append(t)
    s.append(Spacer(1, 5 * mm))
    s.append(P("Кто что делает внутри проекта", "h2"))
    s.append(Spacer(1, 1.5 * mm))
    s.append(table([
        ["Этап", "Цех", "Результат"],
        ["Подбор слеба и сушка", "столярный", "паспорт материала: порода, влажность, дефекты"],
        ["Стабилизация и заливка", "столярный", "монолит без трещин и пузырей"],
        ["Гравировка и каналы под свет", "рекламный (ЧПУ)", "рисунок по эскизу, допуск ±0,5 мм"],
        ["Сборка света", "рекламный", "лента, профиль, драйвер, сценарии"],
        ["Финиш и контроль", "столярный", "покрытие, тесты, паспорт изделия"],
        ["Монтаж и пусконаладка", "монтаж", "подключено, проверено, снято на фото"],
    ], widths=[CONTENT_W * 0.34, CONTENT_W * 0.20, CONTENT_W * 0.46], fs=8.1))
    s.append(PageBreak())

    # ═══════════════════════ 03. ЛИНЕЙКА ═══════════════════════
    s += section_head("03", "Линейка продуктов",
                      "Четыре продукта и кастом: от быстрого входа до флагмана")
    s.append(table([
        ["Продукт", "Что это", "Кому", "Сложность"],
        ["<b>SLAB</b><br/>River-столешница", "Слеб с эпоксидной «рекой», подсветка нижней кромки или внутреннего контура",
         "Бары, рестораны, частные интерьеры", "средняя"],
        ["<b>ENGRAVE</b><br/>Светящиеся линии", "ЧПУ-гравировка 3–8 мм, заливка смолой, светопроводящий акрил",
         "Кофейни, переговорные, лаунжи", "высокая"],
        ["<b>BRAND</b><br/>Ресепшн и стойка", "Слеб + логотип или паттерн клиента в смоле, контурная подсветка",
         "Офисы, клиники, шоурумы", "высокая"],
        ["<b>MODULE</b><br/>Серийная коллекция", "Столы из остатков слебов, 3–4 фиксированных размера",
         "Дизайнеры, шоурумы, B2C", "низкая"],
        ["<b>CUSTOM</b><br/>Кастом", "Лестницы, подоконники, консоли, спинки кроватей",
         "Все сегменты", "по задаче"],
    ], widths=[CONTENT_W * 0.24, CONTENT_W * 0.42, CONTENT_W * 0.20, CONTENT_W * 0.14], fs=8.0))
    s.append(Spacer(1, 6 * mm))
    s.append(P("Логика линейки", "h2"))
    s.append(Spacer(1, 1.5 * mm))
    s += bullets([
        "<b>MODULE</b> — быстрый вход и повторные продажи: короткий срок, понятная цена.",
        "<b>SLAB</b> — основной средний чек: понятный образ, который легко представить в зале.",
        "<b>ENGRAVE и BRAND</b> — маржа и репутация: рисунок и бренд, которые нельзя скопировать.",
        "<b>CUSTOM</b> — рост чека на существующем клиенте без нового привлечения.",
    ])
    s.append(Spacer(1, 5 * mm))
    s.append(P("Пакеты внутри линейки", "h2"))
    s.append(Spacer(1, 1.5 * mm))
    s.append(table([
        ["", "STANDARD", "STUDIO", "SIGNATURE"],
        ["Слеб", "из наличия, 1 порода", "выбор из 3 пород", "отбор под проект"],
        ["Рисунок", "типовой из каталога", "адаптация под место", "индивидуальный эскиз"],
        ["Смола", "один цвет", "2–3 варианта", "подбор оттенка, выкрасы"],
        ["Свет", "нижняя подсветка", "контур или зона", "сценарии, датчик, диммер"],
        ["Монтаж", "стандартный", "стандартный", "ночной / сложный, шеф-монтаж"],
        ["Кому", "частник, кофейня", "дизайнер, офис", "HoReCa-флагман, бренд"],
    ], widths=[CONTENT_W * 0.16, CONTENT_W * 0.28, CONTENT_W * 0.28, CONTENT_W * 0.28],
        fs=8.0, first_col_bold=True))
    s.append(Spacer(1, 3 * mm))
    s.append(P("Пакет — это объём проектной работы, а не «уровень качества». Дерево и смола "
               "одинаково хорошие во всех трёх.", "muted"))
    s.append(PageBreak())

    # ═══════════════════════ 04. КОНЦЕПТЫ 1 ═══════════════════════
    s += section_head("04", "Концепты: река и линии",
                      "Два первых образа, с которых начинается разговор с клиентом")
    s.append(concept_block(
        "concept-river.jpg", "«Река» · SLAB",
        ["Слеб с естественной кромкой, вдоль которого идёт река из полупрозрачной смолы. "
         "Свет — по нижней кромке, поэтому смола светится изнутри, а не блестит сверху.",
         "Орех или дуб. Смола графит или янтарь. 1800–3000 × 700–900 мм, толщина 40–60 мм."],
        [("Свет", "2700 K, лента по периметру снизу, диммер"),
         ("Где", "барная стойка, обеденный стол, консоль в отеле"),
         ("Сложность", "средняя")]))
    s.append(Spacer(1, 7 * mm))
    s.append(concept_block(
        "concept-lines.jpg", "«Линии» · ENGRAVE",
        ["Тонкий рисунок вырезан на ЧПУ и залит смолой. Внутри каналов — светопроводящий "
         "акрил, поэтому линии светятся ровно, без точек.",
         "Ясень или дуб. Топография, изолинии, волны, контуры карты. 1200–2400 × 600–900 мм."],
        [("Свет", "3500–4000 K, внутренний контур, диммер и датчик"),
         ("Где", "переговорная, кофейня, лаунж, ресепшн"),
         ("Сложность", "высокая")]))
    s.append(Spacer(1, 6 * mm))
    s.append(table([
        ["", "«Река»", "«Линии»"],
        ["Что показываем", "макро кромки, где светится смола", "видео: свет проявляет рисунок"],
        ["Какой вопрос задаём", "«какая зона должна стать центром зала?»", "«чей это будет рисунок — ваш или бренда?»"],
        ["Против чего", "против «просто дерева» и шпона", "против печати на стекле и плёнки"],
    ], widths=[CONTENT_W * 0.20, CONTENT_W * 0.40, CONTENT_W * 0.40], fs=8.0, first_col_bold=True))
    s.append(Spacer(1, 4 * mm))
    s.append(panel("Почему эти два — первыми: «Река» понятна любому, «Линии» показывают "
                   "технологию. Вместе они закрывают и эмоцию, и инженерную сложность.", fs=9))
    s.append(PageBreak())

    # ═══════════════════════ 05. КОНЦЕПТЫ 2 ═══════════════════════
    s += section_head("05", "Концепты: соты и кольца",
                      "Геометрия и время: два образа, которые хорошо смотрятся в кадре")
    s.append(concept_block(
        "concept-honeycomb.jpg", "«Соты» · ENGRAVE",
        ["Гексагональная сетка, вырезанная в массиве, с акриловыми вставками и подсветкой "
         "снизу. В выключенном виде — строгая геометрия, включённом — светящийся узор.",
         "Дуб. Прозрачная смола для герметизации вставок. 2400–3600 × 800–1000 мм."],
        [("Свет", "3000 K, подсветка снизу, отдельные зоны"),
         ("Где", "бар, пивной ресторан, кофейня, лаунж"),
         ("Сложность", "высокая: много вставок и точная геометрия")]))
    s.append(Spacer(1, 7 * mm))
    s.append(concept_block(
        "concept-rings.jpg", "«Кольца» · BRAND",
        ["Спил с годовыми кольцами, где кольца дополнительно прорезаны и подсвечены. "
         "Издалека — натуральное дерево, вблизи — светящаяся карта времени.",
         "Дуб, карагач, лиственница. Прозрачная смола только в трещинах. 1000–1600 мм диаметр."],
        [("Свет", "2700 K, внутренние кольца, мягкий диммер"),
         ("Где", "ресепшн клиники, офис, шоурум, отель"),
         ("Сложность", "высокая")]))
    s.append(Spacer(1, 6 * mm))
    s.append(table([
        ["", "«Соты»", "«Кольца»"],
        ["Что показываем", "образец 300 × 300 с реальной подсветкой", "крупный план спила с подсветкой"],
        ["Какой вопрос задаём", "«сколько посадочных мест в баре?»", "«кто первым встречает гостя?»"],
        ["Против чего", "против плитки и мозаики на стойке", "против стандартной ресепшн-стойки"],
    ], widths=[CONTENT_W * 0.20, CONTENT_W * 0.40, CONTENT_W * 0.40], fs=8.0, first_col_bold=True))
    s.append(Spacer(1, 4 * mm))
    s.append(panel("Оба концепта сильно выигрывают на видео. Снимаем 15 секунд: выключили "
                   "верхний свет — включили подсветку. Это лучший продающий кадр.", fs=9))
    s.append(PageBreak())

    # ═══════════════════════ 06. КОНЦЕПТЫ 3 + ПРАВИЛА ═══════════════════════
    s += section_head("06", "Концепты: штабель и бренд",
                      "Серийный вход и прямой носитель логотипа")
    s.append(concept_block(
        "concept-stack.jpg", "«Штабель» · MODULE",
        ["Столешница из брусков разной высоты с зазорами, между которыми проходит свет. "
         "Дерево выглядит как конструктор, свет — как воздух внутри.",
         "Дуб, ясень, остатки слебов. 1200–2000 × 600–800 мм. Хорошо масштабируется в серию."],
        [("Свет", "3000 K, лента между брусками, нижняя зона"),
         ("Где", "кофейня, коворкинг, переговорная, консоль"),
         ("Сложность", "средняя, серийная")]))
    s.append(Spacer(1, 7 * mm))
    s.append(concept_block(
        "concept-reception.jpg", "«Бренд» · BRAND",
        ["Логотип или знак клиента, вырезанный в массиве, залитый смолой и подсвеченный "
         "контуром: днём тиснение, вечером светящийся знак.",
         "Дуб или орех, тёмная база. 1200–2400 × 700–900 мм. Делаем только при "
         "подтверждённых правах на знак."],
        [("Свет", "3500 K, контурная подсветка, отдельный сценарий"),
         ("Где", "офис, клиника, салон, шоурум, ресторан сети"),
         ("Сложность", "высокая: согласование логотипа и прав")]))
    s.append(Spacer(1, 6 * mm))
    s.append(P("Три ограничения, которые спасают проект", "h2"))
    rules = [("Один акцент на изделие",
              "Либо река, либо светящиеся линии, либо логотип. Два акцента спорят, три превращают стол в витрину."),
             ("Свет не бьёт в глаза",
              "Если гость видит точку ленты — схема неправильная. Свет либо отражённый, либо рассеянный."),
             ("Рисунок подчинён волокну",
              "Гравировка вдоль волокон читается, поперёк — выглядит как царапина. Эскиз накладываем на фото слеба.")]
    rows = []
    for i, (t_, d_) in enumerate(rules, 1):
        rows.append([Paragraph(f'<font name="MB" size="13" color="#E9A552">{i}</font>',
                               sty("rn", fontSize=13, leading=15)),
                     Paragraph(f'<font name="MS" color="#F4EFE6">{t_}</font><br/>'
                               f'<font size="7.6" color="#BDB4A8">{d_}</font>',
                               sty("rd", fontSize=7.6, leading=11.6))])
    t = Table(rows, colWidths=[12 * mm, CONTENT_W - 12 * mm])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW", (0, 0), (-1, -2), 0.3, LINE),
    ]))
    s.append(t)
    s.append(PageBreak())

    # ═══════════════════════ 07. ТЕХНОЛОГИЯ ═══════════════════════
    s += section_head("07", "Технология: слеб и смола",
                      "Входной контроль, сушка, стабилизация, заливка")
    s.append(Pic("detail-epoxy.jpg", CONTENT_W, 52 * mm,
                 caption="Заливка смолой: иллюстрация процесса", badge_text="ИЛЛЮСТРАЦИЯ"))
    s.append(Spacer(1, 5 * mm))
    s.append(table([
        ["Порода", "Характер", "Где хороша", "Особенности"],
        ["Дуб", "плотный, крупные волокна", "барные стойки, ресепшн, столы", "тяжёлый, стабильный, держит гравировку"],
        ["Орех", "тёмный, благородный рисунок", "столы, консоли, частные интерьеры", "дороже, аккуратный финиш"],
        ["Ясень", "светлый, выраженные кольца", "светлые интерьеры", "принимает светлые пигменты смолы"],
        ["Карагач", "сложный «вязкий» рисунок", "арт-объекты", "непредсказуемая геометрия, нужен запас"],
        ["Тополь / осина", "мягкий, сучковатый", "эффектные «реки»", "требует стабилизации"],
        ["Лиственница", "смолистая, плотная", "зоны у воды", "смолы мешают склейке"],
    ], widths=[CONTENT_W * 0.16, CONTENT_W * 0.26, CONTENT_W * 0.28, CONTENT_W * 0.30], fs=7.8))
    s.append(Spacer(1, 5 * mm))
    s.append(P("Входной контроль и подготовка", "h2"))
    s += bullets([
        "Влажность по влагомеру в трёх точках — <b>8–10 %</b>, не выше 12 %. Сырой слеб в производство не идёт.",
        "Карта дефектов: трещины крупные — под шпонку или в заливку, сквозные — под стяжку.",
        "Сушка камерная, очистка коры и рыхлой заболони, эпоксидный праймер по трещинам.",
        "Сухая сборка на вакуумном столе, проверка плоскости, компенсационные зазоры.",
    ])
    s.append(Spacer(1, 4 * mm))
    s.append(panel("Правило, которое экономит месяцы: <b>сырой слеб = трещины через месяц</b>. "
                   "Сначала сушка и паспорт материала, потом эскиз и аванс.", fs=9.2))
    s.append(Spacer(1, 4 * mm))
    s.append(table([
        ["Параметр заливки", "Значение"],
        ["Тип смолы", "deep-pour, UV-стабилизированная"],
        ["Слой за проход", "25–50 мм по паспорту смолы, не «всё сразу»"],
        ["Температура в помещении", "18–24 °C, стабильная на всё время полимеризации"],
        ["Влажность", "до 60 %, иначе «апельсиновая корка»"],
        ["Дегазация", "вакуум или прогрев до заливки, пузыри убираем до гелеобразования"],
        ["Полный набор", "48–72 ч на слой, шлифовка только после набора"],
        ["Цвет", "тест на 5 образцах; в договоре — диапазон оттенка, не HEX"],
    ], widths=[CONTENT_W * 0.36, CONTENT_W * 0.64], fs=8.0, first_col_bold=True))
    s.append(PageBreak())

    # ═══════════════════════ 08. ЧПУ И СВЕТ ═══════════════════════
    s += section_head("08", "ЧПУ и свет",
                      "Гравировка, каналы, спецификация света и три схемы")
    s.append(Pic("detail-cnc.jpg", CONTENT_W, 44 * mm,
                 caption="Фрезеровка канала под свет: иллюстрация процесса",
                 badge_text="ИЛЛЮСТРАЦИЯ"))
    s.append(Spacer(1, 5 * mm))
    s.append(table([
        ["Параметр ЧПУ", "Значение"],
        ["Допуск по геометрии", "±0,5 мм на деталь, ±1 мм на изделие после сборки"],
        ["Гравировка", "глубина 2–8 мм, ширина 3–30 мм, фреза с радиусом от 1,5 мм"],
        ["Каналы под свет", "8–12 мм, скруглённые, с выводом в скрытую нишу драйвера"],
        ["Кромка", "фаска 2–3 мм или скругление R3–R5, без сколов"],
        ["Пробный проход", "на обрезке той же породы и той же фрезой до чистовой"],
        ["Нельзя", "перемычки меньше 8 мм, пазы ближе 15 мм к кромке"],
    ], widths=[CONTENT_W * 0.32, CONTENT_W * 0.68], fs=8.0, first_col_bold=True))
    s.append(Spacer(1, 5 * mm))
    s.append(P("Свет: спецификация", "h2"))
    s.append(Spacer(1, 1.5 * mm))
    s.append(table([
        ["Параметр", "Значение", "Почему"],
        ["Напряжение", "12 или 24 В", "безопасность в гостевой зоне"],
        ["Температура", "2700 K тёплый / 3500–4000 K нейтральный", "дерево и смола / бренд-графика"],
        ["CRI", "≥ 90", "иначе дерево и смола «серят»"],
        ["Защита", "IP20 внутри корпуса, IP65 у мойки", "вода и пар"],
        ["Драйвер", "в доступной нише, запас 20 %", "сервис без разбора столешницы"],
        ["Управление", "диммер, датчик, выключатель", "сценарии день / вечер / выкл."],
        ["Гарантия", "24 месяца на свет", "отдельно от гарантии на дерево"],
    ], widths=[CONTENT_W * 0.20, CONTENT_W * 0.44, CONTENT_W * 0.36], fs=7.9))
    s.append(Spacer(1, 5 * mm))
    schemes = [("1 · Нижняя", "Лента по периметру снизу, светит на пол. Самая простая и самая эффектная."),
               ("2 · Контур", "Светопроводящий акрил или оптоволокно внутри смолы — светится рисунок."),
               ("3 · Кромка", "Лента по кромке в профиле, подчёркивает силуэт столешницы.")]
    t = Table([[Paragraph(f'<font name="MS" color="#E9A552">{a}</font><br/>'
                          f'<font size="7.4" color="#C9C1B5">{b}</font>',
                          sty("sc2", fontSize=7.4, leading=11.2)) for a, b in schemes]],
              colWidths=[CONTENT_W / 3] * 3)
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 0), (-1, -1), CARD),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LINEBEFORE", (0, 0), (-1, -1), 1.6, AMBER),
        ("LINEAFTER", (1, 0), (1, 0), 3, BG),
        ("LINEAFTER", (2, 0), (2, 0), 3, BG),
    ]))
    s.append(t)
    s.append(Spacer(1, 4 * mm))
    s.append(P("Тепло: между лентой и смолой — минимум 10 мм или алюминиевый профиль-радиатор. "
               "Смола не должна нагреваться выше 40 °C.", "muted"))
    s.append(PageBreak())

    # ═══════════════════════ 09. КЛИЕНТЫ ═══════════════════════
    s += section_head("09", "Клиенты",
                      "Пять сегментов, доли усилий и кто принимает решение")
    s.append(table([
        ["", "Сегмент", "Что важно", "Что предлагаем", "Цикл"],
        ["A", "Дизайнеры и архитекторы", "его идея должна выжить на производстве", "партнёрство, образец, 10 %", "2–8 нед."],
        ["B", "HoReCa: бары, рестораны, кофейни", "стойка — центр зала, открытие в срок", "объект, а не «мебель»", "1–3 мес."],
        ["C", "Офисы, коворкинги, клиники, салоны", "первое впечатление, брендбук, сроки", "ресепшн с логотипом и светом", "1–4 мес."],
        ["D", "Ритейл и шоурумы", "витрина, узнаваемость, фото", "кассовая стойка с паттерном", "3–8 нед."],
        ["E", "Частные заказчики", "«как на картинке», уход, гарантия", "стол, кухня, консоль", "2–6 нед."],
    ], widths=[6 * mm, CONTENT_W * 0.24, CONTENT_W * 0.28, CONTENT_W * 0.26, 17 * mm], fs=7.8))
    s.append(Spacer(1, 5 * mm))
    s.append(P("Доли усилий в первые 90 дней", "h2"))
    s.append(Spacer(1, 2 * mm))
    s.append(kpi([("40 %", "дизайнеры"), ("25 %", "HoReCa"), ("20 %", "офисы"),
                  ("10 %", "ритейл"), ("5 %", "частники")]))
    s.append(Spacer(1, 6 * mm))
    s.append(P("Кто принимает решение", "h2"))
    s.append(Spacer(1, 1.5 * mm))
    s.append(table([
        ["Сегмент", "Экономист", "Технический", "Влияющий"],
        ["Дизайн", "клиент дизайнера", "дизайнер", "сам дизайнер"],
        ["HoReCa", "владелец", "управляющий / технолог", "шеф-бармен, маркетолог"],
        ["Офис", "финансовый директор", "офис-менеджер / fit-out", "HR, бренд-менеджер"],
        ["Ритейл", "маркетинг-бюджет", "директор магазина", "бренд-команда"],
        ["Частник", "владелец", "дизайнер / прораб", "семья"],
    ], widths=[CONTENT_W * 0.16, CONTENT_W * 0.25, CONTENT_W * 0.31, CONTENT_W * 0.28], fs=7.9))
    s.append(Spacer(1, 4 * mm))
    s.append(panel("Правило: не продавать «в закупки» первым. Сначала тот, у кого болит задача, "
                   "потом тот, кто подписывает счёт.", fs=9.2))
    s.append(PageBreak())

    # ═══════════════════════ 10. ГДЕ ИСКАТЬ ═══════════════════════
    s += section_head("10", "Где искать и как скорить",
                      "Источники, ритм контактов и балльная оценка лида")
    s.append(table([
        ["Источник", "Кого искать", "Что делать", "Ритм"],
        ["Союз дизайнеров, профильные ассоциации", "дизайнеров и архитекторов", "письмо + приглашение на образец", "10 / нед."],
        ["AD, Elle Decoration, InMyRoom, Houzz", "бюро из подборок", "тёплое письмо по проекту", "5 / нед."],
        ["Pinterest, Instagram дизайнеров", "визуальный вкус и аудитория", "комментарии, репосты, личные сообщения", "15 мин / день"],
        ["Telegram-чаты архитекторов", "живые обсуждения", "отвечать по делу, не спамить", "каждый день"],
        ["MosBuild, ARCH Moscow", "бюро, поставщиков, подрядчиков", "образцы и договорённости", "по календарю"],
        ["Restoclub, новости открытий", "новые точки", "письмо за 4–8 недель до открытия", "5 / нед."],
        ["Яндекс Карты и 2ГИС", "новые адреса, ремонт", "звонок или визит", "10 / нед."],
        ["Fit-out и отделочные подрядчики", "офисы, клиники, ритейл", "партнёрство и субподряд", "5 / нед."],
        ["Мебельные и кухонные шоурумы", "частников и дизайнеров", "образец на комиссию", "3 / нед."],
    ], widths=[CONTENT_W * 0.28, CONTENT_W * 0.25, CONTENT_W * 0.35, 22 * mm], fs=7.6))
    s.append(Spacer(1, 4 * mm))
    s.append(P("Не покупать «базы дизайнеров» и не рассылать по ним: работает только персональное "
               "обращение по конкретному проекту или месту.", "muted"))
    s.append(Spacer(1, 5 * mm))
    s.append(P("Скоринг лида: 0–5 по каждому критерию", "h2"))
    s.append(Spacer(1, 1.5 * mm))
    s.append(table([
        ["Критерий", "0", "3", "5"],
        ["Есть объект или место", "нет", "планируется", "есть адрес и срок"],
        ["Бюджет", "«просто спросить»", "обсуждается", "подтверждён"],
        ["ЛПР доступен", "нет", "через секретаря", "прямой контакт"],
        ["Триггер", "нет", "«когда-нибудь»", "открытие / ремонт / переезд"],
        ["Понимает ценность", "«нужен стол»", "«хотим необычный»", "«нужен объект в зале»"],
        ["Срок", "больше 6 месяцев", "2–6 месяцев", "меньше 2 месяцев"],
    ], widths=[CONTENT_W * 0.34, CONTENT_W * 0.20, CONTENT_W * 0.20, CONTENT_W * 0.26], fs=8.0))
    s.append(Spacer(1, 4 * mm))
    s.append(panel("<b>20–30 баллов</b> — в работу первым. <b>12–19</b> — nurture: каталог, образец, "
                   "касание раз в три недели. <b>Меньше 12</b> — в базу, время не тратим.", fs=9.2))
    s.append(PageBreak())

    # ═══════════════════════ 11. ПАРТНЁРЫ ═══════════════════════
    s += section_head("11", "Партнёры-дизайнеры",
                      "Главный канал: не реклама, а человек, которому доверяет клиент")
    s.append(P("Дизайнер — не «канал продвижения», а соавтор. Ему важно, чтобы его идею не "
               "испортили на производстве, и чтобы он выглядел хорошо перед своим клиентом. "
               "Партнёрство строится на трёх вещах: образец в руки, честные сроки, комиссия "
               "по договору.", "lead"))
    s.append(Spacer(1, 5 * mm))
    give = ["образец 300 × 300 мм с гравировкой и подсветкой — бесплатно при встрече",
            "визуализация его эскиза на реальном слебе за 1 рабочий день",
            "фиксированная комиссия <b>10 %</b> по агентскому договору",
            "статус партнёра на сайте и в соцсетях по согласованию",
            "приоритет в очереди производства",
            "совместная фотосъёмка объекта после монтажа"]
    ask = ["знакомить с нами на этапе концепции, а не после закупки мебели",
           "давать фото места и размеры",
           "не передавать наши эскизы другим подрядчикам",
           "честно говорить, если проект встал"]
    def col(title, items, accent):
        out = [Paragraph(title, sty("pt2", fontName="MS", fontSize=9.6, leading=13,
                                    textColor=accent)), Spacer(1, 2.5 * mm)]
        for it in items:
            out.append(Paragraph(it, sty("pi", fontSize=8.2, leading=12.6, textColor=IVORY,
                                         leftIndent=8, bulletText="·", bulletColor=accent,
                                         bulletFontName="MB", bulletFontSize=9)))
            out.append(Spacer(1, 1.6 * mm))
        return out
    t = Table([[col("Что даём", give, AMBER), col("Что просим", ask, ORANGE)]],
              colWidths=[CONTENT_W * 0.56, CONTENT_W * 0.44])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (0, 0), 0),
        ("LEFTPADDING", (1, 0), (1, 0), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("LINEBEFORE", (1, 0), (1, 0), 0.5, LINE),
    ]))
    s.append(t)
    s.append(Spacer(1, 6 * mm))
    s.append(P("Условия", "h2"))
    s += bullets([
        "Комиссия выплачивается после закрытия и оплаты проекта, по договору и с закрывающими документами.",
        "Никаких выплат «наличными в конверте»: это риск для обеих сторон.",
        "Агентский договор подписывается до старта проекта, а не после.",
    ])
    s.append(Spacer(1, 5 * mm))
    s.append(P("Чтобы дизайнер начал рекомендовать, нужны пять вещей", "h2"))
    s.append(Spacer(1, 1.5 * mm))
    s.append(table([
        ["№", "Что", "Без этого"],
        ["1", "образец, который можно потрогать", "не поверит в качество"],
        ["2", "каталог с шестью концептами и сроками", "не сможет показать своему клиенту"],
        ["3", "смета за один рабочий день", "уйдёт к тому, кто посчитал быстрее"],
        ["4", "человек, отвечающий в тот же день", "потеряет доверие на первой задержке"],
        ["5", "понятная гарантия и процедура спора", "побоится рисковать своей репутацией"],
    ], widths=[8 * mm, CONTENT_W * 0.50, CONTENT_W - 8 * mm - CONTENT_W * 0.50], fs=8.0))
    s.append(PageBreak())

    # ═══════════════════════ 12. ЭКОНОМИКА ═══════════════════════
    s += section_head("12", "Экономика и смета",
                      "Формула вместо «цены за м²»: считаем проект, а не доску")
    s.append(P("В пакете нет придуманных цен. Есть формула, структура и правила — рубли "
               "подставляются из фактических закупок и хронометража. После первых трёх смет "
               "они фиксируются как прайс-матрица.", "lead"))
    s.append(Spacer(1, 4 * mm))
    s.append(panel("<b>Себестоимость</b> = слеб + сушка и подготовка + смола + расходники + "
                   "часы ЧПУ + ручной труд + свет + монтаж + брак-резерв 5–8 %.<br/>"
                   "<b>Цена</b> = себестоимость / (1 − маржа), где маржа 25–35 %. "
                   "Не «плюс 30 % сверху» — это разные числа.", fs=8.8))
    s.append(Spacer(1, 5 * mm))
    s.append(table([
        ["Статья в цене", "Доля", "Что внутри"],
        ["Материалы", "30–40 %", "слеб, смола, пигмент, расходники"],
        ["ЧПУ, столярка, сборка света", "15–20 %", "машино-часы и ручной труд"],
        ["Свет и электрика", "8–12 %", "лента, профиль, драйвер, диммер, сборка"],
        ["Монтаж и логистика", "5–10 %", "бригада, такелаж, ночной заезд"],
        ["Накладные и брак-резерв", "5–8 %", "переделки, образцы, упаковка"],
        ["Маржа", "25–35 %", "развитие направления и резерв"],
    ], widths=[CONTENT_W * 0.38, CONTENT_W * 0.14, CONTENT_W * 0.48], fs=8.1, first_col_bold=True))
    s.append(Spacer(1, 5 * mm))
    s.append(P("Что двигает цену сильнее всего", "h2"))
    s.append(Spacer(1, 1.5 * mm))
    s.append(table([
        ["Фактор", "Влияние", "Как управлять"],
        ["Порода и редкость слеба", "высокое", "предлагать 2–3 альтернативы"],
        ["Площадь заливки смолы", "высокое", "река уже, слой тоньше"],
        ["Плотность гравировки", "высокое", "меньше линий, крупнее паттерн"],
        ["Схема света", "среднее", "нижняя подсветка вместо контура"],
        ["Срочность", "высокое, +15–30 %", "честный срок вместо «любой ценой»"],
        ["Монтаж и этаж", "среднее", "считать до выезда, не «по факту»"],
    ], widths=[CONTENT_W * 0.40, CONTENT_W * 0.20, CONTENT_W * 0.40], fs=8.1))
    s.append(PageBreak())

    # ═══════════════════════ 13. ВОЗРАЖЕНИЯ ═══════════════════════
    s += section_head("13", "Возражения",
                      "Восемь фраз, которые звучат чаще всего, и что на них отвечать")
    objections = [
        ("Дорого", "Давайте разделим: есть стоимость стола, а есть стоимость объекта, который "
                   "работает на впечатление и фото. Если бюджет ограничен, сделаем тот же рисунок "
                   "на меньшем слебе или упростим свет — покажу два варианта."),
        ("Эпоксидка пожелтеет", "Желтеет не смола, а дешёвая смола без UV-стабилизации на солнце. "
                                "Мы используем стабилизированную и не ставим изделие под прямое солнце. "
                                "Это прописано в договоре и в памятке."),
        ("Поцарапается, будут пятна", "Для баров делаем 2К-полиуретан, для кухни — масло-воск с "
                                      "обновлением. Даю тесты: вода 24 часа, вино, кофе, горячая кружка. "
                                      "Плюс памятка по эксплуатации."),
        ("Долго", "Срок считается от утверждения эскиза и наличия слеба: обычно производство плюс "
                  "монтаж. Если дата открытия жёсткая — скажите её сразу, подберём слеб из наличия."),
        ("У нас свой столяр", "Отлично, значит, дерево он знает. Мы можем закрыть то, чего у него нет: "
                              "ЧПУ-гравировку, свет внутри смолы, акрил и монтаж. Иногда дешевле, "
                              "чем покупать станок и учиться."),
        ("Пришлите прайс", "Прайса за м² у нас нет — слишком много зависит от слеба, рисунка и света. "
                           "Пришлите фото и размер, за рабочий день будет точная вилка. Бесплатно."),
        ("Сделайте как у конкурента, но дешевле", "Могу сделать похожий характер, но свой рисунок и на "
                                                  "своём материале. Копию «один в один» не беру: там всегда "
                                                  "спор о цене и качестве."),
        ("Нам нужно подумать", "Конечно. Чтобы думать было о чём, пришлю два варианта с разным бюджетом "
                               "и сроком. Когда вернуться — через неделю?"),
    ]
    rows = []
    for i, (q, a) in enumerate(objections, 1):
        rows.append([Paragraph(f'<font name="MB" size="12" color="#E9A552">{i}</font>',
                               sty(f"qn{i}", fontSize=12, leading=14)),
                     Paragraph(f'<font name="MS" color="#F4EFE6">«{q}»</font><br/>'
                               f'<font size="7.9" color="#C9C1B5">{a}</font>',
                               sty(f"qa{i}", fontSize=7.9, leading=12.2))])
    t = Table(rows, colWidths=[11 * mm, CONTENT_W - 11 * mm])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 3.4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4.2),
        ("LINEBELOW", (0, 0), (-1, -2), 0.3, LINE),
    ]))
    s.append(t)
    s.append(Spacer(1, 4 * mm))
    s.append(panel("Чего не говорим: «любой размер за 5 дней», «не пожелтеет никогда», «гарантия 10 лет», "
                   "«мы работали с [известный бренд]», «это фото нашей работы» — если это визуализация.", fs=8.8))
    s.append(PageBreak())

    # ═══════════════════════ 14. ПЛАН ═══════════════════════
    s += section_head("14", "План на 90 дней",
                      "От «мы можем делать» к «нас рекомендуют»")
    s.append(P("Цель квартала: три демо-объекта, десять дизайнеров-партнёров, два-три платных "
               "заказа и посчитанная себестоимость по каждому.", "lead"))
    s.append(Spacer(1, 4 * mm))
    s.append(P("Первая неделя: десять действий", "h2"))
    s.append(Spacer(1, 1.5 * mm))
    s.append(table([
        ["№", "Действие", "Результат"],
        ["1", "Утвердить позиционирование и название линейки", "одна фраза, зафиксирована"],
        ["2", "Проверить наличие слебов: 5–7 под демо", "список с фото и влажностью"],
        ["3", "Сделать три образца 300 × 300", "река, гравировка, штабель"],
        ["4", "Снять видео 15 сек «свет выключили/включили»", "ролик для встреч и соцсетей"],
        ["5", "Собрать каталог из шести концептов", "PDF и 6 изображений"],
        ["6", "Сверстать страницу услуги", "черновик по текстам пакета"],
        ["7", "Собрать список 50 дизайнеров", "CSV с источником и датой"],
        ["8", "Собрать список 30 HoReCa-открытий", "CSV с триггером"],
        ["9", "Подготовить договор, эскиз-приложение, памятку", "шаблоны"],
        ["10", "Посчитать шесть нормативов себестоимости", "таблица в разделе 12"],
    ], widths=[8 * mm, CONTENT_W * 0.56, CONTENT_W - 8 * mm - CONTENT_W * 0.56], fs=7.8))
    s.append(Spacer(1, 4 * mm))
    s.append(P("KPI квартала", "h2"))
    s.append(Spacer(1, 2 * mm))
    s.append(kpi([("200", "контактов"), ("40", "ответов"), ("25", "встреч и образцов"),
                  ("20", "расчётов"), ("2–3", "договора")]))
    s.append(Spacer(1, 4 * mm))
    s.append(panel("Когда останавливаться: меньше 20 ответов на 200 контактов — проблема в оффере "
                   "или списке. Есть встречи без расчётов — не донесли ценность. Есть расчёты без "
                   "сделок — цена или срок. Есть сделки с маржой ниже 25 % — производство не тянет. "
                   "Меняем <b>одну</b> переменную, а не всё сразу.", fs=8.8))
    s.append(PageBreak())

    # ═══════════════════════ 15. СТРАНИЦА САЙТА ═══════════════════════
    s += section_head("15", "Страница сайта",
                      "Структура и тексты для /uslugi/stoleshnicy-iz-sleba")
    s.append(table([
        ["Блок", "Содержание"],
        ["H1", "Столешницы из цельного дерева со светом изнутри"],
        ["Подзаголовок", "Слебы дуба, ореха и ясеня, эпоксидная смола, гравировка на ЧПУ и подсветка. "
                         "От эскиза до монтажа — на своём производстве в Москве."],
        ["1. Почему это не просто столешница", "дерево + рисунок + свет в одном изделии, один подрядчик"],
        ["2. Что делаем", "SLAB, ENGRAVE, BRAND, MODULE — четыре карточки"],
        ["3. Шесть концептов", "изображение + порода + схема света + применение"],
        ["4. Как проходит проект", "фото → эскиз и расчёт → образец → договор → производство → монтаж"],
        ["5. От чего зависит стоимость", "порода, площадь заливки, плотность гравировки, свет, монтаж"],
        ["6. Уход", "без абразивов, горячее через подставку, масло раз в 6–12 месяцев"],
        ["7. Дизайнерам", "10 %, визуализация за день, приоритет в производстве"],
        ["FAQ", "цена, срок, желтизна, горячее, кухня, логотип, регионы, «это ваш объект?»"],
        ["CTA", "«Пришлите фото места — вернёмся с идеей и расчётом»"],
    ], widths=[CONTENT_W * 0.30, CONTENT_W * 0.70], fs=7.9, first_col_bold=True))
    s.append(Spacer(1, 4 * mm))
    s.append(P("Чего на странице быть не должно", "h2"))
    s.append(Spacer(1, 1 * mm))
    s += bullets([
        "«Работаем с 2010 года» и любые сроки, которых нет в фактах компании.",
        "«Более 500 столешниц» — таких данных нет.",
        "Названия клиентов и логотипы без письменного разрешения.",
        "«Гарантия 10 лет», «не желтеет никогда», «цена от …» без себестоимости.",
    ])
    s.append(Spacer(1, 5 * mm))
    s.append(P("Где что лежит", "h2"))
    s.append(Spacer(1, 1.5 * mm))
    s.append(table([
        ["Файл", "Что внутри"],
        ["01-strategy.md", "позиционирование, продукты, воронка, риски, критерий успеха"],
        ["02-production.md", "породы, режимы, смола, ЧПУ, свет, контроль качества, монтаж"],
        ["03-concepts.md", "шесть концептов: порода, рисунок, свет, применение"],
        ["04-clients.md", "сегменты, ЛПР, источники, скоринг, партнёрская программа"],
        ["05-outreach.md", "письма по сегментам, скрипт звонка, восемь возражений, follow-up"],
        ["06-pricing.md", "пакеты, формула себестоимости, условия оплаты, гарантия"],
        ["07-plan-90-days.md", "план по неделям, KPI, роли, контрольные точки"],
        ["08-landing-copy.md", "полный текст страницы услуги и FAQ"],
        ["09-prospects-template.csv", "пустой шаблон базы для CRM"],
    ], widths=[CONTENT_W * 0.30, CONTENT_W * 0.70], fs=7.9))
    s.append(Spacer(1, 3 * mm))
    s.append(P("Сборка PDF: .venv/bin/python marketing/wood-countertops-2026/build_pdf.py", "muted"))
    return s


def make_doc(path: Path) -> int:
    doc = BaseDocTemplate(str(path), pagesize=A4, leftMargin=ML, rightMargin=MR,
                          topMargin=MT, bottomMargin=MB,
                          title="SM Production — SLAB & LIGHT: столешницы из слебов со светом",
                          author="SM Production",
                          subject="Направление: столешницы из дерева и эпоксидной смолы "
                                  "со встроенным светом")
    frame = Frame(ML, MB, CONTENT_W, PAGE_H - MT - MB, id="f",
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates([
        PageTemplate(id="cover", frames=[frame], onPage=on_cover),
        PageTemplate(id="page", frames=[frame], onPage=on_page),
    ])
    story = [NextPageTemplate("page"), PageBreak()] + build_story()
    doc.build(story)
    return doc.page


def main() -> None:
    global TOTAL_PAGES
    # первый проход — узнать реальное число страниц для подписи «стр. N из M»
    probe = OUT.with_suffix(".probe.pdf")
    TOTAL_PAGES = make_doc(probe)
    probe.unlink(missing_ok=True)
    TOTAL_PAGES = make_doc(OUT)
    print(f"  {OUT.name}: {OUT.stat().st_size // 1024} КБ · {TOTAL_PAGES} стр.")


if __name__ == "__main__":
    main()
