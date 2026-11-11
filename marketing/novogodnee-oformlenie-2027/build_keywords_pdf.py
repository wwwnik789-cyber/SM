#!/usr/bin/env python3
"""Build a copy-friendly PDF with Direct keywords and negative keywords.

Layout rules that matter for copying:
  * one phrase per line, one drawString call per phrase;
  * no numbering, bullets or dashes in front of phrases;
  * left column is written to the content stream before the right column,
    so text extraction keeps the reading order;
  * every group heading is upper case and separate from the phrase block.
"""

from __future__ import annotations

import csv
import sys
import tempfile
from pathlib import Path

from fontTools.ttLib import TTFont as FTFont
from fontTools.varLib.instancer import instantiateVariableFont
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
FONT_VF = REPO / "banners" / "anikom-arena-3000x2500-concepts" / "source" / "Montserrat-Variable.ttf"
OUTPUT = REPO / "marketing" / "novogodnee-oformlenie-2027" / "novogodnee-2027-klyuchi-i-minusy.pdf"

NAVY = HexColor("#081A2B")
NAVY_SOFT = HexColor("#0D2238")
CORAL = HexColor("#D94A43")
INK = HexColor("#1A2430")
MUTED = HexColor("#7C8894")
LINE = HexColor("#D8D1C4")
PAPER = HexColor("#F4F1EA")
WHITE = HexColor("#FFFFFF")

PAGE_W, PAGE_H = A4
MARGIN_X = 40
TOP = PAGE_H - 96
BOTTOM = 52

COL_W = 244
GUTTER = 27
COL_X = [MARGIN_X, MARGIN_X + COL_W + GUTTER]

LINE_H = 14.6
GROUP_GAP = 13
SECTION_GAP = 20

GROUP_TITLES = {
    "G01": "ОФИС",
    "G02": "ФОТОЗОНЫ",
    "G03": "СОБЫТИЯ И КОРПОРАТИВЫ",
    "G04": "РИТЕЙЛ, ВИТРИНЫ, РЕСТОРАНЫ",
    "G05": "АРТ-ОБЪЕКТЫ И ФАСАДЫ",
    "G06": "B2B И АГЕНТСТВА",
    "G07": "СРОЧНЫЕ ЗАКАЗЫ",
}

NEGATIVE_GROUPS = {
    "DIY": "СВОИМИ РУКАМИ",
    "INFO": "ИНФОРМАЦИЯ БЕЗ ПОКУПКИ",
    "GOODS": "ТОВАРЫ, А НЕ УСЛУГИ",
    "MARKET": "ПЛОЩАДКИ И МАГАЗИНЫ",
    "JOB": "РАБОТА И ОБУЧЕНИЕ",
    "WRONG": "НЕЦЕЛЕВЫЕ ФОРМАТЫ",
    "RENT": "АРЕНДА",
    "OTHER": "ПРОЧЕЕ",
}


def build_static_font(weight: int, target: Path) -> Path:
    font = FTFont(str(FONT_VF))
    instance = instantiateVariableFont(font, {"wght": weight}, updateFontNames=True)
    instance.save(str(target))
    return target


def register_fonts(workdir: Path) -> tuple[str, str]:
    regular_path = build_static_font(400, workdir / "Montserrat-Regular.ttf")
    semibold_path = build_static_font(600, workdir / "Montserrat-SemiBold.ttf")
    pdfmetrics.registerFont(TTFont("Montserrat", str(regular_path)))
    pdfmetrics.registerFont(TTFont("Montserrat-SemiBold", str(semibold_path)))
    return "Montserrat", "Montserrat-SemiBold"


def load_keywords() -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {}
    with (ROOT / "keywords.csv").open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["group_code"].startswith("G"):
                groups.setdefault(row["group_code"], []).append(row["phrase"].strip())
    return groups


def load_placements() -> list[str]:
    path = ROOT / "blocked-placements.txt"
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_negatives() -> list[tuple[str, list[str]]]:
    blocks: list[tuple[str, list[str]]] = []
    current_key = "OTHER"
    current: list[str] = []

    for raw in (ROOT / "negative-keywords.txt").read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            marker = line.lstrip("# ").strip().lower()
            key = None
            if "diy" in marker:
                key = "DIY"
            elif "информационн" in marker:
                key = "INFO"
            elif "товар" in marker:
                key = "GOODS"
            elif "площадк" in marker or "магазин" in marker:
                key = "MARKET"
            elif "работ" in marker or "обучен" in marker:
                key = "JOB"
            elif "нецелев" in marker:
                key = "WRONG"
            elif "аренда" in marker:
                key = "RENT"
            if key and current:
                blocks.append((current_key, current))
                current = []
            if key:
                current_key = key
            continue
        current.append(line)

    if current:
        blocks.append((current_key, current))
    return blocks


class Layout:
    """Two-column flow that keeps the content-stream order copy-friendly."""

    def __init__(self, c: canvas.Canvas, regular: str, semibold: str) -> None:
        self.c = c
        self.regular = regular
        self.semibold = semibold
        self.column = 0
        self.y = TOP
        self.page_first_column: list[list[tuple]] = [[], []]
        self.pages: list[list[list[tuple]]] = []
        self.page_labels: list[str] = []
        self.label = "Ключевые фразы"
        self.page = 1

    def _new_page(self) -> None:
        self.pages.append(self.page_first_column)
        self.page_labels.append(self.label)
        self.page_first_column = [[], []]
        self.page += 1
        self.column = 0
        self.y = TOP

    def _next_column(self) -> None:
        if self.column == 0:
            self.column = 1
            self.y = TOP
        else:
            self._new_page()

    def need(self, height: float) -> None:
        if self.y - height < BOTTOM:
            self._next_column()

    def add_group(self, code: str, title: str, phrases: list[str]) -> None:
        block_height = 22 + len(phrases) * LINE_H
        if self.y - block_height < BOTTOM and self.y < TOP - 60:
            self._next_column()
        self.need(22)
        self.page_first_column[self.column].append(("group", code, title))
        self.y -= 22
        for phrase in phrases:
            self.need(LINE_H)
            self.page_first_column[self.column].append(("phrase", phrase))
            self.y -= LINE_H
        self.y -= GROUP_GAP

    def add_section(self, title: str, subtitle: str = "", label: str | None = None,
                    new_page: bool = False) -> None:
        if label:
            self.label = label
        if new_page:
            self._new_page()
        elif self.column == 0 and self.y < TOP - 40:
            self._next_column()
        elif self.column == 1:
            self._new_page()
        self.page_first_column[self.column].append(("section", title, subtitle))
        self.y -= 34
        if subtitle:
            self.y -= 16

    def add_plain(self, phrase: str) -> None:
        self.need(LINE_H)
        self.page_first_column[self.column].append(("phrase", phrase))
        self.y -= LINE_H

    def flush(self) -> list[list[list[tuple]]]:
        self.pages.append(self.page_first_column)
        self.page_labels.append(self.label)
        return self.pages


def draw_page_background(c: canvas.Canvas) -> None:
    c.setFillColor(WHITE)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)


def draw_header(c: canvas.Canvas, regular: str, semibold: str, page_no: int, total: int, label: str) -> None:
    c.setFillColor(NAVY)
    c.rect(0, PAGE_H - 74, PAGE_W, 74, stroke=0, fill=1)
    c.setFillColor(CORAL)
    c.rect(0, PAGE_H - 78, PAGE_W, 4, stroke=0, fill=1)

    c.setFillColor(WHITE)
    c.setFont(semibold, 15)
    c.drawString(MARGIN_X, PAGE_H - 40, "SM PRODUCTION")
    c.setFont(regular, 8.6)
    c.drawRightString(PAGE_W - MARGIN_X, PAGE_H - 33, "Новогоднее оформление 2027")
    c.drawRightString(PAGE_W - MARGIN_X, PAGE_H - 46, "Яндекс Директ · ключи и минус-слова")

    c.setFillColor(CORAL)
    c.setFont(semibold, 7.4)
    c.drawString(MARGIN_X, PAGE_H - 64, label.upper())

    c.setFillColor(MUTED)
    c.setFont(regular, 7.4)
    c.drawRightString(PAGE_W - MARGIN_X, PAGE_H - 64, f"{page_no} / {total}")


def draw_footer(c: canvas.Canvas, regular: str) -> None:
    c.setStrokeColor(LINE)
    c.setLineWidth(0.5)
    c.line(MARGIN_X, 34, PAGE_W - MARGIN_X, 34)
    c.setFillColor(MUTED)
    c.setFont(regular, 6.6)
    c.drawString(MARGIN_X, 23, "Одна фраза — одна строка. Выделяйте строки целиком, нумерации и маркеров в списках нет.")
    c.drawRightString(PAGE_W - MARGIN_X, 23, "sm-production.ru/novogodnee-oformlenie")


def render_block(c: canvas.Canvas, x: float, top: float, items: list[tuple], regular: str, semibold: str) -> float:
    y = top
    for item in items:
        kind = item[0]
        if kind == "group":
            code, title = item[1], item[2]
            c.setFillColor(CORAL)
            c.setFont(semibold, 7.2)
            c.drawString(x, y - 8, f"{code}  {title}")
            c.setStrokeColor(LINE)
            c.setLineWidth(0.4)
            c.line(x, y - 13, x + COL_W, y - 13)
            y -= 22
        elif kind == "section":
            title, subtitle = item[1], item[2]
            c.setFillColor(NAVY)
            c.setFont(semibold, 13.5)
            c.drawString(x, y - 10, title)
            y -= 20
            if subtitle:
                c.setFillColor(MUTED)
                c.setFont(regular, 8)
                c.drawString(x, y - 8, subtitle)
                y -= 14
        elif kind == "subtitle":
            c.setFillColor(MUTED)
            c.setFont(regular, 8)
            c.drawString(x, y - 8, item[1])
            y -= 16
        elif kind == "phrase":
            c.setFillColor(INK)
            c.setFont(regular, 9.4)
            c.drawString(x, y - 9.6, item[1])
            y -= LINE_H
    return y


def build() -> Path:
    keywords = load_keywords()
    negatives = load_negatives()
    search_codes = [code for code in GROUP_TITLES if code in keywords]
    search_total = sum(len(keywords[code]) for code in search_codes)
    negative_total = sum(len(words) for _, words in negatives)
    placements = load_placements()
    placements_total = len(placements)

    with tempfile.TemporaryDirectory() as raw_dir:
        workdir = Path(raw_dir)
        regular, semibold = register_fonts(workdir)

        layout = Layout(canvas.Canvas(str(OUTPUT), pagesize=A4), regular, semibold)

        # --- block 1: keywords grouped (reference copy) ---
        layout.label = "Ключевые фразы"
        layout.page_first_column[0].append(
            ("section", "Ключевые фразы по группам", f"{search_total} фраз в {len(search_codes)} группах · поиск Яндекса")
        )
        layout.y -= 34
        for code in search_codes:
            layout.add_group(code, GROUP_TITLES[code], keywords[code])

        # --- block 2: all search phrases as one continuous list ---
        layout.add_section(
            "Все поисковые фразы одним списком",
            "Скопировать блок целиком и вставить в Директ — по одной фразе в строке",
            label="Ключевые фразы",
        )
        for code in search_codes:
            for phrase in keywords[code]:
                layout.add_plain(phrase)

        # --- block 3: negative keywords as one continuous list ---
        layout.add_section(
            "Минус-слова одним списком",
            f"{negative_total} слов · вставлять в общий список минус-слов кампании",
            label="Минус-слова",
        )
        for _, words in negatives:
            for word in words:
                layout.add_plain(word)

        # --- block 4: blocked placements ---
        layout.add_section(
            "Площадки, где запрещены показы",
            f"{placements_total} значений · Запрет показов → Площадки",
            label="Запрещённые площадки",
            new_page=True,
        )
        for item in placements:
            layout.add_plain(item)

        pages = layout.flush()

        c = layout.c
        total = len(pages)
        for index, columns in enumerate(pages):
            draw_page_background(c)
            draw_header(c, regular, semibold, index + 1, total, layout.page_labels[index])

            # Column 1 stream first, column 2 second: keeps copy order correct.
            for column_index, items in enumerate(columns):
                if not items:
                    continue
                render_block(c, COL_X[column_index], TOP, items, regular, semibold)

            # Column rule drawn after text so it never splits a selection.
            if len(pages[index][1]) > 0:
                c.setStrokeColor(HexColor("#EDE7DA"))
                c.setLineWidth(0.8)
                c.line(COL_X[1] - GUTTER / 2, BOTTOM, COL_X[1] - GUTTER / 2, TOP)

            draw_footer(c, regular)
            c.showPage()

        c.setTitle("Новогоднее оформление 2027 — ключи и минус-слова")
        c.setAuthor("SM Production")
        c.setSubject("Ключевые фразы и минус-слова для кампании в Яндекс Директе")
        c.setKeywords("Яндекс Директ, новогоднее оформление, ключевые слова, минус-слова")
        c.save()

    return OUTPUT


def main() -> int:
    path = build()
    print(f"Готово: {path.relative_to(REPO)}")
    print(f"Размер: {path.stat().st_size // 1024} КБ")
    return 0


if __name__ == "__main__":
    sys.exit(main())
