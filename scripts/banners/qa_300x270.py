#!/usr/bin/env python3
"""
Проверка печатных мастеров серии «Кастинг» 300 × 270 см.

Что проверяет:
  · геометрию файла (35 433 × 31 890 px = 300 × 270 см при 300 dpi);
  · плотность 300 dpi в заголовке JFIF;
  · отсутствие chroma-subsampling (4:4:4);
  · читаемость QR-кода прямо из мастера (qrcode извлекается из файла).

Запуск:
  python3 scripts/banners/qa_300x270.py
"""
from __future__ import annotations

import struct
import sys
from pathlib import Path

import numpy as np
import pyvips
import zxingcpp

ROOT = Path(__file__).resolve().parents[2]
PRINT_DIR = ROOT / "banners/casting-series/print"

DPI = 300
PX_CM = DPI / 2.54
W = round(300 * PX_CM)
H = round(270 * PX_CM)

MASTERS = {
    "kino": PRINT_DIR / "banner-kino-300x270.jpg",
    "pokaz": PRINT_DIR / "banner-pokaz-300x270.jpg",
    "dv-production": PRINT_DIR / "banner-dv-production-300x270.jpg",
}

EXPECT_URL = "https://model.dvkino.ru"


def jfif_info(path: Path) -> tuple[int, int, str, int, int]:
    """(units, density, subsampling, ширина, высота) из заголовка JPEG."""
    data = path.read_bytes()
    units = density = 0
    sampling = "?"
    width = height = 0
    pos = 2
    while pos < len(data):
        if data[pos] != 0xFF:
            pos += 1
            continue
        marker = data[pos + 1]
        if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
            pos += 2
            continue
        if marker == 0xDA:
            break
        seg_len = struct.unpack(">H", data[pos + 2:pos + 4])[0]
        seg = data[pos:pos + 2 + seg_len]
        if seg[4:9] == b"JFIF\x00":
            units = seg[11]
            density = struct.unpack(">H", seg[12:14])[0]
        elif marker in (0xC0, 0xC1, 0xC2):  # SOF — базовый кадр
            height = struct.unpack(">H", seg[5:7])[0]
            width = struct.unpack(">H", seg[7:9])[0]
            comps = seg[9]
            factors = [seg[11 + i * 3] for i in range(comps)]
            sampling = "4:4:4" if len(set(factors)) == 1 else "4:2:0"
        pos += 2 + seg_len
    return units, density, sampling, width, height


def qr_from_master(path: Path) -> str | None:
    """Ищет QR в мастере: уменьшаем вчетверо и сканируем всю площадь."""
    im = pyvips.Image.jpegload(str(path), shrink=4, access="sequential")
    buf = im.write_to_memory()
    img = pyvips.Image.new_from_memory(buf, im.width, im.height, im.bands, "uchar")
    arr = np.ndarray(shape=(img.height, img.width, img.bands), dtype=np.uint8,
                     buffer=img.write_to_memory())
    results = zxingcpp.read_barcodes(arr)
    for r in results:
        if r.format.name == "QRCode":
            return r.text
    return None


def main() -> int:
    ok = True
    for key, path in MASTERS.items():
        if not path.exists():
            print(f"✗ {key}: нет файла {path.name}")
            ok = False
            continue
        units, density, sampling, width, height = jfif_info(path)
        size_mb = path.stat().st_size / 1024 / 1024

        checks = [
            ("размер", (width, height) == (W, H), f"{width}×{height} px"),
            ("dpi", units == 1 and density == DPI, f"{density} dpi"),
            ("4:4:4", sampling == "4:4:4", sampling),
        ]
        if key == "dv-production":
            checks.append(("QR", True, "в макете нет QR"))
        else:
            url = qr_from_master(path)
            checks.append(("QR", url == EXPECT_URL, url or "не найден"))

        bad = [c for c in checks if not c[1]]
        ok = ok and not bad
        print(f"{'✓' if not bad else '✗'} {key}: {path.name} ({size_mb:.0f} МБ)")
        for name, good, value in checks:
            print(f"    {'✓' if good else '✗'} {name}: {value}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
