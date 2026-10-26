#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Дизайнерская сетка презентации «Брендинг для автосалонов» — PDF-спецификация.
5 страниц 1920×1080: все размеры на страницах — в 1920-системе (1 px = 1 pt):
модульная сетка, оверлей на слайде, типографика, цвет, координаты.

Запуск:  python3 build_setka.py
Итог:    SM-Production_Setka.pdf
"""
import os
from PIL import ImageFilter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor, Color

BASE  = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(BASE, "fonts")
OUT   = os.path.join(BASE, "SM-Production_Setka.pdf")
SLIDES_PDF = os.path.join(BASE, "SM-Production_Brending-avtosalonov.pdf")

W, H = 1280.0, 720.0      # система координат макета (в ней записаны все размеры)
S    = 1.5                # масштаб отрисовки страницы документа
PW, PH = W * S, H * S     # 1920 × 1080
BG    = HexColor("#0a0a0d")
PANEL = HexColor("#101015")
INK   = HexColor("#f4f2ec")
MUT   = HexColor("#98989f")
MUT2  = HexColor("#d9d6cd")
ACC   = HexColor("#ff4d1c")
ACID  = HexColor("#d8ff3e")
LINE  = Color(244/255, 242/255, 236/255, alpha=0.13)

for name, file in [("Unb", "Unbounded-400.ttf"), ("Unb-B", "Unbounded-700.ttf"),
                   ("Unb-XB", "Unbounded-800.ttf"), ("Man", "Manrope-400.ttf"),
                   ("Man-SB", "Manrope-600.ttf"), ("Man-B", "Manrope-700.ttf"),
                   ("Man-XB", "Manrope-800.ttf")]:
    pdfmetrics.registerFont(TTFont(name, os.path.join(FONTS, file)))

def num(v):
    """число по-русски: 81 вместо 81.0, 20,25 вместо 20.25"""
    return f"{v:.2f}".rstrip("0").rstrip(".").replace(".", ",")

def T(y): return H - y

def txt(c, x, y, s, font="Man", size=14, color=INK, anchor="l"):
    c.setFont(font, size); c.setFillColor(color)
    (c.drawString if anchor == "l" else c.drawRightString if anchor == "r" else c.drawCentredString)(x, T(y), s)

def sw_(s, font, size): return pdfmetrics.stringWidth(s, font, size)

def kicker(c, x, y, label):
    c.setFillColor(ACC); c.rect(x, T(y + 3), 34, 3.2, stroke=0, fill=1)
    txt(c, x + 46, y + 3, label.upper(), "Man-B", 13, ACID)

def tag(c, x, y, label, color=ACC, size=11, bg=True):
    w = sw_(label, "Man-B", size) + 16
    if bg:
        c.setFillColor(Color(0.04, 0.04, 0.05, alpha=0.94))
        c.roundRect(x - 8, T(y + 9), w, 21, 10, stroke=0, fill=1)
    txt(c, x, y, label, "Man-B", size, color)
    return w

def hline(c, x1, y, x2, color=LINE, w=0.7):
    c.setStrokeColor(color); c.setLineWidth(w); c.line(x1, T(y), x2, T(y))

def dashed(c, x1, y1, x2, y2, color, w=0.8, dash=(5, 6)):
    c.saveState(); c.setStrokeColor(color); c.setLineWidth(w); c.setDash(dash[0], dash[1])
    c.line(x1, T(y1), x2, T(y2)); c.restoreState()

def dimh(c, x1, x2, y, label, color=ACID):
    """горизонтальный размер со стрелками"""
    c.saveState(); c.setStrokeColor(color); c.setLineWidth(0.8)
    c.line(x1, T(y), x2, T(y))
    for xx, d in ((x1, 1), (x2, -1)):
        c.line(xx, T(y), xx + 6 * d, T(y - 3)); c.line(xx, T(y), xx + 6 * d, T(y + 3))
    c.restoreState()
    txt(c, (x1 + x2) / 2, y - 9, label, "Man-B", 10, color, "c")

def dimv(c, y1, y2, x, label, color=ACID):
    c.saveState(); c.setStrokeColor(color); c.setLineWidth(0.8)
    c.line(x, T(y1), x, T(y2))
    for yy, d in ((y1, 1), (y2, -1)):
        c.line(x, T(yy), x - 3, T(yy + 6 * d)); c.line(x, T(yy), x + 3, T(yy + 6 * d))
    c.restoreState()
    c.saveState(); c.translate(x - 7, T((y1 + y2) / 2)); c.rotate(90)
    c.setFont("Man-B", 10); c.setFillColor(color)
    c.drawCentredString(0, 0, label)          # в повёрнутой системе — строго у линии
    c.restoreState()

def page_head(c, num, title, sub=""):
    c.setFillColor(BG); c.rect(0, 0, W, H, stroke=0, fill=1)
    kicker(c, 56, 46, f"Дизайнерская сетка · {num}")
    txt(c, 56, 96, title, "Unb-XB", 34, INK)
    if sub:
        txt(c, 56, 124, sub, "Man-SB", 14, MUT)
    txt(c, 1224, 47, "страница 1920 × 1080 · единицы = px макета, 1 px = 1 pt", "Man-SB", 10.5, Color(0.6, 0.6, 0.63, alpha=0.75), "r")

# =====================================================================
def page1(c):
    """Модульная сетка: поля, колонки, шаг"""
    page_head(c, "01", "Модульная сетка",
              "1920 × 1080 px (16:9) · поле 84 px со всех сторон · контент 1752 × 912 px")

    L, R, TOP, BOT = 56, 1224, 196, 604
    c.setFillColor(PANEL); c.rect(L, T(BOT), R - L, BOT - TOP, stroke=0, fill=1)

    # колонки
    for i in range(3):
        cx = 56 + i * 394
        c.setFillColor(Color(1, 0.30, 0.11, alpha=0.07))
        c.rect(cx, T(BOT), 378, BOT - TOP, stroke=0, fill=1)
        c.setStrokeColor(Color(1, 0.30, 0.11, alpha=0.35)); c.setLineWidth(0.7)
        c.rect(cx, T(BOT), 378, BOT - TOP, stroke=1, fill=0)
        txt(c, cx + 12, TOP + 22, f"КОЛОНКА {i+1} · 567 px", "Man-B", 10, Color(1, 1, 1, alpha=0.35))

    # базовые линии 8 px
    for y in range(TOP + 8, BOT, 8):
        c.setStrokeColor(Color(0.96, 0.95, 0.92, 0.04)); c.setLineWidth(0.35)
        c.line(L, T(y), R, T(y))

    # граница поля
    c.setStrokeColor(Color(1, 0.30, 0.11, alpha=0.55)); c.setLineWidth(1); c.setDash(6, 5)
    c.rect(L, T(BOT), R - L, BOT - TOP, stroke=1, fill=0); c.setDash()

    # размеры — над областью, ниже подзаголовка
    dimh(c, L, 56 + 378, TOP - 30, "567")
    dimh(c, 56 + 378, 56 + 394, TOP - 30, "24 px", ACC)
    dimh(c, 56 + 394, 56 + 772, TOP - 30, "567")
    dimv(c, TOP, BOT, 40, "контент 1752 × 912 px")

    # подписи полей — вне сетки
    txt(c, 1128, TOP - 44, "верхнее поле 84 px", "Man-B", 10, ACC, "r")
    tag(c, 56, 612, "левое поле 84 px")
    tag(c, 1040, 612, "правое поле 84 px")

    # производные
    txt(c, 56, 636, "ПРОИЗВОДНЫЕ КОЛОНКИ", "Man-B", 10, MUT)
    variants = [("2 колонки", 576, 16, 2), ("3 колонки", 378, 16, 3), ("4 колонки", 280, 16, 4)]  # значения ×1,5 при подписи
    x0 = 56
    for label, colw, gap, n in variants:
        txt(c, x0, 660, f"{label} · {n}×{colw * 1.5:g} + {gap * 1.5:g}", "Man-SB", 11.5, MUT2)
        bx = x0
        total = (colw * n + gap * (n - 1))
        k = 300 / total
        for i in range(n):
            c.setFillColor(Color(216/255, 255/255, 62/255, alpha=0.38))
            c.rect(bx, T(684), colw * k, 9, stroke=0, fill=1)
            bx += (colw + gap) * k
        x0 += 400

    txt(c, 56, 700, "Базовый шаг — 12 px: все отступы, высоты строк и радиусы кратны 6 / 12.", "Man-SB", 11, MUT)
    c.showPage()

def page2(c):
    """Оверлей на реальном слайде (фон без текста)"""
    c.setFillColor(BG); c.rect(0, 0, W, H, stroke=0, fill=1)

    L, R = 56, 1224
    # слайд 12 как подложка: берём рендер и сильно приглушаем
    if os.path.exists(SLIDES_PDF):
        try:
            import pypdfium2 as pdfium
            from PIL import Image
            pdf = pdfium.PdfDocument(SLIDES_PDF)
            img = pdf[11].render(scale=(1360 * S) / pdf[11].get_size()[0]).to_pil()
            # размытие убирает мелкий текст, оставляя композицию
            from PIL import ImageEnhance
            img = ImageEnhance.Brightness(img).enhance(0.42)
            img = ImageEnhance.Color(img).enhance(0.55)
            img = img.filter(ImageFilter.GaussianBlur(3.4 * S))  # радиус в пикселях рендера, а не в единицах макета
            img.convert("RGB").save("/tmp/slide_bg.jpg", quality=90)
            c.drawImage("/tmp/slide_bg.jpg", 150, 0, 980, 551)
            c.setFillColor(Color(0.039, 0.039, 0.051, alpha=0.78))
            c.rect(0, 0, W, H, stroke=0, fill=1)
        except Exception:
            pass

    kicker(c, 56, 34, "Дизайнерская сетка · 02")
    txt(c, 56, 82, "Ритм и сетка поверх слайда", "Unb-XB", 32, INK)
    txt(c, 56, 110, "Слева — горизонтали макета, справа — вертикальный ритм карточек", "Man-SB", 13, MUT)

    TOP, BOT = 156, 664
    guides = [(156, "начало контента 234"), (244, "первый ряд 300–330"),
              (380, "второй ряд 528–558"), (516, "третий ряд 768–786"),
              (664, "safe-зона 996"), (704, "колонтитул 1056")]
    for gy, label in guides:
        dashed(c, L, gy, R, gy, Color(216/255, 255/255, 62/255, alpha=0.45), 0.9, (5, 6))
        tag(c, 56, gy - 18, label, ACID, 10)

    # вертикали колонок
    for i in range(3):
        cx = 56 + i * 394
        c.setStrokeColor(Color(1, 0.30, 0.11, alpha=0.40)); c.setLineWidth(0.9)
        c.rect(cx, T(BOT), 378, BOT - TOP, stroke=1, fill=0)

    # образцы блоков по сетке
    blocks = [(244, 136, "карточка 567 × 204"), (380, 136, None), (516, 98, "фото 567 × 147")]
    for by, bh, label in blocks:
        c.setFillColor(Color(1, 0.30, 0.11, alpha=0.13))
        c.roundRect(56, T(by + bh), 378, bh, 16, stroke=0, fill=1)
        c.setStrokeColor(Color(1, 0.30, 0.11, alpha=0.65)); c.setLineWidth(1)
        c.roundRect(56, T(by + bh), 378, bh, 16, stroke=1, fill=0)
        if label:
            dimh(c, 56, 56 + 378, by + bh + 16, label)


    # вертикальный ритм справа
    dimv(c, 244, 380, 1256, "204")
    dimv(c, 380, 516, 1256, "204")
    dimv(c, 220, 244, 1216, "36", ACC)

    txt(c, 560, 700, "Шаг между рядами 24–36 px · карточка 204 px = 17 × 12 · фото-полоса 147 px",
        "Man-SB", 11.5, MUT)
    c.showPage()

def page3(c):
    """Типографика"""
    page_head(c, "03", "Типографика", "Unbounded — заголовки · Manrope — текст · все размеры в px")

    rows = [
        ("Unb-XB", 54, "Оперативно решим вашу задачу", "H1 обложки и финала", INK),
        ("Unb-XB", 34, "Модульная сетка", "H1 спецификации", INK),
        ("Unb-XB", 46, "Почему оформление салона", "H2 основной", INK),
        ("Unb-XB", 38, "Зона ресепшн и интерьер", "H2 слайдов с фото", INK),
        ("Unb-XB", 18, "Зона ресепшн и интерьер", "Заголовок карточки", INK),
        ("Unb-B", 15, "БЕЗЛИКИЙ ШОУРУМ", "Метка-кикер в карточке", ACID),
        ("Man-SB", 16, "Световые вывески, короба и объёмные буквы", "Основной текст", MUT2),
        ("Man-SB", 13.5, "Сквозь призму технологий — подпись", "Текст в карточках", MUT),
        ("Man-B", 14, "Срочные заказы от 3 дней", "Чипы и кнопки", INK),
    ]
    y = 160
    txt(c, 56, 150, "РАЗМЕР", "Man-B", 10, MUT)
    txt(c, 150, 150, "НАЧЕРТАНИЕ И ПРИМЕР", "Man-B", 10, MUT)
    txt(c, 900, 150, "НАЗНАЧЕНИЕ", "Man-B", 10, MUT)
    hline(c, 56, 158, 1224)
    for font, size, sample, purpose, color in rows:
        fs = min(float(size), 30)
        txt(c, 56, y + fs * 0.72, num(size * 1.5), "Man-B", 12, ACC)
        txt(c, 150, y + fs * 0.72, sample, font, fs, color)
        txt(c, 900, y + 14, purpose, "Man-SB", 11.5, MUT)
        y += max(34, fs * 1.15) + 12
        hline(c, 56, y - 16, 1224, Color(244/255, 242/255, 236/255, alpha=0.07))

    # межстрочные
    txt(c, 56, 660, "Межстрочное: заголовки ×1.06–1.12 · текст ×1.40–1.45 · подписи ×1.35",
        "Man-SB", 11.5, MUT)
    txt(c, 56, 680, "Трекинг заголовков −0.75…−1.5 px · кикеры в капс с разрядкой 0.22em",
        "Man-SB", 11.5, MUT)
    c.showPage()

def page4(c):
    """Цвет, компоненты, отступы"""
    page_head(c, "04", "Цвет и компоненты", "Палитра, радиусы, правила оформления")

    colors = [
        ("#0A0A0D", HexColor("#0a0a0d"), "Фон слайда"),
        ("#14141C", HexColor("#14141c"), "Карточки"),
        ("#F4F2EC", HexColor("#f4f2ec"), "Основной текст"),
        ("#D9D6CD", HexColor("#d9d6cd"), "Текст поверх фото"),
        ("#98989F", HexColor("#98989f"), "Второстепенный текст"),
        ("#FF4D1C", HexColor("#ff4d1c"), "Акцент, цифры, стрелки"),
        ("#D8FF3E", HexColor("#d8ff3e"), "Кислотный: кикеры, цены"),
        ("#3A3A40", HexColor("#3a3a40"), "Границы (13% от текста)"),
    ]
    txt(c, 56, 160, "ПАЛИТРА", "Man-B", 10, MUT)
    for i, (hexv, col, label) in enumerate(colors):
        cy = 180 + i * 48
        c.setFillColor(col); c.setStrokeColor(LINE); c.setLineWidth(1)
        c.roundRect(56, T(cy + 32), 56, 32, 6, stroke=1, fill=1)
        txt(c, 128, cy + 22, hexv, "Man-B", 13, INK)
        txt(c, 232, cy + 22, label, "Man-SB", 12, MUT)

    # компоненты
    cx = 560
    txt(c, cx, 160, "КОМПОНЕНТЫ", "Man-B", 10, MUT)

    # чип кислотный
    c.setFillColor(HexColor("#d8ff3e")); c.roundRect(cx, T(210), 200, 34, 17, stroke=0, fill=1)
    txt(c, cx + 100, 199, "кислотный чип", "Man-B", 13, BG, "c")
    txt(c, cx + 216, 197, "h=54 · r=pill · текст 21 Man-B", "Man-SB", 11, MUT)

    # чип контурный
    c.setFillColor(Color(0.08, 0.08, 0.11, alpha=0.85)); c.setStrokeColor(LINE); c.setLineWidth(1)
    c.roundRect(cx, T(262), 200, 34, 17, stroke=1, fill=1)
    txt(c, cx + 100, 251, "контурный чип", "Man-B", 13, INK, "c")
    txt(c, cx + 216, 249, "обводка 13% · фон карточки", "Man-SB", 11, MUT)

    # карточка
    c.setFillColor(HexColor("#14141c")); c.setStrokeColor(LINE); c.setLineWidth(1)
    c.roundRect(cx, T(420), 300, 120, 18, stroke=1, fill=1)
    txt(c, cx + 20, 336, "Заголовок карточки", "Unb-XB", 15, INK)
    txt(c, cx + 20, 364, "Текст описания в две строки,", "Man-SB", 12, MUT)
    txt(c, cx + 20, 382, "межстрочное 1.42", "Man-SB", 12, MUT)
    txt(c, cx + 316, 330, "r = 27", "Man-B", 11, MUT2)
    txt(c, cx + 316, 348, "отступы 30–36", "Man-SB", 11, MUT)
    txt(c, cx + 316, 366, "заголовок 27", "Man-SB", 11, MUT)
    txt(c, cx + 316, 384, "текст 20", "Man-SB", 11, MUT)

    # отступы
    txt(c, 56, 592, "ШКАЛА ОТСТУПОВ", "Man-B", 10, MUT)
    steps = [12, 18, 24, 36, 54, 84, 96]
    x = 56
    for s in steps:
        c.setFillColor(Color(216/255, 255/255, 62/255, alpha=0.5))
        c.rect(x, T(626), s / 1.5 * 1.6, 12, stroke=0, fill=1)
        txt(c, x, 646, str(s), "Man-B", 10, MUT2)
        x += s / 1.5 * 1.6 + 34

    txt(c, 56, 682, "Правило: шаг между блоками 24 px, до заголовка 54–84 px, внутри карточки 30–36 px.",
        "Man-SB", 11.5, MUT)
    c.showPage()

def page5(c):
    """Координатная карта — для переноса в InDesign / Figma"""
    page_head(c, "05", "Координатная карта", "Ключевые X / Y всех слайдов — для точного переноса макета")

    cols = [
        ("X", [
            ("поле слева / справа", "84 / 1836"),
            ("колонка 1", "84"),
            ("колонка 2", "675"),
            ("колонка 3", "1266"),
            ("ширина колонки", "567"),
            ("межколонник", "24"),
            ("сетка 2 кол.", "84 и 972"),
            ("сетка 4 кол.", "84 · 528 · 972 · 1416"),
        ]),
        ("Y", [
            ("кикер", "84"),
            ("заголовок H2", "126"),
            ("подзаголовок", "207–249"),
            ("первый ряд карточек", "300–330"),
            ("второй ряд", "528–558"),
            ("фото-полоса", "768–786"),
            ("safe-зона (низ)", "996"),
            ("колонтитул", "1056"),
        ]),
        ("Размеры", [
            ("карточка 3 кол.", "567 × 204"),
            ("карточка 2 кол.", "864 × 315"),
            ("карточка-кейс", "564 × 636"),
            ("фото в карточке", "225 × 273"),
            ("фото-полоса", "567 × 147"),
            ("чип", "h 54"),
            ("логотип на обложке", "h 168"),
            ("знак в колонтитуле", "h 28,5"),
        ]),
    ]
    x = 56
    for title, rows in cols:
        txt(c, x, 160, title.upper(), "Man-B", 10, MUT)
        yy = 186
        for label, val in rows:
            txt(c, x, yy, label, "Man-SB", 11.5, MUT2)
            txt(c, x + 250, yy, val, "Man-B", 11.5, ACID, "r")
            hline(c, x, yy + 8, x + 250, Color(244/255, 242/255, 236/255, alpha=0.07))
            yy += 30
        x += 394

    txt(c, 56, 470, "ПЕРЕНОС В INDESIGN / FIGMA", "Man-B", 10, MUT)
    steps = [
        "1. Документ 1920 × 1080 px: поля 84 px, 3 колонки по 567 px, gutter 24 px, baseline 12 px.",
        "2. Стили абзацев: H1 81/96, H2 69 / 66 / 57, карточка 27, текст 24 / 20, подпись 18,75, чип 21.",
        "3. Шрифты: Unbounded (400/700/800) и Manrope (400/500/600/700/800) — лежат в папке fonts/.",
        "4. Цвета — как на странице 04; границы rgba(244,242,236,0.13).",
        "5. Все тексты и фото — отдельными фреймами: файл PPTX собран так же, можно копировать блоками.",
        "6. PPTX: слайд 13,333 × 7,5 дюйма — та же сетка; при экспорте в 1920 × 1080 px размеры совпадают.",
    ]
    yy = 496
    for s in steps:
        txt(c, 56, yy, s, "Man-SB", 11.5, MUT2)
        yy += 26

    txt(c, 56, 660, "Сетка описывает фактический макет: PDF-презентация собрана в 1920 × 1080 px с ровно этими координатами.",
        "Man-SB", 11.5, MUT)
    c.showPage()

def build():
    c = canvas.Canvas(OUT, pagesize=(PW, PH))
    c.setTitle("SM-Production — дизайнерская сетка презентации")
    c.setAuthor("SM-Production")
    c.setSubject("Модульная сетка, типографика, палитра и координаты презентации «Брендинг для автосалонов»")
    for page in (page1, page2, page3, page4, page5):
        c.saveState(); c.scale(S, S)
        page(c)          # showPage() сам сбрасывает состояние страницы
    c.save()
    print("PDF:", OUT, os.path.getsize(OUT) // 1024, "КБ")

if __name__ == "__main__":
    build()
