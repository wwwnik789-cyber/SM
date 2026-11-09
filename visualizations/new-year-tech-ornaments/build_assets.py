#!/usr/bin/env python3
"""Build a 20-piece neon technology Christmas ornament SVG collection."""
from __future__ import annotations

from dataclasses import dataclass
from math import cos, pi, sin
from pathlib import Path
import csv
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
ELEMENT_DIR = ROOT / "elements"
PREVIEW_DIR = ROOT / "previews"
for directory in (ELEMENT_DIR, PREVIEW_DIR):
    directory.mkdir(parents=True, exist_ok=True)

MIDNIGHT = "#06152F"
NAVY = "#092A5E"
BLUE = "#075BFF"
ELECTRIC = "#18A8FF"
CYAN = "#35E7FF"
ICE = "#DDFBFF"
WHITE = "#FFFFFF"
VIOLET = "#7747FF"
MAGENTA = "#F02DFF"
CUT = "#FF00FF"

DEFS = f"""
<defs>
  <linearGradient id="gBlue" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="{CYAN}"/><stop offset="0.38" stop-color="{ELECTRIC}"/><stop offset="1" stop-color="{BLUE}"/>
  </linearGradient>
  <linearGradient id="gViolet" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="{MAGENTA}"/><stop offset="0.48" stop-color="{VIOLET}"/><stop offset="1" stop-color="{NAVY}"/>
  </linearGradient>
  <linearGradient id="gMidnight" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="{NAVY}"/><stop offset="0.52" stop-color="{MIDNIGHT}"/><stop offset="1" stop-color="{BLUE}"/>
  </linearGradient>
  <linearGradient id="gIce" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="{WHITE}"/><stop offset="0.48" stop-color="{ICE}"/><stop offset="1" stop-color="{CYAN}"/>
  </linearGradient>
  <radialGradient id="gOrb" cx="34%" cy="27%" r="78%">
    <stop offset="0" stop-color="{WHITE}"/><stop offset="0.22" stop-color="{CYAN}"/><stop offset="0.63" stop-color="{VIOLET}"/><stop offset="1" stop-color="{MIDNIGHT}"/>
  </radialGradient>
</defs>
"""


@dataclass(frozen=True)
class Ornament:
    index: int
    slug: str
    name_ru: str
    size_mm: int
    hole_mm: int
    outer: str
    hole_x: float
    hole_y: float
    gradient: str

    @property
    def filename(self) -> str:
        return f"{self.index:02d}-{self.slug}.svg"

    @property
    def clip_id(self) -> str:
        return f"clip{self.index:02d}"

    @property
    def hole_radius(self) -> float:
        return self.hole_mm * 150 / self.size_mm


def clean(content: str) -> str:
    return "\n".join(line.rstrip() for line in content.splitlines()) + "\n"


def star_points(cx: float, cy: float, outer: float, inner: float, count: int = 5, start: float = -pi / 2) -> str:
    points: list[str] = []
    for i in range(count * 2):
        radius = outer if i % 2 == 0 else inner
        angle = start + i * pi / count
        points.append(f"{cx + radius * cos(angle):.2f},{cy + radius * sin(angle):.2f}")
    return " ".join(points)


def radial_points(cx: float, cy: float, radii: list[float], start: float = -pi / 2) -> str:
    points: list[str] = []
    for i, radius in enumerate(radii):
        angle = start + 2 * pi * i / len(radii)
        points.append(f"{cx + radius * cos(angle):.2f},{cy + radius * sin(angle):.2f}")
    return " ".join(points)


def with_style(shape: str, style: str) -> str:
    return shape[:-2] + " " + style + "/>"


def svg_document(body: str, width: str, height: str, view_box: str, title: str) -> str:
    return clean(f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" width="{width}" height="{height}" viewBox="{view_box}">
<title>{title}</title>
{DEFS}
{body}
</svg>''')


def write_svg(path: Path, content: str) -> None:
    path.write_text(clean(content), encoding="utf-8")
    ET.parse(path)


def print_layer(body: str) -> str:
    return f'<g inkscape:groupmode="layer" inkscape:label="PRINT" id="PRINT">{body}</g>'


def cut_layer(contour: str) -> str:
    return (
        f'<g inkscape:groupmode="layer" inkscape:label="CutContour" id="CutContour" '
        f'fill="none" stroke="{CUT}" stroke-width="0.3mm" stroke-linejoin="round" '
        f'stroke-linecap="round" vector-effect="non-scaling-stroke" data-spot-color="CutContour">{contour}</g>'
    )


OUTERS = [
    '<path d="M130 48 V34 Q130 16 150 16 Q170 16 170 34 V48 C225 58 258 104 258 162 C258 225 210 274 150 274 C90 274 42 225 42 162 C42 104 75 58 130 48 Z"/>',
    f'<polygon points="{star_points(150,158,128,58,5)}"/>',
    '<path d="M80 270 V110 C80 58 111 28 155 28 C202 28 231 62 231 105 C231 139 214 161 190 181 L156 143 C173 129 183 119 183 103 C183 84 171 72 154 72 C135 72 123 87 123 110 V270 Z"/>',
    '<path d="M150 20 C105 58 86 118 92 182 L60 224 L103 220 L120 273 L150 246 L180 273 L197 220 L240 224 L208 182 C214 118 195 58 150 20 Z"/>',
    '<path d="M130 50 V30 Q130 14 150 14 Q170 14 170 30 V50 L196 78 H278 V164 H199 L181 207 L208 247 L174 274 L150 230 L126 274 L92 247 L119 207 L101 164 H22 V78 H104 Z"/>',
    '<path d="M130 44 V26 Q130 10 150 10 Q170 10 170 26 V44 H218 Q242 44 242 68 V214 Q242 238 218 238 H200 V276 H158 V238 H142 V276 H100 V238 H82 Q58 238 58 214 V68 Q58 44 82 44 Z"/>',
    '<path d="M132 62 V39 Q132 20 150 20 Q168 20 168 39 V62 C225 62 266 105 274 184 Q280 244 245 258 Q216 270 194 221 L180 194 H120 L106 221 Q84 270 55 258 Q20 244 26 184 Q34 105 91 62 Z"/>',
    f'<polygon points="{radial_points(150,150,[130 if i%2==0 else 76 for i in range(24)])}"/>',
    '<path d="M150 20 L110 72 H127 L85 128 H108 L58 194 H126 V224 H112 V278 H188 V224 H174 L242 194 L192 128 H215 L173 72 H190 Z"/>',
    '<path d="M118 48 V31 Q118 15 136 15 Q154 15 154 31 V85 L174 55 Q190 42 205 55 Q219 68 208 84 L180 118 V225 Q180 272 132 276 Q79 280 58 233 L31 173 Q24 156 39 146 Q55 135 68 150 L88 176 V48 Z"/>',
    '<path d="M100 60 V17 Q100 5 112 5 H188 Q200 5 200 17 V60 H184 V168 Q184 204 214 221 Q248 240 235 266 Q224 286 196 278 L146 263 Q98 249 98 199 V60 Z"/>',
    '<path d="M130 53 V34 Q130 16 150 16 Q170 16 170 34 V53 C213 61 229 102 228 159 C228 194 244 218 259 232 H178 Q172 271 150 271 Q128 271 122 232 H41 C56 218 72 194 72 159 C71 102 87 61 130 53 Z"/>',
    '<path d="M134 50 V32 Q134 16 150 16 Q166 16 166 32 V50 L238 135 L150 278 L62 135 Z"/>',
    '<path d="M132 45 V30 Q132 14 150 14 Q168 14 168 30 V45 L236 85 L264 160 L226 235 L150 276 L74 235 L36 160 L64 85 Z"/>',
    '<path d="M130 34 V24 Q130 10 146 10 Q162 10 162 24 V34 C206 43 235 78 236 121 C237 149 226 174 207 193 L268 238 L226 242 L248 276 L185 228 C165 239 143 244 120 239 L58 275 L81 236 L32 232 L93 193 C68 170 56 139 62 105 C68 65 94 42 130 34 Z"/>',
    '<path d="M135 36 V22 Q135 8 150 8 Q165 8 165 22 V36 C220 44 258 90 258 150 V213 Q258 246 225 246 H201 V143 H231 C228 99 195 68 150 68 C105 68 72 99 69 143 H99 V246 H75 Q42 246 42 213 V150 C42 90 80 44 135 36 Z"/>',
    '<path d="M150 62 C119 34 95 34 85 53 C73 76 91 96 126 97 H54 V276 H246 V97 H174 C209 96 227 76 215 53 C205 34 181 34 150 62 Z"/>',
    '<path d="M132 40 V25 Q132 10 150 10 Q168 10 168 25 V40 L266 128 L240 128 V276 H60 V128 H34 Z"/>',
    '<path d="M132 43 V28 Q132 12 150 12 Q168 12 168 28 V43 C218 52 250 91 252 138 L278 155 L258 186 L244 180 C226 224 191 254 150 254 C108 254 72 224 56 180 L42 186 L22 155 L48 138 C50 91 82 52 132 43 Z"/>',
    '<path d="M132 48 V31 Q132 14 150 14 Q168 14 168 31 V48 C223 57 258 101 258 159 C258 201 239 231 216 249 L231 284 H69 L84 249 C61 231 42 201 42 159 C42 101 77 57 132 48 Z"/>',
]

SPECS = [
    ("pixel-orb", "Пиксельный шар", 70, 5, 150, 31, "gBlue"),
    ("circuit-star", "Звезда-схема", 80, 5, 150, 54, "gViolet"),
    ("neon-candy-cane", "Неоновый леденец", 90, 5, 155, 52, "gBlue"),
    ("launch-rocket", "Ракета", 100, 5, 150, 47, "gMidnight"),
    ("orbit-satellite", "Спутник", 110, 5, 150, 29, "gViolet"),
    ("friendly-robot", "Робот", 120, 5, 150, 26, "gBlue"),
    ("cyber-gamepad", "Геймпад", 130, 6, 150, 40, "gViolet"),
    ("digital-snowflake", "Цифровая снежинка", 140, 6, 150, 46, "gIce"),
    ("circuit-tree", "Ёлка-схема", 150, 6, 150, 48, "gMidnight"),
    ("neon-mitten", "Неоновая варежка", 160, 6, 136, 32, "gViolet"),
    ("data-stocking", "Носок с сеткой", 175, 7, 150, 34, "gBlue"),
    ("signal-bell", "Сигнальный колокол", 190, 7, 150, 33, "gMidnight"),
    ("crystal-diamond", "Кристалл", 210, 7, 150, 33, "gViolet"),
    ("network-hexagon", "Сетевой шестиугольник", 230, 8, 150, 30, "gBlue"),
    ("electric-comet", "Электрическая комета", 250, 8, 146, 25, "gViolet"),
    ("audio-headphones", "Наушники", 270, 8, 150, 23, "gMidnight"),
    ("smart-gift", "Умный подарок", 290, 9, 150, 76, "gBlue"),
    ("future-house", "Дом будущего", 310, 9, 150, 26, "gViolet"),
    ("orbit-planet", "Орбитальная планета", 330, 9, 150, 29, "gBlue"),
    ("digital-snow-globe", "Цифровой снежный шар", 350, 10, 150, 31, "gMidnight"),
]

ORNAMENTS = [
    Ornament(index, slug, name_ru, size, hole, OUTERS[index - 1], hx, hy, gradient)
    for index, (slug, name_ru, size, hole, hx, hy, gradient) in enumerate(SPECS, start=1)
]


def generic_tech(index: int) -> str:
    shift = (index * 13) % 42
    angle = (index * 17) % 70 - 35
    return f'''
<g transform="rotate({angle} 150 150)">
  <path d="M-30 {58+shift} L105 18 L342 92 L212 150 Z" fill="{WHITE}" opacity=".10"/>
  <path d="M-18 {215-shift/2:.1f} L112 158 L329 232 L185 292 Z" fill="{CYAN}" opacity=".12"/>
</g>
<g fill="none" stroke="{ICE}" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round" opacity=".78">
  <path d="M24 {94+shift/3:.1f} H88 L112 {118+shift/3:.1f} H206 L230 {94+shift/3:.1f} H282"/>
  <path d="M35 {220-shift/4:.1f} H92 L118 {194-shift/4:.1f} H187 L212 {219-shift/4:.1f} H272"/>
</g>
<g fill="{CYAN}" stroke="{WHITE}" stroke-width="1.2">
  <circle cx="88" cy="{94+shift/3:.1f}" r="5"/><circle cx="206" cy="{118+shift/3:.1f}" r="5"/>
  <circle cx="92" cy="{220-shift/4:.1f}" r="5"/><circle cx="212" cy="{219-shift/4:.1f}" r="5"/>
</g>
<path d="M42 151 H258" stroke="{WHITE}" stroke-width="1.5" stroke-dasharray="2 9" opacity=".46"/>
'''


def motif(index: int) -> str:
    motifs = {
        1: f'<g fill="{WHITE}" opacity=".82"><rect x="112" y="113" width="28" height="28"/><rect x="145" y="80" width="28" height="28"/><rect x="145" y="146" width="28" height="28"/><rect x="178" y="113" width="28" height="28"/><rect x="112" y="179" width="28" height="28"/></g>',
        2: f'<polygon points="{star_points(150,158,76,34,5)}" fill="none" stroke="{WHITE}" stroke-width="6"/><polygon points="{star_points(150,158,43,20,5)}" fill="{CYAN}" opacity=".5"/>',
        3: f'<path d="M103 92 L176 165 M91 132 L163 204 M86 177 L151 242" stroke="{WHITE}" stroke-width="9" opacity=".72"/>',
        4: f'<circle cx="150" cy="105" r="29" fill="none" stroke="{WHITE}" stroke-width="6"/><path d="M150 136 V224 M118 189 H182 M132 229 L150 246 L168 229" fill="none" stroke="{CYAN}" stroke-width="6"/>',
        5: f'<rect x="112" y="104" width="76" height="76" rx="12" fill="none" stroke="{WHITE}" stroke-width="6"/><path d="M30 98 H104 M196 98 H270 M30 121 H104 M196 121 H270 M30 144 H104 M196 144 H270" stroke="{CYAN}" stroke-width="4"/>',
        6: f'<rect x="92" y="88" width="116" height="94" rx="20" fill="none" stroke="{WHITE}" stroke-width="6"/><circle cx="124" cy="126" r="10" fill="{CYAN}"/><circle cx="176" cy="126" r="10" fill="{CYAN}"/><path d="M116 156 H184 M126 156 V170 M150 156 V170 M174 156 V170" stroke="{WHITE}" stroke-width="5"/>',
        7: f'<path d="M88 151 H136 M112 127 V175" stroke="{WHITE}" stroke-width="10"/><circle cx="194" cy="136" r="9" fill="{CYAN}"/><circle cx="218" cy="160" r="9" fill="{WHITE}"/><path d="M135 211 Q150 225 165 211" fill="none" stroke="{CYAN}" stroke-width="5"/>',
        8: f'<g fill="none" stroke="{NAVY}" stroke-width="6" stroke-linecap="round"><path d="M150 73 V227 M83 112 L217 188 M83 188 L217 112"/><path d="M150 92 L132 110 M150 92 L168 110 M150 208 L132 190 M150 208 L168 190"/></g><circle cx="150" cy="150" r="20" fill="{VIOLET}"/>',
        9: f'<path d="M150 66 V232 M150 100 L110 132 M150 124 L190 151 M150 166 L105 202 M150 190 L196 218" fill="none" stroke="{WHITE}" stroke-width="6"/><g fill="{CYAN}"><circle cx="110" cy="132" r="8"/><circle cx="190" cy="151" r="8"/><circle cx="105" cy="202" r="8"/><circle cx="196" cy="218" r="8"/></g>',
        10: f'<path d="M108 99 H151 L172 121 V204 H114 L94 184 V121 Z" fill="none" stroke="{WHITE}" stroke-width="6"/><path d="M115 132 H151 L166 147 M115 164 H145 L161 180" stroke="{CYAN}" stroke-width="5"/>',
        11: f'<path d="M111 90 H188 M111 121 H188 M109 152 H181 M108 183 H177 M122 218 L199 241" stroke="{WHITE}" stroke-width="5" opacity=".78"/><path d="M125 77 V217 M155 77 V230" stroke="{CYAN}" stroke-width="3" opacity=".72"/>',
        12: f'<path d="M111 156 Q150 176 189 156 M126 189 Q150 204 174 189" fill="none" stroke="{WHITE}" stroke-width="7"/><path d="M90 115 Q58 151 90 187 M210 115 Q242 151 210 187" fill="none" stroke="{CYAN}" stroke-width="5"/>',
        13: f'<path d="M150 65 L205 135 L150 252 L95 135 Z M150 65 V252 M95 135 H205 M150 65 L95 135 L150 164 L205 135 Z" fill="none" stroke="{WHITE}" stroke-width="5"/><path d="M150 164 L120 135 L150 91 L180 135 Z" fill="{CYAN}" opacity=".38"/>',
        14: f'<polygon points="{radial_points(150,158,[73]*6)}" fill="none" stroke="{WHITE}" stroke-width="6"/><polygon points="{radial_points(150,158,[39]*6)}" fill="none" stroke="{CYAN}" stroke-width="5"/><path d="M150 85 V231 M87 122 L213 194 M87 194 L213 122" stroke="{WHITE}" stroke-width="3"/>',
        15: f'<circle cx="143" cy="122" r="56" fill="none" stroke="{WHITE}" stroke-width="7"/><circle cx="143" cy="122" r="28" fill="{CYAN}" opacity=".5"/><path d="M95 178 L50 217 M119 197 L85 239 M152 204 L135 250" stroke="{WHITE}" stroke-width="7" stroke-linecap="round"/>',
        16: f'<path d="M91 157 Q93 92 150 92 Q207 92 209 157" fill="none" stroke="{WHITE}" stroke-width="9"/><rect x="82" y="150" width="35" height="75" rx="13" fill="none" stroke="{CYAN}" stroke-width="6"/><rect x="183" y="150" width="35" height="75" rx="13" fill="none" stroke="{CYAN}" stroke-width="6"/><path d="M129 183 V208 M150 171 V220 M171 188 V204" stroke="{WHITE}" stroke-width="6"/>',
        17: f'<path d="M150 101 V270 M59 161 H241" stroke="{WHITE}" stroke-width="10"/><path d="M150 101 L112 65 M150 101 L188 65" stroke="{CYAN}" stroke-width="7"/><rect x="83" y="184" width="134" height="58" rx="10" fill="none" stroke="{CYAN}" stroke-width="5"/>',
        18: f'<path d="M91 139 L150 86 L209 139 V235 H91 Z" fill="none" stroke="{WHITE}" stroke-width="6"/><rect x="119" y="164" width="62" height="71" fill="none" stroke="{CYAN}" stroke-width="5"/><path d="M119 194 H181 M150 164 V235" stroke="{WHITE}" stroke-width="4"/>',
        19: f'<ellipse cx="150" cy="151" rx="96" ry="39" fill="none" stroke="{WHITE}" stroke-width="7" transform="rotate(-18 150 151)"/><circle cx="150" cy="151" r="59" fill="none" stroke="{CYAN}" stroke-width="6"/><circle cx="219" cy="116" r="9" fill="{WHITE}"/><circle cx="82" cy="185" r="7" fill="{MAGENTA}"/>',
        20: f'<path d="M91 194 Q150 225 209 194" fill="none" stroke="{WHITE}" stroke-width="6"/><path d="M150 87 L120 132 H135 L103 174 H197 L165 132 H180 Z" fill="none" stroke="{CYAN}" stroke-width="6"/><path d="M94 244 H206" stroke="{WHITE}" stroke-width="8"/><g fill="{WHITE}"><circle cx="97" cy="108" r="6"/><circle cx="207" cy="130" r="5"/><circle cx="82" cy="167" r="5"/></g>',
    }
    return motifs[index]


def ornament_body(ornament: Ornament) -> str:
    fill_style = f'fill="url(#{ornament.gradient})" stroke="{ICE}" stroke-width="4.5" stroke-linejoin="round"'
    shape = with_style(ornament.outer, fill_style)
    return f'''
<defs><clipPath id="{ornament.clip_id}">{ornament.outer}</clipPath></defs>
<g clip-path="url(#{ornament.clip_id})">
  {shape}
  {generic_tech(ornament.index)}
  {motif(ornament.index)}
</g>
<circle cx="{ornament.hole_x}" cy="{ornament.hole_y}" r="{ornament.hole_radius + 3:.3f}" fill="{MIDNIGHT}" stroke="{ICE}" stroke-width="2.5"/>
'''


def ornament_cut(ornament: Ornament) -> str:
    return (
        ornament.outer
        + f'<circle cx="{ornament.hole_x}" cy="{ornament.hole_y}" r="{ornament.hole_radius:.3f}" data-purpose="hanging-hole"/>'
    )


# Individual production SVGs.
for ornament in ORNAMENTS:
    layers = print_layer(ornament_body(ornament)) + cut_layer(ornament_cut(ornament))
    write_svg(
        ELEMENT_DIR / ornament.filename,
        svg_document(layers, f"{ornament.size_mm}mm", f"{ornament.size_mm}mm", "0 0 300 300", ornament.slug),
    )

# Actual-scale combined sheet: 5 columns × 4 rows, 370 mm cells.
CELL = 370
sheet_print: list[str] = []
sheet_cut: list[str] = []
for idx, ornament in enumerate(ORNAMENTS):
    col, row = idx % 5, idx // 5
    scale = ornament.size_mm / 300
    x = col * CELL + (CELL - ornament.size_mm) / 2
    y = row * CELL + (CELL - ornament.size_mm) / 2
    sheet_print.append(f'<g transform="translate({x:.3f} {y:.3f}) scale({scale:.6f})">{ornament_body(ornament)}</g>')
    sheet_cut.append(f'<g transform="translate({x:.3f} {y:.3f}) scale({scale:.6f})">{ornament_cut(ornament)}</g>')
combined = print_layer("".join(sheet_print)) + cut_layer("".join(sheet_cut))
write_svg(
    ELEMENT_DIR / "00-all-20-tech-ornaments-actual-scale.svg",
    svg_document(combined, "1850mm", "1480mm", "0 0 1850 1480", "20 technology ornaments actual-scale sheet"),
)

# CSV manifest.
with (ROOT / "manifest.csv").open("w", encoding="utf-8", newline="") as file:
    writer = csv.writer(file, lineterminator="\n")
    writer.writerow(["index", "file", "name_ru", "artboard_mm", "hanging_hole_mm", "layers", "logo"])
    for ornament in ORNAMENTS:
        writer.writerow([
            ornament.index,
            ornament.filename,
            ornament.name_ru,
            f"{ornament.size_mm}x{ornament.size_mm}",
            ornament.hole_mm,
            "PRINT + CutContour",
            "none",
        ])

# Preview 1: all printed forms.
preview_cards: list[str] = []
for idx, ornament in enumerate(ORNAMENTS):
    col, row = idx % 5, idx // 5
    x, y = 36 + col * 229, 126 + row * 132
    preview_cards.append(
        f'<rect x="{x}" y="{y}" width="208" height="116" rx="15" fill="#0A2143" stroke="#176B9A"/>'
        f'<g transform="translate({x+65} {y+4}) scale(.34)">{ornament_body(ornament)}</g>'
        f'<text x="{x+12}" y="{y+97}" font-family="DejaVu Sans,sans-serif" font-size="13" font-weight="700" fill="{WHITE}">{ornament.index:02d} · {ornament.name_ru}</text>'
        f'<text x="{x+12}" y="{y+112}" font-family="DejaVu Sans,sans-serif" font-size="11" fill="{CYAN}">{ornament.size_mm} × {ornament.size_mm} мм · отверстие {ornament.hole_mm} мм</text>'
    )
preview1 = (
    f'<rect width="1200" height="675" fill="{MIDNIGHT}"/>'
    f'<path d="M0 0 H410 L345 102 H0 Z" fill="{BLUE}" opacity=".42"/>'
    f'<text x="38" y="56" font-family="DejaVu Sans,sans-serif" font-size="31" font-weight="700" fill="{WHITE}">TECH NEON · 20 НОВОГОДНИХ ИГРУШЕК</text>'
    f'<text x="38" y="88" font-family="DejaVu Sans,sans-serif" font-size="16" fill="{CYAN}">70–350 ММ · PRINT + CUTCONTOUR · БЕЗ ЛОГОТИПОВ</text>'
    + "".join(preview_cards)
)
write_svg(PREVIEW_DIR / "01-tech-ornaments-board.svg", svg_document(preview1, "1200px", "675px", "0 0 1200 675", "Technology ornaments preview"))

# Preview 2: cut contours and hanging holes.
cut_cards: list[str] = []
for idx, ornament in enumerate(ORNAMENTS):
    col, row = idx % 5, idx // 5
    x, y = 36 + col * 229, 126 + row * 132
    cut_cards.append(
        f'<rect x="{x}" y="{y}" width="208" height="116" rx="15" fill="#F8FBFF" stroke="#D7E5EF"/>'
        f'<g transform="translate({x+65} {y+4}) scale(.34)" fill="none" stroke="{CUT}" stroke-width="2.2" stroke-linejoin="round">{ornament_cut(ornament)}</g>'
        f'<text x="{x+12}" y="{y+100}" font-family="DejaVu Sans,sans-serif" font-size="12" font-weight="700" fill="{MIDNIGHT}">{ornament.index:02d} · {ornament.size_mm} мм</text>'
    )
preview2 = (
    f'<rect width="1200" height="675" fill="#EAF2F7"/>'
    f'<rect x="0" y="0" width="1200" height="105" fill="{MIDNIGHT}"/>'
    f'<text x="38" y="54" font-family="DejaVu Sans,sans-serif" font-size="31" font-weight="700" fill="{WHITE}">КОНТУРЫ РЕЗА · OUTER + HANGING HOLE</text>'
    f'<text x="38" y="84" font-family="DejaVu Sans,sans-serif" font-size="15" fill="{CYAN}">CUTCONTOUR · 0,3 ММ · 100% MAGENTA</text>'
    + "".join(cut_cards)
)
write_svg(PREVIEW_DIR / "02-cut-contours-board.svg", svg_document(preview2, "1200px", "675px", "0 0 1200 675", "Cut contours preview"))

# Preview 3: true relative scale of four key sizes.
selected = [ORNAMENTS[0], ORNAMENTS[8], ORNAMENTS[14], ORNAMENTS[19]]
x_positions = [65, 220, 480, 805]
size_groups: list[str] = []
BASELINE = 530
for ornament, x in zip(selected, x_positions):
    scale = ornament.size_mm / 400
    top = BASELINE - 300 * scale
    size_groups.append(
        f'<g transform="translate({x} {top:.2f}) scale({scale:.6f})">{ornament_body(ornament)}</g>'
        f'<line x1="{x}" y1="{BASELINE+12}" x2="{x+ornament.size_mm*.75}" y2="{BASELINE+12}" stroke="{CYAN}" stroke-width="2"/>'
        f'<text x="{x + ornament.size_mm*.375:.2f}" y="{BASELINE+43}" text-anchor="middle" font-family="DejaVu Sans,sans-serif" font-size="18" font-weight="700" fill="{WHITE}">{ornament.size_mm} мм</text>'
    )
preview3 = (
    f'<rect width="1200" height="675" fill="{MIDNIGHT}"/>'
    f'<text x="42" y="62" font-family="DejaVu Sans,sans-serif" font-size="31" font-weight="700" fill="{WHITE}">ДИАПАЗОН РАЗМЕРОВ · 70–350 ММ</text>'
    f'<text x="42" y="94" font-family="DejaVu Sans,sans-serif" font-size="16" fill="{CYAN}">ЧЕТЫРЕ КОНТРОЛЬНЫЕ ФОРМЫ ПОКАЗАНЫ В ЕДИНОМ МАСШТАБЕ</text>'
    f'<line x1="42" y1="542" x2="1158" y2="542" stroke="#21466F" stroke-width="2"/>'
    + "".join(size_groups)
    + f'<text x="42" y="625" font-family="DejaVu Sans,sans-serif" font-size="14" fill="#A9C9DE">Соотношение размеров сохранено. Артборд каждого производственного SVG задан в миллиметрах.</text>'
)
write_svg(PREVIEW_DIR / "03-size-range-board.svg", svg_document(preview3, "1200px", "675px", "0 0 1200 675", "Size range preview"))

print(f"Generated {len(ORNAMENTS)} ornaments, one actual-scale sheet, manifest and 3 preview boards in {ROOT}")
