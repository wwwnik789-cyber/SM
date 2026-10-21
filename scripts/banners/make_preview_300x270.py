#!/usr/bin/env python3
"""
Превью серии «Кастинг» под конструкцию 300 × 270 см.

Собирает в `banners/casting-series/preview/`:
  • полный печатный файл (1600 px по ширине) — как уходит в типографию;
  • видимое лицо 220 × 250 см — то, что видит зритель у конструкции;
  • контактный лист серии с подписями.

Видимые лица дополнительно кладёт в `public/media/banners/` — они идут
на сайт (витрина серии и кейс).

Запуск:
  python3 scripts/banners/make_preview_300x270.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pyvips
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
PREVIEW = ROOT / "banners/casting-series/preview"
WEB = ROOT / "public/media/banners"

FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
F_REG = FONT_DIR / "DejaVuSans.ttf"
F_BOLD = FONT_DIR / "DejaVuSans-Bold.ttf"

# геометрия печатного файла, см
CANVAS_W_CM, CANVAS_H_CM = 300, 270
FACE = (40, 10, 260, 260)  # x0, y0, x1, y1 — видимое лицо

ITEMS = [
    ("kino", "Кастинг на пробы в кино", "вертикальный, 220 × 250 см лица"),
    ("pokaz", "Кастинг на модный показ", "вертикальный, 220 × 250 см лица"),
    ("dv-production", "Продюсерський центр ДВ ПРОДАКШЕН", "брендовый, 220 × 250 см лица"),
]


def face_crop(src: Path, dst: Path, dst_width: int, webp: bool = False) -> tuple[int, int]:
    """Вырезает видимое лицо из веб-версии печатного файла и масштабирует."""
    im = pyvips.Image.new_from_file(str(src))
    x0 = round(im.width * FACE[0] / CANVAS_W_CM)
    x1 = round(im.width * FACE[2] / CANVAS_W_CM)
    y0 = round(im.height * FACE[1] / CANVAS_H_CM)
    y1 = round(im.height * FACE[3] / CANVAS_H_CM)
    crop = im.crop(x0, y0, x1 - x0, y1 - y0).resize(dst_width / (x1 - x0),
                                                    kernel="lanczos3")
    crop.write_to_file(str(dst.with_suffix(".jpg")), Q=84, strip=True)
    if webp:
        crop.write_to_file(str(dst.with_suffix(".webp")), Q=80, strip=True)
    return crop.width, crop.height


def main() -> int:
    PREVIEW.mkdir(parents=True, exist_ok=True)
    WEB.mkdir(parents=True, exist_ok=True)
    thumbs = []
    for key, title, note in ITEMS:
        src = WEB / f"{key}-300x270.jpg"
        if not src.exists():
            print(f"Нет веб-версии: {src}")
            continue

        # копия полного печатного файла в репозиторий (веб-версия остаётся на месте)
        out = PREVIEW / f"casting-300x270-{key}.jpg"
        im = Image.open(src)
        im.save(out, quality=90, subsampling=0)
        print(f"Превью: {out.relative_to(ROOT)} ({im.size[0]}×{im.size[1]}, "
              f"{out.stat().st_size // 1024} КБ)")

        # видимое лицо — для сайта и для согласования композиции
        fw, fh = face_crop(src, WEB / f"{key}-300x270-face", 1400, webp=True)
        face_out = PREVIEW / f"casting-300x270-{key}-face.jpg"
        face_crop(src, face_out, 1200)
        print(f"  лицо: {face_out.relative_to(ROOT)} ({fw}×{fh})")

        t = im.copy()
        t.thumbnail((760, 760), Image.LANCZOS)
        thumbs.append((t, title, note))

    if not thumbs:
        return 1

    # контактный лист
    pad = 48
    cap = 96
    width = pad + sum(t.width + pad for t, _, _ in thumbs)
    height = pad + max(t.height for t, _, _ in thumbs) + cap + pad
    sheet = Image.new("RGB", (width, height), (247, 244, 240))
    d = ImageDraw.Draw(sheet)
    f_title = ImageFont.truetype(str(F_BOLD), 34)
    f_note = ImageFont.truetype(str(F_REG), 22)

    x = pad
    top = pad
    for t, title, note in thumbs:
        sheet.paste(t, (x, top))
        d.rectangle([x, top, x + t.width, top + t.height], outline=(150, 22, 74), width=2)
        d.text((x, top + t.height + 18), title, font=f_title, fill=(26, 22, 30))
        d.text((x, top + t.height + 56), note, font=f_note, fill=(122, 112, 126))
        x += t.width + pad

    out = PREVIEW / "casting-300x270-contact-sheet.jpg"
    sheet.save(out, quality=90, subsampling=0)
    print(f"Контактный лист: {out.relative_to(ROOT)} ({sheet.size[0]}×{sheet.size[1]}, "
          f"{out.stat().st_size // 1024} КБ)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
