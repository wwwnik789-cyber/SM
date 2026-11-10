#!/usr/bin/env python3
"""Build two horizontal vector banners for the marked lower facade zones."""
from __future__ import annotations

import gzip
import io
import re
import tempfile
from pathlib import Path

import resvg_py
import vtracer
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
SOURCE_LOGO = REPO / "presentations" / "anikom-arena-branding" / "assets" / "anikom-arena-logo.png"
SOURCE_PHOTO = ROOT / "source" / "marked-locations.jpg"

NAVY = "#091A2B"
NAVY_LIGHT = "#102B45"
RED = "#D94B43"
WHITE = "#FFFFFF"
LOGO_VIEWBOX = "25 174 836 823"

BANNERS = [
    {
        "key": "left",
        "label": "ЛЕВЫЙ БАННЕР",
        "width": 2800,
        "height": 1000,
        "svg": "anikom-arena-lower-left-2800x1000.svg",
        "svgz": "anikom-arena-lower-left-2800x1000.svgz",
        "preview": "preview-left-1400x500.png",
        "preview_size": (1400, 500),
        "photo_box": (199, 563, 322, 607),
    },
    {
        "key": "right",
        "label": "ПРАВЫЙ БАННЕР",
        "width": 4000,
        "height": 1000,
        "svg": "anikom-arena-lower-right-4000x1000.svg",
        "svgz": "anikom-arena-lower-right-4000x1000.svgz",
        "preview": "preview-right-1600x400.png",
        "preview_size": (1600, 400),
        "photo_box": (1218, 550, 1536, 629),
    },
]


def trace_logo_paths() -> str:
    """Convert the supplied transparent logo into font-independent paths."""
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


def grid_uses(width: int) -> str:
    uses: list[str] = []
    x = 55
    col = 0
    while x <= width - 235:
        for row, y in enumerate((70, 405, 740)):
            opacity = 0.34 if (row + col) % 2 == 0 else 0.23
            uses.append(
                f'    <use href="#arena-logo" x="{x}" y="{y}" width="190" height="187" opacity="{opacity:.2f}"/>'
            )
        x += 335
        col += 1
    return "\n".join(uses)


def make_svg(width: int, height: int, paths: str) -> str:
    center = width / 2
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
     xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
     width="{width}mm" height="{height}mm" viewBox="0 0 {width} {height}">
  <title>Аником Арена — горизонтальный баннер {width} × {height} мм</title>
  <desc>Векторный макет: основной логотип в центре и мелкая повторяющаяся сетка.</desc>
  <metadata>Предварительный размер по пропорциям фотографии. Перед печатью требуется обмер.</metadata>
  <defs>
    <symbol id="arena-logo" viewBox="{LOGO_VIEWBOX}" preserveAspectRatio="xMidYMid meet">
{paths}
    </symbol>
    <radialGradient id="center-glow" cx="50%" cy="50%" r="55%">
      <stop offset="0" stop-color="{NAVY_LIGHT}" stop-opacity="1"/>
      <stop offset="1" stop-color="{NAVY}" stop-opacity="0.97"/>
    </radialGradient>
  </defs>

  <g id="BACKGROUND" inkscape:groupmode="layer" inkscape:label="ФОН">
    <rect x="0" y="0" width="{width}" height="{height}" fill="{NAVY}"/>
    <path d="M0 0 H430 L700 {height} H0 Z" fill="{RED}" opacity="0.17"/>
    <path d="M{width} 0 H{width - 430} L{width - 700} {height} H{width} Z" fill="{RED}" opacity="0.11"/>
    <rect x="12" y="12" width="{width - 24}" height="{height - 24}" fill="none" stroke="{RED}" stroke-width="24"/>
  </g>

  <g id="PRESS_WALL_GRID" inkscape:groupmode="layer" inkscape:label="МЕЛКАЯ СЕТКА">
{grid_uses(width)}
  </g>

  <g id="CENTER_FIELD" inkscape:groupmode="layer" inkscape:label="ЦЕНТРАЛЬНОЕ ПОЛЕ">
    <ellipse cx="{center:g}" cy="500" rx="455" ry="455" fill="url(#center-glow)"/>
    <ellipse cx="{center:g}" cy="500" rx="425" ry="425" fill="none" stroke="{RED}" stroke-width="16"/>
  </g>

  <g id="MAIN_LOGO" inkscape:groupmode="layer" inkscape:label="ОСНОВНОЙ ЛОГОТИП">
    <use href="#arena-logo" x="{center - 355:g}" y="150" width="710" height="700"/>
  </g>
</svg>
'''


def render_svg(svg_path: Path, output_path: Path, size: tuple[int, int]) -> None:
    rendered = resvg_py.svg_to_bytes(
        svg_path=str(svg_path),
        width=size[0],
        height=size[1],
        dpi=96,
    )
    with Image.open(io.BytesIO(rendered)) as image:
        exact = ImageOps.fit(image.convert("RGBA"), size, Image.Resampling.LANCZOS)
        exact.save(output_path, optimize=True)


def build_files() -> None:
    paths = trace_logo_paths()
    for item in BANNERS:
        svg_path = ROOT / item["svg"]
        svgz_path = ROOT / item["svgz"]
        preview_path = ROOT / item["preview"]
        svg_path.write_text(make_svg(item["width"], item["height"], paths), encoding="utf-8")
        svgz_path.write_bytes(gzip.compress(svg_path.read_bytes(), compresslevel=9, mtime=0))
        render_svg(svg_path, preview_path, item["preview_size"])


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{name}", size)


def build_clean_preview() -> None:
    board = Image.new("RGB", (1600, 1100), "#E7EDF2")
    draw = ImageDraw.Draw(board)
    draw.text((70, 42), "ГОРИЗОНТАЛЬНЫЕ БАННЕРЫ • ДВЕ ОТМЕЧЕННЫЕ ЗОНЫ", font=font(27, True), fill="#172330")

    left = Image.open(ROOT / BANNERS[0]["preview"]).convert("RGB")
    left = ImageOps.fit(left, (1400, 500), Image.Resampling.LANCZOS)
    board.paste(left, (100, 105))
    draw.text((100, 622), "ЛЕВЫЙ • ПРОПОРЦИЯ 2,8:1 • ПРЕДВАРИТЕЛЬНО 2800 × 1000 ММ", font=font(19, True), fill="#172330")

    right = Image.open(ROOT / BANNERS[1]["preview"]).convert("RGB")
    right = ImageOps.fit(right, (1400, 350), Image.Resampling.LANCZOS)
    board.paste(right, (100, 688))
    draw.text((100, 1050), "ПРАВЫЙ • ПРОПОРЦИЯ 4:1 • ПРЕДВАРИТЕЛЬНО 4000 × 1000 ММ", font=font(19, True), fill="#172330")
    board.save(ROOT / "banners-preview-1600x1100.jpg", quality=93, optimize=True, progressive=True)


def build_photo_mockup() -> None:
    photo = Image.open(SOURCE_PHOTO).convert("RGB")
    for item in BANNERS:
        banner = Image.open(ROOT / item["preview"]).convert("RGB")
        box = item["photo_box"]
        fitted = ImageOps.fit(
            banner,
            (box[2] - box[0], box[3] - box[1]),
            Image.Resampling.LANCZOS,
        )
        photo.paste(fitted, (box[0], box[1]))
    photo.save(ROOT / "placement-preview.jpg", quality=94, optimize=True, progressive=True)


def validate() -> None:
    for item in BANNERS:
        svg_path = ROOT / item["svg"]
        svgz_path = ROOT / item["svgz"]
        text = svg_path.read_text(encoding="utf-8")
        assert f'width="{item["width"]}mm" height="{item["height"]}mm"' in text
        assert f'viewBox="0 0 {item["width"]} {item["height"]}"' in text
        assert "<image" not in text and "<text" not in text
        assert gzip.decompress(svgz_path.read_bytes()) == svg_path.read_bytes()
        with Image.open(ROOT / item["preview"]) as preview:
            assert preview.size == item["preview_size"]
    with Image.open(ROOT / "placement-preview.jpg") as mockup:
        assert mockup.size == (1536, 786)


def main() -> None:
    build_files()
    build_clean_preview()
    build_photo_mockup()
    validate()
    for path in sorted(ROOT.iterdir()):
        if path.is_file():
            print(path.name, path.stat().st_size)


if __name__ == "__main__":
    main()
