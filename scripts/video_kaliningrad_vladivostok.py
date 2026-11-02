#!/usr/bin/env python3
"""Build a 1080×1920 video insert: Kaliningrad → Vladivostok."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "visualizations" / "video" / "kaliningrad-vladivostok-clean.jpg"
OUT = ROOT / "visualizations" / "video" / "kaliningrad-vladivostok-vertical.jpg"

W, H = 1080, 1920
NAVY = "#071a2b"
ORANGE = "#ff4d20"
LIME = "#d8ff38"
WHITE = "#ffffff"
MUTED = "#aeb9c7"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def font(size, bold=False):
    return ImageFont.truetype(FONT_B if bold else FONT, size)


def cover(image, size):
    tw, th = size
    scale = max(tw / image.width, th / image.height)
    image = image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS)
    left = (image.width - tw) // 2
    top = (image.height - th) // 2
    return image.crop((left, top, left + tw, top + th))


def gradient_layer(height, top_alpha, bottom_alpha):
    layer = Image.new("RGBA", (W, height), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for y in range(height):
        t = y / max(height - 1, 1)
        alpha = round(top_alpha + (bottom_alpha - top_alpha) * t)
        d.line((0, y, W, y), fill=(7, 26, 43, alpha))
    return layer


def centered(draw, y, text, fnt, fill, stroke=0):
    box = draw.textbbox((0, 0), text, font=fnt, stroke_width=stroke)
    x = (W - (box[2] - box[0])) / 2
    draw.text((x, y), text, font=fnt, fill=fill, stroke_width=stroke, stroke_fill=NAVY)


def city_tag(draw, x, y, text, align="left"):
    fnt = font(22, True)
    box = draw.textbbox((0, 0), text, font=fnt)
    tw = box[2] - box[0]
    pad_x = 20
    width = tw + pad_x * 2
    if align == "right":
        x -= width
    draw.rounded_rectangle((x, y, x + width, y + 54), radius=27,
                           fill=(7, 26, 43, 230), outline=ORANGE, width=2)
    draw.text((x + pad_x, y + 14), text, font=fnt, fill=WHITE)


def main():
    base = cover(Image.open(SOURCE).convert("RGB"), (W, H)).convert("RGBA")

    # Strengthen quiet zones for typography without covering the route.
    base.alpha_composite(gradient_layer(620, 225, 0), (0, 0))
    bottom = gradient_layer(470, 0, 235)
    base.alpha_composite(bottom, (0, H - 470))

    # Very subtle glow behind title.
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((120, 70, 960, 590), fill=(255, 77, 32, 18))
    glow = glow.filter(ImageFilter.GaussianBlur(80))
    base.alpha_composite(glow)

    d = ImageDraw.Draw(base, "RGBA")

    # Brand capsule.
    d.rounded_rectangle((65, 67, 422, 132), radius=33, fill=(5, 14, 24, 220),
                        outline=(255, 255, 255, 105), width=2)
    d.ellipse((88, 93, 104, 109), fill=LIME)
    d.text((122, 83), "SM PRODUCTION", font=font(24, True), fill=WHITE)
    d.text((330, 89), "• РФ", font=font(16, True), fill=ORANGE)

    # Headline.
    centered(d, 202, "ОТ КАЛИНИНГРАДА", font(67, True), WHITE, stroke=2)
    centered(d, 286, "ДО ВЛАДИВОСТОКА", font(67, True), ORANGE, stroke=2)
    centered(d, 390, "ПРОЕКТЫ ПО ВСЕЙ РОССИИ", font(28, True), MUTED)

    # Exact city names adjacent to the route endpoints.
    city_tag(d, 54, 1030, "КАЛИНИНГРАД", "left")
    city_tag(d, 1028, 1262, "ВЛАДИВОСТОК", "right")

    # Footer statement for the final video frame.
    d.line((65, 1618, 215, 1618), fill=ORANGE, width=7)
    d.text((65, 1653), "ПРОИЗВОДСТВО", font=font(38, True), fill=WHITE)
    d.text((65, 1710), "ДОСТАВКА  •  МОНТАЖ", font=font(38, True), fill=WHITE)
    d.text((65, 1795), "sm-production.ru", font=font(26), fill=MUTED)

    base.convert("RGB").save(OUT, quality=95, subsampling=0, optimize=True)
    print(OUT)


if __name__ == "__main__":
    main()
