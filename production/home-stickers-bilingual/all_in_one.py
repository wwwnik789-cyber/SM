"""Все 80 наклеек на одном листе: графика растром, контур реза — вектором.

Зачем: печатнику нужен один файл на всю партию, где картинка уже «заплющена»
в растр (не важно, какие шрифты на машине), а линия реза осталась настоящей
векторной кривой в spot-цвете CutContour — её видит плоттер.

    .venv/bin/python production/home-stickers-bilingual/all_in_one.py

Собирает три PDF одинаковой геометрии:
  all-in-one-art-plus-cut.pdf   печать + рез одним файлом (основной)
  all-in-one-art.pdf            только графика, растр
  all-in-one-cut.pdf            только контуры, вектор, CutContour

Геометрия у всех трёх совпадает до микрона: одинаковый MediaBox, одинаковые
центры. Если печатать и резать разными машинами, файлы накладываются точно.
"""
from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import build_stickers as bs  # noqa: E402  (при импорте регистрирует шрифты)

from reportlab.lib.colors import CMYKColorSep  # noqa: E402
from reportlab.lib.units import mm  # noqa: E402
from reportlab.pdfgen import canvas as rcanvas  # noqa: E402

OUT = HERE / "one-sheet"

MARGIN = 15 * mm
COLS, ROWS = 8, 10
PITCH = bs.PITCH            # 45 мм — тот же шаг, что на листах A4


# стандартные форматы, мм
PAGES = {"tight": None, "a2": (420, 594), "a3plus": (329, 483)}


def sheet_size(cols: int, rows: int) -> tuple[float, float]:
    """Минимальный лист под сетку."""
    return (2 * MARGIN + cols * PITCH, 2 * MARGIN + rows * PITCH)


def cell_centers(cols: int, rows: int, page=None):
    """Центры ячеек снизу вверх, слева направо — как читается лист."""
    gw, gh = cols * PITCH, rows * PITCH
    if page:                                   # сетка по центру стандартного листа
        pw, ph = page[0] * mm, page[1] * mm
        ox, oy = (pw - gw) / 2, (ph - gh) / 2
    else:
        ox, oy = MARGIN, MARGIN
    out = []
    for r in range(rows - 1, -1, -1):
        for c in range(cols):
            out.append((ox + c * PITCH + PITCH / 2, oy + r * PITCH + PITCH / 2))
    return out


# ── растеризация ────────────────────────────────────────────────────────────
def render_cells(items, dpi: int, workdir: Path) -> list[Path]:
    """Каждая наклейка — отдельная страница PDF, потом в PNG ровно по ячейке."""
    import pymupdf
    from PIL import Image

    cell_pdf = workdir / "cells.pdf"
    c = rcanvas.Canvas(str(cell_pdf), pagesize=(PITCH, PITCH))
    for item in items:
        bs.draw_sticker(c, PITCH / 2, PITCH / 2, item, show_cut=False)
        c.showPage()
    c.save()

    doc = pymupdf.open(cell_pdf)
    paths = []
    for i, page in enumerate(doc):
        pix = page.get_pixmap(dpi=dpi, alpha=False)
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        p = workdir / f"cell-{i:02d}.png"
        img.save(p, optimize=True)
        paths.append(p)
    doc.close()
    return paths


# ── сборка PDF ──────────────────────────────────────────────────────────────
def build_pdf(path: Path, items, images, cols: int, rows: int, *,
              with_art: bool, with_cut: bool, dpi: int,
              title: str, page=None) -> Path:
    w, h = (page[0] * mm, page[1] * mm) if page else sheet_size(cols, rows)
    c = rcanvas.Canvas(str(path), pagesize=(w, h))
    c.setTitle(title)
    c.setAuthor("SM Production")
    c.setSubject(f"Наклейки EN+RU · {len(items)} шт. · контур {bs.D_CUT / mm:.0f} мм")

    centers = cell_centers(cols, rows, page)

    if with_art:
        for img_path, (cx, cy) in zip(images, centers):
            c.drawImage(str(img_path), cx - PITCH / 2, cy - PITCH / 2,
                        width=PITCH, height=PITCH, mask=None)

    if with_cut:
        # Отдельный spot-цвет: печатная машина его игнорирует, плоттер — режет.
        spot = CMYKColorSep(0, 1, 0, 0, spotName="CutContour", density=1)
        c.setStrokeColor(spot)
        c.setLineWidth(0.35)
        c.setLineJoin(1)
        for cx, cy in centers[:len(items)]:
            c.drawPath(bs.scallop_path(c, cx, cy, bs.R_CUT), stroke=1, fill=0)

    c.showPage()
    c.save()
    return path


def main() -> int:
    ap = argparse.ArgumentParser(description="Все наклейки на одном листе")
    ap.add_argument("--cols", type=int, default=COLS)
    ap.add_argument("--rows", type=int, default=ROWS)
    ap.add_argument("--dpi", type=int, default=600)
    ap.add_argument("--page", choices=sorted(PAGES), default="tight",
                    help="tight — по размеру сетки, a2 — 420×594 мм, a3plus — 329×483 мм")
    args = ap.parse_args()

    items = bs.ITEMS
    capacity = args.cols * args.rows
    if capacity < len(items):
        print(f"Сетка {args.cols}×{args.rows} вмещает {capacity}, а наклеек {len(items)}. "
              f"Увеличьте rows/cols.", file=sys.stderr)
        return 1

    page = PAGES[args.page]
    OUT.mkdir(parents=True, exist_ok=True)
    w, h = (page[0] * mm, page[1] * mm) if page else sheet_size(args.cols, args.rows)
    need_w, need_h = sheet_size(args.cols, args.rows)
    if page and (w < need_w - 0.5 or h < need_h - 0.5):
        print(f"Сетка {args.cols}×{args.rows} требует {need_w / mm:.0f} × "
              f"{need_h / mm:.0f} мм, а лист {args.page} — {w / mm:.0f} × {h / mm:.0f} мм.",
              file=sys.stderr)
        return 1
    print(f"Лист {w / mm:.0f} × {h / mm:.0f} мм · ячеек {capacity} · наклеек {len(items)} "
          f"· растр {args.dpi} dpi")

    with tempfile.TemporaryDirectory() as td:
        images = render_cells(items, args.dpi, Path(td))

        made = []
        suffix = "" if args.page == "tight" else f"-{args.page}"
        made.append(build_pdf(
            OUT / f"all-in-one-art-plus-cut{suffix}.pdf", items, images, args.cols, args.rows,
            with_art=True, with_cut=True, dpi=args.dpi, page=page,
            title="SM Production · наклейки EN+RU · графика растром + контур реза вектором"))
        if args.page == "tight":      # отдельные наборы нужны только в базовом размере
            made.append(build_pdf(
                OUT / "all-in-one-art.pdf", items, images, args.cols, args.rows,
                with_art=True, with_cut=False, dpi=args.dpi,
                title="SM Production · наклейки EN+RU · только графика"))
            made.append(build_pdf(
                OUT / "all-in-one-cut.pdf", items, images, args.cols, args.rows,
                with_art=False, with_cut=True, dpi=args.dpi,
                title="SM Production · наклейки EN+RU · только контуры реза"))

    for p in made:
        print(f"  {p.name}: {p.stat().st_size / 1024 / 1024:.1f} МБ")

    return 0


if __name__ == "__main__":
    sys.exit(main())
