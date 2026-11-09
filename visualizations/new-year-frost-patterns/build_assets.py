#!/usr/bin/env python3
"""Build premium blue-and-white frost SVG assets for print and CNC routing."""
from __future__ import annotations

from pathlib import Path
from math import cos, sin, pi
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
ELEMENT_DIR = ROOT / "elements"
PATTERN_DIR = ROOT / "patterns"
PREVIEW_DIR = ROOT / "previews"
for directory in (ELEMENT_DIR, PATTERN_DIR, PREVIEW_DIR):
    directory.mkdir(parents=True, exist_ok=True)

MIDNIGHT = "#071B3A"
NAVY = "#0B3566"
COBALT = "#1769AA"
BLUE = "#2E91D1"
ICE = "#8EDCF8"
PALE = "#DDF6FF"
FROST = "#EAFBFF"
WHITE = "#FFFFFF"
SILVER = "#B9CFDE"
STEEL = "#6D8FA8"
MAGENTA = "#FF00FF"

DEFS = f"""
<defs>
  <linearGradient id="blueGradient" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="{BLUE}"/><stop offset="0.52" stop-color="{COBALT}"/><stop offset="1" stop-color="{NAVY}"/>
  </linearGradient>
  <linearGradient id="iceGradient" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="{WHITE}"/><stop offset="0.48" stop-color="{PALE}"/><stop offset="1" stop-color="{ICE}"/>
  </linearGradient>
  <linearGradient id="silverGradient" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="{WHITE}"/><stop offset="0.45" stop-color="{SILVER}"/><stop offset="1" stop-color="{STEEL}"/>
  </linearGradient>
  <radialGradient id="glassGradient" cx="35%" cy="28%" r="78%">
    <stop offset="0" stop-color="{WHITE}"/><stop offset="0.28" stop-color="{ICE}"/><stop offset="0.72" stop-color="{BLUE}"/><stop offset="1" stop-color="{NAVY}"/>
  </radialGradient>
</defs>
"""


def clean(content: str) -> str:
    return "\n".join(line.rstrip() for line in content.splitlines()) + "\n"


def svg_document(body: str, view_box: str = "0 0 300 300", width: str = "300mm", height: str = "300mm", defs: str = DEFS, title: str = "") -> str:
    title_node = f"<title>{title}</title>" if title else ""
    return clean(f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" width="{width}" height="{height}" viewBox="{view_box}">
{title_node}
{defs}
{body}
</svg>''')


def print_layer(body: str, layer_id: str = "PRINT") -> str:
    return f'<g inkscape:groupmode="layer" inkscape:label="{layer_id}" id="{layer_id}">{body}</g>'


def cut_layer(contour: str) -> str:
    return f'<g inkscape:groupmode="layer" inkscape:label="CutContour" id="CutContour" fill="none" stroke="{MAGENTA}" stroke-width="0.3" stroke-linejoin="round" stroke-linecap="round" vector-effect="non-scaling-stroke" data-spot-color="CutContour">{contour}</g>'


def layered_svg(body: str, contour: str, title: str) -> str:
    return svg_document(print_layer(body) + cut_layer(contour), title=title)


def write_svg(path: Path, content: str) -> None:
    path.write_text(clean(content), encoding="utf-8")
    ET.parse(path)


def points(cx: float, cy: float, radii: list[float], start: float = -pi / 2) -> str:
    out = []
    for index, radius in enumerate(radii):
        angle = start + 2 * pi * index / len(radii)
        out.append(f"{cx + radius * cos(angle):.2f},{cy + radius * sin(angle):.2f}")
    return " ".join(out)


def star_points(cx: float, cy: float, outer: float, inner: float, count: int = 5, start: float = -pi / 2) -> str:
    return points(cx, cy, [outer if i % 2 == 0 else inner for i in range(count * 2)], start)


def snowflake(cx: float, cy: float, radius: float, color: str, stroke: float = 4, arms: int = 6, rotation: float = 0, opacity: float = 1.0) -> str:
    arm = f'''
<g fill="none" stroke="{color}" stroke-width="{stroke}" stroke-linecap="round" stroke-linejoin="round" opacity="{opacity}">
  <path d="M0 0 V-{radius}"/>
  <path d="M0 -{radius*.43:.2f} L-{radius*.20:.2f} -{radius*.62:.2f} M0 -{radius*.43:.2f} L{radius*.20:.2f} -{radius*.62:.2f}"/>
  <path d="M0 -{radius*.68:.2f} L-{radius*.17:.2f} -{radius*.83:.2f} M0 -{radius*.68:.2f} L{radius*.17:.2f} -{radius*.83:.2f}"/>
  <path d="M0 -{radius*.87:.2f} L-{radius*.10:.2f} -{radius*.95:.2f} M0 -{radius*.87:.2f} L{radius*.10:.2f} -{radius*.95:.2f}"/>
</g>'''
    arms_svg = "".join(f'<g transform="rotate({rotation + i * 360 / arms})">{arm}</g>' for i in range(arms))
    return f'<g transform="translate({cx} {cy})">{arms_svg}</g>'


def facet_lines(cx: float, cy: float, radius: float, count: int = 8, color: str = WHITE, opacity: float = .55) -> str:
    return "".join(
        f'<path d="M{cx} {cy} L{cx + radius*cos(-pi/2 + i*2*pi/count):.2f} {cy + radius*sin(-pi/2 + i*2*pi/count):.2f}" stroke="{color}" stroke-width="2.5" opacity="{opacity}"/>'
        for i in range(count)
    )


def tree_body(cx: float, cy: float, scale: float = 1.0, variant: int = 1) -> str:
    if variant == 1:
        return f'''
<g transform="translate({cx} {cy}) scale({scale})">
  <path d="M0 -112 L-42 -52 H-22 L-69 9 H-38 L-96 80 H96 L38 9 H69 L22 -52 H42 Z" fill="url(#blueGradient)" stroke="{SILVER}" stroke-width="5" stroke-linejoin="round"/>
  <path d="M0 -101 L-28 -52 H0 Z M0 -44 L-45 8 H0 Z M0 17 L-63 72 H0 Z" fill="{ICE}" opacity=".34"/>
  <path d="M-55 -14 Q0 13 55 -14 M-72 38 Q0 68 72 38" fill="none" stroke="{WHITE}" stroke-width="4" opacity=".86"/>
  <circle cx="-30" cy="-30" r="5" fill="{WHITE}"/><circle cx="29" cy="8" r="5" fill="{ICE}"/><circle cx="-42" cy="42" r="6" fill="{PALE}"/><circle cx="46" cy="50" r="5" fill="{WHITE}"/>
  <polygon points="{star_points(0,-121,13,6,5)}" fill="url(#silverGradient)"/>
  <rect x="-14" y="80" width="28" height="25" rx="3" fill="{MIDNIGHT}"/>
</g>'''
    if variant == 2:
        return f'''
<g transform="translate({cx} {cy}) scale({scale})">
  <path d="M0 -114 Q-10 -78 -43 -49 H-22 Q-30 -14 -70 16 H-38 Q-47 50 -91 82 H91 Q47 50 38 16 H70 Q30 -14 22 -49 H43 Q10 -78 0 -114 Z" fill="url(#iceGradient)" stroke="{COBALT}" stroke-width="5"/>
  <path d="M-38 -42 Q0 -20 38 -42 M-62 19 Q0 47 62 19 M-75 59 Q0 82 75 59" fill="none" stroke="{NAVY}" stroke-width="3.5" stroke-dasharray="2 8" stroke-linecap="round"/>
  <path d="M0 -96 V68" stroke="{WHITE}" stroke-width="3" opacity=".55"/>
  <polygon points="{star_points(0,-122,12,5.5,8)}" fill="{SILVER}"/>
  <rect x="-13" y="82" width="26" height="23" rx="3" fill="{COBALT}"/>
</g>'''
    return f'''
<g transform="translate({cx} {cy}) scale({scale})">
  <polygon points="0,-111 -50,-42 50,-42" fill="{PALE}" stroke="{NAVY}" stroke-width="4"/>
  <polygon points="0,-70 -73,11 73,11" fill="{ICE}" stroke="{COBALT}" stroke-width="4"/>
  <polygon points="0,-23 -96,82 96,82" fill="{NAVY}" stroke="{SILVER}" stroke-width="4"/>
  <path d="M-38 -40 L0 -70 L38 -40 M-55 9 L0 -23 L55 9 M-74 76 L0 16 L74 76" fill="none" stroke="{WHITE}" stroke-width="4" opacity=".78"/>
  <circle cx="0" cy="-57" r="5" fill="{WHITE}"/><circle cx="-34" cy="-1" r="6" fill="{WHITE}"/><circle cx="39" cy="44" r="6" fill="{ICE}"/>
  <polygon points="{star_points(0,-121,12,5.5,6)}" fill="{WHITE}" stroke="{SILVER}" stroke-width="2"/>
  <rect x="-14" y="82" width="28" height="25" rx="3" fill="{MIDNIGHT}"/>
</g>'''


def round_ornament(cx: float, cy: float, scale: float = 1.0) -> str:
    return f'''
<g transform="translate({cx} {cy}) scale({scale})">
  <path d="M-16 -101 V-114 Q-16 -128 0 -128 Q16 -128 16 -114 V-101" fill="none" stroke="{SILVER}" stroke-width="6"/>
  <rect x="-24" y="-104" width="48" height="21" rx="5" fill="url(#silverGradient)"/>
  <circle cx="0" cy="0" r="88" fill="url(#glassGradient)" stroke="{WHITE}" stroke-width="5"/>
  <path d="M-70 -46 L0 0 L70 -46 M-82 12 L0 0 L82 12 M-59 62 L0 0 L59 62" fill="none" stroke="{PALE}" stroke-width="4" opacity=".66"/>
  <circle cx="-37" cy="-46" r="14" fill="{WHITE}" opacity=".22"/>
  <circle cx="0" cy="0" r="26" fill="none" stroke="{WHITE}" stroke-width="3" opacity=".65"/>
</g>'''


def icicle_ornament(cx: float, cy: float, scale: float = 1.0) -> str:
    return f'''
<g transform="translate({cx} {cy}) scale({scale})">
  <path d="M-14 -111 V-124 Q-14 -137 0 -137 Q14 -137 14 -124 V-111" fill="none" stroke="{SILVER}" stroke-width="6"/>
  <rect x="-22" y="-113" width="44" height="20" rx="5" fill="url(#silverGradient)"/>
  <path d="M0 -95 C57 -95 68 -55 50 -12 C37 22 25 62 0 102 C-25 62 -37 22 -50 -12 C-68 -55 -57 -95 0 -95 Z" fill="url(#iceGradient)" stroke="{NAVY}" stroke-width="5"/>
  <path d="M0 -86 V87 M-43 -35 L0 -10 L43 -35 M-34 20 L0 4 L34 20" fill="none" stroke="{COBALT}" stroke-width="4" opacity=".72"/>
  <path d="M-22 -77 Q0 -91 22 -77" fill="none" stroke="{WHITE}" stroke-width="5" opacity=".78"/>
</g>'''


def diamond_ornament(cx: float, cy: float, scale: float = 1.0) -> str:
    return f'''
<g transform="translate({cx} {cy}) scale({scale})">
  <path d="M0 -129 Q-15 -129 -15 -114 V-102" fill="none" stroke="{SILVER}" stroke-width="6"/>
  <path d="M0 -104 L78 -20 L0 99 L-78 -20 Z" fill="url(#blueGradient)" stroke="{WHITE}" stroke-width="5"/>
  <path d="M0 -91 L0 82 M-66 -20 H66 M0 -91 L-66 -20 L0 82 L66 -20 Z" fill="none" stroke="{ICE}" stroke-width="4" opacity=".75"/>
  <path d="M0 -91 L-27 -20 L0 82 L27 -20 Z" fill="{WHITE}" opacity=".18"/>
</g>'''


def star_ornament(cx: float, cy: float, scale: float = 1.0) -> str:
    return f'''
<g transform="translate({cx} {cy}) scale({scale})">
  <polygon points="{star_points(0,1,102,47,8)}" fill="url(#iceGradient)" stroke="{NAVY}" stroke-width="6" stroke-linejoin="round"/>
  <polygon points="{star_points(0,1,68,31,8)}" fill="url(#blueGradient)" stroke="{WHITE}" stroke-width="3"/>
  {facet_lines(0,1,62,8,PALE,.64)}
  <circle cx="0" cy="1" r="18" fill="{WHITE}" opacity=".72"/>
</g>'''


def bell_ornament(cx: float, cy: float, scale: float = 1.0) -> str:
    return f'''
<g transform="translate({cx} {cy}) scale({scale})">
  <path d="M-20 -91 Q0 -119 20 -91" fill="none" stroke="{SILVER}" stroke-width="8"/>
  <path d="M0 -89 C-44 -89 -59 -52 -58 4 C-57 39 -73 58 -82 67 H82 C73 58 57 39 58 4 C59 -52 44 -89 0 -89 Z" fill="url(#blueGradient)" stroke="{WHITE}" stroke-width="5"/>
  <path d="M-64 29 Q0 51 64 29" fill="none" stroke="{ICE}" stroke-width="7"/>
  <path d="M-40 -55 L0 4 L40 -55 M0 -80 V49" fill="none" stroke="{WHITE}" stroke-width="3" opacity=".48"/>
  <circle cx="0" cy="76" r="16" fill="url(#silverGradient)"/>
</g>'''


def snow_globe(cx: float, cy: float, scale: float = 1.0) -> str:
    return f'''
<g transform="translate({cx} {cy}) scale({scale})">
  <circle cx="0" cy="-10" r="84" fill="url(#glassGradient)" stroke="{WHITE}" stroke-width="5"/>
  <path d="M-66 57 H66 L81 96 H-81 Z" fill="url(#silverGradient)" stroke="{NAVY}" stroke-width="5" stroke-linejoin="round"/>
  <path d="M0 -61 L-22 -28 H-10 L-35 5 H-17 L-48 42 H48 L17 5 H35 L10 -28 H22 Z" fill="{MIDNIGHT}" stroke="{PALE}" stroke-width="3"/>
  <circle cx="-48" cy="-42" r="5" fill="{WHITE}"/><circle cx="43" cy="-28" r="4" fill="{WHITE}"/><circle cx="-25" cy="15" r="4" fill="{WHITE}"/><circle cx="34" cy="24" r="5" fill="{WHITE}"/>
  <path d="M-60 70 H60" stroke="{WHITE}" stroke-width="4" opacity=".72"/>
</g>'''


# Closed toolpaths for the 12 elements.
snow1_cut = f'<polygon points="{points(150,150,[126 if i%2==0 else 65 for i in range(24)])}"/>'
snow2_cut = '<circle cx="150" cy="150" r="123"/>'
snow3_cut = f'<polygon points="{points(150,150,[125 if i%2==0 else 67 for i in range(32)],-pi/2+pi/16)}"/>'
tree1_cut = '<path d="M150 22 L108 82 H128 L81 143 H112 L54 214 H136 V255 H164 V214 H246 L188 143 H219 L172 82 H192 Z"/>'
tree2_cut = '<path d="M150 20 Q140 56 107 85 H128 Q120 120 80 150 H112 Q103 184 59 216 H136 V255 H164 V216 H241 Q197 184 188 150 H220 Q180 120 172 85 H193 Q160 56 150 20 Z"/>'
tree3_cut = '<path d="M150 20 L100 89 H119 L77 160 H101 L54 232 H136 V257 H164 V232 H246 L199 160 H223 L181 89 H200 Z"/>'
round_cut = '<path d="M134 51 V37 Q134 23 150 23 Q166 23 166 37 V51 H174 V67 A92 92 0 1 1 126 67 V51 Z"/>'
icicle_cut = '<path d="M136 42 V29 Q136 16 150 16 Q164 16 164 29 V42 H172 V60 C229 60 240 100 222 143 C209 177 197 217 150 257 C103 217 91 177 78 143 C60 100 71 60 128 60 V42 Z"/>'
diamond_cut = '<path d="M150 21 Q135 21 135 36 V48 L72 130 L150 249 L228 130 L165 48 V36 Q165 21 150 21 Z"/>'
star_cut = f'<polygon points="{star_points(150,151,106,50,8)}"/>'
bell_cut = '<path d="M130 60 Q150 32 170 60 C214 60 229 97 228 153 C227 188 243 207 252 216 H169 Q166 236 150 236 Q134 236 131 216 H48 C57 207 73 188 72 153 C71 97 86 60 130 60 Z"/>'
globe_cut = '<path d="M150 54 A88 88 0 0 1 218 198 L231 246 H69 L82 198 A88 88 0 0 1 150 54 Z"/>'

snow1_body = f'''
<polygon points="{points(150,150,[123 if i%2==0 else 63 for i in range(24)])}" fill="url(#blueGradient)" stroke="{WHITE}" stroke-width="5" stroke-linejoin="round"/>
{snowflake(150,150,96,PALE,5.2,6,0,.95)}
<polygon points="{star_points(150,150,51,26,6)}" fill="url(#iceGradient)" stroke="{SILVER}" stroke-width="3"/>
<circle cx="150" cy="150" r="17" fill="{NAVY}"/><circle cx="150" cy="150" r="7" fill="{WHITE}"/>'''

snow2_body = f'''
<circle cx="150" cy="150" r="120" fill="url(#iceGradient)" stroke="{NAVY}" stroke-width="5"/>
<circle cx="150" cy="150" r="100" fill="none" stroke="{COBALT}" stroke-width="3" stroke-dasharray="2 8"/>
{snowflake(150,150,88,NAVY,4.4,8,22.5,.92)}
<circle cx="150" cy="150" r="36" fill="{WHITE}" stroke="{SILVER}" stroke-width="3"/>
<polygon points="{star_points(150,150,26,12,8)}" fill="{COBALT}"/>'''

snow3_body = f'''
<polygon points="{points(150,150,[122 if i%2==0 else 65 for i in range(32)],-pi/2+pi/16)}" fill="url(#silverGradient)" stroke="{MIDNIGHT}" stroke-width="5" stroke-linejoin="round"/>
<polygon points="{points(150,150,[94 if i%2==0 else 48 for i in range(16)],-pi/2)}" fill="{NAVY}" stroke="{WHITE}" stroke-width="4"/>
{facet_lines(150,150,88,8,ICE,.78)}
<circle cx="150" cy="150" r="30" fill="url(#glassGradient)" stroke="{WHITE}" stroke-width="3"/>'''

ELEMENTS = [
    ("01-snowflake-crystal-crown", snow1_body, snow1_cut),
    ("02-snowflake-frost-lace", snow2_body, snow2_cut),
    ("03-snowflake-arctic-compass", snow3_body, snow3_cut),
    ("04-tree-faceted-ice", tree_body(150,145,1,1), tree1_cut),
    ("05-tree-frost-lines", tree_body(150,145,1,2), tree2_cut),
    ("06-tree-snow-facets", tree_body(150,145,1,3), tree3_cut),
    ("07-ornament-glass-sphere", round_ornament(150,156,.94), round_cut),
    ("08-ornament-ice-drop", icicle_ornament(150,156,.91), icicle_cut),
    ("09-ornament-crystal-diamond", diamond_ornament(150,158,.92), diamond_cut),
    ("10-ornament-eight-point-star", star_ornament(150,151,.94), star_cut),
    ("11-ornament-winter-bell", bell_ornament(150,154,.96), bell_cut),
    ("12-ornament-snow-globe", snow_globe(150,148,.92), globe_cut),
]

for filename, body, contour in ELEMENTS:
    write_svg(ELEMENT_DIR / f"{filename}.svg", layered_svg(body, contour, filename))

# Combined 4 × 3 production sheet with PRINT and CutContour layers.
sheet_print, sheet_cut = [], []
for index, (_, body, contour) in enumerate(ELEMENTS):
    x, y = (index % 4) * 300, (index // 4) * 300
    sheet_print.append(f'<g transform="translate({x} {y})">{body}</g>')
    sheet_cut.append(f'<g transform="translate({x} {y})">{contour}</g>')
sheet = print_layer("".join(sheet_print)) + cut_layer("".join(sheet_cut))
write_svg(ELEMENT_DIR / "00-all-elements-layered-sheet.svg", svg_document(sheet,"0 0 1200 900","1200mm","900mm",title="Frost collection layered production sheet"))

# Seamless patterns. Motifs are copied by one tile in all directions.
OFFSETS = (-600,0,600)

p1 = [f'<rect width="600" height="600" fill="{MIDNIGHT}"/>']
for x,y,r,c,arms,rot in [(70,70,48,WHITE,6,0),(305,40,66,ICE,6,30),(535,120,50,PALE,8,22.5),(165,285,80,SILVER,6,0),(425,305,58,WHITE,8,22.5),(30,515,68,ICE,6,30),(300,535,47,WHITE,6,0),(565,505,78,SILVER,8,22.5)]:
    for dx in OFFSETS:
        for dy in OFFSETS:
            p1.append(snowflake(x+dx,y+dy,r,c,3.8 if r<60 else 4.8,arms,rot,.92))
pattern1 = "".join(p1)

p2 = [f'<rect width="600" height="600" fill="{FROST}"/>']
for x,y,s,v in [(585,92,.56,1),(190,170,.72,2),(425,115,.58,3),(75,470,.67,3),(335,475,.78,1),(590,455,.65,2)]:
    for dx in OFFSETS:
        for dy in OFFSETS:
            p2.append(tree_body(x+dx,y+dy,s,v))
for x,y,size,color in [(90,62,15,COBALT),(310,78,12,SILVER),(520,270,16,NAVY),(110,290,10,BLUE),(475,545,14,COBALT),(260,335,10,SILVER)]:
    for dx in OFFSETS:
        for dy in OFFSETS:
            p2.append(f'<polygon points="{star_points(x+dx,y+dy,size,size*.45,8)}" fill="{color}" opacity=".82"/>')
pattern2 = "".join(p2)

p3 = [f'<rect width="600" height="600" fill="{NAVY}"/>']
arts = {"round":round_ornament,"drop":icicle_ornament,"diamond":diamond_ornament,"star":star_ornament,"bell":bell_ornament}
for x,y,s,kind in [(70,110,.40,"round"),(250,195,.38,"drop"),(445,105,.40,"diamond"),(585,260,.36,"drop"),(155,435,.39,"star"),(375,475,.40,"bell"),(560,600,.38,"round")]:
    for dx in OFFSETS:
        for dy in OFFSETS:
            px,py=x+dx,y+dy
            p3.append(f'<path d="M{px} {py-210*s-110} V{py-105*s}" stroke="{SILVER}" stroke-width="2.5" opacity=".72"/>')
            p3.append(arts[kind](px,py,s))
pattern3 = "".join(p3)

p4 = []
for x,y,r,rot in [(590,65,60,0),(215,85,43,30),(435,225,66,0),(70,365,49,30),(280,480,74,0),(12,525,59,30)]:
    for dx in OFFSETS:
        for dy in OFFSETS:
            p4.append(snowflake(x+dx,y+dy,r,WHITE,5,6,rot,.88))
for x,y,s,v in [(135,190,.34,1),(550,395,.37,3),(395,0,.33,2)]:
    for dx in OFFSETS:
        for dy in OFFSETS:
            p4.append(tree_body(x+dx,y+dy,s,v))
for x,y,s,art in [(325,215,.28,round_ornament),(110,580,.27,icicle_ornament),(505,90,.25,star_ornament)]:
    for dx in OFFSETS:
        for dy in OFFSETS:
            p4.append(art(x+dx,y+dy,s))
pattern4 = "".join(p4)

PATTERNS = [
    ("01-midnight-crystal-snowfall",pattern1,"Midnight crystal snowfall"),
    ("02-arctic-fir-rhythm",pattern2,"Arctic fir rhythm"),
    ("03-hanging-glass-ornaments",pattern3,"Hanging glass ornaments"),
    ("04-transparent-frost-window",pattern4,"Transparent frost window"),
]
for filename, body, title in PATTERNS:
    square_cut = '<rect x="0.15" y="0.15" width="599.7" height="599.7"/>'
    content = print_layer(body) + cut_layer(square_cut)
    write_svg(PATTERN_DIR/f"{filename}.svg",svg_document(content,"0 0 600 600","600mm","600mm",title=title))

# Preview boards (not production files).
preview1 = [f'<rect width="1200" height="675" fill="{MIDNIGHT}"/>',f'<rect x="24" y="24" width="1152" height="627" rx="26" fill="{FROST}"/>',f'<text x="64" y="78" font-family="Montserrat,sans-serif" font-size="29" font-weight="700" fill="{MIDNIGHT}">МОРОЗНАЯ КОЛЛЕКЦИЯ · 12 ФОРМ</text>',f'<text x="64" y="107" font-family="Montserrat,sans-serif" font-size="16" fill="{NAVY}">ПРЕМИАЛЬНЫЙ ИНЕЙ · ГОЛУБОЙ · СИНИЙ · БЕЛЫЙ · БЕЗ ЛОГОТИПА</text>']
for index,(_,body,_) in enumerate(ELEMENTS):
    col,row=index%6,index//6
    x,y=49+col*184,132+row*245
    preview1.append(f'<rect x="{x}" y="{y}" width="164" height="218" rx="16" fill="{WHITE}" stroke="{ICE}" stroke-width="2"/>')
    preview1.append(f'<g transform="translate({x+5} {y+8}) scale(.515)">{body}</g>')
    preview1.append(f'<circle cx="{x+21}" cy="{y+197}" r="13" fill="{NAVY}"/><text x="{x+21}" y="{y+202}" text-anchor="middle" font-family="Montserrat,sans-serif" font-size="13" font-weight="700" fill="{WHITE}">{index+1:02d}</text>')
preview1.append(f'<text x="64" y="625" font-family="Montserrat,sans-serif" font-size="14" fill="{NAVY}">В КАЖДОМ SVG: СЛОЙ PRINT + ТЕХНИЧЕСКИЙ СЛОЙ CutContour</text>')
write_svg(PREVIEW_DIR/"01-elements-board.svg",svg_document("".join(preview1),"0 0 1200 675","1200px","675px",title="Frost elements preview"))

preview2=[f'<rect width="1200" height="675" fill="{MIDNIGHT}"/>',f'<text x="54" y="58" font-family="Montserrat,sans-serif" font-size="28" font-weight="700" fill="{WHITE}">БЕСШОВНЫЕ МОРОЗНЫЕ РАППОРТЫ</text>']
labels=["01  КРИСТАЛЬНЫЙ СНЕГОПАД","02  АРКТИЧЕСКИЙ ЛЕС","03  СТЕКЛЯННЫЕ ИГРУШКИ","04  ПРОЗРАЧНЫЙ ИНЕЙ"]
for index,body in enumerate([pattern1,pattern2,pattern3,pattern4]):
    col,row=index%2,index//2
    x,y=54+col*573,82+row*282
    preview2.append(f'<defs><clipPath id="clip{index}"><rect x="{x}" y="{y}" width="519" height="224" rx="18"/></clipPath></defs>')
    if index==3:
        preview2.append(f'<rect x="{x}" y="{y}" width="519" height="224" rx="18" fill="{COBALT}"/>')
    for repeat in range(3):
        tile_x=x+repeat*224
        preview2.append(f'<g clip-path="url(#clip{index})"><g transform="translate({tile_x} {y}) scale(.373333)">{body}</g></g>')
    preview2.append(f'<rect x="{x}" y="{y}" width="519" height="224" rx="18" fill="none" stroke="{ICE}" stroke-width="2"/>')
    preview2.append(f'<text x="{x+16}" y="{y+251}" font-family="Montserrat,sans-serif" font-size="17" font-weight="700" fill="{WHITE}">{labels[index]}</text>')
write_svg(PREVIEW_DIR/"02-patterns-board.svg",svg_document("".join(preview2),"0 0 1200 675","1200px","675px",title="Frost patterns preview"))

preview3=[f'<rect width="1200" height="675" fill="{FROST}"/>',f'<text x="54" y="58" font-family="Montserrat,sans-serif" font-size="28" font-weight="700" fill="{MIDNIGHT}">СЛОЙ ФРЕЗЕРОВКИ CutContour</text>',f'<text x="54" y="84" font-family="Montserrat,sans-serif" font-size="15" fill="{NAVY}">ЗАМКНУТЫЕ КОНТУРЫ · 100% MAGENTA · 0,3 ММ · ВНУТРИ КАЖДОГО SVG</text>']
for index,(_,_,contour) in enumerate(ELEMENTS):
    col,row=index%6,index//6
    x,y=47+col*185,113+row*250
    preview3.append(f'<rect x="{x}" y="{y}" width="166" height="224" rx="14" fill="{WHITE}" stroke="{SILVER}"/>')
    preview3.append(f'<g transform="translate({x+5} {y+15}) scale(.52)" fill="none" stroke="{MAGENTA}" stroke-width="2.2" stroke-linejoin="round">{contour}</g>')
    preview3.append(f'<text x="{x+83}" y="{y+211}" text-anchor="middle" font-family="Montserrat,sans-serif" font-size="13" font-weight="700" fill="{MIDNIGHT}">{index+1:02d}</text>')
preview3.append(f'<text x="54" y="637" font-family="Montserrat,sans-serif" font-size="14" fill="{NAVY}">ПЕРЕД ПЕЧАТЬЮ СЛОЮ НУЖНО НАЗНАЧИТЬ ПЛАШЕЧНЫЙ ЦВЕТ CutContour В RIP</text>')
write_svg(PREVIEW_DIR/"03-cut-contours-board.svg",svg_document("".join(preview3),"0 0 1200 675","1200px","675px",title="Frost cut contour preview"))

print(f"Created {len(ELEMENTS)} layered elements, {len(PATTERNS)} layered seamless patterns and 3 preview boards.")
