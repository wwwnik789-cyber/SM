#!/usr/bin/env python3
"""Build the SM Production commercial interiors presentation as PNG, PDF and PPTX."""
from pathlib import Path
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
from pptx import Presentation
from pptx.util import Inches

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
SLIDES = ROOT / "slides"
SLIDES.mkdir(parents=True, exist_ok=True)

W, H = 1920, 1080
BG = "#1d1d1d"
CARD = "#11111c"
WHITE = "#f7f6f3"
MUTED = "#c9c7c4"
SUBTLE = "#8f8d93"
PURPLE = "#7550b5"
GOLD = "#d5a600"
BORDER = "#67656c"
FONT_PATH = ROOT / "fonts" / "Montserrat-Variable.ttf"

@lru_cache(maxsize=64)
def font(size, weight="Regular"):
    f = ImageFont.truetype(str(FONT_PATH), size=size)
    try:
        f.set_variation_by_name(weight)
    except Exception:
        pass
    return f


def open_rgb(path):
    return Image.open(path).convert("RGB")


def fit(path, size, centering=(0.5, 0.5)):
    return ImageOps.fit(open_rgb(path), size, method=Image.Resampling.LANCZOS, centering=centering)


def rounded_paste(canvas, image, box, radius=26, border=None, border_width=2):
    x, y, w, h = map(int, box)
    if isinstance(image, (str, Path)):
        image = fit(image, (w, h))
    else:
        image = ImageOps.fit(image.convert("RGB"), (w, h), method=Image.Resampling.LANCZOS)
    mask = Image.new("L", (w, h), 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle((0, 0, w - 1, h - 1), radius=radius, fill=255)
    canvas.paste(image, (x, y), mask)
    if border:
        ImageDraw.Draw(canvas).rounded_rectangle((x, y, x + w - 1, y + h - 1), radius=radius, outline=border, width=border_width)


def overlay(canvas, color, alpha, box=None):
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    if box is None:
        box = (0, 0, W, H)
    d.rectangle(box, fill=(*ImageColor(color), alpha))
    canvas.alpha_composite(layer)


def ImageColor(value):
    value = value.lstrip("#")
    return tuple(int(value[i:i+2], 16) for i in (0, 2, 4))


def draw_wrapped(draw, text, xy, max_width, f, fill=WHITE, spacing=8, max_lines=None, align="left"):
    x, y = xy
    paragraphs = text.split("\n")
    lines = []
    for p in paragraphs:
        if not p:
            lines.append("")
            continue
        words = p.split()
        line = ""
        for word in words:
            test = word if not line else f"{line} {word}"
            if draw.textlength(test, font=f) <= max_width:
                line = test
            else:
                if line:
                    lines.append(line)
                line = word
        if line:
            lines.append(line)
    if max_lines:
        lines = lines[:max_lines]
    bbox = draw.textbbox((0, 0), "Ag", font=f)
    line_h = bbox[3] - bbox[1]
    for line in lines:
        draw.text((x, y), line, font=f, fill=fill, anchor="la", align=align)
        y += line_h + spacing
    return y


def label(draw, text, x=84, y=72):
    draw.rounded_rectangle((x, y + 7, x + 78, y + 13), radius=3, fill=PURPLE)
    draw.text((x + 96, y), text.upper(), font=font(18, "Bold"), fill=GOLD)


def footer(canvas, page, note=None):
    d = ImageDraw.Draw(canvas)
    icon = Image.open(ASSETS / "sm-logo-icon.png").convert("RGBA")
    icon.thumbnail((52, 34), Image.Resampling.LANCZOS)
    if canvas.mode == "RGBA":
        canvas.alpha_composite(icon, (84, 1004))
    else:
        canvas.paste(icon, (84, 1004), icon)
    d.text((152, 1010), "SM-PRODUCTION  ·  ОФОРМЛЕНИЕ КОММЕРЧЕСКИХ ИНТЕРЬЕРОВ", font=font(18, "Regular"), fill=MUTED)
    if note:
        d.text((1120, 1010), note, font=font(14, "Regular"), fill=SUBTLE)
    d.text((1742, 1008), f"{page:02d}", font=font(18, "Bold"), fill=PURPLE)
    d.rounded_rectangle((1784, 1017, 1862, 1023), radius=3, fill=GOLD)


def title_lines(draw, lines, x, y, size=60, leading=1.05):
    for parts in lines:
        cx = x
        for text, color in parts:
            draw.text((cx, y), text, font=font(size, "ExtraBold"), fill=color)
            cx += draw.textlength(text, font=font(size, "ExtraBold"))
        y += int(size * leading)
    return y


def bullet_list(draw, items, x, y, width, fsize=26, gap=26):
    for item in items:
        draw.rounded_rectangle((x, y + 12, x + 28, y + 19), radius=3, fill=GOLD)
        y = draw_wrapped(draw, item, (x + 54, y), width - 54, font(fsize, "Regular"), fill=WHITE, spacing=7) + gap
    return y


def card(canvas, box, radius=22, fill_color=CARD, border=BORDER):
    ImageDraw.Draw(canvas).rounded_rectangle(box, radius=radius, fill=fill_color, outline=border, width=2)


def tile_with_caption(canvas, image_path, box, caption, centering=(0.5, 0.5)):
    x, y, w, h = box
    img = fit(image_path, (w, h), centering=centering).convert("RGBA")
    grad = Image.new("L", (w, h), 0)
    gd = ImageDraw.Draw(grad)
    for yy in range(h):
        a = int(max(0, (yy / h - 0.50) / 0.50) * 215)
        gd.line((0, yy, w, yy), fill=a)
    dark = Image.new("RGBA", (w, h), (0, 0, 0, 230))
    img.alpha_composite(Image.composite(dark, Image.new("RGBA", (w, h), (0, 0, 0, 0)), grad))
    rounded_paste(canvas, img.convert("RGB"), box, radius=24, border=BORDER)
    ImageDraw.Draw(canvas).text((x + 26, y + h - 54), caption, font=font(20, "Bold"), fill=WHITE)


def slide1():
    bg = fit(ASSETS / "commercial-interior-hero.jpg", (W, H), centering=(0.5, 0.5)).convert("RGBA")
    # Left-to-right dark gradient for readable title.
    shade = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = shade.load()
    for x in range(W):
        a = int(226 * max(0, 1 - x / 1350)) + 32
        a = min(a, 235)
        for y in range(H):
            px[x, y] = (12, 12, 14, a)
    bg.alpha_composite(shade)
    d = ImageDraw.Draw(bg)
    label(d, "Презентация для бизнеса", 84, 258)
    title_lines(d, [
        [("ОФОРМЛЕНИЕ", WHITE)],
        [("КОММЕРЧЕСКИХ", PURPLE)],
        [("ИНТЕРЬЕРОВ", WHITE)],
    ], 84, 308, 72, 1.02)
    draw_wrapped(d,
        "Ресепшн, интерьерные вывески, навигация, брендированные стены, стекло и торговое оборудование — от замера до монтажа.",
        (84, 555), 910, font(27, "Regular"), fill=WHITE, spacing=10)
    badges = ["СОБСТВЕННОЕ ПРОИЗВОДСТВО", "КП В ТЕЧЕНИЕ ДНЯ", "МОНТАЖ В УДОБНОЕ ВРЕМЯ"]
    bx = 84
    widths = [330, 290, 360]
    for i, b in enumerate(badges):
        bw = widths[i]
        d.rounded_rectangle((bx, 716, bx + bw, 770), radius=18, fill=GOLD if i == 0 else "#222226", outline=BORDER)
        tw = d.textlength(b, font=font(14, "Bold"))
        d.text((bx + (bw - tw) / 2, 734), b, font=font(14, "Bold"), fill=WHITE)
        bx += bw + 24
    logo = Image.open(ASSETS / "sm-logo-full-transparent.png").convert("RGBA")
    logo.thumbnail((330, 270), Image.Resampling.LANCZOS)
    bg.alpha_composite(logo, (1510, 50))
    d.text((1110, 906), "+7 (495) 799-00-19", font=font(25, "Bold"), fill=GOLD)
    d.text((1392, 906), "sm-pro1@yandex.ru", font=font(22, "SemiBold"), fill=WHITE)
    d.text((1640, 906), "sm-production.ru", font=font(22, "SemiBold"), fill=WHITE)
    d.text((1110, 950), "Москва, Остаповский проезд, д. 9 с. 3  ·  м. Текстильщики", font=font(20, "SemiBold"), fill=WHITE)
    d.text((84, 1010), "Концепт-визуализация", font=font(14, "Regular"), fill="#aaa7ad")
    return bg.convert("RGB")


def slide2():
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    label(d, "SM-Production · кто мы")
    title_lines(d, [[("ПРОИЗВОДСТВО,", WHITE)], [("А НЕ ПОСРЕДНИКИ", PURPLE)]], 84, 120, 62, 1.03)
    draw_wrapped(d,
        "SM Production — производственная компания полного цикла: от концепции и 3D-визуализации до печати, изготовления конструкций и монтажа на объекте. Собственный цех в Москве помогает контролировать сроки и качество на каждом этапе.",
        (84, 318), 930, font(26, "Regular"), fill=WHITE, spacing=9)
    stats = [
        ("ОТ 1 ДНЯ", "Производство простых\nконструкций"),
        ("1 ГОД", "Гарантия на\nконструкции"),
        ("24/7", "Производство\nи монтаж"),
        ("ПН–ПТ", "Приём заявок\n10:00–18:00"),
    ]
    sx, sy = 84, 594
    for i, (big, small) in enumerate(stats):
        x = sx + (i % 2) * 490
        y = sy + (i // 2) * 180
        card(im, (x, y, x + 455, y + 152))
        d.text((x + 227, y + 28), big, font=font(43, "ExtraBold"), fill=GOLD, anchor="ma")
        draw_wrapped(d, small, (x + 48, y + 86), 360, font(20, "Bold"), fill=WHITE, spacing=3, align="center")
    # Real production photographs from the source presentation.
    gx, gy, gw, gh = 1080, 0, 840, 980
    cell_w, cell_h = gw // 2, gh // 3
    for idx in range(6):
        rounded_paste(im, ASSETS / f"production-{idx+1}.jpg", (gx + (idx % 2) * cell_w, gy + (idx // 2) * cell_h, cell_w, cell_h), radius=0)
    footer(im, 2)
    return im


def slide3():
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    label(d, "Что оформляем")
    title_lines(d, [[("ЧЕТЫРЕ ЗОНЫ ", WHITE)], [("КОММЕРЧЕСКОГО ИНТЕРЬЕРА", PURPLE)]], 84, 118, 54, 1.03)
    cards = [
        ("ВХОД И РЕСЕПШН", "Стойки, световые логотипы, входные порталы и фоновые панели.", "commercial-reception-office.jpg"),
        ("НАВИГАЦИЯ", "Указатели, таблички, пиктограммы и единая система движения по объекту.", "commercial-wayfinding.jpg"),
        ("СТЕНЫ И СТЕКЛО", "Декоративные панели, графика, плёнка и оформление переговорных.", "commercial-walls-glass.jpg"),
        ("ТОРГОВЫЕ ЗОНЫ", "Витрины, подиумы, дисплеи, POS-элементы и сезонное обновление.", "commercial-retail-showroom.jpg"),
    ]
    positions = [(84, 285), (1008, 285), (84, 588), (1008, 588)]
    for (title, txt, imgname), (x, y) in zip(cards, positions):
        card(im, (x, y, x + 828, y + 260))
        rounded_paste(im, ASSETS / imgname, (x + 22, y + 22, 242, 216), radius=20)
        d.rounded_rectangle((x + 302, y + 28, x + 548, y + 72), radius=15, outline=GOLD, width=3)
        d.text((x + 425, y + 49), title, font=font(16, "Bold"), fill=GOLD, anchor="mm")
        draw_wrapped(d, txt, (x + 302, y + 105), 485, font(23, "SemiBold"), fill=WHITE, spacing=8)
    d.text((84, 918), "Визуализации показывают возможные решения. Финальный вид зависит от объекта, брендбука, материалов и бюджета.", font=font(17, "Regular"), fill=SUBTLE)
    footer(im, 3, "Концепт-визуализации")
    return im


def slide4():
    im = Image.new("RGB", (W, H), BG)
    rounded_paste(im, ASSETS / "commercial-reception-office.jpg", (0, 0, 970, 1080), radius=0)
    # Subtle dark overlay at image edge.
    d = ImageDraw.Draw(im)
    d.rectangle((970, 0, 976, H), fill="#0d0d0f")
    label(d, "Входная зона", 1028, 74)
    title_lines(d, [[("РЕСЕПШН И", WHITE)], [("ПЕРВОЕ ВПЕЧАТЛЕНИЕ", PURPLE)]], 1028, 122, 53, 1.03)
    bullet_list(d, [
        "Стойки ресепшн по индивидуальному дизайну: ЛДСП, МДФ, акрил, металл, дерево и подсветка.",
        "Объёмные и световые логотипы, фоновые панели и декоративные элементы.",
        "Оформление зон ожидания, перегородок и входных порталов в единой стилистике.",
        "Замер, 3D-визуализация и монтаж в согласованное время без остановки работы объекта.",
    ], 1030, 300, 800, 23, 18)
    rounded_paste(im, ASSETS / "commercial-clinic-reception.jpg", (1030, 756, 390, 185), radius=22, border=BORDER)
    rounded_paste(im, ASSETS / "commercial-hospitality.jpg", (1442, 756, 390, 185), radius=22, border=BORDER)
    footer(im, 4, "Концепт-визуализации")
    return im


def slide5():
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    label(d, "Брендинг пространства")
    title_lines(d, [[("СТЕНЫ, СТЕКЛО И ", WHITE), ("НАВИГАЦИЯ", PURPLE)]], 84, 118, 57, 1.03)
    d.text((84, 198), "Собираем визуальные элементы в одну понятную систему — от входа до кабинета или зоны обслуживания.", font=font(24, "Regular"), fill=WHITE)
    tiles = [
        ("commercial-walls-glass.jpg", "Декоративные панели"),
        ("commercial-interior-hero.jpg", "Объёмные элементы"),
        ("commercial-walls-glass.jpg", "Плёнка на стекло"),
        ("commercial-wayfinding.jpg", "Система навигации"),
        ("commercial-wayfinding.jpg", "Таблички и указатели"),
        ("commercial-installation.jpg", "Монтаж на объекте"),
    ]
    for i, (imgname, cap) in enumerate(tiles):
        x = 84 + (i % 3) * 588
        y = 274 + (i // 3) * 326
        cent = (0.35 if i == 2 else 0.5, 0.5)
        tile_with_caption(im, ASSETS / imgname, (x, y, 554, 292), cap, cent)
    footer(im, 5, "Концепт-визуализации")
    return im


def slide6():
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    label(d, "Торговые пространства")
    title_lines(d, [[("ШОУРУМЫ, RETAIL И ", WHITE), ("СЕРВИС", PURPLE)]], 84, 118, 57, 1.03)
    d.text((84, 198), "Производим элементы, которые помогают показать продукт, организовать поток посетителей и быстро обновлять коммуникацию.", font=font(24, "Regular"), fill=WHITE)
    tiles = [
        ("commercial-retail-showroom.jpg", "Витрины и ниши"),
        ("commercial-retail-showroom.jpg", "POS и дисплеи"),
        ("commercial-interior-hero.jpg", "Имиджевые зоны"),
        ("commercial-hospitality.jpg", "Зоны консультаций"),
        ("commercial-clinic-reception.jpg", "Стойки обслуживания"),
        ("commercial-walls-glass.jpg", "Сезонное обновление"),
    ]
    centers = [(0.24, 0.55), (0.72, 0.55), (0.77, 0.45), (0.63, 0.5), (0.63, 0.5), (0.2, 0.5)]
    for i, ((imgname, cap), cent) in enumerate(zip(tiles, centers)):
        x = 84 + (i % 3) * 588
        y = 274 + (i // 3) * 326
        img = fit(ASSETS / imgname, (554, 292), centering=cent)
        # Add caption while preserving custom crop.
        x2, y2 = x, y
        rgba = img.convert("RGBA")
        grad = Image.new("L", (554, 292), 0)
        gd = ImageDraw.Draw(grad)
        for yy in range(292):
            gd.line((0, yy, 554, yy), fill=int(max(0, (yy / 292 - .5) / .5) * 215))
        dark = Image.new("RGBA", (554, 292), (0, 0, 0, 230))
        rgba.alpha_composite(Image.composite(dark, Image.new("RGBA", (554, 292), (0, 0, 0, 0)), grad))
        rounded_paste(im, rgba.convert("RGB"), (x2, y2, 554, 292), radius=24, border=BORDER)
        ImageDraw.Draw(im).text((x2 + 26, y2 + 238), cap, font=font(20, "Bold"), fill=WHITE)
    footer(im, 6, "Концепт-визуализации")
    return im


def slide7():
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    label(d, "Для бизнеса")
    title_lines(d, [[("КАКИЕ ПРОСТРАНСТВА ", WHITE), ("ОФОРМЛЯЕМ", PURPLE)]], 84, 118, 55, 1.03)
    sectors = [
        ("ОФИСЫ И БИЗНЕС-ЦЕНТРЫ", "Ресепшн, переговорные, навигация и брендированные стены.", "commercial-reception-office.jpg"),
        ("МАГАЗИНЫ И ШОУРУМЫ", "Витрины, торговые дисплеи, подиумы и POS-материалы.", "commercial-retail-showroom.jpg"),
        ("КЛИНИКИ И BEAUTY", "Стойки обслуживания, спокойная навигация и оформление кабинетов.", "commercial-clinic-reception.jpg"),
        ("ОТЕЛИ, КАФЕ И СЕРВИС", "Хостес-зоны, интерьерные вывески, декор и указатели.", "commercial-hospitality.jpg"),
    ]
    positions = [(84, 272), (984, 272), (84, 606), (984, 606)]
    for (ttl, txt, imgname), (x, y) in zip(sectors, positions):
        card(im, (x, y, x + 850, y + 290))
        rounded_paste(im, ASSETS / imgname, (x + 20, y + 20, 360, 250), radius=20)
        d.text((x + 418, y + 52), ttl, font=font(21, "Bold"), fill=GOLD)
        draw_wrapped(d, txt, (x + 418, y + 104), 390, font(22, "Regular"), fill=WHITE, spacing=8)
        d.text((x + 418, y + 220), "Дизайн  ·  Производство  ·  Монтаж", font=font(15, "SemiBold"), fill=SUBTLE)
    footer(im, 7, "Концепт-визуализации")
    return im


def slide8():
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    label(d, "Процесс работы")
    title_lines(d, [[("ОТ ЗАМЕРА ДО МОНТАЖА —", WHITE)], [("6 ШАГОВ", PURPLE)]], 84, 120, 52, 1.03)
    d.text((84, 238), "За проектом закрепляется руководитель, который ведёт задачу на всех этапах.", font=font(23, "Regular"), fill=WHITE)
    steps = [
        ("1", "Заявка и замер", "Обсуждаем задачу, объект, сроки и бюджет."),
        ("2", "Концепция и 3D", "Показываем решение до запуска производства."),
        ("3", "Смета и договор", "Фиксируем состав работ, стоимость и сроки."),
        ("4", "Производство", "Изготавливаем элементы и отправляем фотоотчёты."),
        ("5", "Доставка и монтаж", "Планируем работы на удобное для объекта время."),
        ("6", "Сдача объекта", "Проверяем комплектность и остаёмся на связи."),
    ]
    for i, (num, ttl, txt) in enumerate(steps):
        x = 84 + (i % 3) * 380
        y = 336 + (i // 3) * 304
        card(im, (x, y, x + 350, y + 272))
        d.text((x + 175, y + 26), num, font=font(46, "ExtraBold"), fill=GOLD, anchor="ma")
        d.text((x + 175, y + 95), ttl, font=font(20, "Bold"), fill=WHITE, anchor="ma")
        draw_wrapped(d, txt, (x + 28, y + 145), 294, font(18, "Regular"), fill=MUTED, spacing=6)
    rounded_paste(im, ASSETS / "commercial-installation.jpg", (1250, 0, 670, 980), radius=0)
    # Numbered image caption.
    d.rectangle((1250, 840, 1920, 980), fill="#111116")
    d.text((1300, 868), "МОНТАЖ БЕЗ ЛИШНЕГО ПРОСТОЯ", font=font(24, "Bold"), fill=GOLD)
    draw_wrapped(d, "Согласуем время и защищаем чистовые поверхности на объекте.", (1300, 910), 560, font(18, "Regular"), fill=WHITE, spacing=5)
    footer(im, 8, "Концепт-визуализация")
    return im


def slide9():
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    label(d, "Наши контакты")
    title_lines(d, [[("ОБСУДИМ ВАШ ", WHITE), ("ИНТЕРЬЕР", PURPLE)], [("И ПОДГОТОВИМ РАСЧЁТ", WHITE)]], 84, 118, 55, 1.03)
    draw_wrapped(d,
        "Пришлите фотографии или план помещения, размеры, брендбук и желаемый срок. В течение дня подготовим предварительное предложение по составу работ, стоимости и графику.",
        (84, 330), 1050, font(27, "Regular"), fill=WHITE, spacing=10)
    contacts = [
        ("Телефон · ПН–ПТ 10:00–18:00", "+7 (495) 799-00-19"),
        ("Почта для расчётов", "sm-pro1@yandex.ru"),
        ("Сайт", "SM-PRODUCTION.RU"),
    ]
    x = 84
    widths = [360, 390, 340]
    for i, (cap, val) in enumerate(contacts):
        w = widths[i]
        card(im, (x, 548, x + w, 670), radius=18)
        d.text((x + w / 2, 572), cap, font=font(15, "SemiBold"), fill=SUBTLE, anchor="ma")
        d.text((x + w / 2, 624), val, font=font(20 if i else 22, "Bold"), fill=GOLD if i == 0 else WHITE, anchor="mm")
        x += w + 24
    d.text((84, 744), "Бесплатный замер в пределах МКАД — при заказе производства.", font=font(22, "SemiBold"), fill=GOLD)
    # Right-side map and website label.
    d.rounded_rectangle((1260, 236, 1840, 296), radius=16, fill="#45216d")
    d.text((1550, 266), "SM-PRODUCTION.RU", font=font(28, "SemiBold"), fill=WHITE, anchor="mm")
    rounded_paste(im, ASSETS / "location-map.jpg", (1260, 322, 580, 452), radius=24, border=BORDER)
    d.text((1550, 818), "Москва, Остаповский проезд, д. 9 с. 3", font=font(22, "Bold"), fill=WHITE, anchor="mm")
    d.text((1550, 858), "м. Текстильщики", font=font(20, "Regular"), fill=MUTED, anchor="mm")
    footer(im, 9)
    return im


def save_outputs(slides):
    paths = []
    for i, slide in enumerate(slides, 1):
        p = SLIDES / f"slide-{i:02d}.png"
        slide.save(p, quality=95)
        paths.append(p)
    # PDF, 16:9 landscape.
    pdf_path = ROOT / "SM-Production-commercial-interiors.pdf"
    slides[0].save(pdf_path, "PDF", resolution=144.0, save_all=True, append_images=slides[1:], quality=95, title="Оформление коммерческих интерьеров — SM Production")
    # PPTX: high-quality slides preserve the exact approved layout.
    prs = Presentation()
    prs.slide_width = Inches(13.333333)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]
    for p in paths:
        s = prs.slides.add_slide(blank)
        s.shapes.add_picture(str(p), 0, 0, width=prs.slide_width, height=prs.slide_height)
    prs.save(ROOT / "SM-Production-commercial-interiors.pptx")
    return paths


if __name__ == "__main__":
    slides = [slide1(), slide2(), slide3(), slide4(), slide5(), slide6(), slide7(), slide8(), slide9()]
    save_outputs(slides)
    print(f"Built {len(slides)} slides in {ROOT}")
