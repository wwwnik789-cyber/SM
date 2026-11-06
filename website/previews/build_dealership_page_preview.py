#!/usr/bin/env python3
"""Build a 16:9 PDF preview of the dealership landing page."""
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.colors import Color, HexColor, white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

ROOT = Path(__file__).resolve().parents[2]
MEDIA = ROOT / "website" / "public" / "media"
OUT = Path(__file__).with_name("SM-Production-dealership-page-preview.pdf")
PAGE = (960, 540)
W, H = PAGE

BG = HexColor("#0B0D10")
BG2 = HexColor("#12151A")
CARD = HexColor("#171B21")
IVORY = HexColor("#ECE9E1")
INK = HexColor("#17191D")
MUTED = HexColor("#A0A5AE")
DARK_MUTED = HexColor("#62656B")
ACCENT = HexColor("#FF4D1C")
ACID = HexColor("#D8FF3E")
LINE = Color(1, 1, 1, alpha=0.12)
DARK_LINE = Color(0.09, 0.1, 0.11, alpha=0.16)

FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
pdfmetrics.registerFont(TTFont("DV", FONT_REG))
pdfmetrics.registerFont(TTFont("DVB", FONT_BOLD))


def cover_image(c, path, x, y, w, h, focus_x=0.5, focus_y=0.5):
    img = ImageReader(str(path))
    iw, ih = img.getSize()
    scale = max(w / iw, h / ih)
    dw, dh = iw * scale, ih * scale
    dx = x - (dw - w) * focus_x
    dy = y - (dh - h) * focus_y
    c.saveState()
    clip = c.beginPath(); clip.rect(x, y, w, h)
    c.clipPath(clip, stroke=0, fill=0)
    c.drawImage(img, dx, dy, width=dw, height=dh, mask="auto")
    c.restoreState()


def fit_image(c, path, x, y, w, h, radius=12):
    c.saveState()
    clip = c.beginPath(); clip.roundRect(x, y, w, h, radius)
    c.clipPath(clip, stroke=0, fill=0)
    cover_image(c, path, x, y, w, h)
    c.restoreState()


def text(c, value, x, y, size=12, color=white, font="DV"):
    c.setFillColor(color); c.setFont(font, size); c.drawString(x, y, value)


def wrap_lines(value, font, size, max_width):
    words = value.split()
    lines, current = [], ""
    for word in words:
        test = f"{current} {word}".strip()
        if not current or pdfmetrics.stringWidth(test, font, size) <= max_width:
            current = test
        else:
            lines.append(current); current = word
    if current: lines.append(current)
    return lines


def paragraph(c, value, x, y, max_width, size=11, leading=16, color=MUTED, font="DV", max_lines=None):
    lines = wrap_lines(value, font, size, max_width)
    if max_lines: lines = lines[:max_lines]
    c.setFillColor(color); c.setFont(font, size)
    for line in lines:
        c.drawString(x, y, line); y -= leading
    return y


def title(c, value, x, y, max_width, size=30, leading=35, color=white):
    lines = wrap_lines(value, "DVB", size, max_width)
    c.setFillColor(color); c.setFont("DVB", size)
    for line in lines:
        c.drawString(x, y, line); y -= leading
    return y


def kicker(c, value, x, y, color=ACCENT):
    c.setStrokeColor(color); c.setLineWidth(2); c.line(x, y + 3, x + 30, y + 3)
    text(c, value.upper(), x + 42, y, 7.5, color, "DVB")


def bullet(c, value, x, y, max_width, color=white, dot_color=ACCENT, size=9.3):
    c.setFillColor(dot_color); c.circle(x + 3, y + 4, 2.2, fill=1, stroke=0)
    return paragraph(c, value, x + 13, y, max_width - 13, size=size, leading=13, color=color)


def card(c, x, y, w, h, fill=CARD, stroke=LINE, radius=14):
    c.setFillColor(fill); c.setStrokeColor(stroke); c.setLineWidth(0.8)
    c.roundRect(x, y, w, h, radius, fill=1, stroke=1)


def footer(c, page, light=False):
    color = Color(0.09, 0.1, 0.11, alpha=0.5) if light else Color(1, 1, 1, alpha=0.45)
    text(c, "SM PRODUCTION · ПРЕВЬЮ СТРАНИЦЫ «ОФОРМЛЕНИЕ АВТОСАЛОНОВ»", 38, 20, 6.5, color, "DVB")
    c.setFillColor(color); c.setFont("DVB", 7); c.drawRightString(W - 38, 20, f"{page:02}")


def new_page(c, number, bg=BG, light=False):
    c.setFillColor(bg); c.rect(0, 0, W, H, fill=1, stroke=0)
    footer(c, number, light)


def build():
    c = canvas.Canvas(str(OUT), pagesize=PAGE)
    c.setTitle("Превью страницы «Оформление автосалонов»")
    c.setAuthor("SM Production")
    c.setSubject("Премиальная посадочная страница для дилерских центров")

    # 1 — Hero
    c.setFillColor(BG); c.rect(0, 0, W, H, fill=1, stroke=0)
    cover_image(c, MEDIA / "dealer-branding-hero.jpg", 545, 0, W - 545, H, 0.65, 0.5)
    # Opaque stepped transition is deliberate: it renders consistently in every PDF viewer.
    shades = ["#0B0D10", "#11151A", "#1A2027", "#242C34", "#303942"]
    for i, shade in enumerate(shades):
        c.setFillColor(HexColor(shade)); c.rect(525 + i * 16, 0, 18, H, fill=1, stroke=0)
    kicker(c, "Решения для дилерских центров", 52, 438)
    y = title(c, "Оформление автосалонов", 52, 388, 525, 39, 44)
    c.setFillColor(ACCENT); c.setFont("DVB", 39); c.drawString(52, y, "и дилерских центров")
    paragraph(c, "Дизайн, производство и монтаж интерьера, POS, зон выдачи, презентаций моделей, навигации и фасадных элементов.", 52, y - 42, 500, 12, 18, Color(1,1,1,alpha=0.74))
    c.setFillColor(ACCENT); c.roundRect(52, 132, 212, 42, 9, fill=1, stroke=0)
    text(c, "ЗАКАЗАТЬ КОНСУЛЬТАЦИЮ", 70, 147, 8.2, white, "DVB")
    chips = ["Дизайн по брендбуку", "Собственное производство", "Доставка и монтаж", "Несколько адресов"]
    cx = 52
    for label in chips:
        tw = pdfmetrics.stringWidth(label, "DVB", 6.8) + 25
        c.setFillColor(Color(0.04,0.05,0.06,alpha=0.83)); c.setStrokeColor(LINE); c.roundRect(cx, 62, tw, 28, 7, fill=1, stroke=1)
        text(c, "◆", cx + 9, 72, 6.5, ACCENT, "DVB"); text(c, label, cx + 19, 72, 6.8, white, "DVB"); cx += tw + 8
    footer(c, 1); c.showPage()

    # 2 — Client journey
    new_page(c, 2, IVORY, True)
    kicker(c, "От задачи — к единой системе", 42, 474, HexColor("#B74220"))
    title(c, "Оформление поддерживает весь клиентский маршрут", 42, 432, 610, 29, 34, INK)
    paragraph(c, "Витрина, ресепшн, зона консультации и точка выдачи работают как одна система — с учётом монтажа, обслуживания и будущей смены кампаний.", 690, 430, 220, 10.5, 15, DARK_MUTED)
    facts = [
        ("Единая визуальная система", "Интерьер, POS, навигация, фасад и событие в одном стиле."),
        ("Монтаж по графику салона", "До открытия, после закрытия или поэтапно по зонам."),
        ("Производство в одном проекте", "Печать, конструкции, упаковка, доставка и монтаж."),
        ("Один или несколько адресов", "Спецификации и маркировка для каждого центра."),
    ]
    for i, (head, body) in enumerate(facts):
        x = 42 + i * 226
        c.setFillColor(white); c.setStrokeColor(DARK_LINE); c.rect(x, 108, 210, 222, fill=1, stroke=1)
        c.setFillColor(INK); c.circle(x + 32, 292, 16, fill=1, stroke=0)
        text(c, f"0{i+1}", x + 23, 288, 8, white, "DVB")
        paragraph(c, head, x + 20, 252, 170, 13, 17, INK, "DVB")
        paragraph(c, body, x + 20, 195, 170, 9.5, 14, DARK_MUTED)
    c.showPage()

    # 3 — Three formats
    new_page(c, 3)
    kicker(c, "Три формата старта", 42, 478)
    title(c, "Начать можно с конкретной зоны или кампании", 42, 438, 620, 29, 34)
    cards = [
        ("Сезонное обновление", "Быстрый старт", MEDIA / "dealer-seasonal-pos.jpg", ["витринная и напольная графика", "мобильные стенды и POS", "комплекты по адресам"]),
        ("Презентация модели", "Клиентское событие", MEDIA / "dealer-model-launch.jpg", ["подиум и презентационный фон", "регистрация и фотозона", "монтаж по графику"]),
        ("Обновление пространства", "Постоянное решение", MEDIA / "dealer-reception-delivery.jpg", ["ресепшн и зона выдачи", "световые логотипы", "интерьерная навигация"]),
    ]
    for i, (head, tag, image, items) in enumerate(cards):
        x = 42 + i * 300
        card(c, x, 58, 280, 326)
        fit_image(c, image, x, 230, 280, 154, 14)
        c.setFillColor(Color(0,0,0,alpha=0.62)); c.roundRect(x+14, 340, 112, 22, 6, fill=1, stroke=0)
        text(c, tag.upper(), x + 25, 348, 6.3, white, "DVB")
        text(c, f"0{i+1}", x + 18, 204, 7, ACCENT, "DVB")
        paragraph(c, head, x + 18, 180, 244, 14, 18, white, "DVB")
        yy = 136
        for item in items: yy = bullet(c, item, x + 18, yy, 244, Color(1,1,1,alpha=0.74), size=8.2) - 5
    c.showPage()

    # 4 — Zones
    new_page(c, 4, BG2)
    fit_image(c, MEDIA / "dealer-facade-navigation.jpg", 42, 58, 500, 424, 18)
    c.saveState(); c.setFillAlpha(0.78); c.setFillColor(BG); c.rect(42, 58, 500, 120, fill=1, stroke=0); c.restoreState()
    kicker(c, "От парковки до выдачи", 66, 142)
    title(c, "Один язык во всех зонах", 66, 108, 420, 23, 27)
    zones = [
        ("01", "Фасад и вход", "Витрины, световые элементы, входная группа и пилоны."),
        ("02", "Шоурум", "POS, стойки, брендированные стены и сменные кампании."),
        ("03", "Зона выдачи", "Фоновые панели, декоративный свет и зона фотографии."),
        ("04", "Сервис и trade-in", "Навигация, зонирование и информационные стенды."),
    ]
    for i, (n, head, body) in enumerate(zones):
        x = 568 + (i % 2) * 174; y = 270 if i < 2 else 88
        card(c, x, y, 162, 158)
        text(c, n, x + 18, y + 126, 7, ACCENT, "DVB")
        paragraph(c, head, x + 18, y + 96, 126, 11, 14, white, "DVB")
        paragraph(c, body, x + 18, y + 53, 126, 8.2, 12, MUTED)
    c.showPage()

    # 5 — Dealer groups
    new_page(c, 5, IVORY, True)
    kicker(c, "Для дилерских групп", 42, 474, HexColor("#B74220"))
    title(c, "Один стандарт — разные адреса", 42, 432, 470, 29, 34, INK)
    paragraph(c, "Единая концепция превращается в адресные спецификации, маркированные комплекты и монтажный календарь.", 42, 350, 430, 11, 16, DARK_MUTED)
    items = ["единый перечень носителей", "паспорт размеров по каждому адресу", "маркировка упаковки по зонам", "график производства и монтажа", "фотофиксация после установки"]
    yy = 284
    for item in items: yy = bullet(c, item, 42, yy, 430, INK, HexColor("#B74220"), 10) - 8
    fit_image(c, MEDIA / "dealer-reception-delivery.jpg", 538, 92, 160, 332, 15)
    fit_image(c, MEDIA / "dealer-night-installation.jpg", 715, 124, 203, 360, 15)
    c.showPage()

    # 6 — Process
    new_page(c, 6)
    kicker(c, "Процесс", 42, 478)
    title(c, "От первой фотографии до готового объекта", 42, 438, 700, 29, 34)
    process = [
        ("Экспресс-аудит", "Фото, план, задача, адрес и дата."),
        ("Замер и бриф", "Размеры, основания, электрика и ограничения."),
        ("Концепция", "Брендбук и состав носителей до производства."),
        ("Смета и график", "Материалы, логистика и очередность работ."),
        ("Производство", "Печать, конструкции, сборка и маркировка."),
        ("Монтаж и сдача", "Установка, проверка и передача объекта."),
    ]
    for i, (head, body) in enumerate(process):
        x = 42 + (i % 3) * 300; y = 234 if i < 3 else 58
        card(c, x, y, 280, 158)
        text(c, f"{i+1:02}", x + 18, y + 126, 7, ACCENT, "DVB")
        paragraph(c, head, x + 18, y + 92, 244, 12, 16, white, "DVB")
        paragraph(c, body, x + 18, y + 52, 244, 8.7, 13, MUTED)
    c.showPage()

    # 7 — Consultation
    new_page(c, 7, BG2)
    kicker(c, "Первичная консультация", 42, 472)
    title(c, "Не нужен идеальный бриф, чтобы начать разговор", 42, 430, 500, 29, 34)
    paragraph(c, "Менеджер уточнит недостающие вводные и согласует следующий шаг: консультацию, замер или предварительный состав работ.", 42, 338, 470, 11, 16, MUTED)
    inputs = ["фотография или видео зоны", "примерные размеры или план", "брендбук и макеты", "адрес и количество центров", "желаемая дата готовности"]
    yy = 270
    for item in inputs: yy = bullet(c, item, 42, yy, 430, white, ACCENT, 9.6) - 7
    c.setFillColor(ACCENT); c.roundRect(580, 72, 338, 388, 20, fill=1, stroke=0)
    text(c, "ОБСУДИТЬ ЗАДАЧУ", 612, 416, 7.2, Color(1,1,1,alpha=0.72), "DVB")
    title(c, "Закажите консультацию менеджера", 612, 375, 270, 23, 28)
    paragraph(c, "Оставьте имя и телефон. В заявке уже отмечено направление «Оформление автосалона».", 612, 282, 270, 10, 15, Color(1,1,1,alpha=0.82))
    c.setFillColor(ACID); c.roundRect(612, 182, 250, 42, 9, fill=1, stroke=0)
    text(c, "ЗАКАЗАТЬ КОНСУЛЬТАЦИЮ", 630, 197, 8, HexColor("#111111"), "DVB")
    text(c, "+7 (495) 799-00-19", 612, 130, 15, white, "DVB")
    paragraph(c, "Москва, Остаповский проезд, д. 9 с. 3", 612, 106, 260, 8.3, 12, Color(1,1,1,alpha=0.72))
    c.showPage()

    # 8 — FAQ and notes
    new_page(c, 8, IVORY, True)
    kicker(c, "FAQ", 42, 474, HexColor("#B74220"))
    title(c, "Частые вопросы дилерских центров", 42, 432, 620, 29, 34, INK)
    faq = [
        ("Можно обновить салон без остановки работы?", "Во многих проектах — да. График зависит от состава конструкций и правил объекта."),
        ("Работаете по брендбуку автомобильной марки?", "Да. Макеты и правила использования фирменных элементов согласуются до производства."),
        ("Можно оформить несколько центров?", "Да. Формируем адресные спецификации, маркировку комплектов и график логистики."),
        ("Сколько стоит оформление?", "Цена зависит от площади, носителей, материалов, электрики, логистики и монтажа."),
    ]
    for i, (q, a) in enumerate(faq):
        y = 326 - i * 72
        c.setStrokeColor(DARK_LINE); c.line(42, y + 40, 918, y + 40)
        text(c, f"0{i+1}", 42, y + 9, 7, HexColor("#B74220"), "DVB")
        paragraph(c, q, 78, y + 12, 360, 10, 14, INK, "DVB")
        paragraph(c, a, 490, y + 12, 410, 8.7, 13, DARK_MUTED)
    c.setFillColor(white); c.setStrokeColor(DARK_LINE); c.roundRect(42, 42, 876, 56, 10, fill=1, stroke=1)
    paragraph(c, "Интерьерные изображения — концепт-визуализации возможных направлений оформления, а не фотографии реализованных кейсов.", 62, 68, 835, 8.4, 12, DARK_MUTED)
    c.showPage()

    c.save()
    print(OUT)


if __name__ == "__main__":
    build()
