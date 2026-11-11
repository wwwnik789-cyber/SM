#!/usr/bin/env python3
"""
Обложка первого экрана из РЕАЛЬНОГО фото объекта (конференция Mitsubishi, 24.01.2024).

Формат: только фото, без вшитого текста.
Кадры: десктоп 2560×1440 / 1920×1080, мобильный 1080×1920, og 1200×630.

Запуск:  .venv/bin/python marketing/site-hero/build_cover_real.py
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "source" / "candidate-a-conference-mitsubishi.jpg"
OUT = HERE / "cover"

NAVY = (8, 26, 43)
CORAL = (217, 74, 67)


def curve(points):
    """Кусочно-линейная кривая 0..255 для point()."""
    lut = []
    for x in range(256):
        for i in range(len(points) - 1):
            x0, y0 = points[i]
            x1, y1 = points[i + 1]
            if x0 <= x <= x1:
                t = 0 if x1 == x0 else (x - x0) / (x1 - x0)
                lut.append(round(y0 + (y1 - y0) * t))
                break
        else:
            lut.append(255 if x > points[-1][0] else 0)
    return lut


# мягкий грейд: тени уводим в фирменный синий, света оставляем тёплыми,
# красный канал не трогаем, чтобы не убить коралловый акцент на сцене
R_LUT = curve([(0, 6), (64, 66), (128, 130), (192, 196), (255, 255)])
G_LUT = curve([(0, 18), (64, 68), (128, 130), (192, 193), (255, 252)])
B_LUT = curve([(0, 40), (64, 88), (128, 146), (192, 198), (255, 242)])


def grade(image: Image.Image) -> Image.Image:
    image = image.convert("RGB")
    r, g, b = image.split()
    return Image.merge("RGB", (r.point(R_LUT), g.point(G_LUT), b.point(B_LUT)))


def vignette(image: Image.Image, strength: float = 0.28) -> Image.Image:
    """Лёгкая винетка: низ кадра под залом темнее, центр чистый."""
    w, h = image.size
    small = Image.new("L", (max(8, w // 8), max(8, h // 8)), 0)
    d = ImageDraw.Draw(small)
    d.ellipse([-w // 10, -h // 10, w // 8 + w // 10, h // 8 + h // 10], fill=255)
    mask = small.filter(ImageFilter.GaussianBlur(max(1, w // 40))).resize((w, h), Image.LANCZOS)
    dark = Image.new("RGB", (w, h), (2, 8, 16))
    return Image.composite(image, Image.blend(image, dark, strength), mask)


def crop_to(image: Image.Image, size: tuple[int, int], focus: tuple[float, float] = (0.5, 0.5)) -> Image.Image:
    """Кроп по соотношению кадра, потом ресайз в точный размер."""
    tw, th = size
    target = tw / th
    src_ratio = image.width / image.height
    if src_ratio > target:
        new_w = round(image.height * target)
        x0 = round((image.width - new_w) * focus[0])
        box = (x0, 0, x0 + new_w, image.height)
    else:
        new_h = round(image.width / target)
        y0 = round((image.height - new_h) * focus[1])
        box = (0, y0, image.width, y0 + new_h)
    return image.crop(box).resize((tw, th), Image.LANCZOS)


def save(image: Image.Image, name: str, limit_kb: int) -> None:
    """Подбираем качество JPEG под лимит веса, шагая от высокого к низкому."""
    path = OUT / name
    for q in (92, 90, 88, 86, 84, 82, 80, 78, 76, 74, 72):
        image.save(path, "JPEG", quality=q, optimize=True, progressive=True, subsampling=2)
        if path.stat().st_size // 1024 <= limit_kb:
            break
    print(f"  {name:38} {image.width}×{image.height}  {path.stat().st_size // 1024} КБ  q={q}")


def main() -> int:
    if not SOURCE.exists():
        print(f"нет исходника: {SOURCE}", file=sys.stderr)
        return 1
    OUT.mkdir(parents=True, exist_ok=True)

    src = Image.open(SOURCE).convert("RGB")
    print(f"исходник: {SOURCE.name}  {src.width}×{src.height}")

    base = vignette(grade(src), 0.26)

    # десктоп: кадр целиком, сцена по центру
    desk = crop_to(base, (2560, 1440), (0.5, 0.5))
    save(desk, "cover-desktop-clean-2560x1440.jpg", 500)
    save(desk.resize((1920, 1080), Image.LANCZOS), "cover-desktop-clean-1920x1080.jpg", 340)

    # мобильный: вертикаль, сцена целиком, чуть больше пола и потолка
    mob = crop_to(base, (1080, 1920), (0.5, 0.5))
    mob = mob.filter(ImageFilter.UnsharpMask(radius=1.2, percent=45, threshold=3))
    save(mob, "cover-mobile-clean-1080x1920.jpg", 330)

    # og: соцпревью
    og = crop_to(base, (1200, 630), (0.5, 0.5))
    save(og, "og-1200x630.jpg", 200)

    # контактный лист
    tiles = [(desk, "десктоп 16:9"), (mob, "мобильный 9:16")]
    ch = 620
    widths = [round(t[0].width * ch / t[0].height) for t in tiles]
    pad = 26
    W = sum(widths) + pad * (len(tiles) + 1)
    H = ch + 106
    sheet = Image.new("RGB", (W, H), (14, 18, 25))
    d = ImageDraw.Draw(sheet)
    d.rectangle([0, 0, W, 6], fill=CORAL)
    x = pad
    for (img, label), w in zip(tiles, widths):
        sheet.paste(img.resize((w, ch), Image.LANCZOS), (x, 74))
        d.text((x + 2, ch + 80), label, font=None, fill=(200, 209, 220))
        x += w + pad
    sheet.save(OUT / "preview.jpg", "JPEG", quality=90, optimize=True)
    print(f"  {'preview.jpg':38} {sheet.width}×{sheet.height}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
