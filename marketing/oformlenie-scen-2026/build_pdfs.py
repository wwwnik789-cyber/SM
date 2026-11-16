#!/usr/bin/env python3
"""Собирает два PDF для услуги «Оформление сцен».

  1. oformlenie-scen-pravki-stranicy.pdf — правки страницы: выдержки с сайта,
     готовые формулировки, приоритеты.
  2. oformlenie-scen-direct.pdf — кампания в Яндекс.Директе: группы, ключи,
     объявления, минус-слова, настройки, бюджет.

Источник текста — page-audit.md и direct-plan.md (разметка описана ниже),
данные кампании — keywords.csv, ads.csv, extensions.csv, minus-words.txt.

    .venv/bin/python marketing/oformlenie-scen-2026/build_pdfs.py
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

from fontTools.ttLib import TTFont as FTFont
from fontTools.varLib.instancer import instantiateVariableFont
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
FONT_VF = REPO / "banners/anikom-arena-3000x2500-concepts/source/Montserrat-Variable.ttf"
FONT_DIR = Path("/tmp/fonts-scen")

PAGE_W, PAGE_H = A4
ML, MR = 52, 52
MT, MB = 96, 58
CONTENT_W = PAGE_W - ML - MR

NAVY = HexColor("#0F2436")
NAVY_D = HexColor("#081824")
CORAL = HexColor("#D2453C")
INK = HexColor("#1B2430")
MUTED = HexColor("#7A8794")
LINE = HexColor("#D9DEE3")
PAPER = HexColor("#F5F2EB")
TINT = HexColor("#E9F0F4")
WHITE = HexColor("#FFFFFF")

FONTS = {}


def register_fonts() -> None:
    FONT_DIR.mkdir(parents=True, exist_ok=True)
    for weight, alias in [(400, "R"), (500, "M"), (600, "S"), (700, "B")]:
        path = FONT_DIR / f"M{alias}.ttf"
        if not path.exists():
            inst = instantiateVariableFont(FTFont(str(FONT_VF)), {"wght": weight},
                                           updateFontNames=True)
            inst.save(str(path))
        pdfmetrics.registerFont(TTFont(f"M{alias}", str(path)))
        FONTS[alias] = f"M{alias}"


def runs(text: str) -> list[tuple[str, bool]]:
    """Разбирает **жирный** и `код` в список (фрагмент, жирный) кусков."""
    out: list[tuple[str, bool]] = []
    for i, chunk in enumerate(re.split(r"(\*\*.+?\*\*|`.+?`)", text)):
        if not chunk:
            continue
        if chunk.startswith("**") and chunk.endswith("**"):
            out.append((chunk[2:-2], True))
        elif chunk.startswith("`") and chunk.endswith("`"):
            out.append((chunk[1:-1], True))
        else:
            out.append((chunk, False))
    return out


def wrap_rich(text: str, size: float, width: float,
              base: str = "R", bold: str = "S") -> list[list[tuple[str, bool]]]:
    """Перенос строк с сохранением жирных фрагментов."""
    words: list[tuple[str, bool]] = []
    for chunk, is_bold in runs(text):
        for w in chunk.split(" "):
            if w != "" or not words:
                words.append((w, is_bold))
    lines, cur, cur_w = [], [], 0.0
    space = pdfmetrics.stringWidth(" ", FONTS[base], size)
    for word, is_bold in words:
        f = FONTS[bold] if is_bold else FONTS[base]
        w_w = pdfmetrics.stringWidth(word, f, size)
        add = w_w if not cur else space + w_w
        if cur and cur_w + add > width:
            lines.append(cur)
            cur, cur_w = [(word, is_bold)], w_w
        else:
            cur.append((word, is_bold))
            cur_w += add
    if cur:
        lines.append(cur)
    return lines


def wrap(text: str, font: str, size: float, width: float) -> list[str]:
    font = FONTS.get(font, font)
    lines: list[str] = []
    for para in text.split("\n"):
        words, cur = para.split(), ""
        for w in words:
            probe = f"{cur} {w}".strip()
            if pdfmetrics.stringWidth(probe, font, size) <= width or not cur:
                cur = probe
            else:
                lines.append(cur)
                cur = w
        lines.append(cur)
    return lines or [""]


class Doc:
    def __init__(self, path: Path, kicker: str, title: str, subtitle: str,
                 meta: list[tuple[str, str]], note: str, footer: str):
        self.c = canvas.Canvas(str(path), pagesize=A4)
        self.c.setTitle(title + " — SM-Production")
        self.c.setAuthor("SM-Production")
        self.path = path
        self.kicker, self.title, self.subtitle = kicker, title, subtitle
        self.footer = footer
        self.page = 0
        self.cover(meta, note)
        self.new_page()

    # ── каркас ──────────────────────────────────────────────────────────────
    def cover(self, meta, note) -> None:
        c = self.c
        c.setFillColor(NAVY)
        c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
        c.setFillColor(CORAL)
        c.rect(0, PAGE_H - 12, PAGE_W, 12, stroke=0, fill=1)

        y = PAGE_H - 118
        c.setFillColor(HexColor("#8FA6B8"))
        c.setFont(FONTS["S"], 10)
        c.drawString(ML, y, self.kicker.upper())
        y -= 64
        c.setFillColor(WHITE)
        for line in wrap(self.title, "B", 34, CONTENT_W - 20):
            c.setFont(FONTS["B"], 34)
            c.drawString(ML, y, line)
            y -= 42
        y -= 6
        c.setFillColor(HexColor("#C6D3DE"))
        for line in wrap(self.subtitle, "R", 14, CONTENT_W - 40):
            c.setFont(FONTS["R"], 14)
            c.drawString(ML, y, line)
            y -= 21

        # метаданные — внизу обложки
        y = 300
        for label, value in meta:
            c.setFillColor(HexColor("#7E94A6"))
            c.setFont(FONTS["S"], 9)
            c.drawString(ML, y, label.upper())
            c.setFillColor(WHITE)
            c.setFont(FONTS["M"], 12.5)
            c.drawString(ML + 150, y, value)
            y -= 26

        c.setFillColor(HexColor("#22384A"))
        c.rect(0, 0, PAGE_W, 116, stroke=0, fill=1)
        c.setFillColor(HexColor("#93A8B8"))
        c.setFont(FONTS["R"], 9.5)
        yy = 78
        for line in wrap(note, "R", 9.5, CONTENT_W):
            c.drawString(ML, yy, line)
            yy -= 14

    def new_page(self) -> None:
        self.c.showPage()
        self.page += 1
        c = self.c
        c.setFillColor(WHITE)
        c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
        c.setFillColor(MUTED)
        c.setFont(FONTS["S"], 8)
        c.drawString(ML, PAGE_H - 52, self.kicker.upper())
        c.setFont(FONTS["R"], 8)
        c.drawRightString(PAGE_W - MR, PAGE_H - 52, f"{self.page:02d}")
        c.setStrokeColor(LINE)
        c.setLineWidth(0.6)
        c.line(ML, PAGE_H - 62, PAGE_W - MR, PAGE_H - 62)
        c.setFillColor(MUTED)
        c.setFont(FONTS["R"], 7.5)
        c.drawString(ML, 30, self.footer)
        self.y = PAGE_H - MT

    def need(self, h: float) -> None:
        if self.y - h < MB:
            self.new_page()

    def gap(self, h: float) -> None:
        self.y -= h

    # ── блоки ───────────────────────────────────────────────────────────────
    def h1(self, text: str) -> None:
        self.need(150)
        self.y -= 6
        self.y -= 12
        self.c.setFillColor(NAVY_D)
        for line in wrap(text, "B", 21, CONTENT_W):
            self.c.setFont(FONTS["B"], 21)
            self.c.drawString(ML, self.y, line)
            self.y -= 27
        self.y -= 6
        self.c.setStrokeColor(CORAL)
        self.c.setLineWidth(2)
        self.c.line(ML, self.y, ML + 54, self.y)
        self.y -= 22

    def h2(self, text: str) -> None:
        self.need(110)
        self.y -= 16
        self.c.setFillColor(NAVY)
        for line in wrap(text, "S", 13.5, CONTENT_W):
            self.c.setFont(FONTS["S"], 13.5)
            self.c.drawString(ML, self.y, line)
            self.y -= 19
        self.y -= 7

    def draw_rich(self, line, size: float, color, x: float = ML,
                  base: str = "R", bold: str = "S") -> None:
        space = pdfmetrics.stringWidth(" ", FONTS[base], size)
        cx = x
        for word, is_bold in line:
            f = FONTS[bold] if is_bold else FONTS[base]
            self.c.setFillColor(color)
            self.c.setFont(f, size)
            self.c.drawString(cx, self.y, word)
            cx += pdfmetrics.stringWidth(word, f, size) + space

    def p(self, text: str, size: float = 10.5, color=INK) -> None:
        for line in wrap_rich(text, size, CONTENT_W):
            self.need(16)
            self.draw_rich(line, size, color)
            self.y -= size * 1.5
        self.y -= 6

    def quote(self, text: str, label: str) -> None:
        body = wrap(text, "R", 10.2, CONTENT_W - 34)
        h = 24 + len(body) * 14.4 + 10
        self.need(h + 4)
        top = self.y
        self.c.setFillColor(PAPER)
        self.c.rect(ML, top - h, CONTENT_W, h, stroke=0, fill=1)
        self.c.setFillColor(MUTED)
        self.c.rect(ML, top - h, 3, h, stroke=0, fill=1)
        yy = top - 17
        self.c.setFillColor(MUTED)
        self.c.setFont(FONTS["S"], 7.5)
        self.c.drawString(ML + 14, yy, label.upper())
        yy -= 15
        self.c.setFillColor(HexColor("#3A4450"))
        self.c.setFont(FONTS["R"], 10.2)
        for line in body:
            self.c.drawString(ML + 14, yy, line)
            yy -= 14.4
        self.y = top - h - 12
        self.need(20)

    def replace(self, text: str) -> None:
        body = wrap(text, "M", 10.4, CONTENT_W - 34)
        h = 30 + len(body) * 14.8
        self.need(h + 6)
        top = self.y
        self.c.setFillColor(TINT)
        self.c.rect(ML, top - h, CONTENT_W, h, stroke=0, fill=1)
        self.c.setFillColor(NAVY)
        self.c.rect(ML, top - h, 3, h, stroke=0, fill=1)
        self.c.setFillColor(NAVY)
        self.c.setFont(FONTS["S"], 7.5)
        self.c.drawString(ML + 14, top - 16, "ВСТАВИТЬ ТАК")
        yy = top - 33
        self.c.setFillColor(NAVY_D)
        self.c.setFont(FONTS["M"], 10.4)
        for line in body:
            self.c.drawString(ML + 14, yy, line)
            yy -= 14.8
        self.y = top - h - 12
        self.need(20)

    def bullet(self, text: str) -> None:
        body = wrap_rich(text, 10.4, CONTENT_W - 16)
        self.need(len(body) * 15 + 6)
        top = self.y
        self.c.setFillColor(CORAL)
        self.c.circle(ML + 3, top + 3, 1.9, stroke=0, fill=1)
        self.y = top
        for line in body:
            self.draw_rich(line, 10.4, INK, x=ML + 16)
            self.y -= 15
        self.y -= 5

    def callout(self, text: str) -> None:
        body = wrap_rich(text, 10.2, CONTENT_W - 40, base="M", bold="B")
        h = 20 + len(body) * 14.4
        self.need(h + 10)
        top = self.y - 4
        self.c.setFillColor(HexColor("#FBEFED"))
        self.c.rect(ML, top - h, CONTENT_W, h, stroke=0, fill=1)
        self.c.setFillColor(CORAL)
        self.c.setFont(FONTS["B"], 12)
        self.c.drawString(ML + 11, top - 20, "!")
        self.y = top - 20
        for line in body:
            self.draw_rich(line, 10.2, HexColor("#8C2E26"), x=ML + 28,
                           base="M", bold="B")
            self.y -= 14.4
        self.y = top - h - 14
        self.need(16)

    def table(self, rows: list[list[str]], widths: list[float] | None = None,
              size: float = 9.4) -> None:
        n = len(rows[0])
        if widths is None:
            widths = [CONTENT_W / n] * n
        scale = CONTENT_W / sum(widths)
        widths = [w * scale for w in widths]

        def row_height(cells: list[str], font: str, s: float) -> float:
            return max(len(wrap(cell, font, s, widths[i] - 14)) for i, cell in
                       enumerate(cells)) * (s * 1.42) + 11

        for ri, row in enumerate(rows):
            font = FONTS["S"] if ri == 0 else FONTS["R"]
            h = row_height(row, font, size)
            self.need(h)
            top = self.y
            if ri == 0:
                color, font = NAVY, FONTS["S"]
            else:
                if ri % 2 == 0:
                    self.c.setFillColor(HexColor("#F7F8F9"))
                    self.c.rect(ML, top - h, CONTENT_W, h, stroke=0, fill=1)
                color, font = INK, FONTS["R"]
            x = ML
            for ci, cell in enumerate(row):
                yy = top - 11 - size
                self.c.setFillColor(color)
                self.c.setFont(font, size)
                for line in wrap(cell, font, size, widths[ci] - 14):
                    self.c.drawString(x + 7, yy, line)
                    yy -= size * 1.42
                x += widths[ci]
            self.c.setStrokeColor(LINE)
            self.c.setLineWidth(0.5)
            self.c.line(ML, top - h, ML + CONTENT_W, top - h)
            self.y = top - h
        self.y -= 14

    def lines_block(self, lines: list[str], cols: int = 2, size: float = 9.4,
                    color=INK, indent: float = 0) -> None:
        """Строки без буллетов: удобно копировать в Директ."""
        col_w = (CONTENT_W - indent - (cols - 1) * 22) / cols
        lead = size * 1.55
        per_col = 0
        rows = (len(lines) + cols - 1) // cols
        self.need(rows * lead + 6)
        top = self.y
        for i, text in enumerate(lines):
            col, row = i // rows, i % rows
            x = ML + indent + col * (col_w + 22)
            yy = top - row * lead
            s = size
            while pdfmetrics.stringWidth(text, FONTS["M"], s) > col_w and s > 6.4:
                s -= 0.2
            self.c.setFillColor(color)
            self.c.setFont(FONTS["M"], s)
            self.c.drawString(x, yy, text)
        self.y = top - rows * lead - 6

    def group_heading(self, code: str, name: str) -> None:
        self.need(40)
        self.y -= 8
        self.c.setFillColor(CORAL)
        self.c.setFont(FONTS["B"], 9)
        self.c.drawString(ML, self.y, code)
        self.c.setFillColor(NAVY)
        self.c.setFont(FONTS["S"], 11.5)
        self.c.drawString(ML + 30, self.y, name)
        self.y -= 6
        self.c.setStrokeColor(LINE)
        self.c.setLineWidth(0.6)
        self.c.line(ML, self.y, ML + CONTENT_W, self.y)
        self.y -= 14

    def ad_card(self, ad: dict[str, str]) -> None:
        body = wrap(ad["text"], "R", 10, CONTENT_W - 26)
        h = 66 + len(body) * 14
        self.need(h + 10)
        top = self.y
        self.c.setFillColor(HexColor("#FAFAF7"))
        self.c.rect(ML, top - h, CONTENT_W, h, stroke=0, fill=1)
        self.c.setFillColor(LINE)
        self.c.setLineWidth(0.5)
        self.c.rect(ML, top - h, CONTENT_W, h, stroke=1, fill=0)

        self.c.setFillColor(NAVY_D)
        self.c.setFont(FONTS["S"], 12.2)
        self.c.drawString(ML + 13, top - 23, ad["title1"])
        t1_len = len(ad["title1"])
        self.c.setFillColor(MUTED if t1_len <= 56 else CORAL)
        self.c.setFont(FONTS["R"], 7)
        self.c.drawRightString(ML + CONTENT_W - 13, top - 23, f"{t1_len}/56")

        self.c.setFillColor(HexColor("#41586B"))
        self.c.setFont(FONTS["R"], 9.6)
        self.c.drawString(ML + 13, top - 39, ad["title2"])
        self.c.setFillColor(MUTED if len(ad["title2"]) <= 30 else CORAL)
        self.c.setFont(FONTS["R"], 7)
        self.c.drawRightString(ML + CONTENT_W - 13, top - 39,
                               f"{len(ad['title2'])}/30")

        yy = top - 55
        self.c.setFillColor(INK)
        self.c.setFont(FONTS["R"], 10)
        for line in body:
            self.c.drawString(ML + 13, yy, line)
            yy -= 14
        self.c.setFillColor(MUTED)
        self.c.setFont(FONTS["R"], 7.6)
        self.c.drawRightString(ML + CONTENT_W - 13, top - h + 9,
                               f"{len(ad['text'])}/81 · "
                               f"sm-production.ru/{ad['display_path_1']}/"
                               f"{ad['display_path_2']}")
        self.y = top - h - 10

    def save(self) -> None:
        self.c.showPage()
        self.c.save()
        print(f"  ✓ {self.path.relative_to(REPO)}  {self.page} стр.")


# ── разбор markdown-подмножества ────────────────────────────────────────────
def parse_tables(md: str) -> list[tuple[int, list[list[str]]]]:
    """Возвращает (индекс строки, строки таблицы) для каждого блока таблицы."""
    blocks, cur = [], []
    for i, raw in enumerate(md.splitlines()):
        line = raw.strip()
        if line.startswith("|"):
            cur.append([c.strip() for c in line.strip("|").split("|")])
        elif cur:
            blocks.append((i - len(cur), cur))
            cur = []
    if cur:
        blocks.append((len(md.splitlines()) - len(cur), cur))
    return blocks


def render_md_with_tables(doc: Doc, text: str) -> None:
    lines = text.splitlines()
    tables = {start: rows for start, rows in parse_tables(text)}
    i = 0
    while i < len(lines):
        raw = lines[i].rstrip()
        if i in tables:
            doc.table(tables[i])
            i += len(tables[i])
            continue
        line = raw
        if not line.strip():
            doc.gap(3)
        elif line.startswith("## "):
            doc.h1(line[3:])
        elif line.startswith("### "):
            doc.h2(line[4:])
        elif line.startswith("> "):
            doc.quote(line[2:], "с сайта, дословно")
        elif line.startswith("+ "):
            doc.replace(line[2:])
        elif line.startswith("- "):
            doc.bullet(line[2:])
        elif line.startswith("! "):
            doc.callout(line[2:])
        else:
            doc.p(line)
        i += 1


# ── документ 1: правки страницы ─────────────────────────────────────────────
def build_page_pdf() -> None:
    md = (HERE / "page-audit.md").read_text(encoding="utf-8")
    body = md.split("## ", 1)[1]
    body = "## " + body

    doc = Doc(
        HERE / "oformlenie-scen-pravki-stranicy.pdf",
        "SM-Production · оформление сцен",
        "Правки страницы «Оформление сцен»",
        "Выдержки с сайта и готовые формулировки. 5 критичных правок, "
        "6 правок по блокам, 3 новых блока.",
        [("Страница", "sm-production.ru/uslugi/oformleniye-stseny"),
         ("Проверено", "30 октября 2026, вручную по живой странице"),
         ("Сверено с", "/uslugi/kashe-dlya-ekrana, /blog/oformlenie-stsen-sm-production"),
         ("Формат", "правки под Тильду: цитата → что вставить")],
        "Собрано по тексту живой страницы. Все цитаты — дословные, из блоков "
        "Тильды: их можно найти поиском по странице и заменить. Порядок правок "
        "и приоритеты — в конце документа.",
        "SM-Production · Оформление сцен · правки страницы услуги",
    )
    render_md_with_tables(doc, body)
    doc.save()


# ── документ 2: Яндекс.Директ ───────────────────────────────────────────────
def build_direct_pdf() -> None:
    kw = list(csv.DictReader((HERE / "keywords.csv").open(encoding="utf-8")))
    ads = list(csv.DictReader((HERE / "ads.csv").open(encoding="utf-8")))
    ext = list(csv.DictReader((HERE / "extensions.csv").open(encoding="utf-8")))
    minus = [ln.strip() for ln in
             (HERE / "minus-words.txt").read_text(encoding="utf-8").splitlines()
             if ln.strip() and not ln.startswith("#")]

    bad = [a for a in ads if len(a["title1"]) > 56 or len(a["title2"]) > 30
           or len(a["text"]) > 81]
    if bad:
        print("  ! объявления вне лимитов:", [a["ad_id"] for a in bad])

    doc = Doc(
        HERE / "oformlenie-scen-direct.pdf",
        "SM-Production · оформление сцен",
        "Яндекс.Директ: кампания «Оформление сцен»",
        "Структура, ключи, объявления, минус-слова и настройки — "
        "всё, что нужно, чтобы запустить поиск.",
        [("Кампаний", "3: поиск, ретаргетинг, мастер кампаний"),
         ("Групп и фраз", f"6 групп, {len(kw)} фраз"),
         ("Объявлений", f"{len(ads)}, по 3 на группу"),
         ("Гео", "Москва и Московская область")],
        "Ключи, объявления и минус-слова продублированы файлами keywords.csv, "
        "ads.csv, extensions.csv и minus-words.txt — вставляйте построчно, "
        "чтобы не перепечатывать из PDF.",
        "SM-Production · Оформление сцен · кампания в Яндекс.Директе",
    )

    md = (HERE / "direct-plan.md").read_text(encoding="utf-8")
    body = "## " + md.split("## ", 1)[1]
    render_md_with_tables(doc, body)

    # ── ключи ──
    doc.h1("Ключевые фразы для вставки")
    doc.p("По одной фразе в строке, без кавычек и минусов: вставлять в группу "
          "целиком, Директ сам разберёт типы соответствия. Для точного "
          "соответствия обернуть нужные фразы в кавычки в интерфейсе.")
    current = None
    for row in kw:
        if row["group_code"] != current:
            current = row["group_code"]
            doc.group_heading(current, row["group_name"])
            doc.p(f"Лендинг: sm-production.ru{row['landing']}", 8.6, MUTED)
        doc.lines_block([row["phrase"]], cols=1, size=9.8, indent=0)

    # ── минус-слова ──
    doc.h1("Минус-слова")
    doc.p("Добавлять на уровне кампании целиком. Основная проблема запроса "
          "«сцена» — он про кино, театр и компьютерные игры, а не про монтаж; "
          "эти группы минусов экономят больше всего.")
    doc.lines_block(minus, cols=3, size=8.2)

    # ── объявления ──
    doc.h1("Объявления")
    doc.p("Восемнадцать штук, по три на группу — это минимум для теста "
          "заголовков. Лимиты Директа: заголовок 1 — 56 символов, заголовок "
          "2 — 30, текст — 81. Счётчик справа показывает фактическую длину.")
    current = None
    for ad in ads:
        if ad["group_code"] != current:
            current = ad["group_code"]
            doc.group_heading(ad["group_code"],
                              next(r["group_name"] for r in kw
                                   if r["group_code"] == current))
        doc.ad_card(ad)

    # ── расширения ──
    doc.h1("Быстрые ссылки и уточнения")
    rows = [["Тип", "Текст", "Описание"]]
    for e in ext:
        rows.append([e["type"], e["title"], e["description"] or "—"])
    doc.table(rows, widths=[2.0, 3.0, 5.2], size=9.2)
    doc.p("Быстрые ссылки ведут на разделы сайта — проверить, что адреса "
          "существуют: «Каше для экрана» — /uslugi/kashe-dlya-ekrana, «Раус "
          "сцены» — /uslugi/raus-stseny, «Проекты» — /portfolio.")
    doc.save()


def main() -> int:
    register_fonts()
    build_page_pdf()
    build_direct_pdf()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
