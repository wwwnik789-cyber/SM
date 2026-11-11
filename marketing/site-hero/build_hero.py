#!/usr/bin/env python3
"""Сборка файлов для первого экрана главной страницы sm-production.ru.

Готовит из реальных фотографий:
  desktop-2560.jpg   2560×1440 — фон обложки для широких экранов
  desktop-1920.jpg   1920×1080 — базовый фон Tilda
  mobile-1080.jpg    1080×1920 — отдельный фон для телефона
  og-1200x630.jpg    1200×630  — превью для соцсетей и мессенджеров
  scrim/*            те же размеры с затемнением под текст

Файлы кладутся в marketing/site-hero/out/<кандидат>/.

Запуск из корня репозитория:
    .venv/bin/python marketing/site-hero/build_hero.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "source"
OUT = HERE / "out"

# Кандидаты: файл, точка фокуса для десктопа и для мобильного кропа
CANDIDATES = [
    {
        "slug": "a-conference",
        "file": "candidate-a-conference-mitsubishi.jpg",
        "title": "Конференция: сцена, экран, свет",
        "desktop_focus": (0.50, 0.50),
        "mobile_focus": (0.50, 0.42),
        "note": "Самый «масштабный» кадр из архива: ровная геометрия, видны каше, свет, трибуна. "
                "Но на экране и на фартуке сцены читается логотип заказчика.",
    },
    {
        "slug": "b-brandwall",
        "file": "candidate-b-showroom-brandwall.jpg",
        "title": "Бренд-зона в автосалоне",
        "desktop_focus": (0.42, 0.50),
        "mobile_focus": (0.38, 0.50),
        "note": "Чистая композиция, видно качество печати и масштаб полотна, есть люди. "
                "Но это автосалон, а не мероприятие — на главной читается уже как другая услуга.",
    },
    {
        "slug": "c-maxim-set",
        "file": "candidate-c-maxim-set.jpg",
        "title": "Сезонная фотозона MAXIM",
        "desktop_focus": (0.50, 0.55),
        "mobile_focus": (0.52, 0.55),
        "note": "Показывает объёмную конструкцию и печать. Минус тот же: чужой бренд на первом плане "
                "и много бытовых деталей по краям.",
    },
]

# Целевые размеры: имя -> (ширина, высота, максимальный вес в КБ)
SIZES = {
    "desktop-2560": (2560, 1440, 430),
    "desktop-1920": (1920, 1080, 300),
    "mobile-1080": (1080, 1920, 300),
    "og-1200x630": (1200, 630, 160),
}


def cover(image: Image.Image, size: tuple[int, int], focus: tuple[float, float]) -> Image.Image:
    w, h = size
    scale = max(w / image.width, h / image.height)
    resized = image.resize(
        (round(image.width * scale), round(image.height * scale)),
        Image.Resampling.LANCZOS,
    )
    left = int(max(0, min((resized.width - w) * focus[0], resized.width - w)))
    top = int(max(0, min((resized.height - h) * focus[1], resized.height - h)))
    return resized.crop((left, top, left + w, top + h))


def grade(image: Image.Image) -> Image.Image:
    """Мягкая коррекция: чуть контраста и насыщенности, чтобы кадр не выглядел серым."""
    image = ImageEnhance.Contrast(image).enhance(1.06)
    image = ImageEnhance.Color(image).enhance(1.05)
    return image


def scrim(image: Image.Image) -> Image.Image:
    """Затемнение под текст: плотнее сверху и снизу, центр остаётся читаемым."""
    w, h = image.size
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    top_band = int(h * 0.55)
    for y in range(top_band):
        t = 1 - y / top_band
        draw.rectangle([0, y, w, y + 1], fill=(6, 14, 26, int(150 * t ** 1.6)))
    bottom_start = int(h * 0.55)
    for y in range(bottom_start, h):
        t = (y - bottom_start) / (h - bottom_start)
        draw.rectangle([0, y, w, y + 1], fill=(6, 14, 26, int(165 * t ** 1.5)))
    layer = layer.filter(ImageFilter.GaussianBlur(round(min(w, h) * 0.02)))
    return Image.alpha_composite(image.convert("RGBA"), layer).convert("RGB")


def save(image: Image.Image, path: Path, max_kb: int = 300) -> int:
    """Сохраняет JPEG, снижая качество, пока файл не влезет в лимит веса."""
    path.parent.mkdir(parents=True, exist_ok=True)
    quality = 88
    while True:
        image.save(path, format="JPEG", quality=quality, optimize=True, progressive=True)
        kb = path.stat().st_size // 1024
        if kb <= max_kb or quality <= 62:
            return kb
        quality -= 4


def main() -> int:
    total = 0
    for cand in CANDIDATES:
        src = SOURCE / cand["file"]
        if not src.exists():
            print(f"нет файла: {src}")
            return 1
        base = Image.open(src).convert("RGB")
        folder = OUT / cand["slug"]

        # Насколько исходник покрывает самый широкий размер
        widest = SIZES["desktop-2560"][0]
        upscale = widest / base.width

        for name, (w, h, limit) in SIZES.items():
            mobile = name == "mobile-1080"
            focus = cand["mobile_focus"] if mobile else cand["desktop_focus"]
            # для og берём тот же кроп, что для десктопа
            img = grade(cover(base, (w, h), focus))
            kb = save(img, folder / f"{name}.jpg", limit)
            kb_s = save(scrim(img), folder / "scrim" / f"{name}.jpg", limit)
            total += 2
            print(f"  {cand['slug']}/{name}.jpg  {w}×{h}  {kb} КБ / scrim {kb_s} КБ")

        print(f"{cand['slug']}: {cand['title']} (исходник {base.width}×{base.height}, "
              f"растяжение до 2560 — {upscale:.2f}×)")
    print(f"\nвсего файлов: {total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
