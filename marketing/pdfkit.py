"""Мини-вёрстка PDF для маркетинговых документов SM-Production.

Тот же визуальный язык, что у PDF по оформлению сцен: обложка на тёмном,
разделы с коралловой чертой, цитаты, врезки, таблицы.

    from pdfkit import Doc, register_fonts
"""
from __future__ import annotations

from pathlib import Path

from fontTools.ttLib import TTFont as FTFont
from fontTools.varLib.instancer import instantiateVariableFont
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

REPO = Path(__file__).resolve().parent.parent
FONT_VF = REPO / "banners/anikom-arena-3000x2500-concepts/source/Montserrat-Variable.ttf"
FONT_DIR = Path("/tmp/fonts-pdfkit")

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

FONTS: dict[str, str] = {}


def register_fonts(weights=((400, "R"), (500, "M"), (600, "S"), (700, "B"))) -> None:
    FONT_DIR.mkdir(parents=True, exist_ok=True)
    for weight, alias in weights:
        path = FONT_DIR / f"M{alias}.ttf"
        if not path.exists():
            inst = instantiateVariableFont(FTFont(str(FONT_VF)), {"wght": weight},
                                           updateFontNames=True)
            inst.save(str(path))
        pdfmetrics.registerFont(TTFont(f"M{alias}", str(path)))
        FONTS[alias] = f"M{alias}"


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


def width_of(text: str, font: str, size: float) -> float:
    return pdfmetrics.stringWidth(text, FONTS.get(font, font), size)


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
        self.y = PAGE_H - MT
        self.cover(meta, note)
        self.new_page()

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
        for line in wrap(self.title, "B", 33, CONTENT_W - 16):
            c.setFillColor(WHITE)
            c.setFont(FONTS["B"], 33)
            c.drawString(ML, y, line)
            y -= 41
        y -= 8
        for line in wrap(self.subtitle, "R", 14, CONTENT_W - 40):
            c.setFillColor(HexColor("#C6D3DE"))
            c.setFont(FONTS["R"], 14)
            c.drawString(ML, y, line)
            y -= 21
        y = 320
        for label, value in meta:
            c.setFillColor(HexColor("#7E94A6"))
            c.setFont(FONTS["S"], 9)
            c.drawString(ML, y, label.upper())
            c.setFillColor(WHITE)
            c.setFont(FONTS["M"], 12.5)
            c.drawString(ML + 165, y, value)
            y -= 26
        c.setFillColor(HexColor("#22384A"))
        c.rect(0, 0, PAGE_W, 110, stroke=0, fill=1)
        c.setFillColor(HexColor("#93A8B8"))
        c.setFont(FONTS["R"], 9.5)
        yy = 74
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

    # ── заголовки ───────────────────────────────────────────────────────────
    def h1(self, text: str) -> None:
        self.need(150)
        self.y -= 18
        self.c.setFillColor(NAVY_D)
        for line in wrap(text, "B", 21, CONTENT_W):
            self.c.setFont(FONTS["B"], 21)
            self.c.drawString(ML, self.y, line)
            self.y -= 27
        self.y -= 8
        self.c.setStrokeColor(CORAL)
        self.c.setLineWidth(2)
        self.c.line(ML, self.y, ML + 54, self.y)
        self.y -= 22

    def h2(self, text: str) -> None:
        self.need(110)
        self.y -= 14
        self.c.setFillColor(NAVY)
        for line in wrap(text, "S", 13.5, CONTENT_W):
            self.c.setFont(FONTS["S"], 13.5)
            self.c.drawString(ML, self.y, line)
            self.y -= 19
        self.y -= 7

    # ── текст ───────────────────────────────────────────────────────────────
    def p(self, text: str, size: float = 10.5, color=INK) -> None:
        self.c.setFillColor(color)
        self.c.setFont(FONTS["R"], size)
        for line in wrap(text, "R", size, CONTENT_W):
            self.need(16)
            self.c.drawString(ML, self.y, line)
            self.y -= size * 1.5
        self.y -= 6

    def bullet(self, text: str) -> None:
        body = wrap(text, "R", 10.4, CONTENT_W - 16)
        self.need(len(body) * 15 + 6)
        top = self.y
        self.c.setFillColor(CORAL)
        self.c.circle(ML + 3, top + 3, 1.9, stroke=0, fill=1)
        self.c.setFillColor(INK)
        self.c.setFont(FONTS["R"], 10.4)
        yy = top
        for line in body:
            self.c.drawString(ML + 16, yy, line)
            yy -= 15
        self.y = yy - 5

    def quote(self, text: str, label: str = "с сайта, дословно") -> None:
        body = wrap(text, "R", 10.2, CONTENT_W - 34)
        h = 24 + len(body) * 14.4 + 10
        self.need(h + 4)
        top = self.y
        self.c.setFillColor(PAPER)
        self.c.rect(ML, top - h, CONTENT_W, h, stroke=0, fill=1)
        self.c.setFillColor(MUTED)
        self.c.rect(ML, top - h, 3, h, stroke=0, fill=1)
        yy = top - 17
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

    def replace(self, text: str, label: str = "вставить так") -> None:
        body = wrap(text, "M", 10.4, CONTENT_W - 34)
        h = 30 + len(body) * 14.8
        self.need(h + 6)
        top = self.y
        self.c.setFillColor(TINT)
        self.c.rect(ML, top - h, CONTENT_W, h, stroke=0, fill=1)
        self.c.setFillColor(NAVY)
        self.c.rect(ML, top - h, 3, h, stroke=0, fill=1)
        self.c.setFont(FONTS["S"], 7.5)
        self.c.drawString(ML + 14, top - 16, label.upper())
        yy = top - 33
        self.c.setFillColor(NAVY_D)
        self.c.setFont(FONTS["M"], 10.4)
        for line in body:
            self.c.drawString(ML + 14, yy, line)
            yy -= 14.8
        self.y = top - h - 12
        self.need(20)

    def callout(self, text: str) -> None:
        body = wrap(text, "M", 10.2, CONTENT_W - 40)
        h = 20 + len(body) * 14.4
        self.need(h + 10)
        top = self.y - 4
        self.c.setFillColor(HexColor("#FBEFED"))
        self.c.rect(ML, top - h, CONTENT_W, h, stroke=0, fill=1)
        self.c.setFillColor(CORAL)
        self.c.setFont(FONTS["B"], 12)
        self.c.drawString(ML + 11, top - 20, "!")
        self.c.setFillColor(HexColor("#8C2E26"))
        self.c.setFont(FONTS["M"], 10.2)
        yy = top - 20
        for line in body:
            self.c.drawString(ML + 28, yy, line)
            yy -= 14.4
        self.y = top - h - 14
        self.need(16)

    # ── таблицы ─────────────────────────────────────────────────────────────
    def table(self, rows: list[list[str]], widths: list[float] | None = None,
              size: float = 8.8) -> None:
        n = len(rows[0])
        if widths is None:
            widths = [CONTENT_W / n] * n
        scale = CONTENT_W / sum(widths)
        widths = [w * scale for w in widths]

        def row_height(cells, font, s):
            return max(len(wrap(cell, font, s, widths[i] - 12))
                       for i, cell in enumerate(cells)) * (s * 1.42) + 10

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
                yy = top - 10 - size
                self.c.setFillColor(color)
                self.c.setFont(font, size)
                for line in wrap(cell, font, size, widths[ci] - 12):
                    self.c.drawString(x + 6, yy, line)
                    yy -= size * 1.42
                x += widths[ci]
            self.c.setStrokeColor(LINE)
            self.c.setLineWidth(0.5)
            self.c.line(ML, top - h, ML + CONTENT_W, top - h)
            self.y = top - h
        self.y -= 14

    def save(self) -> None:
        self.c.showPage()
        # getPageNumber после showPage смотрит уже на следующую (несуществующую)
        pages = self.c.getPageNumber() - 1
        self.c.save()
        print(f"  ✓ {self.path.name}  {pages} стр.")
