#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Генератор PDF-презентации «Брендинг для автосалонов» (SM-Production).
14 слайдов 16:9. Вся вёрстка в дизайн-пикселях 1280×720 (масштабируется в PDF),
текст векторный, шрифты Unbounded / Manrope (OFL).

Запуск:  python3 build_pdf.py
Итог:    SM-Production_Brending-avtosalonov.pdf
"""
import os, tempfile
from PIL import Image, ImageOps
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import Color, HexColor
from reportlab.lib.utils import ImageReader

BASE = os.path.dirname(os.path.abspath(__file__))
IMG  = os.path.join(BASE, "img")
FONTS = os.path.join(BASE, "fonts")
OUT  = os.path.join(BASE, "SM-Production_Brending-avtosalonov.pdf")

DW, DH = 1280.0, 720.0            # дизайн-система
PW, PH = 1920.0, 1080.0           # страница PDF = 1920×1080 px (1 px = 1 pt)
SCALE = PW / DW

BG   = HexColor("#0a0a0d")
BG_RGB = (10, 10, 13)
CARD = HexColor("#14141c")
INK  = HexColor("#f4f2ec")
MUT  = HexColor("#98989f")
MUT2 = HexColor("#d9d6cd")
DIM  = HexColor("#cfccc4")
ACC  = HexColor("#ff4d1c")
ACID = HexColor("#d8ff3e")
LINE = Color(244/255, 242/255, 236/255, alpha=0.13)

for name, file in [
    ("Unb", "Unbounded-400.ttf"), ("Unb-B", "Unbounded-700.ttf"), ("Unb-XB", "Unbounded-800.ttf"),
    ("Man", "Manrope-400.ttf"), ("Man-M", "Manrope-500.ttf"), ("Man-SB", "Manrope-600.ttf"),
    ("Man-B", "Manrope-700.ttf"), ("Man-XB", "Manrope-800.ttf"),
]:
    pdfmetrics.registerFont(TTFont(name, os.path.join(FONTS, file)))

_cache = {}

def T(y):
    """y от верха (дизайн-px) → y от низа"""
    return DH - y

# ---------------- изображения ----------------
def _prep(name, w, h, focus=(0.5, 0.5), fade=None):
    """ключ кэша: подготовленный (обрезанный + с запечённым градиентом) файл"""
    key = (name, round(w), round(h), focus, fade)
    if key in _cache:
        return _cache[key]
    im = Image.open(os.path.join(IMG, name)).convert("RGB")
    sw, sh = im.size
    target = w / h
    if sw / sh > target:
        nw, nh = int(sh * target), sh
    else:
        nw, nh = sw, int(sw / target)
    left = int((sw - nw) * focus[0]); top = int((sh - nh) * focus[1])
    im = im.crop((left, top, left + nw, top + nh))
    out_px = (max(2, int(w * 1.7)), max(2, int(h * 1.7)))
    im = im.resize(out_px, Image.LANCZOS)

    if fade:
        # fade = (сторона, где фон непрозрачен, a0 → a1): маска фона 0..255
        d, a0, a1 = fade
        W_, H_ = im.size
        if d in ("right", "left"):
            # слева → справа
            vals = [int(round(255 * max(0.0, min(1.0, a0 + (a1 - a0) * (x / max(1, W_ - 1))))))
                    for x in range(W_)]
            if d == "left":
                vals = vals[::-1]
            mask = Image.frombytes("L", (W_, H_), bytes(vals) * H_)
        else:
            vals = [int(round(255 * max(0.0, min(1.0, a0 + (a1 - a0) * (y / max(1, H_ - 1))))))
                    for y in range(H_)]
            if d == "top":
                vals = vals[::-1]
            mask = Image.frombytes("L", (W_, H_), bytes(v for v in vals for _ in range(W_)))
        bgimg = Image.new("RGB", im.size, BG_RGB)
        im = Image.composite(bgimg, im, mask)

    tmp = os.path.join(tempfile.gettempdir(), f"smpdf_{abs(hash(key))}.jpg")
    im.save(tmp, quality=85, optimize=True)
    _cache[key] = tmp
    return tmp

def cover(c, name, x, y, w, h, focus=(0.5, 0.5), fade=None):
    c.drawImage(_prep(name, w, h, focus, fade), x, T(y + h), w, h, mask=None)

def cover_round(c, name, x, y, w, h, r=16, focus=(0.5, 0.5), fade=None):
    c.saveState()
    p = c.beginPath(); p.roundRect(x, T(y + h), w, h, r)
    c.clipPath(p, stroke=0, fill=0)
    cover(c, name, x, y, w, h, focus, fade)
    c.restoreState()

def shade(c, x, y, w, h, alpha=0.86, steps=26):
    """тёмная подложка под подпись на фото: несколько слоёв с нарастающей плотностью"""
    for i in range(steps):
        a = alpha * ((i + 1) / steps) ** 1.6
        band = h / steps
        c.setFillColor(Color(0.031, 0.031, 0.043, alpha=a))
        c.rect(x, T(y + h - i * band), w, band + 0.5, stroke=0, fill=1)

# ---------------- примитивы ----------------
def card(c, x, y, w, h, r=18, fill=CARD, stroke=LINE, sw=1):
    c.setFillColor(fill); c.setStrokeColor(stroke); c.setLineWidth(sw)
    c.roundRect(x, T(y + h), w, h, r, stroke=1, fill=1)

def txt(c, x, y, s, font="Man", size=16, color=INK, anchor="l"):
    c.setFont(font, size); c.setFillColor(color)
    if anchor == "l":   c.drawString(x, T(y), s)
    elif anchor == "r": c.drawRightString(x, T(y), s)
    else:               c.drawCentredString(x, T(y), s)

def sw_(s, font, size):
    return pdfmetrics.stringWidth(s, font, size)

def wrap(s, font, size, maxw):
    lines, cur = [], ""
    for w_ in s.split():
        t = (cur + " " + w_).strip()
        if sw_(t, font, size) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur); cur = w_
    if cur: lines.append(cur)
    return lines

def para(c, x, y, s, font="Man-SB", size=15, leading=None, color=MUT, maxw=400, anchor="l"):
    """абзац; y — верх текстового блока; возвращает высоту"""
    leading = leading or size * 1.42
    lines = wrap(s, font, size, maxw)
    for i, ln in enumerate(lines):
        bx = x if anchor == "l" else x
        txt(c, bx, y + size * 0.82 + i * leading, ln, font, size, color, anchor)
    return len(lines) * leading

def chip(c, x, y, label, style="o", size=14, padx=18, h=36):
    tw = sw_(label, "Man-B", size)
    w = tw + padx * 2
    if style == "acid": c.setFillColor(ACID); c.setStrokeColor(ACID)
    elif style == "acc": c.setFillColor(CARD); c.setStrokeColor(ACC)
    else:               c.setFillColor(Color(0.078, 0.078, 0.11, alpha=0.85)); c.setStrokeColor(LINE)
    c.setLineWidth(1)
    c.roundRect(x, T(y + h), w, h, h / 2, stroke=1, fill=1)
    col = HexColor("#0a0a0d") if style == "acid" else (ACC if style == "acc" else INK)
    txt(c, x + w / 2, y + h / 2 + size * 0.36, label, "Man-B", size, col, "c")
    return w

def chip_row(c, x, y, labels, styles=None, gap=12, size=14, h=36):
    cx = x
    for i, lb in enumerate(labels):
        cx += chip(c, cx, y, lb, styles[i] if styles else "o", size, h=h) + gap
    return cx - gap - x

def kicker(c, x, y, label, size=15):
    c.setFillColor(ACC); c.rect(x, T(y + 3), 34, 3.2, stroke=0, fill=1)
    txt(c, x + 46, y + 3, label.upper(), "Man-B", size, ACID)

def logo(c, x, y, h, name="logo-smproduction.png"):
    path = os.path.join(IMG, name)
    im = Image.open(path)
    ar = im.size[0] / im.size[1]
    c.drawImage(ImageReader(path), x, T(y + h), h * ar, h, mask="auto")
    return h * ar

def h2(c, x, y_top, lines, size=46, lf=1.12):
    lh = size * lf
    for i, segs in enumerate(lines):
        cx = x
        for s, col in segs:
            txt(c, cx, y_top + size * 0.86 + i * lh, s, "Unb-XB", size, col)
            cx += sw_(s, "Unb-XB", size)
    return len(lines) * lh

PAGE = [0]

def footer(c, n=None):
    if n is None:
        n = PAGE[0]
    y = 704
    logo(c, 56, y - 19, 19, "logo-mark.png")
    txt(c, 56 + 32, y, "SM-PRODUCTION · БРЕНДИНГ ДЛЯ АВТОСАЛОНОВ", "Man-SB", 12.5,
        Color(0.44, 0.44, 0.47, 1))
    txt(c, 1224, y, str(n).zfill(2), "Man-XB", 12.5, ACC, "r")

# =====================================================================
#  СЛАЙДЫ
# =====================================================================
def s01(c):
    cover(c, "as-omoda-c5.jpg", 0, 0, 1280, 720, focus=(0.55, 0.5), fade=("right", 1.0, 0.0))
    shade(c, 0, 0, 640, 720, 0.72)
    logo(c, 56, 48, 112)

    kicker(c, 56, 268, "Презентация для дилерских центров")
    h2(c, 56, 296, [
        [("Брендинг", INK)],
        [("для ", INK), ("автосалонов", ACC)],
    ], size=64, lf=1.06)

    para(c, 56, 442, "Оперативно решаем вопросы по брендингу — от вывески на фасаде "
         "до мероприятия в шоуруме. Собственное производство, сроки от 3 дней.",
         "Man-M", 21, 30, MUT2, 660)
    chip_row(c, 56, 534, ["Срочные заказы от 3 дней", "КП в течение дня", "24/7 производство и монтаж"],
             ["acid", "o", "o"])

    y = 664
    txt(c, 56, y, "+7 495 799-00-19", "Man-B", 18, ACID)
    x = 56 + sw_("+7 495 799-00-19", "Man-B", 18) + 30
    for s_ in ["sm-pro1@yandex.ru", "sm-production.ru"]:
        txt(c, x, y, s_, "Man-SB", 18, MUT); x += sw_(s_, "Man-SB", 18) + 30
    # адрес — отдельной строкой, в затемнённой зоне слева
    txt(c, 56, y + 28, "Москва, Остаповский проезд — центральное производство", "Man-SB", 15, MUT)

def s02(c):
    cover(c, "workshop.jpg", 780, 0, 500, 720, fade=("left", 1.0, 0.0))

    kicker(c, 56, 56, "Кто мы")
    h2(c, 56, 84, [
        [("Производство,", INK)],
        [("а ", INK), ("не посредники", ACC)],
    ], size=46)
    para(c, 56, 206, "SM-Production — производственная компания полного цикла: от концепции "
         "и 3D-визуализации до печати, изготовления конструкций и монтажа на объекте. Свой цех "
         "на Остаповском проезде в Москве — вы не переплачиваете наценку посредников.",
         "Man-M", 20, 29, MUT2, 690)

    stats = [("от 3", "дней — срочные конструкции"), ("от 12", "часов — баннеры и печать"),
             ("24/7", "производство и монтаж"), ("ПН–ПТ", "приём заявок 10:00–18:00")]
    for i, (big, small) in enumerate(stats):
        cx = 56 + (i % 2) * 356
        cy = 330 + (i // 2) * 112
        card(c, cx, cy, 340, 96)
        txt(c, cx + 24, cy + 52, big, "Unb-XB", 34, ACC)
        txt(c, cx + 24, cy + 78, small.upper(), "Man-B", 12, MUT)
    chip_row(c, 56, 574, ["Москва, Остаповский проезд — центральное производство",
                          "Доставка и монтаж по всей России"])
    footer(c)

def s03(c):
    kicker(c, 56, 56, "Задача")
    h2(c, 56, 84, [
        [("Почему оформление салона —", INK)],
        [("это ", INK), ("не «просто баннеры»", ACC)],
    ], size=46)

    pains = [
        ("БЕЗЛИКИЙ ШОУРУМ", "Ресепшн и зона продаж не работают на бренд и не создают впечатления премиум-производителя.",
         "→ Брендирование интерьера под ключ с 3D-визуализацией"),
        ("СРОЧНОСТЬ", "Открытие, старт продаж, приезд зоны, день открытых дверей — дедлайн не ждёт согласований.",
         "→ Конструкция с экраном 5×3 м за 3 дня"),
        ("БРЕНД-СТАНДАРТЫ", "Производитель требует точного соблюдения фирменного стиля — любая ошибка в цвете или макете.",
         "→ Работа по брендбуку, проверка пантонов бесплатно"),
        ("ДЕСЯТОК ПОДРЯДЧИКОВ", "Печатники, светильщики, мебельщики, монтажники — и никому нельзя предъявить за результат.",
         "→ Один подрядчик полного цикла: проект, производство, монтаж"),
    ]
    for i, (title, body, arrow) in enumerate(pains):
        cx = 56 + (i % 2) * 384
        cy = 218 + (i // 2) * 196
        w_, h_ = 368, 180
        card(c, cx, cy, w_, h_)
        txt(c, cx + 22, cy + 34, title, "Unb-B", 15, ACID)
        para(c, cx + 22, cy + 46, body, "Man-SB", 15, 21, MUT2, w_ - 44)
        para(c, cx + 22, cy + 118, arrow, "Man-B", 14, 19.5, ACC, w_ - 44)

    cover_round(c, "reception.jpg", 832, 218, 392, 180)
    cover_round(c, "as-haval-day.jpg", 832, 414, 392, 180)
    footer(c)

def s04(c):
    kicker(c, 56, 56, "Что делаем")
    h2(c, 56, 84, [[("Четыре направления ", INK), ("для автосалона", ACC)]], size=44)

    items = [
        ("A · Интерьер", "Зона ресепшн и интерьер",
         "Стойки ресепшн, объёмные логотипы, навигация, брендирование стен и зон ожидания",
         "as-baltavtotrade-wide.jpg"),
        ("B · Фасад", "Вывески и наружная реклама",
         "Световые короба и объёмные буквы, баннеры на фасад, флаги и виндеры, уличные конструкции",
         "lightbox.jpg"),
        ("C · Мероприятия", "События в салоне",
         "Дни открытых дверей, старты продаж, презентации моделей, конференции дилеров",
         "as-tenet-night.jpg"),
        ("D · Акции", "Сезонные акции и печать",
         "Срочная печать, сменные полотна, POS-продукция, оформление спецпредложений",
         "as-haval-day2.jpg"),
    ]
    for i, (tag, title, body, img) in enumerate(items):
        cx = 56 + (i % 2) * 592
        cy = 206 + (i // 2) * 226
        w_, h_ = 576, 210
        card(c, cx, cy, w_, h_)
        cover_round(c, img, cx + 14, cy + 14, 150, h_ - 28, 12)
        tx = cx + 182
        chip(c, tx, cy + 22, tag, "acc", 13, 14, 30)
        txt(c, tx, cy + 88, title, "Unb-XB", 18, INK)
        para(c, tx, cy + 104, body, "Man-SB", 14, 20, MUT, w_ - 200)
    footer(c)

def s05(c):
    cover(c, "sm-reception-zone-1.jpg", 0, 0, 570, 720, fade=("right", 1.0, 0.0))
    chip(c, 40, 606, "Решение A", "acid")

    x = 626
    kicker(c, x, 56, "Интерьер")
    h2(c, x, 84, [[("Зона ресепшн", INK)], [("и интерьер ", INK), ("под ключ", ACC)]], size=38)

    bullets = [
        "Стойка ресепшн по индивидуальному дизайну: МДФ эмаль, акрил, подсветка",
        "Объёмный логотип с контражурной подсветкой",
        "Навигация, таблички, брендирование стен и зон ожидания",
        "Замер, 3D-визуализация, монтаж без остановки работы салона",
    ]
    y = 222
    for i, b in enumerate(bullets):
        txt(c, x, y + 13, "✓", "Man-XB", 16, ACID)
        hh = para(c, x + 26, y, b, "Man-SB", 16, 22, INK, 560)
        y += max(hh, 22) + 12
        if i < len(bullets) - 1:
            c.setStrokeColor(LINE); c.setLineWidth(1); c.line(x, T(y), 1224, T(y))
            y += 14

    prices = [("от 89 000 ₽", "стойка ресепшн стандарт"), ("от 250 000 ₽", "зона ресепшн «под ключ»"),
              ("от 19 500 ₽/м", "объёмный логотип"), ("от 7 дней", "срочно — от 3 дней")]
    for i, (p, lab) in enumerate(prices):
        cx = x + (i % 2) * 306
        cy = 466 + (i // 2) * 104
        card(c, cx, cy, 290, 88)
        txt(c, cx + 18, cy + 40, p, "Unb-XB", 20, ACC)
        para(c, cx + 18, cy + 50, lab, "Man-SB", 12.5, 16, MUT, 254)
    footer(c)

def s06(c):
    cover(c, "lightbox.jpg", 710, 0, 570, 720, fade=("left", 1.0, 0.0))
    chip(c, 1224 - 40 - 150, 606, "Решение B", "acid")

    x = 56
    kicker(c, x, 56, "Фасад и наружная реклама")
    h2(c, x, 84, [[("Салон ", INK), ("видно издалека", ACC)]], size=38)

    bullets = [
        "Световые вывески, короба и объёмные буквы любой формы",
        "Баннеры и фасадная графика — печать от 3 часов",
        "Флаги, виндеры и уличные конструкции для входной зоны",
        "Защита от влаги и УФ — материалы для улицы",
    ]
    y = 208
    for i, b in enumerate(bullets):
        txt(c, x, y + 13, "✓", "Man-XB", 16, ACID)
        hh = para(c, x + 26, y, b, "Man-SB", 16, 22, INK, 520)
        y += max(hh, 22) + 12
        if i < len(bullets) - 1:
            c.setStrokeColor(LINE); c.setLineWidth(1); c.line(x, T(y), 690, T(y))
            y += 14

    prices = [("от 900 ₽/м²", "печать баннеров"), ("от 300 000 ₽", "уличные конструкции"),
              ("от 4 500 ₽", "мобильные стенды"), ("от 12 часов", "изготовление и монтаж")]
    for i, (p, lab) in enumerate(prices):
        cx = x + (i % 2) * 306
        cy = 452 + (i // 2) * 104
        card(c, cx, cy, 290, 88)
        txt(c, cx + 18, cy + 40, p, "Unb-XB", 20, ACC)
        para(c, cx + 18, cy + 50, lab, "Man-SB", 12.5, 16, MUT, 254)
    footer(c)

def s07(c):
    kicker(c, 56, 56, "Мероприятия в салоне")
    h2(c, 56, 84, [
        [("День открытых дверей, старт продаж,", INK)],
        [("конференция дилеров", ACC)],
    ], size=38)
    chip(c, 1224 - 140, 52, "Решение C", "acid")

    cover_round(c, "as-tenet-night.jpg", 56, 212, 596, 286)
    shade(c, 56, 448, 596, 50, 0.97)
    txt(c, 72, 480, "Ночной тест-драйв в салоне: баннер, свет, зона презентации модели", "Man-SB", 12.5, DIM)

    items = [
        ("Сцена и каше для экрана", "Комплект «конференция под ключ» — производство и монтаж за 24 часа"),
        ("Фотозона с автомобилем", "Имиджевые фотозоны, бренд-зоны, press-wall для гостей и прессы"),
        ("Зона регистрации и навигация", "Стойки, таблички, оформление входной группы и путей гостей"),
    ]
    for i, (t, b) in enumerate(items):
        cy = 212 + i * 99
        card(c, 672, cy, 552, 88)
        txt(c, 692, cy + 32, t, "Unb-XB", 16, INK)
        para(c, 692, cy + 42, b, "Man-SB", 13.5, 19, MUT, 512)

    chip_row(c, 56, 560, ["Конференция под ключ — от 89 000 ₽", "Press-wall — от 22 000 ₽",
                          "Фотозоны — от 22 000 ₽", "Имиджевые фотозоны — от 120 000 ₽"],
             size=13)
    footer(c)

def s08(c):
    kicker(c, 56, 56, "Акции и срочная печать")
    h2(c, 56, 84, [[("Сезонные акции ", INK), ("без простоев", ACC)]], size=38)
    chip(c, 1224 - 140, 52, "Решение D", "acid")

    items = [
        ("Печать от 3 часов, баннеры за 12 часов",
         "Срочное оформление спецпредложений, трейд-ин, сезонных программ"),
        ("Сменные полотна брус-баннера",
         "Каркас остаётся у вас — на следующую акцию печатаем только полотно, экономия до 40%"),
        ("POS-продукция и полиграфия",
         "Промо-острова, навигационные стойки, ценники, буклеты, брендированные кубы"),
    ]
    for i, (t, b) in enumerate(items):
        cy = 206 + i * 118
        card(c, 56, cy, 548, 106)
        txt(c, 76, cy + 34, t, "Unb-XB", 16, INK)
        para(c, 76, cy + 44, b, "Man-SB", 13.5, 19, MUT, 508)

    cover_round(c, "as-haval-day.jpg", 624, 206, 600, 344)
    shade(c, 624, 500, 600, 50, 0.97)
    txt(c, 640, 532, "Полотно под акцию: каркас остаётся, печатаем только новую графику", "Man-SB", 12.5, DIM)

    chip_row(c, 56, 560, ["Баннеры — от 900 ₽/м²", "Брус-баннер — от 16 500 ₽",
                          "Монтаж и замена полотна — за 24 часа"], size=13)
    footer(c)

def s09(c):
    """Портфолио: брус-баннеры, которые уже стоят в автосалонах."""
    kicker(c, 56, 56, "Работы в автосалонах")
    h2(c, 56, 84, [[("Брус-баннеры ", INK), ("у наших дилеров", ACC)]], size=42)
    txt(c, 56, 166, "Скрытый деревянный каркас, полотно без складок и бликов — даже под вспышкой "
        "и со стороны витрины.", "Man-SB", 16, MUT)

    shots = [
        ("as-omoda-c5.jpg", "OMODA C5"),
        ("as-haval-f7.jpg", "HAVAL F7"),
        ("as-kgm-1.jpg", "KGM SsangYong"),
        ("as-hongqi.jpg", "HONGQI HQ9"),
        ("as-tenet-night.jpg", "TENET T4"),
        ("as-baltavtotrade-wide.jpg", "БАЛТАВТОТРЕЙД-М"),
    ]
    for i, (img, brand) in enumerate(shots):
        cx = 56 + (i % 3) * 392
        cy = 212 + (i // 3) * 200
        w_, h_ = 376, 184
        cover_round(c, img, cx, cy, w_, h_, 14)
        # плашка с брендом
        c.setFillColor(Color(0.031, 0.031, 0.043, alpha=0.88))
        c.roundRect(cx + 12, T(cy + h_ - 12), sw_(brand, "Man-B", 13) + 28, 30, 15, stroke=0, fill=1)
        txt(c, cx + 26, cy + h_ - 32, brand, "Man-B", 13, ACID)

    txt(c, 56, 628, "Форматы: отдельно стоящие конструкции, зоны выдачи, фотозоны с автомобилем, "
        "оформление тест-драйва и сезонных акций.", "Man-SB", 13.5, MUT)
    footer(c)

def s10(c):
    cover(c, "photozone.jpg", 0, 0, 1280, 720, focus=(0.5, 0.5), fade=("bottom", 0.15, 0.94))

    chip_row(c, 56, 320, ["Кейс", "Дилерская конференция", "2026"], ["acid", "o", "o"])
    h2(c, 56, 384, [
        [("Mitsubishi Motors —", INK)],
        [("дилерская конференция", ACC)],
    ], size=48)
    para(c, 56, 508, "Комплексное оформление конференции для постоянных партнёров в DoubleTree "
         "by Hilton Moscow — Vnukovo Airport: сцена под ключ, зона приветствия и пресс-зона.",
         "Man-M", 20, 29, MUT2, 850)
    chip_row(c, 56, 624, ["Каше для экрана 8×4,5 м", "Сцена: ковролин, раус, трибуна",
                          "Стойка регистрации", "Press-wall"], size=13)
    footer(c)

def s11(c):
    kicker(c, 56, 56, "Портфолио")
    h2(c, 56, 84, [[("Сроки, которые ", INK), ("мы уже выдерживали", ACC)]], size=44)

    cases = [
        ("MIKS Karting", "acc", "Гоночное оформление клуба",
         "Угловая фотозона с подсветкой, пресс-волл для награждения, виндеры по трассе, неон моста", "photozone.jpg"),
        ("РЖД Арена · 3 дня", "acid", "Светящаяся конструкция 5×3 м",
         "Разработали, изготовили и установили мультимедийную конструкцию за 3 дня — с ночным монтажом", "lightbox.jpg"),
        ("Burger King", "acc", "Комплексное оформление конференции",
         "Застройка мероприятия, фотозоны, оформление пространства — полный цикл от концепции до монтажа", "stand-festival.jpg"),
    ]
    for i, (tag, st, title, body, img) in enumerate(cases):
        cx = 56 + i * 392
        cy, w_, h_ = 206, 376, 424
        card(c, cx, cy, w_, h_)
        c.saveState()
        p = c.beginPath(); p.roundRect(cx, T(cy + h_), w_, h_, 18); c.clipPath(p, stroke=0, fill=0)
        cover(c, img, cx, cy, w_, 196)
        c.restoreState()
        chip(c, cx + 20, cy + 210, tag, st, 13, 14, 30)
        txt(c, cx + 20, cy + 274, title, "Unb-XB", 17, INK)
        para(c, cx + 20, cy + 290, body, "Man-SB", 13.5, 19.5, MUT, 336)
    footer(c)

def s12(c):
    kicker(c, 56, 56, "Преимущества")
    h2(c, 56, 84, [[("Почему автосалоны ", INK), ("работают с нами", ACC)]], size=44)

    adv = [
        ("01", "Собственное производство", "Центральное производство в Москве, Остаповский проезд — без наценок"),
        ("02", "Сроки в договоре", "Баннеры от 12 часов, конструкции от 3 дней, события — за 24 часа"),
        ("03", "Работа по брендбуку", "Проверка вылетов, разрешения и пантонов — бесплатно"),
        ("04", "Фикс-цена без сюрпризов", "Стоимость в КП не меняется по ходу работ"),
        ("05", "Монтаж без остановки", "Ночью и в выходные — салон продолжает продавать"),
        ("06", "Один договор на всё", "Проект, производство и монтаж — в одних руках, без субподряда"),
    ]
    for i, (n, t, b) in enumerate(adv):
        cx = 56 + (i % 3) * 394
        cy = 200 + (i // 3) * 152
        card(c, cx, cy, 378, 136)
        txt(c, cx + 22, cy + 40, n, "Unb-XB", 24, ACC)
        txt(c, cx + 22, cy + 76, t, "Unb-XB", 15, INK)
        para(c, cx + 22, cy + 88, b, "Man-SB", 13.5, 19, MUT, 334)

    shots = [("as-haval-side.jpg", "Скрытый каркас: полотно с торца идеально ровное", 520),
             ("as-kgm-1.jpg", "Брус-баннеры у дилеров KGM SsangYong", 356),
             ("as-haval-day2.jpg", "Смена полотна под акцию — каркас остаётся", 356)]
    x = 56
    for img, cap, w_ in shots:
        cover_round(c, img, x, 512, w_, 146, 16)
        # сплошная тёмная плашка под подпись (фото светлое, градиента мало)
        c.setFillColor(BG)
        c.rect(x, T(512 + 146), w_, 34, stroke=0, fill=1)
        txt(c, x + 14, 512 + 146 - 22, cap, "Man-SB", 12.5, DIM)
        x += w_ + 16
    footer(c)

def s13(c):
    kicker(c, 56, 56, "Процесс")
    h2(c, 56, 84, [[("Как проходит работа — ", INK), ("6 шагов", ACC)]], size=44)

    steps = [
        ("1", "Заявка и бесплатный замер", "Приезжаем, снимаем размеры, обсуждаем задачу и бюджет"),
        ("2", "Концепция и 3D", "Видите результат до производства, согласовываем детали"),
        ("3", "Смета и договор", "Прозрачная стоимость и сроки зафиксированы в договоре"),
        ("4", "Производство", "Свой цех + регулярные фотоотчёты о прогрессе"),
        ("5", "Доставка и монтаж", "Ночью или в выходные, без остановки работы салона"),
        ("6", "Сдача объекта", "Принимаем работу вместе и остаёмся на связи после сдачи"),
    ]
    for i, (n, t, b) in enumerate(steps):
        cx = 56 + (i % 3) * 268
        cy = 200 + (i // 3) * 158
        card(c, cx, cy, 254, 150)
        txt(c, cx + 20, cy + 42, n, "Unb-XB", 24, ACC)
        para(c, cx + 20, cy + 52, t, "Unb-XB", 14, 19, INK, 214)
        para(c, cx + 20, cy + 98, b, "Man-SB", 13, 18, MUT, 214)

    cover_round(c, "workshop.jpg", 866, 206, 358, 288, 16)
    shade(c, 866, 206 + 288 - 52, 358, 52, 0.97)
    txt(c, 880, 206 + 288 - 14, "Собственный цех: печать, фрезеровка, сборка", "Man-SB", 11.5, DIM)

    chip_row(c, 56, 560, ["КП в течение дня", "Замер в пределах МКАД — бесплатно", "Работаем по всей России"],
             ["acid", "o", "o"], size=13)
    footer(c)

def s14(c):
    kicker(c, 56, 56, "Форматы сотрудничества")
    h2(c, 56, 84, [[("Готовые пакеты ", INK), ("для автосалонов", ACC)]], size=44)

    packs = [
        ("Пакет A", "acc", "Бренд-зона ресепшн",
         "Стойка + объёмный логотип + навигация + элементы на стены. 3D до производства.",
         "от 250 000 ₽", "от 7 дней · срочно от 3 дней", "sm-reception-zone-1.jpg", False),
        ("Пакет B · хит", "acid", "Мероприятие в салоне",
         "Сцена + каше + фотозона + press-wall + стойка регистрации.",
         "от 89 000 ₽", "производство и монтаж за 24 часа", "as-tenet-night.jpg", True),
        ("Пакет C", "acc", "Фасад и навигация",
         "Световые вывески и буквы + баннеры на фасад + флаги + входная группа.",
         "по замеру", "логотип от 19 500 ₽/м · от 3 дней", "lightbox.jpg", False),
    ]
    for i, (tag, st, title, body, price, term, img, hit) in enumerate(packs):
        cx = 56 + i * 392
        cy, w_, h_ = 200, 376, 392
        card(c, cx, cy, w_, h_, stroke=(ACC if hit else LINE), sw=(1.6 if hit else 1))
        c.saveState()
        p = c.beginPath(); p.roundRect(cx, T(cy + h_), w_, h_, 18); c.clipPath(p, stroke=0, fill=0)
        cover(c, img, cx, cy, w_, 148)
        c.restoreState()
        chip(c, cx + 20, cy + 162, tag, st, 13, 14, 30)
        para(c, cx + 20, cy + 208, title, "Unb-XB", 18, 25, INK, 336)
        para(c, cx + 20, cy + 248, body, "Man-SB", 13.5, 19, MUT, 336)
        txt(c, cx + 20, cy + 326, price, "Unb-XB", 25, ACID)
        para(c, cx + 20, cy + 338, term, "Man-SB", 12.5, 17, MUT, 336)

    txt(c, 56, 636, "Цены указаны «от» и зависят от материалов, размеров и сложности дизайна. "
        "Точная стоимость фиксируется в коммерческом предложении после замера и не меняется по ходу работ.",
        "Man-SB", 13, MUT)
    footer(c)

def s15(c):
    cover(c, "as-tenet-t8.jpg", -30, 0, 1340, 720, focus=(0.55, 0.5), fade=("right", 0.985, 0.45))
    logo(c, 56, 48, 78)

    kicker(c, 56, 250, "Следующий шаг")
    h2(c, 56, 278, [
        [("Оперативно решим вашу", INK)],
        [("задачу ", INK), ("по брендингу", ACC)],
    ], size=54)
    para(c, 56, 414, "Напишите или позвоните — в течение дня подготовим коммерческое предложение "
         "с ценами и сроками. Замер в пределах МКАД — бесплатно.", "Man-M", 20, 29, MUT2, 700)

    contacts = [("ТЕЛЕФОН · 24/7", "+7 495 799-00-19", ACID, True),
                ("ПОЧТА", "sm-pro1@yandex.ru", INK, False),
                ("САЙТ", "sm-production.ru", INK, False)]
    x = 56
    for label, val, col, accented in contacts:
        wl = sw_(val, "Unb-XB", 24) + 56
        card(c, x, 500, wl, 92, stroke=(ACC if accented else LINE), sw=(1.5 if accented else 1))
        txt(c, x + 28, 534, label, "Man-B", 12, MUT)
        txt(c, x + 28, 572, val, "Unb-XB", 24, col)
        x += wl + 14

    chip_row(c, 56, 628, ["КП в течение дня", "24/7 производство и монтаж",
                          "Заявки ПН–ПТ 10:00–18:00", "Москва · Остаповский проезд"], size=13)

# =====================================================================
def build():
    c = canvas.Canvas(OUT, pagesize=(PW, PH), pageCompression=1)
    c.setTitle("SM-Production — Брендинг для автосалонов")
    c.setAuthor("SM-Production")
    c.setSubject("Презентация для дилерских центров: оперативное решение вопросов по брендингу")

    slides = [s01, s02, s03, s04, s05, s06, s07, s08, s09, s10, s11, s12, s13, s14, s15]
    PAGE[0] = 0
    for fn in slides:
        PAGE[0] += 1
        c.saveState()
        c.scale(SCALE, SCALE)                      # дизайн-система 1280×720
        c.setFillColor(BG); c.rect(0, 0, DW, DH, stroke=0, fill=1)
        fn(c)
        c.restoreState()
        c.showPage()
    c.save()
    print("PDF:", OUT, round(os.path.getsize(OUT) / 1048576, 2), "МБ")

if __name__ == "__main__":
    build()
