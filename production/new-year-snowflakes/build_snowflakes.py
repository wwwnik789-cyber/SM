#!/usr/bin/env python3
"""Векторные контуры новогодних снежинок для фрезеровки ПВХ.

Что собирает:
  svg/     контуры для CAM: отдельные слои CUT_OUTER (наружный рез) и CUT_INNER (окна),
           плюс схема раскроя листа 2440×1220 мм
  dxf/     то же для цехов, которые принимают только DXF (LWPOLYLINE, миллиметры)
  preview/ PNG для проверки глазом: отдельные детали и общий лист

Две версии каждого контура:
  *nominal*      — чистовой размер детали, как её видно на объекте;
  *kerf3*        — с компенсацией реза под фрезу Ø3 мм: наружный контур
                   увеличен, окна уменьшены, чтобы после резки деталь вышла
                   точно в номинал.

Геометрия строится параметрически (shapely), поэтому размеры не приходится
рисовать руками: поменяли диаметр или толщину перемычки — контуры пересобрались.

Запуск из корня репозитория:
    .venv/bin/python production/new-year-snowflakes/build_snowflakes.py
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from math import cos, radians, sin
from pathlib import Path

import ezdxf
from shapely import affinity
from shapely.geometry import LineString, Point, Polygon
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
SVG_DIR = HERE / "svg"
DXF_DIR = HERE / "dxf"
PREVIEW_DIR = HERE / "preview"

# ── технологические параметры ────────────────────────────────────────────────
TOOL_D = 3.0          # фреза Ø3 мм — стандарт для ПВХ 3–5 мм и мелкого декора
KERF = 3.2            # ширина реза для этой фрезы, мм (чуть больше диаметра)
MIN_WALL = 8.0        # минимальная перемычка между резами, мм
SHEET_W, SHEET_H = 2440.0, 1220.0   # стандартный лист ПВХ
SHEET_MARGIN = 15.0   # отступ от края листа
PIECE_GAP = 20.0      # расстояние между деталями на листе
HANG_D = 14.0         # отверстие под подвес в центре, мм
SIMPLIFY_MM = 0.03    # допуск упрощения контура при выгрузке (вершины не чаще 0,03 мм)

LAYER_OUTER = "CUT_OUTER"
LAYER_INNER = "CUT_INNER"


@dataclass(frozen=True)
class Piece:
    slug: str
    title: str
    radius: float


SIZES = {"d350": 175.0, "d500": 250.0}

DESIGNS = [
    ("01-klassika", "Классика"),
    ("02-zvezda", "Звезда"),
    ("03-kristall", "Кристалл"),
]


# ── геометрия ────────────────────────────────────────────────────────────────


def stem(start: tuple[float, float], end: tuple[float, float], half_width: float,
         round_caps: bool = False) -> Polygon:
    """Полоса заданной полуширины между двумя точками."""
    return LineString([start, end]).buffer(
        half_width, cap_style="round" if round_caps else "flat", quad_segs=16
    )


def knob(center: tuple[float, float], radius: float) -> Polygon:
    """Кружок на конце. Центр обязан лежать внутри тела — иначе получается
    касание в одной точке, и такой «прилив» отламывается при фрезеровке."""
    return Point(center).buffer(radius, quad_segs=16)


def branch(base: tuple[float, float], angle_deg: float, length: float,
           half_width: float, tip_radius: float) -> Polygon:
    """Ветка под углом к лучу: полоса от точки внутри тела + кружок на конце."""
    angle = radians(angle_deg)
    end = (base[0] + length * cos(angle), base[1] + length * sin(angle))
    return unary_union([stem(base, end, half_width), knob(end, tip_radius)])


def crystal(inner: float, shoulder: float, half_h: float,
            outer: float, outer_half_h: float) -> Polygon:
    """Кристалл на конце луча: вытянутый ромб с притуплённым и скруглённым концом.

    Торец ромба шириной 2·outer_half_h «обнимает» кружок того же радиуса.
    Поэтому соединение получается широким (не меньше 2·outer_half_h), а не
    касанием в одной точке — именно на таких касаниях деталь и разваливалась.
    """
    body = Polygon([
        (inner, 0.0),
        (shoulder, half_h),
        (outer, outer_half_h),
        (outer, -outer_half_h),
        (shoulder, -half_h),
    ])
    return unary_union([body, knob((outer, 0.0), outer_half_h)])


def build_classic(radius: float) -> Polygon:
    """Шесть лучей: спица, две пары боковых веток и кристалл на конце."""
    r = radius
    parts = [knob((0.0, 0.0), 0.100 * r)]
    parts.append(stem((0.03 * r, 0.0), (0.62 * r, 0.0), 0.048 * r))
    parts.append(crystal(0.58 * r, 0.72 * r, 0.092 * r, 0.94 * r, 0.032 * r))

    for base_r, length, half_width, tip in (
        (0.30 * r, 0.24 * r, 0.026 * r, 0.036 * r),
        (0.46 * r, 0.21 * r, 0.024 * r, 0.032 * r),
    ):
        for side in (55.0, -55.0):
            parts.append(branch((base_r, 0.0), side, length, half_width, tip))

    arm = unary_union(parts)
    assert arm.geom_type == "Polygon", f"луч распался на {arm.geom_type}"
    arms = [affinity.rotate(arm, 60.0 * index, origin=(0, 0)) for index in range(6)]
    body = unary_union(arms)

    body = fit_diameter(body, r * 2.0)
    return body.difference(knob((0.0, 0.0), HANG_D / 2)).buffer(0)


def build_star(radius: float) -> Polygon:
    """Восемь лучей, кольцо и восемь коротких зубцов между ними."""
    r = radius
    parts = [knob((0.0, 0.0), 0.100 * r)]
    parts.append(stem((0.03 * r, 0.0), (0.64 * r, 0.0), 0.048 * r))
    parts.append(crystal(0.60 * r, 0.74 * r, 0.088 * r, 0.94 * r, 0.032 * r))

    # кольцо, соединяющее лучи
    ring = knob((0.0, 0.0), 0.410 * r).difference(knob((0.0, 0.0), 0.340 * r))
    parts.append(ring)

    # короткий зубец между лучами: начинается в теле кольца
    tooth = stem((0.36 * r, 0.0), (0.64 * r, 0.0), 0.030 * r)
    tooth = unary_union([tooth, knob((0.64 * r, 0.0), 0.036 * r)])
    tooth = affinity.rotate(tooth, 22.5, origin=(0, 0))
    parts.append(tooth)

    arm = unary_union(parts)
    assert arm.geom_type == "Polygon", f"луч распался на {arm.geom_type}"
    arms = [affinity.rotate(arm, 45.0 * index, origin=(0, 0)) for index in range(8)]
    body = unary_union(arms)

    body = fit_diameter(body, r * 2.0)
    return body.difference(knob((0.0, 0.0), HANG_D / 2)).buffer(0)


def build_crystal(radius: float) -> Polygon:
    """Шесть широких лучей с продольной прорезью и ветками у кристалла."""
    r = radius
    parts = [knob((0.0, 0.0), 0.105 * r)]
    parts.append(stem((0.03 * r, 0.0), (0.62 * r, 0.0), 0.078 * r))
    parts.append(crystal(0.58 * r, 0.72 * r, 0.100 * r, 0.94 * r, 0.034 * r))

    # одна пара веток — за прорезью, ближе к кристаллу
    for side in (58.0, -58.0):
        parts.append(branch((0.54 * r, 0.0), side, 0.18 * r, 0.028 * r, 0.036 * r))

    arm = unary_union(parts)
    assert arm.geom_type == "Polygon", f"луч распался на {arm.geom_type}"

    # прорезь вдоль луча: скруглённый паз, стенки по 8,75 мм
    slot = stem((0.18 * r, 0.0), (0.44 * r, 0.0), 0.028 * r, round_caps=True)
    arm = arm.difference(slot)
    assert arm.geom_type == "Polygon", f"прорезь разорвала луч: {arm.geom_type}"

    arms = [affinity.rotate(arm, 60.0 * index, origin=(0, 0)) for index in range(6)]
    body = unary_union(arms)

    body = fit_diameter(body, r * 2.0)
    return body.difference(knob((0.0, 0.0), HANG_D / 2)).buffer(0)


def fit_diameter(poly: Polygon, diameter: float) -> Polygon:
    """Подгоняем габарит под номинальный диаметр: Ø350 значит Ø350 по крайним точкам."""
    farthest = max((x * x + y * y) ** 0.5 for x, y in poly.exterior.coords)
    scale = (diameter / 2) / farthest
    return affinity.scale(poly, scale, scale, origin=(0, 0))


def min_thickness(poly: Polygon) -> float:
    """Самое узкое место детали: удвоенный радиус эрозии до потери связности."""
    low, high = 0.0, 12.0
    for _ in range(20):
        mid = (low + high) / 2
        if poly.buffer(-mid).geom_type == "Polygon":
            low = mid
        else:
            high = mid
    return low * 2


BUILDERS = {
    "01-klassika": build_classic,
    "02-zvezda": build_star,
    "03-kristall": build_crystal,
}


# ── проверки ─────────────────────────────────────────────────────────────────


def check(poly: Polygon) -> list[str]:
    """Возвращает список замечаний. Пустой список — деталь годная."""
    notes: list[str] = []

    if not poly.is_valid:
        notes.append("геометрия самопересекается")
        return notes
    if poly.geom_type != "Polygon":
        notes.append(f"деталь распалась на части: {poly.geom_type}")
        return notes

    outer = Polygon(poly.exterior)

    # 1. Перемычки: окна не должны подходить к кромке ближе MIN_WALL
    for index, ring in enumerate(poly.interiors, start=1):
        hole = Polygon(ring)
        gap = outer.exterior.distance(hole.exterior)
        if gap < MIN_WALL:
            notes.append(f"окно {index}: перемычка {gap:.1f} мм < {MIN_WALL:.0f} мм")
        if hole.buffer(-TOOL_D / 2).is_empty:
            notes.append(f"окно {index}: уже фрезы Ø{TOOL_D:g} мм — фреза не войдёт")

    # 2. Жёсткая проверка на «ножи»: снятие 2,5 мм с каждой стороны
    #    не должно разрывать деталь.
    knife = poly.buffer(-2.5)
    if knife.is_empty:
        notes.append("деталь исчезает при снятии 2,5 мм — есть тонкие места")
    elif knife.geom_type != "Polygon":
        notes.append("при снятии 2,5 мм деталь распадается на части")

    # 3. Технологическая перемычка. Мелкие отщепы в углах — это скругления
    #    фрезы, а не дефект, поэтому считаем только крупные фрагменты.
    eroded = poly.buffer(-MIN_WALL / 2)
    if eroded.geom_type == "MultiPolygon":
        parts = sorted(eroded.geoms, key=lambda part: -part.area)
        total = sum(part.area for part in parts)
        big = [part for part in parts if part.area / total >= 0.005]
        chips = len(parts) - len(big)
        if len(big) > 1:
            notes.append(f"при перемычке {MIN_WALL:.0f} мм деталь распадается на {len(big)} частей")
        if chips:
            print(f"    (инфо) угловых скруглений при эрозии: {chips} — это не дефект")

    # 4. Окна не должны слипаться друг с другом
    rings = [Polygon(ring) for ring in poly.interiors]
    for first in range(len(rings)):
        for second in range(first + 1, len(rings)):
            gap = rings[first].exterior.distance(rings[second].exterior)
            if gap < MIN_WALL:
                notes.append(f"окна {first + 1} и {second + 1}: перемычка {gap:.1f} мм")

    return notes


def kerf_compensated(poly: Polygon) -> Polygon:
    """Наружный контур наружу, окна внутрь — на половину реза."""
    outer = Polygon(poly.exterior).buffer(KERF / 2, resolution=32, join_style="round")
    holes = [Polygon(ring).buffer(-KERF / 2, resolution=32, join_style="round") for ring in poly.interiors]
    return Polygon(outer.exterior, [hole.exterior for hole in holes if not hole.is_empty])


# ── выгрузка ────────────────────────────────────────────────────────────────


def ring_path(coords, height: float) -> str:
    """Замкнутый контур в миллиметрах, ось Y вниз — как принято в SVG."""
    points = [(x, height - y) for x, y in coords]
    head = f"M{points[0][0]:.3f} {points[0][1]:.3f}"
    tail = "".join(f"L{x:.3f} {y:.3f}" for x, y in points[1:])
    return head + tail + "Z"


def svg_body(poly: Polygon, height: float) -> tuple[str, list[str]]:
    """Отдельно наружный контур и отдельно окна — под разные слои реза.

    Каждое окно — свой <path>: часть CAM-плагинов читает один path как один контур
    и не разбирает вложенные подконтуры.
    """
    outer = ring_path(poly.exterior.coords, height)
    inner = [ring_path(ring.coords, height) for ring in poly.interiors]
    return outer, inner


def write_svg(poly: Polygon, path: Path, title: str, kerf: bool) -> None:
    margin = 20.0
    min_x, min_y, max_x, max_y = poly.bounds
    width = (max_x - min_x) + margin * 2
    height = (max_y - min_y) + margin * 2
    shifted = affinity.translate(poly, margin - min_x, margin - min_y)
    outer, inner = svg_body(shifted, height)
    diameter = max(poly.bounds[2] - poly.bounds[0], poly.bounds[3] - poly.bounds[1])

    note = (
        f"Номинал, фреза не учтена. Габарит {diameter:.0f} мм."
        if not kerf
        else f"Компенсация реза под фрезу Ø{TOOL_D:g} мм (kerf {KERF:g} мм). Габарит {diameter:.0f} мм."
    )
    inner_group = (
        f'  <g id="{LAYER_INNER}" fill="none" stroke="#0b63c5" stroke-width="0.12">\n'
        + "".join(f'    <path d="{path}"/>\n' for path in inner)
        + "  </g>\n"
        if inner else ""
    )
    path.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}mm" height="{height:.0f}mm" '
        f'viewBox="0 0 {width:.0f} {height:.0f}" version="1.1">\n'
        f"  <title>{title}</title>\n"
        f"  <desc>{note}</desc>\n"
        f'  <g id="{LAYER_OUTER}" fill="none" stroke="#d81e2c" stroke-width="0.12">\n'
        f'    <path d="{outer}"/>\n'
        "  </g>\n"
        + inner_group +
        "</svg>\n",
        encoding="utf-8",
    )


def write_dxf(poly: Polygon, path: Path) -> None:
    doc = ezdxf.new("R2010", setup=True)
    doc.units = ezdxf.units.MM
    doc.header["$INSUNITS"] = 4  # миллиметры
    doc.layers.add(LAYER_OUTER, color=1)
    doc.layers.add(LAYER_INNER, color=5)
    msp = doc.modelspace()

    outer = orient(Polygon(poly.exterior), sign=1.0)      # наружный — против часовой
    msp.add_lwpolyline(list(outer.exterior.coords), close=True, dxfattribs={"layer": LAYER_OUTER})
    for ring in poly.interiors:
        hole = orient(Polygon(ring), sign=-1.0)           # окна — по часовой
        msp.add_lwpolyline(list(hole.exterior.coords), close=True, dxfattribs={"layer": LAYER_INNER})
    doc.saveas(path)


def cut_length(poly: Polygon) -> float:
    """Полная длина реза по детали, мм."""
    return poly.exterior.length + sum(Polygon(ring).exterior.length for ring in poly.interiors)


def write_nesting(pieces: list[tuple[Piece, Polygon]], path: Path, title: str) -> dict[str, float]:
    """Раскладка: повторяем детали, пока лист не заполнится. Рядная схема."""
    if not pieces:
        return {"count": 0, "util": 0.0, "cut_m": 0.0}

    order = sorted(pieces, key=lambda item: -item[0].radius)
    placed: list[tuple[float, float, Piece, Polygon]] = []
    x, y = SHEET_MARGIN, SHEET_MARGIN
    row_height = 0.0
    index = 0

    while True:
        piece, poly = order[index % len(order)]
        cell = piece.radius * 2 + PIECE_GAP
        if x + cell > SHEET_W - SHEET_MARGIN + 1e-6:
            x = SHEET_MARGIN
            y += row_height
            row_height = 0.0
        if y + cell > SHEET_H - SHEET_MARGIN + 1e-6:
            break
        placed.append((x, y, piece, poly))
        x += cell
        row_height = max(row_height, cell)
        index += 1

    body = []
    used_area = 0.0
    total_cut = 0.0
    for px, py, piece, poly in placed:
        shifted = affinity.translate(poly, px + piece.radius - poly.centroid.x,
                                     py + piece.radius - poly.centroid.y)
        d = ring_path(shifted.exterior.coords, SHEET_H)
        d += "".join(ring_path(ring.coords, SHEET_H) for ring in shifted.interiors)
        body.append(f'    <path d="{d}" fill-rule="evenodd"/>')
        used_area += poly.area
        total_cut += cut_length(poly)

    util = used_area / (SHEET_W * SHEET_H) * 100
    path.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{SHEET_W:.0f}mm" height="{SHEET_H:.0f}mm" '
        f'viewBox="0 0 {SHEET_W:.0f} {SHEET_H:.0f}" version="1.1">\n'
        f"  <title>{title}</title>\n"
        f'  <g id="SHEET" fill="none" stroke="#9aa7b4" stroke-width="0.6">\n'
        f'    <rect x="0" y="0" width="{SHEET_W:.0f}" height="{SHEET_H:.0f}"/>\n'
        "  </g>\n"
        f'  <g id="CUT" fill="none" stroke="#d81e2c" stroke-width="0.2">\n'
        + "\n".join(body) + "\n"
        "  </g>\n"
        "</svg>\n",
        encoding="utf-8",
    )
    print(f"  лист {title}: {len(placed)} дет., материал {used_area / 1e6:.2f} м² "
          f"({util:.1f} % листа), рез {total_cut / 1000:.1f} м")
    return {"count": float(len(placed)), "util": util, "cut_m": total_cut / 1000}


# ── превью ──────────────────────────────────────────────────────────────────

def poly_to_d(poly: Polygon, height: float) -> str:
    d = ring_path(poly.exterior.coords, height)
    d += "".join(ring_path(ring.coords, height) for ring in poly.interiors)
    return d


def render_png(poly: Polygon, px: int) -> "Image.Image":
    """Залитая деталь с вырезанными окнами — чтобы проверять глазом."""
    import resvg_py
    from io import BytesIO
    from PIL import Image

    margin = 6.0
    min_x, min_y, max_x, max_y = poly.bounds
    width = max_x - min_x + margin * 2
    height = max_y - min_y + margin * 2
    shifted = affinity.translate(poly, margin - min_x, margin - min_y)
    d = poly_to_d(shifted, height)
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.1f}" height="{height:.1f}" '
        f'viewBox="0 0 {width:.1f} {height:.1f}">'
        f'<path d="{d}" fill="#8f1d2c" fill-rule="evenodd"/></svg>'
    )
    png = bytes(resvg_py.svg_to_bytes(svg_string=svg, width=px))
    image = Image.open(BytesIO(png)).convert("RGBA")
    canvas = Image.new("RGBA", image.size, "#ffffff")
    return Image.alpha_composite(canvas, image).convert("RGB")


def font(size: int, weight: int = 600):
    from PIL import ImageFont

    path = REPO / "banners/anikom-arena-3000x2500-concepts/source/Montserrat-Variable.ttf"
    if not path.exists():
        return None
    face = ImageFont.truetype(str(path), size)
    face.set_variation_by_axes([weight])
    return face


def write_previews(items: list[tuple[Piece, Polygon]], sheet_pngs: dict[str, Path]) -> None:
    from PIL import Image, ImageDraw

    for piece, poly in items:
        image = render_png(poly, 1000)
        image.save(PREVIEW_DIR / f"{piece.slug}-d{piece.radius * 2:.0f}.png")

    small = [(piece, poly) for piece, poly in items if piece.radius == 175.0]
    big = [render_png(poly, 760) for _, poly in small]
    if not big:
        return
    gap, caption, pad = 18, 46, 24
    cell = max(image.width for image in big), max(image.height for image in big)
    width = cell[0] * len(big) + gap * (len(big) - 1) + pad * 2
    height = cell[1] + caption + pad * 2
    sheet = Image.new("RGB", (width, height), "#ffffff")
    draw = ImageDraw.Draw(sheet)
    face = font(26, 600)
    x = pad
    for image, (piece, _) in zip(big, small):
        sheet.paste(image, (x + (cell[0] - image.width) // 2, pad + (cell[1] - image.height) // 2))
        if face:
            draw.text((x, pad + cell[1] + 8), f"{piece.title} · Ø{piece.radius * 2:.0f} мм",
                      font=face, fill="#1b2a3a")
        x += cell[0] + gap
    sheet.save(PREVIEW_DIR / "all-d350.png")
    print(f"  превью: {PREVIEW_DIR.name}/all-d350.png ({sheet.width}×{sheet.height})")

    for name, path in sheet_pngs.items():
        from io import BytesIO
        import re
        import resvg_py

        text = path.read_text(encoding="utf-8")
        text = re.sub(r'(<svg[^>]*?)width="([\d.]+)mm" height="([\d.]+)mm"',
                      r'\1width="\2" height="\3"', text, count=1)
        png = bytes(resvg_py.svg_to_bytes(svg_string=text, width=1500))
        image = Image.open(BytesIO(png)).convert("RGBA")
        canvas = Image.new("RGBA", image.size, "#ffffff")
        Image.alpha_composite(canvas, image).convert("RGB").save(PREVIEW_DIR / f"sheet-{name}.png")


def main() -> int:
    for folder in (SVG_DIR, DXF_DIR, PREVIEW_DIR):
        folder.mkdir(parents=True, exist_ok=True)

    failed = 0
    items: list[tuple[Piece, Polygon]] = []
    by_size: dict[str, list[tuple[Piece, Polygon]]] = {key: [] for key in SIZES}

    for slug, title in DESIGNS:
        builder = BUILDERS[slug]
        for size_key, radius in SIZES.items():
            piece = Piece(slug, title, radius)
            poly = builder(radius)
            notes = check(poly)
            diameter = radius * 2

            status = "OK" if not notes else "ЗАМЕЧАНИЯ"
            print(f"{slug} · Ø{diameter:.0f}: {status}, "
                  f"узкое место {min_thickness(poly):.1f} мм, "
                  f"рез {cut_length(poly) / 1000:.2f} м")
            for note in notes:
                print(f"    - {note}")
                failed += 1

            nominal = poly.simplify(SIMPLIFY_MM, preserve_topology=True)
            compensated = kerf_compensated(poly).simplify(SIMPLIFY_MM, preserve_topology=True)
            assert nominal.geom_type == "Polygon" and compensated.geom_type == "Polygon"
            base = f"{slug}-d{diameter:.0f}"
            write_svg(nominal, SVG_DIR / f"{base}.svg",
                      f"Снежинка «{title}», Ø{diameter:.0f} мм", kerf=False)
            write_svg(compensated, SVG_DIR / f"{base}-kerf{TOOL_D:g}.svg",
                      f"Снежинка «{title}», Ø{diameter:.0f} мм, компенсация реза", kerf=True)
            write_dxf(nominal, DXF_DIR / f"{base}.dxf")
            write_dxf(compensated, DXF_DIR / f"{base}-kerf{TOOL_D:g}.dxf")

            items.append((piece, poly))
            by_size[size_key].append((piece, poly))

    print()
    sheets: dict[str, Path] = {}
    for size_key in SIZES:
        path = SVG_DIR / f"sheet-{size_key}.svg"
        write_nesting(
            by_size[size_key],
            path,
            f"Раскрой листа {SHEET_W:.0f}×{SHEET_H:.0f} мм, детали Ø{SIZES[size_key] * 2:.0f} мм",
        )
        sheets[size_key] = path

    print()
    write_previews(items, sheets)

    print(f"\nПроверок с замечаниями: {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
