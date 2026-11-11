#!/usr/bin/env python3
"""Build four print-ready ANIKOM ARENA banner concepts at 3000 × 2500 mm."""

from __future__ import annotations

import copy
import sys
import io
import xml.etree.ElementTree as ET
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont
from PIL import Image
import resvg_py

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "source"
FONT_PATH = SOURCE / "Montserrat-Variable.ttf"
LOGO_PATH = SOURCE / "anikom-arena-logo-vector.svg"
PREVIEW_DIR = ROOT / "previews"

SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)

WIDTH = 3000
HEIGHT = 2500
SAFE = 120

NAVY = "#081A2B"
NAVY_LIGHT = "#102A44"
NAVY_MID = "#0D2238"
PLUM = "#2C222E"
PLUM_DARK = "#1C1E2C"
CORAL = "#D94A43"
WHITE = "#FFFFFF"
MUTED = "#AAB6C3"

# Область, которую занимает плашка с названием в концепции 04 (x0, y0, x1, y1).
PLAQUE_RECT = (750, 1030, 1500, 440)
PLAQUE_ZONE = (
    PLAQUE_RECT[0] - 60,
    PLAQUE_RECT[1] - 60,
    PLAQUE_RECT[0] + PLAQUE_RECT[2] + 60,
    PLAQUE_RECT[1] + PLAQUE_RECT[3] + 60,
)

CONCEPTS = [
    ("01-arena-core", "Arena Core"),
    ("02-match-day", "Match Day"),
    ("03-arena-energy", "Arena Energy"),
    ("04-partner-photozone", "Partner Photozone"),
]


def tag(name: str) -> str:
    return f"{{{SVG_NS}}}{name}"


def rect_path(x: float, y: float, width: float, height: float) -> str:
    return f"M{x:g} {y:g} H{x + width:g} V{y + height:g} H{x:g} Z"


def rounded_rect_path(x: float, y: float, width: float, height: float, radius: float) -> str:
    right, bottom = x + width, y + height
    return (
        f"M{x + radius:g} {y:g} H{right - radius:g} A{radius:g} {radius:g} 0 0 1 {right:g} {y + radius:g} "
        f"V{bottom - radius:g} A{radius:g} {radius:g} 0 0 1 {right - radius:g} {bottom:g} "
        f"H{x + radius:g} A{radius:g} {radius:g} 0 0 1 {x:g} {bottom - radius:g} "
        f"V{y + radius:g} A{radius:g} {radius:g} 0 0 1 {x + radius:g} {y:g} Z"
    )


def circle_path(cx: float, cy: float, radius: float) -> str:
    return (
        f"M{cx - radius:g} {cy:g} A{radius:g} {radius:g} 0 1 0 {cx + radius:g} {cy:g} "
        f"A{radius:g} {radius:g} 0 1 0 {cx - radius:g} {cy:g} Z"
    )


class FontOutliner:
    def __init__(self, path: Path) -> None:
        self.font = TTFont(path)
        self.cmap = self.font.getBestCmap()
        self.cap_height = int(self.font["OS/2"].sCapHeight)
        self.glyph_sets: dict[int, object] = {}
        self.path_cache: dict[tuple[int, str], str] = {}
        self.boxes: list[tuple[str, float, float, float, float]] = []

    def glyph_set(self, weight: int):
        if weight not in self.glyph_sets:
            self.glyph_sets[weight] = self.font.getGlyphSet(location={"wght": weight})
        return self.glyph_sets[weight]

    def measure(self, text: str, weight: int, tracking: float) -> tuple[float, list[tuple[str, float]]]:
        glyph_set = self.glyph_set(weight)
        placements: list[tuple[str, float]] = []
        cursor = 0.0
        for index, character in enumerate(text):
            glyph_name = self.cmap[ord(character)]
            placements.append((character, cursor))
            cursor += glyph_set[glyph_name].width
            if index != len(text) - 1:
                cursor += tracking
        return cursor, placements

    def glyph_path(self, character: str, weight: int) -> str:
        key = (weight, character)
        if key in self.path_cache:
            return self.path_cache[key]
        glyph_set = self.glyph_set(weight)
        glyph_name = self.cmap[ord(character)]
        pen = SVGPathPen(glyph_set)
        glyph_set[glyph_name].draw(pen)
        value = pen.getCommands()
        self.path_cache[key] = value
        return value

    def add_text(
        self,
        parent: ET.Element,
        text: str,
        *,
        x: float,
        baseline: float,
        cap_height: float,
        max_width: float,
        weight: int = 760,
        tracking: float = 15,
        fill: str = WHITE,
        opacity: float = 1.0,
        align: str = "left",
        element_id: str | None = None,
        rotate: float = 0,
    ) -> ET.Element:
        units, placements = self.measure(text, weight, tracking)
        scale = min(cap_height / self.cap_height, max_width / units)
        if max_width / units < cap_height / self.cap_height:
            print(
                f"  WARNING: «{text[:36]}» сжато по ширине до {max_width / units * self.cap_height:.0f} mm "
                f"вместо {cap_height:.0f} mm",
                file=sys.stderr,
            )
        text_width = units * scale
        start_x = x
        if align == "center":
            start_x = x - text_width / 2
        elif align == "right":
            start_x = x - text_width
        self.boxes.append((text, start_x, baseline - cap_height, start_x + text_width, baseline + cap_height * 0.26))
        attributes = {
            "fill": fill,
            "opacity": f"{opacity:.4f}",
            "aria-label": text,
        }
        if element_id:
            attributes["id"] = element_id
        if rotate:
            attributes["transform"] = f"rotate({rotate:g} {x:g} {baseline:g})"
        group = ET.SubElement(parent, tag("g"), attributes)
        for character, offset in placements:
            if character == " ":
                continue
            ET.SubElement(
                group,
                tag("path"),
                {
                    "d": self.glyph_path(character, weight),
                    "transform": (
                        f"matrix({scale:.9f} 0 0 {-scale:.9f} "
                        f"{start_x + offset * scale:.4f} {baseline:.4f})"
                    ),
                },
            )
        return group


class ConceptBuilder:
    def __init__(self) -> None:
        self.outliner = FontOutliner(FONT_PATH)
        logo_root = ET.parse(LOGO_PATH).getroot()
        self.logo_groups = [
            copy.deepcopy(element)
            for element in logo_root
            if element.tag == tag("g")
        ]
        for group in self.logo_groups:
            for element in group.iter():
                element.attrib.pop("id", None)
                element.attrib.pop("data-source-component", None)

    def root(self, concept_id: str, title: str) -> tuple[ET.Element, ET.Element]:
        root = ET.Element(
            tag("svg"),
            {
                "version": "1.1",
                "width": f"{WIDTH}mm",
                "height": f"{HEIGHT}mm",
                "viewBox": f"0 0 {WIDTH} {HEIGHT}",
                "shape-rendering": "geometricPrecision",
            },
        )
        title_node = ET.SubElement(root, tag("title"))
        title_node.text = f"ANIKOM ARENA — {title}"
        desc = ET.SubElement(root, tag("desc"))
        desc.text = "Print-ready vector banner artwork, 3000 × 2500 mm, outlined typography."
        art = ET.SubElement(root, tag("g"), {"id": f"ARTWORK__{concept_id}"})
        return root, art

    def add_logo(
        self,
        parent: ET.Element,
        *,
        x: float,
        y: float,
        width: float,
        height: float,
        opacity: float = 1.0,
        element_id: str,
    ) -> ET.Element:
        scale = min(width / 836, height / 823)
        rendered_width, rendered_height = 836 * scale, 823 * scale
        offset_x = x + (width - rendered_width) / 2
        offset_y = y + (height - rendered_height) / 2
        wrapper = ET.SubElement(
            parent,
            tag("g"),
            {
                "id": element_id,
                "opacity": f"{opacity:.4f}",
                "transform": (
                    f"translate({offset_x:.6f} {offset_y:.6f}) scale({scale:.10f}) "
                    "translate(-25 -174)"
                ),
            },
        )
        for logo_group in self.logo_groups:
            wrapper.append(copy.deepcopy(logo_group))
        return wrapper

    def base(self, art: ET.Element, background: str = NAVY) -> None:
        ET.SubElement(
            art,
            tag("path"),
            {"id": "BACKGROUND", "d": rect_path(0, 0, WIDTH, HEIGHT), "fill": background},
        )

    def border(self, art: ET.Element, inset: float = 42, width: float = 18) -> None:
        ET.SubElement(
            art,
            tag("path"),
            {
                "d": rounded_rect_path(inset, inset, WIDTH - 2 * inset, HEIGHT - 2 * inset, 10),
                "fill": "none",
                "stroke": CORAL,
                "stroke-width": f"{width:g}",
            },
        )

    def concept_arena_core(self) -> ET.Element:
        root, art = self.root("01", "Arena Core")
        self.base(art)
        ET.SubElement(art, tag("path"), {"d": "M0 0 H650 L870 2500 H0 Z", "fill": PLUM})
        ET.SubElement(art, tag("path"), {"d": "M3000 0 H2480 L2250 2500 H3000 Z", "fill": PLUM_DARK})
        ET.SubElement(art, tag("path"), {"d": "M300 0 H430 L560 2500 H430 Z", "fill": CORAL, "opacity": "0.22"})
        ET.SubElement(art, tag("path"), {"d": circle_path(1500, 1210, 770), "fill": "none", "stroke": CORAL, "stroke-width": "20"})
        self.add_logo(art, x=760, y=480, width=1480, height=1455, element_id="MAIN_LOGO")
        self.outliner.add_text(
            art,
            "ПОЛЕ  •  СОБЫТИЯ  •  КОНТЕНТ",
            x=1500,
            baseline=2240,
            cap_height=90,
            max_width=2280,
            weight=670,
            tracking=24,
            align="center",
            fill=MUTED,
            element_id="TAGLINE_OUTLINES",
        )
        self.border(art)
        return root

    def add_pitch(self, art: ET.Element, *, x: float, y: float, width: float, height: float, opacity: float) -> None:
        pitch = ET.SubElement(
            art,
            tag("g"),
            {
                "id": "PITCH_LINEWORK",
                "fill": "none",
                "stroke": CORAL,
                "stroke-width": "10",
                "opacity": f"{opacity:.4f}",
            },
        )
        ET.SubElement(pitch, tag("path"), {"d": rounded_rect_path(x, y, width, height, 22)})
        ET.SubElement(pitch, tag("path"), {"d": f"M{x + width / 2:g} {y:g} V{y + height:g}"})
        ET.SubElement(pitch, tag("path"), {"d": circle_path(x + width / 2, y + height / 2, min(width, height) * 0.14)})
        box_width, box_height = width * 0.18, height * 0.42
        ET.SubElement(pitch, tag("path"), {"d": rect_path(x, y + (height - box_height) / 2, box_width, box_height)})
        ET.SubElement(pitch, tag("path"), {"d": rect_path(x + width - box_width, y + (height - box_height) / 2, box_width, box_height)})

    def concept_match_day(self) -> ET.Element:
        root, art = self.root("02", "Match Day")
        self.base(art)
        ET.SubElement(art, tag("path"), {"d": "M0 0 H520 L1030 2500 H0 Z", "fill": CORAL})
        ET.SubElement(art, tag("path"), {"d": "M300 0 H780 L1270 2500 H800 Z", "fill": WHITE})
        ET.SubElement(art, tag("path"), {"d": "M640 0 H1050 L1470 2500 H1090 Z", "fill": NAVY_LIGHT})
        # Логотип нельзя класть на трёхцветную диагональ: белые элементы знака
        # на белой полосе пропадают. Под знаком — сплошное поле в цвет фона.
        ET.SubElement(art, tag("path"), {"id": "LOGO_FIELD", "d": circle_path(630, 915, 585), "fill": NAVY})
        ET.SubElement(
            art,
            tag("path"),
            {"d": circle_path(630, 915, 585), "fill": "none", "stroke": CORAL, "stroke-width": "14"},
        )
        self.add_logo(art, x=160, y=630, width=1000, height=980, element_id="LEFT_LOGO")
        self.add_pitch(art, x=1670, y=290, width=1120, height=1880, opacity=0.24)
        ET.SubElement(
            art,
            tag("path"),
            {"d": rounded_rect_path(1390, 220, 1280, 235, 42), "fill": NAVY_LIGHT, "stroke": WHITE, "stroke-width": "6"},
        )
        self.outliner.add_text(
            art,
            "АНИКОМ АРЕНА",
            x=2030,
            baseline=385,
            cap_height=82,
            max_width=1090,
            weight=760,
            tracking=15,
            align="center",
            element_id="TOP_LABEL_OUTLINES",
        )
        ET.SubElement(art, tag("path"), {"d": rect_path(1450, 610, 380, 25), "fill": CORAL})
        self.outliner.add_text(
            art, "МАТЧ", x=1450, baseline=1010, cap_height=260, max_width=1250, weight=780, element_id="MATCH_OUTLINES"
        )
        self.outliner.add_text(
            art, "ТРАНСЛЯЦИЯ", x=1450, baseline=1230, cap_height=120, max_width=1360, weight=780, element_id="BROADCAST_OUTLINES"
        )
        self.outliner.add_text(
            art,
            "ДАТА  •  ВРЕМЯ",
            x=1450,
            baseline=1570,
            cap_height=90,
            max_width=1130,
            weight=680,
            tracking=25,
            fill=MUTED,
            element_id="DATE_OUTLINES",
        )
        for index, label in enumerate(("ПАРТНЕР 01", "ПАРТНЕР 02", "ПАРТНЕР 03")):
            x = 1370 + index * 500
            ET.SubElement(
                art,
                tag("path"),
                {"d": rounded_rect_path(x, 1960, 430, 230, 30), "fill": NAVY_MID, "stroke": MUTED, "stroke-width": "7"},
            )
            self.outliner.add_text(
                art,
                label,
                x=x + 215,
                baseline=2098,
                cap_height=38,
                max_width=390,
                weight=670,
                tracking=12,
                align="center",
                element_id=f"PARTNER_{index + 1}_OUTLINES",
            )
        self.border(art)
        return root

    def concept_arena_energy(self) -> ET.Element:
        root, art = self.root("03", "Arena Energy")
        self.base(art, PLUM_DARK)
        ET.SubElement(art, tag("path"), {"d": "M0 0 H3000 L2150 2500 H0 Z", "fill": NAVY})
        ET.SubElement(art, tag("path"), {"d": "M0 1720 L3000 650 V980 L0 2060 Z", "fill": CORAL})
        ET.SubElement(art, tag("path"), {"d": "M0 1850 L3000 780 V900 L0 1970 Z", "fill": WHITE, "opacity": "0.92"})
        ET.SubElement(art, tag("path"), {"d": "M0 1960 L3000 890 V1050 L0 2120 Z", "fill": NAVY_LIGHT})
        for index, y in enumerate((470, 880, 1290, 1700)):
            self.outliner.add_text(
                art,
                "АРЕНА",
                x=1550,
                baseline=y,
                cap_height=420,
                max_width=2350,
                weight=820,
                tracking=-8,
                align="center",
                fill=WHITE,
                opacity=0.075 if index != 1 else 0.12,
                rotate=-8,
                element_id=f"BACKGROUND_WORD_{index + 1}_OUTLINES",
            )
        self.add_logo(art, x=160, y=150, width=720, height=710, opacity=0.96, element_id="TOP_LOGO")
        self.outliner.add_text(
            art,
            "ЭНЕРГИЯ ИГРЫ",
            x=2700,
            baseline=470,
            cap_height=140,
            max_width=1740,
            weight=790,
            tracking=8,
            align="right",
            element_id="ENERGY_OUTLINES",
        )
        self.outliner.add_text(
            art,
            "ПОЛЕ  •  СОБЫТИЯ  •  КОНТЕНТ",
            x=2700,
            baseline=675,
            cap_height=62,
            max_width=1560,
            weight=660,
            tracking=22,
            fill=MUTED,
            align="right",
            element_id="ENERGY_TAGLINE_OUTLINES",
        )
        ET.SubElement(art, tag("path"), {"d": circle_path(2440, 1880, 420), "fill": "none", "stroke": CORAL, "stroke-width": "18", "opacity": "0.75"})
        self.add_pitch(art, x=1780, y=1370, width=1080, height=820, opacity=0.22)
        self.border(art)
        return root

    def concept_partner_photozone(self) -> ET.Element:
        root, art = self.root("04", "Partner Photozone")
        self.base(art, NAVY_MID)
        ET.SubElement(art, tag("path"), {"d": "M0 0 H540 L780 2500 H0 Z", "fill": PLUM})
        ET.SubElement(art, tag("path"), {"d": "M3000 0 H2470 L2220 2500 H3000 Z", "fill": PLUM_DARK})
        # Alternating arena marks and partner cells form a photography-friendly repeat.
        x_positions = (420, 960, 1500, 2040, 2580)
        # Ряды разведены так, чтобы центр остался чистым под плашку с названием:
        # 690 + 167 = 857 сверху, 1810 - 167 = 1643 снизу, плашка занимает 1030–1470.
        y_positions = (300, 690, 1810, 2200)
        for row, y in enumerate(y_positions):
            for column, x in enumerate(x_positions):
                cell_id = row * len(x_positions) + column + 1
                if PLAQUE_ZONE[0] < x < PLAQUE_ZONE[2] and PLAQUE_ZONE[1] < y < PLAQUE_ZONE[3]:
                    continue
                if (row + column) % 2 == 0:
                    self.add_logo(
                        art,
                        x=x - 170,
                        y=y - 165,
                        width=340,
                        height=335,
                        opacity=0.92,
                        element_id=f"REPEAT_LOGO_{cell_id}",
                    )
                else:
                    ET.SubElement(
                        art,
                        tag("path"),
                        {"d": rounded_rect_path(x - 190, y - 90, 380, 180, 28), "fill": NAVY, "stroke": CORAL, "stroke-width": "8"},
                    )
                    self.outliner.add_text(
                        art,
                        "ПАРТНЕР",
                        x=x,
                        baseline=y + 28,
                        cap_height=42,
                        max_width=320,
                        weight=700,
                        tracking=16,
                        align="center",
                        element_id=f"PARTNER_CELL_{cell_id}_OUTLINES",
                    )
        ET.SubElement(art, tag("path"), {"d": rounded_rect_path(*PLAQUE_RECT, 55), "fill": NAVY, "stroke": CORAL, "stroke-width": "16"})
        self.outliner.add_text(
            art,
            "АНИКОМ АРЕНА",
            x=1500,
            baseline=1315,
            cap_height=104,
            max_width=1420,
            weight=790,
            tracking=18,
            align="center",
            element_id="CENTER_NAME_OUTLINES",
        )
        self.border(art)
        return root

    def serialize(self, root: ET.Element, path: Path) -> None:
        ET.indent(root, space="  ")
        body = ET.tostring(root, encoding="unicode", short_empty_elements=True)
        path.write_text('<?xml version="1.0" encoding="UTF-8"?>\n' + body + "\n", encoding="utf-8")

    def build_all(self) -> None:
        builders = [
            self.concept_arena_core,
            self.concept_match_day,
            self.concept_arena_energy,
            self.concept_partner_photozone,
        ]
        PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
        for (slug, _), build in zip(CONCEPTS, builders):
            self.outliner.boxes.clear()
            root = build()
            self.serialize(root, ROOT / f"{slug}.svg")


def validate(builder: ConceptBuilder) -> None:
    for slug, _ in CONCEPTS:
        path = ROOT / f"{slug}.svg"
        root = ET.parse(path).getroot()
        if root.get("viewBox") != f"0 0 {WIDTH} {HEIGHT}":
            raise RuntimeError(f"Incorrect viewBox in {path}")
        for forbidden in ("text", "image", "use", "foreignObject"):
            if root.findall(f".//{tag(forbidden)}"):
                raise RuntimeError(f"Forbidden <{forbidden}> in {path}")

    # Все надписи должны оставаться в безопасных полях, а не наезжать друг на друга.
    inner = (SAFE, SAFE, WIDTH - SAFE, HEIGHT - SAFE)
    for text, x0, y0, x1, y1 in builder.outliner.boxes:
        if x0 < inner[0] or y0 < inner[1] or x1 > inner[2] or y1 > inner[3]:
            raise RuntimeError(
                f"«{text[:40]}» выходит за безопасное поле: "
                f"x {x0:.0f}..{x1:.0f}, y {y0:.0f}..{y1:.0f}"
            )
    ordered = sorted(builder.outliner.boxes, key=lambda box: (box[2], box[1]))
    for index, first in enumerate(ordered):
        for second in ordered[index + 1:]:
            if second[2] >= first[4]:
                break
            if first[1] < second[3] and second[1] < first[3]:
                raise RuntimeError(f"Надписи пересекаются: «{first[0][:30]}» и «{second[0][:30]}»")


def render_previews() -> None:
    cards: list[Image.Image] = []
    for slug, title in CONCEPTS:
        svg = ROOT / f"{slug}.svg"
        png_bytes = resvg_py.svg_to_bytes(
            svg_path=str(svg),
            width=1200,
            height=1000,
            dpi=96,
        )
        image = Image.open(io.BytesIO(png_bytes)).convert("RGB")
        image.save(PREVIEW_DIR / f"{slug}.png", quality=96)
        cards.append(image)

    overview = Image.new("RGB", (2460, 2080), "#E8E4DC")
    positions = [(20, 20), (1240, 20), (20, 1040), (1240, 1040)]
    for image, position in zip(cards, positions):
        overview.paste(image, position)
    overview.save(ROOT / "concepts-overview.png", quality=95)


def main() -> None:
    builder = ConceptBuilder()
    builder.build_all()
    validate(builder)
    render_previews()
    print("Built 4 vector concepts at 3000 × 2500 mm")
    print("Live text, rasters and external references: none")


if __name__ == "__main__":
    main()
