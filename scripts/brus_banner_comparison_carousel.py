#!/usr/bin/env python3
"""Create Post #4 comparison carousel for SM Production (1200×675)."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "visualizations" / "brus-banner-comparison" / "assets"
OUT = ROOT / "visualizations" / "brus-banner-comparison"

W, H, SS = 1200, 675, 2
CW, CH = W * SS, H * SS
BG = (7, 18, 29)
CARD = (13, 30, 44)
INK = (247, 249, 251)
MUTED = (164, 179, 193)
ORANGE = (255, 80, 38)
ACID = (216, 255, 56)
LINE = (255, 255, 255, 35)
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

SOURCES = {
    "rollup": ASSETS / "roll-up-scene.jpg",
    "joker": ASSETS / "joker-banner-scene.jpg",
    "timber": ASSETS / "timber-banner-scene.jpg",
}


def sc(v):
    return round(v * SS)


def font(size, bold=False):
    return ImageFont.truetype(FONT_B if bold else FONT, sc(size))


def cover(path, size):
    im = Image.open(path).convert("RGB")
    tw, th = size
    scale = max(tw / im.width, th / im.height)
    im = im.resize((round(im.width * scale), round(im.height * scale)), Image.Resampling.LANCZOS)
    left = (im.width - tw) // 2
    top = (im.height - th) // 2
    return im.crop((left, top, left + tw, top + th)).convert("RGBA")


def base():
    im = Image.new("RGB", (CW, CH), BG)
    d = ImageDraw.Draw(im)
    for y in range(CH):
        t = y / max(CH - 1, 1)
        d.line((0, y, CW, y), fill=(7 + round(3 * t), 18 + round(7 * t), 29 + round(10 * t)))
    # Quiet glow.
    glow = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((sc(-180), sc(-240), sc(560), sc(430)), fill=ORANGE + (35,))
    gd.ellipse((sc(780), sc(270), sc(1420), sc(850)), fill=(39, 120, 153, 36))
    return Image.alpha_composite(im.convert("RGBA"), glow.filter(ImageFilter.GaussianBlur(sc(90))))


def draw_brand(d, x=48, y=34, dark=True):
    fill = (4, 14, 23, 205) if dark else (255, 255, 255, 24)
    d.rounded_rectangle((sc(x), sc(y), sc(x + 238), sc(y + 48)), radius=sc(24), fill=fill, outline=(255, 255, 255, 75), width=sc(1))
    d.ellipse((sc(x + 17), sc(y + 17), sc(x + 31), sc(y + 31)), fill=ACID + (255,))
    d.text((sc(x + 44), sc(y + 13)), "SM PRODUCTION", font=font(17, True), fill=INK + (255,))


def draw_index(d, index, total=5):
    text = f"{index:02d} / {total:02d}"
    box = d.textbbox((0, 0), text, font=font(13, True))
    d.text((CW - sc(48) - (box[2] - box[0]), sc(49)), text, font=font(13, True), fill=MUTED + (255,))


def rounded_photo(path, size, radius=22):
    im = cover(path, (sc(size[0]), sc(size[1])))
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, im.width, im.height), radius=sc(radius), fill=255)
    im.putalpha(mask)
    return im


def wrap(draw, text, fnt, max_width):
    words = text.split()
    lines, current = [], ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textbbox((0, 0), candidate, font=fnt)[2] <= max_width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_wrapped(draw, xy, text, fnt, fill, max_width, spacing=8, max_lines=None):
    lines = wrap(draw, text, fnt, max_width)
    if max_lines:
        lines = lines[:max_lines]
    x, y = xy
    line_h = draw.textbbox((0, 0), "Аg", font=fnt)[3]
    for line in lines:
        draw.text((x, y), line, font=fnt, fill=fill)
        y += line_h + sc(spacing)
    return y


def save(im, name):
    out = OUT / name
    im.convert("RGB").resize((W, H), Image.Resampling.LANCZOS).save(out, quality=96, subsampling=0, optimize=True)
    print(out)


def slide_cover():
    im = base()
    d = ImageDraw.Draw(im, "RGBA")
    draw_brand(d)
    draw_index(d, 1)
    d.text((sc(48), sc(111)), "КАКУЮ КОНСТРУКЦИЮ", font=font(38, True), fill=INK + (255,))
    d.text((sc(48), sc(157)), "ВЫБРАТЬ ДЛЯ МЕРОПРИЯТИЯ?", font=font(38, True), fill=ORANGE + (255,))
    d.text((sc(50), sc(211)), "ROLL-UP  •  ДЖОКЕР  •  БРУС-БАННЕР", font=font(17, True), fill=MUTED + (255,))

    cards = [
        ("rollup", "ROLL-UP", "Быстро и мобильно"),
        ("joker", "ДЖОКЕР", "Практично и бюджетно"),
        ("timber", "БРУС-БАННЕР", "Премиальный фон"),
    ]
    x0, gap, card_w, card_h, y = 48, 18, 356, 360, 270
    for i, (key, title, subtitle) in enumerate(cards):
        x = x0 + i * (card_w + gap)
        photo = rounded_photo(SOURCES[key], (card_w, card_h), 22)
        im.alpha_composite(photo, (sc(x), sc(y)))
        shade = Image.new("RGBA", (sc(card_w), sc(card_h)), (0, 0, 0, 0))
        sd = ImageDraw.Draw(shade)
        for py in range(sc(card_h)):
            t = py / sc(card_h)
            alpha = round(max(0, (t - 0.48) / 0.52) * 220)
            sd.line((0, py, sc(card_w), py), fill=(2, 10, 18, alpha))
        shade.putalpha(Image.composite(shade.getchannel("A"), Image.new("L", shade.size, 0), photo.getchannel("A")))
        im.alpha_composite(shade, (sc(x), sc(y)))
        d = ImageDraw.Draw(im, "RGBA")
        d.rounded_rectangle((sc(x + 18), sc(y + 18), sc(x + 66), sc(y + 48)), radius=sc(15), fill=(5, 15, 24, 205))
        d.text((sc(x + 31), sc(y + 25)), f"0{i + 1}", font=font(12, True), fill=ACID + (255,))
        d.text((sc(x + 20), sc(y + 292)), title, font=font(23, True), fill=INK + (255,))
        d.text((sc(x + 20), sc(y + 326)), subtitle, font=font(13), fill=(232, 238, 243, 215))
    save(im, "post-04-slide-01-cover.jpg")


def detail_slide(index, key, overline, title, subtitle, rating, facts, suitable, accent):
    im = Image.new("RGBA", (CW, CH), BG + (255,))
    # Product occupies the left side; the panel keeps typography deterministic.
    photo = cover(SOURCES[key], (sc(770), CH))
    im.alpha_composite(photo, (0, 0))
    # Darken photo edges and add right panel.
    overlay = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for x in range(sc(770)):
        t = x / sc(770)
        alpha = round(25 + 150 * max(0, (t - 0.55) / 0.45))
        od.line((x, 0, x, CH), fill=(4, 15, 24, alpha))
    od.rectangle((sc(710), 0, CW, CH), fill=(7, 18, 29, 248))
    im = Image.alpha_composite(im, overlay)
    d = ImageDraw.Draw(im, "RGBA")
    draw_brand(d)
    draw_index(d, index)

    px = 750
    d.text((sc(px), sc(105)), overline, font=font(13, True), fill=accent + (255,))
    d.text((sc(px), sc(136)), title, font=font(34, True), fill=INK + (255,))
    draw_wrapped(d, (sc(px), sc(183)), subtitle, font(15), MUTED + (255,), sc(390), spacing=4, max_lines=2)

    d.text((sc(px), sc(255)), "ВНЕШНИЙ ВИД", font=font(11, True), fill=MUTED + (255,))
    d.text((sc(px), sc(278)), "★" * rating + "☆" * (5 - rating), font=font(24, True), fill=accent + (255,))

    y = 339
    for label, value in facts:
        d.line((sc(px), sc(y - 10), sc(1150), sc(y - 10)), fill=LINE, width=sc(1))
        d.text((sc(px), sc(y)), label.upper(), font=font(10, True), fill=MUTED + (255,))
        d.text((sc(px + 145), sc(y - 3)), value, font=font(16, True), fill=INK + (255,))
        y += 54

    d.rounded_rectangle((sc(px), sc(548), sc(1150), sc(629)), radius=sc(16), fill=(13, 37, 52, 255), outline=accent + (180,), width=sc(1))
    d.text((sc(px + 18), sc(562)), "ПОДХОДИТ ДЛЯ", font=font(10, True), fill=accent + (255,))
    draw_wrapped(d, (sc(px + 18), sc(584)), suitable, font(13, True), INK + (255,), sc(360), spacing=2, max_lines=2)
    save(im, f"post-04-slide-{index:02d}-{key}.jpg")


def slide_summary():
    im = base()
    d = ImageDraw.Draw(im, "RGBA")
    draw_brand(d)
    draw_index(d, 5)
    d.text((sc(48), sc(104)), "СРАВНЕНИЕ В ОДНОМ ЭКРАНЕ", font=font(33, True), fill=INK + (255,))
    d.text((sc(49), sc(148)), "Выбирайте конструкцию под задачу и будущий кадр", font=font(16), fill=MUTED + (255,))

    left, top = 48, 205
    col_widths = [260, 275, 275, 294]
    headers = ["ПАРАМЕТР", "ROLL-UP", "ДЖОКЕР", "БРУС-БАННЕР"]
    rows = [
        ("Монтаж", "5 минут", "1–2 часа", "2–3 часа"),
        ("Нестандартная форма", "Нет", "Ограниченно", "Да"),
        ("Каркас в кадре", "Видно основание", "Трубы видны", "Полностью скрыт"),
        ("Фото на фоне", "Базовый уровень", "Компромисс", "Оптимально"),
        ("Цена", "от 3 500 ₽", "от 9 000 ₽", "от 16 500 ₽"),
    ]
    x = left
    for i, (header, width) in enumerate(zip(headers, col_widths)):
        fill = ORANGE + (255,) if i == 3 else ((22, 42, 57, 255) if i else (13, 30, 44, 255))
        d.rounded_rectangle((sc(x), sc(top), sc(x + width - 8), sc(top + 50)), radius=sc(12), fill=fill)
        d.text((sc(x + 14), sc(top + 16)), header, font=font(11, True), fill=(255, 255, 255, 255) if i == 3 else INK + (255,))
        x += width

    row_h = 58
    for r, values in enumerate(rows):
        y = top + 60 + r * row_h
        x = left
        for c, (value, width) in enumerate(zip(values, col_widths)):
            if c == 3:
                fill = ORANGE + (255,)
            elif c == 0:
                fill = ((17, 36, 50, 255) if r % 2 == 0 else (14, 31, 44, 255))
            else:
                fill = ((23, 48, 65, 255) if r % 2 == 0 else (19, 41, 57, 255))
            d.rounded_rectangle((sc(x), sc(y), sc(x + width - 8), sc(y + row_h - 8)), radius=sc(9), fill=fill)
            fnt = font(12 if c else 11, c == 3 or c == 0)
            color = INK + (255,) if c else MUTED + (255,)
            d.text((sc(x + 14), sc(y + 16)), value, font=fnt, fill=color)
            x += width

    d.rounded_rectangle((sc(48), sc(565), sc(1152), sc(642)), radius=sc(18), fill=ACID + (255,), outline=(238, 255, 158, 255), width=sc(1))
    d.ellipse((sc(67), sc(585), sc(103), sc(621)), fill=BG + (255,))
    d.text((sc(78), sc(591)), "!", font=font(17, True), fill=ACID + (255,))
    d.text((sc(122), sc(579)), "БУДУТ ФОТОГРАФЫ И ПРЕССА?", font=font(13, True), fill=BG + (255,))
    d.text((sc(122), sc(605)), "Экономить на фоне не стоит: конструкция останется на каждом кадре.", font=font(15, True), fill=BG + (255,))
    save(im, "post-04-slide-05-summary.jpg")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    slide_cover()
    detail_slide(
        2,
        "rollup",
        "01  •  МОБИЛЬНАЯ СИСТЕМА",
        "ROLL-UP",
        "Для быстрых выездов и небольших площадок",
        3,
        [("Монтаж", "5 минут"), ("Форма", "Стандартная"), ("Цена", "от 3 500 ₽")],
        "Презентации, выездные встречи, точки продаж",
        (118, 170, 204),
    )
    detail_slide(
        3,
        "joker",
        "02  •  ТРУБЧАТЫЙ КАРКАС",
        "БАННЕР НА ДЖОКЕРЕ",
        "Практичная конструкция с видимым каркасом",
        2,
        [("Монтаж", "1–2 часа"), ("Форма", "С ограничениями"), ("Цена", "от 9 000 ₽")],
        "Уличные мероприятия, бюджетные промоакции",
        ORANGE,
    )
    detail_slide(
        4,
        "timber",
        "03  •  СКРЫТЫЙ КАРКАС",
        "БРУС-БАННЕР",
        "Монолитный фон без труб, креплений и складок",
        5,
        [("Монтаж", "2–3 часа"), ("Форма", "Любая"), ("Цена", "от 16 500 ₽")],
        "Конференции, форумы, премии, выставки, пресса",
        ACID,
    )
    slide_summary()


if __name__ == "__main__":
    main()
