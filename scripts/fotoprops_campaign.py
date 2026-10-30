#!/usr/bin/env python3
"""Generate five minimal 16:9 photorealistic ad creatives for custom photoprops."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "visualizations" / "fotoprops"
OUT = ROOT / "visualizations" / "fotoprops-campaign"
OUT.mkdir(parents=True, exist_ok=True)

W, H = 1200, 675
NAVY = "#071a2b"
BLUE = "#123d69"
ORANGE = "#ff4d20"
LIME = "#d8ff38"
WHITE = "#ffffff"
MUTED = "#c4ccd5"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def font(size, bold=False):
    return ImageFont.truetype(FONT_B if bold else FONT, size)


def cover(image, size=(W, H), focal=(0.5, 0.5)):
    image = image.convert("RGB")
    tw, th = size
    scale = max(tw / image.width, th / image.height)
    nw, nh = round(image.width * scale), round(image.height * scale)
    image = image.resize((nw, nh), Image.Resampling.LANCZOS)
    left = min(max(round((nw - tw) * focal[0]), 0), nw - tw)
    top = min(max(round((nh - th) * focal[1]), 0), nh - th)
    return image.crop((left, top, left + tw, top + th))


def photo(name, focal=(0.5, 0.5), brightness=0.94):
    image = cover(Image.open(SRC / name), focal=focal)
    image = ImageEnhance.Color(image).enhance(0.98)
    image = ImageEnhance.Contrast(image).enhance(1.06)
    image = ImageEnhance.Brightness(image).enhance(brightness)
    return image.convert("RGBA")


def alpha_layer(canvas, painter):
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    painter(ImageDraw.Draw(layer, "RGBA"))
    return Image.alpha_composite(canvas, layer)


def side_gradient(canvas, side="left", strength=235, reach=720):
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    px = layer.load()
    for x in range(W):
        dist = x if side == "left" else W - 1 - x
        alpha = int(strength * max(0, 1 - dist / reach) ** 1.7)
        for y in range(H):
            px[x, y] = (7, 26, 43, alpha)
    return Image.alpha_composite(canvas, layer)


def bottom_gradient(canvas, strength=235, reach=260):
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer, "RGBA")
    for y in range(H - reach, H):
        t = (y - (H - reach)) / reach
        d.line((0, y, W, y), fill=(7, 26, 43, int(strength * t ** 1.4)))
    return Image.alpha_composite(canvas, layer)


def brand(draw, x=42, y=32, inverse=False):
    fill = WHITE if inverse else NAVY
    text = NAVY if inverse else WHITE
    outline = NAVY if inverse else WHITE
    draw.rounded_rectangle((x, y, x + 302, y + 49), radius=25, fill=fill, outline=outline, width=1)
    draw.ellipse((x + 17, y + 18, x + 29, y + 30), fill=LIME)
    draw.text((x + 42, y + 12), "SM PRODUCTION", font=font(18, True), fill=text)
    draw.text((x + 224, y + 15), "• ПРОПСЫ", font=font(12, True), fill=ORANGE)


def signature(draw, x=44, y=620, light=True):
    color = WHITE if light else NAVY
    draw.rectangle((x, y - 10, x + 44, y - 6), fill=ORANGE)
    draw.text((x, y), "ФОТОПРОПСЫ НА ЗАКАЗ", font=font(15, True), fill=color)
    draw.text((x + 240, y), "sm-production.ru", font=font(15), fill=MUTED if light else BLUE)


def save(canvas, filename):
    canvas.convert("RGB").save(OUT / filename, quality=95, subsampling=0, optimize=True)


def creative_01():
    """Words are integrated directly into the three handheld speech bubbles."""
    c = photo("sm-fp-bubbles.jpg", focal=(0.5, 0.47), brightness=0.96)
    c = bottom_gradient(c, strength=225, reach=115)
    d = ImageDraw.Draw(c)
    brand(d)
    bubbles = [
        ((354, 429), "ВАШ", 40, BLUE),
        ((648, 427), "БРЕНД", 39, ORANGE),
        ((958, 429), "В КАДРЕ", 31, BLUE),
    ]
    for (cx, cy), text, size, color in bubbles:
        f = font(size, True)
        box = d.textbbox((0, 0), text, font=f)
        d.text((cx - (box[2] - box[0]) / 2, cy - (box[3] - box[1]) / 2 - 5), text, font=f, fill=color)
    signature(d, y=627)
    save(c, "sm-campaign-01-brand-in-frame.jpg")


def creative_02():
    c = photo("sm-fp-giant-hand.jpg", focal=(0.5, 0.5), brightness=0.88)
    c = side_gradient(c, side="right", strength=240, reach=560)
    d = ImageDraw.Draw(c)
    brand(d)
    d.text((770, 185), "БОЛЬШЕ", font=font(55, True), fill=WHITE)
    d.text((770, 247), "ЭМОЦИЙ", font=font(55, True), fill=ORANGE)
    d.text((770, 309), "В КАДРЕ", font=font(55, True), fill=WHITE)
    d.rectangle((772, 391, 1032, 395), fill=LIME)
    d.text((772, 415), "Реквизит под вашу идею", font=font(21), fill=MUTED)
    signature(d, x=772, y=606)
    save(c, "sm-campaign-02-emotions.jpg")


def creative_03():
    c = photo("sm-fp-instaframe.jpg", focal=(0.52, 0.5), brightness=0.9)
    c = side_gradient(c, side="left", strength=245, reach=565)
    d = ImageDraw.Draw(c)
    brand(d)
    d.text((44, 190), "ВАШ БРЕНД", font=font(53, True), fill=WHITE)
    d.text((44, 250), "В ЦЕНТРЕ", font=font(53, True), fill=WHITE)
    d.text((44, 310), "КАДРА", font=font(53, True), fill=ORANGE)
    d.text((47, 389), "Рамки и формы на заказ", font=font(21), fill=MUTED)
    signature(d, y=606)
    save(c, "sm-campaign-03-brand-focus.jpg")


def creative_04():
    c = photo("sm-fp-giant-cheque.jpg", focal=(0.5, 0.48), brightness=0.9)
    # Compact dark title card preserves the stage and giant cheque.
    def paint(g):
        g.rounded_rectangle((37, 108, 425, 326), radius=26, fill=(7, 26, 43, 228),
                            outline=(255, 255, 255, 70), width=1)
    c = alpha_layer(c, paint)
    c = bottom_gradient(c, strength=215, reach=105)
    d = ImageDraw.Draw(c)
    brand(d)
    d.text((67, 145), "БОЛЬШОЙ", font=font(49, True), fill=WHITE)
    d.text((67, 199), "ФОРМАТ.", font=font(49, True), fill=WHITE)
    d.text((67, 253), "БОЛЬШОЙ ЭФФЕКТ.", font=font(27, True), fill=ORANGE)
    signature(d, y=627)
    save(c, "sm-campaign-04-big-format.jpg")


def creative_05():
    c = photo("sm-fp-tantamareska.jpg", focal=(0.5, 0.5), brightness=0.94)
    c = bottom_gradient(c, strength=245, reach=205)
    d = ImageDraw.Draw(c)
    brand(d)
    d.text((44, 488), "ФОТОЗОНА, КОТОРАЯ ОЖИВАЕТ", font=font(44, True), fill=WHITE)
    d.text((47, 546), "Сюжет и оформление — специально под событие", font=font(20), fill=MUTED)
    signature(d, y=620)
    save(c, "sm-campaign-05-living-photozone.jpg")


def main():
    creative_01()
    creative_02()
    creative_03()
    creative_04()
    creative_05()
    for path in sorted(OUT.glob("sm-campaign-*.jpg")):
        print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
