#!/usr/bin/env python3
"""Build a one-page New Year 2027 campaign plan."""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import resvg_py

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
sys.path.insert(0, str(REPO / "banners" / "anikom-arena-3000x2500-concepts"))

from build_concepts import FontOutliner  # noqa: E402

FONT = REPO / "banners" / "anikom-arena-3000x2500-concepts" / "source" / "Montserrat-Variable.ttf"
SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)

W, H = 1600, 1000
BG = "#F4F1EA"
INK = "#081A2B"
MUTED = "#7C8894"
LINE = "#D8D1C4"
CORAL = "#D94A43"
WHITE = "#FFFFFF"
PANEL = "#0D2238"


def tag(name: str) -> str:
    return f"{{{SVG_NS}}}{name}"


def rect(parent, x, y, w, h, fill, *, rx=0, stroke=None, sw=1, opacity=None):
    attrs = {
        "x": f"{x:g}", "y": f"{y:g}", "width": f"{w:g}", "height": f"{h:g}",
        "fill": fill, "rx": f"{rx:g}",
    }
    if stroke:
        attrs["stroke"] = stroke
        attrs["stroke-width"] = f"{sw:g}"
    if opacity is not None:
        attrs["opacity"] = f"{opacity:g}"
    return ET.SubElement(parent, tag("rect"), attrs)


def line(parent, x1, y1, x2, y2, stroke, sw=1, dash=None, opacity=None):
    attrs = {
        "x1": f"{x1:g}", "y1": f"{y1:g}", "x2": f"{x2:g}", "y2": f"{y2:g}",
        "stroke": stroke, "stroke-width": f"{sw:g}",
    }
    if dash:
        attrs["stroke-dasharray"] = dash
    if opacity is not None:
        attrs["opacity"] = f"{opacity:g}"
    return ET.SubElement(parent, tag("line"), attrs)


def dot(parent, cx, cy, r, fill):
    return ET.SubElement(parent, tag("circle"), {
        "cx": f"{cx:g}", "cy": f"{cy:g}", "r": f"{r:g}", "fill": fill,
    })


class Sheet:
    def __init__(self):
        self.outliner = FontOutliner(FONT)
        self.root = ET.Element(tag("svg"), {
            "version": "1.1",
            "width": f"{W}",
            "height": f"{H}",
            "viewBox": f"0 0 {W} {H}",
        })
        title = ET.SubElement(self.root, tag("title"))
        title.text = "План кампании: Новогоднее оформление 2027"
        desc = ET.SubElement(self.root, tag("desc"))
        desc.text = "Календарь сезона, структура кампаний и бюджет на одном листе."
        self.body = ET.SubElement(self.root, tag("g"), {"id": "SHEET"})
        rect(self.body, 0, 0, W, H, BG)

    def text(self, content, x, y, size, *, fill=INK, weight=500, align="left",
             tracking=10, width=1200, opacity=1.0):
        return self.outliner.add_text(
            self.body, content, x=x, baseline=y, cap_height=size, max_width=width,
            weight=weight, tracking=tracking, fill=fill, align=align, opacity=opacity,
        )

    def save(self):
        svg_path = ROOT / "campaign-one-pager.svg"
        ET.ElementTree(self.root).write(svg_path, encoding="utf-8", xml_declaration=True)
        png = resvg_py.svg_to_bytes(svg_path=str(svg_path), width=W * 2, height=H * 2)
        (ROOT / "campaign-one-pager.png").write_bytes(bytes(png))
        return svg_path


def header(s):
    s.text("SM PRODUCTION", 56, 76, 34, weight=820, tracking=22)
    s.text("НОВОГОДНЕЕ ОФОРМЛЕНИЕ 2027", 56, 112, 13, fill=CORAL, weight=700, tracking=70)
    s.text("План кампании · сезон 30 октября — 10 января", 700, 108, 13, fill=MUTED)
    s.text("Яндекс Директ + страница /novogodnee-oformlenie", 1544, 74, 12, weight=600, align="right")
    s.text("бюджет, структура, сроки", 1544, 100, 10, fill=MUTED, align="right")
    line(s.body, 56, 134, 1544, 134, LINE)


def timeline(s):
    s.text("КАЛЕНДАРЬ СЕЗОНА", 56, 172, 11, fill=MUTED, weight=700, tracking=56)

    x0, x1, y = 56, 1544, 226
    line(s.body, x0, y, x1, y, LINE, 6)
    phases = [
        (56, 340, "30 окт — 9 ноя", "Запуск", "учим стратегии, собираем статистику", CORAL),
        (340, 760, "10 — 30 ноя", "Пик спроса", "держим позиции, чистим запросы", INK),
        (760, 1120, "1 — 15 дек", "Дедлайн", "только проходные по срокам проекты", CORAL),
        (1120, 1340, "16 — 25 дек", "Срочно", "узкая кампания, высокие ставки", INK),
        (1340, 1544, "26 дек — 10 янв", "Спад", "стоп поиска, ретаргетинг", MUTED),
    ]
    for start, end, dates, title, note, color in phases:
        line(s.body, start + 4, y, end - 4, y, color, 6)
        dot(s.body, start + 4, y, 7, color)
        s.text(dates, start + 6, y - 22, 10, fill=MUTED, weight=600)
        s.text(title, start + 6, y + 34, 13, weight=780, tracking=14)
        s.text(note, start + 6, y + 56, 9.5, fill="#4E5A66", width=end - start - 20)

    rect(s.body, 56, 296, 1488, 84, WHITE, rx=6, stroke=LINE)
    s.text("ДЕДЛАЙН СТРАНИЦЫ И РЕКЛАМЫ", 80, 320, 9, fill=MUTED, weight=700, tracking=40)
    s.text("до 10 декабря — приём заявок на гарантированный монтаж до 20 декабря", 80, 346, 13, weight=650)
    s.text("после 15 декабря — срочные проекты с наценкой и отдельным согласованием", 80, 368, 10, fill="#4E5A66")


def structure(s):
    s.text("СТРУКТУРА КАМПАНИЙ", 56, 420, 11, fill=MUTED, weight=700, tracking=56)

    cards = [
        ("ПОИСК", "7 кампаний", "Офис · Фотозоны · События · Ритейл ·\nАрт-объекты · B2B · Срочно", 108000, 60),
        ("РСЯ / ЕПК", "комбинаторные", "5 заголовков, 5 текстов,\n8 креативов 1:1 и 16:9", 54000, 30),
        ("РЕТАРГЕТИНГ", "30 дней", "был на странице\nи не отправил форму", 18000, 10),
    ]
    x = 56
    for title, meta, body, budget, share in cards:
        rect(s.body, x, 444, 476, 208, PANEL, rx=8)
        s.text(title, x + 28, 486, 13, fill=WHITE, weight=780, tracking=44)
        s.text(meta, x + 28, 508, 9.5, fill=CORAL, weight=650, tracking=18)
        line(s.body, x + 28, 524, x + 448, 524, "#24374B", 1)
        for i, chunk in enumerate(body.split("\n")):
            s.text(chunk, x + 28, 550 + i * 20, 10, fill="#C9D2DC", weight=500, width=420)
        s.text(f"{budget:,} ₽".replace(",", " "), x + 28, 626, 22, fill=WHITE, weight=800, tracking=6)
        s.text(f"{share}% бюджета", x + 448, 626, 10, fill="#7E8FA1", align="right")
        x += 506

    rect(s.body, 56, 672, 1488, 60, "#EDE7DA", rx=6)
    s.text("БАЗОВЫЙ БЮДЖЕТ ПЕРВОГО МЕСЯЦА", 80, 708, 10, fill=MUTED, weight=700, tracking=30)
    s.text("180 000 ₽", 470, 710, 14, weight=820, fill=CORAL, tracking=6)
    s.text("цель: 25+ заявок · цена заявки до 7 000 ₽ · 5 квалифицированных проектов", 1544, 708, 10, fill="#4E5A66", align="right")


def funnel(s):
    s.text("ВОРОНКА И ОТВЕТСТВЕННЫЕ", 56, 786, 11, fill=MUTED, weight=700, tracking=56)

    steps = [
        ("КЛИК", "поиск и РСЯ", "Никита"),
        ("ЗАЯВКА", "форма · звонок · мессенджер", "Анастасия / Диля"),
        ("СМЕТА", "1 рабочий день", "Диля"),
        ("СДЕЛКА", "производство и монтаж", "Анастасия"),
    ]
    x = 56
    for i, (title, note, owner) in enumerate(steps):
        rect(s.body, x, 808, 340, 96, WHITE, rx=6, stroke=LINE)
        dot(s.body, x + 26, 836, 5, CORAL)
        s.text(title, x + 42, 844, 12, weight=780, tracking=24)
        s.text(note, x + 26, 868, 9.5, fill="#4E5A66")
        s.text(owner, x + 26, 888, 9, fill=CORAL, weight=650, tracking=10)
        if i < len(steps) - 1:
            line(s.body, x + 344, 856, x + 380, 856, MUTED, 1.5, dash="4 3")
        x += 384

    line(s.body, 56, 928, 1544, 928, LINE)
    s.text("Проверка перед запуском: цель «Заявка» в Метрике, UTM в amoCRM, сроки и цены на странице.", 56, 954, 10, fill="#4E5A66")
    s.text("Документ — план, а не гарантия бюджета и ставок. CPC и конверсия проверяются первые 10–14 дней.", 56, 976, 9, fill=MUTED)
    s.text("SM PRODUCTION · 30.10.2026", 1544, 954, 10, fill=MUTED, align="right")
    s.text("маркетинг/новогоднее оформление 2027", 1544, 976, 9, fill=MUTED, align="right")


def main() -> None:
    sheet = Sheet()
    header(sheet)
    timeline(sheet)
    structure(sheet)
    funnel(sheet)
    path = sheet.save()
    print(f"Готово: {path.relative_to(REPO)}")
    print(f"Готово: {(ROOT / 'campaign-one-pager.png').relative_to(REPO)}")


if __name__ == "__main__":
    main()
