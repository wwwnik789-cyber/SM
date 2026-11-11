#!/usr/bin/env python3
"""Build the ANIKOM ARENA zone map: 7 zones, 27 manufacturing positions."""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import resvg_py

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
sys.path.insert(0, str(REPO / "banners" / "anikom-arena-3000x2500-concepts"))

from build_concepts import FontOutliner  # noqa: E402

FONT = REPO / "banners" / "anikom-arena-3000x2500-concepts" / "source" / "Montserrat-Variable.ttf"
SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)

W, H = 1587, 1122

BG = "#F4F1EA"
INK = "#081A2B"
MUTED = "#7C8894"
LINE = "#CFC7B9"
PITCH = "#DCE5D7"
BUILDING = "#E9E3D7"
STAND = "#E0D6C6"
CORAL = "#D94A43"
PLUM = "#2C222E"
WHITE = "#FFFFFF"


def tag(name: str) -> str:
    return f"{{{SVG_NS}}}{name}"


def add_rect(parent, x, y, w, h, fill, *, stroke=None, sw=1, rx=0, dash=None, opacity=1.0):
    attrs = {
        "x": f"{x:g}",
        "y": f"{y:g}",
        "width": f"{w:g}",
        "height": f"{h:g}",
        "fill": fill,
        "opacity": f"{opacity:g}",
    }
    if rx:
        attrs["rx"] = f"{rx:g}"
    if stroke:
        attrs["stroke"] = stroke
        attrs["stroke-width"] = f"{sw:g}"
    if dash:
        attrs["stroke-dasharray"] = dash
    return ET.SubElement(parent, tag("rect"), attrs)


def add_line(parent, x1, y1, x2, y2, stroke, sw=1, dash=None, opacity=1.0):
    attrs = {
        "x1": f"{x1:g}",
        "y1": f"{y1:g}",
        "x2": f"{x2:g}",
        "y2": f"{y2:g}",
        "stroke": stroke,
        "stroke-width": f"{sw:g}",
        "opacity": f"{opacity:g}",
    }
    if dash:
        attrs["stroke-dasharray"] = dash
    return ET.SubElement(parent, tag("line"), attrs)


def add_circle(parent, cx, cy, r, fill, *, stroke=None, sw=1):
    attrs = {"cx": f"{cx:g}", "cy": f"{cy:g}", "r": f"{r:g}", "fill": fill}
    if stroke:
        attrs["stroke"] = stroke
        attrs["stroke-width"] = f"{sw:g}"
    return ET.SubElement(parent, tag("circle"), attrs)


class Sheet:
    def __init__(self) -> None:
        self.outliner = FontOutliner(FONT)
        self.root = ET.Element(
            tag("svg"),
            {
                "version": "1.1",
                "width": f"{W}",
                "height": f"{H}",
                "viewBox": f"0 0 {W} {H}",
            },
        )
        title = ET.SubElement(self.root, tag("title"))
        title.text = "АНИКОМ АРЕНА — карта носителей"
        desc = ET.SubElement(self.root, tag("desc"))
        desc.text = "Схема размещения 27 позиций брендирования по 7 зонам арены."
        self.body = ET.SubElement(self.root, tag("g"), {"id": "SHEET"})
        add_rect(self.body, 0, 0, W, H, BG)

    def text(self, content, x, y, size, *, fill=INK, weight=500, align="left",
             tracking=10, width=1000, opacity=1.0):
        return self.outliner.add_text(
            self.body,
            content,
            x=x,
            baseline=y,
            cap_height=size,
            max_width=width,
            weight=weight,
            tracking=tracking,
            fill=fill,
            align=align,
            opacity=opacity,
        )

    def rule(self, x1, y, x2, color=LINE, sw=1):
        add_line(self.body, x1, y, x2, y, color, sw)

    def save(self):
        tree = ET.ElementTree(self.root)
        svg_path = ROOT / "arena-zone-map.svg"
        tree.write(svg_path, encoding="utf-8", xml_declaration=True)
        png = resvg_py.svg_to_bytes(svg_path=str(svg_path), width=W * 2, height=H * 2)
        (ROOT / "arena-zone-map.png").write_bytes(bytes(png))
        return svg_path


def header(s: Sheet) -> None:
    s.text("АНИКОМ АРЕНА", 40, 74, 30, weight=820, tracking=18)
    s.text("КАРТА НОСИТЕЛЕЙ", 40, 106, 12, fill=CORAL, weight=700, tracking=90)
    s.text("27 позиций · 7 зон · 3 волны внедрения", 520, 104, 11, fill=MUTED, weight=500)
    s.text("SM PRODUCTION", 1547, 62, 12, weight=700, align="right", tracking=40)
    s.text("предложение по расширению", 1547, 86, 9, fill=MUTED, weight=500, align="right")
    s.rule(40, 120, 1547)


def footer(s: Sheet) -> None:
    s.rule(40, 1092, 1547, LINE, 1)
    s.text("Схема без масштаба: пропорции условные, размеры уточняются обмером.", 40, 1112, 8, fill=MUTED)
    s.text("Документ дополняет баннеры 3000×2500, ПВХ-навигацию и пресс-воллы.", 1547, 1112, 8,
           fill=MUTED, align="right")


def plan(s: Sheet) -> None:
    add_rect(s.body, 40, 140, 900, 742, WHITE, stroke=LINE, sw=1, rx=8)
    s.text("СХЕМА ЗОН", 64, 174, 9, fill=MUTED, weight=650, tracking=54)

    # Administrative and household building
    add_rect(s.body, 254, 190, 572, 118, BUILDING, stroke=LINE, sw=1, rx=4)
    for x in (470, 650):
        add_line(s.body, x, 190, x, 308, LINE, 1)
    s.text("РЕСЕПШЕН · КАФЕ", 296, 232, 10, weight=650, tracking=22)
    s.text("ХОЛЛ · ФОТОЗОНА", 296, 252, 7.6, fill=MUTED, tracking=18)
    s.text("4 РАЗДЕВАЛКИ", 512, 232, 10, weight=650, tracking=22)
    s.text("ШКАФЧИКИ · ДУШ", 512, 252, 7.6, fill=MUTED, tracking=14)
    s.text("VIP-ЛОЖА · 60", 700, 232, 10, weight=650, tracking=22)
    s.text("ОТДЕЛЬНЫЙ ВХОД", 700, 252, 7.6, fill=MUTED, tracking=14)
    s.text("АБК ~650 М²", 812, 296, 7.2, fill=MUTED, align="right", tracking=16)

    # Stand with a clean label chip
    add_rect(s.body, 254, 316, 572, 56, STAND, stroke=LINE, sw=1, rx=3)
    for i in range(29):
        x = 268 + i * 19
        add_line(s.body, x, 328, x, 360, "#BDB2A0", 1)
    add_rect(s.body, 330, 328, 420, 26, STAND, stroke="none", rx=2)
    s.text("ТРИБУНА · 284 МЕСТА ПОД НАВЕСОМ", 540, 345, 9, weight=650, align="center", tracking=22)

    # Pitch
    add_rect(s.body, 280, 396, 520, 315, PITCH, stroke=INK, sw=1.6, rx=1)
    add_line(s.body, 540, 396, 540, 711, INK, 1.4)
    add_circle(s.body, 540, 553.5, 34, "none", stroke=INK, sw=1.4)
    add_circle(s.body, 540, 553.5, 2.4, INK)
    for x0, x1 in ((280, 340), (740, 800)):
        add_rect(s.body, x0, 481, x1 - x0, 145, "none", stroke=INK, sw=1.4)
        add_rect(s.body, x0, 511, 24, 85, "none", stroke=INK, sw=1.2)
    for cx in (272, 808):
        add_rect(s.body, cx - 6, 521, 12, 65, WHITE, stroke=INK, sw=1.2)
    s.text("ПОЛЕ 66 × 40 М · ФОРМАТ 8 × 8", 540, 676, 9, fill="#4A5A48", align="center", weight=600, tracking=24)

    # Fence with sponsor modules
    add_rect(s.body, 254, 372, 572, 355, "none", stroke=INK, sw=1, dash="7 5")
    for i in range(9):
        x = 286 + i * 62
        add_rect(s.body, x, 372, 34, 7, CORAL, opacity=0.85)
    for i in range(4):
        y = 438 + i * 78
        add_rect(s.body, 254, y, 7, 34, CORAL, opacity=0.85)
        add_rect(s.body, 819, y, 7, 34, CORAL, opacity=0.85)

    # Operator and commentary cabin
    add_rect(s.body, 138, 420, 100, 108, PLUM, rx=4)
    s.text("ОПЕРАТОРСКАЯ", 188, 452, 7.6, fill=WHITE, align="center", weight=650, tracking=8, width=92)
    s.text("VAR · КОММЕНТ.", 188, 470, 6.6, fill="#C9BFC6", align="center", tracking=6, width=92)
    add_line(s.body, 238, 474, 254, 474, PLUM, 1, dash="4 3")

    # Scoreboard
    add_rect(s.body, 850, 470, 54, 32, BUILDING, stroke=LINE, sw=1, rx=2)
    add_line(s.body, 877, 502, 877, 526, MUTED, 2)
    s.text("ТАБЛО", 877, 490, 7, fill=MUTED, align="center", weight=600)

    # Street entrance
    add_rect(s.body, 505, 738, 70, 8, CORAL)
    add_line(s.body, 540, 746, 540, 784, CORAL, 2, dash="5 4")
    s.text("ВХОД С УЛИЦЫ", 540, 806, 8, fill=MUTED, align="center", weight=550, tracking=18)

    # Numbered zone markers only; names are in the legend
    markers = [(1, 584, 762), (2, 270, 208), (3, 452, 208), (4, 668, 208),
               (5, 270, 350), (6, 600, 724), (7, 112, 448)]
    for number, x, y in markers:
        add_circle(s.body, x, y, 14, CORAL)
        s.text(str(number), x, y + 5, 11, fill=WHITE, weight=820, align="center", width=40)

    add_line(s.body, 64, 846, 916, 846, LINE, 1)
    s.text("Красным отмечены места размещения носителей. Пропорции условные.", 64, 866, 7.6, fill=MUTED)


def legend(s: Sheet) -> None:
    zones = [
        ("1", "ВХОД И РЕСЕПШЕН", "Тотем 800×2200 · объёмный логотип с подсветкой · план эвакуации · штендер «Матч дня»"),
        ("2", "КАФЕ И ЗОНА ОЖИДАНИЯ", "Меню-борды 600×900 · брендированные стаканы и подносы · таблички зоны ожидания"),
        ("3", "РАЗДЕВАЛКИ · 4", "Таблички со сменными карманами · именные таблички команд · крючки и зеркала · наклейки в душевых"),
        ("4", "VIP-ЛОЖА · 60 МЕСТ", "Логотип на стекле · нумерация мест · меню · таблички партнёров"),
        ("5", "ТРИБУНА · 284 МЕСТА", "Секторные таблички · чехлы на скамейки запасных · флагштоки · табло замен"),
        ("6", "ПЕРИМЕТР И ВОРОТА", "Модули 1000×750, 12–24 шт. · баннер на сетке 3000×1500 · вымпелы · подиум награждения"),
        ("7", "МЕДИАКОМПЛЕКС", "Брендирование операторской · фон флеш-интервью · комментаторская · графика трансляции"),
    ]
    y = 146
    s.text("ЧТО РАЗМЕЩАЕМ", 980, 166, 9, fill=MUTED, weight=650, tracking=54)
    for number, title, items in zones:
        add_rect(s.body, 980, y, 567, 100, WHITE, stroke=LINE, sw=1, rx=6)
        add_circle(s.body, 1012, y + 32, 14, CORAL)
        s.text(number, 1012, y + 37, 11, fill=WHITE, weight=820, align="center", width=40)
        s.text(title, 1038, y + 36, 11, weight=750, tracking=26, width=480)
        s.text(items, 1038, y + 60, 8.2, fill="#4E5A66", width=492, tracking=8)
        y += 106


def waves(s: Sheet) -> None:
    cards = [
        ("ВОЛНА 1", "2–4 НЕДЕЛИ · 150–250 ТЫС. ₽", "Периметр B1 · флажки B6 · табло замен A4 ·\nраздевалки C2 · эвакуация C4 · кафе D2 · штендер E3"),
        ("ВОЛНА 2", "1–2 МЕСЯЦА · 300–450 ТЫС. ₽", "Подиум A1 · составы A2 · сетка B2 · операторская B3 ·\nфлеш-интервью B4 · тотем C1 · графика E1 · комментаторская E2"),
        ("ВОЛНА 3", "СЕЗОН · ПО ПРОЕКТУ", "Ресепшен D1 · VIP D3 · фотозона D5 · напольная C3 ·\nчехлы B5 · турнирный kit F1 · event-kit F2 · тираж F4"),
    ]
    x = 40
    for title, meta, body in cards:
        add_rect(s.body, x, 900, 480, 168, INK, rx=8)
        s.text(title, x + 24, 936, 12, fill=WHITE, weight=780, tracking=46)
        s.text(meta, x + 24, 956, 7.6, fill=CORAL, weight=650, tracking=16)
        add_line(s.body, x + 24, 970, x + 456, 970, "#2A3A4C", 1)
        for index, line in enumerate(body.split("\n")):
            s.text(line, x + 24, 996 + index * 18, 7.4, fill="#C9D2DC", weight=500, tracking=6, width=436)
        x += 504


def main() -> None:
    sheet = Sheet()
    header(sheet)
    plan(sheet)
    legend(sheet)
    waves(sheet)
    footer(sheet)
    path = sheet.save()
    print(f"Wrote {path.relative_to(REPO)}")
    print(f"Wrote {(ROOT / 'arena-zone-map.png').relative_to(REPO)}")


if __name__ == "__main__":
    main()
