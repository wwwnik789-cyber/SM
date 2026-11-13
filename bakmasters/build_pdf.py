"""Сборка PDF из markdown-документов BAK MASTERS.

Нужен, чтобы отдать материалы в мессенджер: .md на телефоне не читается.

    .venv/bin/python bakmasters/build_pdf.py

Скрипт собирает два файла:
  bakmasters/pdf/BAK-MASTERS-SEO.pdf       — для Кристины (SEO, альты, инструкция)
  bakmasters/pdf/BAK-MASTERS-audit.pdf     — аудит сайта

Шрифты Montserrat берутся из переменного TTF в репозитории и на лету
превращаются в статические веса. В git бинарники не попадают.
"""
import os
import re
import sys

from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont as RLFont
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, NextPageTemplate, CondPageBreak,
)
from reportlab.platypus.flowables import HRFlowable
from reportlab.platypus.tableofcontents import TableOfContents

BASE = os.path.dirname(os.path.abspath(__file__))
VAR_FONT = os.path.join(os.path.dirname(BASE),
                        "banners/anikom-arena-3000x2500-concepts/source/Montserrat-Variable.ttf")
FONT_DIR = "/tmp/bakmasters-fonts"
OUT_DIR = os.path.join(BASE, "pdf")

# --- палитра: тёплое дерево и смола, как на сайте ---
INK = colors.HexColor("#1E1A17")
INK_SOFT = colors.HexColor("#4A423C")
WOOD = colors.HexColor("#8C5A32")
AMBER = colors.HexColor("#C08A4A")
SAND = colors.HexColor("#F3EDE4")
LINE = colors.HexColor("#D9CEC1")
MUTED = colors.HexColor("#8A8078")
DARK = colors.HexColor("#16110D")

PAGE_W, PAGE_H = 595.28, 841.89
MARGIN_X = 52
MARGIN_TOP = 66
MARGIN_BOT = 58
TEXT_W = PAGE_W - 2 * MARGIN_X


def prepare_fonts():
    os.makedirs(FONT_DIR, exist_ok=True)
    weights = {"Montserrat": 400, "Montserrat-Medium": 500,
               "Montserrat-SemiBold": 600, "Montserrat-Bold": 700}
    for name, wght in weights.items():
        out = os.path.join(FONT_DIR, f"{name}.ttf")
        if not os.path.exists(out):
            f = TTFont(VAR_FONT)
            axes = {"wght": wght}
            if "ital" in [a.axisTag for a in f["fvar"].axes]:
                axes["ital"] = 0
            inst = instantiateVariableFont(f, axes, updateFontNames=True)
            inst.save(out)
        pdfmetrics.registerFont(RLFont(name, out))
    # DejaVu: моноширинный для кода и глиф для чекбокса
    pdfmetrics.registerFont(RLFont("Mono", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"))
    pdfmetrics.registerFont(RLFont("DejaVu", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
    pdfmetrics.registerFontFamily("Montserrat", normal="Montserrat", bold="Montserrat-Bold",
                                  italic="Montserrat", boldItalic="Montserrat-Bold")


def styles():
    ss = getSampleStyleSheet()
    S = {}
    S["body"] = ParagraphStyle(
        "body", fontName="Montserrat", fontSize=9.4, leading=14.6,
        textColor=INK, spaceAfter=7, alignment=TA_LEFT,
    )
    S["h1toc"] = ParagraphStyle(
        "H1nolink", fontName="Montserrat-Bold", fontSize=19, leading=23,
        textColor=WOOD, spaceBefore=4, spaceAfter=13,
    )
    S["h1"] = ParagraphStyle(
        "H1", fontName="Montserrat-Bold", fontSize=19, leading=23,
        textColor=WOOD, spaceBefore=4, spaceAfter=13,
    )
    S["h2"] = ParagraphStyle(
        "H2", fontName="Montserrat-Bold", fontSize=13, leading=17,
        textColor=INK, spaceBefore=15, spaceAfter=7,
    )
    S["h3"] = ParagraphStyle(
        "H3", fontName="Montserrat-SemiBold", fontSize=10.4, leading=14.5,
        textColor=WOOD, spaceBefore=11, spaceAfter=4,
    )
    S["bullet"] = ParagraphStyle(
        "bullet", parent=S["body"], leftIndent=13, bulletIndent=3,
        spaceAfter=4.5, bulletFontName="Montserrat", bulletFontSize=8,
    )
    S["cell"] = ParagraphStyle(
        "cell", fontName="Montserrat", fontSize=7.9, leading=10.6, textColor=INK,
    )
    S["cellh"] = ParagraphStyle(
        "cellh", fontName="Montserrat-SemiBold", fontSize=7.9, leading=10.6,
        textColor=colors.white,
    )
    S["label"] = ParagraphStyle(
        "label", fontName="Montserrat-Bold", fontSize=7.4, leading=10,
        textColor=WOOD, spaceBefore=6, spaceAfter=3,
    )
    S["quote"] = ParagraphStyle(
        "quote", parent=S["body"], fontName="Montserrat-Medium", textColor=INK_SOFT,
        fontSize=9.2, leading=14, leftIndent=10,
    )
    S["toc1"] = ParagraphStyle("toc1", fontName="Montserrat-SemiBold", fontSize=11.5,
                               leading=30, textColor=INK, spaceBefore=4)
    S["toc2"] = ParagraphStyle("toc2", fontName="Montserrat", fontSize=9.3,
                               leading=17.5, textColor=INK_SOFT, leftIndent=16)
    return S


S = styles()


# ---------------------------------------------------------------- инлайн
def inline(text):
    """Экранирование + разметка **жирного**, `кода`, *курсива*."""
    text = (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
    text = re.sub(r"`([^`]+)`",
                  r'<font name="Mono" size="8.4" color="#6B4A2F">\1</font>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", text)
    text = text.replace("- [ ]", '<font name="DejaVu">\u2610</font>')
    return text


# ---------------------------------------------------------------- таблицы
def split_row(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]


def build_table(rows):
    header, body = rows[0], rows[1:]
    ncol = len(header)
    # вес колонки — по длине самого длинного текста, но не больше 3.2x среднего
    lens = []
    for c in range(ncol):
        vals = [len(header[c])] + [len(r[c]) for r in body if c < len(r)]
        lens.append(max(6, min(max(vals), 46)))
    total = sum(lens)
    widths = [max(46, TEXT_W * l / total) for l in lens]
    k = TEXT_W / sum(widths)
    widths = [w * k for w in widths]

    data = [[Paragraph(inline(c), S["cellh"]) for c in header]]
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), WOOD),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    for i, r in enumerate(body, start=1):
        r = r + [""] * (ncol - len(r))
        data.append([Paragraph(inline(c), S["cell"]) for c in r[:ncol]])
        if i % 2 == 0:
            style.append(("BACKGROUND", (0, i), (-1, i), SAND))
    return Table(data, colWidths=widths, repeatRows=1, style=TableStyle(style),
                 hAlign="LEFT", spaceBefore=6, spaceAfter=10)


# ---------------------------------------------------------------- блоки
def box(flow, bg=SAND, bar=AMBER, pad=9):
    """Текст в рамке с акцентной полосой слева — для «скопируй это»."""
    t = Table([[flow]], colWidths=[TEXT_W], hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("LINEBEFORE", (0, 0), (0, -1), 2.4, bar),
        ("LEFTPADDING", (0, 0), (-1, -1), pad + 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), pad),
        ("TOPPADDING", (0, 0), (-1, -1), pad),
        ("BOTTOMPADDING", (0, 0), (-1, -1), pad),
    ]))
    return t


FENCE_STYLE = ParagraphStyle("fence", fontName="Montserrat-Medium", fontSize=9.1,
                             leading=14, textColor=INK)


def parse_blocks(md):
    """Markdown → список примитивов (тип, данные)."""
    lines = md.split("\n")
    out, i = [], 0
    while i < len(lines):
        ln = lines[i]
        s = ln.strip()

        if s.startswith("```"):
            i += 1
            buf = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            out.append(("fence", "\n".join(buf).strip("\n")))
            continue

        if s.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s:\-|]+\|?$", lines[i + 1].strip()):
            rows = [split_row(s)]
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(split_row(lines[i]))
                i += 1
            out.append(("table", rows))
            continue

        if s in ("---", "***", "___"):
            out.append(("rule", None))
            i += 1
            continue

        m = re.match(r"^(#{1,4})\s+(.*)$", s)
        if m:
            out.append((f"h{len(m.group(1))}", m.group(2).strip()))
            i += 1
            continue

        if re.match(r"^[-*]\s+", s):
            items = []
            while i < len(lines) and re.match(r"^[-*]\s+", lines[i].strip()):
                items.append(re.sub(r"^[-*]\s+", "", lines[i].strip()))
                i += 1
            out.append(("ul", items))
            continue

        if re.match(r"^\d+\.\s+", s):
            items = []
            while i < len(lines) and re.match(r"^\d+\.\s+", lines[i].strip()):
                items.append(re.sub(r"^\d+\.\s+", "", lines[i].strip()))
                i += 1
            out.append(("ol", items))
            continue

        if s.startswith(">"):
            buf = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip().lstrip(">").strip())
                i += 1
            out.append(("quote", " ".join(buf)))
            continue

        if not s:
            i += 1
            continue

        # абзац: склеиваем строки до пустой
        buf = [s]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(
                r"^(#{1,4}\s|[-*]\s|\d+\.\s|\||>|```|---$)", lines[i].strip()):
            buf.append(lines[i].strip())
            i += 1
        out.append(("p", " ".join(buf)))
    return out


def render(blocks, skip_h1=False):
    """Возвращает поток, где заголовки склеены с первым блоком — не висят внизу."""
    seq = []
    for kind, data in blocks:
        if kind == "h1":
            if skip_h1:
                continue
            seq.append(("h1", Paragraph(inline(data), S["h1"])))
            seq.append(("other", HRFlowable(width="100%", thickness=1.1, color=AMBER,
                                            spaceBefore=-6, spaceAfter=13)))
        elif kind == "h2":
            seq.append(("h2", Paragraph(inline(data), S["h2"])))
        elif kind == "h3":
            seq.append(("h3", Paragraph(inline(data), S["h3"])))
        elif kind == "h4":
            seq.append(("h3", Paragraph(inline(data), S["h3"])))
        elif kind == "p":
            txt = data.strip()
            is_label = bool(re.fullmatch(r"\*\*[^*]{1,60}:\*\*", txt)) and len(txt) <= 70
            if is_label:
                seq.append(("label", Paragraph(inline(txt), S["label"])))
            else:
                seq.append(("other", Paragraph(inline(txt), S["body"])))
        elif kind == "ul":
            for it in data:
                seq.append(("other", Paragraph(inline(it), S["bullet"], bulletText="\u2022")))
            seq.append(("other", Spacer(1, 3)))
        elif kind == "ol":
            for n, it in enumerate(data, 1):
                st = ParagraphStyle(f"ol{n}", parent=S["bullet"], bulletFontName="Montserrat-SemiBold",
                                    bulletFontSize=8.6, bulletColor=WOOD)
                seq.append(("other", Paragraph(inline(it), st, bulletText=f"{n}.")))
            seq.append(("other", Spacer(1, 3)))
        elif kind == "quote":
            seq.append(("other", box(Paragraph(inline(data), S["quote"]),
                                     bg=colors.HexColor("#FAF6F1"))))
            seq.append(("other", Spacer(1, 8)))
        elif kind == "fence":
            fp = [Paragraph(inline(l) if l.strip() else "&nbsp;", FENCE_STYLE)
                  for l in data.split("\n")]
            seq.append(("fence", box(fp)))
            seq.append(("other", Spacer(1, 8)))
        elif kind == "table":
            seq.append(("table", build_table(data)))
        elif kind == "rule":
            seq.append(("other", HRFlowable(width="100%", thickness=0.7, color=LINE,
                                            spaceBefore=6, spaceAfter=10)))

    # склейка: заголовок или подпись не должны оставаться внизу страницы одни
    flow, pending = [], []

    def flush_with(item):
        nonlocal pending
        if pending:
            short_table = isinstance(item, Table) and len(item._cellvalues) <= 7
            if isinstance(item, Table) and not short_table:
                flow.extend(pending)          # длинная таблица сама рвётся
                flow.append(item)
            else:
                flow.append(KeepTogether(pending + [item]))
            pending = []
        else:
            flow.append(item)

    for kind, f in seq:
        if kind in ("h1", "h2", "h3", "label"):
            if pending:
                # заголовок без пары: если до низа меньше 60 мм — переносим
                flow.append(CondPageBreak(60 * mm))
                flow.extend(pending)
            pending.append(f)
            continue
        flush_with(f)
    if pending:
        flow.extend(pending)
    return flow


# ---------------------------------------------------------------- документ
class Doc(BaseDocTemplate):
    def __init__(self, path, title, subtitle, footer_note, **kw):
        super().__init__(path, pagesize=(PAGE_W, PAGE_H),
                         leftMargin=MARGIN_X, rightMargin=MARGIN_X,
                         topMargin=MARGIN_TOP, bottomMargin=MARGIN_BOT,
                         title=title.replace("\n", " ").strip(),
                         author="SM Production",
                         subject=subtitle.replace("\n", " ").strip(),
                         **kw)
        self.doc_title = title
        self.doc_subtitle = subtitle
        self.footer_note = footer_note
        self.toc = TableOfContents()
        self.toc.levelStyles = [S["toc1"]]
        self.toc.dotsMinLevel = 0
        frame = Frame(MARGIN_X, MARGIN_BOT, TEXT_W, PAGE_H - MARGIN_TOP - MARGIN_BOT,
                      id="main", leftPadding=0, rightPadding=0,
                      topPadding=0, bottomPadding=0)
        self.addPageTemplates([PageTemplate(id="page", frames=[frame], onPage=self.decorate)])

    def decorate(self, canv, doc):
        if doc.page == 1:
            return
        canv.saveState()
        # колонтитул
        canv.setFont("Montserrat-SemiBold", 7.2)
        canv.setFillColor(MUTED)
        canv.drawString(MARGIN_X, PAGE_H - 38, "BAK MASTERS")
        canv.setFont("Montserrat", 7.2)
        canv.drawRightString(PAGE_W - MARGIN_X, PAGE_H - 38,
                             self.doc_title.replace("\n", " "))
        canv.setStrokeColor(LINE)
        canv.setLineWidth(0.5)
        canv.line(MARGIN_X, PAGE_H - 44, PAGE_W - MARGIN_X, PAGE_H - 44)
        # подвал
        canv.line(MARGIN_X, MARGIN_BOT - 14, PAGE_W - MARGIN_X, MARGIN_BOT - 14)
        canv.setFont("Montserrat", 7.2)
        canv.setFillColor(MUTED)
        canv.drawString(MARGIN_X, MARGIN_BOT - 26, self.footer_note)
        canv.setFont("Montserrat-SemiBold", 8.2)
        canv.setFillColor(WOOD)
        canv.drawRightString(PAGE_W - MARGIN_X, MARGIN_BOT - 26, str(doc.page))
        canv.restoreState()

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph):
            name = flowable.style.name
            if name in ("H1", "H2"):
                level = 0 if name == "H1" else 1
                text = flowable.getPlainText()
                key = f"bm{level}-{self.page}-{abs(hash(text)) % 100000}"
                self.canv.bookmarkPage(key)
                self.canv.addOutlineEntry(text, key, level=level, closed=(level == 1))
                if level == 0:
                    self.notify("TOCEntry", (0, text, self.page, key))


def cover(canv, doc, title, subtitle, contents, meta_lines):
    canv.saveState()
    canv.setFillColor(DARK)
    canv.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    # тонкая рамка
    canv.setStrokeColor(colors.HexColor("#3A2C21"))
    canv.setLineWidth(0.7)
    canv.rect(26, 26, PAGE_W - 52, PAGE_H - 52, stroke=1, fill=0)

    y = PAGE_H - 118
    canv.setFillColor(AMBER)
    canv.setFont("Montserrat-Bold", 11)
    canv.drawString(MARGIN_X, y, "BAK MASTERS")
    canv.setFillColor(colors.HexColor("#6E5C4C"))
    canv.setFont("Montserrat", 8.4)
    canv.drawString(MARGIN_X + 92, y, "изделия из дерева и эпоксидной смолы")

    y -= 72
    canv.setFillColor(colors.HexColor("#F6F1EA"))
    canv.setFont("Montserrat-Bold", 34)
    for line in title.split("\n"):
        canv.drawString(MARGIN_X, y, line)
        y -= 42

    y -= 6
    canv.setStrokeColor(AMBER)
    canv.setLineWidth(2.4)
    canv.line(MARGIN_X, y, MARGIN_X + 74, y)

    y -= 34
    canv.setFillColor(colors.HexColor("#BFAF9E"))
    canv.setFont("Montserrat-Medium", 11.5)
    for line in subtitle.split("\n"):
        canv.drawString(MARGIN_X, y, line)
        y -= 18

    # состав
    y -= 40
    canv.setFillColor(colors.HexColor("#6E5C4C"))
    canv.setFont("Montserrat-SemiBold", 8.2)
    canv.drawString(MARGIN_X, y, "В ДОКУМЕНТЕ")
    y -= 24
    for num, name, pages in contents:
        canv.setFillColor(AMBER)
        canv.setFont("Montserrat-Bold", 9.4)
        canv.drawString(MARGIN_X, y, num)
        canv.setFillColor(colors.HexColor("#E6DCD1"))
        canv.setFont("Montserrat-Medium", 10.6)
        canv.drawString(MARGIN_X + 26, y, name)
        canv.setFillColor(colors.HexColor("#6E5C4C"))
        canv.setFont("Montserrat", 9.4)
        canv.drawRightString(PAGE_W - MARGIN_X, y, pages)
        y -= 26

    # подвал обложки
    canv.setFillColor(colors.HexColor("#8A7A6A"))
    canv.setFont("Montserrat", 8.6)
    yy = 96
    for line in meta_lines:
        canv.drawString(MARGIN_X, yy, line)
        yy -= 14

    canv.setFillColor(AMBER)
    canv.setFont("Montserrat-Bold", 8.6)
    canv.drawRightString(PAGE_W - MARGIN_X, 96, "bakmasters.ru")
    canv.restoreState()


def make_pdf(path, title, subtitle, contents, meta_lines, docs, footer_note,
             lead=None, checklist=False):
    """docs — список (md_path, skip_h1)."""
    doc = Doc(path, title, subtitle, footer_note)

    def on_first(canv, d):
        cover(canv, d, title, subtitle, contents, meta_lines)

    doc.addPageTemplates([
        PageTemplate(id="cover", frames=[
            Frame(MARGIN_X, MARGIN_BOT, TEXT_W, PAGE_H - MARGIN_TOP - MARGIN_BOT, id="cf")],
            onPage=on_first),
    ])
    # обложка первой, дальше обычная страница
    doc.pageTemplates.insert(0, doc.pageTemplates.pop())

    story = [NextPageTemplate("page"), PageBreak()]
    if len(docs) > 1:                      # содержание нужно только сборнику
        story.append(Paragraph("Содержание", S["h1toc"]))
        story.append(HRFlowable(width="100%", thickness=1.1, color=AMBER,
                                spaceBefore=-6, spaceAfter=16))
        if lead:
            story.append(box(Paragraph(inline(lead), S["quote"])))
            story.append(Spacer(1, 12))
        story.append(doc.toc)
        story.append(PageBreak())
    elif lead:
        story.append(box(Paragraph(inline(lead), S["quote"])))
        story.append(Spacer(1, 14))

    for idx, (md_path, skip_h1) in enumerate(docs):
        with open(md_path, encoding="utf-8") as f:
            blocks = parse_blocks(f.read())
        story.extend(render(blocks, skip_h1=skip_h1))
        if idx < len(docs) - 1:
            story.append(PageBreak())

    if checklist:
        story.append(PageBreak())
        story.append(Paragraph("Чек-лист", S["h1"]))
        story.append(HRFlowable(width="100%", thickness=1.1, color=AMBER,
                                spaceBefore=-6, spaceAfter=8))
        story.append(Paragraph(
            "Распечатайте эту страницу или отмечайте прямо в PDF. Сначала — первые "
            "три строки: они про потерянные заказы, а не про поиск.", S["body"]))
        story.append(Spacer(1, 6))
        story.append(checklist_flow())

    doc.multiBuild(story)
    return path



CHECKLIST = [
    ("Ссылки .su → относительные (/shop, /toorder, /aboutus, /privacypolicy)", "20 мин"),
    ("VK и Telegram в шапке: vk.com/bak_mast и t.me/bak_masters", "10 мин"),
    ("Один телефон, один Telegram, один WhatsApp на всех страницах", "20 мин"),
    ("Title и Description: главная", "5 мин"),
    ("Title и Description: каталог /shop", "5 мин"),
    ("Title и Description: на заказ /toorder", "5 мин"),
    ("Title и Description: о нас /aboutus", "5 мин"),
    ("Title и Description: доставка /delivery_and_payment", "5 мин"),
    ("Title и Description: контакты /contacts", "5 мин"),
    ("Title и Description: политика /privacypolicy", "5 мин"),
    ("H1 назначен стилем на каждой из 7 страниц", "15 мин"),
    ("Картинка для соцсетей 1200 × 630 в настройках сайта", "15 мин"),
    ("9 страниц-копий page…html закрыты от индексации", "15 мин"),
    ("Альты: главная", "20 мин"),
    ("Альты: карточки товаров", "40 мин"),
    ("Title и Description: 37 карточек товаров", "1 час"),
    ("Сотрудничество: SEO прописано до публикации", "5 мин"),
    ("Вебмастер: подтверждение + «Переезд сайта»", "20 мин"),
    ("Search Console: подтверждение + «Изменение адреса»", "20 мин"),
]


def checklist_flow():
    rows = [[Paragraph("\u2610", ParagraphStyle("cb", fontName="DejaVu", fontSize=11, textColor=WOOD)),
             Paragraph("<b>" + inline(t) + "</b>", S["cell"]),
             Paragraph(inline(m), S["cell"])] for t, m in CHECKLIST]
    head = [Paragraph("", S["cellh"]), Paragraph("Что сделать", S["cellh"]),
            Paragraph("Время", S["cellh"])]
    t = Table([head] + rows, colWidths=[22, TEXT_W - 22 - 52, 52], repeatRows=1, hAlign="LEFT")
    st = [("BACKGROUND", (0, 0), (-1, 0), WOOD),
          ("VALIGN", (0, 0), (-1, -1), "TOP"),
          ("LINEBELOW", (0, 0), (-1, -1), 0.4, LINE),
          ("LEFTPADDING", (0, 0), (-1, -1), 5),
          ("RIGHTPADDING", (0, 0), (-1, -1), 5),
          ("TOPPADDING", (0, 0), (-1, -1), 4.5),
          ("BOTTOMPADDING", (0, 0), (-1, -1), 4.5),
          ("ALIGN", (2, 0), (2, -1), "RIGHT")]
    for i in range(1, len(rows) + 1):
        if i % 2 == 0:
            st.append(("BACKGROUND", (0, i), (-1, i), SAND))
    t.setStyle(TableStyle(st))
    return t


def main():
    prepare_fonts()
    os.makedirs(OUT_DIR, exist_ok=True)

    p1 = os.path.join(OUT_DIR, "BAK-MASTERS-SEO.pdf")
    make_pdf(
        p1,
        title="SEO и альты\nпосле переезда на .ru",
        subtitle="Что заполнить в Тильде и в каком порядке.\nГотовые тексты — копировать и вставлять.",
        contents=[
            ("1", "SEO страниц и товаров", "7 страниц + 37 карточек"),
            ("2", "Альты изображений", "правила и готовые тексты"),
            ("3", "Инструкция по Тильде", "куда кликать, пошагово"),
        ],
        meta_lines=["Собрано 30 октября 2026", "Документ подготовлен SM Production"],
        docs=[(os.path.join(BASE, "01-seo-stranic.md"), False),
              (os.path.join(BASE, "02-alty-izobrazhenij.md"), False),
              (os.path.join(BASE, "03-instrukciya-tilda.md"), False)],
        footer_note="BAK MASTERS · SEO и альты · bakmasters.ru",
        lead="Сначала прочитайте третий раздел — «Инструкция по Тильде»: там всего четыре "
             "поля на страницу, и станет понятно, что делать. Тексты для копирования — "
             "в первом разделе, альты — во втором.",
        checklist=True,
    )

    p2 = os.path.join(OUT_DIR, "BAK-MASTERS-audit.pdf")
    make_pdf(
        p2,
        title="Аудит сайта\nbakmasters.ru",
        subtitle="Что сломано после переезда с .su,\nв каком порядке чинить и сколько это займёт.",
        contents=[("1", "Критические ошибки", "P0–P3, с адресами")],
        meta_lines=["Проверено 30 октября 2026", "Документ подготовлен SM Production"],
        docs=[(os.path.join(BASE, "04-kriticheskie-oshibki.md"), False)],
        footer_note="BAK MASTERS · аудит сайта · bakmasters.ru",
        lead="Проверено снаружи: доступные страницы, sitemap.xml, robots.txt, карточки товаров. "
             "Первые два пункта — не про SEO, а про потерянные заказы: на них стоит "
             "потратить первые полчаса.",
    )

    for p in (p1, p2):
        print(f"{p}  {os.path.getsize(p) // 1024} KB")


if __name__ == "__main__":
    sys.exit(main())
