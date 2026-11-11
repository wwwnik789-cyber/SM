#!/usr/bin/env python3
"""Build 240x400 Direct creatives under 120 KB each.

At 240x400 px the previous layout (photo half + navy panel half) leaves the
text column around 110 px wide, which is unreadable. This version stacks:
photo occupies the top ~58%, a solid navy block below carries the text.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
SOURCE = ROOT / "source"
OUT_DIR = ROOT / "240x400"
FONT_VF = REPO / "banners" / "anikom-arena-3000x2500-concepts" / "source" / "Montserrat-Variable.ttf"

if not FONT_VF.exists():
    raise SystemExit(f"Не найден шрифт: {FONT_VF}")

W, H = 240, 400
LIMIT_KB = 120

NAVY = (8, 26, 43)
CORAL = (217, 74, 67)
WHITE = (255, 255, 255)
MUTED = (186, 198, 212)

SCENES = [
    {
        "slug": "01-office",
        "image": "lobby.jpg",
        "photo_h": 218,
        "kicker": "СЕЗОН 2027",
        "title": "Новогоднее оформление офиса",
        "promise": "Расчёт за 1 рабочий день",
        "sub": "Своё производство 750 м²",
        "focus": (0.62, 0.55),
    },
    {
        "slug": "02-photozone",
        "image": "photozone.jpg",
        "photo_h": 218,
        "kicker": "ФОТОЗОНЫ И БРЕНД-ЗОНЫ",
        "title": "Фотозона к Новому году",
        "promise": "Монтаж за 7 дней",
        "sub": "Скрытый каркас и свет",
        "focus": (0.66, 0.50),
    },
    {
        "slug": "03-corporate",
        "image": "corporate.jpg",
        "photo_h": 218,
        "kicker": "КОРПОРАТИВЫ",
        "title": "Оформление новогоднего события",
        "promise": "Монтаж в ночное окно",
        "sub": "Сцена, фотозона, навигация",
        "focus": (0.55, 0.50),
    },
    {
        "slug": "04-art",
        "image": "art.jpg",
        "photo_h": 218,
        "kicker": "АРТ-ОБЪЕКТЫ",
        "title": "Ёлка как арт-объект",
        "promise": "Улица и интерьер",
        "sub": "Своё производство 750 м²",
        "focus": (0.60, 0.50),
    },
]


def font(size: int, weight: int) -> ImageFont.FreeTypeFont:
    face = ImageFont.truetype(str(FONT_VF), size)
    face.set_variation_by_axes([weight])
    return face


def text_width(draw: ImageDraw.ImageDraw, text: str, face) -> int:
    box = draw.textbbox((0, 0), text, font=face)
    return box[2] - box[0]


def wrap(draw, text: str, face, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if text_width(draw, candidate, face) <= max_width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def cover(image: Image.Image, size: tuple[int, int], focus: tuple[float, float]) -> Image.Image:
    target_w, target_h = size
    scale = max(target_w / image.width, target_h / image.height)
    resized = image.resize(
        (round(image.width * scale), round(image.height * scale)),
        Image.Resampling.LANCZOS,
    )
    # Keep the requested focal point inside the crop.
    left = round((resized.width - target_w) * focus[0])
    top = round((resized.height - target_h) * focus[1])
    left = max(0, min(left, resized.width - target_w))
    top = max(0, min(top, resized.height - target_h))
    return resized.crop((left, top, left + target_w, top + target_h))


def build(scene: dict, out_path: Path) -> int:
    canvas = Image.new("RGB", (W, H), NAVY)
    draw = ImageDraw.Draw(canvas)

    photo_h = scene["photo_h"]
    photo = cover(Image.open(SOURCE / scene["image"]).convert("RGB"), (W, photo_h), scene["focus"])
    canvas.paste(photo, (0, 0))

    # Soft fade from photo into the navy block.
    fade_h = 34
    for offset in range(fade_h):
        y = photo_h - fade_h + offset
        alpha = int(255 * (offset / fade_h) ** 1.5)
        stripe = Image.new("RGB", (W, 1), NAVY)
        canvas.paste(stripe, (0, y), Image.new("L", (W, 1), alpha))

    # Coral divider
    draw.rectangle([0, photo_h - 2, W, photo_h], fill=CORAL)

    margin = 14
    inner_w = W - margin * 2
    cursor = photo_h + 12

    # Kicker
    kicker = font(9, 700)
    draw.text((margin, cursor), scene["kicker"], font=kicker, fill=CORAL)
    cursor += 16

    # Title, auto-fitted (up to 3 lines now that the price is gone)
    title_size = 20
    while title_size > 12:
        face = font(title_size, 800)
        lines = wrap(draw, scene["title"], face, inner_w)
        line_h = round(title_size * 1.12)
        if len(lines) <= 3 and max(text_width(draw, l, face) for l in lines) <= inner_w:
            break
        title_size -= 1
    face = font(title_size, 800)
    lines = wrap(draw, scene["title"], face, inner_w)
    line_h = round(title_size * 1.12)
    for line in lines:
        draw.text((margin, cursor), line, font=face, fill=WHITE)
        cursor += line_h

    cursor += 8

    # Accent rule + promise (replaces the price block)
    draw.rectangle([margin, cursor, margin + 22, cursor + 2], fill=CORAL)
    cursor += 9
    promise_face = font(11, 700)
    draw.text((margin, cursor), scene["promise"], font=promise_face, fill=CORAL)
    cursor += 16

    sub_face = font(8.5, 500)
    draw.text((margin, cursor), scene["sub"], font=sub_face, fill=MUTED)

    # Brand lockup pinned to the bottom edge
    brand = font(9, 750)
    brand_y = H - 22
    draw.rectangle([margin, brand_y - 3, margin + 16, brand_y - 1], fill=CORAL)
    draw.text((margin, brand_y + 4), "SM PRODUCTION", font=brand, fill=(150, 164, 180))
    site = font(7, 500)
    draw.text((W - margin, brand_y + 5), "sm-production.ru", font=site, fill=(96, 112, 130), anchor="ra")

    canvas.save(out_path, format="JPEG", quality=88, optimize=True, progressive=True, subsampling=2)
    return out_path.stat().st_size


def shrink_to_limit(path: Path) -> int:
    """Lower quality only if a file is above the limit."""
    if path.stat().st_size <= LIMIT_KB * 1024:
        return path.stat().st_size
    image = Image.open(path)
    for quality in (84, 80, 76, 72, 68, 64):
        image.save(path, format="JPEG", quality=quality, optimize=True, progressive=True, subsampling=2)
        if path.stat().st_size <= LIMIT_KB * 1024:
            break
    return path.stat().st_size


def main() -> int:
    OUT_DIR.mkdir(exist_ok=True)
    over = 0
    for scene in SCENES:
        out = OUT_DIR / f"{scene['slug']}-240x400.jpg"
        build(scene, out)
        size = shrink_to_limit(out)
        kb = size / 1024
        flag = "OK" if kb <= LIMIT_KB else "ПРЕВЫШЕНИЕ"
        if kb > LIMIT_KB:
            over += 1
        with Image.open(out) as check:
            dims = check.size
        print(f"{out.name}: {kb:.1f} КБ · {dims[0]}×{dims[1]} · {flag}")
    print(f"\nФайлов: {len(SCENES)} · лимит {LIMIT_KB} КБ · превышений: {over}")
    return 1 if over else 0


if __name__ == "__main__":
    sys.exit(main())
