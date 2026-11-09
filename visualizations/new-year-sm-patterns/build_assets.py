#!/usr/bin/env python3
"""Build editable SVG New Year ornaments and seamless patterns for SM Production."""
from __future__ import annotations

from pathlib import Path
from math import cos, sin, pi
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
PRINT_DIR = ROOT / "elements" / "print"
CUT_DIR = ROOT / "elements" / "contours"
PATTERN_DIR = ROOT / "patterns"
PREVIEW_DIR = ROOT / "previews"
for directory in (PRINT_DIR, CUT_DIR, PATTERN_DIR, PREVIEW_DIR):
    directory.mkdir(parents=True, exist_ok=True)

RED = "#B3262D"
DARK_RED = "#731A24"
GREEN = "#17483A"
DARK_GREEN = "#0B2F27"
GOLD = "#D6B45B"
LIGHT_GOLD = "#F1D98E"
CREAM = "#FFF8E9"
WHITE = "#FFFFFF"
CHARCOAL = "#17231F"
MAGENTA = "#FF00FF"

DEFS = f"""
<defs>
  <linearGradient id="redGradient" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#DC4A4A"/><stop offset="0.55" stop-color="{RED}"/><stop offset="1" stop-color="{DARK_RED}"/>
  </linearGradient>
  <linearGradient id="greenGradient" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#2C6B55"/><stop offset="0.55" stop-color="{GREEN}"/><stop offset="1" stop-color="{DARK_GREEN}"/>
  </linearGradient>
  <linearGradient id="goldGradient" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#FFF0B5"/><stop offset="0.45" stop-color="{GOLD}"/><stop offset="1" stop-color="#9F7630"/>
  </linearGradient>
</defs>
"""


def svg_document(body: str, view_box: str = "0 0 300 300", width: str = "300mm", height: str = "300mm", defs: str = DEFS, title: str = "") -> str:
    title_node = f"<title>{title}</title>" if title else ""
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="{view_box}">
{title_node}
{defs}
{body}
</svg>
'''


def write_svg(path: Path, content: str) -> None:
    content = "\n".join(line.rstrip() for line in content.splitlines()) + "\n"
    path.write_text(content, encoding="utf-8")
    ET.parse(path)


def points(cx: float, cy: float, radii: list[float], start: float = -pi / 2) -> str:
    values = []
    for index, radius in enumerate(radii):
        angle = start + 2 * pi * index / len(radii)
        values.append(f"{cx + radius * cos(angle):.2f},{cy + radius * sin(angle):.2f}")
    return " ".join(values)


def star_points(cx: float, cy: float, outer: float, inner: float, count: int = 5, start: float = -pi / 2) -> str:
    radii = [outer if i % 2 == 0 else inner for i in range(count * 2)]
    return points(cx, cy, radii, start)


def sm_mark(x: float, y: float, scale: float = 1.0, color: str = CREAM, opacity: float = 0.58, stroke: float = 3.2) -> str:
    """Compact path-based SM monogram; no external font is required."""
    return f'''
<g class="sm-monogram" transform="translate({x} {y}) scale({scale})" fill="{color}" opacity="{opacity}">
  <path d="M-28 -14 H-8 V-8 H-21 Q-24 -8 -24 -5 Q-24 -2 -21 -2 H-14 Q-7 -2 -7 6 Q-7 14 -15 14 H-28 V8 H-16 Q-12 8 -12 5 Q-12 2 -16 2 H-22 Q-30 2 -30 -6 Q-30 -14 -22 -14 Z"/>
  <path d="M0 14 V-14 H6 L14 -2 L22 -14 H28 V14 H22 V-5 L14 6 L6 -5 V14 Z"/>
</g>'''


def snowflake(cx: float, cy: float, radius: float, color: str, stroke_width: float = 5, arms: int = 6, opacity: float = 1.0, rotation: float = 0) -> str:
    arm = f'''
<g fill="none" stroke="{color}" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round" opacity="{opacity}">
  <path d="M0 0 V-{radius}"/>
  <path d="M0 -{radius * 0.48:.2f} L-{radius * 0.20:.2f} -{radius * 0.66:.2f} M0 -{radius * 0.48:.2f} L{radius * 0.20:.2f} -{radius * 0.66:.2f}"/>
  <path d="M0 -{radius * 0.73:.2f} L-{radius * 0.16:.2f} -{radius * 0.86:.2f} M0 -{radius * 0.73:.2f} L{radius * 0.16:.2f} -{radius * 0.86:.2f}"/>
  <circle cx="0" cy="-{radius}" r="{stroke_width * 0.62:.2f}" fill="{color}" stroke="none"/>
</g>'''
    rotated = "".join(f'<g transform="rotate({rotation + 360 * i / arms})">{arm}</g>' for i in range(arms))
    return f'<g transform="translate({cx} {cy})">{rotated}</g>'


def tree_art(cx: float, cy: float, scale: float = 1.0, variant: int = 1) -> str:
    if variant == 1:
        return f'''
<g transform="translate({cx} {cy}) scale({scale})">
  <path d="M0 -108 L-42 -48 H-22 L-63 10 H-34 L-84 75 H84 L34 10 H63 L22 -48 H42 Z" fill="url(#greenGradient)" stroke="{GOLD}" stroke-width="4" stroke-linejoin="round"/>
  <path d="M-44 -20 Q0 4 44 -20 M-61 31 Q0 57 61 31" fill="none" stroke="{LIGHT_GOLD}" stroke-width="4" stroke-linecap="round"/>
  <circle cx="-26" cy="-43" r="5" fill="{RED}"/><circle cx="24" cy="-8" r="5" fill="{CREAM}"/><circle cx="-39" cy="27" r="6" fill="{RED}"/><circle cx="33" cy="48" r="6" fill="{CREAM}"/>
  <polygon points="{star_points(0, -116, 14, 6.5)}" fill="url(#goldGradient)"/>
  <rect x="-13" y="75" width="26" height="27" rx="4" fill="{DARK_RED}"/>
  {sm_mark(0, 55, 0.42, LIGHT_GOLD, 0.62, 3.5)}
</g>'''
    if variant == 2:
        return f'''
<g transform="translate({cx} {cy}) scale({scale})">
  <path d="M0 -110 Q-8 -75 -47 -44 H-20 Q-29 -12 -70 17 H-35 Q-43 47 -91 79 H91 Q43 47 35 17 H70 Q29 -12 20 -44 H47 Q8 -75 0 -110 Z" fill="url(#redGradient)" stroke="{LIGHT_GOLD}" stroke-width="4"/>
  <path d="M-42 -33 Q0 -15 42 -33 M-62 25 Q0 48 62 25" fill="none" stroke="{CREAM}" stroke-width="3.5" stroke-dasharray="5 9" stroke-linecap="round"/>
  <circle cx="0" cy="-64" r="6" fill="{GOLD}"/><circle cx="-34" cy="1" r="5" fill="{GREEN}"/><circle cx="43" cy="36" r="6" fill="{GREEN}"/>
  <polygon points="{star_points(0, -119, 13, 6)}" fill="{GOLD}"/>
  <rect x="-13" y="79" width="26" height="24" rx="4" fill="{GREEN}"/>
  {sm_mark(0, 62, 0.38, CREAM, 0.52, 3.4)}
</g>'''
    return f'''
<g transform="translate({cx} {cy}) scale({scale})">
  <polygon points="0,-108 -49,-42 49,-42" fill="{GREEN}"/>
  <polygon points="0,-68 -72,10 72,10" fill="{DARK_GREEN}"/>
  <polygon points="0,-22 -94,82 94,82" fill="{GREEN}" stroke="{GOLD}" stroke-width="4" stroke-linejoin="round"/>
  <path d="M-61 14 H61 M-43 48 H43" stroke="{LIGHT_GOLD}" stroke-width="4" stroke-linecap="round"/>
  <circle cx="0" cy="-69" r="6" fill="{RED}"/><circle cx="-29" cy="-7" r="6" fill="{RED}"/><circle cx="31" cy="35" r="6" fill="{RED}"/>
  <rect x="-14" y="82" width="28" height="25" rx="4" fill="{DARK_RED}"/>
  {sm_mark(0, 64, 0.38, LIGHT_GOLD, 0.56, 3.4)}
</g>'''


def round_bauble(cx: float, cy: float, scale: float = 1.0) -> str:
    return f'''
<g transform="translate({cx} {cy}) scale({scale})">
  <path d="M-17 -98 V-112 Q-17 -126 0 -126 Q17 -126 17 -112 V-98" fill="none" stroke="{GOLD}" stroke-width="6"/>
  <rect x="-24" y="-102" width="48" height="21" rx="6" fill="url(#goldGradient)"/>
  <circle cx="0" cy="0" r="87" fill="url(#redGradient)" stroke="{LIGHT_GOLD}" stroke-width="5"/>
  <path d="M-76 -22 Q0 23 76 -22 M-76 27 Q0 -13 76 27" fill="none" stroke="{GOLD}" stroke-width="7" opacity="0.9"/>
  <circle cx="-42" cy="-48" r="12" fill="{WHITE}" opacity="0.18"/>
  {sm_mark(0, 7, 1.05, CREAM, 0.52, 3.0)}
</g>'''


def long_bauble(cx: float, cy: float, scale: float = 1.0) -> str:
    return f'''
<g transform="translate({cx} {cy}) scale({scale})">
  <path d="M-14 -108 V-121 Q-14 -134 0 -134 Q14 -134 14 -121 V-108" fill="none" stroke="{GOLD}" stroke-width="6"/>
  <rect x="-22" y="-111" width="44" height="20" rx="5" fill="url(#goldGradient)"/>
  <path d="M0 -93 C58 -93 69 -52 52 -10 C39 24 25 61 0 92 C-25 61 -39 24 -52 -10 C-69 -52 -58 -93 0 -93 Z" fill="url(#greenGradient)" stroke="{LIGHT_GOLD}" stroke-width="5"/>
  <path d="M-47 -36 Q0 -5 47 -36 M-39 20 Q0 -4 39 20" fill="none" stroke="{GOLD}" stroke-width="6"/>
  {sm_mark(0, 45, 0.75, CREAM, 0.5, 3.2)}
</g>'''


def diamond_bauble(cx: float, cy: float, scale: float = 1.0) -> str:
    return f'''
<g transform="translate({cx} {cy}) scale({scale})">
  <path d="M0 -130 Q-15 -130 -15 -115 V-104" fill="none" stroke="{GOLD}" stroke-width="6"/>
  <path d="M0 -104 L75 -20 L0 96 L-75 -20 Z" fill="url(#goldGradient)" stroke="{DARK_RED}" stroke-width="5" stroke-linejoin="round"/>
  <path d="M0 -86 L55 -18 L0 73 L-55 -18 Z" fill="{RED}"/>
  <path d="M-52 -18 H52 M0 -84 V72" stroke="{LIGHT_GOLD}" stroke-width="4" opacity="0.75"/>
  {sm_mark(0, 0, 0.75, CREAM, 0.5, 3.1)}
</g>'''


def star_bauble(cx: float, cy: float, scale: float = 1.0) -> str:
    return f'''
<g transform="translate({cx} {cy}) scale({scale})">
  <polygon points="{star_points(0, 2, 100, 43)}" fill="url(#goldGradient)" stroke="{DARK_GREEN}" stroke-width="6" stroke-linejoin="round"/>
  <polygon points="{star_points(0, 2, 65, 28)}" fill="{GREEN}"/>
  {sm_mark(0, 7, 0.72, CREAM, 0.52, 3.1)}
</g>'''


def bell(cx: float, cy: float, scale: float = 1.0) -> str:
    return f'''
<g transform="translate({cx} {cy}) scale({scale})">
  <path d="M-20 -91 Q0 -118 20 -91" fill="none" stroke="{GOLD}" stroke-width="8"/>
  <path d="M0 -89 C-43 -89 -58 -53 -57 3 C-56 39 -72 57 -80 66 H80 C72 57 56 39 57 3 C58 -53 43 -89 0 -89 Z" fill="url(#redGradient)" stroke="{LIGHT_GOLD}" stroke-width="5"/>
  <path d="M-61 31 Q0 50 61 31" fill="none" stroke="{GOLD}" stroke-width="6"/>
  <circle cx="0" cy="74" r="16" fill="url(#goldGradient)"/>
  {sm_mark(0, -4, 0.70, CREAM, 0.48, 3.2)}
</g>'''


def drop_bauble(cx: float, cy: float, scale: float = 1.0) -> str:
    return f'''
<g transform="translate({cx} {cy}) scale({scale})">
  <path d="M0 -128 V-104" stroke="{GOLD}" stroke-width="6" stroke-linecap="round"/>
  <path d="M0 -105 C23 -73 69 -38 66 18 C63 70 32 98 0 111 C-32 98 -63 70 -66 18 C-69 -38 -23 -73 0 -105 Z" fill="{CREAM}" stroke="{GREEN}" stroke-width="6"/>
  <path d="M-54 -30 Q0 0 54 -30 M-57 27 Q0 -3 57 27" fill="none" stroke="{RED}" stroke-width="9"/>
  <path d="M0 -84 V91" stroke="{GOLD}" stroke-width="4" stroke-dasharray="4 9"/>
  {sm_mark(0, 58, 0.66, GREEN, 0.48, 3.2)}
</g>'''


# Closed outer shapes used by the dedicated contour files.
snow1_contour = f'<polygon points="{points(150, 150, [126 if i % 2 == 0 else 66 for i in range(24)])}"/>'
snow2_contour = f'<polygon points="{points(150, 150, [124 if i % 2 == 0 else 72 for i in range(32)], -pi / 2 + pi / 16)}"/>'
snow3_contour = '<circle cx="150" cy="150" r="122"/>'
tree1_contour = '<path d="M150 24 L108 84 H128 L87 142 H116 L66 207 H136 V252 H164 V207 H234 L184 142 H213 L172 84 H192 Z"/>'
tree2_contour = '<path d="M150 22 Q142 57 103 88 H130 Q121 120 80 149 H115 Q107 179 59 211 H136 V253 H164 V211 H241 Q193 179 185 149 H220 Q179 120 170 88 H197 Q158 57 150 22 Z"/>'
tree3_contour = '<path d="M150 24 L101 90 H120 L78 160 H102 L56 232 H136 V257 H164 V232 H244 L198 160 H222 L180 90 H199 Z"/>'
round_contour = '<path d="M133 52 V38 Q133 24 150 24 Q167 24 167 38 V52 H174 V67 A91 91 0 1 1 126 67 V52 Z"/>'
long_contour = '<path d="M136 42 V29 Q136 16 150 16 Q164 16 164 29 V42 H172 V59 C230 59 241 100 224 142 C211 176 197 213 150 246 C103 213 89 176 76 142 C59 100 70 59 128 59 V42 Z"/>'
diamond_contour = '<path d="M150 20 Q135 20 135 35 V46 L75 130 L150 246 L225 130 L165 46 V35 Q165 20 150 20 Z"/>'
star_contour = f'<polygon points="{star_points(150, 157, 104, 47)}"/>'
bell_contour = '<path d="M130 59 Q150 32 170 59 C213 59 228 95 227 151 C226 187 242 205 250 214 H169 Q166 234 150 234 Q134 234 131 214 H50 C58 205 74 187 73 151 C72 95 87 59 130 59 Z"/>'
drop_contour = '<path d="M150 22 V46 C173 78 219 113 216 169 C213 221 182 249 150 262 C118 249 87 221 84 169 C81 113 127 78 150 46 V22 Z"/>'

snow1_body = f'''
<g id="PRINT">
  <polygon points="{points(150, 150, [123 if i % 2 == 0 else 64 for i in range(24)])}" fill="{CREAM}" stroke="{GREEN}" stroke-width="5" stroke-linejoin="round"/>
  {snowflake(150, 150, 97, GREEN, 5.5, 6)}
  <circle cx="150" cy="150" r="34" fill="{RED}" stroke="{GOLD}" stroke-width="4"/>
  {sm_mark(150, 150, 0.72, CREAM, 0.62, 3.2)}
</g>'''

snow2_body = f'''
<g id="PRINT">
  <polygon points="{points(150, 150, [121 if i % 2 == 0 else 70 for i in range(32)], -pi / 2 + pi / 16)}" fill="url(#greenGradient)" stroke="{LIGHT_GOLD}" stroke-width="5" stroke-linejoin="round"/>
  {snowflake(150, 150, 91, CREAM, 4.5, 8, 0.94, 22.5)}
  <circle cx="150" cy="150" r="31" fill="{GOLD}"/>
  {sm_mark(150, 150, 0.62, DARK_GREEN, 0.58, 3.2)}
</g>'''

snow3_body = f'''
<g id="PRINT">
  <circle cx="150" cy="150" r="119" fill="url(#redGradient)" stroke="{LIGHT_GOLD}" stroke-width="5"/>
  <circle cx="150" cy="150" r="100" fill="none" stroke="{CREAM}" stroke-width="3" stroke-dasharray="3 8"/>
  {snowflake(150, 150, 88, LIGHT_GOLD, 5, 6, 1, 30)}
  <circle cx="150" cy="150" r="38" fill="{CREAM}"/>
  {sm_mark(150, 150, 0.72, RED, 0.60, 3.2)}
</g>'''

ELEMENTS = [
    ("01-snowflake-classic", snow1_body, snow1_contour),
    ("02-snowflake-crystal", snow2_body, snow2_contour),
    ("03-snowflake-rosette", snow3_body, snow3_contour),
    ("04-tree-garland", f'<g id="PRINT">{tree_art(150, 145, 1.0, 1)}</g>', tree1_contour),
    ("05-tree-ribbon", f'<g id="PRINT">{tree_art(150, 145, 1.0, 2)}</g>', tree2_contour),
    ("06-tree-geometric", f'<g id="PRINT">{tree_art(150, 145, 1.0, 3)}</g>', tree3_contour),
    ("07-ornament-round", f'<g id="PRINT">{round_bauble(150, 155, 0.94)}</g>', round_contour),
    ("08-ornament-long", f'<g id="PRINT">{long_bauble(150, 155, 0.90)}</g>', long_contour),
    ("09-ornament-diamond", f'<g id="PRINT">{diamond_bauble(150, 158, 0.92)}</g>', diamond_contour),
    ("10-ornament-star", f'<g id="PRINT">{star_bauble(150, 156, 0.94)}</g>', star_contour),
    ("11-ornament-bell", f'<g id="PRINT">{bell(150, 154, 0.96)}</g>', bell_contour),
    ("12-ornament-drop", f'<g id="PRINT">{drop_bauble(150, 150, 0.92)}</g>', drop_contour),
]

for filename, body, contour in ELEMENTS:
    write_svg(PRINT_DIR / f"{filename}.svg", svg_document(body, title=filename))
    cut_body = f'<g id="CutContour" fill="none" stroke="{MAGENTA}" stroke-width="0.3" vector-effect="non-scaling-stroke" stroke-linejoin="round">{contour}</g>'
    write_svg(CUT_DIR / f"{filename}-cut.svg", svg_document(cut_body, defs="", title=f"{filename} cut contour"))

# Production sheets: 4 columns × 3 rows, no labels and no raster content.
sheet_print = ['<rect width="1200" height="900" fill="white"/>', '<g id="PRINT_SHEET">']
sheet_cut = ['<g id="CutContour" fill="none" stroke="#FF00FF" stroke-width="0.3" vector-effect="non-scaling-stroke" stroke-linejoin="round">']
for index, (_, body, contour) in enumerate(ELEMENTS):
    x = (index % 4) * 300
    y = (index // 4) * 300
    body_inner = body.replace('<g id="PRINT">', '<g>').replace('</g>', '</g>', 1)
    sheet_print.append(f'<g transform="translate({x} {y})">{body_inner}</g>')
    sheet_cut.append(f'<g transform="translate({x} {y})">{contour}</g>')
sheet_print.append('</g>')
sheet_cut.append('</g>')
write_svg(PRINT_DIR / "00-all-elements-print-sheet.svg", svg_document("".join(sheet_print), "0 0 1200 900", "1200mm", "900mm", title="SM New Year print sheet"))
write_svg(CUT_DIR / "00-all-elements-cut-sheet.svg", svg_document("".join(sheet_cut), "0 0 1200 900", "1200mm", "900mm", defs="", title="SM New Year cut contour sheet"))

# Every motif is repeated one tile in all directions. This guarantees that artwork
# crossing any edge continues at the opposite edge of the 600 × 600 mm tile.
OFFSETS = (-600, 0, 600)

# Seamless pattern 01: snowflakes on deep green.
p1 = [f'<rect width="600" height="600" fill="{DARK_GREEN}"/>', '<g id="PRINT">']
for x, y, r, c, sw, arms, rot in [
    (55, 70, 44, CREAM, 3.0, 6, 0), (310, 38, 62, GOLD, 3.5, 6, 30),
    (548, 112, 48, CREAM, 3.0, 8, 22.5), (160, 275, 76, LIGHT_GOLD, 4.5, 6, 0),
    (420, 300, 54, CREAM, 3.2, 6, 30), (20, 500, 62, GOLD, 3.6, 8, 22.5),
    (285, 530, 44, CREAM, 3.0, 6, 0), (565, 510, 76, LIGHT_GOLD, 4.4, 6, 30),
]:
    for dx in OFFSETS:
        for dy in OFFSETS:
            p1.append(snowflake(x + dx, y + dy, r, c, sw, arms, 0.92, rot))
for x, y in [(82, 420), (520, 420), (280, 175), (490, 205), (215, 95)]:
    for dx in OFFSETS:
        for dy in OFFSETS:
            p1.append(f'<circle cx="{x+dx}" cy="{y+dy}" r="4" fill="{RED}"/><circle cx="{x+15+dx}" cy="{y+10+dy}" r="2.5" fill="{GOLD}"/>')
p1.append(sm_mark(420, 300, 0.55, CREAM, 0.28, 3.0))
p1.append('</g>')
pattern1 = "".join(p1)

# Seamless pattern 02: rhythmic firs on cream.
p2 = [f'<rect width="600" height="600" fill="{CREAM}"/>', '<g id="PRINT">']
for x, y, scale, variant in [(585, 85, .55, 1), (190, 165, .72, 2), (420, 105, .58, 3), (70, 470, .68, 3), (330, 470, .78, 1), (590, 455, .66, 2)]:
    for dx in OFFSETS:
        for dy in OFFSETS:
            p2.append(tree_art(x + dx, y + dy, scale, variant))
for x, y, size, color in [(90, 60, 16, GOLD), (305, 75, 12, RED), (520, 255, 16, GREEN), (105, 275, 11, RED), (470, 545, 14, GOLD), (250, 330, 10, GREEN)]:
    for dx in OFFSETS:
        for dy in OFFSETS:
            p2.append(f'<polygon points="{star_points(x+dx, y+dy, size, size * .44)}" fill="{color}" opacity="0.86"/>')
p2.append('</g>')
pattern2 = "".join(p2)

# Seamless pattern 03: hanging ornaments on red.
p3 = [f'<rect width="600" height="600" fill="{DARK_RED}"/>', '<g id="PRINT">']
ornaments = [
    (60, 105, .42, 'round'), (250, 190, .40, 'long'), (445, 100, .40, 'diamond'),
    (585, 250, .38, 'drop'), (150, 430, .40, 'star'), (370, 470, .42, 'bell'),
    (560, 600, .40, 'round'),
]
ornament_art = {'round': round_bauble, 'long': long_bauble, 'diamond': diamond_bauble, 'star': star_bauble, 'bell': bell, 'drop': drop_bauble}
for x, y, scale, kind in ornaments:
    for dx in OFFSETS:
        for dy in OFFSETS:
            px, py = x + dx, y + dy
            top = py - 160 * scale
            p3.append(f'<path d="M{px} {top-140} V{top}" stroke="{LIGHT_GOLD}" stroke-width="2.5" opacity="0.75"/>')
            p3.append(ornament_art[kind](px, py, scale))
for x, y in [(150, 95), (345, 60), (510, 340), (80, 330), (285, 570)]:
    for dx in OFFSETS:
        for dy in OFFSETS:
            p3.append(f'<circle cx="{x+dx}" cy="{y+dy}" r="4" fill="{CREAM}" opacity="0.65"/>')
p3.append('</g>')
pattern3 = "".join(p3)

# Seamless pattern 04: transparent window-film linework.
p4 = ['<g id="PRINT">']
for x, y, r, rot in [(590, 60, 60, 0), (210, 80, 42, 30), (430, 220, 65, 0), (65, 360, 48, 30), (275, 475, 72, 0), (10, 520, 58, 30)]:
    for dx in OFFSETS:
        for dy in OFFSETS:
            p4.append(snowflake(x + dx, y + dy, r, WHITE, 5.0, 6, 0.92, rot))
for x, y, s, variant in [(130, 185, .35, 1), (545, 390, .38, 3), (390, 0, .34, 2)]:
    for dx in OFFSETS:
        for dy in OFFSETS:
            p4.append(tree_art(x + dx, y + dy, s, variant))
for x, y, s, art in [(320, 210, .30, round_bauble), (105, 575, .28, drop_bauble), (500, 85, .26, star_bauble)]:
    for dx in OFFSETS:
        for dy in OFFSETS:
            p4.append(art(x + dx, y + dy, s))
p4.append(sm_mark(275, 475, .60, GOLD, .30, 3.0))
p4.append('</g>')
pattern4 = "".join(p4)

PATTERNS = [
    ("01-snowfall-deep-green", pattern1, "Snowfall / deep green"),
    ("02-fir-rhythm-cream", pattern2, "Fir rhythm / cream"),
    ("03-hanging-ornaments-red", pattern3, "Hanging ornaments / red"),
    ("04-window-film-transparent", pattern4, "Window film / transparent"),
]
for filename, body, title in PATTERNS:
    write_svg(PATTERN_DIR / f"{filename}.svg", svg_document(body, "0 0 600 600", "600mm", "600mm", title=title))

# Visual approval boards. These are previews only; production graphics above contain no text.
preview_elements = [f'<rect width="1200" height="675" fill="{CHARCOAL}"/>',
                    f'<rect x="24" y="24" width="1152" height="627" rx="26" fill="{CREAM}"/>',
                    f'<text x="64" y="78" font-family="Montserrat,sans-serif" font-size="29" font-weight="700" fill="{DARK_GREEN}">SM · НОВОГОДНИЕ ЭЛЕМЕНТЫ</text>',
                    f'<text x="64" y="107" font-family="Montserrat,sans-serif" font-size="16" fill="{GREEN}">СНЕЖИНКИ · ЁЛКИ · ИГРУШКИ / 12 ВЕКТОРНЫХ ФОРМ</text>']
for index, (_, body, _) in enumerate(ELEMENTS):
    col, row = index % 6, index // 6
    cell_x, cell_y = 49 + col * 184, 132 + row * 245
    preview_elements.append(f'<rect x="{cell_x}" y="{cell_y}" width="164" height="218" rx="16" fill="{WHITE}" stroke="{GOLD}" stroke-width="1.5"/>')
    preview_elements.append(f'<g transform="translate({cell_x + 5} {cell_y + 8}) scale(.515)">{body}</g>')
    preview_elements.append(f'<circle cx="{cell_x+21}" cy="{cell_y+197}" r="13" fill="{DARK_GREEN}"/><text x="{cell_x+21}" y="{cell_y+202}" text-anchor="middle" font-family="Montserrat,sans-serif" font-size="13" font-weight="700" fill="{CREAM}">{index+1:02d}</text>')
preview_elements.append(f'<text x="64" y="625" font-family="Montserrat,sans-serif" font-size="14" fill="{GREEN}">КЛАССИЧЕСКАЯ ПАЛИТРА · ЛОГОТИП SM ИНТЕГРИРОВАН ДЕЛИКАТНО</text>')
write_svg(PREVIEW_DIR / "01-elements-board.svg", svg_document("".join(preview_elements), "0 0 1200 675", "1200px", "675px", title="SM New Year elements preview"))

preview_patterns = [f'<rect width="1200" height="675" fill="{CHARCOAL}"/>',
                    f'<text x="54" y="58" font-family="Montserrat,sans-serif" font-size="28" font-weight="700" fill="{CREAM}">SM · БЕСШОВНЫЕ НОВОГОДНИЕ УЗОРЫ</text>']
pattern_bodies = [pattern1, pattern2, pattern3, pattern4]
labels = ["01  СНЕГОПАД", "02  РИТМ ЕЛЕЙ", "03  ИГРУШКИ", "04  ПРОЗРАЧНАЯ ПЛЁНКА"]
for index, body in enumerate(pattern_bodies):
    col, row = index % 2, index // 2
    x, y = 54 + col * 573, 82 + row * 282
    preview_patterns.append(f'<defs><clipPath id="clip{index}"><rect x="{x}" y="{y}" width="519" height="224" rx="18"/></clipPath></defs>')
    if index == 3:
        preview_patterns.append(f'<rect x="{x}" y="{y}" width="519" height="224" rx="18" fill="{GREEN}"/>')
    for repeat in range(3):
        tile_x = x + repeat * 224
        preview_patterns.append(f'<g clip-path="url(#clip{index})"><g transform="translate({tile_x} {y}) scale(.373333)">{body}</g></g>')
    preview_patterns.append(f'<rect x="{x}" y="{y}" width="519" height="224" rx="18" fill="none" stroke="{GOLD}" stroke-width="2"/>')
    preview_patterns.append(f'<text x="{x+16}" y="{y+251}" font-family="Montserrat,sans-serif" font-size="17" font-weight="700" fill="{CREAM}">{labels[index]}</text>')
write_svg(PREVIEW_DIR / "02-patterns-board.svg", svg_document("".join(preview_patterns), "0 0 1200 675", "1200px", "675px", title="SM New Year seamless patterns preview"))

preview_cuts = [f'<rect width="1200" height="675" fill="{CREAM}"/>',
                f'<text x="54" y="58" font-family="Montserrat,sans-serif" font-size="28" font-weight="700" fill="{DARK_GREEN}">ОТДЕЛЬНЫЕ ВЕКТОРНЫЕ КОНТУРЫ РЕЗА</text>',
                f'<text x="54" y="84" font-family="Montserrat,sans-serif" font-size="15" fill="{GREEN}">ID СЛОЯ: CutContour · ЛИНИЯ: 100% MAGENTA · ТОЛЩИНА: 0,3 ММ</text>']
for index, (_, _, contour) in enumerate(ELEMENTS):
    col, row = index % 6, index // 6
    x, y = 47 + col * 185, 113 + row * 250
    preview_cuts.append(f'<rect x="{x}" y="{y}" width="166" height="224" rx="14" fill="white" stroke="#E7DDCA"/>')
    preview_cuts.append(f'<g transform="translate({x+5} {y+15}) scale(.52)" fill="none" stroke="{MAGENTA}" stroke-width="2.2" stroke-linejoin="round">{contour}</g>')
    preview_cuts.append(f'<text x="{x+83}" y="{y+211}" text-anchor="middle" font-family="Montserrat,sans-serif" font-size="13" font-weight="700" fill="{DARK_GREEN}">{index+1:02d}</text>')
preview_cuts.append(f'<text x="54" y="637" font-family="Montserrat,sans-serif" font-size="14" fill="{GREEN}">ПЕЧАТНЫЕ МАКЕТЫ И КОНТУРЫ ХРАНЯТСЯ В РАЗНЫХ SVG-ФАЙЛАХ</text>')
write_svg(PREVIEW_DIR / "03-cut-contours-board.svg", svg_document("".join(preview_cuts), "0 0 1200 675", "1200px", "675px", title="SM New Year cut contours preview"))

print(f"Created {len(ELEMENTS)} print elements, {len(ELEMENTS)} contours, {len(PATTERNS)} seamless patterns and 3 preview boards.")
