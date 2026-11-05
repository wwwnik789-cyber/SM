#!/usr/bin/env python3
"""Build the internal SM Production dealership manager playbook PDF."""
from pathlib import Path
import re
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Frame, Image, KeepTogether, NextPageTemplate, PageBreak,
    PageTemplate, Paragraph, Spacer, Table, TableStyle, Flowable
)
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
MD_PATH = ROOT / "manager-guide.md"
OUT_PATH = ROOT / "SM-Production-dealership-manager-playbook.pdf"
ASSET_DIR = REPO / "presentations" / "dealerships-2026" / "assets"

PAGE_W, PAGE_H = A4
PURPLE = colors.HexColor("#7550B5")
PURPLE_DARK = colors.HexColor("#4B2B78")
GOLD = colors.HexColor("#D5A600")
INK = colors.HexColor("#18191F")
MUTED = colors.HexColor("#61636A")
LINE = colors.HexColor("#DDD9D1")
SOFT = colors.HexColor("#F4F1EB")
SOFT_PURPLE = colors.HexColor("#EEE8F7")
WHITE = colors.white

FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
pdfmetrics.registerFont(TTFont("Body", str(FONT_DIR / "DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("Body-Bold", str(FONT_DIR / "DejaVuSans-Bold.ttf")))
pdfmetrics.registerFontFamily("Body", normal="Body", bold="Body-Bold", italic="Body", boldItalic="Body-Bold")

STYLES = {
    "h1": ParagraphStyle("h1", fontName="Body-Bold", fontSize=20, leading=24, textColor=INK, spaceAfter=8),
    "h2": ParagraphStyle("h2", fontName="Body-Bold", fontSize=12.5, leading=16, textColor=PURPLE_DARK, spaceBefore=7, spaceAfter=4),
    "h3": ParagraphStyle("h3", fontName="Body-Bold", fontSize=10.2, leading=13.5, textColor=INK, spaceBefore=5, spaceAfter=2),
    "body": ParagraphStyle("body", fontName="Body", fontSize=9.2, leading=13.4, textColor=INK, spaceAfter=5),
    "bullet": ParagraphStyle("bullet", fontName="Body", fontSize=9.1, leading=13.1, textColor=INK, leftIndent=12, bulletIndent=1.5, spaceAfter=2.5),
    "number": ParagraphStyle("number", fontName="Body", fontSize=9.1, leading=13.1, textColor=INK, leftIndent=15, bulletIndent=0, spaceAfter=2.5),
    "quote": ParagraphStyle("quote", fontName="Body", fontSize=9.1, leading=13.6, textColor=INK, leftIndent=0, rightIndent=0),
    "cell": ParagraphStyle("cell", fontName="Body", fontSize=7.6, leading=10.2, textColor=INK),
    "cellhead": ParagraphStyle("cellhead", fontName="Body-Bold", fontSize=7.4, leading=9.5, textColor=WHITE),
    "caption": ParagraphStyle("caption", fontName="Body", fontSize=7, leading=9, textColor=MUTED, alignment=TA_CENTER),
    "small": ParagraphStyle("small", fontName="Body", fontSize=7.5, leading=10.5, textColor=MUTED),
}


def inline(text):
    text = escape(text)
    text = re.sub(r"`([^`]+)`", r'<font name="Body-Bold" color="#4B2B78">\1</font>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\w)\*([^*\n]+)\*", r"<i>\1</i>", text)
    text = re.sub(r"(https?://[^\s<]+)", r'<link href="\1" color="#4B2B78"><u>\1</u></link>', text)
    return text


class SectionKicker(Flowable):
    def __init__(self, text):
        super().__init__()
        self.text = text.upper()
        self.height = 16

    def wrap(self, availWidth, availHeight):
        return availWidth, self.height

    def draw(self):
        self.canv.setFillColor(PURPLE)
        self.canv.roundRect(0, 7, 28, 3, 1.5, fill=1, stroke=0)
        self.canv.setFont("Body-Bold", 7.2)
        self.canv.setFillColor(GOLD)
        self.canv.drawString(38, 3.8, self.text)


class CoverFlowable(Flowable):
    def __init__(self):
        super().__init__()
        self.width = PAGE_W
        self.height = PAGE_H

    def wrap(self, availWidth, availHeight):
        return PAGE_W, PAGE_H

    def draw(self):
        c = self.canv
        hero = ASSET_DIR / "dealer-branding-hero.jpg"
        c.drawImage(str(hero), 0, 0, PAGE_W, PAGE_H, preserveAspectRatio=False, mask="auto")
        c.saveState()
        try:
            c.setFillAlpha(0.82)
        except Exception:
            pass
        c.setFillColor(INK)
        c.rect(0, 0, PAGE_W * 0.72, PAGE_H, fill=1, stroke=0)
        try:
            c.setFillAlpha(1)
        except Exception:
            pass
        c.setFillColor(PURPLE)
        c.roundRect(24 * mm, PAGE_H - 47 * mm, 33 * mm, 2.3 * mm, 1.1 * mm, fill=1, stroke=0)
        c.setFont("Body-Bold", 9)
        c.setFillColor(GOLD)
        c.drawString(24 * mm, PAGE_H - 39 * mm, "SM PRODUCTION · ВНУТРЕННИЙ ДОКУМЕНТ")
        c.setFont("Body-Bold", 27)
        c.setFillColor(WHITE)
        c.drawString(24 * mm, PAGE_H - 70 * mm, "ПАМЯТКА")
        c.drawString(24 * mm, PAGE_H - 82 * mm, "МЕНЕДЖЕРА")
        c.setFillColor(PURPLE)
        c.drawString(24 * mm, PAGE_H - 94 * mm, "ДИЛЕРСКИЕ ЦЕНТРЫ")
        c.setFont("Body", 11.5)
        c.setFillColor(WHITE)
        c.drawString(24 * mm, PAGE_H - 111 * mm, "Кого искать · что предлагать · как звонить")
        c.drawString(24 * mm, PAGE_H - 119 * mm, "как квалифицировать · что фиксировать в CRM")

        logo = ASSET_DIR / "sm-logo-full-transparent.png"
        c.drawImage(str(logo), 24 * mm, 23 * mm, 66 * mm, 54 * mm, preserveAspectRatio=True, mask="auto")
        c.setFont("Body", 8.5)
        c.setFillColor(colors.HexColor("#D9D9DD"))
        c.drawString(24 * mm, 16 * mm, "Версия от 5 ноября 2026 года")
        c.drawRightString(PAGE_W - 16 * mm, 16 * mm, "Только для внутреннего использования")
        c.restoreState()


def inner_page(canv, doc):
    canv.saveState()
    canv.setFillColor(colors.HexColor("#FBFAF7"))
    canv.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    canv.setStrokeColor(GOLD)
    canv.setLineWidth(1.2)
    canv.line(doc.leftMargin, PAGE_H - 13 * mm, PAGE_W - doc.rightMargin, PAGE_H - 13 * mm)
    canv.setFont("Body-Bold", 6.8)
    canv.setFillColor(PURPLE_DARK)
    canv.drawString(doc.leftMargin, PAGE_H - 10.5 * mm, "SM PRODUCTION · ДИЛЕРСКИЕ ЦЕНТРЫ")
    canv.setStrokeColor(LINE)
    canv.setLineWidth(0.4)
    canv.line(doc.leftMargin, 12 * mm, PAGE_W - doc.rightMargin, 12 * mm)
    canv.setFont("Body", 7)
    canv.setFillColor(MUTED)
    canv.drawString(doc.leftMargin, 8.2 * mm, "Памятка менеджера · внутренний документ")
    canv.drawRightString(PAGE_W - doc.rightMargin, 8.2 * mm, str(doc.page))
    canv.restoreState()


def split_row(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def table_flow(rows, avail):
    head = rows[0]
    body = rows[1:]
    n = len(head)
    data = [[Paragraph(inline(v), STYLES["cellhead"]) for v in head]]
    for row in body:
        row = (row + [""] * n)[:n]
        data.append([Paragraph(inline(v), STYLES["cell"]) for v in row])
    # Give descriptive columns more room.
    if n == 3:
        widths = [avail * 0.25, avail * 0.33, avail * 0.42]
    elif n == 2:
        widths = [avail * 0.62, avail * 0.38]
    else:
        widths = [avail / n] * n
    t = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PURPLE_DARK),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.45, LINE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, SOFT]),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


def quote_box(text, avail):
    t = Table([[Paragraph(inline(text), STYLES["quote"])]], colWidths=[avail - 10])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), SOFT_PURPLE),
        ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#C9B7E2")),
        ("LINEBEFORE", (0, 0), (0, -1), 4, GOLD),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    return t


def image_strip():
    images = [
        (ASSET_DIR / "dealer-seasonal-pos.jpg", "Сезонное обновление"),
        (ASSET_DIR / "dealer-model-launch.jpg", "Презентация модели"),
        (ASSET_DIR / "dealer-reception-delivery.jpg", "Обновление пространства"),
    ]
    cells = []
    for path, cap in images:
        img = Image(str(path), width=51 * mm, height=28.7 * mm)
        cells.append([img, Paragraph(cap, STYLES["caption"])])
    table = Table([
        [cells[0][0], cells[1][0], cells[2][0]],
        [cells[0][1], cells[1][1], cells[2][1]],
    ], colWidths=[54 * mm] * 3)
    table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 1),
        ("RIGHTPADDING", (0, 0), (-1, -1), 1),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    return table


def qr_drawing(url, size=30 * mm):
    qr = QrCodeWidget(url)
    bounds = qr.getBounds()
    w = bounds[2] - bounds[0]
    h = bounds[3] - bounds[1]
    drawing = Drawing(size, size, transform=[size/w, 0, 0, size/h, 0, 0])
    drawing.add(qr)
    return drawing


def final_materials_block(avail):
    qr = qr_drawing("https://sm-production.ru/uslugi/oformlenie-avtosalonov")
    text = Paragraph(
        "<b>Страница для клиента</b><br/>"
        "<link href='https://sm-production.ru/uslugi/oformlenie-avtosalonov' color='#4B2B78'>"
        "sm-production.ru/uslugi/oformlenie-avtosalonov</link><br/><br/>"
        "<b>Контакты</b><br/>+7 (495) 799-00-19<br/>sm-pro1@yandex.ru<br/>"
        "Москва, Остаповский проезд, д. 9 с. 3",
        STYLES["body"],
    )
    t = Table([[qr, text]], colWidths=[40 * mm, avail - 40 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), SOFT_PURPLE),
        ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#C9B7E2")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    return t


def parse_markdown(md, avail):
    lines = md.splitlines()
    story = []
    i = 0
    section_count = 0
    while i < len(lines):
        s = lines[i].strip()
        if not s or s == "---":
            i += 1
            continue

        if s.startswith("# "):
            heading = s[2:].strip()
            # Ignore document title before first numbered section.
            if not re.match(r"\d+\.", heading):
                i += 1
                continue
            if section_count > 0:
                story.append(PageBreak())
            section_count += 1
            story += [SectionKicker(f"Раздел {section_count:02d}"), Paragraph(inline(heading), STYLES["h1"]), Spacer(1, 2)]
            if heading.startswith("4."):
                story += [image_strip(), Spacer(1, 5)]
            i += 1
            continue

        if s.startswith("## "):
            story.append(Paragraph(inline(s[3:]), STYLES["h2"]))
            i += 1
            continue

        if s.startswith("### "):
            story.append(Paragraph(inline(s[4:]), STYLES["h3"]))
            i += 1
            continue

        if s.startswith(">"):
            parts = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                parts.append(lines[i].strip().lstrip("> "))
                i += 1
            story += [quote_box("<br/>".join(parts), avail), Spacer(1, 5)]
            continue

        if s.startswith("|") and i + 1 < len(lines) and set(lines[i+1].strip()) <= set("|-: "):
            rows = [split_row(s)]
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(split_row(lines[i]))
                i += 1
            story += [table_flow(rows, avail), Spacer(1, 5)]
            continue

        m = re.match(r"^([-*]|\d+\.)\s+(.*)$", s)
        if m:
            while i < len(lines):
                mm = re.match(r"^([-*]|\d+\.)\s+(.*)$", lines[i].strip())
                if not mm:
                    break
                marker, text = mm.group(1), mm.group(2)
                style = STYLES["bullet"] if marker in ("-", "*") else STYLES["number"]
                bullet = "•" if marker in ("-", "*") else marker
                story.append(Paragraph(inline(text), style, bulletText=bullet))
                i += 1
            story.append(Spacer(1, 3))
            continue

        # Normal paragraph.
        buf = [s]
        i += 1
        while i < len(lines):
            nxt = lines[i].strip()
            if not nxt or nxt == "---" or re.match(r"^(#|[-*]\s|\d+\.\s|\|)", nxt):
                break
            buf.append(nxt)
            i += 1
        text = " ".join(buf)
        # Highlight the core offer and rule-like statements.
        if text.startswith("Бесплатно смотрим") or text.startswith("Не продать проект"):
            story += [quote_box(text, avail), Spacer(1, 5)]
        else:
            story.append(Paragraph(inline(text), STYLES["body"]))

    # Add QR block after the final materials section.
    story += [Spacer(1, 7), final_materials_block(avail)]
    return story


def build():
    doc = BaseDocTemplate(
        str(OUT_PATH), pagesize=A4,
        leftMargin=18 * mm, rightMargin=16 * mm,
        topMargin=20 * mm, bottomMargin=17 * mm,
        title="Памятка менеджера SM Production: дилерские центры",
        author="SM Production", subject="Внутренняя инструкция для менеджеров", lang="ru",
    )
    cover_frame = Frame(0, 0, PAGE_W, PAGE_H, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0, id="cover")
    inner_frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="inner")
    doc.addPageTemplates([
        PageTemplate(id="cover", frames=[cover_frame]),
        PageTemplate(id="inner", frames=[inner_frame], onPage=inner_page),
    ])
    md = MD_PATH.read_text(encoding="utf-8")
    story = [CoverFlowable(), NextPageTemplate("inner"), PageBreak()]
    story += parse_markdown(md, doc.width)
    doc.build(story)
    print(OUT_PATH)


if __name__ == "__main__":
    build()
