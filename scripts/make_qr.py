#!/usr/bin/env python3
"""
Генерация QR-кода для баннеров «ДВ Продакшен».

    python3 scripts/make_qr.py "https://ссылка-на-форму" kino
    python3 scripts/make_qr.py "https://ссылка-на-другую-форму" pokaz

Результат: visualizations/dv-production/qr-kino.png (qr-pokaz.png).
После этого пересоберите макеты — build_dv_banners.py подхватит файл сам.
"""

from __future__ import annotations

import sys
from pathlib import Path

import qrcode
from qrcode.constants import ERROR_CORRECT_H

OUT_DIR = Path(__file__).resolve().parents[1] / "visualizations/dv-production"


def make(url: str, name: str, px: int = 1600) -> Path:
    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_H,  # запас на блики/грязь при печати
        box_size=40,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    img = img.resize((px, px), resample=0)  # чёткие модули, без размытия
    out = OUT_DIR / f"qr-{name}.png"
    img.save(out)
    print(f"✓ {out}  ← {url}")
    return out


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        raise SystemExit(1)
    make(sys.argv[1], sys.argv[2])
