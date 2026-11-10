#!/usr/bin/env python3
"""Build print-ready ANIKOM ARENA PVC navigation signs with cut contours."""

from __future__ import annotations

import copy
import io
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont
from PIL import Image
import resvg_py

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "source"
FONT_PATH = SOURCE / "Montserrat-Variable.ttf"
LOGO_PATH = SOURCE / "anikom-arena-logo-vector.svg"
MASTER = ROOT / "anikom-arena-navigation-master-sheet.svg"
PREVIEW = ROOT / "master-sheet-preview.png"
INDIVIDUAL = ROOT / "individual"

SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)

# Final cut size is 600 × 200 mm. The SVG includes 3 mm bleed on every side.
BLEED = 3
CUT_WIDTH = 600
CUT_HEIGHT = 200
CANVAS_WIDTH = CUT_WIDTH + BLEED * 2
CANVAS_HEIGHT = CUT_HEIGHT + BLEED * 2
CORNER_RADIUS = 12
CELL_GAP = 20
SHEET_MARGIN = 20
SHEET_COLUMNS = 4

NAVY = "#081A2B"
NAVY_LIGHT = "#102A44"
PLUM = "#2C222E"
CORAL = "#D94A43"
WHITE = "#FFFFFF"
CUT_MAGENTA = "#FF00FF"


@dataclass(frozen=True)
class Sign:
    slug: str
    lines: tuple[str, ...]
    icon: str


SIGNS = [
    Sign("razdevalka-1", ("РАЗДЕВАЛКА 1",), "changing"),
    Sign("razdevalka-2", ("РАЗДЕВАЛКА 2",), "changing"),
    Sign("wc", ("WC",), "wc"),
    Sign("cafe", ("КАФЕ",), "cafe"),
    Sign("sudeyskaya", ("СУДЕЙСКАЯ",), "referee"),
    Sign("vhod", ("ВХОД",), "entrance"),
    Sign("vyhod", ("ВЫХОД",), "exit"),
    Sign("administrator", ("АДМИНИСТРАТОР",), "admin"),
    Sign("pole", ("ПОЛЕ",), "field"),
    Sign("tribuny", ("ТРИБУНЫ",), "stands"),
    Sign("medpunkt", ("МЕДПУНКТ",), "medical"),
    Sign("dushevye", ("ДУШЕВЫЕ",), "shower"),
    Sign("trenerskaya", ("ТРЕНЕРСКАЯ",), "coach"),
    Sign("inventarnaya", ("ИНВЕНТАРНАЯ",), "inventory"),
    Sign("technical", ("ТЕХНИЧЕСКОЕ", "ПОМЕЩЕНИЕ"), "technical"),
    Sign("emergency-exit", ("ЭВАКУАЦИОННЫЙ", "ВЫХОД"), "evacuation"),
    Sign("parking", ("ПАРКОВКА",), "parking"),
    Sign("kassa", ("КАССА",), "ticket"),
    Sign("reception", ("РЕСЕПШЕН",), "reception"),
    Sign("waiting", ("ЗОНА ОЖИДАНИЯ",), "waiting"),
]


ICON_CONTENT = {
    "changing": """
      <path d="M50 17 C50 9 62 10 62 19 C62 26 53 27 50 33"/>
      <path d="M50 33 L18 60 C14 64 17 71 23 71 H77 C83 71 86 64 82 60 Z"/>
      <path d="M31 49 L18 60 M69 49 L82 60"/>
    """,
    "wc": """
      <path d="M29 17 A9 9 0 1 1 28.9 17 Z M71 17 A9 9 0 1 1 70.9 17 Z" fill="#FFFFFF" stroke="none"/>
      <path d="M17 39 C17 32 23 28 29 28 C35 28 41 32 41 39 V58 H35 V84 H23 V58 H17 Z" fill="#FFFFFF" stroke="none"/>
      <path d="M59 39 C59 32 65 28 71 28 C77 28 83 32 83 39 L91 65 H80 V84 H62 V65 H51 Z" fill="#FFFFFF" stroke="none"/>
    """,
    "cafe": """
      <path d="M20 35 H70 V61 C70 74 59 82 45 82 C31 82 20 74 20 61 Z"/>
      <path d="M70 42 H78 C88 42 90 57 80 62 H70"/>
      <path d="M28 21 C24 15 31 11 28 6 M46 21 C42 15 49 11 46 6 M63 21 C59 15 66 11 63 6"/>
      <path d="M15 88 H83"/>
    """,
    "referee": """
      <path d="M26 45 C26 31 37 22 50 22 H69 L83 35 L70 50 H54 C47 61 26 57 26 45 Z"/>
      <path d="M64 22 L74 10 M32 55 L20 82"/>
      <path d="M45 43 A6 6 0 1 1 44.9 43 Z" fill="#FFFFFF" stroke="none"/>
    """,
    "entrance": """
      <path d="M17 14 H60 V86 H17 Z M29 14 V86"/>
      <path d="M42 50 H88 M72 34 L88 50 L72 66"/>
    """,
    "exit": """
      <path d="M40 14 H83 V86 H40 Z M71 14 V86"/>
      <path d="M58 50 H12 M28 34 L12 50 L28 66"/>
    """,
    "admin": """
      <path d="M50 12 A38 38 0 1 1 49.9 12 Z"/>
      <path d="M50 42 V72"/>
      <path d="M50 28 L50.1 28" stroke-width="10"/>
    """,
    "field": """
      <path d="M50 10 A40 40 0 1 1 49.9 10 Z"/>
      <path d="M50 32 L65 43 L59 61 H41 L35 43 Z"/>
      <path d="M50 32 V18 M65 43 L80 36 M59 61 L68 76 M41 61 L32 76 M35 43 L20 36"/>
    """,
    "stands": """
      <path d="M14 78 H86 M20 78 V61 H39 V44 H58 V27 H82"/>
      <path d="M20 61 H82 M39 44 H82 M58 27 V78"/>
    """,
    "medical": """
      <path d="M39 12 H61 V39 H88 V61 H61 V88 H39 V61 H12 V39 H39 Z" fill="#FFFFFF" stroke="none"/>
    """,
    "shower": """
      <path d="M18 29 C18 14 31 8 43 8 C57 8 66 17 66 30"/>
      <path d="M53 31 H79 L68 48 H43 Z"/>
      <path d="M48 58 L43 70 M62 58 L57 73 M76 58 L71 70"/>
      <path d="M18 29 V88"/>
    """,
    "coach": """
      <path d="M13 18 H87 V77 H13 Z"/>
      <path d="M50 18 V77 M13 47 H87 M50 39 A8 8 0 1 1 49.9 39 Z"/>
      <path d="M28 86 H72 M50 77 V86"/>
    """,
    "inventory": """
      <path d="M14 31 L50 13 L86 31 L50 50 Z"/>
      <path d="M14 31 V70 L50 88 L86 70 V31 M50 50 V88"/>
      <path d="M32 22 L68 41"/>
    """,
    "technical": """
      <path d="M64 16 C52 13 42 20 40 31 C39 36 40 41 43 45 L16 72 C10 78 20 88 26 82 L53 55 C58 58 64 59 69 57 C80 54 86 44 83 32 L70 43 L58 40 L55 28 Z"/>
    """,
    "evacuation": """
      <path d="M55 12 H86 V88 H55"/>
      <path d="M12 50 H67 M51 34 L67 50 L51 66"/>
      <path d="M34 19 A7 7 0 1 1 33.9 19 Z M34 29 L27 45 L39 55 L35 76 M28 45 L15 58 M39 55 L52 69"/>
    """,
    "parking": """
      <path d="M27 88 V12 H55 C75 12 86 23 86 40 C86 58 74 68 55 68 H44 V88 Z M44 29 V51 H55 C64 51 69 47 69 40 C69 33 64 29 55 29 Z" fill="#FFFFFF" stroke="none"/>
    """,
    "ticket": """
      <path d="M12 29 H88 V44 C78 44 78 56 88 56 V71 H12 V56 C22 56 22 44 12 44 Z"/>
      <path d="M52 29 V71 M63 41 H78 M63 52 H75 M63 62 H72"/>
    """,
    "reception": """
      <path d="M50 14 A10 10 0 1 1 49.9 14 Z" fill="#FFFFFF" stroke="none"/>
      <path d="M30 48 C30 34 39 28 50 28 C61 28 70 34 70 48"/>
      <path d="M12 51 H88 V82 H12 Z M24 82 V91 M76 82 V91"/>
    """,
    "waiting": """
      <path d="M50 11 A39 39 0 1 1 49.9 11 Z"/>
      <path d="M50 26 V50 L67 61"/>
      <path d="M50 11 V18 M50 82 V89 M11 50 H18 M82 50 H89"/>
    """,
}


def svg_tag(name: str) -> str:
    return f"{{{SVG_NS}}}{name}"


def rounded_rect_path(x: float, y: float, width: float, height: float, radius: float) -> str:
    right = x + width
    bottom = y + height
    return (
        f"M{x + radius:g} {y:g} H{right - radius:g} "
        f"A{radius:g} {radius:g} 0 0 1 {right:g} {y + radius:g} "
        f"V{bottom - radius:g} A{radius:g} {radius:g} 0 0 1 {right - radius:g} {bottom:g} "
        f"H{x + radius:g} A{radius:g} {radius:g} 0 0 1 {x:g} {bottom - radius:g} "
        f"V{y + radius:g} A{radius:g} {radius:g} 0 0 1 {x + radius:g} {y:g} Z"
    )


class FontOutliner:
    def __init__(self, path: Path) -> None:
        self.font = TTFont(path)
        self.cmap = self.font.getBestCmap()
        self.cap_height = int(self.font["OS/2"].sCapHeight)
        self.glyph_sets: dict[int, object] = {}
        self.path_cache: dict[tuple[int, str], str] = {}

    def glyph_set(self, weight: int):
        if weight not in self.glyph_sets:
            self.glyph_sets[weight] = self.font.getGlyphSet(location={"wght": weight})
        return self.glyph_sets[weight]

    def metrics(self, text: str, weight: int, tracking: float) -> tuple[float, list[tuple[str, float]]]:
        glyph_set = self.glyph_set(weight)
        placements: list[tuple[str, float]] = []
        cursor = 0.0
        visible = [character for character in text]
        for index, character in enumerate(visible):
            glyph_name = self.cmap[ord(character)]
            placements.append((character, cursor))
            cursor += glyph_set[glyph_name].width
            if index != len(visible) - 1:
                cursor += tracking
        return cursor, placements

    def path(self, character: str, weight: int) -> str:
        key = (weight, character)
        if key in self.path_cache:
            return self.path_cache[key]
        glyph_set = self.glyph_set(weight)
        glyph_name = self.cmap[ord(character)]
        pen = SVGPathPen(glyph_set)
        glyph_set[glyph_name].draw(pen)
        path = pen.getCommands()
        self.path_cache[key] = path
        return path

    def add_text(
        self,
        parent: ET.Element,
        text: str,
        *,
        x: float,
        baseline: float,
        cap_height: float,
        max_width: float,
        weight: int,
        tracking: float,
        fill: str,
        element_id: str,
    ) -> float:
        total_units, placements = self.metrics(text, weight, tracking)
        scale = min(cap_height / self.cap_height, max_width / total_units)
        group = ET.SubElement(
            parent,
            svg_tag("g"),
            {"id": element_id, "fill": fill, "aria-label": text},
        )
        for character, offset in placements:
            if character == " ":
                continue
            ET.SubElement(
                group,
                svg_tag("path"),
                {
                    "d": self.path(character, weight),
                    "transform": (
                        f"matrix({scale:.8f} 0 0 {-scale:.8f} "
                        f"{x + offset * scale:.4f} {baseline:.4f})"
                    ),
                },
            )
        return scale


class SignBuilder:
    def __init__(self) -> None:
        self.outliner = FontOutliner(FONT_PATH)
        self.logo_groups = self._load_logo_groups()
        self.icon_elements = self._load_icon_elements()

    def _load_logo_groups(self) -> list[ET.Element]:
        root = ET.parse(LOGO_PATH).getroot()
        groups = [copy.deepcopy(element) for element in root if element.tag == svg_tag("g")]
        # Repeated logos on the master sheet must not introduce duplicate IDs.
        for group in groups:
            for element in group.iter():
                element.attrib.pop("id", None)
                element.attrib.pop("data-source-component", None)
        return groups

    def _load_icon_elements(self) -> dict[str, list[ET.Element]]:
        icons: dict[str, list[ET.Element]] = {}
        for icon_name, content in ICON_CONTENT.items():
            symbol_xml = f'<g xmlns="{SVG_NS}">{content}</g>'
            parsed = ET.fromstring(symbol_xml)
            icons[icon_name] = [copy.deepcopy(element) for element in parsed]
        return icons

    def add_icon(self, parent: ET.Element, sign: Sign) -> None:
        group = ET.SubElement(
            parent,
            svg_tag("g"),
            {
                "id": f"{sign.slug}__icon-outlines",
                "transform": "translate(20 53) scale(0.88)",
                "fill": "none",
                "stroke": WHITE,
                "stroke-width": "7",
                "stroke-linecap": "round",
                "stroke-linejoin": "round",
            },
        )
        for element in self.icon_elements[sign.icon]:
            group.append(copy.deepcopy(element))

    def add_logo(self, parent: ET.Element, sign: Sign) -> None:
        # Map the corrected logo viewBox 25 174 836 823 into an 84 mm square.
        scale = min(84 / 836, 84 / 823)
        rendered_height = 823 * scale
        y_offset = 55 + (84 - rendered_height) / 2
        group = ET.SubElement(
            parent,
            svg_tag("g"),
            {
                "id": f"{sign.slug}__logo-watermark-outlines",
                "opacity": "0.16",
                "transform": (
                    f"translate(501 {y_offset:.6f}) scale({scale:.9f}) "
                    "translate(-25 -174)"
                ),
            },
        )
        for logo_group in self.logo_groups:
            group.append(copy.deepcopy(logo_group))

    def add_print_art(self, parent: ET.Element, sign: Sign, *, group_id: str) -> None:
        group = ET.SubElement(
            parent,
            svg_tag("g"),
            {"id": group_id, "data-final-size": "600x200mm"},
        )
        # Full bleed print background.
        ET.SubElement(
            group,
            svg_tag("path"),
            {"d": f"M0 0 H{CANVAS_WIDTH} V{CANVAS_HEIGHT} H0 Z", "fill": NAVY},
        )
        ET.SubElement(
            group,
            svg_tag("path"),
            {"d": f"M0 0 H137 L109 {CANVAS_HEIGHT / 2:g} L137 {CANVAS_HEIGHT} H0 Z", "fill": PLUM},
        )
        ET.SubElement(
            group,
            svg_tag("path"),
            {
                "d": f"M112 0 H130 L101 {CANVAS_HEIGHT / 2:g} L130 {CANVAS_HEIGHT} H112 L82 {CANVAS_HEIGHT / 2:g} Z",
                "fill": CORAL,
                "opacity": "0.26",
            },
        )
        ET.SubElement(
            group,
            svg_tag("path"),
            {"d": f"M480 0 H{CANVAS_WIDTH} V{CANVAS_HEIGHT} H450 L476 {CANVAS_HEIGHT / 2:g} Z", "fill": NAVY_LIGHT, "opacity": "0.44"},
        )
        ET.SubElement(
            group,
            svg_tag("path"),
            {
                "d": rounded_rect_path(10, 10, CANVAS_WIDTH - 20, CANVAS_HEIGHT - 20, 12),
                "fill": "none",
                "stroke": CORAL,
                "stroke-width": "3",
            },
        )

        self.add_icon(group, sign)
        self.add_logo(group, sign)

        self.outliner.add_text(
            group,
            "АНИКОМ АРЕНА",
            x=146,
            baseline=55,
            cap_height=13,
            max_width=230,
            weight=700,
            tracking=52,
            fill=CORAL,
            element_id=f"{sign.slug}__brand-caption-outlines",
        )

        if len(sign.lines) == 1:
            requested_cap = 67 if sign.slug == "wc" else 56
            self.outliner.add_text(
                group,
                sign.lines[0],
                x=146,
                baseline=137 if sign.slug != "wc" else 148,
                cap_height=requested_cap,
                max_width=420,
                weight=760,
                tracking=14,
                fill=WHITE,
                element_id=f"{sign.slug}__title-outlines",
            )
        else:
            for index, line in enumerate(sign.lines):
                self.outliner.add_text(
                    group,
                    line,
                    x=146,
                    baseline=111 + index * 48,
                    cap_height=34,
                    max_width=420,
                    weight=760,
                    tracking=8,
                    fill=WHITE,
                    element_id=f"{sign.slug}__title-line-{index + 1}-outlines",
                )

    def add_cut_contour(self, parent: ET.Element, *, contour_id: str) -> None:
        ET.SubElement(
            parent,
            svg_tag("path"),
            {
                "id": contour_id,
                "d": rounded_rect_path(BLEED, BLEED, CUT_WIDTH, CUT_HEIGHT, CORNER_RADIUS),
                "fill": "none",
                "stroke": CUT_MAGENTA,
                "stroke-width": "0.5",
                "vector-effect": "non-scaling-stroke",
                "data-operation": "CUT",
            },
        )

    def new_root(self, width: float, height: float, title: str) -> ET.Element:
        root = ET.Element(
            svg_tag("svg"),
            {
                "version": "1.1",
                "width": f"{width:g}mm",
                "height": f"{height:g}mm",
                "viewBox": f"0 0 {width:g} {height:g}",
                "shape-rendering": "geometricPrecision",
            },
        )
        title_element = ET.SubElement(root, svg_tag("title"))
        title_element.text = title
        desc = ET.SubElement(root, svg_tag("desc"))
        desc.text = "Print artwork with outlined typography and separate magenta cut contours."
        return root

    def serialize(self, root: ET.Element, path: Path) -> None:
        ET.indent(root, space="  ")
        content = ET.tostring(root, encoding="unicode", short_empty_elements=True)
        path.write_text('<?xml version="1.0" encoding="UTF-8"?>\n' + content + "\n", encoding="utf-8")

    def build_individual(self, sign: Sign) -> None:
        root = self.new_root(CANVAS_WIDTH, CANVAS_HEIGHT, f"ANIKOM ARENA — {sign.lines[0]}")
        print_layer = ET.SubElement(root, svg_tag("g"), {"id": "PRINT"})
        self.add_print_art(print_layer, sign, group_id=f"SIGN__{sign.slug}")
        cut_layer = ET.SubElement(
            root,
            svg_tag("g"),
            {"id": "CUT_CONTOUR", "data-layer": "CUT_CONTOUR"},
        )
        self.add_cut_contour(cut_layer, contour_id=f"CUT__{sign.slug}")
        self.serialize(root, INDIVIDUAL / f"{sign.slug}.svg")

    def build_master(self) -> None:
        rows = (len(SIGNS) + SHEET_COLUMNS - 1) // SHEET_COLUMNS
        sheet_width = SHEET_MARGIN * 2 + SHEET_COLUMNS * CANVAS_WIDTH + (SHEET_COLUMNS - 1) * CELL_GAP
        sheet_height = SHEET_MARGIN * 2 + rows * CANVAS_HEIGHT + (rows - 1) * CELL_GAP
        root = self.new_root(sheet_width, sheet_height, "ANIKOM ARENA — PVC navigation master sheet")
        print_layer = ET.SubElement(root, svg_tag("g"), {"id": "PRINT"})
        cut_layer = ET.SubElement(
            root,
            svg_tag("g"),
            {"id": "CUT_CONTOUR", "data-layer": "CUT_CONTOUR"},
        )

        for index, sign in enumerate(SIGNS):
            column = index % SHEET_COLUMNS
            row = index // SHEET_COLUMNS
            x = SHEET_MARGIN + column * (CANVAS_WIDTH + CELL_GAP)
            y = SHEET_MARGIN + row * (CANVAS_HEIGHT + CELL_GAP)
            wrapper = ET.SubElement(
                print_layer,
                svg_tag("g"),
                {"id": f"PLACED__{sign.slug}", "transform": f"translate({x:g} {y:g})"},
            )
            self.add_print_art(wrapper, sign, group_id=f"SIGN__{sign.slug}")
            contour_wrapper = ET.SubElement(
                cut_layer,
                svg_tag("g"),
                {"transform": f"translate({x:g} {y:g})"},
            )
            self.add_cut_contour(contour_wrapper, contour_id=f"CUT__{sign.slug}")
        self.serialize(root, MASTER)


def validate() -> None:
    master_root = ET.parse(MASTER).getroot()
    if master_root.findall(f".//{svg_tag('text')}"):
        raise RuntimeError("Live text found in master SVG")
    if master_root.findall(f".//{svg_tag('use')}"):
        raise RuntimeError("Unexpanded symbol references found in master SVG")
    element_ids = [
        element.get("id")
        for element in master_root.iter()
        if element.get("id") is not None
    ]
    if len(element_ids) != len(set(element_ids)):
        raise RuntimeError("Duplicate element IDs found in master SVG")
    cut_paths = [
        element
        for element in master_root.findall(f".//{svg_tag('path')}")
        if element.get("data-operation") == "CUT"
    ]
    if len(cut_paths) != len(SIGNS):
        raise RuntimeError(f"Expected {len(SIGNS)} cut contours, found {len(cut_paths)}")
    for sign in SIGNS:
        path = INDIVIDUAL / f"{sign.slug}.svg"
        root = ET.parse(path).getroot()
        if root.findall(f".//{svg_tag('text')}"):
            raise RuntimeError(f"Live text found in {path}")
        if root.findall(f".//{svg_tag('use')}"):
            raise RuntimeError(f"Unexpanded symbol references found in {path}")
        cuts = [
            element
            for element in root.findall(f".//{svg_tag('path')}")
            if element.get("data-operation") == "CUT"
        ]
        if len(cuts) != 1:
            raise RuntimeError(f"Expected one cut contour in {path}")


def render_preview() -> None:
    root = ET.parse(MASTER).getroot()
    width = float(root.get("viewBox").split()[2])
    height = float(root.get("viewBox").split()[3])
    preview_width = 2400
    preview_height = round(preview_width * height / width)
    png = resvg_py.svg_to_bytes(
        svg_path=str(MASTER),
        width=preview_width,
        height=preview_height,
        dpi=96,
    )
    rendered = Image.open(io.BytesIO(png)).convert("RGBA")
    background = Image.new("RGBA", rendered.size, "#E9E6DF")
    background.alpha_composite(rendered)
    background.convert("RGB").save(PREVIEW, quality=95)


def main() -> None:
    INDIVIDUAL.mkdir(parents=True, exist_ok=True)
    builder = SignBuilder()
    for sign in SIGNS:
        builder.build_individual(sign)
    builder.build_master()
    validate()
    render_preview()
    print(f"Built {len(SIGNS)} signs")
    print(f"Final cut size per sign: {CUT_WIDTH} × {CUT_HEIGHT} mm")
    print(f"Master sheet: {MASTER}")
    print("Live text: none")
    print(f"Cut contours: {len(SIGNS)}")


if __name__ == "__main__":
    main()
