#!/usr/bin/env python3
"""Обложки для статьи и соцсетей: 1200×630 и 1080×1350.

Иконки берём из генератора наклеек, поэтому картинки совпадают
с тем, что напечатано в PDF: те же фестоны, шрифты и палитра.

Запуск из корня репозитория:
    .venv/bin/python marketing/home-stickers-blog-2026/build_blog_assets.py
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pymupdf
from PIL import Image
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas

HERE = Path(__file__).resolve().parent
STICKERS = HERE.parents[1] / "production/home-stickers-bilingual/build_stickers.py"

BG = colors.HexColor("#12100E")
LIGHT = colors.HexColor("#F4EFE6")
MUTED = colors.HexColor("#8E877C")
ACCENT = colors.HexColor("#E9A552")
LINE = colors.HexColor("#FF4D1C")


def load_stickers():
    spec = importlib.util.spec_from_file_location("stickers", STICKERS)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


S = load_stickers()
BY_NAME = {item[1]: item for item in S.ITEMS}   # по английскому слову


def fit(c, text, font, size, max_w, floor=8.0):
    while size > floor and pdfmetrics.stringWidth(text, font, size) > max_w:
        size -= 0.5
    return size


def sticker(c, name, x, y, diameter):
    """Наклейка с центром (x, y) и заданным диаметром в пунктах."""
    k = diameter / (2 * S.R_CUT)
    c.saveState()
    c.translate(x, y)
    c.scale(k, k)
    S.draw_sticker(c, 0, 0, BY_NAME[name], show_cut=False)
    c.restoreState()


def wrap(c, text, font, size, max_w):
    words, line, lines = text.split(), "", []
    for w in words:
        probe = (line + " " + w).strip()
        if pdfmetrics.stringWidth(probe, font, size) > max_w and line:
            lines.append(line)
            line = w
        else:
            line = probe
    lines.append(line)
    return lines


def render(pdf_path: Path, png_path: Path, width: float, height: float, draw, target_w: int):
    """Рисуем в логических единицах width×height, отдаём PNG шириной target_w."""
    k = target_w / width
    c = canvas.Canvas(str(pdf_path), pagesize=(target_w, height * k))
    c.scale(k, k)
    c.setFillColor(BG)
    c.rect(0, 0, width, height, stroke=0, fill=1)
    draw(c, width, height)
    c.showPage()
    c.save()

    doc = pymupdf.open(str(pdf_path))
    pix = doc[0].get_pixmap(matrix=pymupdf.Matrix(1, 1), alpha=False)
    pix.save(str(png_path))
    print(f"  {png_path.name}: {pix.width}×{pix.height}, {png_path.stat().st_size // 1024} КБ")


def draw_og(c, W, H):
    # справа — 2×2 наклеек
    d = 112
    for name, x, y in [("Fridge", W - 196, H - 92), ("Kettle", W - 74, H - 92),
                       ("Bed", W - 196, H - 214), ("Backpack", W - 74, H - 214)]:
        sticker(c, name, x, y, d)

    left = 34
    c.setFillColor(ACCENT)
    c.setFont("MS", 8.4)
    c.drawString(left, H - 46, "SM PRODUCTION · ОБУЧАЮЩИЕ НАКЛЕЙКИ · 2026")

    c.setFillColor(LIGHT)
    c.setFont("MB", 30)
    c.drawString(left, H - 84, "Дом говорит")
    c.drawString(left, H - 118, "по-английски")

    c.setFillColor(colors.HexColor("#B8AFA2"))
    c.setFont("M", 10.4)
    for i, line in enumerate(wrap(c, "80 наклеек на предметы быта: английское слово сверху, русское под ним",
                                  "M", 10.4, 300)):
        c.drawString(left, H - 146 - i * 15, line)

    c.setStrokeColor(colors.HexColor("#2E2A25"))
    c.setLineWidth(0.8)
    c.line(left, H - 196, 380, H - 196)

    stats = [("80", "наклеек"), ("Ø 35 мм", "по контуру"), ("A4", "20 на лист")]
    for i, (v, sub) in enumerate(stats):
        x = left + i * 94
        c.setFillColor(LIGHT)
        c.setFont("MB", 15)
        c.drawString(x, H - 226, v)
        c.setFillColor(MUTED)
        c.setFont("M", 7.6)
        c.drawString(x, H - 240, sub)

    c.setFillColor(colors.HexColor("#B8AFA2"))
    c.setFont("M", 8.4)
    c.drawString(left, H - 268, "Контур реза на каждой · вылет краски 0,8 мм")

    c.setFillColor(LINE)
    c.rect(0, 0, W, 5, stroke=0, fill=1)


def draw_ig(c, W, H):
    # верх: три наклейки в ряд
    d = 132
    for name, x in [("Table", 96), ("Fridge", 270), ("Backpack", 444)]:
        sticker(c, name, x, H - 132, d)

    c.setFillColor(ACCENT)
    c.setFont("MS", 9.6)
    c.drawString(40, H - 44, "SM PRODUCTION")

    c.setFillColor(LIGHT)
    c.setFont("MB", 40)
    c.drawString(40, H - 250, "80 наклеек")
    c.drawString(40, H - 292, "на дом")

    c.setFillColor(colors.HexColor("#B8AFA2"))
    c.setFont("M", 12.4)
    for i, line in enumerate(wrap(c, "Английский на предметах, а не в учебнике", "M", 12.4, 440)):
        c.drawString(40, H - 322 - i * 16, line)

    bullets = [
        ("EN сверху, RU под ним", "английское слово крупным и первым"),
        ("Ø 35 мм", "влезает на выключатель и крышку чайника"),
        ("Контур реза на каждой", "ножницы или плоттер — как удобно"),
        ("7 групп по комнатам", "кухня, ванная, детская, прихожая…"),
    ]
    y = H - 376
    for title, sub in bullets:
        c.setFillColor(LINE)
        c.circle(44, y + 4, 2.6, stroke=0, fill=1)
        c.setFillColor(LIGHT)
        c.setFont("MS", 12.6)
        c.drawString(56, y, title)
        c.setFillColor(MUTED)
        c.setFont("M", 9.4)
        c.drawString(56, y - 14, sub)
        y -= 44

    c.setStrokeColor(colors.HexColor("#2E2A25"))
    c.setLineWidth(0.8)
    c.line(40, 78, W - 40, 78)

    c.setFillColor(LIGHT)
    c.setFont("MS", 12.2)
    c.drawString(40, 52, "Напишите — пришлём PDF")
    c.setFillColor(ACCENT)
    c.setFont("MB", 12.2)
    c.drawRightString(W - 40, 52, "8 495 799-00-19")

    c.setFillColor(LINE)
    c.rect(0, 0, W, 6, stroke=0, fill=1)


def main() -> None:
    render(HERE / "_og.pdf", HERE / "og-cover-1200x630.png", 600, 315, draw_og, 1200)
    render(HERE / "_ig.pdf", HERE / "instagram-1080x1350.png", 540, 675, draw_ig, 1080)
    for tmp in ("_og.pdf", "_ig.pdf"):
        (HERE / tmp).unlink(missing_ok=True)


if __name__ == "__main__":
    main()
