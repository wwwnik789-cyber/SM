#!/usr/bin/env python3
"""Replace only the printed inserts on the supplied acrylic stands.

The acrylic construction, perspective, showroom and cars remain untouched.
"""

from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path("/tmp/arena-coding-uploads/Акриловые стойки для автосалонов.png")
OUT = ROOT / "visualizations" / "dealer-acrylic-stands"
OUT.mkdir(parents=True, exist_ok=True)

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
SCALE = 2

# Interior areas of the original black inserts. The aluminium frames and screws
# are deliberately left outside these quadrilaterals.
QUADS = [
    [(247, 170), (331, 170), (292, 339), (158, 335)],
    [(419, 179), (534, 178), (493, 368), (301, 363)],
    [(636, 181), (785, 181), (729, 398), (522, 395)],
]

MODELS = [
    {
        "name": "AUTO S7",
        "price": "от 3 490 000 ₽",
        "specs": [("Двигатель", "2.0 Turbo"), ("Мощность", "190 л.с."),
                  ("Коробка", "7DCT"), ("Привод", "передний"),
                  ("Расход", "7,2 л / 100 км")],
        "body": "sedan",
    },
    {
        "name": "AUTO X5",
        "price": "от 4 290 000 ₽",
        "specs": [("Двигатель", "2.0 Turbo"), ("Мощность", "249 л.с."),
                  ("Коробка", "8AT"), ("Привод", "полный"),
                  ("Разгон", "7,8 сек")],
        "body": "suv",
    },
    {
        "name": "AUTO E8",
        "price": "от 5 150 000 ₽",
        "specs": [("Тип", "электромобиль"), ("Мощность", "286 л.с."),
                  ("Запас хода", "520 км"), ("Привод", "задний"),
                  ("Зарядка", "30–80% · 28 мин")],
        "body": "coupe",
    },
]


def font(size, bold=False):
    return ImageFont.truetype(FONT_B if bold else FONT, size)


def car_silhouette(draw, body, color, line):
    if body == "suv":
        pts = [(82, 249), (114, 191), (202, 153), (394, 153), (483, 206),
               (531, 224), (545, 280), (520, 305), (83, 305), (57, 282)]
    elif body == "coupe":
        pts = [(61, 271), (113, 231), (210, 172), (354, 172), (445, 225),
               (525, 245), (544, 282), (514, 305), (83, 305)]
    else:
        pts = [(65, 264), (114, 224), (198, 183), (374, 183), (447, 226),
               (522, 246), (543, 281), (518, 305), (84, 305)]
    draw.line(pts, fill=color, width=10, joint="curve")
    draw.line((105, 307, 497, 307), fill=color, width=8)
    draw.ellipse((117, 272, 184, 339), outline=color, width=12, fill=line)
    draw.ellipse((425, 272, 492, 339), outline=color, width=12, fill=line)
    draw.line((201, 184, 238, 231, 400, 231, 365, 184), fill=color, width=7)


def make_card(model, style):
    w, h = 600, 900
    palettes = {
        "dark": {"bg": "#0b111b", "text": "#f8fbff", "muted": "#aebccc",
                 "accent": "#35d7d2", "line": "#202c3b", "chip": "#142334"},
        "light": {"bg": "#f4f6f8", "text": "#111923", "muted": "#5e6c7b",
                  "accent": "#1569c7", "line": "#d7dde4", "chip": "#e4edf8"},
        "graphite": {"bg": "#17191d", "text": "#ffffff", "muted": "#bec2c9",
                     "accent": "#ff8a2a", "line": "#34383f", "chip": "#24272c"},
    }
    p = palettes[style]
    card = Image.new("RGB", (w, h), p["bg"])
    d = ImageDraw.Draw(card)

    # Header and exact model identification.
    d.rectangle((0, 0, 18, h), fill=p["accent"])
    d.text((48, 37), "AUTO", font=font(31, True), fill=p["accent"])
    d.text((48, 84), model["name"], font=font(57, True), fill=p["text"])
    d.text((48, 155), "ХАРАКТЕРИСТИКИ МОДЕЛИ", font=font(19, True), fill=p["muted"])

    # Vehicle silhouette.
    car_silhouette(d, model["body"], p["accent"], p["bg"])

    # Price band.
    d.rounded_rectangle((47, 355, 553, 439), radius=19, fill=p["chip"])
    d.text((72, 374), model["price"], font=font(34, True), fill=p["text"])

    # Technical table.
    top = 474
    row_h = 72
    for i, (label, value) in enumerate(model["specs"]):
        y = top + i * row_h
        if i:
            d.line((48, y, 552, y), fill=p["line"], width=2)
        d.text((49, y + 18), label.upper(), font=font(18, True), fill=p["muted"])
        vb = d.textbbox((0, 0), value, font=font(22, True))
        d.text((550 - (vb[2] - vb[0]), y + 15), value, font=font(22, True), fill=p["text"])

    d.line((48, 846, 552, 846), fill=p["accent"], width=4)
    d.text((48, 859), "КОМПЛЕКТАЦИЯ · ЦЕНА · ТЕСТ-ДРАЙВ", font=font(17, True), fill=p["muted"])
    return card


def perspective_coeffs(dst_quad, src_size):
    """Coefficients mapping output coordinates to source-card coordinates."""
    sw, sh = src_size
    src = [(0, 0), (sw, 0), (sw, sh), (0, sh)]
    rows, values = [], []
    for (x, y), (u, v) in zip(dst_quad, src):
        rows.append([x, y, 1, 0, 0, 0, -u * x, -u * y])
        values.append(u)
        rows.append([0, 0, 0, x, y, 1, -v * x, -v * y])
        values.append(v)
    return tuple(np.linalg.solve(np.asarray(rows, dtype=float), np.asarray(values, dtype=float)))


def place_card(canvas, card, quad):
    coeffs = perspective_coeffs(quad, card.size)
    warped = card.convert("RGBA").transform(canvas.size, Image.Transform.PERSPECTIVE,
                                              coeffs, Image.Resampling.BICUBIC)
    alpha_source = Image.new("L", card.size, 255)
    alpha = alpha_source.transform(canvas.size, Image.Transform.PERSPECTIVE,
                                   coeffs, Image.Resampling.BICUBIC)
    warped.putalpha(alpha)
    canvas.alpha_composite(warped)


def full_version(style, filename):
    original = Image.open(SOURCE).convert("RGB").resize(
        (896 * SCALE, 1195 * SCALE), Image.Resampling.LANCZOS).convert("RGBA")
    for model, quad in zip(MODELS, QUADS):
        scaled_quad = [(x * SCALE, y * SCALE) for x, y in quad]
        place_card(original, make_card(model, style), scaled_quad)
    original.convert("RGB").save(OUT / filename, quality=95, subsampling=0, optimize=True)


def detail_version():
    """A closer crop of the same untouched stands with dark cards."""
    original = Image.open(SOURCE).convert("RGB").resize(
        (896 * SCALE, 1195 * SCALE), Image.Resampling.LANCZOS).convert("RGBA")
    for model, quad in zip(MODELS, QUADS):
        place_card(original, make_card(model, "dark"), [(x * SCALE, y * SCALE) for x, y in quad])
    # Crop without geometric transformation, retaining all three acrylic constructions.
    crop = original.crop((55 * SCALE, 90 * SCALE, 850 * SCALE, 930 * SCALE))
    crop.convert("RGB").save(OUT / "acrylic-stands-specs-detail.jpg",
                              quality=95, subsampling=0, optimize=True)


def main():
    full_version("dark", "acrylic-stands-specs-dark.jpg")
    full_version("light", "acrylic-stands-specs-light.jpg")
    detail_version()
    for path in sorted(OUT.glob("acrylic-stands-specs-*.jpg")):
        print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
