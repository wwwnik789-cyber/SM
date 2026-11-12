#!/usr/bin/env python3
"""Фотореалистичные сцены применения снежинок из ПВХ.

Берём контуры из production/new-year-snowflakes (тот же сборщик, что делает
файлы для фрезера) и «ставим» их в интерьерные фото: фотозона, холл офиса,
участок ЧПУ. Это визуализации возможного оформления, а не фото готовых работ.

Запуск из корня репозитория:
    .venv/bin/python visualizations/pvh-snowflakes-cut/build_scenes.py
"""

from __future__ import annotations

import sys
from io import BytesIO
from math import radians
from pathlib import Path

import numpy as np
import resvg_py
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from shapely import affinity
from shapely.geometry import Polygon

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "production/new-year-snowflakes"))
import build_snowflakes as S  # noqa: E402

OUT = Path(__file__).resolve().parent
W, H = 1200, 675


# ── геометрия: контур снежинки → маска ───────────────────────────────────────

def poly_path(poly: Polygon, height: float) -> str:
    parts = [S.ring_path(poly.exterior.coords, height)]
    parts += [S.ring_path(ring.coords, height) for ring in poly.interiors]
    return " ".join(parts)


def render_mask(poly: Polygon, px: int) -> Image.Image:
    """Белая заливка контура на прозрачном фоне, ширина px."""
    min_x, min_y, max_x, max_y = poly.bounds
    w, h = max_x - min_x, max_y - min_y
    shifted = affinity.translate(poly, -min_x, -min_y)
    path = poly_path(shifted, h)
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.2f}" height="{h:.2f}" '
        f'viewBox="0 0 {w:.2f} {h:.2f}">'
        f'<path d="{path}" fill="#ffffff" fill-rule="evenodd"/></svg>'
    )
    png = bytes(resvg_py.svg_to_bytes(svg_string=svg, width=px))
    return Image.open(BytesIO(png)).convert("L")


def material(alpha: Image.Image, tint=(247, 245, 239), light=1.0,
             edge: float = 0.10) -> Image.Image:
    """Деталь из ПВХ: ровная поверхность, скос по кромке, лёгкий шум материала."""
    width, height = alpha.size
    rng = np.random.default_rng(7)
    noise = rng.normal(0, 1.6, (height, width)).astype(np.float32)

    base = np.zeros((height, width, 3), np.float32)
    vertical = np.linspace(1.02, 0.95, height).astype(np.float32)[:, None]
    for channel, value in enumerate(tint):
        base[..., channel] = value * vertical + noise

    inner = np.asarray(alpha, np.float32) / 255.0
    # скос: у самой кромки деталь темнее, к центру светлее
    eroded = np.asarray(alpha.filter(ImageFilter.MinFilter(7)), np.float32) / 255.0
    rim = np.clip(inner - eroded, 0.0, 1.0)
    rim = np.asarray(Image.fromarray((rim * 255).astype(np.uint8)).filter(
        ImageFilter.GaussianBlur(1.6)), np.float32) / 255.0
    base *= (1.0 - edge * rim[..., None] * light)

    rgb = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8), "RGB")
    out = rgb.convert("RGBA")
    out.putalpha(alpha)
    return out


# ── перспективная вставка ────────────────────────────────────────────────────

def homography(dst, src) -> tuple[float, ...]:
    """Коэффициенты PIL PERSPECTIVE: координата выхода → координата входа."""
    matrix, vector = [], []
    for (x, y), (u, v) in zip(dst, src):
        matrix.append([x, y, 1, 0, 0, 0, -u * x, -u * y])
        matrix.append([0, 0, 0, x, y, 1, -v * x, -v * y])
        vector += [u, v]
    a = np.array(matrix, float)
    b = np.array(vector, float)
    return tuple(np.linalg.solve(a, b))


def shade(sprite: Image.Image, alpha: float) -> Image.Image:
    """Приглушаем деталь: свет на стене не такой яркий, как в центре кадра."""
    rgb = sprite.convert("RGB").point(lambda value: int(value * alpha))
    out = rgb.convert("RGBA")
    out.putalpha(sprite.getchannel("A"))
    return out


def place(scene: Image.Image, sprite: Image.Image, quad,
          shadow=(0.34, 5, 9), strings=None) -> None:
    """Кладём деталь в четырёхугольник сцены: тень под ней и мягкий контакт."""
    canvas = scene.convert("RGBA")
    w, h = sprite.size
    coeffs = homography(quad, [(0, 0), (w, 0), (w, h), (0, h)])
    warped = sprite.transform(canvas.size, Image.PERSPECTIVE, coeffs, Image.BICUBIC)
    alpha = warped.getchannel("A")

    if shadow:
        opacity, offset, blur = shadow
        soft = alpha.filter(ImageFilter.GaussianBlur(blur))
        # тень темнее у детали и рассеивается к краю
        spread = alpha.filter(ImageFilter.GaussianBlur(blur * 2.2))
        strength = np.asarray(soft, np.float32) / 255.0
        halo = np.asarray(spread, np.float32) / 255.0
        weight = np.clip(strength * 0.75 + halo * 0.4, 0, 1) * opacity
        shadow_layer = Image.new("RGBA", canvas.size, (26, 22, 18, 255))
        shadow_layer.putalpha(Image.fromarray((weight * 255).astype(np.uint8)))
        moved = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        moved.paste(shadow_layer, (offset, offset))
        canvas = Image.alpha_composite(canvas, moved)

    if strings:
        draw = ImageDraw.Draw(canvas)
        for (x1, y1), (x2, y2) in strings:
            draw.line([(x1, y1), (x2, y2)], fill=(232, 230, 224, 190), width=1)

    canvas = Image.alpha_composite(canvas, warped)
    scene.paste(canvas.convert("RGB"))


def load_scene(path: Path) -> Image.Image:
    image = Image.open(REPO / path).convert("RGB")
    ratio = W / H
    src_ratio = image.width / image.height
    if src_ratio > ratio:
        new_w = int(image.height * ratio)
        left = (image.width - new_w) // 2
        image = image.crop((left, 0, left + new_w, image.height))
    else:
        new_h = int(image.width / ratio)
        top = (image.height - new_h) // 2
        image = image.crop((0, top, image.width, top + new_h))
    return image.resize((W, H), Image.LANCZOS)


def sprite(poly: Polygon, px: int, tint=(250, 249, 246), edge: float = 0.10) -> Image.Image:
    return material(render_mask(poly, px), tint, edge=edge)


def quad(cx: float, cy: float, w: float, h: float, tilt: float = 0.0, yaw: float = 0.0):
    """Прямоугольник на стене: tilt — наклон стены, yaw — уход плоскости вглубь."""
    hw, hh = w / 2, h / 2
    left_h = hh * (1 - yaw)
    right_h = hh * (1 + yaw)
    return [
        (cx - hw, cy - left_h + tilt),
        (cx + hw, cy - right_h + tilt),
        (cx + hw, cy + right_h + tilt),
        (cx - hw, cy + left_h + tilt),
    ]


# ── сцены ────────────────────────────────────────────────────────────────────

def scene_photozone() -> None:
    """Фотозона: снежинки на свободной части стены в палитре проекта."""
    base = load_scene(Path("marketing/novogodnee-oformlenie-2027/creatives/source/photozone.jpg"))

    white = (255, 252, 243)
    navy = (24, 44, 66)
    coral = (214, 88, 74)

    big_white = shade(sprite(S.build_classic(175.0), 1000, tint=white, edge=0.14), 0.96)
    big_navy = shade(sprite(S.build_star(175.0), 1000, tint=navy, edge=0.30), 0.92)
    big_coral = shade(sprite(S.build_crystal(175.0), 1000, tint=coral, edge=0.26), 0.94)
    s_white = shade(sprite(S.build_star(175.0), 520, tint=white, edge=0.14), 0.90)
    s_navy = shade(sprite(S.build_classic(175.0), 520, tint=navy, edge=0.30), 0.90)
    s_coral = shade(sprite(S.build_crystal(175.0), 520, tint=coral, edge=0.26), 0.90)

    # стена в кадре: x 167…875, y 54…606. Декор заказчика начинается с x≈610
    # стена: x 168…878, y 52…560 — всё держим внутри, с полем 10 мм от кромки
    place(base, big_white, quad(296, 250, 258, 224), shadow=(0.34, 4, 8))
    place(base, big_navy, quad(465, 154, 170, 170), shadow=(0.30, 4, 7))
    place(base, big_coral, quad(286, 450, 232, 188), shadow=(0.34, 4, 8))
    place(base, s_coral, quad(476, 318, 104, 104), shadow=(0.28, 3, 6))
    place(base, s_white, quad(488, 470, 112, 96), shadow=(0.26, 3, 6))

    base.save(OUT / "01-photozone-wall.jpg", quality=90, optimize=True)


def scene_office() -> None:
    """Холл офиса: подвес из снежинок на лесках к потолку."""
    base = load_scene(Path("marketing/novogodnee-oformlenie-2027/creatives/source/lobby.jpg"))

    star = shade(sprite(S.build_star(175.0), 900, tint=(255, 253, 245), edge=0.16), 0.97)
    classic = shade(sprite(S.build_classic(175.0), 900, tint=(255, 253, 245), edge=0.16), 0.96)
    crystal = shade(sprite(S.build_crystal(175.0), 900, tint=(255, 253, 245), edge=0.16), 0.96)

    hang = [
        (star, quad(196, 300, 170, 170), 196, 92),
        (classic, quad(372, 208, 180, 158), 372, 88),
        (crystal, quad(492, 312, 128, 112), 492, 96),
    ]
    for art, box, anchor_x, anchor_y in hang:
        strings = [((anchor_x, anchor_y), (anchor_x, box[0][1]))]
        place(base, art, box, shadow=(0.26, 4, 9), strings=strings)

    base.save(OUT / "02-office-lobby.jpg", quality=90, optimize=True)


def scene_workshop() -> None:
    """Участок: вырезанная деталь лежит на столе у фрезера."""
    base = load_scene(Path("public/media/workshop.jpg"))
    detail = shade(sprite(S.build_star(175.0), 1400, tint=(247, 243, 232), edge=0.16), 0.86)
    place(base, detail, [(0, 468), (395, 495), (372, 660), (-30, 648)], shadow=(0.30, 5, 9))
    base.save(OUT / "03-workshop-detail.jpg", quality=90, optimize=True)


def scene_showroom() -> None:
    """Автосалон: подвесные снежинки над машиной и декор на бренд-стене."""
    base = load_scene(Path("marketing/site-hero/source/candidate-b-showroom-brandwall.jpg"))

    navy = (20, 40, 62)
    white = (250, 248, 242)

    big = shade(sprite(S.build_star(175.0), 950, tint=navy, edge=0.30), 0.90)
    mid = shade(sprite(S.build_classic(175.0), 900, tint=white, edge=0.16), 0.92)
    small = shade(sprite(S.build_crystal(175.0), 800, tint=navy, edge=0.30), 0.88)

    # подвес в верхней части кадра, к сетчатому потолку
    place(base, big, quad(300, 190, 150, 150), shadow=(0.18, 3, 8),
          strings=[((300, 8), (300, 115))])
    place(base, mid, quad(452, 128, 140, 122), shadow=(0.18, 3, 8),
          strings=[((452, 8), (452, 67))])
    place(base, small, quad(568, 214, 122, 108), shadow=(0.16, 3, 7),
          strings=[((568, 8), (568, 160))])

    base.save(OUT / "04-showroom-suspension.jpg", quality=90, optimize=True)


def make_preview() -> None:
    """Лист-превью 2×2 с подписями — для согласования в переписке."""
    names = [
        ("01-photozone-wall.jpg", "Фотозона: снежинки на ПВХ, Ø350–500 мм"),
        ("02-office-lobby.jpg", "Холл офиса: подвес на лесках, Ø350 мм"),
        ("03-workshop-detail.jpg", "Участок: деталь после фрезеровки"),
        ("04-showroom-suspension.jpg", "Автосалон: подвес над экспозицией"),
    ]
    cells = []
    for name, caption in names:
        image = Image.open(OUT / name).convert("RGB").resize((600, 338), Image.LANCZOS)
        cells.append((image, caption))

    gap, pad, caption_h = 16, 20, 34
    cols, rows = 2, 2
    width = pad * 2 + 600 * cols + gap * (cols - 1)
    height = pad * 2 + (338 + caption_h) * rows + gap * (rows - 1)
    sheet = Image.new("RGB", (width, height), "#ffffff")
    draw = ImageDraw.Draw(sheet)
    face = S.font(19, 600) if hasattr(S, "font") else None
    for index, (image, caption) in enumerate(cells):
        x = pad + (index % cols) * (600 + gap)
        y = pad + (index // cols) * (338 + caption_h + gap)
        sheet.paste(image, (x, y))
        if face:
            draw.text((x, y + 338 + 8), caption, font=face, fill="#16283b")
        else:
            draw.text((x, y + 338 + 8), caption, fill="#16283b")
    sheet.save(OUT / "preview.jpg", quality=88, optimize=True)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    scene_photozone()
    scene_office()
    scene_workshop()
    scene_showroom()
    make_preview()
    for name in ("01-photozone-wall.jpg", "02-office-lobby.jpg",
                 "03-workshop-detail.jpg", "04-showroom-suspension.jpg", "preview.jpg"):
        path = OUT / name
        print(f"  {name}: {Image.open(path).size}, {path.stat().st_size / 1024:.0f} КБ")


if __name__ == "__main__":
    main()
