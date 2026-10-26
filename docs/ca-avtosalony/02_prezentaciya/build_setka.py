#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Дизайнерская сетка презентации «Брендинг для автосалонов» — PDF-спецификация.
5 страниц 1280×720: модульная сетка, оверлей на слайде, типографика, цвет, координаты.

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

W, H = 1280.0, 720.0
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
    txt(c, 0, 0, label, "Man-B", 10, color, "c"); c.restoreState()

def page_head(c, num, title, sub=""):
    c.setFillColor(BG); c.rect(0, 0, W, H, stroke=0, fill=1)
    kicker(c, 56, 46, f"Дизайнерская сетка · {num}")
    txt(c, 56, 96, title, "Unb-XB", 34, INK)
    if sub:
        txt(c, 56, 124, sub, "Man-SB", 14, MUT)

# =====================================================================
def page1(c):
    """Модульная сетка: поля, колонки, шаг"""
    page_head(c, "01", "Модульная сетка",
              "1280 × 720 px (16:9) · поле 56 px со всех сторон · контент 1168 × 608 px")

    L, R, TOP, BOT = 56, 1224, 196, 604
    c.setFillColor(PANEL); c.rect(L, T(BOT), R - L, BOT - TOP, stroke=0, fill=1)

    # колонки
    for i in range(3):
        cx = 56 + i * 394
        c.setFillColor(Color(1, 0.30, 0.11, alpha=0.07))
        c.rect(cx, T(BOT), 378, BOT - TOP, stroke=0, fill=1)
        c.setStrokeColor(Color(1, 0.30, 0.11, alpha=0.35)); c.setLineWidth(0.7)
        c.rect(cx, T(BOT), 378, BOT - TOP, stroke=1, fill=0)
        txt(c, cx + 12, TOP + 22, f"КОЛОНКА {i+1} · 378 px", "Man-B", 10, Color(1, 1, 1, alpha=0.35))

    # базовые линии 8 px
    for y in range(TOP + 8, BOT, 8):
        c.setStrokeColor(Color(0.96, 0.95, 0.92, 0.05)); c.setLineWidth(0.4)
        c.line(L, T(y), R, T(y))

    # граница поля
    c.setStrokeColor(Color(1, 0.30, 0.11, alpha=0.55)); c.setLineWidth(1); c.setDash(6, 5)
    c.rect(L, T(BOT), R - L, BOT - TOP, stroke=1, fill=0); c.setDash()

    # размеры — над областью, ниже подзаголовка
    dimh(c, L, 56 + 378, TOP - 30, "378")
    dimh(c, 56 + 378, 56 + 394, TOP - 30, "16 px", ACC)
    dimh(c, 56 + 394, 56 + 772, TOP - 30, "378")
    dimv(c, TOP, BOT, 40, f"{BOT - TOP} px контент")

    # подписи полей — вне сетки
    txt(c, 1128, TOP - 44, "верхнее поле 56 px", "Man-B", 10, ACC, "r")
    tag(c, 56, 618, "левое поле 56 px")
    tag(c, 1040, 618, "правое поле 56 px")

    # производные
    txt(c, 56, 648, "ПРОИЗВОДНЫЕ КОЛОНКИ", "Man-B", 10, MUT)
    variants = [("2 колонки", 576, 16, 2), ("3 колонки", 378, 16, 3), ("4 колонки", 280, 16, 4)]
    x0 = 56
    for label, colw, gap, n in variants:
        txt(c, x0, 674, f"{label} · {n}x{colw} + {gap}", "Man-SB", 11.5, MUT2)
        bx = x0
        total = (colw * n + gap * (n - 1))
        k = 300 / total
        for i in range(n):
            c.setFillColor(Color(216/255, 255/255, 62/255, alpha=0.38))
            c.rect(bx, T(700), colw * k, 10, stroke=0, fill=1)
            bx += (colw + gap) * k
        x0 += 400

    txt(c, 56, 714, "Базовый шаг — 8 px: все отступы, высоты строк и радиусы кратны 4 / 8.", "Man-SB", 11, MUT)
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
            img = pdf[11].render(scale=1360 / 960).to_pil()
            # размытие убирает мелкий текст, оставляя композицию
            img = img.filter(ImageFilter.GaussianBlur(2.2))
            img.save("/tmp/slide_bg.png")
            c.drawImage("/tmp/slide_bg.png", 150, 0, 980, 551)
            c.setFillColor(Color(0.039, 0.039, 0.051, alpha=0.80))
            c.rect(0, 0, W, H, stroke=0, fill=1)
        except Exception:
            pass

    kicker(c, 56, 34, "Дизайнерская сетка · 02")
    txt(c, 56, 82, "Ритм и сетка поверх слайда", "Unb-XB", 32, INK)
    txt(c, 56, 110, "Слева — горизонтали макета, справа — вертикальный ритм карточек", "Man-SB", 13, MUT)

    TOP, BOT = 156, 664
    guides = [(156, "кикер 56 / заголовок 84"), (244, "первый ряд 200–220"),
              (380, "второй ряд 352–372"), (516, "третий ряд 512–524"),
              (664, "safe-зона 664"), (704, "колонтитул 704")]
    for gy, label in guides:
        dashed(c, L, gy, R, gy, Color(216/255, 255/255, 62/255, alpha=0.45), 0.9, (5, 6))
        tag(c, 56, gy - 18, label, ACID, 10)

    # вертикали колонок
    for i in range(3):
        cx = 56 + i * 394
        c.setStrokeColor(Color(1, 0.30, 0.11, alpha=0.40)); c.setLineWidth(0.9)
        c.rect(cx, T(BOT), 378, BOT - TOP, stroke=1, fill=0)

    # образцы блоков по сетке
    blocks = [(244, 136, "карточка 378 × 136"), (380, 136, None), (516, 98, "фото 378 × 98")]
    for by, bh, label in blocks:
        c.setFillColor(Color(1, 0.30, 0.11, alpha=0.13))
        c.roundRect(56, T(by + bh), 378, bh, 16, stroke=0, fill=1)
        c.setStrokeColor(Color(1, 0.30, 0.11, alpha=0.65)); c.setLineWidth(1)
        c.roundRect(56, T(by + bh), 378, bh, 16, stroke=1, fill=0)
        if label:
            dimh(c, 56, 56 + 378, by + bh + 16, label)


    # вертикальный ритм справа
    dimv(c, 244, 380, 1256, "136")
    dimv(c, 380, 516, 1256, "136")
    dimv(c, 220, 244, 1216, "24", ACC)

    txt(c, 560, 700, "Шаг между рядами 16–24 px · карточка 136 px = 17 x 8 · фото-полоса 98 px",
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
        txt(c, 56, y + fs * 0.72, f"{size}", "Man-B", 12, ACC)
        txt(c, 150, y + fs * 0.72, sample, font, fs, color)
        txt(c, 900, y + 14, purpose, "Man-SB", 11.5, MUT)
        y += max(34, fs * 1.15) + 12
        hline(c, 56, y - 16, 1224, Color(244/255, 242/255, 236/255, alpha=0.07))

    # межстрочные
    txt(c, 56, 660, "Межстрочное: заголовки ×1.06–1.12 · текст ×1.40–1.45 · подписи ×1.35",
        "Man-SB", 11.5, MUT)
    txt(c, 56, 680, "Трекинг заголовков −0.5…−1 px · кикеры в капс с разрядкой 0.22em",
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
    txt(c, cx + 100, 210 + 35, "кислотный чип", "Man-B", 13, BG, "c")
    txt(c, cx + 216, 197, "h=36 · r=pill · текст 14 Man-B", "Man-SB", 11, MUT)

    # чип контурный
    c.setFillColor(Color(0.08, 0.08, 0.11, alpha=0.85)); c.setStrokeColor(LINE); c.setLineWidth(1)
    c.roundRect(cx, T(262), 200, 34, 17, stroke=1, fill=1)
    txt(c, cx + 100, 262 + 35, "контурный чип", "Man-B", 13, INK, "c")
    txt(c, cx + 216, 249, "обводка 13% · фон карточки", "Man-SB", 11, MUT)

    # карточка
    c.setFillColor(HexColor("#14141c")); c.setStrokeColor(LINE); c.setLineWidth(1)
    c.roundRect(cx, T(420), 300, 120, 18, stroke=1, fill=1)
    txt(c, cx + 20, 336, "Заголовок карточки", "Unb-XB", 15, INK)
    txt(c, cx + 20, 364, "Текст описания в две строки,", "Man-SB", 12, MUT)
    txt(c, cx + 20, 382, "межстрочное 1.42", "Man-SB", 12, MUT)
    txt(c, cx + 316, 330, "r = 18", "Man-B", 11, MUT2)
    txt(c, cx + 316, 348, "отступы 20–24", "Man-SB", 11, MUT)
    txt(c, cx + 316, 366, "заголовок 18", "Man-SB", 11, MUT)
    txt(c, cx + 316, 384, "текст 13.5", "Man-SB", 11, MUT)

    # отступы
    txt(c, 56, 592, "ШКАЛА ОТСТУПОВ", "Man-B", 10, MUT)
    steps = [8, 12, 16, 24, 36, 56, 64]
    x = 56
    for s in steps:
        c.setFillColor(Color(216/255, 255/255, 62/255, alpha=0.5))
        c.rect(x, T(626), s * 1.6, 12, stroke=0, fill=1)
        txt(c, x, 646, str(s), "Man-B", 10, MUT2)
        x += s * 1.6 + 34

    txt(c, 56, 682, "Правило: шаг между блоками 16 px, до заголовка 36–56 px, внутри карточки 20–24 px.",
        "Man-SB", 11.5, MUT)
    c.showPage()

def page5(c):
    """Координатная карта — для переноса в InDesign / Figma"""
    page_head(c, "05", "Координатная карта", "Ключевые X / Y всех слайдов — для точного переноса макета")

    cols = [
        ("X", [
            ("поле слева / справа", "56 / 1224"),
            ("колонка 1", "56"),
            ("колонка 2", "450"),
            ("колонка 3", "844"),
            ("ширина колонки", "378"),
            ("межколонник", "16"),
            ("сетка 2 кол.", "56 и 648"),
            ("сетка 4 кол.", "56 · 352 · 648 · 944"),
        ]),
        ("Y", [
            ("кикер", "56"),
            ("заголовок H2", "84"),
            ("подзаголовок", "138–166"),
            ("первый ряд карточек", "200–220"),
            ("второй ряд", "352–372"),
            ("фото-полоса", "512–524"),
            ("safe-зона (низ)", "664"),
            ("колонтитул", "704"),
        ]),
        ("Размеры", [
            ("карточка 3 кол.", "378 × 136"),
            ("карточка 2 кол.", "576 × 210"),
            ("карточка-кейс", "376 × 424"),
            ("фото в карточке", "150 × 182"),
            ("фото-полоса", "378 × 98"),
            ("чип", "h 36"),
            ("логотип на обложке", "h 112"),
            ("знак в колонтитуле", "h 19"),
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
        "1. Документ 1280 × 720 px, поля 56 px, 3 колонки по 378 px, gutter 16 px, baseline 8 px.",
        "2. Стили абзацев: H1 54/64, H2 46/44/38, карточка 18, текст 16/13.5, подпись 12.5, чип 14.",
        "3. Шрифты: Unbounded (400/700/800) и Manrope (400/500/600/700/800) — лежат в папке fonts/.",
        "4. Цвета — как на странице 04; границы rgba(244,242,236,0.13).",
        "5. Все тексты и фото — отдельными фреймами: файл PPTX собран так же, можно копировать блоками.",
    ]
    yy = 496
    for s in steps:
        txt(c, 56, yy, s, "Man-SB", 11.5, MUT2)
        yy += 26

    txt(c, 56, 660, "Сетка описывает фактический макет: build_pdf.py / build_pptx.py используют ровно эти координаты.",
        "Man-SB", 11.5, MUT)
    c.showPage()

def build():
    c = canvas.Canvas(OUT, pagesize=(W, H))
    c.setTitle("SM-Production — дизайнерская сетка презентации")
    c.setAuthor("SM-Production")
    c.setSubject("Модульная сетка, типографика, палитра и координаты презентации «Брендинг для автосалонов»")
    page1(c); page2(c); page3(c); page4(c); page5(c)
    c.save()
    print("PDF:", OUT, os.path.getsize(OUT) // 1024, "КБ")

if __name__ == "__main__":
    build()
