#!/usr/bin/env python3
"""Build one 4×4 production SVG sheet of candy-cartoon Christmas ornaments."""
from __future__ import annotations

from dataclasses import dataclass
from math import cos, pi, sin
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "new-year-cartoon-candy-ornaments-16.svg"

WHITE = "#FFFFFF"
CREAM = "#FFF5DE"
DARK = "#38234C"
BROWN = "#B96A38"
COOKIE = "#D9904F"
RED = "#F04465"
CORAL = "#FF6F61"
PINK = "#FF8BCB"
YELLOW = "#FFD84D"
MINT = "#66E3B4"
TEAL = "#23BDD2"
BLUE = "#4A8DFF"
PURPLE = "#8F62E8"
CUT = "#FF00FF"

DEFS = f"""
<defs>
  <linearGradient id="gCookie" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#F6BC71"/><stop offset="1" stop-color="{COOKIE}"/>
  </linearGradient>
  <linearGradient id="gRed" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#FF7D86"/><stop offset="1" stop-color="{RED}"/>
  </linearGradient>
  <linearGradient id="gPink" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#FFC1E3"/><stop offset="1" stop-color="{PINK}"/>
  </linearGradient>
  <linearGradient id="gMint" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#B9FFE1"/><stop offset="1" stop-color="{MINT}"/>
  </linearGradient>
  <linearGradient id="gBlue" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#9DDCFF"/><stop offset="1" stop-color="{BLUE}"/>
  </linearGradient>
  <linearGradient id="gPurple" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#D3B3FF"/><stop offset="1" stop-color="{PURPLE}"/>
  </linearGradient>
  <radialGradient id="gCream" cx="35%" cy="28%" r="80%">
    <stop offset="0" stop-color="{WHITE}"/><stop offset="1" stop-color="{CREAM}"/>
  </radialGradient>
</defs>
"""


@dataclass(frozen=True)
class Toy:
    index: int
    slug: str
    name_ru: str
    outer: str
    hole_x: float
    hole_y: float
    gradient: str

    @property
    def clip_id(self) -> str:
        return f"candyClip{self.index:02d}"


def clean(content: str) -> str:
    return "\n".join(line.rstrip() for line in content.splitlines()) + "\n"


def star_points(cx: float, cy: float, outer: float, inner: float, count: int = 5) -> str:
    result: list[str] = []
    for i in range(count * 2):
        radius = outer if i % 2 == 0 else inner
        angle = -pi / 2 + i * pi / count
        result.append(f"{cx + radius * cos(angle):.2f},{cy + radius * sin(angle):.2f}")
    return " ".join(result)


def style_shape(shape: str, attributes: str) -> str:
    return shape[:-2] + " " + attributes + "/>"


def face(cx: float, cy: float, scale: float = 1.0, smile: bool = True) -> str:
    mouth = (
        f'<path d="M{cx-18*scale:.2f} {cy+20*scale:.2f} Q{cx:.2f} {cy+37*scale:.2f} {cx+18*scale:.2f} {cy+20*scale:.2f}" fill="none" stroke="{DARK}" stroke-width="{5*scale:.2f}" stroke-linecap="round"/>'
        if smile
        else f'<ellipse cx="{cx}" cy="{cy+25*scale:.2f}" rx="{13*scale:.2f}" ry="{9*scale:.2f}" fill="{DARK}"/>'
    )
    return f'''
<g>
  <ellipse cx="{cx-31*scale:.2f}" cy="{cy+16*scale:.2f}" rx="{15*scale:.2f}" ry="{8*scale:.2f}" fill="{PINK}" opacity=".58"/>
  <ellipse cx="{cx+31*scale:.2f}" cy="{cy+16*scale:.2f}" rx="{15*scale:.2f}" ry="{8*scale:.2f}" fill="{PINK}" opacity=".58"/>
  <ellipse cx="{cx-25*scale:.2f}" cy="{cy-5*scale:.2f}" rx="{8*scale:.2f}" ry="{11*scale:.2f}" fill="{DARK}"/>
  <ellipse cx="{cx+25*scale:.2f}" cy="{cy-5*scale:.2f}" rx="{8*scale:.2f}" ry="{11*scale:.2f}" fill="{DARK}"/>
  <circle cx="{cx-22*scale:.2f}" cy="{cy-9*scale:.2f}" r="{2.8*scale:.2f}" fill="{WHITE}"/>
  <circle cx="{cx+28*scale:.2f}" cy="{cy-9*scale:.2f}" r="{2.8*scale:.2f}" fill="{WHITE}"/>
  {mouth}
</g>'''


def shine(x: float, y: float, width: float = 54, height: float = 18, rotate: float = -28) -> str:
    return f'<ellipse cx="{x}" cy="{y}" rx="{width/2}" ry="{height/2}" fill="{WHITE}" opacity=".48" transform="rotate({rotate} {x} {y})"/>'


def sprinkles() -> str:
    items = [
        (105, 107, RED, -25), (142, 88, TEAL, 18), (184, 109, YELLOW, -15),
        (91, 145, PURPLE, 28), (158, 142, WHITE, -30), (205, 153, MINT, 22),
        (119, 184, YELLOW, 12), (181, 192, RED, -18),
    ]
    return "".join(
        f'<rect x="{x-8}" y="{y-2.5}" width="16" height="5" rx="2.5" fill="{color}" transform="rotate({angle} {x} {y})"/>'
        for x, y, color, angle in items
    )


OUTERS = [
    '<path d="M150 26 C122 26 108 44 109 66 C110 82 119 92 128 98 L106 110 L67 88 Q51 80 42 95 Q34 111 50 122 L100 153 L94 186 L70 238 Q62 255 77 264 Q93 273 104 257 L137 215 H163 L196 257 Q207 273 223 264 Q238 255 230 238 L206 186 L200 153 L250 122 Q266 111 258 95 Q249 80 233 88 L194 110 L172 98 Q190 86 191 66 C192 44 178 26 150 26 Z"/>',
    '<path d="M80 270 V110 C80 58 111 28 155 28 C202 28 231 62 231 105 C231 139 214 161 190 181 L156 143 C173 129 183 119 183 103 C183 84 171 72 154 72 C135 72 123 87 123 110 V270 Z"/>',
    '<path d="M120 46 V18 H180 V46 H198 V75 H179 C198 88 210 108 210 130 C210 150 202 166 189 178 C216 193 232 219 232 247 C232 267 216 278 196 278 H104 C84 278 68 267 68 247 C68 219 84 193 111 178 C98 166 90 150 90 130 C90 108 102 88 121 75 H102 V46 Z"/>',
    '<path d="M50 80 C50 62 64 49 82 49 C95 26 120 15 151 20 C190 25 221 48 232 82 C252 85 264 102 260 119 C257 135 243 144 227 143 C231 158 229 176 222 191 C233 206 238 225 233 244 C228 268 207 282 183 276 L150 266 L117 276 C93 282 72 268 67 244 C62 225 67 206 78 191 C71 176 69 158 73 143 C57 144 43 135 40 119 C36 102 48 85 68 82 Z"/>',
    '<path d="M130 62 V46 L105 21 L96 31 L111 52 L82 37 L73 51 L104 72 C83 92 72 121 76 153 C80 194 105 233 150 267 C195 233 220 194 224 153 C228 121 217 92 196 72 L227 51 L218 37 L189 52 L204 31 L195 21 L170 46 V62 Z"/>',
    '<path d="M132 54 V34 Q132 18 150 18 Q168 18 168 34 V54 C210 62 231 111 225 166 L258 194 L232 228 L207 211 C194 251 174 278 150 278 C126 278 106 251 93 211 L68 228 L42 194 L75 166 C69 111 90 62 132 54 Z"/>',
    '<path d="M150 22 L110 76 H127 L84 132 H108 L55 201 H126 V225 H112 V278 H188 V225 H174 L245 201 L192 132 H216 L173 76 H190 Z"/>',
    '<path d="M150 62 C119 34 95 34 85 53 C73 76 91 96 126 97 H54 V276 H246 V97 H174 C209 96 227 76 215 53 C205 34 181 34 150 62 Z"/>',
    '<path d="M82 144 C56 139 50 119 64 102 C75 88 92 88 104 94 C105 71 124 54 148 58 C169 39 206 50 210 79 C232 83 244 100 238 120 C233 137 218 145 200 144 L224 262 H76 L100 144 Z"/>',
    '<path d="M132 38 V25 Q132 12 150 12 Q168 12 168 25 V38 C214 47 242 75 242 118 C242 163 214 197 174 208 V278 H126 V208 C86 197 58 163 58 118 C58 75 86 47 132 38 Z"/>',
    '<path d="M118 48 V31 Q118 15 136 15 Q154 15 154 31 V85 L174 55 Q190 42 205 55 Q219 68 208 84 L180 118 V225 Q180 272 132 276 Q79 280 58 233 L31 173 Q24 156 39 146 Q55 135 68 150 L88 176 V48 Z"/>',
    '<path d="M100 60 V17 Q100 5 112 5 H188 Q200 5 200 17 V60 H184 V168 Q184 204 214 221 Q248 240 235 266 Q224 286 196 278 L146 263 Q98 249 98 199 V60 Z"/>',
    '<path d="M132 48 V31 Q132 14 150 14 Q168 14 168 31 V48 C223 57 258 101 258 159 C258 201 239 231 216 249 L231 284 H69 L84 249 C61 231 42 201 42 159 C42 101 77 57 132 48 Z"/>',
    f'<polygon points="{star_points(150,157,130,60,5)}"/>',
    '<path d="M130 55 V37 Q130 20 150 20 Q170 20 170 37 V55 C195 61 215 83 214 110 H229 Q267 110 267 160 Q267 210 229 210 H214 V242 Q214 270 186 270 H96 Q68 270 68 242 V110 H86 C85 83 105 61 130 55 Z"/>',
    '<path d="M130 53 V34 Q130 16 150 16 Q170 16 170 34 V53 C213 61 229 102 228 159 C228 194 244 218 259 232 H178 Q172 271 150 271 Q128 271 122 232 H41 C56 218 72 194 72 159 C71 102 87 61 130 53 Z"/>',
]

SPECS = [
    ("gingerbread", "Пряничный человечек", 150, 52, "gCookie"),
    ("candy-cane", "Леденец", 155, 52, "gRed"),
    ("snowman", "Снеговик", 150, 33, "gBlue"),
    ("santa", "Санта", 150, 45, "gRed"),
    ("reindeer", "Олень", 150, 57, "gCookie"),
    ("penguin", "Пингвин", 150, 35, "gPurple"),
    ("christmas-tree", "Ёлка", 150, 49, "gMint"),
    ("gift", "Подарок", 150, 76, "gBlue"),
    ("cupcake", "Капкейк", 150, 77, "gPink"),
    ("lollipop", "Леденец на палочке", 150, 46, "gPurple"),
    ("mitten", "Варежка", 136, 32, "gPink"),
    ("stocking", "Носок", 150, 34, "gRed"),
    ("snow-globe", "Снежный шар", 150, 31, "gBlue"),
    ("smiling-star", "Улыбающаяся звезда", 150, 57, "gMint"),
    ("cocoa-mug", "Какао", 150, 42, "gPink"),
    ("jingle-bell", "Колокольчик", 150, 33, "gRed"),
]

TOYS = [Toy(index, slug, name, OUTERS[index - 1], hx, hy, gradient) for index, (slug, name, hx, hy, gradient) in enumerate(SPECS, 1)]


def toy_art(index: int) -> str:
    art = {
        1: f'''
{face(150,100,.82)}
<path d="M106 151 Q150 176 194 151" fill="none" stroke="{WHITE}" stroke-width="10" stroke-linecap="round"/>
<path d="M86 112 L68 101 M214 112 L232 101 M100 214 L86 245 M200 214 L214 245" stroke="{WHITE}" stroke-width="10" stroke-linecap="round"/>
<circle cx="150" cy="176" r="9" fill="{RED}"/><circle cx="150" cy="204" r="9" fill="{MINT}"/>
{shine(127,54,45,13,-25)}''',
        2: f'''
<g stroke="{WHITE}" stroke-width="17" opacity=".88">
  <path d="M93 106 L122 121 M89 151 L122 166 M90 198 L122 213"/>
  <path d="M150 52 L174 78 M190 65 L211 91 M171 139 L196 160"/>
</g>
{face(103,186,.62)}
{shine(133,52,40,12,-30)}''',
        3: f'''
<ellipse cx="150" cy="132" rx="57" ry="53" fill="url(#gCream)" stroke="{WHITE}" stroke-width="6"/>
<path d="M103 79 H197" stroke="{DARK}" stroke-width="9" stroke-linecap="round"/>
<path d="M118 191 Q150 209 182 191" fill="none" stroke="{MINT}" stroke-width="12"/>
{face(150,128,.75)}
<circle cx="150" cy="150" r="7" fill="{CORAL}"/>
<circle cx="109" cy="224" r="7" fill="{WHITE}" opacity=".65"/><circle cx="189" cy="241" r="6" fill="{WHITE}" opacity=".65"/>''',
        4: f'''
<path d="M76 84 Q150 42 228 91 L219 127 Q150 102 81 130 Z" fill="{RED}" stroke="{WHITE}" stroke-width="7"/>
<ellipse cx="150" cy="147" rx="67" ry="61" fill="#FFD1B3"/>
<path d="M88 174 Q150 241 212 174 Q211 248 150 266 Q89 248 88 174 Z" fill="url(#gCream)"/>
{face(150,143,.72)}
<ellipse cx="150" cy="169" rx="10" ry="7" fill="{CORAL}"/>
<circle cx="231" cy="102" r="19" fill="{WHITE}"/>{shine(112,66,52,14,-20)}''',
        5: f'''
<ellipse cx="150" cy="140" rx="71" ry="76" fill="#E79C52"/>
<path d="M104 90 L86 60 M196 90 L214 60" stroke="{BROWN}" stroke-width="13" stroke-linecap="round"/>
<ellipse cx="150" cy="177" rx="48" ry="39" fill="#F6C985"/>
{face(150,139,.75)}
<ellipse cx="150" cy="168" rx="15" ry="11" fill="{RED}"/>
<path d="M135 190 Q150 202 165 190" fill="none" stroke="{DARK}" stroke-width="5"/>
<circle cx="108" cy="118" r="7" fill="{CREAM}"/><circle cx="192" cy="118" r="7" fill="{CREAM}"/>''',
        6: f'''
<ellipse cx="150" cy="157" rx="69" ry="104" fill="{DARK}"/>
<ellipse cx="150" cy="172" rx="48" ry="70" fill="url(#gCream)"/>
<path d="M93 186 L64 203 M207 186 L236 203" stroke="{PURPLE}" stroke-width="18" stroke-linecap="round"/>
<path d="M116 256 L91 270 M184 256 L209 270" stroke="{YELLOW}" stroke-width="14" stroke-linecap="round"/>
{face(150,154,.72)}
<path d="M140 175 L150 185 L160 175" fill="{YELLOW}" stroke="{YELLOW}" stroke-width="5"/>
{shine(126,78,45,12,-28)}''',
        7: f'''
<path d="M150 63 L119 111 H135 L98 158 H121 L79 207 H221 L179 158 H202 L165 111 H181 Z" fill="#42C996" stroke="{WHITE}" stroke-width="6"/>
<path d="M112 124 Q150 141 188 124 M94 176 Q150 197 206 176" fill="none" stroke="{PINK}" stroke-width="9" stroke-linecap="round"/>
<circle cx="128" cy="104" r="8" fill="{YELLOW}"/><circle cx="177" cy="150" r="8" fill="{RED}"/><circle cx="122" cy="184" r="8" fill="{BLUE}"/>
{face(150,187,.64)}
<polygon points="{star_points(150,53,18,8,5)}" fill="{YELLOW}"/>''',
        8: f'''
<rect x="59" y="101" width="182" height="170" rx="18" fill="url(#gBlue)"/>
<path d="M150 101 V271 M59 160 H241" stroke="{WHITE}" stroke-width="15"/>
<path d="M150 95 C119 64 92 59 86 75 C81 92 107 104 150 101 C193 104 219 92 214 75 C208 59 181 64 150 95 Z" fill="{PINK}" stroke="{WHITE}" stroke-width="6"/>
{face(105,207,.58)}
<circle cx="199" cy="210" r="12" fill="{YELLOW}"/><circle cx="219" cy="190" r="9" fill="{MINT}"/>{shine(98,123,38,12,-20)}''',
        9: f'''
<path d="M81 145 H219 L204 255 H96 Z" fill="url(#gPurple)" stroke="{WHITE}" stroke-width="6"/>
<path d="M76 139 C54 126 58 105 76 98 C89 92 101 99 106 108 C107 84 126 68 149 70 C169 51 200 61 204 85 C225 88 237 104 232 121 C228 137 212 144 195 139 Z" fill="url(#gPink)"/>
{sprinkles()}
{face(150,187,.68)}
<circle cx="150" cy="69" r="13" fill="{RED}"/>{shine(123,92,43,13,-24)}''',
        10: f'''
<circle cx="150" cy="117" r="83" fill="url(#gPurple)"/>
<path d="M99 67 Q150 104 201 67 M79 110 Q150 151 221 110 M92 161 Q150 190 208 161" fill="none" stroke="{WHITE}" stroke-width="11" opacity=".82"/>
<rect x="132" y="196" width="36" height="82" rx="16" fill="{MINT}"/>
{face(150,127,.70)}
{shine(116,72,50,16,-25)}''',
        11: f'''
<path d="M91 61 H154 V91 L178 67 Q190 57 200 66 Q211 76 202 88 L178 116 V226 Q178 261 142 267 Q103 274 86 239 L55 174 Q49 162 59 156 Q70 149 80 161 L96 181 Z" fill="url(#gPink)"/>
<path d="M93 77 H152" stroke="{WHITE}" stroke-width="12"/>
<circle cx="121" cy="127" r="12" fill="{YELLOW}"/><circle cx="145" cy="157" r="10" fill="{MINT}"/>
{face(128,202,.58)}
{shine(111,91,38,11,-20)}''',
        12: f'''
<path d="M101 59 H199 V105 H184 V171 Q184 205 214 222 Q239 236 229 257 Q220 274 198 268 L148 253 Q105 240 105 198 V105 H101 Z" fill="url(#gRed)"/>
<path d="M104 82 H196" stroke="{WHITE}" stroke-width="17"/>
<path d="M116 139 H183 M120 171 H181" stroke="{MINT}" stroke-width="8" stroke-linecap="round"/>
{face(153,218,.58)}
{shine(127,114,45,12,-22)}''',
        13: f'''
<circle cx="150" cy="153" r="99" fill="#8EE8FF" opacity=".72" stroke="{WHITE}" stroke-width="7"/>
<path d="M82 246 H218 L229 280 H71 Z" fill="url(#gPurple)" stroke="{WHITE}" stroke-width="6"/>
<path d="M150 97 L124 136 H137 L105 177 H195 L163 136 H176 Z" fill="{MINT}" stroke="{WHITE}" stroke-width="5"/>
<circle cx="112" cy="111" r="6" fill="{WHITE}"/><circle cx="194" cy="137" r="5" fill="{WHITE}"/><circle cx="92" cy="174" r="5" fill="{WHITE}"/>
{face(150,205,.58)}
{shine(112,86,46,14,-24)}''',
        14: f'''
<polygon points="{star_points(150,157,123,56,5)}" fill="url(#gMint)"/>
{face(150,160,.85)}
<circle cx="104" cy="126" r="8" fill="{YELLOW}"/><circle cx="198" cy="121" r="8" fill="{PINK}"/>
{shine(117,80,52,14,-22)}''',
        15: f'''
<path d="M74 114 H215 V242 Q215 267 190 267 H99 Q74 267 74 242 Z" fill="url(#gPink)"/>
<path d="M213 139 H232 Q258 139 258 174 Q258 209 232 209 H214" fill="none" stroke="{PURPLE}" stroke-width="17"/>
<path d="M104 104 Q92 81 116 67 Q111 42 137 35 Q150 18 165 35 Q191 42 184 67 Q209 82 196 104 Z" fill="url(#gCream)"/>
<circle cx="121" cy="79" r="10" fill="#FFFFFF"/><circle cx="154" cy="62" r="10" fill="#FFFFFF"/><circle cx="181" cy="84" r="9" fill="#FFFFFF"/>
{face(145,188,.70)}
{shine(106,130,45,13,-20)}''',
        16: f'''
<path d="M150 54 C107 54 89 92 90 151 C91 190 73 215 59 228 H241 C227 215 209 190 210 151 C211 92 193 54 150 54 Z" fill="url(#gRed)"/>
<path d="M76 203 Q150 231 224 203" fill="none" stroke="{WHITE}" stroke-width="13"/>
<circle cx="150" cy="242" r="24" fill="{YELLOW}" stroke="{WHITE}" stroke-width="6"/>
{face(150,141,.76)}
<path d="M102 108 Q150 83 198 108" fill="none" stroke="{PINK}" stroke-width="8"/>
{shine(118,78,44,12,-23)}''',
    }
    return art[index]


def toy_body(toy: Toy) -> str:
    outer_print = style_shape(
        toy.outer,
        f'fill="url(#{toy.gradient})" stroke="{WHITE}" stroke-width="8" stroke-linejoin="round" stroke-linecap="round"',
    )
    return f'''
<defs><clipPath id="{toy.clip_id}">{toy.outer}</clipPath></defs>
{outer_print}
<g clip-path="url(#{toy.clip_id})">
  {toy_art(toy.index)}
</g>
<circle cx="{toy.hole_x}" cy="{toy.hole_y}" r="7" fill="{DARK}" stroke="{WHITE}" stroke-width="3"/>
'''


def cut_geometry(toy: Toy) -> str:
    return toy.outer + f'<circle cx="{toy.hole_x}" cy="{toy.hole_y}" r="4" data-purpose="hanging-hole"/>'


print_groups: list[str] = []
cut_groups: list[str] = []
for idx, toy in enumerate(TOYS):
    col, row = idx % 4, idx // 4
    x, y = col * 300, row * 300
    print_groups.append(
        f'<g id="toy-{toy.index:02d}-{toy.slug}" inkscape:label="{toy.index:02d} {toy.name_ru}" transform="translate({x} {y})">{toy_body(toy)}</g>'
    )
    cut_groups.append(
        f'<g id="cut-{toy.index:02d}-{toy.slug}" transform="translate({x} {y})">{cut_geometry(toy)}</g>'
    )

layers = (
    '<g inkscape:groupmode="layer" inkscape:label="PRINT" id="PRINT">'
    + "".join(print_groups)
    + '</g>'
    + f'<g inkscape:groupmode="layer" inkscape:label="CutContour" id="CutContour" fill="none" stroke="{CUT}" stroke-width="0.3mm" stroke-linejoin="round" stroke-linecap="round" vector-effect="non-scaling-stroke" data-spot-color="CutContour">'
    + "".join(cut_groups)
    + '</g>'
)

svg = clean(f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" width="1200mm" height="1200mm" viewBox="0 0 1200 1200">
<title>Candy cartoon Christmas ornaments — 16-piece production sheet</title>
{DEFS}
{layers}
</svg>''')
OUTPUT.write_text(svg, encoding="utf-8")
ET.parse(OUTPUT)
print(OUTPUT)
