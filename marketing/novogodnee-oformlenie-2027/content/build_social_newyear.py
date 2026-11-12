#!/usr/bin/env python3
"""Новогодняя картинка без текста к посту об открытии сезона.

Съёмка своего производства: световое дерево из неонового шнура на прозрачном
ПВХ, ёлочные игрушки с логотипом SM вырезаны и подвешены на леске. Это не
сторонний сток и не визуализация, а реальный объект — то, что и продаёт пост.

Кадр собран без надписей: ни заголовка, ни плашки, ни логотипа. В ленте он
читается как фотография, а не как реклама, и текст поста работает подписью.

Что делается с фотографией:
  * кадрирование под три формата (4:5, 1:1, 9:16);
  * охлаждение: убирается лишняя маджента от бордовой ткани;
  * приглушение света — неон должен светиться, а не выжигать кадр;
  * виньетка и лёгкая резкость после уменьшения.

Запуск из корня репозитория:
    .venv/bin/python marketing/novogodnee-oformlenie-2027/content/build_social_newyear.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SOURCE = HERE / "source" / "ny-neon-tree.jpg"
OUT = HERE / "images"

# Кадрирование задано в долях от размера исходника, чтобы не зависеть от его пикселей.
FORMATS = [
    ("social/1080x1350/ny-image-neon-4x5.jpg", (1080, 1350), (0.00, 0.05, 0.53, 1.00)),
    ("social/1080x1080/ny-image-neon-1x1.jpg", (1080, 1080), (0.00, 0.18, 0.53, 0.94)),
    ("stories/ny-image-neon-1080x1920.jpg", (1080, 1920), (0.02, 0.00, 0.40, 1.00)),
]


def crop_ratio(image: Image.Image, ratio: float, box: tuple[float, float, float, float]) -> Image.Image:
    """Берёт область box (в долях) и подгоняет её под нужное соотношение сторон."""
    w, h = image.size
    left, top, right, bottom = (round(box[0] * w), round(box[1] * h), round(box[2] * w), round(box[3] * h))
    region = image.crop((left, top, right, bottom))

    current = region.width / region.height
    if current > ratio:                     # шире нужного — режем по бокам
        new_w = round(region.height * ratio)
        offset = (region.width - new_w) // 2
        return region.crop((offset, 0, offset + new_w, region.height))
    new_h = round(region.width / ratio)     # выше нужного — режем сверху и снизу
    offset = (region.height - new_h) // 2
    return region.crop((0, offset, region.width, offset + new_h))


def vignette(image: Image.Image, strength: float = 0.34) -> Image.Image:
    w, h = image.size
    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse(
        [-w * 0.22, -h * 0.18, w * 1.22, h * 1.18],
        fill=255,
    )
    mask = mask.filter(ImageFilter.GaussianBlur(radius=max(w, h) * 0.18))
    shadow = Image.new("RGB", (w, h), (10, 6, 16))
    return Image.composite(image, Image.blend(image, shadow, strength), mask)


def grade(image: Image.Image) -> Image.Image:
    # бордовая ткань даёт сильную мадженту — снимаем её, уводя кадр в холодный
    red, green, blue = image.split()
    red = red.point(lambda value: max(0, round(value * 0.965)))
    green = green.point(lambda value: min(255, round(value * 1.02)))
    blue = blue.point(lambda value: min(255, round(value * 1.06)))
    image = Image.merge("RGB", (red, green, blue))

    image = ImageEnhance.Brightness(image).enhance(0.93)
    image = ImageEnhance.Contrast(image).enhance(1.10)
    image = ImageEnhance.Color(image).enhance(1.05)
    image = vignette(image)
    return image.filter(ImageFilter.UnsharpMask(radius=1.6, percent=70, threshold=3))


def main() -> int:
    if not SOURCE.exists():
        print(f"Нет исходника: {SOURCE}")
        return 1

    source = Image.open(SOURCE).convert("RGB")
    for relative, size, box in FORMATS:
        ratio = size[0] / size[1]
        image = grade(crop_ratio(source, ratio, box)).resize(size, Image.Resampling.LANCZOS)
        path = OUT / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        image.save(path, format="JPEG", quality=92, optimize=True, progressive=True)
        print(f"{path.relative_to(HERE)}: {size[0]}×{size[1]}, {path.stat().st_size // 1024} КБ")
    return 0


if __name__ == "__main__":
    sys.exit(main())
