#!/usr/bin/env python3
"""Render a geographically accurate 1080×1920 Russia video insert.

The country outline is based on Natural Earth 1:50m data and rendered with an
equidistant cylindrical projection whose true-scale parallel runs through
Russia. This gives a familiar, geographically grounded silhouette rather than
an AI-drawn approximation.
"""

from pathlib import Path
import json
import math
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
MAP_DATA = ROOT / "assets" / "data" / "russia-natural-earth-50m.geojson"
OUT = ROOT / "visualizations" / "video" / "kaliningrad-vladivostok-vertical.jpg"

W, H, SS = 1080, 1920, 2
CW, CH = W * SS, H * SS
NAVY = (5, 17, 29)
ORANGE = (255, 78, 37)
LIME = (216, 255, 56)
WHITE = (247, 250, 253)
MUTED = (172, 187, 202)
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# Projection and layout parameters. At 58°N, one degree of longitude is
# multiplied by cos(58°), preserving a realistic Russia-wide aspect ratio.
CENTRAL_MERIDIAN = 100.0
STANDARD_PARALLEL = math.radians(58.0)
MAP_BOX = (55, 680, 1025, 1245)


def sc(value):
    return round(value * SS)


def font(size, bold=False):
    return ImageFont.truetype(FONT_B if bold else FONT, sc(size))


def project_raw(lon, lat):
    """Equidistant cylindrical projection, unwrapped around Russia."""
    delta = (lon - CENTRAL_MERIDIAN + 180.0) % 360.0 - 180.0
    x = math.radians(delta) * math.cos(STANDARD_PARALLEL)
    y = math.radians(lat)
    return x, y


def load_geometry():
    feature = json.loads(MAP_DATA.read_text())
    return feature["geometry"]["coordinates"]


def make_mapper(geometry):
    raw = [project_raw(*point) for polygon in geometry for ring in polygon for point in ring]
    min_x = min(p[0] for p in raw)
    max_x = max(p[0] for p in raw)
    min_y = min(p[1] for p in raw)
    max_y = max(p[1] for p in raw)
    left, top, right, bottom = MAP_BOX
    scale = min((right - left) / (max_x - min_x), (bottom - top) / (max_y - min_y))
    used_w = (max_x - min_x) * scale
    used_h = (max_y - min_y) * scale
    ox = left + ((right - left) - used_w) / 2 - min_x * scale
    oy = top + ((bottom - top) - used_h) / 2 + max_y * scale

    def mapper(lon, lat):
        x, y = project_raw(lon, lat)
        return sc(ox + x * scale), sc(oy - y * scale)

    return mapper


def draw_background():
    image = Image.new("RGB", (CW, CH))
    pixels = image.load()
    # Deep blue vertical gradient with a subtle warm horizon.
    for y in range(CH):
        t = y / (CH - 1)
        horizon = math.exp(-((t - 0.50) / 0.19) ** 2)
        r = round(5 - 2 * t + 4 * horizon)
        g = round(18 - 8 * t + 11 * horizon)
        b = round(31 - 13 * t + 18 * horizon)
        for x in range(CW):
            pixels[x, y] = (r, g, b)

    # Cinematic aurora, intentionally restrained behind the title and map.
    aurora = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    ad = ImageDraw.Draw(aurora, "RGBA")
    ribbons = [
        ([(70, 480), (310, 430), (545, 500), (785, 410), (1060, 485)], (44, 196, 173, 50), 64),
        ([(20, 555), (260, 500), (510, 555), (770, 485), (1080, 530)], (65, 124, 205, 36), 42),
    ]
    for points, color, width in ribbons:
        ad.line([(sc(x), sc(y)) for x, y in points], fill=color, width=sc(width), joint="curve")
    aurora = aurora.filter(ImageFilter.GaussianBlur(sc(58)))
    image = Image.alpha_composite(image.convert("RGBA"), aurora)

    # Fine atmospheric particles, deterministic for reproducibility.
    stars = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    sd = ImageDraw.Draw(stars, "RGBA")
    rng = random.Random(789)
    for _ in range(270):
        x, y = rng.randrange(CW), rng.randrange(sc(430), sc(1450))
        r = rng.choice([1, 1, 1, 2]) * SS
        alpha = rng.randrange(18, 68)
        sd.ellipse((x - r, y - r, x + r, y + r), fill=(190, 220, 235, alpha))
    return Image.alpha_composite(image, stars)


def map_mask_and_rings(geometry, mapper):
    mask = Image.new("L", (CW, CH), 0)
    md = ImageDraw.Draw(mask)
    rings = []
    for polygon in geometry:
        outer = [mapper(*point) for point in polygon[0]]
        if len(outer) >= 3:
            md.polygon(outer, fill=255)
            rings.append(outer)
        for hole in polygon[1:]:
            inner = [mapper(*point) for point in hole]
            if len(inner) >= 3:
                md.polygon(inner, fill=0)
                rings.append(inner)
    return mask, rings


def paint_map(image, geometry, mapper):
    mask, rings = map_mask_and_rings(geometry, mapper)

    # Wide amber light behind the actual coastline.
    glow = Image.new("RGBA", (CW, CH), (255, 93, 36, 0))
    glow.putalpha(mask.filter(ImageFilter.GaussianBlur(sc(24))).point(lambda v: min(92, v)))
    image = Image.alpha_composite(image, glow)

    # Blue-steel land fill with gentle vertical depth.
    land = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    ld = ImageDraw.Draw(land)
    for y in range(sc(MAP_BOX[1] - 20), sc(MAP_BOX[3] + 20)):
        t = (y / SS - MAP_BOX[1]) / (MAP_BOX[3] - MAP_BOX[1])
        ld.line((0, y, CW, y), fill=(18 + round(8 * t), 43 + round(10 * t), 60 + round(12 * t), 248))
    land.putalpha(mask)
    image = Image.alpha_composite(image, land)

    # Low-frequency terrain texture clipped exactly to the true outline.
    terrain = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    td = ImageDraw.Draw(terrain, "RGBA")
    rng = random.Random(643)
    for _ in range(95):
        x = rng.randrange(sc(35), sc(1045))
        y = rng.randrange(sc(675), sc(1255))
        rx, ry = rng.randrange(sc(22), sc(95)), rng.randrange(sc(10), sc(42))
        color = rng.choice([(97, 151, 157, 26), (221, 134, 76, 18), (79, 112, 150, 25)])
        td.ellipse((x - rx, y - ry, x + rx, y + ry), fill=color)
    terrain = terrain.filter(ImageFilter.GaussianBlur(sc(20)))
    terrain.putalpha(Image.composite(terrain.getchannel("A"), Image.new("L", (CW, CH), 0), mask))
    image = Image.alpha_composite(image, terrain)

    # Geographic graticule, clipped to the silhouette.
    grid = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grid, "RGBA")
    for lat in range(45, 81, 10):
        pts = [mapper(lon, lat) for lon in range(20, 191, 2)]
        gd.line(pts, fill=(168, 205, 215, 22), width=sc(1))
    for lon in range(30, 191, 20):
        pts = [mapper(lon, lat) for lat in range(42, 83)]
        gd.line(pts, fill=(168, 205, 215, 18), width=sc(1))
    grid.putalpha(Image.composite(grid.getchannel("A"), Image.new("L", (CW, CH), 0), mask))
    image = Image.alpha_composite(image, grid)

    # Crisp coastline and a small outer glow.
    coast_glow = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    cgd = ImageDraw.Draw(coast_glow, "RGBA")
    for ring in rings:
        cgd.line(ring, fill=(255, 108, 54, 115), width=sc(5), joint="curve")
    coast_glow = coast_glow.filter(ImageFilter.GaussianBlur(sc(6)))
    image = Image.alpha_composite(image, coast_glow)

    coast = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    cd = ImageDraw.Draw(coast, "RGBA")
    for ring in rings:
        cd.line(ring, fill=(255, 179, 112, 238), width=sc(1.8), joint="curve")
    return Image.alpha_composite(image, coast)


def great_circle(start, end, count=90):
    def vector(lon, lat):
        lon, lat = math.radians(lon), math.radians(lat)
        return (math.cos(lat) * math.cos(lon), math.cos(lat) * math.sin(lon), math.sin(lat))

    a, b = vector(*start), vector(*end)
    omega = math.acos(max(-1.0, min(1.0, sum(x * y for x, y in zip(a, b)))))
    result = []
    for i in range(count):
        t = i / (count - 1)
        s = math.sin(omega)
        v = tuple((math.sin((1 - t) * omega) * a[j] + math.sin(t * omega) * b[j]) / s for j in range(3))
        lon = math.degrees(math.atan2(v[1], v[0]))
        lat = math.degrees(math.atan2(v[2], math.hypot(v[0], v[1])))
        result.append((lon, lat))
    return result


def draw_route(image, mapper):
    kaliningrad = (20.4522, 54.7104)
    vladivostok = (131.8855, 43.1155)
    route = [mapper(*point) for point in great_circle(kaliningrad, vladivostok)]

    glow = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow, "RGBA")
    gd.line(route, fill=(255, 73, 26, 220), width=sc(17), joint="curve")
    glow = glow.filter(ImageFilter.GaussianBlur(sc(13)))
    image = Image.alpha_composite(image, glow)

    layer = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer, "RGBA")
    d.line(route, fill=ORANGE + (255,), width=sc(4), joint="curve")
    d.line(route, fill=(255, 220, 164, 235), width=sc(1), joint="curve")
    for point in (route[0], route[-1]):
        x, y = point
        d.ellipse((x - sc(17), y - sc(17), x + sc(17), y + sc(17)), fill=(255, 81, 32, 54))
        d.ellipse((x - sc(9), y - sc(9), x + sc(9), y + sc(9)), fill=(255, 248, 215, 255), outline=ORANGE + (255,), width=sc(3))
    return Image.alpha_composite(image, layer), route[0], route[-1]


def center_text(draw, y, text, text_font, fill, stroke=0):
    box = draw.textbbox((0, 0), text, font=text_font, stroke_width=sc(stroke))
    width = box[2] - box[0]
    draw.text(((CW - width) / 2, sc(y)), text, font=text_font, fill=fill,
              stroke_width=sc(stroke), stroke_fill=NAVY + (255,))


def city_tag(draw, point, text, side):
    x, y = point
    f = font(20, True)
    box = draw.textbbox((0, 0), text, font=f)
    tw = box[2] - box[0]
    w, h = tw + sc(34), sc(49)
    if side == "left":
        tx = max(sc(42), x - sc(4))
        ty = y + sc(25)
    else:
        tx = min(sc(1038) - w, x - w + sc(8))
        ty = y + sc(26)
    draw.rounded_rectangle((tx, ty, tx + w, ty + h), radius=sc(24),
                           fill=(4, 17, 29, 232), outline=ORANGE + (255,), width=sc(1.5))
    draw.text((tx + sc(17), ty + sc(12)), text, font=f, fill=WHITE + (255,))


def add_typography(image, west, east):
    layer = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer, "RGBA")

    # Brand capsule, with clear spacing and no generated lettering.
    d.rounded_rectangle((sc(64), sc(62), sc(408), sc(128)), radius=sc(33),
                        fill=(3, 12, 22, 224), outline=(255, 255, 255, 120), width=sc(1.5))
    d.ellipse((sc(87), sc(87), sc(103), sc(103)), fill=LIME + (255,))
    d.text((sc(121), sc(79)), "SM PRODUCTION", font=font(23, True), fill=WHITE + (255,))

    center_text(d, 196, "ОТ КАЛИНИНГРАДА", font(65, True), WHITE + (255,), stroke=1)
    center_text(d, 280, "ДО ВЛАДИВОСТОКА", font(65, True), ORANGE + (255,), stroke=1)
    center_text(d, 384, "ПРОЕКТЫ ПО ВСЕЙ РОССИИ", font(27, True), MUTED + (255,))

    city_tag(d, west, "КАЛИНИНГРАД", "left")
    city_tag(d, east, "ВЛАДИВОСТОК", "right")

    d.line((sc(64), sc(1587), sc(214), sc(1587)), fill=ORANGE + (255,), width=sc(7))
    d.text((sc(64), sc(1623)), "ПРОИЗВОДСТВО", font=font(38, True), fill=WHITE + (255,))
    d.text((sc(64), sc(1680)), "ДОСТАВКА  •  МОНТАЖ", font=font(38, True), fill=WHITE + (255,))
    d.text((sc(64), sc(1772)), "sm-production.ru", font=font(26), fill=MUTED + (255,))
    return Image.alpha_composite(image, layer)


def main():
    geometry = load_geometry()
    mapper = make_mapper(geometry)
    image = draw_background()
    image = paint_map(image, geometry, mapper)
    image, west, east = draw_route(image, mapper)
    image = add_typography(image, west, east)
    image = image.convert("RGB").resize((W, H), Image.Resampling.LANCZOS)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    image.save(OUT, quality=95, subsampling=0, optimize=True)
    print(OUT)


if __name__ == "__main__":
    main()
