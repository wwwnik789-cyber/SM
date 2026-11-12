#!/usr/bin/env python3
"""Фотореалистичные сцены применения снежинок из ПВХ.

Контуры берутся из production/new-year-snowflakes — те же полигоны, что уходят
в SVG/DXF для фрезера. Дальше render_pvc.py заливает их с фаской и светом,
считает тень и вставляет в фотографию интерьера.

Главное про масштаб: у каждой сцены задано, сколько миллиметров в пикселе.
Снежинка ставится с реальным диаметром (350, 500, 700 мм), поэтому рядом
с ёлкой, ресепшеном или машиной она выглядит так, как выглядела бы в жизни,
а не как наклейка на треть стены.

Это визуализации возможного оформления, а не фотографии выполненных работ.

Запуск из корня репозитория:
    .venv/bin/python visualizations/pvh-snowflakes-cut/build_scenes.py
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "production/new-year-snowflakes"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_snowflakes as S  # noqa: E402
import render_pvc as R  # noqa: E402

OUT = Path(__file__).resolve().parent
W, H = 1200, 675

WHITE = (250, 246, 236)
NAVY = (26, 45, 66)
CORAL = (206, 92, 78)
MILK = (244, 239, 228)


@dataclass(frozen=True)
class Flake:
    """Одна деталь в сцене."""

    poly: object
    diameter_mm: float
    center: tuple[float, float]
    tint: tuple[int, int, int]
    rotate: float = 0.0
    yaw: float = 0.0          # уход плоскости вглубь: левый край дальше
    skew: float = 0.0         # лёгкий наклон по вертикали
    blur: float = 0.0
    thickness_mm: float = 3.0          # ПВХ 3 мм
    standoff_mm: float = 0.0           # вынос от стены: 0 — вплотную, 20 — на держателях
    shadow: float = 0.30
    contact: float = 0.45
    edge_line: float = 0.0             # тёмный зазор по кромке, для светлого на светлом
    strings_from: float | None = None   # координата Y потолка для лески
    flat_quad: tuple | None = None      # своя четырёхугольная площадка (стол, пол)


def build(poly_of, diameter_mm: float, center, tint, mm_per_px: float, **kw) -> Flake:
    return Flake(poly=poly_of(diameter_mm / 2), diameter_mm=diameter_mm,
                 center=center, tint=tint, **kw)


def quad_for(flake: Flake, mm_per_px: float):
    """Четырёхугольник под деталь с реальным размером и лёгкой перспективой."""
    poly = flake.poly
    min_x, min_y, max_x, max_y = poly.bounds
    width_px = (max_x - min_x) / mm_per_px
    height_px = (max_y - min_y) / mm_per_px
    cx, cy = flake.center
    half_w, half_h = width_px / 2, height_px / 2
    left_scale = 1.0 - flake.yaw
    right_scale = 1.0 + flake.yaw
    return [
        (cx - half_w, cy - half_h * left_scale + flake.skew),
        (cx + half_w, cy - half_h * right_scale + flake.skew),
        (cx + half_w, cy + half_h * right_scale + flake.skew),
        (cx - half_w, cy + half_h * left_scale + flake.skew),
    ]


def render_flake(scene: Image.Image, flake: Flake, mm_per_px: float,
                 light, bevel_mm: float, seed: int) -> Image.Image:
    """Собираем спрайт под условия сцены и ставим его в кадр.

    Толщина и вынос от плоскости пересчитываются из миллиметров в пиксели:
    лист ПВХ 3 мм на стене на таком масштабе — это меньше пикселя, поэтому
    «толстая» кромка в кадре сразу читается как подделка.
    """
    poly = flake.poly
    diameter_px = max(48, int(round(flake.diameter_mm / mm_per_px)))
    alpha = R.render_alpha(poly, diameter_px * 3)

    quad = flake.flat_quad or quad_for(flake, mm_per_px)
    sprite = R.shade(
        alpha,
        tint=flake.tint,
        light=(light[0], light[1], 0.82),
        bevel_px=max(1.6, bevel_mm / mm_per_px * 3.0),
        ambient=0.78,
        diffuse=0.30,
        specular=0.030,
        sheen=34.0,
        brightness=1.0,
        roughness=0.10,
        seed=seed,
    )

    strings = ()
    if flake.strings_from is not None:
        top_x = (quad[0][0] + quad[1][0]) / 2
        strings = [((top_x, flake.strings_from), (top_x, quad[0][1]))]

    return R.place(
        scene,
        sprite,
        quad,
        light=(light[0], light[1]),
        thickness_px=max(1.0, flake.thickness_mm / mm_per_px),
        standoff_px=flake.standoff_mm / mm_per_px,
        shadow=flake.shadow,
        contact=flake.contact,
        blur=flake.blur,
        grain=1.5,
        edge_line=flake.edge_line,
        strings=strings,
    )


# ── сцены ────────────────────────────────────────────────────────────────────

def scene_photozone() -> None:
    """Фотозона 3×2,5 м: снежинки накладкой на свободную часть стены.

    Масштаб: стена в кадре 710 px, реальная ширина около 3 м → ~4,2 мм на пиксель.
    """
    base = R.load_scene(REPO / "marketing/novogodnee-oformlenie-2027/creatives/source/photozone.jpg", W, H)
    mm_per_px = 4200 / 710
    light = (-0.55, -0.62)          # софит сверху-слева, как на стене

    flakes = [
        build(S.build_classic, 700, (300, 245), WHITE, mm_per_px, rotate=3,
              standoff_mm=18, shadow=0.24, contact=0.40),
        build(S.build_star, 500, (470, 155), NAVY, mm_per_px, rotate=-4, yaw=0.03,
              standoff_mm=18, shadow=0.24, contact=0.40),
        build(S.build_crystal, 500, (300, 465), CORAL, mm_per_px, rotate=-2,
              standoff_mm=18, shadow=0.24, contact=0.40),
        build(S.build_star, 350, (480, 345), MILK, mm_per_px, rotate=5,
              standoff_mm=12, shadow=0.22, contact=0.38),
        build(S.build_crystal, 350, (500, 465), WHITE, mm_per_px, rotate=-6,
              standoff_mm=12, shadow=0.22, contact=0.38),
        build(S.build_classic, 350, (200, 395), WHITE, mm_per_px, rotate=8,
              standoff_mm=12, shadow=0.22, contact=0.38),
    ]
    for index, flake in enumerate(flakes):
        render_flake(base, flake, mm_per_px, light, bevel_mm=2.0, seed=index)
    base.save(OUT / "01-photozone-wall.jpg", quality=92, optimize=True)


def scene_office() -> None:
    """Холл офиса: подвес на лесках. Потолок 3 м, масштаб ~4,4 мм на пиксель."""
    base = R.load_scene(REPO / "marketing/novogodnee-oformlenie-2027/creatives/source/lobby.jpg", W, H)
    mm_per_px = 3000 / 660
    light = (-0.25, -0.72)          # основной свет сверху, чуть слева

    flakes = [
        build(S.build_star, 500, (205, 250), WHITE, mm_per_px, rotate=2, blur=0.6,
              strings_from=96, thickness_mm=5.0, shadow=0.26, contact=0.34),
        build(S.build_classic, 500, (400, 190), MILK, mm_per_px, rotate=-3, blur=0.5,
              strings_from=88, thickness_mm=5.0, shadow=0.26, contact=0.34),
        build(S.build_crystal, 350, (560, 265), NAVY, mm_per_px, rotate=4, blur=0.8,
              strings_from=100, thickness_mm=5.0, shadow=0.24, contact=0.32),
    ]
    for index, flake in enumerate(flakes):
        render_flake(base, flake, mm_per_px, light, bevel_mm=2.0, seed=10 + index)
    base.save(OUT / "02-office-lobby.jpg", quality=92, optimize=True)


def scene_workshop() -> None:
    """Участок: деталь на столе фрезера. Стол ближе к камере, ~3,2 мм на пиксель."""
    base = R.load_scene(REPO / "public/media/workshop.jpg", W, H)
    mm_per_px = 3.0
    light = (-0.62, -0.40)          # окна слева, свет падает вправо

    # стол фрезера в кадре: x 0…440, y 490…600 — деталь кладём на его плоскость
    # площадка по плоскости стола: передний край ниже, дальний — выше и уже
    flat = [(118, 520), (330, 500), (338, 556), (126, 580)]
    # белая снежинка на белом листе ПВХ не читается и в жизни, поэтому
    # показываем цветной лист: деталь вырезана из тёмно-синего ПВХ 5 мм
    flake = build(S.build_star, 340, (228, 538), (34, 54, 78), mm_per_px,
                  rotate=-4, thickness_mm=6.0, standoff_mm=0,
                  shadow=0.30, contact=0.45, edge_line=0.0, flat_quad=flat)
    render_flake(base, flake, mm_per_px, light, bevel_mm=2.2, seed=20)
    base.save(OUT / "03-workshop-detail.jpg", quality=92, optimize=True)


def scene_showroom() -> None:
    """Автосалон: подвес над экспозицией. Потолок 4 м, ~5,9 мм на пиксель."""
    base = R.load_scene(REPO / "marketing/site-hero/source/candidate-b-showroom-brandwall.jpg", W, H)
    mm_per_px = 4200 / 700
    light = (-0.20, -0.76)

    flakes = [
        build(S.build_star, 700, (300, 205), (238, 233, 222), mm_per_px, rotate=3, blur=0.7,
              strings_from=10, thickness_mm=5.0, shadow=0.26, contact=0.34),
        build(S.build_classic, 500, (455, 145), (246, 243, 236), mm_per_px, rotate=-5, blur=0.5,
              strings_from=8, thickness_mm=5.0, shadow=0.26, contact=0.34),
        build(S.build_crystal, 500, (585, 250), (232, 227, 216), mm_per_px, rotate=6, blur=0.9,
              strings_from=12, thickness_mm=5.0, shadow=0.24, contact=0.32),
    ]
    for index, flake in enumerate(flakes):
        render_flake(base, flake, mm_per_px, light, bevel_mm=2.4, seed=30 + index)
    base.save(OUT / "04-showroom-suspension.jpg", quality=92, optimize=True)


def make_preview() -> None:
    """Лист-превью 2×2 с подписями."""
    names = [
        ("01-photozone-wall.jpg", "Фотозона: накладка на стену, Ø350–700 мм"),
        ("02-office-lobby.jpg", "Холл офиса: подвес на лесках, Ø350–500 мм"),
        ("03-workshop-detail.jpg", "Участок: деталь на столе фрезера, Ø350 мм"),
        ("04-showroom-suspension.jpg", "Автосалон: подвес над экспозицией, Ø500–700 мм"),
    ]
    cells = []
    for name, caption in names:
        cells.append((Image.open(OUT / name).convert("RGB").resize((600, 338), Image.LANCZOS), caption))

    gap, pad, caption_h = 16, 20, 34
    width = pad * 2 + 600 * 2 + gap
    height = pad * 2 + (338 + caption_h) * 2 + gap
    sheet = Image.new("RGB", (width, height), "#ffffff")
    draw = ImageDraw.Draw(sheet)
    face = S.font(19, 600) if hasattr(S, "font") else None
    for index, (image, caption) in enumerate(cells):
        x = pad + (index % 2) * (600 + gap)
        y = pad + (index // 2) * (338 + caption_h + gap)
        sheet.paste(image, (x, y))
        if face:
            draw.text((x, y + 338 + 8), caption, font=face, fill="#16283b")
        else:
            draw.text((x, y + 338 + 8), caption, fill="#16283b")
    sheet.save(OUT / "preview.jpg", quality=90, optimize=True)


def main() -> None:
    scene_photozone()
    scene_office()
    scene_workshop()
    scene_showroom()
    make_preview()
    for name in ("01-photozone-wall.jpg", "02-office-lobby.jpg", "03-workshop-detail.jpg",
                 "04-showroom-suspension.jpg", "preview.jpg"):
        path = OUT / name
        print(f"  {name}: {Image.open(path).size}, {path.stat().st_size / 1024:.0f} КБ")


if __name__ == "__main__":
    main()
