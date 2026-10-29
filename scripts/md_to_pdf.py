"""Конвертер аудита (markdown) в PDF: reportlab + DejaVu (кириллица)."""
import re
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, KeepTogether, PageBreak,
                                PageTemplate, Paragraph, Spacer, Table, TableStyle,
                                XPreformatted)

FONT_DIR = "/usr/share/fonts/truetype/dejavu"
pdfmetrics.registerFont(TTFont("DJ", f"{FONT_DIR}/DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DJ-B", f"{FONT_DIR}/DejaVuSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("DJ-M", f"{FONT_DIR}/DejaVuSansMono.ttf"))
pdfmetrics.registerFontFamily("DJ", normal="DJ", bold="DJ-B", italic="DJ", boldItalic="DJ-B")

INK = colors.HexColor("#14161a")
MUT = colors.HexColor("#5f6470")
ACCENT = colors.HexColor("#ff4d1c")
NAVY = colors.HexColor("#0f3460")
LINE = colors.HexColor("#dcd9d2")
SOFT = colors.HexColor("#f5f4f1")

S = {
    "title": ParagraphStyle("title", fontName="DJ-B", fontSize=25, leading=30, textColor=INK, spaceAfter=6),
    "subtitle": ParagraphStyle("subtitle", fontName="DJ", fontSize=11.5, leading=17, textColor=MUT),
    "kicker": ParagraphStyle("kicker", fontName="DJ-B", fontSize=8.5, leading=12, textColor=ACCENT),
    "h1": ParagraphStyle("h1", fontName="DJ-B", fontSize=18, leading=23, textColor=INK, spaceBefore=16, spaceAfter=8),
    "h2": ParagraphStyle("h2", fontName="DJ-B", fontSize=12.8, leading=17, textColor=NAVY, spaceBefore=14, spaceAfter=6),
    "h3": ParagraphStyle("h3", fontName="DJ-B", fontSize=10.6, leading=14.5, textColor=INK, spaceBefore=10, spaceAfter=4),
    "body": ParagraphStyle("body", fontName="DJ", fontSize=9.6, leading=14.4, textColor=INK, spaceAfter=6, alignment=TA_LEFT),
    "bullet": ParagraphStyle("bullet", fontName="DJ", fontSize=9.6, leading=14, textColor=INK,
                             leftIndent=12, bulletIndent=2, spaceAfter=3),
    "cell": ParagraphStyle("cell", fontName="DJ", fontSize=8.6, leading=12, textColor=INK),
    "cellhead": ParagraphStyle("cellhead", fontName="DJ-B", fontSize=8.4, leading=11.5, textColor=colors.white),
    "code": ParagraphStyle("code", fontName="DJ-M", fontSize=7.4, leading=10.8, textColor=INK),
    "quote": ParagraphStyle("quote", fontName="DJ", fontSize=9.2, leading=14, textColor=MUT, leftIndent=10),
}


def inline(text):
    """Мини-парсер инлайновой разметки -> reportlab-разметка."""
    text = (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
    text = re.sub(r"`([^`]+)`", r'<font name="DJ-M" size="8.2">\1</font>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\w)\*([^*\n]+)\*", r"<i>\1</i>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<link href="\2" color="#0f3460"><u>\1</u></link>', text)
    text = re.sub(r"https?://\S+", lambda m: f'<link href="{m.group(0)}" color="#0f3460">{m.group(0)}</link>', text)
    return text


def split_row(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def wrap_code(text, width=96):
    out = []
    for line in text.split("\n"):
        while len(line) > width:
            out.append(line[:width])
            line = "    " + line[width:]
        out.append(line)
    return "\n".join(out)


def build_table(rows, avail):
    head, body = rows[0], rows[1:]
    ncols = len(head)
    data = [[Paragraph(inline(c), S["cellhead"]) for c in head]]
    for r in body:
        r = (r + [""] * ncols)[:ncols]
        data.append([Paragraph(inline(c), S["cell"]) for c in r])
    t = Table(data, colWidths=[avail / ncols] * ncols, repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.4, LINE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, SOFT]),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


def md_to_flowables(md, avail):
    flow, i = [], 0
    lines = md.split("\n")
    while i < len(lines):
        ln = lines[i]
        s = ln.strip()

        if not s:
            i += 1
            continue

        if re.fullmatch(r"-{3,}|\*{3,}|_{3,}", s):
            i += 1
            flow.append(Spacer(1, 6))
            continue

        # код
        if s.startswith("```"):
            i += 1
            buf = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            box = Table([[XPreformatted(wrap_code("\n".join(buf)), S["code"])]], colWidths=[avail])
            box.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), SOFT),
                ("BOX", (0, 0), (-1, -1), 0.5, LINE),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]))
            flow += [box, Spacer(1, 8)]
            continue

        # таблица
        if s.startswith("|") and i + 1 < len(lines) and set(lines[i + 1].strip()) <= set("|-: "):
            rows = [split_row(s)]
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(split_row(lines[i]))
                i += 1
            flow += [Spacer(1, 3), build_table(rows, avail), Spacer(1, 9)]
            continue

        # заголовки
        m = re.match(r"^(#{1,4})\s+(.*)$", s)
        if m:
            level, text = len(m.group(1)), m.group(2)
            if level == 1:
                flow += [PageBreak()] if flow else []
                flow += [Paragraph(inline(text), S["h1"])]
            elif level == 2:
                flow += [Paragraph(inline(text), S["h2"])]
            else:
                flow += [Paragraph(inline(text), S["h3"])]
            i += 1
            continue

        # цитата
        if s.startswith(">"):
            flow.append(Paragraph(inline(s.lstrip("> ")), S["quote"]))
            i += 1
            continue

        # списки
        m = re.match(r"^([-*]|\d+\.)\s+(.*)$", s)
        if m:
            while i < len(lines):
                mm = re.match(r"^([-*]|\d+\.)\s+(.*)$", lines[i].strip())
                if not mm:
                    break
                bullet = "•" if mm.group(1) in "-*" else mm.group(1)
                flow.append(Paragraph(inline(mm.group(2)), S["bullet"], bulletText=bullet))
                i += 1
            flow.append(Spacer(1, 5))
            continue

        # абзац
        buf = [s]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r"^(#{1,4}\s|[-*]\s|\d+\.\s|\||```|>)", lines[i].strip()):
            buf.append(lines[i].strip())
            i += 1
        flow.append(Paragraph(inline(" ".join(buf)), S["body"]))
    return flow


def cover():
    return [
        Spacer(1, 30 * mm),
        Paragraph("SM PRODUCTION · АУДИТ И ПРОТОТИП", S["kicker"]),
        Spacer(1, 6),
        Paragraph("Страница «Новогоднее оформление»", S["title"]),
        Paragraph("SEO и юзабилити: что мешает продавать и что делать по приоритетам", S["subtitle"]),
        Spacer(1, 14 * mm),
        Table(
            [[Paragraph("Документ", S["cell"]), Paragraph("Аудит <b>sm-production.ru/novogodnee-oformlenie</b> + план работ P0–P2", S["cell"])],
             [Paragraph("Сезон", S["cell"]), Paragraph("Новогодний сезон 2027", S["cell"])],
             [Paragraph("Дата", S["cell"]), Paragraph("29 октября 2026", S["cell"])],
             [Paragraph("Платформа", S["cell"]), Paragraph("Tilda, React-прототип прилагается отдельным файлом", S["cell"])],
             [Paragraph("Приложения", S["cell"]), Paragraph("prototip/index.html, vizualy/ (20 изображений), audit.md", S["cell"])]],
            colWidths=[32 * mm, 120 * mm], hAlign="LEFT",
            style=TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LINEBELOW", (0, 0), (-1, -1), 0.4, LINE),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ])),
        Spacer(1, 12 * mm),
        Paragraph(
            "Документ содержит: разбор SEO-проблем новогоднего кластера (каннибализация, мета-теги, "
            "разметка, изображения), разбор юзабилити и конверсии, готовые тексты и микроразметку для вставки "
            "в Tilda, а также приоритезированный план работ с метриками результата.", S["body"]),
    ]


def main():
    md = open("/home/user/SM/site_content/05_seo-ux-audit-novogodnee-oformlenie.md", encoding="utf-8").read()
    out = "/home/user/SM/site_content/05_seo-ux-audit-novogodnee-oformlenie.pdf"
    doc = BaseDocTemplate(out, pagesize=A4,
                          leftMargin=18 * mm, rightMargin=16 * mm,
                          topMargin=18 * mm, bottomMargin=16 * mm,
                          title="Аудит страницы «Новогоднее оформление» — SM Production",
                          author="SM Production", lang="ru")
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")

    def deco(canv, d):
        canv.saveState()
        canv.setFont("DJ", 7.6)
        canv.setFillColor(MUT)
        canv.drawString(doc.leftMargin, 9 * mm, "SM Production · аудит страницы «Новогоднее оформление»")
        canv.drawRightString(A4[0] - doc.rightMargin, 9 * mm, f"{d.page}")
        canv.setStrokeColor(LINE)
        canv.setLineWidth(0.4)
        canv.line(doc.leftMargin, 12 * mm, A4[0] - doc.rightMargin, 12 * mm)
        canv.restoreState()

    doc.addPageTemplates([PageTemplate(id="page", frames=[frame], onPage=deco)])
    story = cover()
    body_md = md.split("\n", 1)[1] if md.startswith("# ") else md
    cut = body_md.find("## 1.")
    if cut > 0:
        body_md = body_md[cut:]
    story += md_to_flowables(body_md, doc.width)
    doc.build(story)
    print("PDF:", out)


if __name__ == "__main__":
    main()
