#!/usr/bin/env python3
"""
Презентация первого касания с директором «Аником Арены».

16:9, 1920×1080 pt. Векторный PDF: текст живой, шрифты вложены,
фотографии предварительно готовятся в JPEG (иначе PDF раздувается в 100 раз).

Стиль из текущего макета SM: NAVY #08192D, коралл #D94941,
заголовки Unbounded, текст Golos Text.

Запуск:
    .venv/bin/python docs/anikom-arena/pitch/build_pitch.py
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image as PILImage
from reportlab.lib.colors import Color, HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parent
FONTS = ROOT / "source" / "fonts"
IMG = ROOT / "source" / "img"
OUT = ROOT / "out"
CACHE = OUT / ".cache"

W, H = 1920, 1080
M = 112
COL = W - 2 * M

NAVY = HexColor("#08192D")
NAVY_2 = HexColor("#0C2237")
NAVY_3 = HexColor("#123049")
CORAL = HexColor("#D94941")
WHITE = HexColor("#FFFFFF")
MUTED = HexColor("#9BAEBF")
PAPER = HexColor("#E9EFF4")
INK = HexColor("#08192D")
INK_SOFT = HexColor("#54697C")
LIGHT_TEXT = HexColor("#C9D6E1")

FONT_FILES = {
    "UB": "Unbounded-Bold.ttf",
    "UBs": "Unbounded-SemiBold.ttf",
    "GR": "GolosText-Regular.ttf",
    "GM": "GolosText-Medium.ttf",
    "GS": "GolosText-SemiBold.ttf",
    "GB": "GolosText-Bold.ttf",
}
F = {}


def register_fonts() -> None:
    for key, filename in FONT_FILES.items():
        pdfmetrics.registerFont(TTFont(key, str(FONTS / filename)))
        F[key] = key


def tw(text: str, font: str, size: float) -> float:
    return pdfmetrics.stringWidth(text, font, size)


def wrap(text: str, font: str, size: float, width: float) -> list[str]:
    lines: list[str] = []
    for paragraph in text.split("\n"):
        line = ""
        for word in paragraph.split(" "):
            probe = f"{line} {word}".strip()
            if tw(probe, font, size) <= width or not line:
                line = probe
            else:
                lines.append(line)
                line = word
        lines.append(line)
    return lines


def text_block(c, text, font, size, x, y, width, leading=None, color=INK, align="left"):
    leading = leading or size * 1.45
    for line in wrap(text, font, size, width):
        c.setFillColor(color)
        c.setFont(font, size)
        if align == "right":
            c.drawRightString(x + width, y, line)
        elif align == "center":
            c.drawCentredString(x + width / 2, y, line)
        else:
            c.drawString(x, y, line)
        y -= leading
    return y + leading


def block_height(text, font, size, width, leading=None) -> float:
    leading = leading or size * 1.45
    return len(wrap(text, font, size, width)) * leading


def kicker(c, text, x, y, color=CORAL, size=16):
    c.setFillColor(color)
    c.rect(x, y + size * 1.15, 44, 5, fill=1, stroke=0)
    c.setFont("GS", size)
    c.drawString(x + 60, y, text.upper())


def page_bg(c, color):
    c.setFillColor(color)
    c.rect(0, 0, W, H, fill=1, stroke=0)


def footer(c, left, right, dark=True):
    color = MUTED if dark else INK_SOFT
    c.setFillColor(color)
    c.setFont("GR", 15)
    c.drawString(M, 44, left)
    c.drawRightString(W - M, 44, right)


# ───────────────────────────────────────────── подготовка фотографий

_prepared: dict[tuple[str, int, int], Path] = {}


def prepare(name: str, w_pt: float, h_pt: float, focus=(0.5, 0.5), dpi: int = 150,
            scrim_left: float = 0.0) -> Path:
    """Кроп, затемнение и сохранение в JPEG.

    scrim_left — доля ширины, на которой слева направо уходит затемнение в NAVY.
    Делается в Pillow: градиенты reportlab ложатся неровно.
    """
    px_w = max(64, round(w_pt / 72 * dpi))
    key = (name, px_w, round(h_pt / w_pt * 1000), scrim_left)
    if key in _prepared:
        return _prepared[key]

    im = PILImage.open(IMG / name).convert("RGB")
    target = w_pt / h_pt
    src = im.width / im.height
    if src > target:
        nw = round(im.height * target)
        x0 = round((im.width - nw) * focus[0])
        im = im.crop((x0, 0, x0 + nw, im.height))
    else:
        nh = round(im.width / target)
        y0 = round((im.height - nh) * focus[1])
        im = im.crop((0, y0, im.width, y0 + nh))
    if im.width > px_w:
        im = im.resize((px_w, round(px_w * h_pt / w_pt)), PILImage.LANCZOS)

    if scrim_left > 0:
        from PIL import ImageDraw as _D
        w_px, h_px = im.size
        veil = PILImage.new("L", (w_px, 1))
        span = max(1, int(w_px * scrim_left))
        d = _D.Draw(veil)
        for x in range(span):
            t = x / span
            # плавно: у левого края сплошной NAVY, к концу полосы — прозрачно
            d.point((x, 0), fill=int(255 * (1 - t) ** 1.35))
        veil = veil.resize((w_px, h_px), PILImage.BILINEAR)
        layer = PILImage.new("RGB", (w_px, h_px), (8, 25, 45))
        im = PILImage.composite(layer, im, veil)

    CACHE.mkdir(parents=True, exist_ok=True)
    suffix = f"-s{int(scrim_left*100)}" if scrim_left else ""
    path = CACHE / f"{Path(name).stem}-{px_w}x{round(px_w * h_pt / w_pt)}{suffix}.jpg"
    im.save(path, "JPEG", quality=84, optimize=True, progressive=True)
    _prepared[key] = path
    return path


def photo(c, name, x, y, w, h, radius=0, focus=(0.5, 0.5), scrim_left=0.0):
    path = prepare(name, w, h, focus, scrim_left=scrim_left)
    c.saveState()
    if radius:
        clip = c.beginPath()
        clip.roundRect(x, y, w, h, radius)
        c.clipPath(clip, stroke=0, fill=0)
    c.drawImage(str(path), x, y, w, h, mask=None)
    c.restoreState()


def logo(c, x, y, width, white=True):
    path = IMG / ("sm-logo-white.png" if white else "sm-logo-navy.png")
    im = PILImage.open(path)
    h = width * im.height / im.width
    c.drawImage(str(path), x, y, width, h, mask="auto")
    return h


# ─────────────────────────────────────────────────────────── слайды

def s01_cover(c):
    page_bg(c, NAVY)
    photo(c, "arena-2.jpg", 700, 0, W - 700, H, focus=(0.58, 0.42), scrim_left=0.62)

    logo(c, M, H - 150, 150)

    kicker(c, "первое предложение · 11.11.2026", M, 742)

    c.setFillColor(WHITE)
    c.setFont("UB", 58)
    width_avail = 700 - M - 60
    c.drawString(M, 650, "ОФОРМЛЕНИЕ")
    c.drawString(M, 574, "АНИКОМ АРЕНЫ")
    c.setFillColor(CORAL)
    c.rect(M, 534, 112, 7, fill=1, stroke=0)

    text_block(c, "Четыре зоны, которые видят зрители,\nкамеры и партнёры — каждый матч.",
               "GR", 26, M, 470, 560, leading=36, color=LIGHT_TEXT)

    c.setFillColor(MUTED)
    c.setFont("GR", 16)
    c.drawString(M, 128, "Общий концепт для обсуждения и последующих замеров")
    c.setFont("GS", 16)
    c.drawString(M, 96, "SM Production · Москва")
    c.showPage()


def s02_diagnosis(c):
    page_bg(c, PAPER)
    kicker(c, "с чего начинается разговор", M, H - 150)
    c.setFillColor(INK)
    c.setFont("UB", 44)
    c.drawString(M, H - 236, "Арена выглядит как спортплощадка,")
    c.drawString(M, H - 292, "а не как стадион уровня мероприятий")
    c.setFillColor(INK_SOFT)
    c.setFont("GR", 22)
    c.drawString(M, H - 344, "Это не про красоту. Это про деньги и про то, что попадает в кадр.")

    cards = [
        ("Эфир", "Камеры снимают арену 22 раза в неделю. В кадре — белые панели и сетка, "
                 "а не бренды партнёров."),
        ("Деньги", "Спонсорские пакеты продаются, но рекламу некуда нанести: "
                   "носителей, которые видят в кадре, почти нет."),
        ("Первый кадр", "Телебашня — самая заметная точка объекта — сейчас пустая "
                        "белая панель."),
        ("Повтор", "Каждый турнир и матч проходит без сменных материалов: "
                   "нечего менять от события к событию."),
    ]
    gap = 30
    cw = (COL - 3 * gap) / 4
    ch = 264
    top = 660
    for i, (title, body) in enumerate(cards):
        x = M + i * (cw + gap)
        c.setFillColor(WHITE)
        c.roundRect(x, top - ch, cw, ch, 12, fill=1, stroke=0)
        c.setFillColor(CORAL)
        c.rect(x + 26, top - 32, 46, 5, fill=1, stroke=0)
        c.setFillColor(INK)
        c.setFont("UB", 20)
        c.drawString(x + 26, top - 74, title)
        text_block(c, body, "GR", 16.5, x + 26, top - 108, cw - 52, leading=25, color=INK_SOFT)

    c.setFillColor(NAVY)
    c.roundRect(M, 120, COL, 130, 12, fill=1, stroke=0)
    c.setFillColor(CORAL)
    c.setFont("GS", 15)
    c.drawString(M + 30, 206, "ВЫВОД ДЛЯ РАЗГОВОРА")
    c.setFillColor(WHITE)
    c.setFont("GS", 22)
    c.drawString(M + 30, 166, "Арене нужен не один баннер, а комплект носителей, которые работают каждый матч.")
    c.setFillColor(MUTED)
    c.setFont("GR", 16)
    c.drawString(M + 30, 138, "Дальше — четыре зоны, где это даёт эффект быстрее всего.")

    footer(c, "Аником Арена · первое предложение", "02", dark=False)
    c.showPage()


def s03_concept(c):
    page_bg(c, NAVY)
    kicker(c, "суть предложения", M, H - 150)
    c.setFillColor(WHITE)
    c.setFont("UB", 42)
    c.drawString(M, H - 236, "Не разовая печать, а система")
    c.drawString(M, H - 288, "оформления арены")

    text_block(c, "Собираем оформление в один комплект: зоны, носители, сменные модули. "
                  "Дальше это живёт сезон за сезоном — меняется только печать.",
               "GR", 22, M, H - 344, 700, leading=32, color=LIGHT_TEXT)

    c.setFillColor(CORAL)
    c.setFont("GS", 15)
    c.drawString(M, 610, "КАК ЭТО РАБОТАЕТ")

    steps = [
        ("01", "Замер", "Выезжаем на объект, снимаем размеры зон и креплений"),
        ("02", "Концепт", "2–3 варианта дизайна под задачи арены и партнёров"),
        ("03", "Производство", "Свой цех: печать, фрезеровка ПВХ, каркасы"),
        ("04", "Монтаж", "Ставим и обслуживаем, меняем печать к событию"),
    ]
    y = 536
    for num, title, body in steps:
        c.setFillColor(CORAL)
        c.setFont("UB", 24)
        c.drawString(M, y, num)
        c.setFillColor(WHITE)
        c.setFont("GS", 24)
        c.drawString(M + 86, y, title)
        c.setFillColor(MUTED)
        c.setFont("GR", 18)
        c.drawString(M + 86, y - 30, body)
        c.setStrokeColor(HexColor("#1D3A54"))
        c.setLineWidth(1)
        c.line(M, y - 56, M + 760, y - 56)
        y -= 104

    photo(c, "photozone.jpg", 980, 300, 828, 470, radius=14, focus=(0.5, 0.45))
    c.setFillColor(NAVY_3)
    c.rect(980, 300, 828, 66, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont("GR", 17)
    c.drawString(1006, 324, "Имиджевая фотозона — пример нашего оформления объекта")

    c.setFillColor(MUTED)
    c.setFont("GR", 16)
    c.drawString(980, 246, "Фотозона, баннеры и навигация на реальных объектах — слайд 09")

    footer(c, "Аником Арена · первое предложение", "03")
    c.showPage()


def s04_map(c):
    page_bg(c, PAPER)
    kicker(c, "объект", M, H - 150)
    c.setFillColor(INK)
    c.setFont("UB", 42)
    c.drawString(M, H - 236, "С чего начинаем: арена и её сильные стороны")

    photo(c, "arena-2.jpg", M, 420, COL, 400, radius=14, focus=(0.5, 0.44))

    nums = [
        ("01", "Телебашня", "Самая заметная точка, всегда в кадре"),
        ("02", "Трибуны", "Нижний и верхний пояса, пролёты между дверями"),
        ("03", "PressWall", "Постоянное брендирование и партнёрская линия"),
        ("04", "Навигация", "20 табличек: раздевалки, кафе, входы"),
    ]
    gap = 28
    cw = (COL - 3 * gap) / 4
    y = 150
    for i, (num, title, cap) in enumerate(nums):
        x = M + i * (cw + gap)
        c.setFillColor(WHITE)
        c.roundRect(x, y, cw, 214, 12, fill=1, stroke=0)
        c.setFillColor(CORAL)
        c.setFont("UB", 30)
        c.drawString(x + 24, y + 150, num)
        c.setFillColor(INK)
        c.setFont("GS", 21)
        c.drawString(x + 24, y + 100, title)
        text_block(c, cap, "GR", 16, x + 24, y + 68, cw - 48, leading=23, color=INK_SOFT)

    footer(c, "Аником Арена · первое предложение", "04", dark=False)
    c.showPage()


def zone_slide(c, num, title, subtitle, bullets, photo_name, caption, page_no, effect, focus=(0.5, 0.5)):
    page_bg(c, NAVY)
    kicker(c, f"зона {num}", M, H - 150)

    c.setFillColor(CORAL)
    c.setFont("UB", 84)
    c.drawString(M, H - 300, num)

    c.setFillColor(WHITE)
    c.setFont("UB", 42)
    c.drawString(M + 168, H - 262, title)
    text_block(c, subtitle, "GR", 21, M + 132, H - 306, 700, leading=30, color=LIGHT_TEXT)

    y = H - 420
    for head, body in bullets:
        c.setFillColor(CORAL)
        c.rect(M, y + 7, 8, 8, fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont("GS", 20)
        c.drawString(M + 26, y, head)
        end = text_block(c, body, "GR", 17, M + 26, y - 28, 740, leading=25, color=MUTED)
        y = end - 30

    photo(c, photo_name, 1000, 236, 808, 560, radius=14, focus=focus)
    c.setFillColor(NAVY_3)
    c.rect(1000, 236, 808, 62, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont("GR", 16)
    c.drawString(1026, 258, caption)

    panel_w = 780
    body_h = block_height(effect, "GR", 17, panel_w - 56, leading=25)
    panel_h = 58 + body_h + 14
    c.setFillColor(NAVY_2)
    c.roundRect(M, 128, panel_w, panel_h, 12, fill=1, stroke=0)
    c.setFillColor(CORAL)
    c.rect(M, 128, 6, panel_h, fill=1, stroke=0)
    c.setFont("GS", 14)
    c.drawString(M + 28, 128 + panel_h - 32, "ЧТО ЭТО ДАЁТ АРЕНЕ")
    text_block(c, effect, "GR", 17, M + 28, 128 + panel_h - 62, panel_w - 56, leading=25, color=WHITE)

    footer(c, "Аником Арена · первое предложение", page_no)
    c.showPage()


def s05_zone1(c):
    zone_slide(
        c, "01", "Телебашня",
        "Самая заметная точка арены: её видно с поля, с трибуны и в каждом кадре трансляции.",
        [
            ("Сейчас", "Белая панель под камерой — самое большое пустое место объекта. "
                       "Баннер заменяемый, печать под турнир."),
            ("Предлагаем", "Крупный логотип арены в центре + линейка партнёров внизу. "
                           "Концепт подстраиваем под ваши задачи."),
            ("Крепление", "Два варианта: баннер на люверсах или на плоском каркасе. "
                          "Выбираем после осмотра башни."),
            ("Следующий шаг", "Нужен замер панели: точные размеры и способ крепления."),
        ],
        "tower-before.jpg", "Сейчас здесь пустая панель — точка, куда смотрит камера", "05",
        "Носитель, который видно каждый матч и на каждой трансляции. Это сильный аргумент "
        "в спонсорском предложении: место, которое гарантированно попадает в кадр.",
        focus=(0.55, 0.45),
    )


def s06_zone2(c):
    zone_slide(
        c, "02", "Трибуны",
        "Вторая по важности зона: попадает во все трансляции, фото и соцсети арены.",
        [
            ("Нижний пояс", "Баннеры на люверсах или каркасе — самая видимая часть трибуны."),
            ("Верхняя часть", "Панели из композита с печатью или оклейка плёнкой, "
                              "крепление в существующие отверстия."),
            ("Вывеска", "Вывеску школы ПФК ЦСКА делаем такую же — размеры и стоимость посчитаем."),
            ("Пролёты", "Между техническими дверями — широкоформатные баннеры "
                        "по принципу телебашни."),
        ],
        "arena-wide.jpg", "Трибуна арены: пояса под баннеры и панели", "06",
        "Два пояса носителей на одной трибуне: постоянные панели сверху и сменные баннеры "
        "снизу. Партнёров можно менять, не трогая конструкцию.",
        focus=(0.6, 0.45),
    )


def s07_zone3(c):
    zone_slide(
        c, "03", "PressWall",
        "Не только фон для фото: постоянное брендирование и партнёрская линия.",
        [
            ("Что видим", "Существующий баннер слегка перетянут — картинка деформируется, "
                          "на фото это видно."),
            ("Что делаем", "Такую же конструкцию (Joker / Tritix) — или новую на скрытом "
                           "каркасе из бруса."),
            ("Преимущества", "Брус подходит для улицы и помещения, может быть двусторонним, "
                             "устойчив за счёт утяжеления внутри."),
            ("Переезд", "Переставляется двумя людьми — удобно под турнирные раскладки."),
        ],
        "presswall-5-0.jpg", "Наш макет presswall для арены: «Энергия игры»", "07",
        "Двусторонний носитель, который работает и в помещении, и на улице. "
        "Один раз изготовили конструкцию — дальше меняете только полотно.",
        focus=(0.5, 0.5),
    )


def s08_zone4(c):
    zone_slide(
        c, "04", "Навигация",
        "Люди приходят на арену впервые каждую неделю — и каждый раз ищут раздевалку.",
        [
            ("Что делаем", "Таблички: печать на ПВХ 5 мм + фрезеровка контура."),
            ("Комплект", "Около 20 табличек: раздевалки, судейская, кафе, медпункт, "
                         "пресс-центр, парковка."),
            ("Плюс", "Указатели на трибуны и вход, схема эвакуации по нормам."),
            ("Почему важно", "Это первое впечатление об объекте: гости, родители, "
                             "команды-гости."),
        ],
        "reception.jpg", "Ресепшн арены: точка, где начинается любой маршрут", "08",
        "Навигация снижает количество вопросов на входе и делает объект понятным "
        "с первого визита — без администратора рядом.",
        focus=(0.5, 0.55),
    )


def s09_cases(c):
    page_bg(c, NAVY)
    kicker(c, "наши объекты", M, H - 142)
    c.setFillColor(WHITE)
    c.setFont("UB", 38)
    c.drawString(M, H - 222, "Мы уже делали это на других объектах")

    c.setFillColor(MUTED)
    c.setFont("GR", 17)
    c.drawString(M, H - 262, "Ниже — наши работы. Оформление арены — на слайдах 05–08.")

    tiles = [
        ("montage.jpg", "Монтаж на объекте", "Наша бригада: конструкции, свет, объёмные элементы", (0.5, 0.42)),
        ("workshop.jpg", "Имиджевые зоны", "Фотозоны с подсветкой и объёмными элементами", (0.35, 0.5)),
        ("banner-arena.jpg", "Аренда конструкций", "Скрытый каркас с утяжелением, двусторонняя печать", (0.5, 0.5)),
    ]
    gap = 28
    tw_ = (COL - 2 * gap) / 3
    th = 400
    y = 360
    for i, (img, title, cap, focus) in enumerate(tiles):
        x = M + i * (tw_ + gap)
        photo(c, img, x, y, tw_, th, radius=12, focus=focus)
        c.setFillColor(WHITE)
        c.setFont("GS", 20)
        c.drawString(x, y - 38, title)
        c.setFillColor(MUTED)
        c.setFont("GR", 15.5)
        for j, line in enumerate(wrap(cap, "GR", 15.5, tw_)):
            c.drawString(x, y - 62 - j * 21, line)

    c.setFillColor(NAVY_2)
    c.roundRect(M, 132, COL, 96, 12, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont("GS", 19)
    c.drawString(M + 30, 188, "Опыт, который переносится на арену: конструкции, баннеры, навигация, фотозоны")
    c.setFillColor(MUTED)
    c.setFont("GR", 15.5)
    c.drawString(M + 30, 158, "Своё производство и монтаж — сроки и качество держим сами")

    footer(c, "Аником Арена · первое предложение", "09")
    c.showPage()


def s10_production(c):
    page_bg(c, PAPER)
    kicker(c, "почему мы", M, H - 150)
    c.setFillColor(INK)
    c.setFont("UB", 42)
    c.drawString(M, H - 236, "Своё производство, а не посредники")

    photo(c, "print.jpg", M, 300, 780, 480, radius=12, focus=(0.5, 0.5))
    c.setFillColor(WHITE)
    c.rect(M, 300, 780, 60, fill=1, stroke=0)
    c.setFillColor(INK_SOFT)
    c.setFont("GR", 16)
    c.drawString(M + 22, 322, "Широкоформатная печать в цеху SM Production")

    items = [
        ("750 м²", "производство"),
        ("24/7", "режим монтажа"),
        ("Печать", "баннер, плёнка, ПВХ"),
        ("Фрезеровка", "ПВХ и композит"),
        ("Каркасы", "плоские и скрытые"),
        ("Монтаж", "своя бригада"),
    ]
    x0 = M + 848
    cw = (W - M - x0 - 26) / 2
    for i, (head, cap) in enumerate(items):
        r, cc = divmod(i, 2)
        x = x0 + cc * (cw + 26)
        y = H - 320 - r * 112
        c.setFillColor(CORAL)
        c.setFont("UB", 27)
        c.drawString(x, y, head)
        c.setFillColor(INK_SOFT)
        c.setFont("GR", 16)
        c.drawString(x, y - 24, cap)

    c.setFillColor(NAVY)
    c.roundRect(M, 132, 780, 130, 12, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont("GS", 19)
    text_block(c, "Один подрядчик на весь цикл: замер, дизайн, производство, монтаж, "
                  "замена печати к следующему событию.",
               "GR", 19, M + 28, 226, 724, leading=28, color=WHITE)

    footer(c, "Аником Арена · первое предложение", "10", dark=False)
    c.showPage()


def s11_next(c):
    page_bg(c, NAVY)
    kicker(c, "что предлагаем дальше", M, H - 150)
    c.setFillColor(WHITE)
    c.setFont("UB", 40)
    c.drawString(M, H - 236, "Три шага, чтобы перейти от концепта к делу")

    steps = [
        ("Шаг 1", "Встреча на объекте", "Проход по арене, уточняем задачи сезона и приоритет по зонам."),
        ("Шаг 2", "Замер", "Снимаем размеры четырёх зон и креплений. По итогам — точный состав и смета."),
        ("Шаг 3", "Пилот", "Начинаем с одной зоны: телебашня или presswall. Дальше — по готовности."),
    ]
    y = H - 330
    for tag, title, body in steps:
        c.setFillColor(CORAL)
        c.setFont("GS", 15)
        c.drawString(M, y, tag.upper())
        c.setFillColor(WHITE)
        c.setFont("GS", 26)
        c.drawString(M, y - 40, title)
        text_block(c, body, "GR", 18, M, y - 74, 620, leading=27, color=MUTED)
        y -= 176

    photo(c, "arena-2.jpg", 900, 330, 908, 420, radius=12, focus=(0.5, 0.45))

    c.setFillColor(NAVY_2)
    c.roundRect(M, 120, 700, 128, 12, fill=1, stroke=0)
    c.setFillColor(CORAL)
    c.setFont("GS", 15)
    c.drawString(M + 28, 204, "КОНТАКТ")
    c.setFillColor(WHITE)
    c.setFont("GS", 24)
    c.drawString(M + 28, 166, "+7 (495) 799-00-19")
    c.setFillColor(MUTED)
    c.setFont("GR", 16)
    c.drawString(M + 28, 138, "sm-pro1@yandex.ru · Москва")

    footer(c, "Аником Арена · первое предложение", "11")
    c.showPage()


def s12_thanks(c):
    page_bg(c, NAVY)
    photo(c, "arena-2.jpg", 0, 0, W, H, focus=(0.5, 0.42))
    c.setFillColor(Color(0.031, 0.098, 0.176, alpha=0.84))
    c.rect(0, 0, W, H, fill=1, stroke=0)

    kicker(c, "спасибо за внимание", M, H - 300)
    c.setFillColor(WHITE)
    c.setFont("UB", 64)
    c.drawString(M, H - 420, "Готовы приехать")
    c.drawString(M, H - 500, "на объект")

    text_block(c, "Посмотрим зоны, снимем размеры и назовём сроки.\nПервый шаг — за вами.",
               "GR", 26, M, H - 560, 800, leading=38, color=LIGHT_TEXT)

    c.setFillColor(WHITE)
    c.setFont("GS", 30)
    c.drawString(M, 210, "+7 (495) 799-00-19")
    c.setFillColor(MUTED)
    c.setFont("GR", 18)
    c.drawString(M, 176, "sm-pro1@yandex.ru")
    c.drawString(M, 144, "SM Production · event · branding · decor")

    logo(c, W - M - 140, H - 180, 140)
    c.showPage()


def main() -> int:
    register_fonts()
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "Anikom-Arena-first-meeting.pdf"
    c = canvas.Canvas(str(path), pagesize=(W, H))
    c.setTitle("Аником Арена — оформление арены, первое предложение")
    c.setAuthor("SM Production")
    c.setSubject("Презентация для первого касания с директором арены")

    for slide in (s01_cover, s02_diagnosis, s03_concept, s04_map,
                  s05_zone1, s06_zone2, s07_zone3, s08_zone4,
                  s09_cases, s10_production, s11_next, s12_thanks):
        slide(c)

    c.save()
    print(f"готово: {path}  {path.stat().st_size // 1024} КБ")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
