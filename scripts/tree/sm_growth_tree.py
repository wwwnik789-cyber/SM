"""«Дерево роста SM» — вертикальная инфографика 1:2 (SVG, 1000×2000).

Пласты снизу вверх:
  01 корни  — каналы продвижения и роста (соцсети, платная реклама, новые и старые клиенты);
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
SHIFT = 110                 # на сколько поднята верхняя часть (ствол/ветви/земля) ради места под корни
GROUND = 1488 - SHIFT       # линия земли

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

# (название, подпись, иконка[, значки мессенджеров справа])
ANALYTICS = [("amoCRM", "сделки и воронка", "funnel"), ("Яндекс Метрика", "цели, вебвизор", "chart"),
             ("Аналитика сайта", "заявки и конверсии", "cursor"),
             ("Аналитика телефонии", "коллтрекинг, записи", "phonecall"),
             ("Сквозная аналитика", "реклама → сделка", "route")]
# мобильные номера менеджеров привязаны к телефонии, на них же MAX и Telegram
MOBILE_DILYA = "+7 999 928-51-48"
MOBILE_NASTYA = "+7 909 993-60-28"
CONTACTS = [("Почта", "sm-pro1@yandex.ru", "mail"), ("Телефония Билайн", "+7 495 799-00-19", "phone"),
            ("Диля", MOBILE_DILYA, "mobile", ("tg", "max")), ("Настя", MOBILE_NASTYA, "mobile", ("tg", "max")),
            ("Telegram", "чат и канал", "tg"), ("MAX", "мессенджер", "max"),
            ("Заявки с сайта", "формы, калькулятор", "form")]

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

# корни: каналы продвижения и роста — три главных корня (группы) и их отростки
SOCIAL = ["MAX", "Telegram", "YouTube", "Rutube", "Дзен", "Группа VK", "Яндекс Карты", "Яндекс Услуги", "Avito"]
ADS = ("Рекламные кампании", "за деньги", "платное продвижение")
OUTREACH = ["Автосалоны", "Коммерческие интерьеры", "и другие новые ниши"]
# старые клиенты: работа с базой — категории по вниманию и условиям
REPEAT = [("A", "Ключевые", "максимум внимания · лучшие условия"),
          ("Б", "Постоянные", "регулярные касания · скидки за серию"),
          ("В", "Разовые", "рассылки, акции · базовые условия")]

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
# линейные иконки 24×24 (stroke), в стиле Lucide
ICONS = {
    "funnel": ['<path d="M22 3H2l8 9.46V19l4 2v-8.54L22 3z"/>'],
    "chart": ['<path d="M3 3v18h18"/>', '<path d="M18 17V9"/>', '<path d="M13 17V5"/>', '<path d="M8 17v-3"/>'],
    "cursor": ['<rect x="2" y="3" width="20" height="14" rx="2"/>', '<path d="M11 10l3 9 1.5-3.5L19 14z"/>'],
    "phone": ['<path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 '
              '19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 '
              '2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 '
              '2.81.7A2 2 0 0 1 22 16.92z"/>'],
    "route": ['<circle cx="6" cy="19" r="3"/>', '<path d="M9 19h8.5a3.5 3.5 0 0 0 0-7h-11a3.5 3.5 0 0 1 0-7H15"/>',
              '<circle cx="18" cy="5" r="3"/>'],
    "mail": ['<rect x="2" y="4" width="20" height="16" rx="2"/>', '<path d="M22 7l-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>'],
    "mobile": ['<rect x="5" y="2" width="14" height="20" rx="2.5"/>', '<path d="M10.5 18h3"/>'],
    "tg": ['<path d="M22 2L15 22l-4-9-9-4z"/>', '<path d="M22 2L11 13"/>'],
    "max": ['<path d="M7.9 20A9 9 0 1 0 4 16.1L2 22z"/>', '<path d="M8 14.5V9.5l4 3.2 4-3.2v5"/>'],
    "form": ['<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7z"/>', '<path d="M14 2v5h6"/>',
             '<path d="M8 13h8"/>', '<path d="M8 17h5"/>'],
}
ICONS["phonecall"] = ICONS["phone"] + ['<path d="M14.05 2a9 9 0 0 1 8 7.94"/>', '<path d="M14.05 6A5 5 0 0 1 18 10"/>']


def icon(svg, kind, cx, cy, size, color=GOLD_L, sw=2.0):
    s_ = size / 24
    svg.add(f'<g transform="translate({cx - size / 2:.2f} {cy - size / 2:.2f}) scale({s_:.4f})" fill="none" '
            f'stroke="{color}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round">'
            + "".join(ICONS[kind]) + "</g>")


def icon_badge(svg, kind, cx, cy, r, ring=GOLD, fill="#2A2410", color=GOLD_L):
    """Иконка в круглой подложке."""
    svg.add(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="{fill}" stroke="{ring}" stroke-width="1"/>')
    icon(svg, kind, cx, cy, r * 1.15, color)


def pill(svg, cx, cy, label, size=13, font="m6", h=30, fill=NAVY_1, stroke=STEEL, tfill=WHITE,
         padx=14, sw=1.2, opacity=0.94, detail=None, dsize=None, dfill=STEEL_L, x_left=None, w_fix=None,
         ico=None, badges=()):
    w = F[font].width(label, size) + 2 * padx
    if detail:
        dsize = dsize or size - 1.5
        w += 8 + F["m4"].width(detail, dsize)
    w = w_fix or w
    x0 = x_left if x_left is not None else cx - w / 2
    svg.add(f'<rect x="{x0:.1f}" y="{cy - h / 2:.1f}" width="{w:.1f}" height="{h}" rx="{h / 2}" '
            f'fill="{fill}" fill-opacity="{opacity}" stroke="{stroke}" stroke-width="{sw}"/>')
    ty = cy + size * 0.36
    lx = x0 + padx
    if ico:
        icon_badge(svg, ico, x0 + h / 2, cy, h / 2 - 3.5)
        lx = x0 + h + 4
    for k, b in enumerate(badges):                       # значки мессенджеров справа
        icon_badge(svg, b, x0 + w - h / 2 - k * (h - 5), cy, h / 2 - 5, ring=STEEL, fill=NAVY_1)
    if detail:
        svg.text(lx, ty, label, size, font, tfill)
        dx = lx + F[font].width(label, size) + 8
        room = x0 + w - 10 - len(badges) * (h - 5) - dx
        dsize = svg.fit(detail, "m4", dsize, room, min_size=9.5)
        svg.text(dx, ty, detail, dsize, "m4", dfill)
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
    ell = [(500, 440, 450, 280), (500, 265, 300, 105), (225, 630, 215, 170), (775, 630, 215, 170),
           (500, 510, 290, 150)]
    return any(((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1 for cx, cy, rx, ry in ell)


def foliage(svg, rnd):
    def sample(n, rmin, rmax):
        pts = []
        while len(pts) < n:
            x, y = rnd.uniform(20, 980), rnd.uniform(120, 830)
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
          ("M650 640 C 710 580 770 520 800 450", 14), ("M500 560 C 500 480 500 420 500 380", 16)]
    svg.add(f'<g transform="translate(0 {-SHIFT})">')
    for d, w in br:
        svg.add(f'<path d="{d}" fill="none" stroke="#1A120C" stroke-opacity="0.45" stroke-width="{w + 6}" '
                f'stroke-linecap="round"/>')
        svg.add(f'<path d="{d}" fill="none" stroke="url(#barkV)" stroke-width="{w}" stroke-linecap="round"/>')
    svg.add("</g>")


def trunk(svg):
    svg.add(f'<g transform="translate(0 {-SHIFT})">')
    # ствол с корневым расширением
    svg.add('<path d="M440 860 C 446 1050 430 1300 404 1430 C 392 1468 345 1480 300 1492 '
            'L 700 1492 C 655 1480 608 1468 596 1430 C 570 1300 554 1050 560 860 '
            'C 556 830 530 815 500 812 C 470 815 444 830 440 860 Z" fill="url(#bark)"/>')
    # фактура коры
    for x0, x1 in [(462, 430), (480, 462), (497, 494), (514, 530), (534, 566)]:
        svg.add(f'<path d="M{x0} 840 C {x0 - 6} 1050 {x1 + 8} 1250 {x1} 1470" fill="none" '
                f'stroke="#1E140D" stroke-opacity="0.45" stroke-width="2"/>')
        svg.add(f'<path d="M{x0 + 3} 840 C {x0 - 3} 1050 {x1 + 11} 1250 {x1 + 3} 1470" fill="none" '
                f'stroke="#C9A27A" stroke-opacity="0.22" stroke-width="1.2"/>')
    svg.add("</g>")


def root_path(svg, x0, y0, x1, y1, w, op=1.0):
    my = (y0 + y1) / 2
    svg.add(f'<path d="M{x0:.0f} {y0:.0f} C {x0:.0f} {my:.0f} {x1:.0f} {my - 20:.0f} {x1:.0f} {y1:.0f}" fill="none" '
            f'stroke="url(#rootG)" stroke-width="{w:.1f}" stroke-linecap="round" opacity="{op}"/>')


def roots(svg, groups):
    """Три главных корня от ствола к группам каналов, от групп — отростки к каждому каналу."""
    rnd = random.Random(7)
    for _ in range(46):                                   # мелкие корешки
        x0 = rnd.uniform(330, 670)
        y0 = GROUND + 7
        x1 = x0 + rnd.uniform(-330, 330)
        y1 = y0 + rnd.uniform(60, 500)
        svg.add(f'<path d="M{x0:.0f} {y0} C {x0:.0f} {(y0 + y1) / 2:.0f} {x1:.0f} {(y0 + y1) / 2:.0f} {x1:.0f} {y1:.0f}" '
                f'fill="none" stroke="#B88A3A" stroke-opacity="{rnd.uniform(.08, .2):.2f}" '
                f'stroke-width="{rnd.uniform(.8, 2.4):.1f}" stroke-linecap="round"/>')
    bases = [430, 480, 525, 572]
    for (gx, gy, tips), bx in zip(groups, bases):
        root_path(svg, bx, GROUND + 2, gx, gy, 22)
        for tx, ty in tips:
            root_path(svg, gx, gy + 12, tx, ty - 18, 6, 0.9)


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
    targets = [(250, 860), (750, 860), (500, 420), (300, 610), (700, 610), (500, 550)]
    for i, (tx, ty) in enumerate(tips[::2][:8]):
        ex, ey = targets[i % len(targets)]
        g = GROUND
        d = (f"M{tx} {ty - 18} C {tx} {(ty + g) / 2 - 30} 500 {(ty + g) / 2} 500 {g - 8} "
             f"L 500 {980 - SHIFT} C 500 {900 - SHIFT} {ex} {ey - SHIFT + 80} {ex} {ey - SHIFT}")
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
  <stop offset="0" stop-color="#5E9A55" stop-opacity="0.32"/><stop offset="1" stop-color="#5E9A55" stop-opacity="0"/></radialGradient>
<linearGradient id="soil" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#2A2019"/><stop offset="0.25" stop-color="#1D1915"/><stop offset="1" stop-color="#121420"/></linearGradient>
<radialGradient id="leafA" cx="0.35" cy="0.3" r="0.75">
  <stop offset="0" stop-color="#3F7F3A"/><stop offset="1" stop-color="#173F1F"/></radialGradient>
<radialGradient id="leafB" cx="0.35" cy="0.3" r="0.75">
  <stop offset="0" stop-color="#7DBA55"/><stop offset="0.65" stop-color="#3E8A3C"/><stop offset="1" stop-color="#2A6430"/></radialGradient>
<radialGradient id="leafC" cx="0.35" cy="0.3" r="0.7">
  <stop offset="0" stop-color="#C8EC8E"/><stop offset="1" stop-color="#6FB04E" stop-opacity="0"/></radialGradient>
<linearGradient id="bark" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="#2A1B12"/><stop offset="0.3" stop-color="#5E412B"/><stop offset="0.55" stop-color="#8C6745"/>
  <stop offset="0.8" stop-color="#553A26"/><stop offset="1" stop-color="#2A1B12"/></linearGradient>
<linearGradient id="barkV" gradientUnits="userSpaceOnUse" x1="0" y1="190" x2="0" y2="790">
  <stop offset="0" stop-color="#4A3322"/><stop offset="1" stop-color="#6E4F35"/></linearGradient>
<linearGradient id="rootG" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#5E412B"/><stop offset="0.45" stop-color="#8A6A2E"/><stop offset="1" stop-color="{GOLD}"/></linearGradient>
<linearGradient id="ground" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="#6FB04E" stop-opacity="0"/><stop offset="0.5" stop-color="#8FCB5E"/>
  <stop offset="1" stop-color="#6FB04E" stop-opacity="0"/></linearGradient>
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
    svg.add(f'<rect x="0" y="{GROUND}" width="{W}" height="{H - GROUND}" fill="url(#soil)"/>')

    # корни: группы и позиции подписей
    GY = GROUND + 140
    ROWS = [GY + 105, GY + 185, GY + 265]
    SOC_X = (74, 202, 330)
    AX, OX, RX = 472, 642, 868               # платная реклама · новые клиенты · старые клиенты
    soc_tips = [(SOC_X[i % 3], ROWS[i // 3]) for i in range(len(SOCIAL))]
    out_tips = [(OX, ROWS[i]) for i in range(len(OUTREACH))]
    rep_tips = [(RX, ROWS[i]) for i in range(len(REPEAT))]
    ads_tip = [(AX, ROWS[0])]
    groups = [(202, GY, soc_tips), (AX, GY, ads_tip), (OX, GY, out_tips), (RX, GY, rep_tips)]
    roots(svg, groups)
    tips = soc_tips + ads_tip + out_tips + rep_tips
    svg.add(f'<rect x="0" y="{GROUND - 2}" width="1000" height="4" fill="url(#ground)"/>')

    # ствол, ветви, крона
    trunk(svg)
    svg.add(f'<ellipse cx="500" cy="450" rx="430" ry="280" fill="#2F6B35" opacity="0.45" filter="url(#soft)"/>')
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
    layer_title(svg, 500, 190, "04", "КЛИЕНТЫ И ПРОЕКТЫ")
    for row, items in enumerate([CLIENTS[:6], CLIENTS[6:]]):
        sz, gap = 12, 8
        ws = [F["m6"].width(c, sz) + 24 for c in items]
        x = 500 - (sum(ws) + gap * (len(ws) - 1)) / 2
        for c, w in zip(items, ws):
            pill(svg, 0, 230 + row * 31, c, sz, "m6", h=26, stroke=GOLD, sw=1, x_left=x, w_fix=w,
                 fill=NAVY_0, opacity=0.8)
            x += w + gap
    svg.text(500, 290, "проекты по годам — крона растёт вверх", 11.5, "m4", STEEL_L, anchor="middle")

    years = {}
    for p in port:
        years.setdefault(p["year"], []).append(p)
    y = 318
    for yr in sorted(years, reverse=True):
        items = [short_project(p) for p in years[yr]]
        rows = [items[i:i + 3] for i in range(0, len(items), 3)]
        for r_i, row in enumerate(rows):
            sz = 12
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
                pill(svg, 0, y, c, sz, "m6", h=27, stroke=STEEL_L, sw=0.9, x_left=x, w_fix=w, fill=NAVY_1)
                x += w + 8
            y += 34
        y += 4
    crown_bottom = y

    # ---------------- 03 ветви: активы компании
    ay = crown_bottom + 18
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
        step_c = 34 if len(items) <= 5 else 31
        for i, it in enumerate(items):
            name, det, ico = it[:3]
            badges = it[3] if len(it) > 3 else ()
            py = ay + 60 + i * step_c
            mob = bool(badges)
            pill(svg, 0, py, name, 13.5, "m6", h=step_c - 3, detail=det, dsize=12, x_left=x_left, w_fix=CLW,
                 fill=NAVY_0, stroke=GOLD if mob else STEEL, sw=1.2, opacity=0.92, ico=ico, badges=badges,
                 padx=12)
        # связь с сайтом: золотые стрелки к сайту
        for k in (-1, 1):
            yk = cy + k * 26
            if side < 0:
                x1, x2 = x_left + CLW + 6, 352
            else:
                x1, x2 = x_left - 6, 648
            svg.add(f'<line x1="{x1}" y1="{yk}" x2="{x2 - 7 * -side}" y2="{yk}" stroke="{GOLD}" stroke-width="1.6"/>')
            svg.add(f'<path d="M{x2} {yk} l{7 * side} -5 v10 Z" fill="{GOLD}"/>')
    assets_bottom = ay + 60 + (len(CONTACTS) - 1) * 31 + 16
    # подпись к мобильным: привязаны к телефонии
    svg.text(1000 - 28 - 145, assets_bottom + 12, "мобильные менеджеров — в телефонии, с MAX и Telegram", 10.5, "m4",
             GOLD_L, anchor="middle")
    assets_bottom += 14

    # ---------------- 02 ствол: услуги
    sy = assets_bottom + 30
    layer_title(svg, 500, sy, "02", "УСЛУГИ — НА ЧЁМ ЗАРАБАТЫВАЕМ")
    lx = 500 - 175
    depth_bar(svg, lx, sy + 34, 3)
    svg.text(lx + 72, sy + 38, "— насколько подробно и уникально услуга описана на сайте", 12, "m4", STEEL_L)
    top = sy + 70
    step = (GROUND - 42 - top) / 6
    for i, (title, sub, src, main) in enumerate(SERVICES):
        score = src if isinstance(src, int) else max(depth_score(svc[s_]) for s_ in src if s_ in svc)
        col, row = i % 2, i // 2
        CW = 344
        x0 = 24 if col == 0 else 1000 - 24 - CW
        cyc = top + row * step + step / 2 - 4
        hh = 58
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
    layer_title(svg, 500, GROUND + 56, "01", "КАНАЛЫ ПРОДВИЖЕНИЯ И РОСТА")
    heads = [(["СОЦСЕТИ И ПЛОЩАДКИ"], 330), (["ПЛАТНАЯ", "РЕКЛАМА"], 140), (["ВЫХОД НА НОВЫХ", "КЛИЕНТОВ"], 190),
             (["СТАРЫЕ КЛИЕНТЫ", "РАБОТА С БАЗОЙ"], 236)]
    for (gx, gy, _), (lines, w) in zip(groups, heads):
        svg.add(f'<rect x="{gx - w / 2:.1f}" y="{gy - 23}" width="{w:.1f}" height="46" rx="23" fill="{GOLD}"/>')
        if len(lines) == 1:
            svg.text(gx, gy + 4.5, lines[0], 12, "u5", NAVY_0, anchor="middle", ls=0.8)
        else:
            svg.text(gx, gy - 3, lines[0], 11, "u5", NAVY_0, anchor="middle", ls=0.6)
            svg.text(gx, gy + 12, lines[1], 11 if gx != RX else 9.5, "u5", NAVY_0, anchor="middle",
                     ls=0.6, opacity=1 if gx != RX else 0.75)
    for (tx_, ty_), name in zip(soc_tips, SOCIAL):
        pill(svg, tx_, ty_, name, 14, "m6", h=40, fill=NAVY_0, stroke=GOLD, sw=1.3, opacity=0.95, w_fix=122)
    for (tx_, ty_), name in zip(out_tips, OUTREACH):
        sz = svg.fit(name, "m6", 14, 190 - 20)
        pill(svg, tx_, ty_, name, sz, "m6", h=40, fill=NAVY_0, stroke=GOLD, sw=1.3, opacity=0.95, w_fix=190)
    # старые клиенты: категории A / Б / В
    for (tx_, ty_), (letter, name, det) in zip(rep_tips, REPEAT):
        w, hh = 236, 56
        x0 = tx_ - w / 2
        svg.add(f'<rect x="{x0:.1f}" y="{ty_ - hh / 2:.1f}" width="{w}" height="{hh}" rx="18" fill="{NAVY_0}" '
                f'fill-opacity="0.95" stroke="{GOLD}" stroke-width="1.3"/>')
        svg.add(f'<circle cx="{x0 + 28:.1f}" cy="{ty_}" r="17" fill="{GOLD}"/>')
        svg.text(x0 + 28, ty_ + 6.5, letter, 17, "u5", NAVY_0, anchor="middle")
        svg.text(x0 + 54, ty_ - 3, name, 14, "m6", WHITE)
        dsz = svg.fit(det, "m4", 10.5, w - 54 - 10)
        svg.text(x0 + 54, ty_ + 15, det, dsz, "m4", STEEL_L)
    svg.text(RX, ROWS[2] + 46, "кому сколько внимания и какие условия", 11, "m4", GOLD_L, anchor="middle")
    ax, ay_ = ads_tip[0]
    hb = ROWS[2] - ROWS[0] + 40
    mid = (ROWS[0] + ROWS[2]) / 2
    svg.add(f'<rect x="{ax - 70}" y="{ay_ - 20}" width="140" height="{hb}" rx="20" fill="{NAVY_0}" fill-opacity="0.95" '
            f'stroke="{GOLD}" stroke-width="1.3"/>')
    svg.text(ax, mid - 30, "Рекламные", 14, "m6", WHITE, anchor="middle")
    svg.text(ax, mid - 10, "кампании", 14, "m6", WHITE, anchor="middle")
    svg.text(ax, mid + 10, ADS[1], 14, "m6", WHITE, anchor="middle")
    svg.text(ax, mid + 36, "платное", 12, "m4", STEEL_L, anchor="middle")
    svg.text(ax, mid + 52, "продвижение", 12, "m4", STEEL_L, anchor="middle")
    svg.text(500, 1890, "Каналы роста питают дерево:  лиды → заявки → услуги → проекты → клиенты → повторные заказы",
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
