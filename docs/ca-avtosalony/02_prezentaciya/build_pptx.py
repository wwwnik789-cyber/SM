#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Сборка редактируемой версии презентации «Брендинг для автосалонов» в PowerPoint (.pptx).
15 слайдов 16:9. Каждый текст — отдельный текстовый блок (правится штатно),
фотографии — отдельные картинки (меняются штатно).

Вёрстка повторяет design-систему PDF: 1280×720 «пикселей» → 13.333×7.5 дюйма.
Шрифты Unbounded / Manrope: чтобы вёрстка совпала, установите TTF из папки fonts/.

Запуск:  python3 build_pptx.py
Итог:    SM-Production_Brending-avtosalonov.pptx
"""
import os, tempfile
from PIL import Image, ImageFont
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from lxml import etree

BASE  = os.path.dirname(os.path.abspath(__file__))
IMG   = os.path.join(BASE, "img")
FONTS = os.path.join(BASE, "fonts")
OUT   = os.path.join(BASE, "SM-Production_Brending-avtosalonov.pptx")

DW, DH = 1280.0, 720.0
PXE = 9525                                    # EMU в одном design-px (96 dpi)

# ---------- палитра ----------
BG    = RGBColor(0x0A, 0x0A, 0x0D)
CARD  = RGBColor(0x14, 0x14, 0x1C)
INK   = RGBColor(0xF4, 0xF2, 0xEC)
MUT   = RGBColor(0x98, 0x98, 0x9F)
MUT2  = RGBColor(0xD9, 0xD6, 0xCD)
DIM   = RGBColor(0xCF, 0xCC, 0xC4)
ACC   = RGBColor(0xFF, 0x4D, 0x1C)
ACID  = RGBColor(0xD8, 0xFF, 0x3E)
LINE  = RGBColor(0x3A, 0x3A, 0x40)

# ---------- шрифты: имя в PPTX + файл для измерений ----------
FONT_PPT = {
    "Unb":    ("Unbounded", False),
    "Unb-B":  ("Unbounded", True),
    "Unb-XB": ("Unbounded ExtraBold", False),
    "Man":    ("Manrope", False),
    "Man-M":  ("Manrope", False),
    "Man-SB": ("Manrope SemiBold", False),
    "Man-B":  ("Manrope", True),
    "Man-XB": ("Manrope ExtraBold", False),
}
FONT_FILE = {
    "Unb": "Unbounded-400.ttf", "Unb-B": "Unbounded-700.ttf", "Unb-XB": "Unbounded-800.ttf",
    "Man": "Manrope-400.ttf", "Man-M": "Manrope-500.ttf", "Man-SB": "Manrope-600.ttf",
    "Man-B": "Manrope-700.ttf", "Man-XB": "Manrope-800.ttf",
}
_fonts, _metric = {}, {}

def _font(key, size):
    k = (key, round(size, 2))
    if k not in _fonts:
        _fonts[k] = ImageFont.truetype(os.path.join(FONTS, FONT_FILE[key]), int(round(size)))
    return _fonts[k]

def tw(s, key, size):
    """ширина строки в design-px"""
    return _font(key, size).getlength(s)

def ascent(key, size):
    k = ("asc", key, round(size, 2))
    if k not in _metric:
        f = _font(key, size)
        a, d = f.getmetrics()
        _metric[k] = (a, d)
    return _metric[k][0]

def wrap(s, key, size, maxw):
    words, lines, cur = s.split(), [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if not cur or tw(t, key, size) <= maxw:
            cur = t
        else:
            lines.append(cur); cur = w_
    if cur:
        lines.append(cur)
    return lines

# ---------- картинки: обрезка + запечённый градиент ----------
_bg_rgb = (10, 10, 13)
_cache = {}

def prep(name, w, h, focus=(0.5, 0.5), fade=None):
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
    im = im.crop((left, top, left + nw, top + nh)).resize((max(2, int(w * 1.7)), max(2, int(h * 1.7))), Image.LANCZOS)

    if fade:
        d, a0, a1 = fade
        W_, H_ = im.size
        if d in ("right", "left"):
            vals = [int(round(255 * max(0.0, min(1.0, a0 + (a1 - a0) * (x / max(1, W_ - 1)))))) for x in range(W_)]
            if d == "left":
                vals = vals[::-1]
            mask = Image.frombytes("L", (W_, H_), bytes(vals) * H_)
        else:
            vals = [int(round(255 * max(0.0, min(1.0, a0 + (a1 - a0) * (y / max(1, H_ - 1)))))) for y in range(H_)]
            if d == "top":
                vals = vals[::-1]
            mask = Image.frombytes("L", (W_, H_), bytes(v for v in vals for _ in range(W_)))
        im = Image.composite(Image.new("RGB", im.size, _bg_rgb), im, mask)

    tmp = os.path.join(tempfile.gettempdir(), f"pptx_{abs(hash(key))}.jpg")
    im.save(tmp, quality=86, optimize=True)
    _cache[key] = tmp
    return tmp

# ---------- примитивы ----------
def _noshadow(shp):
    try:
        shp.shadow.inherit = False
    except Exception:
        pass

def _alpha(shp, pct):
    """прозрачность заливки: pct 0..100 (непрозрачность)"""
    fill = shp.fill._xPr.find('{http://schemas.openxmlformats.org/drawingml/2006/main}solidFill')
    if fill is None:
        return
    clr = fill[0]
    a = etree.SubElement(clr, '{http://schemas.openxmlformats.org/drawingml/2006/main}alpha')
    a.set("val", str(int(pct * 1000)))

def rect(sl, x, y, w, h, r=18, fill=CARD, line=None, lw=0.75, alpha=None):
    shape = MSO_SHAPE.ROUNDED_RECTANGLE if r > 0 else MSO_SHAPE.RECTANGLE
    shp = sl.shapes.add_shape(shape, Emu(int(x * PXE)), Emu(int(y * PXE)), Emu(int(w * PXE)), Emu(int(h * PXE)))
    if r > 0:
        try:
            shp.adjustments[0] = min(0.5, r / min(w, h))
        except Exception:
            pass
    shp.fill.solid(); shp.fill.fore_color.rgb = fill
    if alpha is not None:
        _alpha(shp, alpha)
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line; shp.line.width = Pt(lw)
    _noshadow(shp)
    return shp

def pic(sl, name, x, y, w, h, r=0, focus=(0.5, 0.5), fade=None):
    path = prep(name, w, h, focus, fade)
    p = sl.shapes.add_picture(path, Emu(int(x * PXE)), Emu(int(y * PXE)), Emu(int(w * PXE)), Emu(int(h * PXE)))
    if r > 0:  # скругление геометрии картинки
        sp = p._element.spPr
        geom = sp.find('{http://schemas.openxmlformats.org/drawingml/2006/main}prstGeom')
        if geom is not None:
            geom.set("prst", "roundRect")
            av = geom.find('{http://schemas.openxmlformats.org/drawingml/2006/main}avLst')
            if av is None:
                av = etree.SubElement(geom, '{http://schemas.openxmlformats.org/drawingml/2006/main}avLst')
            for ch in list(av):
                av.remove(ch)
            gd = etree.SubElement(av, '{http://schemas.openxmlformats.org/drawingml/2006/main}gd')
            gd.set("name", "adj")
            gd.set("fmla", f"val {int(min(0.5, r / min(w, h)) * 100000)}")
    return p

def _frame(sl, x, y, w, h, anchor=MSO_ANCHOR.TOP):
    tb = sl.shapes.add_textbox(Emu(int(x * PXE)), Emu(int(y * PXE)), Emu(int(w * PXE)), Emu(int(h * PXE)))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    tf.auto_size = None
    return tb, tf

def _run(p, s, key, size, color):
    r = p.add_run(); r.text = s
    name, bold = FONT_PPT[key]
    r.font.name = name
    r.font.bold = bold
    r.font.size = Pt(size * 0.75)
    r.font.color.rgb = color
    return r

def fit_size(s, key, size, maxw):
    """уменьшаем кегль, пока строка не влезет в maxw"""
    while size > 6 and tw(s, key, size) > maxw:
        size -= 0.5
    return size

def txt(sl, x, base_y, s, key="Man", size=16, color=INK, align="l", width=None, maxw=None):
    """одна строка, привязка по базовой линии; maxw — жёсткая граница по ширине"""
    if maxw:
        size = fit_size(s, key, size, maxw)
    w = width or (tw(s, key, size) + size * 2)
    top = base_y - ascent(key, size)
    h = size * 1.6
    if align == "r":
        x = x - w
    elif align == "c":
        x = x - w / 2
    tb, tf = _frame(sl, x, top, w, h)
    p = tf.paragraphs[0]
    p.alignment = {"l": PP_ALIGN.LEFT, "r": PP_ALIGN.RIGHT, "c": PP_ALIGN.CENTER}[align]
    _run(p, s, key, size, color)
    return w

def para(sl, x, top, s, key="Man-SB", size=15, leading=None, color=MUT, maxw=400):
    """абзац: строки переносятся заранее — как в PDF, вёрстка не «поедет»"""
    leading = leading or size * 1.42
    lines = wrap(s, key, size, maxw)
    h = len(lines) * leading + size
    tb, tf = _frame(sl, x, top, maxw + 8, h)
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.line_spacing = Pt(leading * 0.75)
        p.space_before = Pt(0); p.space_after = Pt(0)
        _run(p, ln, key, size, color)
    return len(lines) * leading

def chip(sl, x, y, label, style="o", size=14, padx=18, h=36):
    w = tw(label, "Man-B", size) + padx * 2
    if style == "acid":
        fill, line = ACID, None
    elif style == "acc":
        fill, line = CARD, ACC
    else:
        fill, line = RGBColor(0x14, 0x14, 0x1C), LINE
    shp = rect(sl, x, y, w, h, r=h / 2, fill=fill, line=line, lw=1)
    if style == "o":
        _alpha(shp, 85)
    col = BG if style == "acid" else (ACC if style == "acc" else INK)
    tb, tf = _frame(sl, x, y, w, h, anchor=MSO_ANCHOR.MIDDLE)
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    _run(p, label, "Man-B", size, col)
    return w

def chip_row(sl, x, y, labels, styles=None, gap=12, size=14, h=36):
    cx = x
    for i, lb in enumerate(labels):
        cx += chip(sl, cx, y, lb, styles[i] if styles else "o", size, h=h) + gap
    return cx - gap - x

def kicker(sl, x, y, label, size=15):
    rect(sl, x, y + 3, 34, 3.2, r=0, fill=ACC)
    txt(sl, x + 46, y + 3, label.upper(), "Man-B", size, ACID)

def logo(sl, x, y, h, name="logo-smproduction.png"):
    im = Image.open(os.path.join(IMG, name))
    ar = im.size[0] / im.size[1]
    sl.shapes.add_picture(os.path.join(IMG, name), Emu(int(x * PXE)), Emu(int(y * PXE)),
                          Emu(int(h * ar * PXE)), Emu(int(h * PXE)))
    return h * ar

def h2(sl, x, top, lines, size=46, lf=1.12):
    lh = size * lf
    for i, segs in enumerate(lines):
        cx = x
        base = top + size * 0.86 + i * lh
        for s, col in segs:
            txt(sl, cx, base, s, "Unb-XB", size, col)
            cx += tw(s, "Unb-XB", size)
    return len(lines) * lh

PAGE = [0]

def footer(sl):
    y = 704
    logo(sl, 56, y - 19, 19, "logo-mark.png")
    txt(sl, 56 + 32, y, "SM-PRODUCTION · БРЕНДИНГ ДЛЯ АВТОСАЛОНОВ", "Man-SB", 12.5, RGBColor(0x70, 0x70, 0x78))
    txt(sl, 1224, y, str(PAGE[0]).zfill(2), "Man-XB", 12.5, ACC, "r")

def notes(sl, text):
    sl.notes_slide.notes_text_frame.text = text

# =====================================================================
#  СЛАЙДЫ
# =====================================================================
def s01(sl):
    pic(sl, "as-omoda-c5.jpg", 0, 0, 1280, 720, focus=(0.55, 0.5), fade=("right", 1.0, 0.0))
    rect(sl, 0, 0, 640, 720, r=0, fill=BG, alpha=72)
    logo(sl, 56, 48, 112)

    kicker(sl, 56, 268, "Презентация для дилерских центров")
    h2(sl, 56, 296, [[("Брендинг", INK)], [("для ", INK), ("автосалонов", ACC)]], size=64, lf=1.06)

    para(sl, 56, 442, "Оперативно решаем вопросы по брендингу — от вывески на фасаде "
         "до мероприятия в шоуруме. Собственное производство, сроки от 3 дней.",
         "Man-M", 21, 30, MUT2, 660)
    chip_row(sl, 56, 534, ["Срочные заказы от 3 дней", "КП в течение дня", "24/7 производство и монтаж"],
             ["acid", "o", "o"])

    y = 664
    txt(sl, 56, y, "+7 495 799-00-19", "Man-B", 18, ACID)
    x = 56 + tw("+7 495 799-00-19", "Man-B", 18) + 30
    for s_ in ["sm-pro1@yandex.ru", "sm-production.ru"]:
        txt(sl, x, y, s_, "Man-SB", 18, MUT); x += tw(s_, "Man-SB", 18) + 30
    txt(sl, 56, y + 28, "Москва, Остаповский проезд — центральное производство", "Man-SB", 15, MUT)
    notes(sl, "Обложка. Ключевой посыл: оперативность + своё производство. "
              "Фото — наш брус-баннер в действующем салоне OMODA.")

def s02(sl):
    pic(sl, "workshop.jpg", 780, 0, 500, 720, fade=("left", 1.0, 0.0))

    kicker(sl, 56, 56, "Кто мы")
    h2(sl, 56, 84, [[("Производство,", INK)], [("а ", INK), ("не посредники", ACC)]], size=46)
    para(sl, 56, 206, "SM-Production — производственная компания полного цикла: от концепции "
         "и 3D-визуализации до печати, изготовления конструкций и монтажа на объекте. Свой цех "
         "на Остаповском проезде в Москве — вы не переплачиваете наценку посредников.",
         "Man-M", 20, 29, MUT2, 690)

    stats = [("от 3", "дней — срочные конструкции"), ("от 12", "часов — баннеры и печать"),
             ("24/7", "производство и монтаж"), ("ПН–ПТ", "приём заявок 10:00–18:00")]
    for i, (big, small) in enumerate(stats):
        cx = 56 + (i % 2) * 356
        cy = 330 + (i // 2) * 112
        rect(sl, cx, cy, 340, 96, r=18)
        txt(sl, cx + 24, cy + 52, big, "Unb-XB", 34, ACC)
        txt(sl, cx + 24, cy + 78, small.upper(), "Man-B", 12, MUT)
    chip_row(sl, 56, 574, ["Москва, Остаповский проезд — центральное производство",
                           "Доставка и монтаж по всей России"])
    footer(sl)
    notes(sl, "Кто мы. Акцент: собственное производство = сроки и цена без наценки посредников.")

def s03(sl):
    kicker(sl, 56, 56, "Задача")
    h2(sl, 56, 84, [[("Почему оформление салона —", INK)], [("это ", INK), ("не «просто баннеры»", ACC)]], size=46)

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
        rect(sl, cx, cy, 368, 180, r=18)
        txt(sl, cx + 22, cy + 34, title, "Unb-B", 15, ACID)
        para(sl, cx + 22, cy + 46, body, "Man-SB", 15, 21, MUT2, 324)
        para(sl, cx + 22, cy + 118, arrow, "Man-B", 14, 19.5, ACC, 324)

    pic(sl, "reception.jpg", 832, 218, 392, 180, r=18)
    pic(sl, "as-haval-day.jpg", 832, 414, 392, 180, r=18)
    footer(sl)
    notes(sl, "Боли клиента. Каждой боли — наш ответ (стрелка). Справа — реальные объекты.")

def s04(sl):
    kicker(sl, 56, 56, "Что делаем")
    h2(sl, 56, 84, [[("Четыре направления ", INK), ("для автосалона", ACC)]], size=44)

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
        rect(sl, cx, cy, 576, 210, r=18)
        pic(sl, img, cx + 14, cy + 14, 150, 182, r=12)
        tx = cx + 182
        chip(sl, tx, cy + 22, tag, "acc", 13, 14, 30)
        txt(sl, tx, cy + 88, title, "Unb-XB", 18, INK)
        para(sl, tx, cy + 104, body, "Man-SB", 14, 20, MUT, 376)
    footer(sl)
    notes(sl, "Карта направлений: интерьер, фасад, мероприятия, акции — можно начать с одного.")

def s05(sl):
    pic(sl, "sm-reception-zone-1.jpg", 0, 0, 570, 720, fade=("right", 1.0, 0.0))
    chip(sl, 40, 606, "Решение A", "acid")

    x = 626
    kicker(sl, x, 56, "Интерьер")
    h2(sl, x, 84, [[("Зона ресепшн", INK)], [("и интерьер ", INK), ("под ключ", ACC)]], size=38)

    bullets = [
        "Стойка ресепшн по индивидуальному дизайну: МДФ эмаль, акрил, подсветка",
        "Объёмный логотип с контражурной подсветкой",
        "Навигация, таблички, брендирование стен и зон ожидания",
        "Замер, 3D-визуализация, монтаж без остановки работы салона",
    ]
    y = 222
    for i, b in enumerate(bullets):
        txt(sl, x, y + 13, "✓", "Man-XB", 16, ACID)
        hh = para(sl, x + 26, y, b, "Man-SB", 16, 22, INK, 560)
        y += max(hh, 22) + 12
        if i < len(bullets) - 1:
            rect(sl, x, y, 598, 1, r=0, fill=LINE)
            y += 14

    prices = [("от 89 000 ₽", "стойка ресепшн стандарт"), ("от 250 000 ₽", "зона ресепшн «под ключ»"),
              ("от 19 500 ₽/м", "объёмный логотип"), ("от 7 дней", "срочно — от 3 дней")]
    for i, (p, lab) in enumerate(prices):
        cx = x + (i % 2) * 306
        cy = 466 + (i // 2) * 104
        rect(sl, cx, cy, 290, 88, r=18)
        txt(sl, cx + 18, cy + 40, p, "Unb-XB", 20, ACC)
        para(sl, cx + 18, cy + 50, lab, "Man-SB", 12.5, 16, MUT, 254)
    footer(sl)
    notes(sl, "Решение A: ресепшн под ключ. Цены «от» — уточняются замером.")

def s06(sl):
    pic(sl, "lightbox.jpg", 710, 0, 570, 720, fade=("left", 1.0, 0.0))
    chip(sl, 1224 - 40 - 150, 606, "Решение B", "acid")

    x = 56
    kicker(sl, x, 56, "Фасад и наружная реклама")
    h2(sl, x, 84, [[("Салон ", INK), ("видно издалека", ACC)]], size=38)

    bullets = [
        "Световые вывески, короба и объёмные буквы любой формы",
        "Баннеры и фасадная графика — печать от 3 часов",
        "Флаги, виндеры и уличные конструкции для входной зоны",
        "Защита от влаги и УФ — материалы для улицы",
    ]
    y = 208
    for i, b in enumerate(bullets):
        txt(sl, x, y + 13, "✓", "Man-XB", 16, ACID)
        hh = para(sl, x + 26, y, b, "Man-SB", 16, 22, INK, 520)
        y += max(hh, 22) + 12
        if i < len(bullets) - 1:
            rect(sl, x, y, 634, 1, r=0, fill=LINE)
            y += 14

    prices = [("от 900 ₽/м²", "печать баннеров"), ("от 300 000 ₽", "уличные конструкции"),
              ("от 4 500 ₽", "мобильные стенды"), ("от 12 часов", "изготовление и монтаж")]
    for i, (p, lab) in enumerate(prices):
        cx = x + (i % 2) * 306
        cy = 452 + (i // 2) * 104
        rect(sl, cx, cy, 290, 88, r=18)
        txt(sl, cx + 18, cy + 40, p, "Unb-XB", 20, ACC)
        para(sl, cx + 18, cy + 50, lab, "Man-SB", 12.5, 16, MUT, 254)
    footer(sl)
    notes(sl, "Решение B: фасад и наружка. Работаем по брендбуку производителя.")

def s07(sl):
    kicker(sl, 56, 56, "Мероприятия в салоне")
    h2(sl, 56, 84, [[("День открытых дверей, старт продаж,", INK)],
                    [("конференция дилеров", ACC)]], size=38)
    chip(sl, 1224 - 140, 52, "Решение C", "acid")

    pic(sl, "as-tenet-night.jpg", 56, 212, 596, 286, r=16)
    rect(sl, 56, 448, 596, 50, r=0, fill=BG, alpha=97)
    txt(sl, 72, 480, "Ночной тест-драйв в салоне: баннер, свет, зона презентации модели", "Man-SB", 12.5, DIM)

    items = [
        ("Сцена и каше для экрана", "Комплект «конференция под ключ» — производство и монтаж за 24 часа"),
        ("Фотозона с автомобилем", "Имиджевые фотозоны, бренд-зоны, press-wall для гостей и прессы"),
        ("Зона регистрации и навигация", "Стойки, таблички, оформление входной группы и путей гостей"),
    ]
    for i, (t, b) in enumerate(items):
        cy = 212 + i * 99
        rect(sl, 672, cy, 552, 88, r=18)
        txt(sl, 692, cy + 32, t, "Unb-XB", 16, INK)
        para(sl, 692, cy + 42, b, "Man-SB", 13.5, 19, MUT, 512)

    chip_row(sl, 56, 560, ["Конференция под ключ — от 89 000 ₽", "Press-wall — от 22 000 ₽",
                           "Фотозоны — от 22 000 ₽", "Имиджевые фотозоны — от 120 000 ₽"], size=13)
    footer(sl)
    notes(sl, "Решение C: мероприятия в салоне. ДОД, старт продаж, конференция дилеров.")

def s08(sl):
    kicker(sl, 56, 56, "Акции и срочная печать")
    h2(sl, 56, 84, [[("Сезонные акции ", INK), ("без простоев", ACC)]], size=38)
    chip(sl, 1224 - 140, 52, "Решение D", "acid")

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
        rect(sl, 56, cy, 548, 106, r=18)
        txt(sl, 76, cy + 34, t, "Unb-XB", 16, INK)
        para(sl, 76, cy + 44, b, "Man-SB", 13.5, 19, MUT, 508)

    pic(sl, "as-haval-day.jpg", 624, 206, 600, 344, r=16)
    rect(sl, 624, 500, 600, 50, r=0, fill=BG, alpha=97)
    txt(sl, 640, 532, "Полотно под акцию: каркас остаётся, печатаем только новую графику", "Man-SB", 12.5, DIM)

    chip_row(sl, 56, 560, ["Баннеры — от 900 ₽/м²", "Брус-баннер — от 16 500 ₽",
                           "Монтаж и замена полотна — за 24 часа"], size=13)
    footer(sl)
    notes(sl, "Решение D: акции и срочная печать. Сменное полотно = экономия до 40%.")

def s09(sl):
    kicker(sl, 56, 56, "Работы в автосалонах")
    h2(sl, 56, 84, [[("Брус-баннеры ", INK), ("у наших дилеров", ACC)]], size=42)
    txt(sl, 56, 166, "Скрытый деревянный каркас, полотно без складок и бликов — даже под вспышкой "
        "и со стороны витрины.", "Man-SB", 16, MUT)

    shots = [("as-omoda-c5.jpg", "OMODA C5"), ("as-haval-f7.jpg", "HAVAL F7"),
             ("as-kgm-1.jpg", "KGM SsangYong"), ("as-hongqi.jpg", "HONGQI HQ9"),
             ("as-tenet-night.jpg", "TENET T4"), ("as-baltavtotrade-wide.jpg", "БАЛТАВТОТРЕЙД-М")]
    for i, (img, brand) in enumerate(shots):
        cx = 56 + (i % 3) * 392
        cy = 212 + (i // 3) * 200
        pic(sl, img, cx, cy, 376, 184, r=14)
        bw = tw(brand, "Man-B", 13) + 28
        rect(sl, cx + 12, cy + 184 - 42, bw, 30, r=15, fill=BG, alpha=88)
        txt(sl, cx + 26, cy + 184 - 32, brand, "Man-B", 13, ACID)

    txt(sl, 56, 628, "Форматы: отдельно стоящие конструкции, зоны выдачи, фотозоны с автомобилем, "
        "оформление тест-драйва и сезонных акций.", "Man-SB", 13.5, MUT)
    footer(sl)
    notes(sl, "Портфолио: реальные объекты у дилеров — главный аргумент доверия.")

def s10(sl):
    pic(sl, "photozone.jpg", 0, 0, 1280, 720, focus=(0.5, 0.5), fade=("bottom", 0.15, 0.94))

    chip_row(sl, 56, 320, ["Кейс", "Дилерская конференция", "2026"], ["acid", "o", "o"])
    h2(sl, 56, 384, [[("Mitsubishi Motors —", INK)], [("дилерская конференция", ACC)]], size=48)
    para(sl, 56, 508, "Комплексное оформление конференции для постоянных партнёров в DoubleTree "
         "by Hilton Moscow — Vnukovo Airport: сцена под ключ, зона приветствия и пресс-зона.",
         "Man-M", 20, 29, MUT2, 850)
    chip_row(sl, 56, 624, ["Каше для экрана 8×4,5 м", "Сцена: ковролин, раус, трибуна",
                           "Стойка регистрации", "Press-wall"], size=13)
    footer(sl)
    notes(sl, "Кейс Mitsubishi Motors — единственный автомобильный клиент в портфолио.")

def s11(sl):
    kicker(sl, 56, 56, "Портфолио")
    h2(sl, 56, 84, [[("Сроки, которые ", INK), ("мы уже выдерживали", ACC)]], size=44)

    cases = [
        ("MIKS Karting", "acc", "Гоночное оформление клуба",
         "Угловая фотозона с подсветкой, пресс-волл для награждения, виндеры по трассе, неон моста", "photozone.jpg"),
        ("РЖД Арена · 3 дня", "acid", "Конструкция 5×3 м",
         "Разработали, изготовили и установили мультимедийную конструкцию за 3 дня — с ночным монтажом", "lightbox.jpg"),
        ("Burger King", "acc", "Оформление конференции",
         "Застройка мероприятия, фотозоны, оформление пространства — полный цикл от концепции до монтажа", "stand-festival.jpg"),
    ]
    for i, (tag, st, title, body, img) in enumerate(cases):
        cx = 56 + i * 392
        cy, w_, h_ = 206, 376, 424
        rect(sl, cx, cy, w_, h_, r=18)
        pic(sl, img, cx, cy, w_, 196, r=18)
        rect(sl, cx, cy + 160, w_, 36, r=0, fill=CARD)   # «срез» нижних углов фото
        chip(sl, cx + 20, cy + 210, tag, st, 13, 14, 30)
        txt(sl, cx + 20, cy + 274, title, "Unb-XB", 17, INK, maxw=336)
        para(sl, cx + 20, cy + 290, body, "Man-SB", 13.5, 19.5, MUT, 336)
    footer(sl)
    notes(sl, "Сроки: РЖД Арена — 3 дня от идеи до монтажа. Это снимает возражение «не успеете».")

def s12(sl):
    kicker(sl, 56, 56, "Преимущества")
    h2(sl, 56, 84, [[("Почему автосалоны ", INK), ("работают с нами", ACC)]], size=44)

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
        rect(sl, cx, cy, 378, 136, r=18)
        txt(sl, cx + 22, cy + 40, n, "Unb-XB", 24, ACC)
        txt(sl, cx + 22, cy + 76, t, "Unb-XB", 15, INK)
        para(sl, cx + 22, cy + 88, b, "Man-SB", 13.5, 19, MUT, 334)

    shots = [("as-haval-side.jpg", "Скрытый каркас: полотно с торца идеально ровное", 520),
             ("as-kgm-1.jpg", "Брус-баннеры у дилеров KGM SsangYong", 356),
             ("as-haval-day2.jpg", "Смена полотна под акцию — каркас остаётся", 356)]
    x = 56
    for img, cap, w_ in shots:
        pic(sl, img, x, 512, w_, 146, r=16)
        rect(sl, x, 512 + 146 - 34, w_, 34, r=0, fill=BG)
        txt(sl, x + 14, 512 + 146 - 22, cap, "Man-SB", 12.5, DIM)
        x += w_ + 16
    footer(sl)
    notes(sl, "Шесть причин. Фото внизу — доказательство: торец конструкции, дилеры, смена полотна.")

def s13(sl):
    kicker(sl, 56, 56, "Процесс")
    h2(sl, 56, 84, [[("Как проходит работа — ", INK), ("6 шагов", ACC)]], size=44)

    steps = [
        ("1", "Заявка и бесплатный замер", "Приезжаем, снимаем размеры, обсуждаем задачу и бюджет"),
        ("2", "Концепция и 3D", "Видите результат до производства, согласовываем детали"),
        ("3", "Смета и договор", "Прозрачная стоимость, сроки и гарантии зафиксированы"),
        ("4", "Производство", "Свой цех + регулярные фотоотчёты о прогрессе"),
        ("5", "Доставка и монтаж", "Ночью или в выходные, без остановки работы салона"),
        ("6", "Сдача объекта", "Принимаем работу вместе и остаёмся на связи после сдачи"),
    ]
    for i, (n, t, b) in enumerate(steps):
        cx = 56 + (i % 3) * 268
        cy = 206 + (i // 3) * 152
        rect(sl, cx, cy, 254, 136, r=18)
        txt(sl, cx + 20, cy + 42, n, "Unb-XB", 24, ACC)
        para(sl, cx + 20, cy + 52, t, "Unb-XB", 14, 19, INK, 214)
        para(sl, cx + 20, cy + 98, b, "Man-SB", 13, 18, MUT, 214)

    pic(sl, "workshop.jpg", 866, 206, 358, 288, r=16)
    rect(sl, 866, 206 + 288 - 52, 358, 52, r=0, fill=BG, alpha=97)
    txt(sl, 880, 206 + 288 - 14, "Собственный цех: печать, фрезеровка, сборка", "Man-SB", 11.5, DIM)

    chip_row(sl, 56, 560, ["КП в течение дня", "Замер в пределах МКАД — бесплатно", "Работаем по всей России"],
             ["acid", "o", "o"], size=13)
    footer(sl)
    notes(sl, "Процесс: 6 шагов. КП — в течение дня, замер по Москве бесплатный.")

def s14(sl):
    kicker(sl, 56, 56, "Форматы сотрудничества")
    h2(sl, 56, 84, [[("Готовые пакеты ", INK), ("для автосалонов", ACC)]], size=44)

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
        rect(sl, cx, cy, w_, h_, r=18, line=(ACC if hit else LINE), lw=(1.6 if hit else 1))
        pic(sl, img, cx, cy, w_, 148, r=18)
        rect(sl, cx, cy + 112, w_, 36, r=0, fill=CARD)
        chip(sl, cx + 20, cy + 162, tag, st, 13, 14, 30)
        para(sl, cx + 20, cy + 208, title, "Unb-XB", 18, 25, INK, 336)
        para(sl, cx + 20, cy + 248, body, "Man-SB", 13.5, 19, MUT, 336)
        txt(sl, cx + 20, cy + 326, price, "Unb-XB", 25, ACID)
        para(sl, cx + 20, cy + 338, term, "Man-SB", 12.5, 17, MUT, 336)

    txt(sl, 56, 636, "Цены указаны «от» и зависят от материалов, размеров и сложности дизайна. "
        "Точная стоимость фиксируется в коммерческом предложении после замера и не меняется по ходу работ.",
        "Man-SB", 13, MUT)
    footer(sl)
    notes(sl, "Три готовых пакета — менеджеру проще продавать, клиенту проще выбирать.")

def s15(sl):
    pic(sl, "as-tenet-t8.jpg", -30, 0, 1340, 720, focus=(0.55, 0.5), fade=("right", 0.985, 0.45))
    logo(sl, 56, 48, 78)

    kicker(sl, 56, 250, "Следующий шаг")
    h2(sl, 56, 278, [[("Оперативно решим вашу", INK)], [("задачу ", INK), ("по брендингу", ACC)]], size=54)
    para(sl, 56, 414, "Напишите или позвоните — в течение дня подготовим коммерческое предложение "
         "с ценами и сроками. Замер в пределах МКАД — бесплатно.", "Man-M", 20, 29, MUT2, 700)

    contacts = [("ТЕЛЕФОН · 24/7", "+7 495 799-00-19", ACID, True),
                ("ПОЧТА", "sm-pro1@yandex.ru", INK, False),
                ("САЙТ", "sm-production.ru", INK, False)]
    x = 56
    for label, val, col, accented in contacts:
        wl = tw(val, "Unb-XB", 24) + 56
        rect(sl, x, 500, wl, 92, r=18, line=(ACC if accented else LINE), lw=(1.5 if accented else 1))
        txt(sl, x + 28, 534, label, "Man-B", 12, MUT)
        txt(sl, x + 28, 572, val, "Unb-XB", 24, col)
        x += wl + 14

    chip_row(sl, 56, 628, ["КП в течение дня", "24/7 производство и монтаж",
                           "Заявки ПН–ПТ 10:00–18:00", "Москва · Остаповский проезд"], size=13)
    notes(sl, "Финал: прямой призыв. Контакты крупно — их видно в превью письма.")

# =====================================================================
def build():
    prs = Presentation()
    prs.slide_width = Emu(int(DW * PXE))
    prs.slide_height = Emu(int(DH * PXE))
    blank = prs.slide_layouts[6]

    slides = [s01, s02, s03, s04, s05, s06, s07, s08, s09, s10, s11, s12, s13, s14, s15]
    PAGE[0] = 0
    for fn in slides:
        PAGE[0] += 1
        sl = prs.slides.add_slide(blank)
        bgfill = sl.background.fill
        bgfill.solid(); bgfill.fore_color.rgb = BG
        fn(sl)

    prs.core_properties.title = "SM-Production — Брендинг для автосалонов"
    prs.core_properties.author = "SM-Production"
    prs.core_properties.subject = "Презентация для дилерских центров"
    prs.save(OUT)
    print("PPTX:", OUT, round(os.path.getsize(OUT) / 1048576, 2), "МБ")

if __name__ == "__main__":
    build()
