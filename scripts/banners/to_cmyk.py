#!/usr/bin/env python3
"""
Конвертация печатных мастеров в CMYK по профилю FOGRA39.

Мастера лежат в sRGB (конвертацию в CMYK обычно делает типография со своим
профилем). Если типография требует готовый CMYK — этот скрипт собирает
такие файлы: TIFF 8 бит/канал, профиль встроен в файл, рендеринг
относительный с компенсацией чёрной точки.

Полотно 300 × 270 см — это 1,13 гигапикселя, поэтому конвертация идёт
потоково через libvips (по полосам), а не в памяти целиком.

Профили:
  • `icc/Coated_Fogra39L_VIGC_300.icc` — X-Rite / ECI, Coated FOGRA39 (L),
    300 % TAC (им конвертированы выпущенные мастера);
  • `icc/craft-coated-fogra39.icc` — CC0, FOGRA39 по данным Fogra
    (запасной вариант, в репозитории лежит по умолчанию).

Запуск:
  python3 scripts/banners/to_cmyk.py --profile scripts/banners/icc/Coated_Fogra39L_VIGC_300.icc
  python3 scripts/banners/to_cmyk.py --only kino --out /home/user/print-cmyk
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pyvips

ROOT = Path(__file__).resolve().parents[2]
PRINT_DIR = ROOT / "banners/casting-series/print"
ICC_DIR = Path(__file__).resolve().parent / "icc"

# Мастера обеих концепций: относительный путь → подпись.
TARGETS = {
    "banner-kino-300x270.jpg": "сценическая · пробы в кино",
    "banner-pokaz-300x270.jpg": "сценическая · модный показ",
    "banner-dv-production-300x270.jpg": "сценическая · ДВ ПРОДАКШЕН",
    "sheet/banner-kino-300x270.jpg": "кастинг-лист · пробы в кино",
    "sheet/banner-pokaz-300x270.jpg": "кастинг-лист · модный показ",
    "sheet/banner-dv-production-300x270.jpg": "кастинг-лист · ДВ ПРОДАКШЕН",
}


def convert(src: Path, dst: Path, profile: Path, intent: str = "relative",
            compression: str = "lzw") -> None:
    """sRGB → CMYK (профиль FOGRA39) → TIFF."""
    im = pyvips.Image.new_from_file(str(src), access="sequential")
    out = im.icc_transform(
        str(profile),
        pcs="lab",
        intent=intent,
        black_point_compensation=True,
        embedded=False,
        input_profile="srgb",
        depth=8,
    )
    dst.parent.mkdir(parents=True, exist_ok=True)
    out.write_to_file(str(dst), compression=compression, predictor="horizontal",
                      pyramid=False)
    print(f"  {dst.name}: CMYK, {out.width}×{out.height}, "
          f"{dst.stat().st_size // 1024 // 1024} МБ")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", type=Path, default=ICC_DIR / "craft-coated-fogra39.icc",
                    help="ICC-профиль CMYK (по умолчанию CC0 FOGRA39 в scripts/banners/icc/)")
    ap.add_argument("--out", type=Path, default=ROOT / "banners/casting-series/print/cmyk",
                    help="куда складывать CMYK-файлы")
    ap.add_argument("--only", help="собрать один файл (имя мастера, например kino)")
    ap.add_argument("--intent", default="relative",
                    choices=("relative", "perceptual", "saturation", "absolute"))
    args = ap.parse_args()

    if not args.profile.exists():
        print(f"Нет профиля: {args.profile}", file=sys.stderr)
        return 1

    from PIL import ImageCms
    prof = ImageCms.getOpenProfile(str(args.profile))
    print(f"Профиль: {ImageCms.getProfileDescription(prof).strip()} "
          f"({args.profile.name})")
    print(f"Намерение: {args.intent}, компенсация чёрной точки — вкл.\n")

    for rel, note in TARGETS.items():
        src = PRINT_DIR / rel
        if not src.exists():
            print(f"Нет мастера: {src}")
            continue
        if args.only and args.only not in rel:
            continue
        print(f"→ {note}")
        stem = rel.replace("/", "-").replace(".jpg", "")
        dst = args.out / f"{stem}-cmyk-fogra39.tif"
        convert(src, dst, args.profile, args.intent)
    return 0


if __name__ == "__main__":
    sys.exit(main())
