#!/usr/bin/env python3
"""Собирает статью о трендах оформления мероприятий 2027 года в один PDF."""

from __future__ import annotations

import html
import os
import re
from pathlib import Path

# Фиксируем дату метаданных PDF на дату подготовки статьи.
os.environ.setdefault("SOURCE_DATE_EPOCH", "1793318400")

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    KeepTogether,
    LongTable,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

BASE_DIR = Path(__file__).resolve().parent
ARTICLE_PATH = BASE_DIR / "article.md"
OUTPUT_PATH = BASE_DIR / "SM-Production-trendy-oformleniya-meropriyatiy-2027.pdf"
FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")

PAGE_W, PAGE_H = A4
LEFT = 18 * mm
RIGHT = 16 * mm
TOP = 19 * mm
BOTTOM = 18 * mm
CONTENT_W = PAGE_W - LEFT - RIGHT

NAVY = colors.HexColor("#071A35")
BLUE = colors.HexColor("#0755A5")
CYAN = colors.HexColor("#39C8F0")
ICE = colors.HexColor("#EAF7FC")
INK = colors.HexColor("#122033")
MUTED = colors.HexColor("#66758A")
LINE = colors.HexColor("#D9E2EC")
SOFT = colors.HexColor("#F3F7FA")
WHITE = colors.white


def register_fonts() -> None:
    pdfmetrics.registerFont(TTFont("SM", str(FONT_DIR / "DejaVuSans.ttf")))
    pdfmetrics.registerFont(TTFont("SM-B", str(FONT_DIR / "DejaVuSans-Bold.ttf")))
    pdfmetrics.registerFontFamily("SM", normal="SM", bold="SM-B", italic="SM", boldItalic="SM-B")


register_fonts()

STYLES = {
    "cover_kicker": ParagraphStyle(
        "CoverKicker", fontName="SM-B", fontSize=9, leading=12,
        textColor=CYAN, tracking=1.4, spaceAfter=5 * mm,
    ),
    "cover_title": ParagraphStyle(
        "CoverTitle", fontName="SM-B", fontSize=27, leading=33,
        textColor=WHITE, spaceAfter=4 * mm,
    ),
    "cover_subtitle": ParagraphStyle(
        "CoverSubtitle", fontName="SM", fontSize=11.5, leading=17,
        textColor=colors.HexColor("#C8D8EA"), spaceAfter=8 * mm,
    ),
    "cover_meta": ParagraphStyle(
        "CoverMeta", fontName="SM", fontSize=8.5, leading=12,
        textColor=colors.HexColor("#D6E3F1"), alignment=TA_LEFT,
    ),
    "cover_note": ParagraphStyle(
        "CoverNote", fontName="SM", fontSize=8.4, leading=12.5,
        textColor=colors.HexColor("#AFC5DA"), spaceBefore=5 * mm,
    ),
    "toc_title": ParagraphStyle(
        "TOCTitle", fontName="SM-B", fontSize=23, leading=28,
        textColor=NAVY, spaceAfter=8 * mm,
    ),
    "h2": ParagraphStyle(
        "H2", fontName="SM-B", fontSize=16, leading=21,
        textColor=NAVY, spaceBefore=8 * mm, spaceAfter=3.2 * mm,
        keepWithNext=True,
    ),
    "h3": ParagraphStyle(
        "H3", fontName="SM-B", fontSize=11.4, leading=15.5,
        textColor=BLUE, spaceBefore=5 * mm, spaceAfter=2 * mm,
        keepWithNext=True,
    ),
    "body": ParagraphStyle(
        "Body", fontName="SM", fontSize=9.25, leading=14.1,
        textColor=INK, spaceAfter=3.2 * mm, alignment=TA_LEFT,
        allowWidows=0, allowOrphans=0,
    ),
    "lead": ParagraphStyle(
        "Lead", fontName="SM", fontSize=10.2, leading=15.7,
        textColor=colors.HexColor("#263A52"), spaceAfter=4 * mm,
    ),
    "bullet": ParagraphStyle(
        "Bullet", fontName="SM", fontSize=9.1, leading=13.5,
        textColor=INK, leftIndent=6 * mm, firstLineIndent=-3.5 * mm,
        bulletIndent=1.3 * mm, spaceAfter=1.6 * mm,
    ),
    "caption": ParagraphStyle(
        "Caption", fontName="SM", fontSize=7.7, leading=11,
        textColor=MUTED, alignment=TA_CENTER, spaceBefore=1.8 * mm,
    ),
    "table_head": ParagraphStyle(
        "TableHead", fontName="SM-B", fontSize=7.5, leading=10.3,
        textColor=WHITE,
    ),
    "table_cell": ParagraphStyle(
        "TableCell", fontName="SM", fontSize=7.35, leading=10.5,
        textColor=INK,
    ),
}


def inline_markup(text: str) -> str:
    """Минимальная Markdown-разметка, совместимая с Paragraph ReportLab."""
    text = html.escape(text, quote=True)

    def link_repl(match: re.Match[str]) -> str:
        label, href = match.group(1), html.unescape(match.group(2))
        if href.startswith("/"):
            href = "https://sm-production.ru" + href
        return f'<link href="{html.escape(href, quote=True)}" color="#0755A5"><u>{label}</u></link>'

    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link_repl, text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<i>\1</i>", text)
    return text


def plain_markdown(text: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    return text.replace("**", "").replace("*", "").strip()


def strip_front_matter(markdown: str) -> str:
    if markdown.startswith("---\n"):
        end = markdown.find("\n---\n", 4)
        if end >= 0:
            return markdown[end + 5 :]
    return markdown


def split_table_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def build_table(rows: list[list[str]]) -> LongTable:
    ncols = len(rows[0])
    data: list[list[Paragraph]] = []
    for row_index, row in enumerate(rows):
        normalized = (row + [""] * ncols)[:ncols]
        style = STYLES["table_head"] if row_index == 0 else STYLES["table_cell"]
        data.append([Paragraph(inline_markup(cell), style) for cell in normalized])

    if ncols == 3:
        widths = [CONTENT_W * 0.27, CONTENT_W * 0.40, CONTENT_W * 0.33]
    else:
        widths = [CONTENT_W / ncols] * ncols

    table = LongTable(data, colWidths=widths, repeatRows=1, hAlign="LEFT", splitByRow=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BLUE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, SOFT]),
        ("GRID", (0, 0), (-1, -1), 0.4, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return table


def build_image(relative_path: str, alt: str) -> KeepTogether:
    path = BASE_DIR / relative_path
    with PILImage.open(path) as source:
        width_px, height_px = source.size
    width = CONTENT_W
    height = width * height_px / width_px
    max_height = 99 * mm
    if height > max_height:
        height = max_height
        width = height * width_px / height_px
    image = Image(str(path), width=width, height=height)
    image.hAlign = "CENTER"
    return KeepTogether([
        Spacer(1, 2.5 * mm),
        image,
        Paragraph(inline_markup(alt), STYLES["caption"]),
        Spacer(1, 3.2 * mm),
    ])


def markdown_to_flowables(markdown: str) -> list:
    lines = strip_front_matter(markdown).splitlines()
    flowables: list = []
    index = 0
    body_paragraphs = 0

    while index < len(lines):
        stripped = lines[index].strip()
        if not stripped:
            index += 1
            continue

        image_match = re.fullmatch(r"!\[([^]]*)\]\(([^)]+)\)", stripped)
        if image_match:
            alt, relative_path = image_match.groups()
            # Первая иллюстрация уже занимает обложку PDF; в теле не дублируем её.
            if not relative_path.endswith("01-cover-immersive-event.jpg"):
                flowables.append(build_image(relative_path, alt))
            index += 1
            continue

        table_separator = (
            index + 1 < len(lines)
            and stripped.startswith("|")
            and bool(re.fullmatch(r"[|:\-\s]+", lines[index + 1].strip()))
        )
        if table_separator:
            rows = [split_table_row(stripped)]
            index += 2
            while index < len(lines) and lines[index].strip().startswith("|"):
                rows.append(split_table_row(lines[index]))
                index += 1
            flowables.extend([Spacer(1, 1.5 * mm), build_table(rows), Spacer(1, 4 * mm)])
            continue

        heading_match = re.match(r"^(#{1,3})\s+(.*)$", stripped)
        if heading_match:
            level = len(heading_match.group(1))
            title = heading_match.group(2)
            if level == 1:
                # H1 полностью воспроизведён на обложке.
                index += 1
                continue
            paragraph = Paragraph(inline_markup(title), STYLES["h2"] if level == 2 else STYLES["h3"])
            paragraph._outline_text = plain_markdown(title)  # type: ignore[attr-defined]
            flowables.append(paragraph)
            index += 1
            continue

        list_match = re.match(r"^([-*]|\d+\.)\s+(.*)$", stripped)
        if list_match:
            while index < len(lines):
                item_match = re.match(r"^([-*]|\d+\.)\s+(.*)$", lines[index].strip())
                if not item_match:
                    break
                marker, item = item_match.groups()
                bullet = "•" if marker in {"-", "*"} else marker
                flowables.append(Paragraph(inline_markup(item), STYLES["bullet"], bulletText=bullet))
                index += 1
            flowables.append(Spacer(1, 1.6 * mm))
            continue

        if stripped.startswith(">"):
            text = stripped.lstrip("> ")
            quote = Table(
                [[Paragraph(inline_markup(text), STYLES["lead"])]],
                colWidths=[CONTENT_W],
                style=TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), ICE),
                    ("LINEBEFORE", (0, 0), (0, -1), 2.2, CYAN),
                    ("LEFTPADDING", (0, 0), (-1, -1), 9),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]),
            )
            flowables.extend([quote, Spacer(1, 3 * mm)])
            index += 1
            continue

        paragraph_lines = [stripped]
        index += 1
        while index < len(lines):
            candidate = lines[index].strip()
            if not candidate:
                break
            if re.match(r"^(#{1,3})\s+", candidate):
                break
            if re.match(r"^([-*]|\d+\.)\s+", candidate):
                break
            if candidate.startswith("|") or candidate.startswith(">"):
                break
            if re.fullmatch(r"!\[([^]]*)\]\(([^)]+)\)", candidate):
                break
            paragraph_lines.append(candidate)
            index += 1

        style = STYLES["lead"] if body_paragraphs < 2 else STYLES["body"]
        body_paragraphs += 1
        flowables.append(Paragraph(inline_markup(" ".join(paragraph_lines)), style))

    return flowables


class ArticleDocument(BaseDocTemplate):
    def afterFlowable(self, flowable) -> None:  # noqa: N802 - API ReportLab
        if not isinstance(flowable, Paragraph):
            return
        if flowable.style.name not in {"H2", "H3"}:
            return

        level = 0 if flowable.style.name == "H2" else 1
        text = getattr(flowable, "_outline_text", flowable.getPlainText())
        key = f"heading-{self.seq.nextf('heading')}"
        self.canv.bookmarkPage(key)
        self.canv.addOutlineEntry(text, key, level=level, closed=(level == 0))
        if level == 0:
            self.notify("TOCEntry", (level, text, self.page, key))


def draw_cover(canvas, doc) -> None:
    canvas.setCreator("SM Production")
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    canvas.setFillColor(BLUE)
    canvas.rect(0, PAGE_H - 7 * mm, PAGE_W, 7 * mm, fill=1, stroke=0)
    canvas.setFillColor(CYAN)
    canvas.rect(0, PAGE_H - 7 * mm, PAGE_W * 0.32, 7 * mm, fill=1, stroke=0)
    canvas.restoreState()


def draw_body(canvas, doc) -> None:
    canvas.saveState()
    canvas.setStrokeColor(LINE)
    canvas.setLineWidth(0.45)
    canvas.line(LEFT, PAGE_H - 12 * mm, PAGE_W - RIGHT, PAGE_H - 12 * mm)
    canvas.setFont("SM-B", 7.2)
    canvas.setFillColor(BLUE)
    canvas.drawString(LEFT, PAGE_H - 9 * mm, "SM PRODUCTION")
    canvas.setFont("SM", 7.2)
    canvas.setFillColor(MUTED)
    canvas.drawRightString(PAGE_W - RIGHT, PAGE_H - 9 * mm, "Тренды оформления мероприятий · 2027")

    canvas.line(LEFT, 12 * mm, PAGE_W - RIGHT, 12 * mm)
    canvas.setFont("SM", 7.1)
    canvas.drawString(LEFT, 8.5 * mm, "sm-production.ru")
    canvas.drawRightString(PAGE_W - RIGHT, 8.5 * mm, str(doc.page))
    canvas.restoreState()


def cover_story() -> list:
    hero = BASE_DIR / "images" / "01-cover-immersive-event.jpg"
    hero_width = CONTENT_W
    hero_height = hero_width * 675 / 1200
    image = Image(str(hero), width=hero_width, height=hero_height)
    image.hAlign = "CENTER"

    meta = Table([
        [
            Paragraph("<b>Автор</b><br/>SM Production", STYLES["cover_meta"]),
            Paragraph("<b>Дата</b><br/>30 октября 2026", STYLES["cover_meta"]),
            Paragraph("<b>Чтение</b><br/>≈ 12 минут", STYLES["cover_meta"]),
        ]
    ], colWidths=[CONTENT_W / 3] * 3)
    meta.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#0E294A")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#294766")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#294766")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))

    return [
        Spacer(1, 7 * mm),
        Paragraph("SM PRODUCTION · БЛОГ", STYLES["cover_kicker"]),
        Paragraph("Что будет популярно в оформлении мероприятий в 2027 году", STYLES["cover_title"]),
        Paragraph(
            "9 практических трендов: от цельной сценографии и модульных систем до персонализации, "
            "интерактива и пространств для вертикального видео.",
            STYLES["cover_subtitle"],
        ),
        image,
        Spacer(1, 5 * mm),
        meta,
        Paragraph(
            "Прогноз подготовлен осенью 2026 года. Иллюстрации внутри документа являются "
            "концептуальными и не представлены как реализованные проекты.",
            STYLES["cover_note"],
        ),
    ]


def build_pdf() -> Path:
    markdown = ARTICLE_PATH.read_text(encoding="utf-8")

    document = ArticleDocument(
        str(OUTPUT_PATH),
        pagesize=A4,
        leftMargin=LEFT,
        rightMargin=RIGHT,
        topMargin=TOP,
        bottomMargin=BOTTOM,
        title="Что будет популярно в оформлении мероприятий в 2027 году",
        author="SM Production",
        subject="Тренды оформления мероприятий 2027 года",
        keywords="оформление мероприятий, event-дизайн, тренды 2027, SM Production",
        lang="ru-RU",
    )

    cover_frame = Frame(LEFT, 15 * mm, CONTENT_W, PAGE_H - 27 * mm, id="cover-frame", showBoundary=0)
    body_frame = Frame(LEFT, BOTTOM, CONTENT_W, PAGE_H - TOP - BOTTOM, id="body-frame", showBoundary=0)
    document.addPageTemplates([
        PageTemplate(id="cover", frames=[cover_frame], onPage=draw_cover),
        PageTemplate(id="body", frames=[body_frame], onPage=draw_body),
    ])

    toc = TableOfContents()
    toc.levelStyles = [
        ParagraphStyle(
            "TOCLevel0", fontName="SM", fontSize=9.2, leading=14,
            textColor=INK, leftIndent=0, firstLineIndent=0,
            rightIndent=8 * mm, spaceBefore=1.6 * mm,
        )
    ]
    toc.dotsMinLevel = 0

    story = cover_story()
    story.extend([
        NextPageTemplate("body"),
        PageBreak(),
        Paragraph("Содержание", STYLES["toc_title"]),
        Paragraph(
            "Прогноз и практические рекомендации для брендов, организаторов и площадок.",
            STYLES["lead"],
        ),
        Spacer(1, 2 * mm),
        toc,
        PageBreak(),
    ])
    story.extend(markdown_to_flowables(markdown))

    document.multiBuild(story)
    return OUTPUT_PATH


if __name__ == "__main__":
    output = build_pdf()
    print(output)
