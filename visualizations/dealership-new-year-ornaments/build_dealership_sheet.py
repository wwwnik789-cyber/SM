#!/usr/bin/env python3
"""Build a restrained premium automotive New Year ornament sheet.

Revision 2 replaces the earlier icon-like treatment with precise automotive
silhouettes, thin metallic detailing, deep red and evergreen fields, and
architectural fir-tree motifs. Client artwork is intentionally not included.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import cos, pi, sin
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "dealership-new-year-ornaments-16.svg"

INK = "#101820"
GRAPHITE = "#26323B"
CHARCOAL = "#182229"
GREEN_DARK = "#082C24"
GREEN = "#0C4A36"
GREEN_LIGHT = "#2E6B4D"
BURGUNDY = "#651725"
RED_DARK = "#831B2A"
RED = "#B82132"
RED_LIGHT = "#D74A52"
SILVER_DARK = "#7E898D"
SILVER = "#C5CCCA"
PEARL = "#EDF0EB"
IVORY = "#F5F0E5"
GOLD_DARK = "#8A6B34"
GOLD = "#C4A15D"
GOLD_LIGHT = "#E2C982"
ICE = "#DCE9E5"
CUT = "#FF00FF"

DEFS = f"""
<defs>
  <linearGradient id="gGreen" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="{GREEN_LIGHT}"/><stop offset="0.48" stop-color="{GREEN}"/><stop offset="1" stop-color="{GREEN_DARK}"/>
  </linearGradient>
  <linearGradient id="gRed" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="{RED_LIGHT}"/><stop offset="0.45" stop-color="{RED}"/><stop offset="1" stop-color="{BURGUNDY}"/>
  </linearGradient>
  <linearGradient id="gBurgundy" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="{RED_DARK}"/><stop offset="1" stop-color="{BURGUNDY}"/>
  </linearGradient>
  <linearGradient id="gGraphite" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#3C4A52"/><stop offset="0.48" stop-color="{GRAPHITE}"/><stop offset="1" stop-color="{INK}"/>
  </linearGradient>
  <linearGradient id="gSilver" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="{IVORY}"/><stop offset="0.32" stop-color="{SILVER}"/><stop offset="0.62" stop-color="{PEARL}"/><stop offset="1" stop-color="{SILVER_DARK}"/>
  </linearGradient>
  <linearGradient id="gGold" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="{GOLD_LIGHT}"/><stop offset="0.52" stop-color="{GOLD}"/><stop offset="1" stop-color="{GOLD_DARK}"/>
  </linearGradient>
  <radialGradient id="gGlass" cx="34%" cy="22%" r="82%">
    <stop offset="0" stop-color="#FFFFFF" stop-opacity=".88"/><stop offset="0.38" stop-color="{ICE}" stop-opacity=".62"/><stop offset="1" stop-color="#668A82" stop-opacity=".30"/>
  </radialGradient>
</defs>
"""


@dataclass(frozen=True)
class Ornament:
    index: int
    slug: str
    name_ru: str
    outer: str
    hole_x: float
    hole_y: float
    gradient: str

    @property
    def clip_id(self) -> str:
        return f"autoClip{self.index:02d}"


def clean(content: str) -> str:
    return "\n".join(line.rstrip() for line in content.splitlines()) + "\n"


def style_shape(shape: str, attributes: str) -> str:
    return shape[:-2] + " " + attributes + "/>"


def star_points(cx: float, cy: float, outer: float, inner: float, count: int = 5) -> str:
    points: list[str] = []
    for i in range(count * 2):
        radius = outer if i % 2 == 0 else inner
        angle = -pi / 2 + i * pi / count
        points.append(f"{cx + radius*cos(angle):.2f},{cy + radius*sin(angle):.2f}")
    return " ".join(points)


def snowflake(cx: float, cy: float, radius: float, color: str = IVORY, width: float = 1.5, opacity: float = .7) -> str:
    arm = f'<path d="M0 0 V-{radius} M0 -{radius*.48:.2f} L-{radius*.18:.2f} -{radius*.64:.2f} M0 -{radius*.48:.2f} L{radius*.18:.2f} -{radius*.64:.2f}"/>'
    return (
        f'<g transform="translate({cx} {cy})" fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="round" opacity="{opacity}">'
        + "".join(f'<g transform="rotate({i*60})">{arm}</g>' for i in range(6))
        + '</g>'
    )


def fir_tree(x: float, y: float, scale: float = 1.0, fill: str = GREEN_DARK, accent: str = GOLD) -> str:
    return f'''
<g transform="translate({x} {y}) scale({scale})">
  <path d="M0 -56 L-20 -25 H-11 L-32 8 H-20 L-46 48 H46 L20 8 H32 L11 -25 H20 Z" fill="{fill}"/>
  <path d="M0 -48 V44" stroke="{accent}" stroke-width="2" opacity=".65"/>
  <path d="M-16 -23 H16 M-27 7 H27 M-39 39 H39" stroke="{accent}" stroke-width="1.5" opacity=".5"/>
  <rect x="-5" y="48" width="10" height="14" fill="{GOLD_DARK}"/>
</g>'''


def fir_branch(x: float, y: float, angle: float = 0, scale: float = 1.0) -> str:
    needles: list[str] = []
    for i in range(7):
        px = 9 + i * 12
        length = 18 - i * 1.25
        needles.append(f'<path d="M{px} 0 l{-length*.62:.2f} {-length:.2f} M{px} 0 l{-length*.28:.2f} {length:.2f}"/>')
    return f'''
<g transform="translate({x} {y}) rotate({angle}) scale({scale})" fill="none" stroke="{GREEN_LIGHT}" stroke-width="3" stroke-linecap="round">
  <path d="M0 0 C28 -2 56 1 88 0" stroke="{GOLD_DARK}" stroke-width="2"/>
  {''.join(needles)}
  <circle cx="27" cy="-11" r="4" fill="{RED}" stroke="none"/><circle cx="54" cy="12" r="3.5" fill="{RED_LIGHT}" stroke="none"/>
</g>'''


def sparkle_field() -> str:
    return f'''
<g fill="{IVORY}" opacity=".72">
  <circle cx="71" cy="83" r="2.2"/><circle cx="229" cy="99" r="2.8"/><circle cx="59" cy="183" r="1.8"/>
  <circle cx="239" cy="201" r="2.1"/><circle cx="111" cy="247" r="1.7"/><circle cx="204" cy="244" r="2"/>
</g>'''


# Closed technical outlines. Forms remain manufacturable while the visual language is
# intentionally quieter than the first revision: finer borders and cleaner geometry.
OUTERS = [
    '<path d="M136 43 V28 Q136 14 150 14 Q164 14 164 28 V43 C218 50 259 96 259 157 C259 222 211 270 150 270 C89 270 41 222 41 157 C41 96 82 50 136 43 Z"/>',
    '<path d="M136 51 V34 Q136 18 150 18 Q164 18 164 34 V51 H198 L231 94 H260 Q276 94 276 111 V215 Q276 231 260 231 H239 Q232 261 204 261 Q176 261 169 231 H113 Q106 261 78 261 Q50 261 43 231 H25 Q18 231 18 214 V131 Q18 115 34 109 L72 96 L102 65 Q116 51 136 51 Z"/>',
    '<path d="M136 54 V36 Q136 20 150 20 Q164 20 164 36 V54 H183 L224 95 L263 111 Q280 118 280 136 V210 Q280 230 260 230 H240 Q233 260 204 260 Q175 260 168 230 H111 Q104 260 75 260 Q46 260 39 230 H23 Q16 230 16 212 V149 Q16 130 35 120 L77 104 L112 66 Q122 54 136 54 Z"/>',
    '<path d="M136 43 V28 Q136 14 150 14 Q164 14 164 28 V43 C218 50 259 96 259 157 C259 222 211 270 150 270 C89 270 41 222 41 157 C41 96 82 50 136 43 Z"/>',
    '<path d="M134 40 V27 Q134 13 148 13 Q162 13 162 27 V40 C201 47 224 75 224 116 V228 Q224 264 188 276 H108 Q72 264 72 228 V116 Q72 75 111 47 Z"/>',
    '<path d="M133 43 V29 Q133 15 147 15 Q161 15 161 29 V43 C120 50 89 80 79 121 C70 157 83 194 116 216 L171 270 H203 V241 H230 V214 H259 V184 H218 L177 143 C184 100 163 59 133 43 Z"/>',
    '<path d="M136 43 V28 Q136 14 150 14 Q164 14 164 28 V43 C218 50 259 96 259 157 C259 222 211 270 150 270 C89 270 41 222 41 157 C41 96 82 50 136 43 Z"/>',
    '<path d="M136 43 V28 Q136 14 150 14 Q164 14 164 28 V43 C218 50 259 96 259 157 C259 222 211 270 150 270 C89 270 41 222 41 157 C41 96 82 50 136 43 Z"/>',
    '<path d="M135 46 V29 Q135 15 150 15 Q165 15 165 29 V46 H239 Q262 46 262 69 V247 Q262 270 239 270 H61 Q38 270 38 247 V69 Q38 46 61 46 Z"/>',
    '<path d="M136 43 V28 Q136 14 150 14 Q164 14 164 28 V43 C218 50 259 96 259 157 C259 222 211 270 150 270 C89 270 41 222 41 157 C41 96 82 50 136 43 Z"/>',
    '<path d="M136 43 V28 Q136 14 150 14 Q164 14 164 28 V43 C218 50 259 96 259 157 C259 222 211 270 150 270 C89 270 41 222 41 157 C41 96 82 50 136 43 Z"/>',
    '<path d="M136 43 V28 Q136 14 150 14 Q164 14 164 28 V43 C218 50 259 96 259 157 C259 222 211 270 150 270 C89 270 41 222 41 157 C41 96 82 50 136 43 Z"/>',
    '<path d="M136 42 V28 Q136 14 150 14 Q164 14 164 28 V42 L260 120 V272 H40 V120 Z"/>',
    '<path d="M136 46 V30 Q136 15 150 15 Q164 15 164 30 V46 C218 54 257 99 257 158 C257 201 238 230 216 248 L230 282 H70 L84 248 C62 230 43 201 43 158 C43 99 82 54 136 46 Z"/>',
    '<path d="M136 39 V27 Q136 13 150 13 Q164 13 164 27 V39 L181 61 H169 L204 104 H188 L228 155 H207 L252 215 H175 V273 H125 V215 H48 L93 155 H72 L112 104 H96 L131 61 H119 Z"/>',
    '<path d="M136 43 V28 Q136 14 150 14 Q164 14 164 28 V43 C218 50 259 96 259 157 C259 222 211 270 150 270 C89 270 41 222 41 157 C41 96 82 50 136 43 Z"/>',
]

SPECS = [
    ("sedan-medallion", "Премиальный седан и еловые ветви", 150, 29, "gGreen"),
    ("suv-winter-forest", "SUV в зимнем хвойном пейзаже", 150, 35, "gGreen"),
    ("grand-tourer", "Спортивное купе", 150, 37, "gBurgundy"),
    ("electric-crossover", "Электрокроссовер", 150, 29, "gGraphite"),
    ("key-fob", "Премиальный брелок", 148, 28, "gBurgundy"),
    ("classic-key", "Автомобильный ключ", 147, 30, "gGreen"),
    ("alloy-wheel", "Легкосплавный диск", 150, 29, "gGraphite"),
    ("winter-tire", "Зимнее колесо и хвоя", 150, 29, "gGreen"),
    ("instrument-cluster", "Приборная панель", 150, 29, "gGraphite"),
    ("steering-wreath", "Руль в хвойном венке", 150, 29, "gGreen"),
    ("delivery-car", "Выдача автомобиля", 150, 29, "gBurgundy"),
    ("gift-key-medallion", "Ключ и подарочная лента", 150, 29, "gGreen"),
    ("showroom", "Фасад автосалона с ёлками", 150, 29, "gGraphite"),
    ("car-snow-globe", "Снежный шар с автомобилем и ёлкой", 150, 30, "gGreen"),
    ("fir-route", "Ёлка с автомобильным маршрутом", 150, 28, "gGreen"),
    ("tread-bauble", "Шар с протектором и еловой ветвью", 150, 29, "gBurgundy"),
]

ORNAMENTS = [
    Ornament(index, slug, name, OUTERS[index - 1], hx, hy, gradient)
    for index, (slug, name, hx, hy, gradient) in enumerate(SPECS, 1)
]


def sedan_front() -> str:
    return f'''
<path d="M87 145 C92 106 111 82 150 76 C189 82 208 106 213 145" fill="none" stroke="{SILVER}" stroke-width="4"/>
<path d="M91 140 H209 L220 205 H80 Z" fill="url(#gSilver)" stroke="{INK}" stroke-width="3"/>
<path d="M111 96 H189 L202 137 H98 Z" fill="{CHARCOAL}" stroke="{SILVER_DARK}" stroke-width="2"/>
<path d="M91 158 H121 M179 158 H209" stroke="{IVORY}" stroke-width="6" stroke-linecap="round"/>
<path d="M106 178 H194 L187 199 H113 Z" fill="{INK}"/>
<path d="M118 182 H182 M116 188 H184 M115 194 H185" stroke="{SILVER_DARK}" stroke-width="1.5"/>
<path d="M94 207 V229 M206 207 V229" stroke="{INK}" stroke-width="12"/>
'''


def vehicle_side(body: str = "url(#gSilver)", sport: bool = False) -> str:
    if sport:
        body_path = "M35 168 C51 151 71 145 96 140 L124 104 C132 94 143 89 158 89 H185 C199 91 211 103 224 126 L253 143 C264 149 271 159 271 176 V196 H31 V180 C31 175 32 171 35 168 Z"
        glass = "M108 137 L132 106 H160 L184 137 Z M166 106 H183 C193 108 204 118 214 137 H190 Z"
    else:
        body_path = "M28 164 C41 150 64 144 91 140 L116 99 C122 90 133 85 147 85 H190 C203 87 214 97 227 128 L258 144 C269 149 275 159 275 174 V201 H23 V178 C23 172 25 167 28 164 Z"
        glass = "M102 137 L124 100 H150 V137 Z M157 100 H187 C197 103 207 113 217 137 H157 Z"
    return f'''
<path d="{body_path}" fill="{body}" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>
<path d="{glass}" fill="{CHARCOAL}" stroke="{SILVER_DARK}" stroke-width="2"/>
<path d="M36 171 H72 M232 155 H262" stroke="{IVORY}" stroke-width="5" stroke-linecap="round"/>
<path d="M52 184 H247" stroke="{GOLD}" stroke-width="2" opacity=".85"/>
<circle cx="81" cy="202" r="27" fill="{INK}" stroke="{SILVER}" stroke-width="5"/><circle cx="81" cy="202" r="10" fill="{GRAPHITE}" stroke="{GOLD}" stroke-width="2"/>
<circle cx="215" cy="202" r="27" fill="{INK}" stroke="{SILVER}" stroke-width="5"/><circle cx="215" cy="202" r="10" fill="{GRAPHITE}" stroke="{GOLD}" stroke-width="2"/>
'''


def ornament_art(index: int) -> str:
    art = {
        1: f'''
<circle cx="150" cy="157" r="101" fill="url(#gGreen)"/>
<circle cx="150" cy="157" r="91" fill="none" stroke="{GOLD}" stroke-width="2" opacity=".8"/>
{fir_branch(48,110,68,.75)}{fir_branch(252,111,112,.75)}
{sedan_front()}
<path d="M65 230 Q150 250 235 230" fill="none" stroke="{GOLD}" stroke-width="2"/>
{snowflake(213,77,11,IVORY,1.2,.6)}''',
        2: f'''
<path d="M22 127 H274 V224 H22 Z" fill="{GREEN_DARK}"/>
{fir_tree(51,130,.62,GREEN_LIGHT,GOLD_DARK)}{fir_tree(244,129,.72,GREEN_DARK,GOLD)}
<path d="M21 208 Q90 186 151 205 T276 204 V235 H18 Z" fill="{IVORY}" opacity=".9"/>
{vehicle_side('url(#gSilver)', False)}
<path d="M35 175 H265" stroke="{RED}" stroke-width="3"/>
{snowflake(67,76,10,IVORY,1.2,.65)}{snowflake(227,83,8,IVORY,1.1,.55)}''',
        3: f'''
<path d="M18 119 H280 V224 H18 Z" fill="{BURGUNDY}"/>
<path d="M20 210 Q112 190 280 201 V232 H18 Z" fill="{GREEN_DARK}"/>
{vehicle_side('url(#gRed)', True)}
<path d="M54 73 H246" stroke="{GOLD}" stroke-width="2" opacity=".75"/>
<path d="M73 67 H227" stroke="{IVORY}" stroke-width="1" opacity=".5"/>
{snowflake(51,95,10,IVORY,1.2,.55)}''',
        4: f'''
<circle cx="150" cy="157" r="101" fill="url(#gGraphite)"/>
<circle cx="150" cy="157" r="91" fill="none" stroke="{GOLD}" stroke-width="2"/>
<path d="M57 192 C66 164 92 148 122 144 L145 114 H184 L211 146 C228 150 242 160 247 180 L238 204 H64 Z" fill="url(#gSilver)" stroke="{INK}" stroke-width="3"/>
<path d="M135 141 L151 119 H181 L198 144 Z" fill="{GREEN_DARK}"/>
<circle cx="101" cy="203" r="20" fill="{INK}" stroke="{SILVER}" stroke-width="4"/><circle cx="207" cy="203" r="20" fill="{INK}" stroke="{SILVER}" stroke-width="4"/>
<path d="M74 178 H104 M218 174 H241" stroke="{IVORY}" stroke-width="5" stroke-linecap="round"/>
<path d="M54 126 C31 116 34 86 54 79 C74 72 90 89 83 107 C78 120 66 125 54 126 Z M51 79 L38 61" fill="none" stroke="{RED}" stroke-width="4" stroke-linecap="round"/>
<path d="M35 57 H45 V68" fill="none" stroke="{GOLD}" stroke-width="3"/>
{fir_tree(218,96,.38,GREEN,GOLD)}''',
        5: f'''
<rect x="84" y="62" width="128" height="196" rx="42" fill="url(#gGraphite)" stroke="{GOLD}" stroke-width="3"/>
<rect x="94" y="74" width="108" height="172" rx="34" fill="{BURGUNDY}" stroke="{RED_LIGHT}" stroke-width="2"/>
<path d="M111 112 H185 M111 136 H185" stroke="{SILVER}" stroke-width="3" stroke-linecap="round"/>
<circle cx="117" cy="124" r="5" fill="{GREEN_LIGHT}"/><circle cx="179" cy="124" r="5" fill="{RED_LIGHT}"/>
<path d="M117 219 Q148 235 179 219" fill="none" stroke="{GOLD}" stroke-width="2"/>
{fir_branch(102,189,-9,.52)}
''',
        6: f'''
<circle cx="119" cy="116" r="56" fill="url(#gGraphite)" stroke="{GOLD}" stroke-width="3"/>
<circle cx="119" cy="116" r="29" fill="{GREEN_DARK}" stroke="{SILVER}" stroke-width="3"/>
<circle cx="119" cy="116" r="13" fill="{BURGUNDY}"/>
<path d="M157 146 L220 209 H251 V235 H224 V258 H198 L129 190 Z" fill="url(#gSilver)" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>
<path d="M171 166 L203 198 M191 150 L219 178" stroke="{RED}" stroke-width="3"/>
{fir_branch(62,67,12,.5)}''',
        7: f'''
<circle cx="150" cy="157" r="101" fill="{INK}" stroke="{GOLD}" stroke-width="3"/>
<circle cx="150" cy="157" r="84" fill="url(#gSilver)" stroke="{SILVER_DARK}" stroke-width="2"/>
<circle cx="150" cy="157" r="69" fill="{GRAPHITE}"/>
<g fill="url(#gSilver)" stroke="{INK}" stroke-width="2">
  <path d="M150 157 L137 84 Q150 74 163 84 Z"/><path d="M150 157 L213 113 Q226 121 226 137 Z"/>
  <path d="M150 157 L202 211 Q195 226 179 231 Z"/><path d="M150 157 L104 220 Q88 216 80 201 Z"/>
  <path d="M150 157 L76 130 Q76 114 89 103 Z"/>
</g>
<circle cx="150" cy="157" r="36" fill="{INK}" stroke="{GOLD}" stroke-width="3"/>
<circle cx="150" cy="157" r="22" fill="{GREEN_DARK}"/>
<g fill="{SILVER}"><circle cx="150" cy="124" r="3"/><circle cx="181" cy="147" r="3"/><circle cx="169" cy="184" r="3"/><circle cx="131" cy="184" r="3"/><circle cx="119" cy="147" r="3"/></g>''',
        8: f'''
<circle cx="150" cy="157" r="101" fill="url(#gGreen)" stroke="{GOLD}" stroke-width="3"/>
<circle cx="150" cy="157" r="84" fill="{INK}" stroke="{SILVER}" stroke-width="4"/>
<path d="M91 87 L110 109 M121 67 L134 98 M179 67 L166 98 M209 87 L190 109 M232 124 L199 134 M232 190 L199 180 M91 228 L112 207 M209 228 L188 207" stroke="{SILVER}" stroke-width="6" stroke-linecap="round"/>
<circle cx="150" cy="157" r="62" fill="url(#gGraphite)" stroke="{GOLD}" stroke-width="2"/>
<path d="M150 100 V214 M93 157 H207 M110 117 L190 197 M190 117 L110 197" stroke="{SILVER_DARK}" stroke-width="5"/>
<circle cx="150" cy="157" r="29" fill="{GREEN_DARK}"/>
{fir_branch(66,68,15,.54)}''',
        9: f'''
<rect x="52" y="64" width="196" height="190" rx="22" fill="url(#gGraphite)" stroke="{GOLD}" stroke-width="3"/>
<path d="M76 184 A74 74 0 0 1 224 184" fill="none" stroke="{SILVER_DARK}" stroke-width="12"/>
<path d="M83 184 A67 67 0 0 1 100 139 M117 119 A67 67 0 0 1 151 112 M180 119 A67 67 0 0 1 211 151" fill="none" stroke="{GREEN_LIGHT}" stroke-width="4"/>
<path d="M150 184 L202 128" stroke="{RED_LIGHT}" stroke-width="5" stroke-linecap="round"/>
<circle cx="150" cy="184" r="10" fill="{GOLD}"/>
<g stroke="{IVORY}" stroke-width="2"><path d="M86 181 l10 -1"/><path d="M102 139 l8 6"/><path d="M132 118 l2 10"/><path d="M169 118 l-2 10"/><path d="M200 138 l-8 7"/><path d="M215 181 l-10 -1"/></g>
{snowflake(82,87,10,IVORY,1.2,.5)}''',
        10: f'''
<circle cx="150" cy="157" r="101" fill="url(#gGreen)"/>
<circle cx="150" cy="157" r="90" fill="none" stroke="{GOLD}" stroke-width="2"/>
<g fill="none" stroke="{GREEN_LIGHT}" stroke-width="11" stroke-linecap="round" stroke-dasharray="14 7"><circle cx="150" cy="157" r="80"/></g>
<g fill="{RED}"><circle cx="92" cy="105" r="4"/><circle cx="204" cy="112" r="4"/><circle cx="80" cy="183" r="4"/><circle cx="215" cy="184" r="4"/></g>
<circle cx="150" cy="157" r="67" fill="{INK}" stroke="{SILVER}" stroke-width="10"/>
<path d="M150 158 L108 111 M150 158 L192 111 M150 158 V218" stroke="{SILVER}" stroke-width="10" stroke-linecap="round"/>
<circle cx="150" cy="158" r="35" fill="{GREEN_DARK}" stroke="{GOLD}" stroke-width="3"/>
''',
        11: f'''
<circle cx="150" cy="157" r="101" fill="url(#gBurgundy)"/>
<circle cx="150" cy="157" r="91" fill="none" stroke="{GOLD}" stroke-width="2"/>
{fir_branch(44,105,66,.67)}{fir_branch(255,106,114,.67)}
{sedan_front()}
<path d="M150 94 C129 72 106 68 98 82 C91 96 114 107 150 100 C186 107 209 96 202 82 C194 68 171 72 150 94 Z" fill="{RED}" stroke="{GOLD_LIGHT}" stroke-width="2"/>
<path d="M145 98 L132 133 L150 124 L168 133 L155 98" fill="{RED_DARK}"/>
''',
        12: f'''
<circle cx="150" cy="157" r="101" fill="url(#gGreen)"/>
<circle cx="150" cy="157" r="91" fill="none" stroke="{GOLD}" stroke-width="2"/>
<path d="M74 54 H95 V260 H74 Z M205 54 H226 V260 H205 Z" fill="{BURGUNDY}" opacity=".94"/>
<path d="M46 145 H254 V168 H46 Z" fill="{RED_DARK}" opacity=".94"/>
<circle cx="114" cy="126" r="38" fill="url(#gGraphite)" stroke="{GOLD}" stroke-width="3"/>
<circle cx="114" cy="126" r="16" fill="none" stroke="{SILVER}" stroke-width="4"/>
<path d="M139 151 L197 209 H225 V229 H204 V249 H181 L126 193" fill="url(#gSilver)" stroke="{INK}" stroke-width="3"/>
<path d="M171 180 L202 210" stroke="{RED}" stroke-width="3"/>
{fir_branch(79,82,-8,.48)}''',
        13: f'''
<path d="M52 127 L150 48 L248 127 V268 H52 Z" fill="url(#gGraphite)"/>
<path d="M62 130 L150 61 L238 130" fill="none" stroke="{GOLD}" stroke-width="3"/>
<rect x="75" y="138" width="150" height="105" rx="4" fill="{CHARCOAL}" stroke="{SILVER_DARK}" stroke-width="2"/>
<path d="M125 138 V243 M175 138 V243" stroke="{GREEN_LIGHT}" stroke-width="3"/>
<path d="M80 216 Q101 183 149 180 Q198 183 220 216" fill="none" stroke="{SILVER}" stroke-width="3"/>
<path d="M103 193 H195" stroke="{SILVER_DARK}" stroke-width="2"/>
{fir_tree(61,211,.42,GREEN,GOLD)}{fir_tree(239,211,.42,GREEN,GOLD)}
<path d="M65 251 H235" stroke="{RED}" stroke-width="4"/>
''',
        14: f'''
<circle cx="150" cy="157" r="99" fill="url(#gGlass)" stroke="{GOLD}" stroke-width="3"/>
<path d="M80 244 H220 L231 281 H69 Z" fill="url(#gGraphite)" stroke="{GOLD}" stroke-width="3"/>
{fir_tree(100,174,.68,GREEN_DARK,GOLD)}
<path d="M94 203 C106 181 125 171 153 168 L172 145 H200 L220 172 C232 176 240 184 243 198 L236 218 H96 Z" fill="url(#gSilver)" stroke="{INK}" stroke-width="3"/>
<path d="M159 166 L178 148 H197 L211 170 Z" fill="{CHARCOAL}"/>
<circle cx="127" cy="216" r="15" fill="{INK}"/><circle cx="210" cy="216" r="15" fill="{INK}"/>
<g fill="{IVORY}"><circle cx="77" cy="112" r="3"/><circle cx="193" cy="89" r="3"/><circle cx="222" cy="132" r="2.4"/><circle cx="132" cy="105" r="2"/></g>
''',
        15: f'''
<path d="M150 43 L177 78 H165 L199 120 H183 L222 168 H203 L244 217 H174 V268 H126 V217 H56 L97 168 H78 L117 120 H101 L135 78 H123 Z" fill="url(#gGreen)"/>
<path d="M150 52 V260" stroke="{GOLD}" stroke-width="2" opacity=".6"/>
<path d="M112 105 H188 M92 154 H208 M68 208 H232" stroke="{GOLD}" stroke-width="2" opacity=".55"/>
<path d="M86 184 C104 166 124 158 148 158 H181 C197 159 211 168 224 184" fill="none" stroke="{SILVER}" stroke-width="5"/>
<path d="M83 189 H227" stroke="{RED}" stroke-width="4"/>
<circle cx="102" cy="190" r="12" fill="{INK}" stroke="{SILVER}" stroke-width="3"/><circle cx="210" cy="190" r="12" fill="{INK}" stroke="{SILVER}" stroke-width="3"/>
<path d="M92 135 C119 120 164 113 205 126" fill="none" stroke="{IVORY}" stroke-width="2" stroke-dasharray="5 6"/>
<circle cx="92" cy="135" r="5" fill="{RED}"/><circle cx="205" cy="126" r="5" fill="{GOLD}"/>
<polygon points="{star_points(150,72,13,5.5)}" fill="{GOLD_LIGHT}"/>
''',
        16: f'''
<circle cx="150" cy="157" r="101" fill="url(#gBurgundy)"/>
<circle cx="150" cy="157" r="91" fill="none" stroke="{GOLD}" stroke-width="2"/>
<g stroke="{GRAPHITE}" stroke-width="9" stroke-linecap="round" opacity=".88">
  <path d="M74 84 L105 116 M110 62 L128 104 M171 59 L154 104 M214 82 L184 116 M235 126 L195 141 M231 191 L194 178 M83 226 L111 199 M207 230 L183 201"/>
</g>
{fir_branch(62,78,14,.72)}
<circle cx="150" cy="164" r="49" fill="{GREEN_DARK}" stroke="{GOLD}" stroke-width="3"/>
<path d="M126 186 L150 125 L174 186" fill="none" stroke="{SILVER}" stroke-width="3"/>
<path d="M135 163 H165 M130 176 H170" stroke="{RED_LIGHT}" stroke-width="3"/>
''',
    }
    return art[index]


def logo_zone(index: int) -> str:
    zones = {
        1: '<rect x="116" y="202" width="68" height="25" rx="4"/>',
        2: '<rect x="126" y="153" width="72" height="29" rx="4"/>',
        3: '<rect x="126" y="149" width="72" height="29" rx="4"/>',
        4: '<rect x="118" y="183" width="68" height="25" rx="4"/>',
        5: '<path d="M148 153 L181 170 V207 Q181 224 148 240 Q115 224 115 207 V170 Z"/>',
        6: '<circle cx="119" cy="116" r="23"/>',
        7: '<circle cx="150" cy="157" r="20"/>',
        8: '<circle cx="150" cy="157" r="22"/>',
        9: '<rect x="111" y="205" width="78" height="31" rx="5"/>',
        10: '<circle cx="150" cy="158" r="25"/>',
        11: '<rect x="116" y="202" width="68" height="25" rx="4"/>',
        12: '<rect x="170" y="200" width="54" height="34" rx="4" transform="rotate(-10 197 217)"/>',
        13: '<rect x="91" y="102" width="118" height="25" rx="4"/>',
        14: '<rect x="105" y="251" width="90" height="22" rx="4"/>',
        15: '<rect x="111" y="218" width="78" height="32" rx="5"/>',
        16: '<rect x="112" y="147" width="76" height="34" rx="6"/>',
    }
    return zones[index]


def print_body(ornament: Ornament) -> str:
    outer = style_shape(
        ornament.outer,
        f'fill="url(#{ornament.gradient})" stroke="{GOLD}" stroke-width="3.5" stroke-linejoin="round" stroke-linecap="round"',
    )
    return f'''
<defs><clipPath id="{ornament.clip_id}">{ornament.outer}</clipPath></defs>
{outer}
<g clip-path="url(#{ornament.clip_id})">{ornament_art(ornament.index)}</g>
<circle cx="{ornament.hole_x}" cy="{ornament.hole_y}" r="7" fill="{GREEN_DARK}" stroke="{GOLD_LIGHT}" stroke-width="2"/>
'''


def cut_geometry(ornament: Ornament) -> str:
    return ornament.outer + f'<circle cx="{ornament.hole_x}" cy="{ornament.hole_y}" r="4" data-purpose="hanging-hole"/>'


print_groups: list[str] = []
logo_groups: list[str] = []
cut_groups: list[str] = []
for idx, ornament in enumerate(ORNAMENTS):
    col, row = idx % 4, idx // 4
    x, y = col * 300, row * 300
    transform = f'translate({x} {y})'
    print_groups.append(
        f'<g id="ornament-{ornament.index:02d}-{ornament.slug}" inkscape:label="{ornament.index:02d} {ornament.name_ru}" transform="{transform}">{print_body(ornament)}</g>'
    )
    logo_groups.append(
        f'<g id="logo-zone-{ornament.index:02d}" data-client-logo-zone="true" transform="{transform}" fill="{IVORY}" stroke="{GOLD}" stroke-width="1.8">{logo_zone(ornament.index)}</g>'
    )
    cut_groups.append(
        f'<g id="cut-{ornament.index:02d}-{ornament.slug}" transform="{transform}">{cut_geometry(ornament)}</g>'
    )

layers = (
    '<g inkscape:groupmode="layer" inkscape:label="PRINT" id="PRINT">' + "".join(print_groups) + '</g>'
    + '<g inkscape:groupmode="layer" inkscape:label="LOGO ZONES — PLACE CLIENT ART" id="LOGO_ZONES">' + "".join(logo_groups) + '</g>'
    + f'<g inkscape:groupmode="layer" inkscape:label="CutContour" id="CutContour" fill="none" stroke="{CUT}" stroke-width="0.3mm" stroke-linejoin="round" stroke-linecap="round" vector-effect="non-scaling-stroke" data-spot-color="CutContour">' + "".join(cut_groups) + '</g>'
)

svg = clean(f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" width="1200mm" height="1200mm" viewBox="0 0 1200 1200">
<title>Premium automotive New Year ornaments — red and evergreen revision — 16-piece dealership sheet</title>
{DEFS}
{layers}
</svg>''')
OUTPUT.write_text(svg, encoding="utf-8")
ET.parse(OUTPUT)
print(OUTPUT)
