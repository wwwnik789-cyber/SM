#!/usr/bin/env python3
"""Плашка TSUM для наложения на белое поле в сцене.

Рамка не рисуется — она уже есть на сцене. Логотип рисуется на отдельном слое,
обрезается по фактическим границам штрихов и центрируется, поэтому оптический
центр совпадает с геометрическим (у «Ц» есть выносной хвост).
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
FONT = Path("/home/user/SM/banners/anikom-arena-3000x2500-concepts/source/Montserrat-Variable.ttf")
OUT = HERE / "assets"
W, H = 1200, 600
FILL = 0.74          # доля ширины плашки под логотип


def tracked(draw: ImageDraw.ImageDraw, text: str, font, center_x: float,
            y: float, track: float, fill) -> None:
    widths = [draw.textlength(ch, font=font) for ch in text]
    total = sum(widths) + track * (len(text) - 1)
    x = center_x - total / 2
    for ch, w_ in zip(text, widths):
        draw.text((x, y), ch, font=font, fill=fill)
        x += w_ + track


def build() -> Image.Image:
    cw, ch = 2400, 1200
    layer = Image.new("L", (cw, ch), 0)
    d = ImageDraw.Draw(layer)

    big = ImageFont.truetype(str(FONT), 470)
    big.set_variation_by_name("Medium")
    small = ImageFont.truetype(str(FONT), 108)
    small.set_variation_by_name("Medium")

    tracked(d, "ЦУМ", big, cw / 2, 250, 60, 255)
    tracked(d, "TSUM MOSCOW", small, cw / 2, 830, 32, 255)

    bbox = layer.getbbox()
    glyphs = layer.crop(bbox)

    target_w = int(W * FILL)
    scale = target_w / glyphs.width
    glyphs = glyphs.resize((target_w, int(glyphs.height * scale)), Image.LANCZOS)

    plate = Image.new("RGB", (W, H), (255, 255, 255))
    ink = Image.new("RGB", glyphs.size, (26, 22, 19))
    plate.paste(ink, ((W - glyphs.width) // 2, (H - glyphs.height) // 2), glyphs)
    return plate


def main() -> None:
    OUT.mkdir(exist_ok=True)
    plaque = build()
    plaque.save(OUT / "plaque-tsum.png")
    print(f"  {OUT / 'plaque-tsum.png'}: {plaque.size}")


if __name__ == "__main__":
    main()
