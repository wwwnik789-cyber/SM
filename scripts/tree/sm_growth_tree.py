"""«Дерево роста SM» — вертикальная инфографика 1:2 (SVG, 1000×2000).

Пласты снизу вверх:
  01 корни  — каналы продвижения и роста;
  02 ствол  — услуги, на которых зарабатываем (+ насколько подробно описаны на сайте);
  03 ветви  — активы компании: сайт в центре, аналитика слева, каналы связи справа;
  04 крона  — клиенты и проекты по годам.

Данные услуг и портфолио читаются из src/data/*.js (через node), логотип векторизуется
из assets/brand/sm-logo-extracted.png. На выходе две версии:
  sm-growth-tree.svg          — живой текст + встроенные шрифты (редактируемый, с анимацией);
  sm-growth-tree_outlined.svg — текст переведён в кривые (для печати/Illustrator/Figma).

Запуск: python3 scripts/tree/sm_growth_tree.py
"""
import base64
import json
import math
import random
import subprocess
from pathlib import Path
from xml.sax.saxutils import escape

import cv2
import numpy as np
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[2]
FONTS = ROOT / "scripts/rebrand/fonts"
OUT = ROOT / "visualizations/sm-growth-tree"
W, H = 1000, 2000

# ------------------------------------------------------------------ палитра (из баннера SM)
NAVY_0 = "#141C2E"
NAVY_1 = "#1E2A44"
NAVY_2 = "#2F3B51"
BLUE = "#3B5274"
STEEL = "#627C9A"
STEEL_L = "#A9BCD3"
GOLD = "#D4A027"
GOLD_L = "#F0C75A"
WHITE = "#FFFFFF"

# ------------------------------------------------------------------ содержимое
CLIENTS = ["Tele2", "Сбер", "Яндекс", "S7 Airlines", "Haval", "Mitsubishi Motors",
           "Газпромнефть · G-Drive", "Sanofi", "Aurus", "МОСГОРТУР", "Домодедово", "Новатэк"]

ANALYTICS = [("amoCRM", "сделки и воронка"), ("Яндекс Метрика", "цели, вебвизор"),
             ("Аналитика сайта", "заявки и конверсии"), ("Аналитика телефонии", "коллтрекинг, записи"),
             ("Сквозная аналитика", "реклама → сделка")]
CONTACTS = [("Почта", "sm-pro1@yandex.ru"), ("Телефония Билайн", "+7 495 799-00-19"),
            ("Telegram", "чат и канал"), ("MAX", "мессенджер"), ("Заявки с сайта", "формы, калькулятор")]

# услуги: (заголовок, подпись, slug-и из services.js для оценки | число для ручной оценки, основная?)
SERVICES = [
    ("Комплексное оформление мероприятий", "застройка под ключ · от 89 000 ₽", ["zastroyka-meropriyatiy"], True),
    ("Имиджевые фотозоны", "брендированные фотозоны под событие", ["imidzhevye-fotozony"], True),
    ("Оформление сцен", "задник, каше, раус · от 89 000 ₽", ["oformlenie-stseny"], True),
    ("Press-Wall и Brand-Wall", "от 24 900 ₽ · изготовление за 24 часа", ["press-wall", "brand-wall"], False),
    ("Каше и раус-сцены", "обрамление экранов, юбка сцены", ["kashe-dlya-ekrana", "raus-stseny"], False),
    ("Фотозоны на заказ", "от 24 900 ₽ · акции на фотозоны", ["fotozony", "akciya-fotozona"], False),
    ("Выставочные и мобильные стенды", "стенды, Roll Up, уличные", ["vystavochnye-stendy", "mobilnye-stendy",
                                                                    "ulichnye-stendy"], False),
    ("Бренд-зоны", "активации бренда на площадке", ["brend-zony"], False),
    ("Баннеры и печать", "печать и монтаж · от 900 ₽", ["pechat-bannerov"], False),
    ("POS и интерактивные стенды", "ритейл и digital-элементы", ["pos-produkciya", "interaktivnye-stendy"], False),
    ("Собственное производство", "вывески, лайтбоксы, буквы, ресепшн", 4, False),
    ("Аренда и SM-Media", "LED-бары, свет, мебель · видео", 3, False),
]

# корни: каналы продвижения и роста
ROOTS = ["SEO и органика", "Яндекс Директ", "Яндекс Бизнес и Карты", "ВКонтакте",
         "Telegram-канал", "Rutube · видео SM-Media", "Pinterest", "Блог и полезный контент",
         "Отзывы и рейтинги", "Сарафан и повторные заказы", "Партнёрство с агентствами", "Тендеры и выставки"]

PHONE, SITE = "+7 495 799-00-19", "sm-production.ru"

# короткие подписи проектов портфолио (ключ — подстрока заголовка в src/data/portfolio.js)
PROJECT_SHORT = {
    "CTC Kids на VK Fest": "СТС Kids · VK Fest 2025", "Локомотив": "РЖД Арена · светящийся «Локомотив»",
    "конференции": "Burger King · конференция", "Mitsubishi": "Mitsubishi Motors · дилерская конференция",
    "MIKS": "MIKS Karting · гоночное оформление", "Invest Battle": "Invest Battle · подиум-октагон",
    "мерча": "Магазин мерча · Лужники", "DECKHOUSE": "DECKHOUSE · конференция",
    "Новатэк": "Новатэк · каше на три экрана", "VK Fest 2024": "VK Fest 2024 · три города",
    "Яндекс Лавка": "Яндекс Лавка · «ПОДАРОК»", "Три кота": "СТС · пространство «Три кота»",
}


def short_project(p):
    for k, v in PROJECT_SHORT.items():
        if k in p["title"]:
            return v
    return p["title"]


# ------------------------------------------------------------------ данные сайта
def site_data():
    js = """
    Promise.all([import('./src/data/services.js'), import('./src/data/portfolio.js')]).then(([s, p]) =>
      console.log(JSON.stringify({services: s.services, portfolio: p.portfolio})))"""
    return json.loads(subprocess.check_output(["node", "-e", js], cwd=ROOT))


def depth_score(svc):
    """0–5: насколько подробно услуга описана на сайте (по текстам страницы)."""
    text = " ".join([svc.get("short", "")] + svc.get("features", []) + svc.get("long", []))
    return (int(len(text) >= 300) + int(len(text) >= 450) + int(bool(svc.get("priceFrom")))
            + int(len(svc.get("features", [])) >= 4) + int(len(svc.get("long", [])) >= 2))


# ------------------------------------------------------------------ шрифты: замер и кривые
class Font:
    def __init__(self, file, family, weight):
        self.file, self.family, self.weight = file, family, weight
        self.tt = TTFont(str(FONTS / file))
        self.gs = self.tt.getGlyphSet()
        self.cmap = self.tt.getBestCmap()
        self.upm = self.tt["head"].unitsPerEm
        self.hmtx = self.tt["hmtx"]
        self.used = set()

    def glyph(self, ch):
        return self.cmap.get(ord(ch)) or self.cmap.get(ord("?"))

    def width(self, s, size, ls=0.0):
        return sum(self.hmtx[self.glyph(c)][0] for c in s) * size / self.upm + ls * max(len(s) - 1, 0)

    def outline(self, s, x, y, size, ls=0.0):
        k = size / self.upm
        pen = SVGPathPen(self.gs, ntos=lambda v: f"{v:.2f}".rstrip("0").rstrip("."))
        cx = x
        for c in s:
            g = self.glyph(c)
            self.gs[g].draw(TransformPen(pen, (k, 0, 0, -k, cx, y)))
            cx += self.hmtx[g][0] * k + ls
        return pen.getCommands()


F = {"u5": Font("Unbounded_500Medium.ttf", "Unbounded", 500),
     "m4": Font("Manrope_400Regular.ttf", "Manrope", 400),
     "m6": Font("Manrope_600SemiBold.ttf", "Manrope", 600)}


# ------------------------------------------------------------------ сборщик SVG
class SVG:
    def __init__(self, outlined):
        self.outlined = outlined
        self.parts = []

    def add(self, s):
        self.parts.append(s)

    def text(self, x, y, s, size, font="m4", fill=WHITE, anchor="start", opacity=1.0, ls=0.0, extra=""):
        f = F[font]
        f.used.update(s)
        op = f' opacity="{opacity}"' if opacity < 1 else ""
        if self.outlined:
            w = f.width(s, size, ls)
            x0 = x - (w / 2 if anchor == "middle" else w if anchor == "end" else 0)
            self.add(f'<path d="{f.outline(s, x0, y, size, ls)}" fill="{fill}"{op}{extra}/>')
        else:
            lsa = f' letter-spacing="{ls:g}"' if ls else ""
            self.add(f'<text x="{x:.1f}" y="{y:.1f}" font-family="{f.family}" font-weight="{f.weight}" '
                     f'font-size="{size:g}" fill="{fill}" text-anchor="{anchor}"{lsa}{op}{extra}>{escape(s)}</text>')

    def fit(self, s, font, size, max_w, min_size=9, ls=0.0):
        while size > min_size and F[font].width(s, size, ls) > max_w:
            size -= 0.5
        return size


def fmt(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


# ------------------------------------------------------------------ логотип → вектор
def logo_paths():
    lg = cv2.imread(str(ROOT / "assets/brand/sm-logo-extracted.png"), cv2.IMREAD_UNCHANGED)
    b, g, r, a = [lg[..., i].astype(int) for i in range(4)]
    k = 4
    out = []
    for name, m, col in [("white", (a > 0) & ~((r - b > 60) & (a > 60)), WHITE), ("gold", (r - b > 60) & (a > 60), GOLD)]:
        alpha = np.where(m, a, 0).astype(np.uint8)
        big = cv2.resize(alpha, None, fx=k, fy=k, interpolation=cv2.INTER_CUBIC)
        big = cv2.GaussianBlur(big, (0, 0), 1.2)
        _, bw = cv2.threshold(big, 110, 255, cv2.THRESH_BINARY)
        cnts, _ = cv2.findContours(bw, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
        d = []
        for c in cnts:
            if cv2.contourArea(c) < 6 * k * k:
                continue
            c = cv2.approxPolyDP(c, 0.9, True)[:, 0, :] / k
            d.append("M" + " L".join(f"{fmt(x)} {fmt(y)}" for x, y in c) + "Z")
        out.append((" ".join(d), col))
    return out, lg.shape[1], lg.shape[0]


# ------------------------------------------------------------------ элементы
def pill(svg, cx, cy, label, size=13, font="m6", h=30, fill=NAVY_1, stroke=STEEL, tfill=WHITE,
         padx=14, sw=1.2, opacity=0.94, detail=None, dsize=None, dfill=STEEL_L, x_left=None, w_fix=None):
    w = F[font].width(label, size) + 2 * padx
    if detail:
        dsize = dsize or size - 1.5
        w += 8 + F["m4"].width(detail, dsize)
    w = w_fix or w
    x0 = x_left if x_left is not None else cx - w / 2
    svg.add(f'<rect x="{x0:.1f}" y="{cy - h / 2:.1f}" width="{w:.1f}" height="{h}" rx="{h / 2}" '
            f'fill="{fill}" fill-opacity="{opacity}" stroke="{stroke}" stroke-width="{sw}"/>')
    ty = cy + size * 0.36
    if detail:
        svg.text(x0 + padx, ty, label, size, font, tfill)
        svg.text(x0 + padx + F[font].width(label, size) + 8, ty, detail, dsize, "m4", dfill)
    else:
        svg.text(x0 + w / 2, ty, label, size, font, tfill, anchor="middle")
    return w


def layer_title(svg, cx, cy, num, title, color=GOLD):
    size = 15
    tw = F["u5"].width(title, size, 1.2)
    w = tw + 74
    svg.add(f'<rect x="{cx - w / 2:.1f}" y="{cy - 19:.1f}" width="{w:.1f}" height="38" rx="19" '
            f'fill="{NAVY_0}" fill-opacity="0.92" stroke="{color}" stroke-width="1.5"/>')
    svg.add(f'<circle cx="{cx - w / 2 + 21:.1f}" cy="{cy}" r="13" fill="{color}"/>')
    svg.text(cx - w / 2 + 21, cy + 4.6, num, 12.5, "u5", NAVY_0, anchor="middle")
    svg.text(cx - w / 2 + 44, cy + 5.4, title, size, "u5", WHITE, ls=1.2)


def depth_bar(svg, x, y, score, n=5):
    for i in range(n):
        on = i < score
        svg.add(f'<rect x="{x + i * 13:.1f}" y="{y - 5:.1f}" width="10" height="10" rx="2.5" '
                f'fill="{GOLD if on else "none"}" stroke="{GOLD if on else STEEL}" stroke-width="1.1"/>')


# ------------------------------------------------------------------ дерево
def inside_crown(x, y):
    ell = [(500, 460, 450, 290), (500, 275, 300, 110), (225, 720, 215, 170), (775, 720, 215, 170),
           (500, 590, 290, 150)]
    return any(((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1 for cx, cy, rx, ry in ell)


def foliage(svg, rnd):
    def sample(n, rmin, rmax):
        pts = []
        while len(pts) < n:
            x, y = rnd.uniform(20, 980), rnd.uniform(120, 930)
            if inside_crown(x, y):
                pts.append((x, y, rnd.uniform(rmin, rmax)))
        return pts

    layers = [(95, 60, 115, "leafA", 1.0), (80, 40, 80, "leafB", 0.93), "branches", (40, 34, 64, "leafB", 0.9),
              (150, 22, 52, "leafC", 0.55)]
    for layer in layers:
        if layer == "branches":
            branches(svg)
            continue
        n, r0, r1, grad, op = layer
        pts = sample(n, r0, r1)
        pts.sort(key=lambda p: p[1])
        g = [f'<g fill="url(#{grad})" opacity="{op}">']
        g += [f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.0f}"/>' for x, y, r in pts]
        g.append("</g>")
        svg.add("".join(g))
    # искры-листочки
    sp = sample(220, 1.2, 3.4)
    g = ['<g>']
    for x, y, r in sp:
        col = GOLD_L if rnd.random() < 0.35 else WHITE
        g.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.1f}" fill="{col}" opacity="{rnd.uniform(.25, .7):.2f}"/>')
    g.append("</g>")
    svg.add("".join(g))


def branches(svg):
    # ветви: между задним и передним слоями листвы — просвечивают сквозь крону
    br = [("M480 880 C 450 800 360 790 240 740", 50), ("M520 880 C 550 800 640 790 760 740", 50),
          ("M500 900 C 495 780 505 680 500 520", 58), ("M470 830 C 420 700 340 620 300 500", 30),
          ("M530 830 C 580 700 660 620 700 500", 30), ("M300 770 C 220 740 150 690 110 620", 22),
          ("M700 770 C 780 740 850 690 890 620", 22), ("M500 660 C 450 560 420 460 410 340", 20),
          ("M500 660 C 550 560 580 460 590 340", 20), ("M350 640 C 290 580 230 520 200 450", 14),
          ("M650 640 C 710 580 770 520 800 450", 14), ("M500 560 C 500 450 500 360 500 260", 16)]
    for d, w in br:
        svg.add(f'<path d="{d}" fill="none" stroke="#141C2E" stroke-opacity="0.45" stroke-width="{w + 6}" '
                f'stroke-linecap="round"/>')
        svg.add(f'<path d="{d}" fill="none" stroke="url(#barkV)" stroke-width="{w}" stroke-linecap="round"/>')


def trunk(svg):
    # ствол с корневым расширением
    svg.add('<path d="M440 860 C 446 1050 430 1300 404 1430 C 392 1468 345 1480 300 1492 '
            'L 700 1492 C 655 1480 608 1468 596 1430 C 570 1300 554 1050 560 860 '
            'C 556 830 530 815 500 812 C 470 815 444 830 440 860 Z" fill="url(#bark)"/>')
    # фактура коры
    for x0, x1 in [(462, 430), (480, 462), (497, 494), (514, 530), (534, 566)]:
        svg.add(f'<path d="M{x0} 840 C {x0 - 6} 1050 {x1 + 8} 1250 {x1} 1470" fill="none" '
                f'stroke="#0F1626" stroke-opacity="0.35" stroke-width="2"/>')
        svg.add(f'<path d="M{x0 + 3} 840 C {x0 - 3} 1050 {x1 + 11} 1250 {x1 + 3} 1470" fill="none" '
                f'stroke="{STEEL_L}" stroke-opacity="0.18" stroke-width="1.2"/>')


def roots(svg, tips):
    """Корни: от основания ствола к подписям-каналам + мелкие корешки."""
    base = [(420, 1488), (460, 1490), (500, 1492), (540, 1490), (580, 1488)]
    for i, (tx, ty) in enumerate(tips):
        bx, by = base[min(4, int(tx / 1000 * 5))]
        midy = (by + ty) / 2
        d = f"M{bx} {by} C {bx} {midy} {tx} {midy - 30} {tx} {ty - 18}"
        w = max(3, 14 - (ty - 1580) / 28)
        svg.add(f'<path d="{d}" fill="none" stroke="url(#rootG)" stroke-width="{w:.1f}" stroke-linecap="round"/>')
    rnd = random.Random(7)
    for _ in range(46):
        x0 = rnd.uniform(330, 670)
        y0 = 1495
        x1 = x0 + rnd.uniform(-330, 330)
        y1 = y0 + rnd.uniform(60, 420)
        svg.add(f'<path d="M{x0:.0f} {y0} C {x0:.0f} {(y0 + y1) / 2:.0f} {x1:.0f} {(y0 + y1) / 2:.0f} {x1:.0f} {y1:.0f}" '
                f'fill="none" stroke="{GOLD}" stroke-opacity="{rnd.uniform(.08, .22):.2f}" '
                f'stroke-width="{rnd.uniform(.8, 2.4):.1f}" stroke-linecap="round"/>')


def network(svg, rnd):
    """Тонкая «сеть» как на фирменном баннере."""
    pts = [(rnd.uniform(0, W), rnd.uniform(0, H)) for _ in range(46)]
    g = [f'<g stroke="{STEEL_L}" stroke-opacity="0.10" stroke-width="0.8" fill="{STEEL_L}">']
    for i, (x, y) in enumerate(pts):
        near = sorted(pts, key=lambda p: (p[0] - x) ** 2 + (p[1] - y) ** 2)[1:3]
        for nx, ny in near:
            g.append(f'<line x1="{x:.0f}" y1="{y:.0f}" x2="{nx:.0f}" y2="{ny:.0f}"/>')
        g.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="2" fill-opacity="0.25" stroke="none"/>')
    g.append("</g>")
    svg.add("".join(g))


def particles(svg, tips):
    """«Сок» дерева: золотые частицы идут от корней к кроне (SMIL-анимация, в статике скрыты)."""
    targets = [(250, 770), (750, 770), (500, 330), (300, 520), (700, 520), (500, 460)]
    for i, (tx, ty) in enumerate(tips[::2]):
        ex, ey = targets[i % len(targets)]
        d = (f"M{tx} {ty - 18} C {tx} {(ty + 1490) / 2 - 30} 500 {(ty + 1490) / 2} 500 1480 "
             f"L 500 980 C 500 900 {ex} {ey + 80} {ex} {ey}")
        dur = 7 + i * 0.8
        svg.add(f'<circle r="3.4" fill="{GOLD_L}" filter="url(#glow)" opacity="0">'
                f'<animateMotion dur="{dur:.1f}s" begin="{i * 1.1:.1f}s" repeatCount="indefinite" path="{d}"/>'
                f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.08;0.9;1" dur="{dur:.1f}s" '
                f'begin="{i * 1.1:.1f}s" repeatCount="indefinite"/></circle>')


# ------------------------------------------------------------------ сборка
def defs(svg):
    svg.add(f"""<defs>
<style>@@FONTS@@</style>
<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="{NAVY_1}"/><stop offset="0.45" stop-color="{NAVY_2}"/>
  <stop offset="0.74" stop-color="{NAVY_1}"/><stop offset="1" stop-color="{NAVY_0}"/></linearGradient>
<radialGradient id="halo" cx="0.5" cy="0.5" r="0.5">
  <stop offset="0" stop-color="{STEEL}" stop-opacity="0.45"/><stop offset="1" stop-color="{STEEL}" stop-opacity="0"/></radialGradient>
<linearGradient id="soil" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#18213A"/><stop offset="1" stop-color="#0E1424"/></linearGradient>
<radialGradient id="leafA" cx="0.35" cy="0.3" r="0.75">
  <stop offset="0" stop-color="#4F77A3"/><stop offset="1" stop-color="#22395A"/></radialGradient>
<radialGradient id="leafB" cx="0.35" cy="0.3" r="0.75">
  <stop offset="0" stop-color="#7499C2"/><stop offset="0.7" stop-color="#3B5E88"/><stop offset="1" stop-color="#2D4A70"/></radialGradient>
<radialGradient id="leafC" cx="0.35" cy="0.3" r="0.7">
  <stop offset="0" stop-color="#B5CCE4"/><stop offset="1" stop-color="#5E84AE" stop-opacity="0"/></radialGradient>
<linearGradient id="bark" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="#121A2C"/><stop offset="0.3" stop-color="#3D5172"/><stop offset="0.55" stop-color="#6F87A8"/>
  <stop offset="0.8" stop-color="#34476A"/><stop offset="1" stop-color="#121A2C"/></linearGradient>
<linearGradient id="barkV" gradientUnits="userSpaceOnUse" x1="0" y1="300" x2="0" y2="900">
  <stop offset="0" stop-color="#2E4364"/><stop offset="1" stop-color="#4C6386"/></linearGradient>
<linearGradient id="rootG" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#34445F"/><stop offset="0.35" stop-color="#8A6A22"/><stop offset="1" stop-color="{GOLD}"/></linearGradient>
<linearGradient id="ground" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="{GOLD}" stop-opacity="0"/><stop offset="0.5" stop-color="{GOLD_L}"/>
  <stop offset="1" stop-color="{GOLD}" stop-opacity="0"/></linearGradient>
<linearGradient id="timeG" x1="0" y1="1" x2="0" y2="0">
  <stop offset="0" stop-color="{GOLD}" stop-opacity="0.15"/><stop offset="1" stop-color="{GOLD_L}"/></linearGradient>
<filter id="glow" x="-200%" y="-200%" width="500%" height="500%"><feGaussianBlur stdDeviation="2.6" result="b"/>
  <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<filter id="soft" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="14"/></filter>
</defs>""")


def build(outlined):
    data = site_data()
    svc = {s["slug"]: s for s in data["services"]}
    port = sorted(data["portfolio"], key=lambda p: -int(p["year"]))
    for p in port:
        p["year"] = str(p["year"])
    rnd = random.Random(2026)
    svg = SVG(outlined)
    svg.add(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">')
    svg.add("<title>Дерево роста SM-Production</title><desc>Корни — каналы продвижения; ствол — услуги; "
            "ветви — активы компании; крона — клиенты и проекты.</desc>")
    defs(svg)

    # фон
    svg.add(f'<rect width="{W}" height="{H}" fill="url(#sky)"/>')
    svg.add(f'<ellipse cx="500" cy="480" rx="560" ry="520" fill="url(#halo)"/>')
    network(svg, rnd)
    svg.add(f'<rect x="0" y="1488" width="{W}" height="{H - 1488}" fill="url(#soil)"/>')

    # корни (позиции подписей — сетка 4×3)
    xs = [130, 375, 625, 870]
    rows_y = [1612, 1712, 1812]
    tips = [(xs[i % 4], rows_y[i // 4]) for i in range(len(ROOTS))]
    roots(svg, tips)
    svg.add('<rect x="0" y="1486" width="1000" height="4" fill="url(#ground)"/>')

    # ствол, ветви, крона
    trunk(svg)
    svg.add(f'<ellipse cx="500" cy="480" rx="430" ry="300" fill="{BLUE}" opacity="0.35" filter="url(#soft)"/>')
    foliage(svg, rnd)
    particles(svg, tips)

    # ---------------- шапка
    lp, lw, lh = logo_paths()
    s = 92 / lh
    svg.add(f'<g transform="translate(40 36) scale({s:.4f})">' +
            "".join(f'<path d="{d}" fill="{c}" fill-rule="evenodd"/>' for d, c in lp) + "</g>")
    tx = 40 + lw * s + 26
    svg.add(f'<line x1="{tx - 13:.0f}" y1="42" x2="{tx - 13:.0f}" y2="124" stroke="{STEEL}" stroke-opacity="0.6"/>')
    svg.text(tx, 78, "ДЕРЕВО РОСТА", 36, "u5", WHITE, ls=1)
    svg.text(tx + F["u5"].width("ДЕРЕВО РОСТА ", 36, 1), 78, "SM", 36, "u5", GOLD, ls=1)
    svg.text(tx, 104, "Как компания растёт во времени: каналы продвижения питают услуги,", 15.5, "m4", STEEL_L)
    svg.text(tx, 124, "активы превращают заявки в проекты, а проекты — в новых клиентов", 15.5, "m4", STEEL_L)

    # ---------------- 04 крона: клиенты и проекты
    layer_title(svg, 500, 200, "04", "КЛИЕНТЫ И ПРОЕКТЫ")
    for row, items in enumerate([CLIENTS[:6], CLIENTS[6:]]):
        sz, gap = 12.5, 8
        ws = [F["m6"].width(c, sz) + 24 for c in items]
        x = 500 - (sum(ws) + gap * (len(ws) - 1)) / 2
        for c, w in zip(items, ws):
            pill(svg, 0, 246 + row * 36, c, sz, "m6", h=28, stroke=GOLD, sw=1, x_left=x, w_fix=w,
                 fill=NAVY_0, opacity=0.8)
            x += w + gap
    svg.text(500, 302 + 26, "проекты по годам — крона растёт вверх", 12, "m4", STEEL_L, anchor="middle")

    years = {}
    for p in port:
        years.setdefault(p["year"], []).append(p)
    y = 368
    for yr in sorted(years, reverse=True):
        items = [short_project(p) for p in years[yr]]
        rows = [items[i:i + 3] for i in range(0, len(items), 3)]
        for r_i, row in enumerate(rows):
            sz = 12.5
            while True:
                ws = [F["m6"].width(c, sz) + 26 for c in row]
                tot = sum(ws) + 8 * (len(ws) - 1)
                if tot < 760 or sz <= 10:
                    break
                sz -= 0.5
            x = 520 - tot / 2
            if r_i == 0:
                svg.text(x - 14, y + 5, str(yr), 15, "u5", GOLD_L, anchor="end")
            for c, w in zip(row, ws):
                pill(svg, 0, y, c, sz, "m6", h=30, stroke=STEEL_L, sw=0.9, x_left=x, w_fix=w, fill=NAVY_1)
                x += w + 8
            y += 40
        y += 6
    crown_bottom = y

    # ---------------- 03 ветви: активы компании
    ay = max(crown_bottom + 26, 640)
    layer_title(svg, 500, ay, "03", "АКТИВЫ КОМПАНИИ")
    # сайт в центре
    cy = ay + 92
    svg.add(f'<rect x="355" y="{cy - 52}" width="290" height="104" rx="22" fill="{NAVY_0}" fill-opacity="0.95" '
            f'stroke="{GOLD}" stroke-width="2"/>')
    svg.add(f'<rect x="355" y="{cy - 52}" width="290" height="104" rx="22" fill="none" stroke="{GOLD_L}" '
            f'stroke-opacity="0.35" stroke-width="7" filter="url(#glow)"/>')
    svg.text(500, cy - 20, "САЙТ · ГЛАВНЫЙ АКТИВ", 11, "u5", GOLD_L, anchor="middle", ls=1.5)
    svg.text(500, cy + 12, "SM-PRODUCTION.RU", 22.5, "u5", WHITE, anchor="middle")
    svg.text(500, cy + 36, "услуги · портфолио · калькулятор · заявки", 11.5, "m4", STEEL_L, anchor="middle")
    # кластеры
    for side, title, items in [(-1, "АНАЛИТИКА", ANALYTICS), (1, "КАНАЛЫ СВЯЗИ", CONTACTS)]:
        CLW = 290
        x_left = 28 if side < 0 else 1000 - 28 - CLW
        svg.text(x_left + CLW / 2, ay + 38, title, 12.5, "u5", GOLD_L, anchor="middle", ls=1.5)
        for i, (name, det) in enumerate(items):
            py = ay + 64 + i * 37
            pill(svg, 0, py, name, 13.5, "m6", h=31, detail=det, dsize=12, x_left=x_left, w_fix=CLW,
                 fill=NAVY_0, stroke=STEEL, opacity=0.92)
        # связь с сайтом: золотые стрелки к сайту
        for k in (-1, 1):
            yk = cy + k * 26
            if side < 0:
                x1, x2 = x_left + CLW + 6, 352
            else:
                x1, x2 = x_left - 6, 648
            svg.add(f'<line x1="{x1}" y1="{yk}" x2="{x2 - 7 * -side}" y2="{yk}" stroke="{GOLD}" stroke-width="1.6"/>')
            svg.add(f'<path d="M{x2} {yk} l{7 * side} -5 v10 Z" fill="{GOLD}"/>')
    assets_bottom = ay + 64 + 4 * 37 + 16

    # ---------------- 02 ствол: услуги
    sy = assets_bottom + 34
    layer_title(svg, 500, sy, "02", "УСЛУГИ — НА ЧЁМ ЗАРАБАТЫВАЕМ")
    lx = 500 - 175
    depth_bar(svg, lx, sy + 34, 3)
    svg.text(lx + 72, sy + 38, "— насколько подробно и уникально услуга описана на сайте", 12, "m4", STEEL_L)
    top = sy + 76
    step = (1440 - top) / 6
    for i, (title, sub, src, main) in enumerate(SERVICES):
        score = src if isinstance(src, int) else max(depth_score(svc[s_]) for s_ in src if s_ in svc)
        col, row = i % 2, i // 2
        CW = 344
        x0 = 24 if col == 0 else 1000 - 24 - CW
        cyc = top + row * step + step / 2 - 4
        hh = 64
        svg.add(f'<rect x="{x0}" y="{cyc - hh / 2:.1f}" width="{CW}" height="{hh}" rx="16" fill="{NAVY_0}" '
                f'fill-opacity="0.93" stroke="{GOLD if main else STEEL}" stroke-width="{1.8 if main else 1}"/>')
        # связь со стволом
        ex = x0 + CW if col == 0 else x0
        tx_ = 440 if col == 0 else 560
        svg.add(f'<line x1="{ex}" y1="{cyc:.1f}" x2="{tx_}" y2="{cyc:.1f}" stroke="{GOLD if main else STEEL}" '
                f'stroke-width="1.2" stroke-opacity="0.8"/>')
        svg.add(f'<circle cx="{tx_}" cy="{cyc:.1f}" r="4" fill="{GOLD if main else STEEL_L}"/>')
        tsz = svg.fit(title, "m6", 16.5, CW - 32)
        svg.text(x0 + 16, cyc - 6, title, tsz, "m6", WHITE)
        svg.text(x0 + 16, cyc + 17, sub, 12, "m4", STEEL_L)
        depth_bar(svg, x0 + CW - 16 - 62, cyc + 13, score)
        if main:
            bw = F["u5"].width("ОСНОВНАЯ", 9, 1) + 18
            bx = x0 + CW - 18 - bw
            svg.add(f'<rect x="{bx:.1f}" y="{cyc - hh / 2 - 9:.1f}" width="{bw:.1f}" height="18" rx="9" fill="{GOLD}"/>')
            svg.text(bx + bw / 2, cyc - hh / 2 + 3.3, "ОСНОВНАЯ", 9, "u5", NAVY_0, anchor="middle", ls=1)

    # ---------------- 01 корни: каналы роста
    layer_title(svg, 500, 1540, "01", "КАНАЛЫ ПРОДВИЖЕНИЯ И РОСТА")
    for (tx_, ty_), name in zip(tips, ROOTS):
        sz = svg.fit(name, "m6", 13.5, 200)
        pill(svg, tx_, ty_, name, sz, "m6", h=34, fill=NAVY_0, stroke=GOLD, sw=1.3, opacity=0.95, w_fix=226)
    svg.text(500, 1890, "Каналы роста питают дерево:  лиды → заявки → услуги → проекты → новые клиенты",
             14, "m6", GOLD_L, anchor="middle")

    # ---------------- ось времени слева
    svg.add(f'<line x1="12" y1="1870" x2="12" y2="190" stroke="url(#timeG)" stroke-width="2"/>')
    svg.add(f'<path d="M5 200 L12 184 L19 200 Z" fill="{GOLD_L}"/>')
    tag = "ВРЕМЯ  ·  РОСТ КОМПАНИИ"
    if outlined:
        svg.add(f'<g transform="rotate(-90 9 1040)">')
        svg.text(9, 1040 + 4, tag, 10, "u5", GOLD_L, anchor="middle", ls=2)
        svg.add("</g>")
    else:
        svg.text(9, 1044, tag, 10, "u5", GOLD_L, anchor="middle", ls=2, extra=' transform="rotate(-90 9 1040)"')

    # ---------------- подвал
    svg.add(f'<line x1="40" y1="1930" x2="960" y2="1930" stroke="{STEEL}" stroke-opacity="0.4"/>')
    svg.text(40, 1964, "SM-PRODUCTION  ·  event branding decor", 13, "u5", WHITE, ls=1)
    svg.text(960, 1964, f"{SITE}   ·   {PHONE}", 14, "m6", STEEL_L, anchor="end")
    svg.add("</svg>")
    out = "\n".join(svg.parts)
    return out.replace("@@FONTS@@", "" if outlined else embedded_fonts())


def embedded_fonts():
    """@font-face с подмножеством глифов (только реально использованные символы)."""
    import io
    from fontTools import subset
    css = ""
    for f in F.values():
        if not f.used:
            continue
        font = TTFont(str(FONTS / f.file))
        sub = subset.Subsetter(subset.Options())
        sub.populate(text="".join(sorted(f.used)) + " ")
        sub.subset(font)
        buf = io.BytesIO()
        font.save(buf)
        b64 = base64.b64encode(buf.getvalue()).decode()
        css += (f"@font-face{{font-family:'{f.family}';font-weight:{f.weight};"
                f"src:url(data:font/ttf;base64,{b64}) format('truetype');}}")
    return css


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for outlined, name in [(False, "sm-growth-tree.svg"), (True, "sm-growth-tree_outlined.svg")]:
        s = build(outlined)
        (OUT / name).write_text(s, encoding="utf-8")
        print("✓", name, f"{len(s) / 1024:.0f} KB")


if __name__ == "__main__":
    main()
