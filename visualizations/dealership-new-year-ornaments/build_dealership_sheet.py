#!/usr/bin/env python3
"""Build a premium automotive New Year ornament sheet with editable client-logo zones."""
from __future__ import annotations

from dataclasses import dataclass
from math import cos, pi, sin
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "dealership-new-year-ornaments-16.svg"

MIDNIGHT = "#061523"
NAVY = "#0B2544"
GRAPHITE = "#1F2D3D"
STEEL = "#64788E"
SILVER = "#C7D4DF"
ICE = "#EAF8FF"
WHITE = "#FFFFFF"
BLUE = "#1F6FE5"
CYAN = "#67D8FF"
GOLD = "#C7AA6A"
RED = "#A82A43"
CUT = "#FF00FF"

DEFS = f"""
<defs>
  <linearGradient id="gNavy" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="{GRAPHITE}"/><stop offset="0.52" stop-color="{NAVY}"/><stop offset="1" stop-color="{MIDNIGHT}"/>
  </linearGradient>
  <linearGradient id="gSteel" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="{WHITE}"/><stop offset="0.46" stop-color="{SILVER}"/><stop offset="1" stop-color="{STEEL}"/>
  </linearGradient>
  <linearGradient id="gBlue" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="{CYAN}"/><stop offset="0.45" stop-color="{BLUE}"/><stop offset="1" stop-color="{NAVY}"/>
  </linearGradient>
  <linearGradient id="gGold" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#F1DCA3"/><stop offset="0.5" stop-color="{GOLD}"/><stop offset="1" stop-color="#8F7445"/>
  </linearGradient>
  <radialGradient id="gIce" cx="35%" cy="28%" r="78%">
    <stop offset="0" stop-color="{WHITE}"/><stop offset="0.55" stop-color="{ICE}"/><stop offset="1" stop-color="{CYAN}"/>
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


def snowflake(cx: float, cy: float, radius: float, color: str = WHITE, width: float = 3.2, opacity: float = .8) -> str:
    arm = f'<path d="M0 0 V-{radius} M0 -{radius*.48:.2f} L-{radius*.20:.2f} -{radius*.67:.2f} M0 -{radius*.48:.2f} L{radius*.20:.2f} -{radius*.67:.2f}"/>'
    return (
        f'<g transform="translate({cx} {cy})" fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="round" opacity="{opacity}">'
        + "".join(f'<g transform="rotate({i*60})">{arm}</g>' for i in range(6))
        + '</g>'
    )


def winter_dots() -> str:
    return f'''
<g fill="{WHITE}" opacity=".76">
  <circle cx="72" cy="82" r="4"/><circle cx="230" cy="94" r="5"/><circle cx="56" cy="174" r="3.5"/>
  <circle cx="241" cy="198" r="4"/><circle cx="102" cy="244" r="3"/><circle cx="204" cy="250" r="3.5"/>
</g>'''


OUTERS = [
    '<path d="M132 44 V28 Q132 12 150 12 Q168 12 168 28 V44 C199 50 218 75 228 115 L252 122 Q268 125 268 143 V205 Q268 225 248 225 H235 V258 H194 V232 H106 V258 H65 V225 H52 Q32 225 32 205 V143 Q32 125 48 122 L72 115 C82 75 101 50 132 44 Z"/>',
    '<path d="M132 53 V34 Q132 16 150 16 Q168 16 168 34 V53 H198 L232 100 H260 Q276 100 276 118 V208 Q276 227 257 227 H239 Q233 260 202 260 Q171 260 165 227 H116 Q110 260 79 260 Q48 260 42 227 H27 Q18 227 18 208 V133 Q18 117 33 112 L75 100 L101 70 Q113 53 132 53 Z"/>',
    '<path d="M132 55 V36 Q132 18 150 18 Q168 18 168 36 V55 H184 L224 96 L265 112 Q280 118 280 137 V207 Q280 229 258 229 H241 Q234 260 204 260 Q174 260 167 229 H112 Q105 260 75 260 Q45 260 38 229 H24 Q16 229 16 211 V150 Q16 129 36 120 L78 105 L111 68 Q121 55 132 55 Z"/>',
    '<path d="M132 45 V29 Q132 13 150 13 Q168 13 168 29 V45 C220 54 255 95 255 151 C255 217 208 270 150 270 C92 270 45 217 45 151 C45 95 80 54 132 45 Z"/>',
    '<path d="M128 40 V27 Q128 11 146 11 Q164 11 164 27 V40 C205 48 226 78 226 119 V226 Q226 270 182 278 H112 Q68 270 68 226 V119 Q68 78 109 48 Z"/>',
    '<path d="M130 44 V29 Q130 13 148 13 Q166 13 166 29 V44 C120 52 86 83 76 125 C67 165 84 202 119 222 L168 270 H202 V239 H229 V212 H258 V181 H216 L176 141 C182 97 160 59 130 44 Z"/>',
    '<path d="M132 44 V28 Q132 12 150 12 Q168 12 168 28 V44 C224 53 263 99 263 158 C263 224 213 274 150 274 C87 274 37 224 37 158 C37 99 76 53 132 44 Z"/>',
    '<path d="M132 44 V28 Q132 12 150 12 Q168 12 168 28 V44 C224 53 263 99 263 158 C263 224 213 274 150 274 C87 274 37 224 37 158 C37 99 76 53 132 44 Z"/>',
    '<path d="M130 47 V29 Q130 13 150 13 Q170 13 170 29 V47 H239 Q263 47 263 71 V247 Q263 271 239 271 H61 Q37 271 37 247 V71 Q37 47 61 47 Z"/>',
    '<path d="M132 44 V28 Q132 12 150 12 Q168 12 168 28 V44 C224 53 263 99 263 158 C263 224 213 274 150 274 C87 274 37 224 37 158 C37 99 76 53 132 44 Z"/>',
    '<path d="M150 72 C119 42 96 42 84 61 C72 82 89 103 123 104 L102 119 C77 91 50 84 38 101 Q24 121 43 136 L70 155 C57 173 50 195 52 218 Q54 242 77 242 H223 Q246 242 248 218 C250 195 243 173 230 155 L257 136 Q276 121 262 101 Q250 84 223 91 L198 119 L177 104 C211 103 228 82 216 61 C204 42 181 42 150 72 Z"/>',
    '<path d="M150 60 C119 32 95 32 85 51 C73 74 91 94 126 95 H54 V276 H246 V95 H174 C209 94 227 74 215 51 C205 32 181 32 150 60 Z"/>',
    '<path d="M132 42 V27 Q132 11 150 11 Q168 11 168 27 V42 L261 123 V274 H39 V123 Z"/>',
    '<path d="M132 47 V30 Q132 13 150 13 Q168 13 168 30 V47 C222 57 257 101 257 159 C257 202 238 232 215 250 L230 283 H70 L85 250 C62 232 43 202 43 159 C43 101 78 57 132 47 Z"/>',
    '<path d="M132 43 V28 Q132 12 150 12 Q168 12 168 28 V43 L247 82 V178 Q247 235 150 280 Q53 235 53 178 V82 Z"/>',
    '<path d="M132 45 V29 Q132 13 150 13 Q168 13 168 29 V45 C222 54 257 96 257 153 C257 219 210 271 150 271 C90 271 43 219 43 153 C43 96 78 54 132 45 Z"/>',
]

SPECS = [
    ("sedan-front", "Седан — вид спереди", 150, 29, "gNavy"),
    ("suv-side", "SUV — профиль", 150, 35, "gSteel"),
    ("sport-coupe", "Спорткупе", 150, 37, "gNavy"),
    ("electric-crossover", "Электрокроссовер", 150, 30, "gBlue"),
    ("key-fob", "Брелок ключа", 146, 28, "gNavy"),
    ("classic-key", "Ключ", 148, 30, "gSteel"),
    ("alloy-wheel", "Легкосплавный диск", 150, 29, "gNavy"),
    ("winter-tire", "Колесо", 150, 29, "gSteel"),
    ("speedometer", "Приборная панель", 150, 29, "gNavy"),
    ("steering-wheel", "Рулевое колесо", 150, 29, "gBlue"),
    ("delivery-car", "Выдача автомобиля", 150, 84, "gNavy"),
    ("gift-and-key", "Подарок и ключ", 150, 74, "gBlue"),
    ("showroom", "Фасад автосалона", 150, 28, "gNavy"),
    ("car-snow-globe", "Снежный шар с автомобилем", 150, 30, "gBlue"),
    ("route-shield", "Маршрутный шильд", 150, 29, "gNavy"),
    ("tread-bauble", "Шар с протектором", 150, 30, "gSteel"),
]

ORNAMENTS = [
    Ornament(index, slug, name, OUTERS[index - 1], hx, hy, gradient)
    for index, (slug, name, hx, hy, gradient) in enumerate(SPECS, 1)
]


def car_front() -> str:
    return f'''
<path d="M83 119 Q96 72 150 65 Q204 72 217 119" fill="none" stroke="{ICE}" stroke-width="7"/>
<path d="M87 122 H213 L225 198 H75 Z" fill="url(#gSteel)" stroke="{WHITE}" stroke-width="5"/>
<path d="M108 92 H192 L207 122 H93 Z" fill="{NAVY}"/>
<path d="M92 151 H126 M174 151 H208" stroke="{CYAN}" stroke-width="10" stroke-linecap="round"/>
<path d="M109 180 H191" stroke="{GRAPHITE}" stroke-width="12" stroke-linecap="round"/>
<path d="M92 217 V244 M208 217 V244" stroke="{GRAPHITE}" stroke-width="16"/>
{snowflake(55,90,19,CYAN,2.5,.55)}{snowflake(238,83,14,WHITE,2.2,.45)}'''


def car_side(sport: bool = False) -> str:
    roof = "M76 113 L112 73 H178 L218 112" if not sport else "M72 119 L118 80 H182 L226 117"
    body = "M34 121 H236 L260 143 V206 H36 L20 187 V145 Z" if not sport else "M29 126 H243 L270 144 V204 H30 L16 187 V150 Z"
    return f'''
<path d="{roof}" fill="none" stroke="{ICE}" stroke-width="8" stroke-linejoin="round"/>
<path d="{body}" fill="url(#gBlue)" stroke="{WHITE}" stroke-width="5" stroke-linejoin="round"/>
<path d="M107 84 H174 L203 117 H80 Z" fill="{NAVY}" opacity=".92"/>
<circle cx="80" cy="210" r="29" fill="{GRAPHITE}" stroke="{SILVER}" stroke-width="7"/><circle cx="202" cy="210" r="29" fill="{GRAPHITE}" stroke="{SILVER}" stroke-width="7"/>
<circle cx="80" cy="210" r="10" fill="{CYAN}"/><circle cx="202" cy="210" r="10" fill="{CYAN}"/>
<path d="M42 150 H76 M229 150 H259" stroke="{CYAN}" stroke-width="9" stroke-linecap="round"/>
<path d="M22 178 H260" stroke="{WHITE}" stroke-width="3" opacity=".58"/>
{snowflake(54,76,14,WHITE,2.3,.5)}'''


def ornament_art(index: int) -> str:
    art = {
        1: car_front(),
        2: car_side(False),
        3: car_side(True),
        4: f'''
<circle cx="150" cy="153" r="94" fill="url(#gNavy)" stroke="{ICE}" stroke-width="5"/>
<path d="M71 178 Q94 133 154 126 Q209 129 230 171 L218 205 H81 Z" fill="url(#gSteel)" stroke="{WHITE}" stroke-width="5"/>
<path d="M103 139 H180 L204 170 H85 Z" fill="{NAVY}"/>
<circle cx="105" cy="204" r="20" fill="{GRAPHITE}" stroke="{CYAN}" stroke-width="5"/><circle cx="202" cy="204" r="20" fill="{GRAPHITE}" stroke="{CYAN}" stroke-width="5"/>
<path d="M69 114 C46 106 43 78 62 68 C80 58 99 70 98 88 C97 103 82 111 69 114 Z M62 68 L46 48" fill="none" stroke="{CYAN}" stroke-width="7" stroke-linecap="round"/>
<path d="M43 43 H55 V55" fill="none" stroke="{CYAN}" stroke-width="5"/>
{winter_dots()}''',
        5: f'''
<rect x="82" y="70" width="136" height="183" rx="48" fill="url(#gNavy)" stroke="{WHITE}" stroke-width="6"/>
<path d="M103 111 H197 M103 141 H197 M103 213 H197" stroke="{SILVER}" stroke-width="5" stroke-linecap="round"/>
<circle cx="112" cy="126" r="8" fill="{CYAN}"/><circle cx="188" cy="126" r="8" fill="{GOLD}"/>
<path d="M115 238 Q150 254 185 238" fill="none" stroke="{CYAN}" stroke-width="5"/>
{snowflake(150,181,24,ICE,3,.55)}''',
        6: f'''
<circle cx="119" cy="116" r="59" fill="url(#gNavy)" stroke="{WHITE}" stroke-width="6"/>
<circle cx="119" cy="116" r="24" fill="none" stroke="{CYAN}" stroke-width="6"/>
<path d="M157 146 L220 209 H250 V235 H223 V258 H196 L128 190" fill="url(#gSteel)" stroke="{WHITE}" stroke-width="6" stroke-linejoin="round"/>
<path d="M174 169 L203 198 M195 154 L220 179" stroke="{BLUE}" stroke-width="5"/>
{snowflake(81,80,14,WHITE,2.4,.52)}''',
        7: f'''
<circle cx="150" cy="158" r="103" fill="{GRAPHITE}" stroke="{WHITE}" stroke-width="7"/>
<circle cx="150" cy="158" r="82" fill="url(#gSteel)" stroke="{CYAN}" stroke-width="4"/>
<g fill="{NAVY}" stroke="{ICE}" stroke-width="3">
  <path d="M150 157 L132 82 L150 67 L168 82 Z"/><path d="M150 157 L217 114 L233 130 L210 160 Z"/>
  <path d="M150 157 L196 218 L181 236 L149 184 Z"/><path d="M150 157 L103 218 L83 207 L123 169 Z"/>
  <path d="M150 157 L74 126 L81 104 L134 137 Z"/>
</g>
<circle cx="150" cy="158" r="35" fill="{GRAPHITE}" stroke="{WHITE}" stroke-width="5"/>
{snowflake(229,74,13,CYAN,2,.48)}''',
        8: f'''
<circle cx="150" cy="158" r="104" fill="{GRAPHITE}" stroke="{WHITE}" stroke-width="7"/>
<path d="M93 77 L112 101 M126 60 L136 92 M174 60 L164 92 M207 77 L188 101 M225 118 L194 129 M225 198 L194 187 M93 239 L112 215 M207 239 L188 215" stroke="{SILVER}" stroke-width="7" stroke-linecap="round"/>
<circle cx="150" cy="158" r="74" fill="url(#gSteel)" stroke="{CYAN}" stroke-width="5"/>
<path d="M150 92 V224 M84 158 H216 M103 111 L197 205 M197 111 L103 205" stroke="{NAVY}" stroke-width="8"/>
<circle cx="150" cy="158" r="33" fill="{GRAPHITE}"/>
{winter_dots()}''',
        9: f'''
<rect x="54" y="66" width="192" height="185" rx="25" fill="url(#gNavy)" stroke="{WHITE}" stroke-width="6"/>
<path d="M79 177 A71 71 0 0 1 221 177" fill="none" stroke="{SILVER}" stroke-width="13"/>
<path d="M86 177 A64 64 0 0 1 101 137 M115 119 A64 64 0 0 1 150 109 M174 114 A64 64 0 0 1 205 141" fill="none" stroke="{CYAN}" stroke-width="6"/>
<path d="M150 177 L196 128" stroke="{GOLD}" stroke-width="7" stroke-linecap="round"/>
<circle cx="150" cy="177" r="13" fill="{WHITE}"/>
{snowflake(83,86,14,WHITE,2,.45)}''',
        10: f'''
<circle cx="150" cy="158" r="102" fill="{GRAPHITE}" stroke="{WHITE}" stroke-width="7"/>
<circle cx="150" cy="158" r="75" fill="none" stroke="{SILVER}" stroke-width="17"/>
<path d="M150 159 L103 105 M150 159 L197 105 M150 159 V226" stroke="{SILVER}" stroke-width="17" stroke-linecap="round"/>
<circle cx="150" cy="159" r="39" fill="{NAVY}" stroke="{CYAN}" stroke-width="6"/>
<path d="M114 239 Q150 251 186 239" fill="none" stroke="{CYAN}" stroke-width="4"/>
{snowflake(225,82,14,WHITE,2.2,.44)}''',
        11: f'''
<path d="M79 135 Q95 86 150 78 Q205 86 221 135" fill="none" stroke="{ICE}" stroke-width="7"/>
<path d="M83 137 H217 L229 216 H71 Z" fill="url(#gSteel)" stroke="{WHITE}" stroke-width="5"/>
<path d="M103 104 H197 L209 138 H91 Z" fill="{NAVY}"/>
<path d="M96 166 H126 M174 166 H204" stroke="{CYAN}" stroke-width="9" stroke-linecap="round"/>
<path d="M150 111 C119 76 91 72 83 90 C76 108 105 122 150 113 C195 122 224 108 217 90 C209 72 181 76 150 111 Z" fill="{RED}" stroke="{WHITE}" stroke-width="5"/>
<path d="M93 224 V249 M207 224 V249" stroke="{GRAPHITE}" stroke-width="15"/>
{snowflake(56,84,15,WHITE,2.3,.5)}''',
        12: f'''
<rect x="59" y="101" width="182" height="170" rx="18" fill="url(#gBlue)" stroke="{WHITE}" stroke-width="6"/>
<path d="M150 101 V271 M59 160 H241" stroke="{GOLD}" stroke-width="15"/>
<path d="M150 95 C119 64 92 59 86 75 C81 92 107 104 150 101 C193 104 219 92 214 75 C208 59 181 64 150 95 Z" fill="url(#gGold)" stroke="{WHITE}" stroke-width="5"/>
<path d="M103 202 C77 181 79 153 101 145 C122 137 140 153 137 173 L180 216" fill="none" stroke="{ICE}" stroke-width="10"/>
<circle cx="103" cy="164" r="16" fill="{NAVY}" stroke="{WHITE}" stroke-width="5"/>
{snowflake(208,219,18,WHITE,2.5,.5)}''',
        13: f'''
<path d="M54 129 L150 49 L246 129 V266 H54 Z" fill="url(#gNavy)" stroke="{WHITE}" stroke-width="6"/>
<rect x="78" y="139" width="144" height="102" rx="8" fill="{GRAPHITE}" stroke="{SILVER}" stroke-width="5"/>
<path d="M126 139 V241 M174 139 V241" stroke="{CYAN}" stroke-width="4"/>
<path d="M62 129 Q150 102 238 129" fill="none" stroke="{ICE}" stroke-width="9"/>
<path d="M91 222 Q109 184 150 180 Q191 184 209 222" fill="none" stroke="{WHITE}" stroke-width="5"/>
<path d="M111 190 H189" stroke="{SILVER}" stroke-width="5"/>
{winter_dots()}''',
        14: f'''
<circle cx="150" cy="157" r="99" fill="#A7E7FF" opacity=".68" stroke="{WHITE}" stroke-width="7"/>
<path d="M80 246 H220 L231 281 H69 Z" fill="url(#gNavy)" stroke="{WHITE}" stroke-width="6"/>
<path d="M79 197 Q103 156 151 151 Q201 155 224 196 L213 222 H88 Z" fill="url(#gSteel)" stroke="{WHITE}" stroke-width="5"/>
<circle cx="112" cy="219" r="17" fill="{GRAPHITE}"/><circle cx="196" cy="219" r="17" fill="{GRAPHITE}"/>
<path d="M104 170 H186 L207 198 H84 Z" fill="{NAVY}"/>
<circle cx="91" cy="99" r="6" fill="{WHITE}"/><circle cx="205" cy="119" r="5" fill="{WHITE}"/><circle cx="72" cy="157" r="4" fill="{WHITE}"/>''',
        15: f'''
<path d="M74 94 L150 59 L226 94 V178 Q226 222 150 258 Q74 222 74 178 Z" fill="url(#gNavy)" stroke="{WHITE}" stroke-width="6"/>
<path d="M98 132 H130 L151 112 L174 151 H205" fill="none" stroke="{CYAN}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>
<circle cx="98" cy="132" r="8" fill="{WHITE}"/><circle cx="205" cy="151" r="8" fill="{GOLD}"/>
<path d="M97 204 H203" stroke="{SILVER}" stroke-width="5" stroke-dasharray="5 8"/>
{snowflake(205,91,14,WHITE,2.2,.45)}''',
        16: f'''
<circle cx="150" cy="157" r="105" fill="url(#gSteel)" stroke="{WHITE}" stroke-width="7"/>
<path d="M76 84 L101 112 M114 59 L128 96 M164 57 L153 96 M209 81 L185 112 M231 126 L194 140 M229 190 L194 179 M82 224 L108 201 M207 229 L184 204" stroke="{NAVY}" stroke-width="10" stroke-linecap="round"/>
<path d="M92 73 L114 99 M187 67 L166 99 M73 161 H108 M192 159 H227 M103 236 L122 208 M181 237 L163 207" stroke="{BLUE}" stroke-width="5" stroke-linecap="round"/>
<circle cx="150" cy="157" r="48" fill="{NAVY}" stroke="{CYAN}" stroke-width="5"/>
{snowflake(150,157,27,WHITE,3,.52)}''',
    }
    return art[index]


def logo_zone(index: int) -> str:
    zones = {
        1: '<rect x="117" y="194" width="66" height="25" rx="5"/>',
        2: '<rect x="127" y="139" width="68" height="31" rx="6"/>',
        3: '<rect x="126" y="142" width="70" height="30" rx="6"/>',
        4: '<rect x="125" y="174" width="64" height="28" rx="6"/>',
        5: '<path d="M150 151 L185 169 V209 Q185 228 150 244 Q115 228 115 209 V169 Z"/>',
        6: '<circle cx="119" cy="116" r="26"/>',
        7: '<circle cx="150" cy="158" r="25"/>',
        8: '<circle cx="150" cy="158" r="25"/>',
        9: '<rect x="113" y="195" width="74" height="34" rx="8"/>',
        10: '<circle cx="150" cy="159" r="28"/>',
        11: '<rect x="117" y="190" width="66" height="25" rx="5"/>',
        12: '<rect x="172" y="196" width="51" height="38" rx="6" transform="rotate(-12 197.5 215)"/>',
        13: '<rect x="93" y="103" width="114" height="26" rx="5"/>',
        14: '<rect x="106" y="252" width="88" height="22" rx="5"/>',
        15: '<rect x="102" y="160" width="96" height="39" rx="10"/>',
        16: '<rect x="111" y="139" width="78" height="38" rx="9"/>',
    }
    return zones[index]


def print_body(ornament: Ornament) -> str:
    outer = style_shape(
        ornament.outer,
        f'fill="url(#{ornament.gradient})" stroke="{WHITE}" stroke-width="7" stroke-linejoin="round" stroke-linecap="round"',
    )
    return f'''
<defs><clipPath id="{ornament.clip_id}">{ornament.outer}</clipPath></defs>
{outer}
<g clip-path="url(#{ornament.clip_id})">{ornament_art(ornament.index)}</g>
<circle cx="{ornament.hole_x}" cy="{ornament.hole_y}" r="7" fill="{MIDNIGHT}" stroke="{WHITE}" stroke-width="3"/>
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
        f'<g id="logo-zone-{ornament.index:02d}" data-client-logo-zone="true" transform="{transform}" fill="{WHITE}" stroke="{STEEL}" stroke-width="2.5">{logo_zone(ornament.index)}</g>'
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
<title>Premium automotive New Year ornaments — 16-piece dealership sheet</title>
{DEFS}
{layers}
</svg>''')
OUTPUT.write_text(svg, encoding="utf-8")
ET.parse(OUTPUT)
print(OUTPUT)
