#!/usr/bin/env python3
"""Экспорт наклеек для CorelDRAW: каждая наклейка — группа, контуры реза — сверху.

Зачем: в PDF всё лежит отдельными объектами, и при импорте в Corel наклейка
рассыпается на десятки кусков. Здесь каждая наклейка собирается в один
`<g>`, а линии реза выносятся в отдельный слой над графикой.

Структура файла (снизу вверх):
    0 · Фон листа      белый прямоугольник A4, можно удалить
    1 · Наклейки       80 групп, по одной на наклейку
    2 · Контуры реза   малиновые линии Ø 35 мм, поверх графики

Текст переведён в кривые: в Corel не нужен шрифт Montserrat.

Запуск из корня репозитория:
    .venv/bin/python production/home-stickers-bilingual/export_corel.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
from xml.sax.saxutils import escape

import build_stickers as bs
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from reportlab.pdfbase import pdfmetrics

HERE = Path(__file__).resolve().parent
OUT = HERE / "corel"
FONT_DIR = Path("/tmp/fonts-stickers")

FONT_ALIAS = {"M": "Regular", "MM": "Medium", "MS": "SemiBold", "MB": "Bold"}
CUT_COLOR = "#FF00FF"
LAYER_NAMES = {
    "bg": "0 · Фон листа",
    "stickers": "1 · Наклейки",
    "cut": "2 · Контуры реза",
}


# ── шрифты в кривые ─────────────────────────────────────────────────────────
class GlyphCache:
    """Обводки глифов из TTF, чтобы текст стал кривыми."""

    def __init__(self) -> None:
        self._fonts: dict[str, tuple] = {}

    def _load(self, alias: str):
        if alias not in self._fonts:
            path = FONT_DIR / f"Montserrat-{FONT_ALIAS[alias]}.ttf"
            font = TTFont(str(path))
            self._fonts[alias] = (font, font.getGlyphSet(), font.getBestCmap(),
                                  font["head"].unitsPerEm)
        return self._fonts[alias]

    def path(self, text: str, alias: str, size: float, x: float, y: float) -> str:
        font, glyphs, cmap, upem = self._load(alias)
        scale = size / upem
        chunks = []
        pen_x = x
        for ch in text:
            gname = cmap.get(ord(ch))
            if gname is None:
                continue
            glyph = glyphs[gname]
            spen = SVGPathPen(glyphs, ntos=lambda v: f"{v:.2f}")
            tpen = TransformPen(spen, (scale, 0, 0, scale, pen_x, y))
            glyph.draw(tpen)
            d = spen.getCommands()
            if d:
                chunks.append(d)
            pen_x += glyph.width * scale
        return " ".join(chunks)


GLYPHS = GlyphCache()


# ── записывающий «canvas» ───────────────────────────────────────────────────
class Recorder:
    """Повторяет тот минимум canvas API, который нужен иконкам и тексту."""

    def __init__(self) -> None:
        self.ctm = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
        self.fill = "#000000"
        self.stroke = "#000000"
        self.line_width = 1.0
        self.line_cap = "butt"
        self.line_join = "miter"
        self.font = ("M", 10.0)
        self._state: list[tuple] = []
        self._out: list[str] = []
        self._stack: list[list[str]] = [self._out]
        self._pending_id: str | None = None

    # --- вывод
    def _emit(self, attrs: dict, d: str) -> None:
        if self._pending_id:
            attrs = {"id": self._pending_id, **attrs}
            self._pending_id = None
        body = " ".join(f'{k}="{v}"' for k, v in attrs.items() if v is not None)
        self._stack[-1].append(f"<path d='{d}' {body}/>")

    def _matrix(self) -> str | None:
        a, b, c, d, e, f = self.ctm
        if (a, b, c, d) == (1.0, 0.0, 0.0, 1.0):
            return f"translate({e:.3f} {f:.3f})" if (e, f) != (0.0, 0.0) else None
        return f"matrix({a:.4f} {b:.4f} {c:.4f} {d:.4f} {e:.3f} {f:.3f})"

    def _paint(self, fill: float, stroke: float) -> dict:
        return {
            "fill": self.fill if fill else "none",
            "stroke": self.stroke if stroke else "none",
            "stroke-width": f"{self.line_width:.3f}" if stroke else None,
            "stroke-linecap": self.line_cap if stroke else None,
            "stroke-linejoin": self.line_join if stroke else None,
            "transform": self._matrix(),
        }

    # --- группы
    def begin_group(self, gid: str, label: str,
                    translate: tuple[float, float] | None = None) -> None:
        # трансформацию несёт каждый путь: координаты внутри группы — страничные
        attrs = [f'id="{gid}"', f'inkscape:label="{_attr(label)}"',
                 'inkscape:groupmode="group"']
        self._stack[-1].append(f"<g {' '.join(attrs)}>")
        self._stack.append([])
        # состояние снимаем ДО сдвига, иначе группы накапливают трансформацию
        self._state.append((self.ctm, self.fill, self.stroke, self.line_width,
                            self.line_cap, self.line_join, self.font))
        if translate:
            self.ctm = _mat_mul(self.ctm, (1.0, 0.0, 0.0, 1.0, translate[0], translate[1]))

    def end_group(self) -> None:
        self.ctm, self.fill, self.stroke, self.line_width, self.line_cap, self.line_join, self.font = \
            self._state.pop()
        body = self._stack.pop()
        self._stack[-1].extend(body)
        self._stack[-1].append("</g>")

    # --- состояние
    def saveState(self) -> None:
        self._state.append((self.ctm, self.fill, self.stroke, self.line_width,
                            self.line_cap, self.line_join, self.font))

    def restoreState(self) -> None:
        self.ctm, self.fill, self.stroke, self.line_width, self.line_cap, self.line_join, self.font = \
            self._state.pop()

    def setFillColor(self, color) -> None:
        self.fill = _hex(color)

    def setStrokeColor(self, color) -> None:
        self.stroke = _hex(color)

    def setLineWidth(self, w: float) -> None:
        self.line_width = float(w)

    def setLineCap(self, cap) -> None:
        self.line_cap = {0: "butt", 1: "round", 2: "square"}.get(cap, "butt")

    def setLineJoin(self, join) -> None:
        self.line_join = {0: "miter", 1: "round", 2: "bevel"}.get(join, "miter")

    def set_id(self, ident: str) -> None:
        self._pending_id = ident

    def setFont(self, name: str, size: float) -> None:
        self.font = (name, float(size))

    def translate(self, tx: float, ty: float) -> None:
        self.ctm = _mat_mul(self.ctm, (1.0, 0.0, 0.0, 1.0, tx, ty))

    def scale(self, sx: float, sy: float) -> None:
        self.ctm = _mat_mul(self.ctm, (sx, 0.0, 0.0, sy, 0.0, 0.0))

    def rotate(self, deg: float) -> None:
        r = math.radians(deg)
        c, s = math.cos(r), math.sin(r)
        self.ctm = _mat_mul(self.ctm, (c, s, -s, c, 0.0, 0.0))

    # --- пути
    def beginPath(self):
        return _Path()

    def drawPath(self, path, stroke=1, fill=0) -> None:
        d = path.d()
        if not d:
            return
        self._emit(self._paint(fill, stroke), d)

    def rect(self, x, y, w, h, stroke=1, fill=0) -> None:
        d = f"M{x:.2f} {y:.2f} h{w:.2f} v{h:.2f} h{-w:.2f} Z"
        self._emit(self._paint(fill, stroke), d)

    def roundRect(self, x, y, w, h, r, stroke=1, fill=0) -> None:
        r = min(r, w / 2, h / 2)
        d = (f"M{x + r:.2f} {y:.2f} h{w - 2 * r:.2f} "
             f"a{r:.2f} {r:.2f} 0 0 1 {r:.2f} {r:.2f} "
             f"v{h - 2 * r:.2f} "
             f"a{r:.2f} {r:.2f} 0 0 1 {-r:.2f} {r:.2f} "
             f"h{-(w - 2 * r):.2f} "
             f"a{r:.2f} {r:.2f} 0 0 1 {-r:.2f} {-r:.2f} "
             f"v{-(h - 2 * r):.2f} "
             f"a{r:.2f} {r:.2f} 0 0 1 {r:.2f} {-r:.2f} Z")
        self._emit(self._paint(fill, stroke), d)

    def circle(self, x, y, r, stroke=1, fill=0) -> None:
        self.ellipse(x - r, y - r, x + r, y + r, stroke=stroke, fill=fill)

    def ellipse(self, x1, y1, x2, y2, stroke=1, fill=0) -> None:
        rx, ry = (x2 - x1) / 2, (y2 - y1) / 2
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        d = (f"M{x1:.2f} {cy:.2f} "
             f"a{rx:.2f} {ry:.2f} 0 0 1 {rx:.2f} {-ry:.2f} "
             f"a{rx:.2f} {ry:.2f} 0 0 1 {rx:.2f} {ry:.2f} "
             f"a{rx:.2f} {ry:.2f} 0 0 1 {-rx:.2f} {ry:.2f} "
             f"a{rx:.2f} {ry:.2f} 0 0 1 {-rx:.2f} {-ry:.2f} Z")
        self._emit(self._paint(fill, stroke), d)

    def arc(self, x1, y1, x2, y2, startAng=0, extent=90) -> None:
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        rx, ry = (x2 - x1) / 2, (y2 - y1) / 2
        d = _arc_segments(cx, cy, rx, ry, startAng, extent)
        self._emit(self._paint(0, 1), d)

    def line(self, x1, y1, x2, y2) -> None:
        d = f"M{x1:.2f} {y1:.2f} L{x2:.2f} {y2:.2f}"
        self._emit(self._paint(0, 1), d)

    # --- текст (в кривые)
    def drawString(self, x, y, text) -> None:
        alias, size = self.font
        d = GLYPHS.path(text, alias, size, x, y)
        if d:
            self._emit(self._paint(1, 0), d)

    def drawCentredString(self, x, y, text) -> None:
        alias, size = self.font
        w = pdfmetrics.stringWidth(text, alias, size)
        self.drawString(x - w / 2, y, text)

    def drawRightString(self, x, y, text) -> None:
        alias, size = self.font
        w = pdfmetrics.stringWidth(text, alias, size)
        self.drawString(x - w, y, text)

    # --- сборка
    def body(self) -> str:
        return "\n".join(self._out)


class _Path:
    def __init__(self) -> None:
        self.cmds: list[str] = []

    def moveTo(self, x, y) -> None:
        self.cmds.append(f"M{x:.2f} {y:.2f}")

    def lineTo(self, x, y) -> None:
        self.cmds.append(f"L{x:.2f} {y:.2f}")

    def curveTo(self, x1, y1, x2, y2, x3, y3) -> None:
        self.cmds.append(f"C{x1:.2f} {y1:.2f} {x2:.2f} {y2:.2f} {x3:.2f} {y3:.2f}")

    def close(self) -> None:
        self.cmds.append("Z")

    def d(self) -> str:
        return " ".join(self.cmds)


def _mat_mul(m, n):
    a1, b1, c1, d1, e1, f1 = m
    a2, b2, c2, d2, e2, f2 = n
    return (a1 * a2 + c1 * b2, b1 * a2 + d1 * b2,
            a1 * c2 + c1 * d2, b1 * c2 + d1 * d2,
            a1 * e2 + c1 * f2 + e1, b1 * e2 + d1 * f2 + f1)


def _attr(text: str) -> str:
    return escape(text, {'"': '&quot;'})


def _hex(color) -> str:
    r = max(0, min(255, round(color.red * 255)))
    g = max(0, min(255, round(color.green * 255)))
    b = max(0, min(255, round(color.blue * 255)))
    return f"#{r:02X}{g:02X}{b:02X}"


def _arc_segments(cx, cy, rx, ry, a0, a1) -> str:
    """Эллиптическая дуга кубическими Безье — как в PDF, только кривыми."""
    total = a1 - a0
    steps = max(1, math.ceil(abs(total) / 90))
    step = total / steps
    out = []
    for i in range(steps):
        t0 = math.radians(a0 + step * i)
        t1 = math.radians(a0 + step * (i + 1))
        k = 4 / 3 * math.tan((t1 - t0) / 4)
        p0 = (cx + rx * math.cos(t0), cy + ry * math.sin(t0))
        p1 = (cx + rx * math.cos(t1), cy + ry * math.sin(t1))
        c0 = (p0[0] - k * rx * math.sin(t0), p0[1] + k * ry * math.cos(t0))
        c1 = (p1[0] + k * rx * math.sin(t1), p1[1] - k * ry * math.cos(t1))
        out.append(f"M{p0[0]:.2f} {p0[1]:.2f}"
                   f" C{c0[0]:.2f} {c0[1]:.2f} {c1[0]:.2f} {c1[1]:.2f}"
                   f" {p1[0]:.2f} {p1[1]:.2f}")
    return " ".join(out)


# ── сборка листа ────────────────────────────────────────────────────────────
def layout(batch) -> list[tuple[float, float]]:
    """Координаты центров наклеек на листе — как в PDF."""
    rows = [batch[i:i + bs.COLS] for i in range(0, len(batch), bs.COLS)]
    grid_w = bs.COLS * bs.PITCH
    x0 = (bs.PW - grid_w) / 2 + bs.PITCH / 2
    y_top = bs.PH / 2 + (len(rows) - 1) * bs.PITCH / 2
    out = []
    for r, row in enumerate(rows):
        shift = (bs.COLS - len(row)) * bs.PITCH / 2
        for col in range(len(row)):
            out.append((x0 + col * bs.PITCH + shift, y_top - r * bs.PITCH))
    return out


SVG_HEAD = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<svg xmlns="http://www.w3.org/2000/svg" '
    'xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" '
    'width="210mm" height="297mm" viewBox="0 0 {w:.4f} {h:.4f}" version="1.1">\n'
    '<title>{title}</title>\n'
    '<desc>{desc}</desc>\n'
)
FLIP = 'transform="translate(0 {h:.4f}) scale(1 -1)"'


def layer_open(key: str, h: float) -> str:
    return (f'<g id="layer-{key}" inkscape:groupmode="layer" '
            f'inkscape:label="{_attr(LAYER_NAMES[key])}" {FLIP.format(h=h)}>\n')


def build_sheet(batch, sheet_no: int, total_sheets: int, first_no: int) -> str:
    spots = layout(batch)

    # 1 · наклейки: каждая — своя группа
    st = Recorder()
    for i, (item, (cx, cy)) in enumerate(zip(batch, spots)):
        n = first_no + i
        ru, en = item[0], item[1]
        st.begin_group(f"sticker-{n:02d}", f"{n:02d} · {en} ({ru})", (cx, cy))
        bs.draw_sticker(st, 0, 0, item, show_cut=False)
        st.end_group()

    # 2 · контуры реза: отдельные объекты поверх графики
    cut = Recorder()
    cut.setStrokeColor(bs.CUT_COLOR)
    cut.setLineWidth(0.35)
    for i, (item, (cx, cy)) in enumerate(zip(batch, spots)):
        cut.set_id(f"cut-{first_no + i:02d}")
        cut.drawPath(bs.scallop_path(cut, cx, cy, bs.R_CUT), stroke=1, fill=0)

    w, h = bs.PW, bs.PH
    out = [SVG_HEAD.format(w=w, h=h,
                           title=f"SM Production · наклейки EN+RU · лист {sheet_no} из {total_sheets}",
                           desc="Слой 1 — наклейки, каждая сгруппирована. "
                                "Слой 2 — контуры реза Ø 35 мм, поверх графики.")]
    out.append(layer_open("bg", h))
    out.append(f'<path d="M0 0 h{w:.3f} v{h:.3f} h{-w:.3f} Z" fill="#FFFFFF" stroke="none"/>')
    out.append("</g>\n")
    out.append(layer_open("stickers", h))
    out.append(st.body())
    out.append("\n</g>\n")
    out.append(layer_open("cut", h))
    out.append(cut.body())
    out.append("\n</g>\n</svg>\n")
    return "".join(out)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    batches = bs.sheet_batches()
    total = len(batches)
    first = 1
    for i, batch in enumerate(batches, start=1):
        svg = build_sheet(batch, i, total, first)
        dst = OUT / f"stickers-sheet-{i:02d}.svg"
        dst.write_text(svg, encoding="utf-8")
        print(f"  {dst.name}: {dst.stat().st_size // 1024} КБ · наклеек {len(batch)} · "
              f"групп {len(batch)} · контуров {len(batch)}")
        first += len(batch)
    print(f"  всего листов {total}, наклеек {len(bs.ITEMS)}")
    main_pdf()


# ── PDF для печати и резки ──────────────────────────────────────────────────
def pdf_sheet(batch, sheet_no: int, total: int, *, with_art: bool, with_cut: bool,
              path: Path) -> None:
    """PDF листа: графика CMYK, контуры — spot-цветом CutContour."""
    from reportlab.pdfgen import canvas as rcanvas
    from reportlab.lib.colors import CMYKColorSep

    c = rcanvas.Canvas(str(path), pagesize=(bs.PW, bs.PH))
    if with_art:
        for item, (cx, cy) in zip(batch, layout(batch)):
            bs.draw_sticker(c, cx, cy, item, show_cut=False)
    if with_cut:
        spot = CMYKColorSep(0, 1, 0, 0, spotName="CutContour", density=1)
        c.setStrokeColor(spot)
        c.setLineWidth(0.35)
        for cx, cy in layout(batch):
            c.drawPath(bs.scallop_path(c, cx, cy, bs.R_CUT), stroke=1, fill=0)
    c.setTitle(f"SM Production · наклейки · лист {sheet_no} из {total}")
    c.setAuthor("SM Production")
    c.showPage()
    c.save()


def main_pdf() -> None:
    import pymupdf

    batches = bs.sheet_batches()
    total = len(batches)
    made = []
    for i, batch in enumerate(batches, start=1):
        art = OUT / f"pechat-sheet-{i:02d}.pdf"
        cut = OUT / f"rez-sheet-{i:02d}.pdf"
        both = OUT / f"pechat-i-rez-sheet-{i:02d}.pdf"
        pdf_sheet(batch, i, total, with_art=True, with_cut=False, path=art)
        pdf_sheet(batch, i, total, with_art=False, with_cut=True, path=cut)
        pdf_sheet(batch, i, total, with_art=True, with_cut=True, path=both)
        made += [art, cut, both]

    # сверка: spot-цвет действительно попал в файл
    for p in sorted(OUT.glob("rez-sheet-*.pdf")):
        doc = pymupdf.open(p)
        page = doc[0]
        drawings = page.get_drawings()
        print(f"  {p.name}: объектов {len(drawings)} · {p.stat().st_size // 1024} КБ")
        break


if __name__ == "__main__":
    main()
