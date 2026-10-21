#!/usr/bin/env python3
"""Печатная обработка одиночного кадра (сцена) под баннер 300 dpi.

Задача: взять клиентский кадр, не меняя композицию, поднять качество под
печать (чистка шума, апскейл, резкость, зерно против бандинга) и подтянуть
оттенки к фирменному мадженте бренда (#971a81).

Пайплайн:
  1. clean()   — хроматическая шумоподавление (CbCr) + лёгкая по яркости,
                  звёзды/лучи/контуры остаются резкими.
  2. grade()   — HSV-тяга оттенков к целевому цвету (по умолчанию #971a81)
                  с защитой золота лучей и красного ковра; лёгкий CLAHE.
  3. upscale() — LANCZOS-апскейл полосами в .raw (memmap), детализация
                  отдельным слоем (чтобы не «замылить» микро-контраст).
  4. finish()  — unsharp mask + плёночное зерно/дизер (анти-бандинг).
  5. Сохранение: sRGB JPEG 4:4:4 300 dpi + CMYK TIFF (FOGRA39) + превью.

Пример:
  python3 scripts/banners/print_stage.py \
      --src /tmp/arena-coding-uploads/1792567453.png \
      --out-dir /home/user/print-stage --width-cm 220
"""

from __future__ import annotations

import argparse
import math
import shutil
import struct
import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np
import pyvips
from PIL import Image, ImageFilter

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts" / "banners"))
sys.path.insert(0, str(REPO / "scripts"))

from jfif_density import ensure_dpi  # noqa: E402  (плотность JPEG вручную)

ICC_DIR = Path(__file__).resolve().parent / "icc"
DPI = 300
PX_CM = DPI / 2.54


# ---------------------------------------------------------------- утилиты ---

def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def smoothstep(edge0: float, edge1: float, x: np.ndarray) -> np.ndarray:
    t = np.clip((x - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def rss_mb() -> int:
    try:
        with open("/proc/self/status", encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) // 1024
    except OSError:
        pass
    return 0


# ------------------------------------------------------------- исходник ------

def load_source(path: Path) -> np.ndarray:
    """Читает кадр в float32 0..1 (без изменения геометрии)."""
    img = Image.open(path)
    if img.mode != "RGB":
        img = img.convert("RGB")
    return np.asarray(img, dtype=np.float32) / 255.0


def clean(src: np.ndarray, chroma: float = 0.85, luma: float = 0.45) -> np.ndarray:
    """Шумоподавление: цвет гасим сильнее, яркость — осторожно (звёзды, лучи)."""
    ycrcb = cv2.cvtColor(src, cv2.COLOR_RGB2YCrCb)
    y, cr, cb = ycrcb[:, :, 0], ycrcb[:, :, 1], ycrcb[:, :, 2]
    if chroma > 0:
        k = 5
        cr_s = cv2.GaussianBlur(cr, (k, k), 0)
        cb_s = cv2.GaussianBlur(cb, (k, k), 0)
        cr = cr * (1 - chroma) + cr_s * chroma
        cb = cb * (1 - chroma) + cb_s * chroma
    if luma > 0:
        y_s = cv2.bilateralFilter(y, 5, 14, 3)
        y = y * (1 - luma) + y_s * luma
    out = cv2.cvtColor(np.dstack([y, cr, cb]), cv2.COLOR_YCrCb2RGB)
    return np.clip(out, 0.0, 1.0)


def local_contrast(src: np.ndarray, amount: float = 0.45,
                   clip: float = 1.25, grid: int = 10) -> np.ndarray:
    """Мягкий CLAHE по яркости — возвращает «печатную» глубину после апскейла."""
    if amount <= 0:
        return src
    lab = cv2.cvtColor((np.clip(src, 0, 1) * 255).astype(np.uint8), cv2.COLOR_RGB2LAB)
    cl = cv2.createCLAHE(clipLimit=clip, tileGridSize=(grid, grid))
    lab[:, :, 0] = cl.apply(lab[:, :, 0])
    out = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB).astype(np.float32) / 255.0
    return np.clip(src * (1 - amount) + out * amount, 0.0, 1.0)


# --------------------------------------------------------------- грейд -------

def grade(src: np.ndarray, target: str = "971a81", hue_pull: float = 0.55,
          sat_boost: float = 0.15, tint: float = 0.10,
          protect_gold: tuple[float, float] = (14.0, 66.0)) -> np.ndarray:
    """Тянет оттенки к фирменному цвету, сохраняя золото лучей и красный ковёр.

    Золото (H 14…66°) и «тёплая дымка» лучей (H 100…240°) не трогаем —
    иначе лучи станут маджентовыми. Маджента-семейство (H 280…348°)
    тянем к целевому тону и подсыщаем.
    """
    img8 = (np.clip(src, 0, 1) * 255).astype(np.uint8)
    hsv = cv2.cvtColor(img8, cv2.COLOR_RGB2HSV)      # uint8: H 0..179, S/V 0..255
    h = hsv[:, :, 0].astype(np.float32) * 2.0        # 0..360
    s = hsv[:, :, 1].astype(np.float32) / 255.0

    # вес маджента-семейства: мягкие края, чтобы не было швов
    w = smoothstep(268.0, 300.0, h) * (1.0 - smoothstep(340.0, 356.0, h))
    w *= smoothstep(0.08, 0.22, s)

    # тёплая дымка и золото — защита
    warm = smoothstep(78.0, 104.0, h) * (1.0 - smoothstep(250.0, 276.0, h))
    w *= (1.0 - warm)

    # основной ход: Lab-тяга a/b к фирменному цвету (светлота не трогаем —
    # тоновая структура кадра остаётся как в оригинале)
    lab = cv2.cvtColor(img8, cv2.COLOR_RGB2LAB).astype(np.float32)
    tgt = np.array([[hex_to_rgb(target)]], dtype=np.uint8)
    t_lab = cv2.cvtColor(tgt, cv2.COLOR_RGB2LAB)[0, 0].astype(np.float32)
    f = np.clip(hue_pull, 0.0, 1.0) * w
    lab[:, :, 1] += (t_lab[1] - lab[:, :, 1]) * f
    lab[:, :, 2] += (t_lab[2] - lab[:, :, 2]) * f
    out = cv2.cvtColor(np.clip(lab, 0, 255).astype(np.uint8), cv2.COLOR_LAB2RGB).astype(np.float32) / 255.0

    # лёгкое насыщение маджента-семейства
    if sat_boost > 0:
        hsv = cv2.cvtColor((out * 255).astype(np.uint8), cv2.COLOR_RGB2HSV)
        s2 = np.clip(hsv[:, :, 1].astype(np.float32) / 255.0 * (1.0 + sat_boost * w), 0.0, 1.0)
        hsv[:, :, 1] = s2 * 255.0
        out = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB).astype(np.float32) / 255.0

    # сквозная лёгкая «маджента-заливка» в тенях/полутонах (как split-tone)
    if tint > 0:
        mag = np.array(hex_to_rgb(target), dtype=np.float32) / 255.0
        lum = 0.2126 * out[:, :, 0] + 0.7152 * out[:, :, 1] + 0.0722 * out[:, :, 2]
        weight = tint * np.clip(1.0 - lum, 0.0, 1.0) ** 1.2
        factor = 1.0 + weight[:, :, None] * (mag[None, None, :] * 1.9 - 1.0)
        tinted = np.clip(out * factor, 0.0, 1.0)
        out = np.clip(out * (1.0 - weight[:, :, None] * 0.55)
                      + tinted * (weight[:, :, None] * 0.55), 0.0, 1.0)
    return out


# --------------------------------------------------------------- апскейл -----

def upscale(src: np.ndarray, out_w: int, out_h: int, raw: Path,
            band: int = 58, detail: float = 0.85) -> np.memmap:
    """LANCZOS-апскейл полосами + отдельный слой деталей (сохраняет микро-контраст)."""
    H, W = src.shape[:2]
    scale = out_w / W
    canvas = np.memmap(raw, dtype=np.uint8, mode="w+", shape=(out_h, out_w, 3))

    det = src - cv2.GaussianBlur(src, (0, 0), 1.15)
    rng = np.random.default_rng(20261021)

    margin = 4
    for y0 in range(0, H, band):
        y1 = min(H, y0 + band)
        oy0, oy1 = int(round(y0 * scale)), int(round(y1 * scale))
        sy0, sy1 = max(0, y0 - margin), min(H, y1 + margin)
        bh = int(round((sy1 - sy0) * scale))

        chunk = (np.clip(src[sy0:sy1], 0, 1) * 255).astype(np.uint8)
        big = np.asarray(Image.fromarray(chunk).resize((out_w, bh), Image.LANCZOS))

        # слой деталей: микро-контраст, который LANCZOS сглаживает
        dchunk = (np.clip(det[sy0:sy1] * 128 + 128, 0, 255)).astype(np.uint8)
        dbig = np.asarray(Image.fromarray(dchunk).resize((out_w, bh), Image.BICUBIC))
        big = np.clip(big.astype(np.int16) + ((dbig.astype(np.int16) - 128) * detail / 64.0),
                      0, 255).astype(np.uint8)
        del dchunk, dbig

        cut0 = oy0 - int(round(sy0 * scale))
        cut1 = cut0 + (oy1 - oy0)
        big = big[cut0:cut1]

        # резкость: unsharp mask по полосе
        pil = Image.fromarray(big).filter(ImageFilter.UnsharpMask(radius=4.0, percent=62, threshold=2))
        big = np.asarray(pil)
        del pil

        # плёночное зерно + дизер против бандинга на больших площадях
        noise = rng.normal(0.0, 1.05, big.shape[:2]).astype(np.float32)
        big = np.clip(big.astype(np.float32) + noise[:, :, None], 0, 255).astype(np.uint8)
        del noise

        canvas[oy0:oy1] = big
        canvas.flush()
        del big
        print(f"  полоса {oy0}–{oy1} / {out_h} (RSS {rss_mb()} МБ)", flush=True)
    return canvas


# ---------------------------------------------------------------- вывод ------

def write_jpeg(raw: Path, out: Path, w: int, h: int, quality: int = 95) -> None:
    img = pyvips.Image.rawload(str(raw), w, h, 3, access="sequential")
    img.write_to_file(str(out), Q=quality, subsample_mode="off", strip=True)
    ensure_dpi(out, DPI)
    print(f"  sRGB-мастер: {out.name} {w}×{h} px, "
          f"{w / PX_CM:.0f}×{h / PX_CM:.0f} см, {out.stat().st_size // 1024 // 1024} МБ, Q{quality}")


def write_cmyk(raw: Path, out: Path, w: int, h: int, profile: Path) -> None:
    img = pyvips.Image.rawload(str(raw), w, h, 3, access="sequential")
    out_img = img.icc_transform(
        str(profile), pcs="lab", intent="relative", black_point_compensation=True,
        input_profile="srgb", depth=8,
    )
    out_img.write_to_file(str(out), compression="lzw", predictor="horizontal")
    print(f"  CMYK FOGRA39: {out.name} {w}×{h} px, "
          f"{out.stat().st_size // 1024 // 1024} МБ")


def write_preview(raw: Path, out: Path, w: int, h: int, px: int = 1600) -> None:
    img = pyvips.Image.rawload(str(raw), w, h, 3, access="sequential")
    small = img.resize(px / w, kernel="lanczos3")
    small.write_to_file(str(out), Q=88, strip=True)
    print(f"  превью: {out.name} {small.width}×{small.height}")


def write_preview_from_array(arr: np.ndarray, out: Path) -> None:
    Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8)).save(out, quality=92)


# ---------------------------------------------------------------- main -------

def main() -> int:
    ap = argparse.ArgumentParser(description="Печатная обработка кадра под баннер 300 dpi")
    ap.add_argument("--src", type=Path, required=True, help="исходный кадр")
    ap.add_argument("--out-dir", type=Path, default=Path("/home/user/print-stage"))
    ap.add_argument("--width-cm", type=float, default=220.0,
                    help="ширина печатного мастера в см (лицо баннера — 220 см)")
    ap.add_argument("--target", default="971a81", help="целевой оттенок (HEX)")
    ap.add_argument("--hue-pull", type=float, default=0.55)
    ap.add_argument("--sat-boost", type=float, default=0.15)
    ap.add_argument("--tint", type=float, default=0.10)
    ap.add_argument("--detail", type=float, default=0.85)
    ap.add_argument("--quality", type=int, default=95)
    ap.add_argument("--preview-only", action="store_true",
                    help="только превью исходного кадра (без апскейла)")
    ap.add_argument("--no-cmyk", action="store_true")
    ap.add_argument("--profile", type=Path,
                    default=ICC_DIR / "Coated_Fogra39L_VIGC_300.icc")
    args = ap.parse_args()

    pyvips.cache_set_max_mem(256 * 1024 * 1024)
    pyvips.cache_set_max(60)

    src = load_source(args.src)
    H, W = src.shape[:2]
    print(f"исходник: {args.src.name} {W}×{H} px")

    if args.preview_only:
        work = clean(src)
        work = local_contrast(work)
        work = grade(work, args.target, args.hue_pull, args.sat_boost, args.tint)
        args.out_dir.mkdir(parents=True, exist_ok=True)
        write_preview_from_array(work, args.out_dir / "stage-preview-graded.jpg")
        return 0

    out_w = int(round(args.width_cm * PX_CM))
    out_h = int(round(out_w * H / W))
    args.out_dir.mkdir(parents=True, exist_ok=True)
    work_dir = Path(tempfile.mkdtemp(prefix="stage-"))
    raw = work_dir / "stage.raw"
    try:
        cleaned = clean(src)
        cleaned = local_contrast(cleaned)
        graded = grade(cleaned, args.target, args.hue_pull, args.sat_boost, args.tint)
        print(f"грейд к #{args.target}: hue-pull {args.hue_pull}, sat +{args.sat_boost}")
        upscale(graded, out_w, out_h, raw, detail=args.detail)

        base = "stage-print-xl"
        write_jpeg(raw, args.out_dir / f"{base}-300dpi.jpg", out_w, out_h, args.quality)
        write_preview(raw, args.out_dir / f"{base}-preview.jpg", out_w, out_h)
        if not args.no_cmyk and args.profile.exists():
            write_cmyk(raw, args.out_dir / f"{base}-300dpi-cmyk-fogra39.tif", out_w, out_h,
                       args.profile)
        else:
            print("  CMYK пропущен (нет профиля)")
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)
    print("готово")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
