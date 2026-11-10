#!/usr/bin/env python3
"""Build a print-size vector banner for the Anikom Arena TV tower."""
from __future__ import annotations

import gzip
import re
import tempfile
from pathlib import Path

import resvg_py
import vtracer
from PIL import Image

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
SOURCE_LOGO = REPO / "presentations" / "anikom-arena-branding" / "assets" / "anikom-arena-logo.png"
SVG_OUT = ROOT / "anikom-arena-tv-tower-banner-4000x4000.svg"
SVGZ_OUT = ROOT / "anikom-arena-tv-tower-banner-4000x4000.svgz"
PREVIEW_OUT = ROOT / "preview-1200x1200.png"

FINAL_MM = 4000
LOGO_VIEWBOX = "25 174 836 823"
NAVY = "#091A2B"
NAVY_LIGHT = "#102B45"
RED = "#D94B43"
WHITE = "#FFFFFF"


def trace_logo_paths() -> str:
    """Trace the supplied transparent logo into font-independent SVG paths."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        mask_path = tmp / "logo-mask.png"
        trace_path = tmp / "logo-trace.svg"

        logo = Image.open(SOURCE_LOGO).convert("RGBA")
        alpha = logo.getchannel("A")
        mask = Image.new("L", logo.size, 255)
        mask.paste(0, mask=alpha)
        mask.save(mask_path)

        vtracer.convert_image_to_svg_py(
            str(mask_path),
            str(trace_path),
            colormode="binary",
            hierarchical="stacked",
            mode="spline",
            filter_speckle=2,
            corner_threshold=60,
            length_threshold=4.0,
            max_iterations=10,
            splice_threshold=45,
            path_precision=3,
        )
        traced = trace_path.read_text(encoding="utf-8")

    paths = "\n".join(re.findall(r"<path\b[^>]*/>", traced))
    if not paths:
        raise RuntimeError("Logo tracing produced no vector paths")
    return paths.replace('fill="#000000"', f'fill="{WHITE}"')


def grid_uses() -> str:
    """Build a regular small-logo grid around the central logo."""
    uses: list[str] = []
    x_positions = [145, 715, 1285, 1855, 2425, 2995, 3565]
    y_positions = [145, 715, 1285, 1855, 2425, 2995, 3565]
    for row, y in enumerate(y_positions):
        for col, x in enumerate(x_positions):
            opacity = 0.34 if (row + col) % 2 == 0 else 0.24
            uses.append(
                f'    <use href="#arena-logo" x="{x}" y="{y}" width="290" height="286" opacity="{opacity:.2f}"/>'
            )
    return "\n".join(uses)


def build_svg() -> None:
    paths = trace_logo_paths()
    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
     xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
     width="{FINAL_MM}mm" height="{FINAL_MM}mm" viewBox="0 0 {FINAL_MM} {FINAL_MM}">
  <title>Аником Арена — баннер для телебашни 4000 × 4000 мм</title>
  <desc>Полностью векторный макет: центральный логотип и мелкая повторяющаяся сетка.</desc>
  <metadata>Финальный размер 4000 × 4000 мм. Масштаб 1:1. Все знаки переведены в векторные контуры.</metadata>
  <defs>
    <symbol id="arena-logo" viewBox="{LOGO_VIEWBOX}" preserveAspectRatio="xMidYMid meet">
{paths}
    </symbol>
    <radialGradient id="center-glow" cx="50%" cy="50%" r="50%">
      <stop offset="0" stop-color="{NAVY_LIGHT}" stop-opacity="1"/>
      <stop offset="0.72" stop-color="{NAVY}" stop-opacity="0.98"/>
      <stop offset="1" stop-color="{NAVY}" stop-opacity="0.94"/>
    </radialGradient>
  </defs>

  <g id="BACKGROUND" inkscape:groupmode="layer" inkscape:label="ФОН">
    <rect x="0" y="0" width="4000" height="4000" fill="{NAVY}"/>
    <path d="M0 0 H760 L1250 4000 H0 Z" fill="{RED}" opacity="0.18"/>
    <path d="M4000 0 H3400 L2920 4000 H4000 Z" fill="{RED}" opacity="0.10"/>
    <rect x="30" y="30" width="3940" height="3940" fill="none" stroke="{RED}" stroke-width="34"/>
  </g>

  <g id="PRESS_WALL_GRID" inkscape:groupmode="layer" inkscape:label="МЕЛКАЯ СЕТКА">
{grid_uses()}
  </g>

  <g id="CENTER_FIELD" inkscape:groupmode="layer" inkscape:label="ЦЕНТРАЛЬНОЕ ПОЛЕ">
    <circle cx="2000" cy="2000" r="1120" fill="url(#center-glow)"/>
    <circle cx="2000" cy="2000" r="1085" fill="none" stroke="{RED}" stroke-width="26" opacity="0.95"/>
  </g>

  <g id="MAIN_LOGO" inkscape:groupmode="layer" inkscape:label="ОСНОВНОЙ ЛОГОТИП">
    <use href="#arena-logo" x="1090" y="1105" width="1820" height="1790"/>
  </g>
</svg>
'''
    SVG_OUT.write_text(svg, encoding="utf-8")


def render_outputs() -> None:
    """Build a compressed SVG for downloading and a small approval preview."""
    SVGZ_OUT.write_bytes(gzip.compress(SVG_OUT.read_bytes(), compresslevel=9, mtime=0))
    preview = resvg_py.svg_to_bytes(
        svg_path=str(SVG_OUT),
        width=1200,
        height=1200,
        dpi=96,
    )
    PREVIEW_OUT.write_bytes(preview)


def validate() -> None:
    text = SVG_OUT.read_text(encoding="utf-8")
    assert 'width="4000mm"' in text and 'height="4000mm"' in text
    assert 'viewBox="0 0 4000 4000"' in text
    assert "<image" not in text
    assert "<text" not in text
    assert text.count("<path") >= 2
    assert text.count('href="#arena-logo"') == 50
    assert gzip.decompress(SVGZ_OUT.read_bytes()) == SVG_OUT.read_bytes()
    with Image.open(PREVIEW_OUT) as preview:
        assert preview.size == (1200, 1200)


def main() -> None:
    build_svg()
    render_outputs()
    validate()
    print(SVG_OUT)
    print(SVGZ_OUT)
    print(PREVIEW_OUT)


if __name__ == "__main__":
    main()
