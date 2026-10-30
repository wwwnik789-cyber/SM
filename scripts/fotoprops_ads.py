#!/usr/bin/env python3
"""Create five vertical SM Production ad creatives from the photoprops catalog.

The outputs are deterministic 1080×1350 JPGs suitable for VK/Instagram feeds.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "visualizations" / "fotoprops"
OUT = ROOT / "visualizations" / "fotoprops-ads"
OUT.mkdir(parents=True, exist_ok=True)

W, H = 1080, 1350
NAVY = "#071a2b"
BLUE = "#123d69"
ORANGE = "#ff4d20"
CORAL = "#ff654d"
LIME = "#d8ff38"
IVORY = "#f5f1e9"
WHITE = "#ffffff"
MUTED = "#a8b3c2"
DARK = "#050b12"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def font(size, bold=False):
    return ImageFont.truetype(FONT_B if bold else FONT, size)


def cover(image, size, focal=(0.5, 0.5)):
    """Crop an image to cover a box, preserving a configurable focal point."""
    image = image.convert("RGB")
    tw, th = size
    scale = max(tw / image.width, th / image.height)
    nw, nh = round(image.width * scale), round(image.height * scale)
    image = image.resize((nw, nh), Image.Resampling.LANCZOS)
    left = round((nw - tw) * focal[0])
    top = round((nh - th) * focal[1])
    left = min(max(left, 0), nw - tw)
    top = min(max(top, 0), nh - th)
    return image.crop((left, top, left + tw, top + th))


def crop_region(name, crop_box, size):
    image = Image.open(SRC / name).convert("RGB")
    image = image.crop(crop_box)
    return cover(image, size)


def rounded_panel(canvas, image, box, radius=32, shadow=True, border=None, border_width=0):
    x, y, w, h = box
    image = cover(image, (w, h))
    if shadow:
        sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        sd = ImageDraw.Draw(sh)
        sd.rounded_rectangle((x + 10, y + 18, x + w + 10, y + h + 18), radius=radius,
                             fill=(0, 0, 0, 100))
        sh = sh.filter(ImageFilter.GaussianBlur(18))
        canvas.alpha_composite(sh)
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w, h), radius=radius, fill=255)
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    layer.paste(image.convert("RGBA"), (x, y), mask)
    canvas.alpha_composite(layer)
    if border and border_width:
        ImageDraw.Draw(canvas).rounded_rectangle((x, y, x + w, y + h), radius=radius,
                                                  outline=border, width=border_width)


def linear_gradient(size, top_color, bottom_color):
    from PIL import ImageColor
    tr, tg, tb = ImageColor.getrgb(top_color)
    br, bg, bb = ImageColor.getrgb(bottom_color)
    grad = Image.new("RGB", size)
    d = ImageDraw.Draw(grad)
    for y in range(size[1]):
        t = y / max(size[1] - 1, 1)
        d.line((0, y, size[0], y), fill=(round(tr + (br - tr) * t),
                                         round(tg + (bg - tg) * t),
                                         round(tb + (bb - tb) * t)))
    return grad


def add_brand(draw, x=55, y=48, dark=True):
    fill = NAVY if not dark else (5, 14, 24, 210)
    outline = NAVY if not dark else (255, 255, 255, 105)
    draw.rounded_rectangle((x, y, x + 365, y + 60), radius=30, fill=fill, outline=outline, width=2)
    draw.ellipse((x + 20, y + 23, x + 34, y + 37), fill=LIME)
    draw.text((x + 49, y + 16), "SM PRODUCTION", font=font(21, True), fill=WHITE)
    draw.text((x + 264, y + 20), "• ПРОПСЫ", font=font(14, True), fill=ORANGE)


def footer(draw, y, light=False, cta="РАССЧИТАТЬ СТОИМОСТЬ"):
    text_color = NAVY if light else WHITE
    draw.rounded_rectangle((55, y, 550, y + 72), radius=36, fill=ORANGE)
    draw.text((86, y + 21), cta, font=font(22, True), fill=WHITE)
    draw.text((585, y + 4), "+7 (495) 799-00-19", font=font(24, True), fill=text_color)
    draw.text((585, y + 41), "sm-production.ru", font=font(19), fill=BLUE if light else MUTED)


def save(canvas, name):
    canvas.convert("RGB").save(OUT / name, quality=94, subsampling=0, optimize=True)


def ad_01():
    c = Image.new("RGBA", (W, H), NAVY)
    d = ImageDraw.Draw(c, "RGBA")
    # Architectural campaign background.
    d.ellipse((690, -190, 1240, 360), fill=(255, 77, 32, 38))
    d.ellipse((-260, 920, 380, 1560), fill=NAVY, outline=LIME, width=3)
    for x in range(720, 1120, 42):
        d.line((x, 0, x - 270, 430), fill=(255, 255, 255, 15), width=2)
    add_brand(d)
    d.text((58, 153), "ФОТОПРОПСЫ,", font=font(69, True), fill=WHITE)
    d.text((58, 231), "КОТОРЫЕ", font=font(69, True), fill=WHITE)
    d.text((58, 309), "РАБОТАЮТ НА БРЕНД", font=font(52, True), fill=ORANGE)
    d.text((60, 390), "Дизайн  •  печать  •  производство", font=font(25), fill=MUTED)

    image = Image.open(SRC / "sm-fp4-variety-collection.jpg")
    rounded_panel(c, image, (55, 474, 970, 570), radius=38, border=(255, 255, 255, 65), border_width=2)
    d = ImageDraw.Draw(c, "RGBA")
    d.rounded_rectangle((77, 988, 520, 1028), radius=20, fill=(7, 26, 43, 225))
    d.text((99, 996), "ПОД ВАШ ЛОГОТИП И БРЕНДБУК", font=font(17, True), fill=WHITE)
    d.text((58, 1092), "От одного пропса до полной фотозоны", font=font(29, True), fill=WHITE)
    d.text((58, 1137), "Смета и макет — за один рабочий час", font=font(22), fill=MUTED)
    footer(d, 1220)
    save(c, "sm-ad-01-brand.jpg")


def ad_02():
    c = Image.new("RGBA", (W, H), NAVY)
    image = Image.open(SRC / "sm-fp2-bubbles-handheld.jpg")
    c.paste(cover(image, (1080, 720), focal=(0.5, 0.46)).convert("RGBA"), (0, 0))
    # Darken the top edge so the logo is always legible.
    overlay = Image.new("RGBA", (W, 250), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for y in range(250):
        od.line((0, y, W, y), fill=(5, 12, 20, round(170 * (1 - y / 250))))
    c.alpha_composite(overlay, (0, 0))
    d = ImageDraw.Draw(c, "RGBA")
    d.polygon(((0, 665), (1080, 610), (1080, 755), (0, 755)), fill=ORANGE)
    add_brand(d)
    d.text((58, 773), "ВАШ БРЕНД", font=font(73, True), fill=WHITE)
    d.text((58, 854), "ХОЧЕТСЯ", font=font(73, True), fill=WHITE)
    d.text((58, 935), "ФОТОГРАФИРОВАТЬ", font=font(48, True), fill=LIME)
    d.text((61, 1019), "Фразы, формы и цвета — специально под событие", font=font(24), fill=MUTED)
    # Three proof points.
    labels = (("ПВХ 3–12 ММ", 58), ("ПЕЧАТЬ 1440 DPI", 360), ("ОТ 1–2 ДНЕЙ", 730))
    for label, x in labels:
        tw = d.textbbox((0, 0), label, font=font(17, True))[2]
        d.rounded_rectangle((x, 1081, x + tw + 34, 1127), radius=23, fill=BLUE,
                            outline=WHITE, width=1)
        d.text((x + 17, 1093), label, font=font(17, True), fill=WHITE)
    footer(d, 1217)
    save(c, "sm-ad-02-photo.jpg")


def ad_03():
    c = Image.new("RGBA", (W, H), IVORY)
    d = ImageDraw.Draw(c, "RGBA")
    d.rectangle((0, 0, 22, H), fill=ORANGE)
    d.ellipse((805, -80, 1160, 275), fill=(255, 77, 32, 35))
    add_brand(d, dark=False)
    d.text((58, 150), "ОТКРЫТИЕ", font=font(78, True), fill=NAVY)
    d.text((58, 236), "НАЧИНАЕТСЯ", font=font(64, True), fill=NAVY)
    d.text((58, 310), "С БОЛЬШОГО КЛЮЧА", font=font(49, True), fill=ORANGE)
    d.text((61, 389), "Церемониальный реквизит под фирменный стиль", font=font(23), fill=BLUE)

    image = crop_region("sm-fp3-giant-key-pvc.jpg", (75, 145, 1150, 662), (970, 555))
    rounded_panel(c, image, (55, 465, 970, 555), radius=38, border=(7, 26, 43, 55), border_width=2)
    d = ImageDraw.Draw(c, "RGBA")
    d.rounded_rectangle((76, 487, 421, 535), radius=24, fill=ORANGE)
    d.text((97, 499), "ПОД ЛОГОТИП ЗАКАЗЧИКА", font=font(17, True), fill=WHITE)
    d.text((58, 1068), "Ключи  •  кубки  •  медали  •  рамки", font=font(29, True), fill=NAVY)
    d.text((58, 1112), "Для открытий, награждений и презентаций", font=font(22), fill=BLUE)
    footer(d, 1215, light=True)
    save(c, "sm-ad-03-corporate.jpg")


def ad_04():
    c = Image.new("RGBA", (W, H), IVORY)
    image = Image.open(SRC / "sm-fp2-face-props.jpg")
    c.paste(cover(image, (1080, 735), focal=(0.5, 0.5)).convert("RGBA"), (0, 0))
    d = ImageDraw.Draw(c, "RGBA")
    d.rectangle((0, 690, W, 735), fill=CORAL)
    d.polygon(((0, 735), (1080, 675), (1080, 780), (0, 810)), fill=IVORY)
    add_brand(d)
    d.text((58, 806), "ЭМОЦИИ", font=font(78, True), fill=NAVY)
    d.text((58, 892), "НАЧИНАЮТСЯ", font=font(67, True), fill=NAVY)
    d.text((58, 970), "С РЕКВИЗИТА", font=font(67, True), fill=ORANGE)
    d.text((61, 1058), "Свадьбы  •  корпоративы  •  фестивали  •  промо", font=font(22), fill=BLUE)
    d.rounded_rectangle((58, 1104, 740, 1153), radius=24, fill=NAVY)
    d.text((80, 1116), "ЛЁГКИЙ ПВХ · БЕЗОПАСНЫЕ КРАЯ · ЯРКАЯ ПЕЧАТЬ", font=font(16, True), fill=WHITE)
    footer(d, 1214, light=True)
    save(c, "sm-ad-04-emotions.jpg")


def ad_05():
    c = linear_gradient((W, H), "#071a2b", "#0d2e4e").convert("RGBA")
    d = ImageDraw.Draw(c, "RGBA")
    d.ellipse((790, -235, 1350, 325), fill=ORANGE, outline=WHITE, width=2)
    add_brand(d)
    d.text((58, 149), "ВАШ НАБОР", font=font(76, True), fill=WHITE)
    d.text((58, 236), "ЗА 1–2 ДНЯ", font=font(76, True), fill=LIME)
    d.text((61, 334), "От идеи до готовых фотопропсов на мероприятии", font=font(23), fill=MUTED)

    items = [
        ("sm-fp5-croissant-pvc.jpg", "КРУАССАН"),
        ("sm-fp5-coffee-cup-pvc.jpg", "КОФЕ С БРЕНДИНГОМ"),
        ("sm-fp5-glasses-pvc.jpg", "ОЧКИ"),
        ("sm-fp5-lips-pvc.jpg", "ГУБЫ"),
    ]
    boxes = [(55, 415, 470, 300), (555, 415, 470, 300), (55, 745, 470, 300), (555, 745, 470, 300)]
    for (name, label), box in zip(items, boxes):
        source = Image.open(SRC / name).crop((0, 165, 1200, 672))
        rounded_panel(c, source, box, radius=30, shadow=True, border=(255, 255, 255, 48), border_width=1)
        d = ImageDraw.Draw(c, "RGBA")
        x, y, w, h = box
        tw = d.textbbox((0, 0), label, font=font(16, True))[2]
        d.rounded_rectangle((x + 18, y + h - 52, x + 44 + tw, y + h - 14), radius=19,
                            fill=(7, 26, 43, 225))
        d.text((x + 31, y + h - 43), label, font=font(16, True), fill=WHITE)

    d = ImageDraw.Draw(c, "RGBA")
    d.text((58, 1091), "ОТ 1 ШТУКИ  •  ПО ВАШЕМУ МАКЕТУ", font=font(27, True), fill=WHITE)
    d.text((58, 1137), "Поможем с формой, конструкцией и печатью", font=font(22), fill=MUTED)
    footer(d, 1217, cta="ЗАКАЗАТЬ МАКЕТ")
    save(c, "sm-ad-05-fast-set.jpg")


def main():
    ad_01()
    ad_02()
    ad_03()
    ad_04()
    ad_05()
    for path in sorted(OUT.glob("sm-ad-*.jpg")):
        print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
