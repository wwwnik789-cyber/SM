#!/usr/bin/env python3
"""Build the SM Production dealership proposal as PNG, PDF and PPTX."""
from pathlib import Path
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont, ImageOps
from pptx import Presentation
from pptx.util import Inches

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
SLIDES = ROOT / "slides"
SLIDES.mkdir(parents=True, exist_ok=True)
W, H = 1920, 1080
BG, CARD = "#1d1d1d", "#11111c"
WHITE, MUTED, SUBTLE = "#f7f6f3", "#c9c7c4", "#8f8d93"
PURPLE, GOLD, BORDER = "#7550b5", "#d5a600", "#67656c"
FONT_PATH = ROOT / "fonts" / "Montserrat-Variable.ttf"

@lru_cache(maxsize=64)
def font(size, weight="Regular"):
    f = ImageFont.truetype(str(FONT_PATH), size=size)
    try: f.set_variation_by_name(weight)
    except Exception: pass
    return f


def fit(path, size, centering=(0.5, 0.5)):
    return ImageOps.fit(Image.open(path).convert("RGB"), size, method=Image.Resampling.LANCZOS, centering=centering)


def rounded_paste(canvas, image, box, radius=24, border=None, centering=(0.5, 0.5)):
    x, y, w, h = map(int, box)
    if isinstance(image, (str, Path)):
        image = fit(image, (w, h), centering)
    else:
        image = ImageOps.fit(image.convert("RGB"), (w, h), method=Image.Resampling.LANCZOS, centering=centering)
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 1), radius=radius, fill=255)
    canvas.paste(image, (x, y), mask)
    if border:
        ImageDraw.Draw(canvas).rounded_rectangle((x, y, x + w - 1, y + h - 1), radius=radius, outline=border, width=2)


def card(canvas, box, radius=22):
    ImageDraw.Draw(canvas).rounded_rectangle(box, radius=radius, fill=CARD, outline=BORDER, width=2)


def wrap(draw, text, xy, max_width, f, fill=WHITE, spacing=7):
    x, y = xy; lines = []
    for para in text.split("\n"):
        if not para: lines.append(""); continue
        line = ""
        for word in para.split():
            test = word if not line else f"{line} {word}"
            if draw.textlength(test, font=f) <= max_width: line = test
            else:
                if line: lines.append(line)
                line = word
        if line: lines.append(line)
    lh = draw.textbbox((0, 0), "Ag", font=f)[3]
    for line in lines:
        draw.text((x, y), line, font=f, fill=fill)
        y += lh + spacing
    return y


def label(draw, text, x=84, y=72):
    draw.rounded_rectangle((x, y + 7, x + 78, y + 13), radius=3, fill=PURPLE)
    draw.text((x + 96, y), text.upper(), font=font(18, "Bold"), fill=GOLD)


def title(draw, lines, x=84, y=120, size=58, leading=1.03):
    for parts in lines:
        cx = x
        for text, color in parts:
            f = font(size, "ExtraBold")
            draw.text((cx, y), text, font=f, fill=color)
            cx += draw.textlength(text, font=f)
        y += int(size * leading)
    return y


def footer(canvas, page, note=None):
    d = ImageDraw.Draw(canvas)
    icon = Image.open(ASSETS / "sm-logo-icon.png").convert("RGBA")
    icon.thumbnail((52, 34), Image.Resampling.LANCZOS)
    canvas.paste(icon, (84, 1004), icon)
    d.text((152, 1010), "SM-PRODUCTION  ·  ОФОРМЛЕНИЕ ДИЛЕРСКИХ ЦЕНТРОВ", font=font(18), fill=MUTED)
    if note: d.text((1190, 1010), note, font=font(14), fill=SUBTLE)
    d.text((1742, 1008), f"{page:02d}", font=font(18, "Bold"), fill=PURPLE)
    d.rounded_rectangle((1784, 1017, 1862, 1023), radius=3, fill=GOLD)


def bullets(draw, items, x, y, width, fsize=24, gap=20):
    for item in items:
        draw.rounded_rectangle((x, y + 12, x + 28, y + 19), radius=3, fill=GOLD)
        y = wrap(draw, item, (x + 54, y), width - 54, font(fsize), WHITE, 7) + gap
    return y


def caption_tile(canvas, image, box, caption, centering=(0.5, 0.5)):
    x, y, w, h = box
    img = fit(image, (w, h), centering).convert("RGBA")
    shade = Image.new("RGBA", (w, h), (0, 0, 0, 0)); sd = ImageDraw.Draw(shade)
    for yy in range(h // 2, h):
        a = int((yy - h / 2) / (h / 2) * 205)
        sd.line((0, yy, w, yy), fill=(0, 0, 0, a))
    img.alpha_composite(shade)
    rounded_paste(canvas, img.convert("RGB"), box, radius=24, border=BORDER)
    ImageDraw.Draw(canvas).text((x + 24, y + h - 52), caption, font=font(19, "Bold"), fill=WHITE)


def slide1():
    im = fit(ASSETS / "dealer-branding-hero.jpg", (W, H), (0.5, 0.5)).convert("RGBA")
    shade = Image.new("RGBA", (W, H), (0, 0, 0, 0)); px = shade.load()
    for x in range(W):
        a = min(235, int(228 * max(0, 1 - x / 1350)) + 34)
        for y in range(H): px[x, y] = (10, 10, 12, a)
    im.alpha_composite(shade); d = ImageDraw.Draw(im)
    label(d, "Предложение для дилерских центров", 84, 220)
    title(d, [[("ОФОРМЛЕНИЕ", WHITE)], [("ДИЛЕРСКИХ", PURPLE)], [("ЦЕНТРОВ", WHITE)]], 84, 272, 74, 1.01)
    wrap(d, "Сезонные кампании, запуски моделей, интерьер, навигация и фасад — от идеи до монтажа без лишнего простоя.", (84, 525), 900, font(27), WHITE, 10)
    badges = [("СОБСТВЕННОЕ ПРОИЗВОДСТВО", 332), ("РАСЧЁТ В ТЕЧЕНИЕ ДНЯ", 315), ("МОНТАЖ ПО ГРАФИКУ САЛОНА", 355)]
    x = 84
    for i, (txt, w) in enumerate(badges):
        d.rounded_rectangle((x, 700, x + w, 756), radius=18, fill=GOLD if i == 0 else "#222226", outline=BORDER)
        d.text((x + w / 2, 728), txt, font=font(14, "Bold"), fill=WHITE, anchor="mm"); x += w + 22
    logo = Image.open(ASSETS / "sm-logo-full-transparent.png").convert("RGBA"); logo.thumbnail((330, 270), Image.Resampling.LANCZOS)
    im.alpha_composite(logo, (1510, 54))
    d.text((1095, 900), "+7 (495) 799-00-19", font=font(25, "Bold"), fill=GOLD)
    d.text((1383, 900), "sm-pro1@yandex.ru", font=font(22, "SemiBold"), fill=WHITE)
    d.text((1640, 900), "sm-production.ru", font=font(22, "SemiBold"), fill=WHITE)
    d.text((1095, 944), "Москва, Остаповский проезд, д. 9 с. 3  ·  м. Текстильщики", font=font(20, "SemiBold"), fill=WHITE)
    d.text((84, 1010), "Концепт-визуализация", font=font(14), fill=SUBTLE)
    return im.convert("RGB")


def slide2():
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    label(d, "С чего начинают")
    title(d, [[("ТРИ ЗАДАЧИ, КОТОРЫЕ", WHITE)], [("НУЖНО ЗАПУСТИТЬ В СРОК", PURPLE)]], 84, 120, 58)
    cards = [
        ("01", "СЕЗОННАЯ КАМПАНИЯ", "Обновить витрины, POS, баннеры, стойки и навигацию одновременно.", "dealer-seasonal-pos.jpg"),
        ("02", "ПРЕЗЕНТАЦИЯ МОДЕЛИ", "Подготовить подиум, фон, фотозону, регистрацию и маршрут гостей.", "dealer-model-launch.jpg"),
        ("03", "ОБНОВЛЕНИЕ САЛОНА", "Освежить ресепшн, зону выдачи, стены, световые элементы и фасад.", "dealer-reception-delivery.jpg"),
    ]
    for i, (num, ttl, txt, img) in enumerate(cards):
        x = 84 + i * 588; y = 315
        card(im, (x, y, x + 552, y + 555))
        rounded_paste(im, ASSETS / img, (x + 18, y + 18, 516, 260), radius=20)
        d.text((x + 34, y + 310), num, font=font(42, "ExtraBold"), fill=GOLD)
        d.text((x + 112, y + 322), ttl, font=font(20, "Bold"), fill=WHITE)
        wrap(d, txt, (x + 34, y + 382), 474, font(22), MUTED, 8)
    d.text((84, 912), "Один производственный подрядчик отвечает за согласованный комплект, маркировку, доставку и монтаж.", font=font(21, "SemiBold"), fill=GOLD)
    footer(im, 2, "Концепт-визуализации")
    return im


def slide3():
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    label(d, "Что производим")
    title(d, [[("ЧЕТЫРЕ НАПРАВЛЕНИЯ", WHITE)], [("ДЛЯ ДИЛЕРСКОГО ЦЕНТРА", PURPLE)]], 84, 118, 56)
    items = [
        ("ИНТЕРЬЕР", "Ресепшн, зона выдачи, стены, логотипы и клиентские зоны.", "dealer-reception-delivery.jpg"),
        ("АКЦИИ И POS", "Баннеры, витрины, Roll Up, дисплеи и сменная графика.", "dealer-seasonal-pos.jpg"),
        ("МЕРОПРИЯТИЯ", "Запуски моделей, фотозоны, подиумы, регистрация и навигация.", "dealer-model-launch.jpg"),
        ("ФАСАД", "Световые элементы, стекло, пилоны, флаги и территория.", "dealer-facade-navigation.jpg"),
    ]
    pos = [(84, 300), (1008, 300), (84, 596), (1008, 596)]
    for (ttl, txt, img), (x, y) in zip(items, pos):
        card(im, (x, y, x + 828, y + 252))
        rounded_paste(im, ASSETS / img, (x + 20, y + 20, 250, 212), radius=18)
        d.rounded_rectangle((x + 304, y + 30, x + 570, y + 74), radius=15, outline=GOLD, width=3)
        d.text((x + 437, y + 52), ttl, font=font(17, "Bold"), fill=GOLD, anchor="mm")
        wrap(d, txt, (x + 304, y + 105), 474, font(23, "SemiBold"), WHITE, 8)
    footer(im, 3, "Концепт-визуализации")
    return im


def slide4():
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    rounded_paste(im, ASSETS / "dealer-reception-delivery.jpg", (0, 0, 980, H), radius=0, centering=(0.44, 0.5))
    d.rectangle((974, 0, 982, H), fill="#0c0c0e")
    label(d, "Интерьер", 1035, 70)
    title(d, [[("РЕСЕПШН И", WHITE)], [("ЗОНА ВЫДАЧИ", PURPLE)]], 1035, 122, 56)
    bullets(d, [
        "Стойки ресепшн и консультационные зоны под архитектуру и стандарты бренда.",
        "Световые логотипы, фоновые панели, брендированные стены и перегородки.",
        "Подиум, декоративный свет и место для фотографии при передаче автомобиля.",
        "Навигация, информационные стойки и графика на стекле в единой системе.",
    ], 1035, 310, 790, 23, 18)
    rounded_paste(im, ASSETS / "dealer-branding-hero.jpg", (1035, 790, 370, 150), radius=20, border=BORDER)
    rounded_paste(im, ASSETS / "dealer-night-installation.jpg", (1430, 790, 390, 150), radius=20, border=BORDER)
    footer(im, 4, "Концепт-визуализации")
    return im


def slide5():
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    label(d, "Маркетинговый календарь")
    title(d, [[("СЕЗОННЫЕ КАМПАНИИ И ", WHITE), ("POS", PURPLE)]], 84, 120, 58)
    d.text((84, 202), "Комплектуем все точки контакта, чтобы акция запускалась в салоне одновременно.", font=font(24), fill=WHITE)
    tiles = [
        ("dealer-seasonal-pos.jpg", "Витринная графика", (0.15, 0.5)),
        ("dealer-seasonal-pos.jpg", "Roll Up и мобильные стенды", (0.52, 0.48)),
        ("dealer-seasonal-pos.jpg", "POS и информационные стойки", (0.85, 0.52)),
        ("dealer-facade-navigation.jpg", "Флаги и входная группа", (0.15, 0.5)),
        ("dealer-branding-hero.jpg", "Зоны консультации", (0.46, 0.52)),
        ("dealer-night-installation.jpg", "Замена вне клиентского потока", (0.55, 0.5)),
    ]
    for i, (img, cap, cent) in enumerate(tiles):
        x = 84 + (i % 3) * 588; y = 276 + (i // 3) * 326
        caption_tile(im, ASSETS / img, (x, y, 554, 292), cap, cent)
    footer(im, 5, "Концепт-визуализации")
    return im


def slide6():
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    label(d, "События в салоне")
    title(d, [[("ЗАПУСК МОДЕЛИ И", WHITE)], [("КЛИЕНТСКОЕ СОБЫТИЕ", PURPLE)]], 84, 116, 58)
    rounded_paste(im, ASSETS / "dealer-model-launch.jpg", (84, 290, 1080, 610), radius=28, border=BORDER)
    card(im, (1200, 290, 1836, 900))
    d.text((1244, 336), "СОСТАВ ПРОЕКТА", font=font(22, "Bold"), fill=GOLD)
    bullets(d, [
        "подиум и презентационный фон",
        "фотозона или Brand Wall",
        "стойка регистрации и welcome-зона",
        "навигация и маршрут гостей",
        "объёмная графика и декоративный свет",
        "монтаж, дежурство и демонтаж",
    ], 1244, 405, 540, 22, 18)
    d.text((1244, 822), "Сценарий → состав конструкций → график монтажа", font=font(17, "SemiBold"), fill=SUBTLE)
    footer(im, 6, "Концепт-визуализация")
    return im


def slide7():
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    label(d, "SM-Production · кто мы")
    title(d, [[("ПРОИЗВОДСТВО,", WHITE)], [("А НЕ ПОСРЕДНИКИ", PURPLE)]], 84, 120, 62)
    wrap(d, "Собственный цех в Москве: печать, раскрой, сборка, контроль комплектности и подготовка к монтажу. Один руководитель проекта координирует задачу от брифа до сдачи объекта.", (84, 315), 900, font(26), WHITE, 9)
    stats = [("ОТ 1 ДНЯ", "Простые конструкции"), ("1 ГОД", "Гарантия на конструкции"), ("24/7", "Производство и монтаж"), ("ФОТООТЧЁТ", "Контроль по этапам")]
    for i, (big, small) in enumerate(stats):
        x = 84 + (i % 2) * 480; y = 590 + (i // 2) * 170
        card(im, (x, y, x + 445, y + 142))
        d.text((x + 222, y + 32), big, font=font(38, "ExtraBold"), fill=GOLD, anchor="ma")
        d.text((x + 222, y + 98), small, font=font(18, "Bold"), fill=WHITE, anchor="mm")
    gx, gy, cw, ch = 1080, 0, 420, 326
    for i in range(6): rounded_paste(im, ASSETS / f"production-{i+1}.jpg", (gx + (i % 2) * cw, gy + (i // 2) * ch, cw, ch), radius=0)
    footer(im, 7)
    return im


def slide8():
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    label(d, "Первый проект")
    title(d, [[("ТРИ ФОРМАТА,", WHITE)], [("С КОТОРЫХ ЛЕГКО НАЧАТЬ", PURPLE)]], 84, 118, 58)
    offers = [
        ("01", "СЕЗОННОЕ ОБНОВЛЕНИЕ", ["витрины и баннеры", "Roll Up и POS", "напольная графика", "сменная навигация"]),
        ("02", "ПРЕЗЕНТАЦИЯ МОДЕЛИ", ["подиум и фон", "фотозона", "регистрация", "навигация гостей"]),
        ("03", "ОБНОВЛЕНИЕ ПРОСТРАНСТВА", ["ресепшн", "зона выдачи", "стены и логотипы", "фасадные элементы"]),
    ]
    for i, (num, ttl, lines) in enumerate(offers):
        x = 84 + i * 588; y = 315
        card(im, (x, y, x + 552, y + 530))
        d.text((x + 42, y + 50), num, font=font(50, "ExtraBold"), fill=GOLD)
        wrap(d, ttl, (x + 42, y + 130), 470, font(23, "Bold"), WHITE, 5)
        yy = y + 230
        for line in lines:
            d.rounded_rectangle((x + 44, yy + 9, x + 59, yy + 15), radius=3, fill=PURPLE)
            d.text((x + 78, yy), line, font=font(21), fill=MUTED); yy += 58
        d.rounded_rectangle((x + 42, y + 458, x + 510, y + 492), radius=12, outline=GOLD, width=2)
        d.text((x + 276, y + 475), "СОСТАВ И СРОК — ПОСЛЕ БРИФА", font=font(14, "Bold"), fill=GOLD, anchor="mm")
    d.text((84, 900), "Для предварительного расчёта достаточно фотографий зоны, примерных размеров, брендбука и даты запуска.", font=font(21, "SemiBold"), fill=WHITE)
    footer(im, 8)
    return im


def slide9():
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    label(d, "Процесс")
    title(d, [[("ОТ ФОТОГРАФИИ ЗОНЫ ДО", WHITE)], [("ГОТОВОГО МОНТАЖА", PURPLE)]], 84, 118, 55)
    steps = [
        ("1", "Экспресс-аудит", "Смотрим фото, задачу и дату."),
        ("2", "Замер и бриф", "Проверяем размеры и условия."),
        ("3", "Концепция", "Адаптируем брендбук."),
        ("4", "Смета и график", "Фиксируем состав и сроки."),
        ("5", "Производство", "Собираем комплекты по зонам."),
        ("6", "Монтаж и сдача", "Устанавливаем по графику."),
    ]
    for i, (num, ttl, txt) in enumerate(steps):
        x = 84 + (i % 3) * 380; y = 330 + (i // 3) * 292
        card(im, (x, y, x + 350, y + 260))
        d.text((x + 175, y + 30), num, font=font(44, "ExtraBold"), fill=GOLD, anchor="ma")
        d.text((x + 175, y + 100), ttl, font=font(19, "Bold"), fill=WHITE, anchor="ma")
        wrap(d, txt, (x + 30, y + 153), 290, font(18), MUTED, 5)
    rounded_paste(im, ASSETS / "dealer-night-installation.jpg", (1250, 0, 670, 980), radius=0, centering=(0.53, 0.5))
    d.rectangle((1250, 824, 1920, 980), fill="#111116")
    d.text((1300, 855), "МОНТАЖ ПО ГРАФИКУ САЛОНА", font=font(23, "Bold"), fill=GOLD)
    wrap(d, "Согласуем доступ, защиту поверхностей и последовательность открытия зон.", (1300, 905), 560, font(18), WHITE, 5)
    footer(im, 9, "Концепт-визуализация")
    return im


def slide10():
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    label(d, "Следующий шаг")
    title(d, [[("БЕСПЛАТНЫЙ ЭКСПРЕСС-АУДИТ", WHITE)], [("ПО ФОТОГРАФИЯМ САЛОНА", PURPLE)]], 84, 118, 54)
    wrap(d, "Пришлите фотографию зоны, примерные размеры и дату. Предложим состав носителей и в течение рабочего дня подготовим предварительный расчёт.", (84, 326), 1060, font(27), WHITE, 10)
    d.text((84, 514), "ДЛЯ СТАРТА ДОСТАТОЧНО", font=font(20, "Bold"), fill=GOLD)
    d.text((84, 564), "1. Фото или видео зоны     2. Дата запуска     3. Брендбук, если есть", font=font(21, "SemiBold"), fill=MUTED)
    contacts = [("Телефон · ПН–ПТ 10:00–18:00", "+7 (495) 799-00-19"), ("Почта", "sm-pro1@yandex.ru"), ("Сайт", "SM-PRODUCTION.RU")]
    x = 84
    for i, (cap, val) in enumerate(contacts):
        w = [360, 390, 340][i]; card(im, (x, 680, x + w, 806), radius=18)
        d.text((x + w / 2, 710), cap, font=font(15, "SemiBold"), fill=SUBTLE, anchor="ma")
        d.text((x + w / 2, 762), val, font=font(20 if i else 22, "Bold"), fill=GOLD if i == 0 else WHITE, anchor="mm"); x += w + 24
    d.rounded_rectangle((1260, 236, 1840, 296), radius=16, fill="#51277e")
    d.text((1550, 266), "SM-PRODUCTION.RU", font=font(28, "SemiBold"), fill=WHITE, anchor="mm")
    rounded_paste(im, ASSETS / "location-map.jpg", (1260, 322, 580, 452), radius=24, border=BORDER)
    d.text((1550, 818), "Москва, Остаповский проезд, д. 9 с. 3", font=font(22, "Bold"), fill=WHITE, anchor="mm")
    d.text((1550, 858), "м. Текстильщики", font=font(20), fill=MUTED, anchor="mm")
    footer(im, 10)
    return im


def save(slides):
    paths=[]
    for i, slide in enumerate(slides, 1):
        p=SLIDES/f"slide-{i:02d}.png"; slide.save(p, quality=95); paths.append(p)
    slides[0].save(ROOT/"SM-Production-dealership-proposal-2026.pdf", "PDF", resolution=144, save_all=True, append_images=slides[1:], quality=95, title="Оформление дилерских центров — SM Production")
    prs=Presentation(); prs.slide_width=Inches(13.333333); prs.slide_height=Inches(7.5); blank=prs.slide_layouts[6]
    for p in paths:
        s=prs.slides.add_slide(blank); s.shapes.add_picture(str(p),0,0,width=prs.slide_width,height=prs.slide_height)
    prs.save(ROOT/"SM-Production-dealership-proposal-2026.pptx")

if __name__ == "__main__":
    slides=[slide1(),slide2(),slide3(),slide4(),slide5(),slide6(),slide7(),slide8(),slide9(),slide10()]
    save(slides)
    print(f"Built {len(slides)} slides")
