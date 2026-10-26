#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Новогоднее оформление — лукбук форматов SM-Production.
9 страниц 1920×1080 (отрисовка в 1,5× от дизайн-системы 1280×720).

Запуск:  python3 build_lookbook.py
Итог:    SM-Production_Novyy-god-2027.pdf
"""
import os
from PIL import Image, ImageFilter, ImageEnhance
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor, Color

BASE   = os.path.dirname(os.path.abspath(__file__))
VIZ    = os.path.join(BASE, "viz")
FONTS  = os.path.abspath(os.path.join(BASE, "..", "ca-avtosalony", "02_prezentaciya", "fonts"))
LOGO   = os.path.abspath(os.path.join(BASE, "..", "ca-avtosalony", "02_prezentaciya", "img", "logo-smproduction.png"))
OUT    = os.path.join(BASE, "SM-Production_Novyy-god-2027.pdf")
CACHE  = "/tmp/lb"

W, H = 1280.0, 720.0
S    = 1.5
PW, PH = W * S, H * S

BG   = HexColor("#0a0a0d")
CARD = HexColor("#14141c")
INK  = HexColor("#f4f2ec")
MUT  = HexColor("#98989f")
MUT2 = HexColor("#d9d6cd")
ACC  = HexColor("#ff4d1c")
ACID = HexColor("#d8ff3e")
LINE = Color(244/255, 242/255, 236/255, alpha=0.13)

for name, file in [("Unb", "Unbounded-400.ttf"), ("Unb-B", "Unbounded-700.ttf"),
                   ("Unb-XB", "Unbounded-800.ttf"), ("Man", "Manrope-400.ttf"),
                   ("Man-SB", "Manrope-600.ttf"), ("Man-B", "Manrope-700.ttf"),
                   ("Man-XB", "Manrope-800.ttf")]:
    pdfmetrics.registerFont(TTFont(name, os.path.join(FONTS, file)))

os.makedirs(CACHE, exist_ok=True)


def T(y):
    return H - y


def txt(c, x, y, s, font="Man", size=14, color=INK, anchor="l"):
    c.setFont(font, size)
    c.setFillColor(color)
    f = {"l": c.drawString, "r": c.drawRightString, "c": c.drawCentredString}[anchor]
    f(x, T(y), s)


def sw_(s, font, size):
    return pdfmetrics.stringWidth(s, font, size)


def wrap(c, x, y, text, font, size, color, maxw, lh=1.45):
    """простой перенос по словам"""
    words, line, out = text.split(), "", []
    for w in words:
        t = (line + " " + w).strip()
        if sw_(t, font, size) <= maxw:
            line = t
        else:
            out.append(line)
            line = w
    out.append(line)
    for i, l in enumerate(out):
        txt(c, x, y + i * size * lh, l, font, size, color)
    return y + (len(out) - 1) * size * lh


def kicker(c, x, y, label):
    c.setFillColor(ACC)
    c.rect(x, T(y + 3), 34, 3.2, stroke=0, fill=1)
    txt(c, x + 46, y + 3, label.upper(), "Man-B", 13, ACID)


def head(c, num, title, sub=""):
    c.setFillColor(BG)
    c.rect(0, 0, W, H, stroke=0, fill=1)
    kicker(c, 56, 46, f"Новый год 2027 · {num}")
    txt(c, 56, 96, title, "Unb-XB", 34, INK)
    if sub:
        txt(c, 56, 124, sub, "Man-SB", 14, MUT)


def chip(c, x, y, label, fill=None, color=INK, size=12, pad=14, h=28):
    w = sw_(label, "Man-B", size) + pad * 2
    if fill is None:
        c.setFillColor(Color(0.08, 0.08, 0.11, alpha=0.9))
        c.setStrokeColor(LINE)
        c.setLineWidth(1)
        c.roundRect(x, T(y + h), w, h, h / 2, stroke=1, fill=1)
    else:
        c.setFillColor(fill)
        c.roundRect(x, T(y + h), w, h, h / 2, stroke=0, fill=1)
    txt(c, x + w / 2, y + h / 2 + size * 0.36, label, "Man-B", size, color, "c")
    return w


def _prep(path, w_px, h_px):
    """кроп по центру под нужное соотношение + лёгкая цветокоррекция"""
    key = os.path.join(CACHE, f"{os.path.basename(path)[:-4]}_{w_px}x{h_px}.jpg")
    if os.path.exists(key):
        return key
    im = Image.open(path).convert("RGB")
    tw, th = w_px, h_px
    sc = max(tw / im.width, th / im.height)
    nw, nh = int(im.width * sc + 0.5), int(im.height * sc + 0.5)
    im = im.resize((nw, nh), Image.LANCZOS)
    l, t = (nw - tw) // 2, (nh - th) // 2
    im = im.crop((l, t, l + tw, t + th))
    im = ImageEnhance.Contrast(im).enhance(1.04)
    im.save(key, quality=88, optimize=True)
    return key


def img(c, path, x, y, w, h, r=16, px=1200, dark=0.0):
    """картинка в блоке x,y,w,h (верхний левый угол) со скруглением"""
    k = int(w * (px / 380)) if px else 1200
    p = _prep(path, k, int(k * h / w))
    c.saveState()
    pth = c.beginPath()
    pth.roundRect(x, T(y + h), w, h, r)
    c.clipPath(pth, stroke=0, fill=0)
    c.drawImage(p, x, T(y + h), w, h)
    if dark:
        c.setFillColor(Color(0, 0, 0, alpha=dark))
        c.rect(x, T(y + h), w, h, stroke=0, fill=1)
    c.restoreState()


def logo(c, x, y, h=40, alpha=1.0):
    im = Image.open(LOGO).convert("RGBA")
    w = h * im.width / im.height
    p = os.path.join(CACHE, f"logo_{int(h)}.png")
    if not os.path.exists(p):
        im.resize((int(w * 3), int(h * 3)), Image.LANCZOS).save(p)
    c.saveState()
    c.setFillAlpha(alpha)
    c.drawImage(p, x, T(y + h), w, h, mask="auto")
    c.restoreState()
    return w


def footer(c, num):
    c.setFillColor(Color(244/255, 242/255, 236/255, alpha=0.10))
    c.rect(56, T(676), 1168, 0.8, stroke=0, fill=1)
    logo(c, 56, 690, 14, 0.55)
    txt(c, 1224, 702, f"{num:02d}", "Man-B", 11, MUT, "r")


def caption(c, x, y, w, title, text=""):
    txt(c, x, y, title, "Man-B", 15, INK)
    if text:
        wrap(c, x, y + 22, text, "Man-SB", 12, MUT, w, 1.5)


# =====================================================================
def p01(c):
    """Обложка"""
    c.setFillColor(BG); c.rect(0, 0, W, H, stroke=0, fill=1)
    img(c, os.path.join(VIZ, "03-lounge.jpg"), 380, 0, 900, 720, r=0)
    # затемнение под текст слева
    c.saveState()
    c.setFillColor(Color(0.039, 0.039, 0.051, alpha=0.96))
    c.rect(0, 0, 520, H, stroke=0, fill=1)
    for i in range(40):
        c.setFillColor(Color(0.039, 0.039, 0.051, alpha=0.96 * (1 - i / 40) * 0.55))
        c.rect(380 + i * 6, 0, 6, H, stroke=0, fill=1)
    c.restoreState()

    logo(c, 56, 48, 40)
    txt(c, 56, 132, "СЕЗОН 2026 / 2027", "Man-B", 12, ACC)
    txt(c, 56, 214, "Новый год", "Unb-XB", 62, INK)
    txt(c, 56, 292, "в вашем", "Unb-XB", 62, INK)
    txt(c, 56, 370, "пространстве", "Unb-XB", 62, ACC)
    txt(c, 56, 432, "Фотозоны · ресепшн · офисы · витрины и входные группы",
        "Man-SB", 15, MUT2)
    c.setFillColor(Color(244/255, 242/255, 236/255, alpha=0.16))
    c.rect(56, T(470), 120, 1, stroke=0, fill=1)
    txt(c, 56, 508, "Визуализации форматов, ориентировочные цены и сроки.", "Man", 13, MUT)
    txt(c, 56, 530, "Производство и монтаж — Москва, 24/7.", "Man", 13, MUT)
    chip(c, 56, 566, "заезды с 15 ноября", ACID, BG)
    chip(c, 56 + sw_("заезды с 15 ноября", "Man-B", 12) + 28 + 10, 566, "демонтаж после праздников")


def p02(c):
    """Четыре направления"""
    head(c, "01", "Что делаем на Новый год",
         "Четыре направления, которые собираются вместе или по отдельности")

    items = [
        ("01-portal.jpg", "Фотозоны", "Арки, порталы и пресс-воллы с подсветкой и подиумом", "от 24 900 ₽"),
        ("02-reception.jpg", "Зона ресепшн", "Стойка, панель с подсветкой, гирлянды и объёмный логотип", "от 89 000 ₽"),
        ("07-office.jpg", "Офисы", "Дерево, световые завесы, лаунж-зоны и переговорные", "от 450 000 ₽"),
        ("05-facade.jpg", "Вход и витрины", "Козырьки, световые колонны, витрины ТЦ и шоурумов", "по проекту"),
    ]
    x = 56
    cw, ch = 280, 300
    for i, (f, title, desc, price) in enumerate(items):
        img(c, os.path.join(VIZ, f), x, 180, cw, 170, r=16)
        c.setFillColor(CARD)
        c.roundRect(x, T(180 + ch), cw, ch - 170, 16, stroke=0, fill=1)
        c.setFillColor(LINE); c.setStrokeColor(LINE); c.setLineWidth(1)
        c.roundRect(x, T(180 + ch), cw, ch, 16, stroke=1, fill=0)
        txt(c, x + 20, 380, title, "Unb-XB", 17, INK)
        wrap(c, x + 20, 406, desc, "Man-SB", 12, MUT, cw - 40, 1.5)
        txt(c, x + 20, 466, price, "Man-B", 13, ACID)
        x += cw + 16

    txt(c, 56, 540, "Один подрядчик на весь сезон: дизайн, производство, монтаж и демонтаж.",
        "Man-SB", 13, MUT2)
    txt(c, 56, 566, "Собираем комплект под бюджет — от одной фотозоны до оформления всего офиса.",
        "Man", 13, MUT)
    footer(c, 2)


def p03(c):
    """Фотозоны"""
    head(c, "02", "Фотозоны и пресс-воллы",
         "Главный кадр вечера — то, что останется в соцсетях гостей")

    img(c, os.path.join(VIZ, "01-portal.jpg"), 56, 168, 700, 430, r=18)
    chip(c, 78, 540, "портал 4 × 3 м · скрытый каркас · тёплая гирлянда", None, MUT2, 11, 12, 26)

    x = 800
    rows = [
        ("Конструкция", "Брус-каркас, баннер BlackBack, ткань или зеркальный полистирол"),
        ("Свет", "Гирлянда, контурная LED-подсветка, подиум с подсветкой снизу"),
        ("Декор", "Ель, ветки, шары, арт-объекты — по концепции"),
        ("Сборка", "2 часа на площадке, ночной заезд по согласованию"),
    ]
    y = 176
    for h, p in rows:
        txt(c, x, y, h, "Man-B", 10, MUT)
        y = wrap(c, x, y + 18, p, "Man-SB", 13, MUT2, 424, 1.5) + 34

    # размеры
    txt(c, x, y + 8, "СТАНДАРТНЫЕ РАЗМЕРЫ", "Man-B", 10, MUT)
    sizes = [("2 × 2 м", "24 900 ₽"), ("3 × 2,5 м", "38 300 ₽"), ("4 × 3 м", "53 500 ₽"), ("5 × 3 м", "65 800 ₽")]
    yy = y + 34
    for i, (s, p) in enumerate(sizes):
        if i % 2 == 0:
            c.setFillColor(Color(244/255, 242/255, 236/255, alpha=0.04))
            c.rect(x, T(yy + 28), 424, 28, stroke=0, fill=1)
        txt(c, x + 12, yy + 18, s, "Man-SB", 13, MUT2)
        txt(c, x + 412, yy + 18, p, "Man-B", 13, ACID, "r")
        yy += 32

    yb = yy + 16
    txt(c, x, yb, "Нестандарт считаем по площади: от 4 400 ₽/м² + 450 ₽ за метр периметра.",
        "Man", 12, MUT)
    txt(c, x, yb + 26, "Свет +18 000 ₽ · объёмные буквы +26 000 ₽ · подиум +21 000 ₽", "Man-SB", 12, MUT2)
    txt(c, x, yb + 52, "Срочный заказ — коэффициент 1,3.", "Man", 12, MUT)
    footer(c, 3)


def p04(c):
    """Брус-баннер"""
    head(c, "03", "Брус-баннер как новогодний фон",
         "Матовое полотно без складок и бликов — кадр не «плывёт» от вспышки")

    img(c, os.path.join(VIZ, "04-brus.jpg"), 56, 168, 760, 440, r=18)
    chip(c, 78, 552, "5 × 3 м · каркас полностью скрыт", None, MUT2, 11, 12, 26)

    x = 852
    txt(c, x, 190, "Почему именно он", "Unb-XB", 20, INK)
    y = 224
    for h, p in [
        ("Ровная поверхность", "Жёсткий деревянный каркас: ни складок, ни силуэта труб."),
        ("Без блика", "Матовый баннер не отражает вспышку и софиты — лица и фон читаются."),
        ("Любая форма", "Прямоугольник, арка, фигурный вырез под логотип или ёлку."),
        ("Быстрый монтаж", "Стандарт от 24 часов, сборка на площадке — около 2 часов."),
    ]:
        txt(c, x, y, h, "Man-B", 14, INK)
        y = wrap(c, x, y + 22, p, "Man", 12.5, MUT, 372, 1.5) + 34

    txt(c, x, y + 34, "от 16 500 ₽", "Unb-XB", 30, ACID)
    txt(c, x, y + 62, "печать и каркас, без монтажа", "Man", 12, MUT)
    txt(c, x, y + 96, "Декабрь — самый плотный месяц на производстве.", "Man-SB", 12, MUT2)
    txt(c, x, y + 118, "Согласуйте макет до 20 ноября, чтобы выбрать дату заезда.", "Man-SB", 12, MUT2)
    footer(c, 4)


def p05(c):
    """Ресепшн"""
    head(c, "04", "Зона ресепшн",
         "Первое, что видит гость: стойка, панель и свет")

    img(c, os.path.join(VIZ, "02-reception.jpg"), 560, 168, 664, 420, r=18)

    x = 56
    txt(c, x, 190, "Из чего собирается зона", "Unb-XB", 20, INK)
    items = [
        ("Панель с подсветкой", "Фрезерованный МДФ или акрил, контражур — тёплый или нейтральный"),
        ("Объёмный логотип", "19 500 ₽ за метр ширины, световой или несветовой"),
        ("Гирлянды и ветки", "Живая или искусственная ель, микро-лампы на 220 В"),
        ("Стойка ресепшн", "От 89 000 ₽ — стандарт; премиум с эмалью и акрилом — от 180 000 ₽"),
    ]
    y = 224
    for h, p in items:
        txt(c, x, y, h, "Man-B", 14, INK)
        y = wrap(c, x, y + 22, p, "Man", 12.5, MUT, 460, 1.5) + 34

    c.setFillColor(Color(244/255, 242/255, 236/255, alpha=0.05))
    c.roundRect(x, T(560), 464, 74, 16, stroke=0, fill=1)
    txt(c, x + 20, 512, "Зона ресепшн под ключ", "Man-B", 13, MUT2)
    txt(c, x + 20, 546, "от 250 000 ₽", "Unb-XB", 26, ACID)
    txt(c, x + 444, 546, "монтаж вечером или в выходные", "Man", 11.5, MUT, "r")
    footer(c, 5)


def p06(c):
    """Офис"""
    head(c, "05", "Офис целиком",
         "От входной группы до переговорных — в единой стилистике")

    img(c, os.path.join(VIZ, "07-office.jpg"), 56, 168, 620, 372, r=18)
    img(c, os.path.join(VIZ, "03-lounge.jpg"), 692, 168, 532, 212, r=18)

    txt(c, 692, 412, "Зоны, которые оформляем", "Unb-XB", 18, INK)
    zones = ["Входная группа и ресепшн", "Опенспейс и лаунж-зона", "Переговорные и кухня", "Лифтовые холлы и коридоры", "Фотозона для сотрудников"]
    y = 440
    for z in zones:
        c.setFillColor(ACC)
        c.circle(697, T(y - 5), 2.4, stroke=0, fill=1)
        txt(c, 710, y, z, "Man-SB", 12.5, MUT2)
        y += 24

    c.setFillColor(Color(244/255, 242/255, 236/255, alpha=0.05))
    c.roundRect(56, T(628), 1168, 74, 16, stroke=0, fill=1)
    txt(c, 76, 580, "Комплексное оформление офиса до 200 м²", "Man-B", 13, MUT2)
    txt(c, 76, 610, "от 450 000 ₽", "Unb-XB", 26, ACID)
    txt(c, 420, 610, "включая замер, концепцию, производство, монтаж и демонтаж после праздников",
        "Man", 12.5, MUT)
    footer(c, 6)


def p07(c):
    """Вход и витрины"""
    head(c, "06", "Вход, витрины, холлы",
         "Новогодняя рамка для тех, кто заходит с улицы")

    img(c, os.path.join(VIZ, "05-facade.jpg"), 56, 168, 560, 320, r=18)
    img(c, os.path.join(VIZ, "06-window.jpg"), 632, 168, 296, 320, r=18)

    caption(c, 56, 520, 300, "Козырек и фасад",
            "Гирлянда под козырьком, световые колонны, шары на ступенях — без монтажа на несущие элементы.")
    caption(c, 632, 520, 296, "Витрина ТЦ и шоурума",
            "Световой короб, подвесные снежинки на разной глубине, ели в снегу и шары на подложке.")
    caption(c, 960, 520, 300, "Лифтовой холл",
            "Световая панель, гирлянда по контуру, композиция из елей на подиуме.")

    img(c, os.path.join(VIZ, "08-corridor.jpg"), 960, 168, 264, 320, r=16)
    footer(c, 7)


def p08(c):
    """Цены и сроки"""
    head(c, "07", "Ориентировочные цены и сроки",
         "Точная смета — после замера и согласования макета")

    cols = [56, 470, 760, 980, 1120]
    headers = ["Позиция", "Изготовление", "Монтаж", "Стоимость от"]
    txt(c, cols[0], 178, headers[0], "Man-B", 10, MUT)
    txt(c, cols[1], 178, headers[1], "Man-B", 10, MUT)
    txt(c, cols[2], 178, headers[2], "Man-B", 10, MUT)
    txt(c, cols[3], 178, headers[3], "Man-B", 10, MUT)
    c.setFillColor(LINE); c.rect(56, T(190), 1168, 0.8, stroke=0, fill=1)

    rows = [
        ("Фотозона 2 × 2 м", "1 сутки", "2 часа", "24 900 ₽"),
        ("Фотозона 3 × 2,5 м", "1 сутки", "2 часа", "38 300 ₽"),
        ("Фотозона 4 × 3 м", "1–2 суток", "3 часа", "53 500 ₽"),
        ("Брус-баннер 5 × 3 м", "от 24 часов", "около 2 часов", "16 500 ₽"),
        ("Объёмный логотип на ресепшн", "3–5 дней", "ночной заезд", "19 500 ₽ / м"),
        ("Стойка ресепшн по дизайну", "7 дней", "ночной заезд", "89 000 ₽"),
        ("Зона ресепшн под ключ", "7–10 дней", "ночной заезд", "250 000 ₽"),
        ("Оформление офиса до 200 м²", "10–14 дней", "по графику", "450 000 ₽"),
        ("Витрина или входная группа", "по проекту", "ночной заезд", "по проекту"),
    ]
    y = 216
    for i, r in enumerate(rows):
        if i % 2 == 0:
            c.setFillColor(Color(244/255, 242/255, 236/255, alpha=0.035))
            c.rect(56, T(y + 30), 1168, 32, stroke=0, fill=1)
        txt(c, cols[0], y + 20, r[0], "Man-SB", 13, INK)
        txt(c, cols[1], y + 20, r[1], "Man", 12.5, MUT)
        txt(c, cols[2], y + 20, r[2], "Man", 12.5, MUT)
        txt(c, 1224, y + 20, r[3], "Man-B", 13, ACID, "r")
        y += 34

    txt(c, 56, 566, "Печать баннера — от 3 часов. Срочный монтаж — за 2 часа. Ночные заезды и выходные — по графику площадки.",
        "Man", 12, MUT)
    txt(c, 56, 592, "Замер в пределах МКАД бесплатный при заказе производства.", "Man", 12, MUT)
    txt(c, 56, 618, "Цены ориентировочные: зависят от материалов, размеров и сложности декора.",
        "Man-SB", 12, MUT2)
    footer(c, 8)


def p09(c):
    """Как работаем + контакты"""
    head(c, "08", "Как работаем", "Шесть шагов от заявки до демонтажа")

    steps = [
        ("Заявка и замер", "Смотрим площадку, снимаем размеры, обсуждаем бюджет."),
        ("Концепция", "Визуализация и паспорт конструкции — до производства."),
        ("Смета и договор", "Фиксированная стоимость и график заездов."),
        ("Производство", "Своё производство в Москве, фотоотчёты по этапам."),
        ("Монтаж", "Ночью или в выходные — чтобы не останавливать офис."),
        ("Демонтаж", "Убираем и вывозим после праздников, декор — на хранение."),
    ]
    x = 56
    for i, (h, p) in enumerate(steps):
        cw = 180
        c.setFillColor(CARD)
        c.roundRect(x, T(320), cw, 162, 16, stroke=0, fill=1)
        c.setStrokeColor(LINE); c.setLineWidth(1)
        c.roundRect(x, T(320), cw, 162, 16, stroke=1, fill=0)
        txt(c, x + 18, 214, f"0{i+1}", "Man-B", 11, ACC)
        txt(c, x + 18, 244, h, "Man-B", 13, INK)
        wrap(c, x + 18, 272, p, "Man", 11.5, MUT, cw - 36, 1.45)
        x += cw + 16

    c.setFillColor(Color(244/255, 242/255, 236/255, alpha=0.05))
    c.roundRect(56, T(620), 1168, 168, 18, stroke=0, fill=1)

    logo(c, 84, 480, 34)
    txt(c, 84, 556, "Напишите — соберём смету", "Man", 13, MUT2)
    txt(c, 84, 576, "и предложим свободные даты заезда.", "Man", 13, MUT2)

    txt(c, 500, 484, "+7 495 799-00-19", "Unb-XB", 22, INK)
    txt(c, 500, 516, "sm-pro1@yandex.ru", "Man-SB", 14, MUT2)
    txt(c, 500, 540, "sm-production.ru", "Man-SB", 14, MUT2)

    txt(c, 800, 484, "Заявки ПН–ПТ 10:00–18:00", "Man-SB", 12, MUT2)
    txt(c, 800, 506, "Производство и монтаж 24/7", "Man-SB", 12, MUT2)
    txt(c, 800, 540, "Москва, Остаповский проезд —", "Man", 12, MUT)
    txt(c, 800, 558, "центральное производство", "Man", 12, MUT)
    footer(c, 9)


def build():
    c = canvas.Canvas(OUT, pagesize=(PW, PH))
    c.setTitle("SM-Production — новогоднее оформление, сезон 2027")
    c.setAuthor("SM-Production")
    c.setSubject("Фотозоны, зона ресепшн, офисы, входные группы и витрины к Новому году")
    for page in (p01, p02, p03, p04, p05, p06, p07, p08, p09):
        c.saveState()
        c.scale(S, S)
        page(c)
        c.restoreState()
        c.showPage()
    c.save()
    print("PDF:", OUT, round(os.path.getsize(OUT) / 1048576, 2), "МБ")


if __name__ == "__main__":
    build()
