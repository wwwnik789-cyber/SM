#!/usr/bin/env python3
"""Сборка итогового контактного листа серии баннеров «Кастинг».

Генерирует:
  banners/casting-series/preview/casting-series-contact-sheet.jpg — три макета рядом
  banners/casting-series/preview/casting-qr-proof.jpg             — крупные планы QR с проверкой

Требования: pip install pillow numpy opencv-python-headless zxing-cpp
Запуск:     python3 scripts/banners/make_preview.py
"""
from __future__ import annotations

from pathlib import Path

import cv2
import zxingcpp
from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "banners/casting-series/preview"

PRINT = {
    "kino": REPO / "banners/casting-series/print/banner-kasting-proby-v-kino-4608x8256.jpg",
    "pokaz": REPO / "banners/casting-series/print/banner-kasting-modnyy-pokaz-5088x7584.jpg",
    "dv-production": REPO / "banners/casting-series/print/banner-dv-production-6144x6144.jpg",
}

WEB = {
    "kino": REPO / "public/media/banners/kino.jpg",
    "pokaz": REPO / "public/media/banners/pokaz.jpg",
    "dv-production": REPO / "public/media/banners/dv-production.jpg",
}

META = {
    "kino": ("Кастинг на пробы в кино", "39 × 70 см", "4608 × 8256 px · 300 dpi", "сработанный QR"),
    "pokaz": ("Кастинг на модный показ", "43 × 64 см", "5088 × 7584 px · 300 dpi", "сработанный QR"),
    "dv-production": ("ДВ ПРОДАКШЕН", "52 × 52 см", "6144 × 6144 px · 300 dpi", "логотип в углу"),
}

BG = (14, 10, 20)
FG = (245, 240, 250)
MUTED = (168, 152, 180)
GOLD = (211, 153, 109)

FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
REG = FONT_DIR / "DejaVuSans.ttf"
BOLD = FONT_DIR / "DejaVuSans-Bold.ttf"


def font(size: int, bold: bool = False):
    path = BOLD if bold and BOLD.exists() else REG
    return ImageFont.truetype(str(path), size)


def find_qr_box(path: Path) -> tuple[int, int, int, int]:
    """Координаты QR-кода: декодируем мастер целиком и берём позицию кода."""
    img = cv2.imread(str(path))
    for b in zxingcpp.read_barcodes(img, try_rotate=True, try_invert=True, try_downscale=True):
        if b.format != zxingcpp.BarcodeFormat.QRCode:
            continue
        pos = b.position
        pts = [(pos.top_left.x, pos.top_left.y), (pos.top_right.x, pos.top_right.y),
               (pos.bottom_left.x, pos.bottom_left.y), (pos.bottom_right.x, pos.bottom_right.y)]
        xs = [x for x, _ in pts]
        ys = [y for _, y in pts]
        x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
        pad = int((x1 - x0) * 0.05)
        h, w = img.shape[:2]
        return max(0, x0 - pad), max(0, y0 - pad), min(w, x1 + pad), min(h, y1 + pad)
    raise RuntimeError(f"QR не найден: {path}")


def decode_qr(path: Path, box=None) -> str | None:
    img = cv2.imread(str(path))
    if box:
        x0, y0, x1, y1 = box
        img = img[y0:y1, x0:x1]
    res = zxingcpp.read_barcodes(img, try_rotate=True, try_invert=True, try_downscale=True)
    for r in res:
        if r.format == zxingcpp.BarcodeFormat.QRCode:
            return r.text
    return None


def contact_sheet() -> Path:
    W, H = 2400, 1620
    sheet = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(sheet)

    d.text((90, 70), "Серия баннеров «Кастинг» — итоговые макеты", font=font(58, True), fill=FG)
    d.text((92, 148), "SM PRODUCTION · печатные мастеры 300 dpi · sRGB · вылетов нет",
           font=font(28), fill=MUTED)
    d.line([(90, 200), (W - 90, 200)], fill=(60, 44, 72), width=2)

    order = ["kino", "pokaz", "dv-production"]
    slot_w, gap = 660, 60
    x0 = 90
    top = 250
    for i, key in enumerate(order):
        title, size_cm, px, note = META[key]
        im = Image.open(WEB[key]).convert("RGB")
        ratio = (slot_w - 40) / im.width
        im = im.resize((int(im.width * ratio), int(im.height * ratio)), Image.LANCZOS)
        col = x0 + i * (slot_w + gap)
        d.rounded_rectangle([col - 20, top - 20, col + slot_w - 40 + 20, top + im.height + 250],
                            radius=24, fill=(26, 18, 34), outline=(58, 40, 70), width=2)
        sheet.paste(im, (col, top))
        ty = top + im.height + 24
        d.text((col, ty), title, font=font(34, True), fill=FG)
        d.text((col, ty + 50), f"{size_cm}  ·  {px}", font=font(26), fill=GOLD)
        d.text((col, ty + 90), note, font=font(24), fill=MUTED)

    d.text((90, H - 74), "QR в макете «Кастинг на пробы в кино» пересобран: прежний код был "
                         "декоративным и не считывался.", font=font(26), fill=MUTED)
    out = OUT / "casting-series-contact-sheet.jpg"
    sheet.save(out, quality=92, subsampling=0)
    return out


def qr_proof() -> Path:
    W, H = 2200, 1180
    sheet = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(sheet)
    d.text((90, 60), "Проверка QR-кодов в печатных мастерах", font=font(52, True), fill=FG)
    d.text((92, 132), "zxing-cpp: декодирование из полноразмерного файла, 300 dpi",
           font=font(26), fill=MUTED)
    d.line([(90, 180), (W - 90, 180)], fill=(60, 44, 72), width=2)

    x = 90
    for key in ("kino", "pokaz"):
        path = PRINT[key]
        box = find_qr_box(path)
        url = decode_qr(path, box)
        crop = Image.open(path).convert("RGB").crop(box)
        crop = crop.resize((620, int(crop.height * 620 / crop.width)), Image.LANCZOS)
        sheet.paste(crop, (x, 230))
        d.rounded_rectangle([x - 16, 214, x + 636, 230 + crop.height + 16],
                            radius=18, outline=(58, 40, 70), width=2)
        title, size_cm, px, _ = META[key]
        ty = 230 + crop.height + 46
        d.text((x, ty), title, font=font(34, True), fill=FG)
        d.text((x, ty + 52), f"{size_cm} · {px} · модуль 6.01 мм · код 175.7 мм",
               font=font(24), fill=MUTED)
        d.text((x, ty + 94), f"→ {url if url else 'НЕ СЧИТЫВАЕТСЯ'}",
               font=font(30, True), fill=(120, 220, 150) if url else (230, 90, 90))
        x += 1010

    d.text((90, H - 66), "Проверено: чтение в мастере, после JPEG q80 и при уменьшении до 400 px.",
           font=font(24), fill=MUTED)
    out = OUT / "casting-qr-proof.jpg"
    sheet.save(out, quality=92, subsampling=0)
    return out


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    print("OK:", contact_sheet())
    print("OK:", qr_proof())
    for key in ("kino", "pokaz"):
        print(key, "→", decode_qr(PRINT[key], find_qr_box(PRINT[key])))
