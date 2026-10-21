#!/usr/bin/env python3
"""
Пересборка серии «Кастинг» под крупную конструкцию 300 × 270 см.

Геометрия печатного файла (всё в одном полотне):

    ┌──────────┬──────────────────────────────────┬──────────┐
    │  ухо 30  │ загиб 10 │ ЛИЦО 220 × 250 │ загиб 10 │  ухо 30 │  300 см
    ├──────────┴──────────────────────────────────┴──────────┤
    │                    загиб 10 сверху                     │
    │                    ЛИЦО 220 × 250                     │  270 см
    │                    загиб 10 снизу                     │
    └────────────────────────────────────────────────────────┘

Уши — боковые части конструкции (по 40 см: 10 см загиб + 30 см возврат),
загибы уходят на подгиб к раме.

Что делает скрипт:
  1. Берёт исходники клиента и вычищает из них запечённые надписи
     (заголовки, QR, «Я звезда!») — фон восстанавливается интерполяцией
     по градиенту сцены.
  2. Собирает лицевую панель 220 × 250 см: фото сцены уходит вниз,
     наверху остаётся стена, туда ставятся свежие заголовок и QR.
  3. Разворачивает панель в полотно 300 × 270 см: уши и загибы — зеркальное
     продолжение краёв лица, поэтому фон идёт непрерывно.
  4. Отдаёт печатный мастер 300 dpi, 4:4:4 + производные версии.

Полотно собирается полосами в файл на диске (память не растёт),
финальный JPEG пишет libvips.

Запуск:
  python3 scripts/banners/build_300x270.py
  python3 scripts/banners/build_300x270.py --only kino
  python3 scripts/banners/build_300x270.py --bare      # без подписей, логотипа и QR
"""
from __future__ import annotations

import argparse
import gc
import mmap
import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

Image.MAX_IMAGE_PIXELS = None  # мастер 300 × 270 см — это 1.13 гигапикселя

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cv2  # noqa: E402

import edit_dv_production as edp  # noqa: E402  (общие приёмы: заливка фона, текст)
import jfif_density as jfif  # noqa: E402  (простановка dpi без перекодирования)

import pyvips  # noqa: E402
import segno  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
PRINT_DIR = ROOT / "banners/casting-series/print"
WEB_DIR = ROOT / "public/media/banners"
SOCIAL_DIR = WEB_DIR / "social"

DPI = 300
PX_CM = DPI / 2.54

CANVAS_W_CM, CANVAS_H_CM = 300, 270
EAR_CM, FOLD_CM = 40, 10

W = round(CANVAS_W_CM * PX_CM)
H = round(CANVAS_H_CM * PX_CM)
EAR = round(EAR_CM * PX_CM)
FOLD = round(FOLD_CM * PX_CM)
FACE_W = W - 2 * EAR
FACE_H = H - 2 * FOLD
FACE_X0, FACE_Y0 = EAR, FOLD
FACE_X1, FACE_Y1 = EAR + FACE_W, FOLD + FACE_H

QR_TARGET = "https://model.dvkino.ru"
MAJENTA = (150, 22, 74)
BAND = 1024  # высота полосы при сборке


def cm(v: float) -> int:
    return round(v * PX_CM)


# --------------------------------------------------------------------------
# Источники и чистка
# --------------------------------------------------------------------------
SOURCES = {
    "kino": PRINT_DIR / "banner-kasting-proby-v-kino-4608x8256.jpg",
    "pokaz": PRINT_DIR / "banner-kasting-modnyy-pokaz-5088x7584.jpg",
    "dv-production": PRINT_DIR / "banner-dv-production-original-6144x6144.jpg",
}

# Блоки с запечёнными надписями (координаты исходника) — вычищаются.
CLEAN = {
    "kino": {
        "title": (500, 640, 3990, 1630),
        "qr": (1160, 2010, 3450, 4320),
    },
    "pokaz": {
        # левый край блока выходит за «М» исходного заголовка (x = 818)
        "title": (760, 380, 4400, 1600),
        "qr": (1330, 1780, 3840, 4140),
    },
}

# С какой строки исходника начинается фотоблок (ниже вычищенного QR).
PHOTO_TOP = {"kino": 4400, "pokaz": 4200}


def clean_plate(key: str) -> np.ndarray:
    """Исходник без запечённых надписей."""
    arr = np.array(Image.open(SOURCES[key]).convert("RGB"))
    if key == "dv-production":
        return edp.repair(arr)
    spec = CLEAN[key]
    h, w = arr.shape[:2]
    mask = np.zeros((h, w), np.uint8)
    for box in (spec["title"], spec["qr"]):
        x0, y0, x1, y1 = box
        mask[y0:y1, x0:x1] = 255
    regions = [(spec["title"], "v"), (spec["qr"], "v")]
    return edp.build_background(arr, mask, regions)


# --------------------------------------------------------------------------
# Элементы: текст и QR
# --------------------------------------------------------------------------
def text_tile(lines, font_file, size, track, color=None, gradient=False, shadow=True):
    """Плитка с наборным текстом в финальном разрешении."""
    if isinstance(lines, str):
        lines = [lines]
    font = ImageFont.truetype(str(edp.FONTS / font_file), size)
    latin = edp.LATIN.get(font_file, font_file)
    fallback = ImageFont.truetype(str(edp.FONTS / latin), size)

    probe = ImageDraw.Draw(Image.new("L", (8, 8)))
    widths = []
    for line in lines:
        w = sum(probe.textlength(ch, font=font if ch not in edp.FALLBACK_CHARS else fallback)
                for ch in line)
        widths.append(w + track * max(0, len(line) - 1))
    line_h = int(size * 1.28)
    width = int(max(widths)) + int(size * 1.2)
    height = int(line_h * (len(lines) - 1) + size * 1.7)

    mask = Image.new("L", (width, height), 0)
    d = ImageDraw.Draw(mask)
    for i, line in enumerate(lines):
        x = (width - widths[i]) / 2
        y = size * 1.05 + i * line_h
        for ch in line:
            f = fallback if ch in edp.FALLBACK_CHARS else font
            d.text((x, y), ch, font=f, fill=255, anchor="ls")
            x += probe.textlength(ch, font=f) + track

    if gradient:
        layer = Image.new("RGB", (width, height))
        gd = ImageDraw.Draw(layer)
        for y in range(height):
            t = min(1.0, max(0.0, (y - size * 0.1) / (size * 1.5)))
            gd.line([(0, y), (width, y)], fill=tuple(
                int(edp.GOLD_TOP[c] + (edp.GOLD_BOTTOM[c] - edp.GOLD_TOP[c]) * t) for c in range(3)))
    else:
        layer = Image.new("RGB", (width, height), color or edp.CREAM)

    out = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    if shadow:
        blurred = mask.filter(ImageFilter.GaussianBlur(size * 0.06)).point(lambda v: int(v * 0.5))
        sh = Image.new("L", (width, height), 0)
        sh.paste(blurred, (0, int(size * 0.05)))
        out.paste(Image.new("RGBA", (width, height), edp.SHADOW + (255,)), (0, 0), sh)
    out.paste(layer, (0, 0), mask)
    return premultiply(out)


def premultiply(tile: Image.Image) -> Image.Image:
    """Альфа premultiplied — так считает композитинг."""
    r, g, b, a = tile.split()
    return Image.merge("RGBA", (ImageChops.multiply(r, a), ImageChops.multiply(g, a),
                                ImageChops.multiply(b, a), a))


def qr_tile(module_px: int) -> Image.Image:
    """QR в финальном разрешении: белые модули, фон прозрачный."""
    code = segno.make(QR_TARGET, error="m", version=3)
    m = code.matrix
    n = len(m)
    border = 4
    size = (n + border * 2) * module_px
    out = Image.new("RGBA", (size, size), (255, 255, 255, 0))
    img = Image.new("1", (n, n), 0)
    for y in range(n):
        for x in range(n):
            img.putpixel((x, y), 1 if m[y][x] else 0)
    img = img.resize((n * module_px, n * module_px), Image.NEAREST)
    out.paste(Image.new("RGBA", img.size, (255, 255, 255, 255)),
              (border * module_px, border * module_px), img.convert("L"))
    return out


def logo_block(mono: Image.Image, width: int) -> Image.Image:
    """Логотип: монограмма + подпись PRODUCTION, общей шириной width."""
    m = mono.resize((width, int(mono.height * width / mono.width)), Image.LANCZOS)
    # Монограмма приходит из макета 52 см и растягивается вчетверо —
    # лёгкая резкость по RGB возвращает чёткость края (альфа не трогаем).
    rgb = m.convert("RGB").filter(ImageFilter.UnsharpMask(radius=7, percent=110, threshold=3))
    m = Image.merge("RGBA", (*rgb.split(), m.getchannel("A")))

    # Подпись — латинский сабсет гарнитуры, ширина подгоняется трекингом.
    text = "PRODUCTION"
    size = int(width * 0.105)
    font = ImageFont.truetype(str(edp.FONTS / "Manrope-500-latin.ttf"), size)
    probe = ImageDraw.Draw(Image.new("L", (8, 8)))
    natural = sum(probe.textlength(ch, font=font) for ch in text)
    target = width * 0.94
    track = max(0, int((target - natural) / (len(text) - 1)))
    word = text_tile(text, "Manrope-500-latin.ttf", size, track, color=edp.CREAM, shadow=False)

    gap = int(width * 0.09)
    block = Image.new("RGBA", (width, m.height + gap + word.height), (0, 0, 0, 0))
    block.paste(m, ((width - m.width) // 2, 0), m)
    block.paste(word, ((width - word.width) // 2, m.height + gap), word)
    return block


def overlays_for(key: str, logo: Image.Image | None):
    """Слои с контентом: [(RGBA numpy, x, y)] в координатах лица."""
    items = []

    def add(img: Image.Image, x: int, y: int, name: str):
        items.append((np.array(img), int(x), int(y)))
        print(f"  слой {name}: {img.size[0]}×{img.size[1]} px "
              f"({img.size[0] / PX_CM:.0f}×{img.size[1] / PX_CM:.0f} см) @ {x},{y}")

    if key == "kino":
        title = text_tile(["КАСТИНГ НА ПРОБЫ", "В КИНО"], "Unbounded-700.ttf", cm(8.6), cm(0.8),
                          gradient=True)
        add(title, (FACE_W - title.width) // 2, cm(12.0), "title")
        add(qr_tile(cm(0.75)), (FACE_W - cm(0.75) * 37) // 2, cm(36.0), "qr")
    elif key == "pokaz":
        title = text_tile(["КАСТИНГ НА", "МОДНЫЙ ПОКАЗ"], "Unbounded-700.ttf", cm(10.4), cm(0.95),
                          gradient=True)
        add(title, (FACE_W - title.width) // 2, cm(14.0), "title")
        add(qr_tile(cm(0.95)), (FACE_W - cm(0.95) * 37) // 2, cm(46.0), "qr")
    else:
        if logo is not None:
            add(logo, cm(43.3), cm(20.3), "logo")
        desc = text_tile("ПРОДЮСЕРСЬКИЙ ЦЕНТР", "Unbounded-600.ttf", cm(7.34), cm(0.86),
                         gradient=True)
        add(desc, (FACE_W - desc.width) // 2, cm(65.0) - cm(7.34) * 1.05, "desc")
        brand = text_tile("ДВ ПРОДАКШЕН", "Unbounded-700.ttf", cm(12.0), cm(0.50), gradient=True)
        add(brand, (FACE_W - brand.width) // 2, cm(93.0) - cm(12.0) * 1.05, "brand")
        sub = text_tile("актёрско-модельная студия", "Manrope-500.ttf", cm(5.37), cm(0.72))
        add(sub, (FACE_W - sub.width) // 2, cm(124.5) - cm(5.37) * 1.05, "sub")
    return items


# --------------------------------------------------------------------------
# Геометрия лица
# --------------------------------------------------------------------------
def pad_mirror(arr: np.ndarray, top: int, bottom: int) -> np.ndarray:
    """Достраивает фон зеркалом сверху и снизу."""
    parts = []
    if top > 0:
        t = arr[:min(top, arr.shape[0])][::-1]
        if t.shape[0] < top:
            t = np.concatenate([np.repeat(t[:1], top - t.shape[0], axis=0), t], axis=0)
        parts.append(t)
    parts.append(arr)
    if bottom > 0:
        b = arr[-min(bottom, arr.shape[0]):][::-1]
        if b.shape[0] < bottom:
            b = np.concatenate([b, np.repeat(b[-1:], bottom - b.shape[0], axis=0)], axis=0)
        parts.append(b)
    return np.concatenate(parts, axis=0)


def face_segments(key: str, plate: np.ndarray):
    """Сегменты исходника → полосы лица: (src_y0, src_y1, dst_y0, dst_y1)."""
    sh = plate.shape[0]
    s = FACE_W / plate.shape[1]
    if key == "dv-production":
        src_h = int(round(sh * s))
        pad = max(0, int(round((FACE_H - src_h) / 2 / s)))
        plate = pad_mirror(plate, pad, pad)
        sh = plate.shape[0]
        h = int(round(sh * s))
        return plate, [(0, sh, 0, h)]
    photo_top = PHOTO_TOP[key]
    photo_h = int(round((sh - photo_top) * s))
    wall_h = FACE_H - photo_h
    wall_src = int(round(wall_h / s))
    segs = []
    y = 0
    for src_y0, src_y1 in ((0, wall_src), (photo_top, sh)):
        h = int(round((src_y1 - src_y0) * s))
        segs.append((src_y0, src_y1, y, y + h))
        y += h
    print(f"  {key}: стена {wall_h / PX_CM:.0f} см, фото {photo_h / PX_CM:.0f} см")
    return plate, segs


def resample(src: np.ndarray, src_y0: int, src_y1: int, out_w: int, out_h: int) -> Image.Image:
    """Полоса исходника [src_y0, src_y1) → (out_w, out_h)."""
    sh, sw = src.shape[:2]
    s = out_w / sw
    margin = 14
    sy0 = max(0, src_y0 - margin)
    sy1 = min(sh, src_y1 + margin)
    crop = Image.fromarray(src[sy0:sy1]).resize(
        (out_w, max(1, round((sy1 - sy0) * s))), Image.LANCZOS)
    off = round((src_y0 - sy0) * s)
    return crop.crop((0, off, out_w, min(crop.height, off + out_h)))


# --------------------------------------------------------------------------
# Сборка полотна
# --------------------------------------------------------------------------
def rss_mb() -> int:
    """Сколько памяти занял процесс."""
    return int(Path("/proc/self/status").read_text().split("VmRSS:")[1].split("kB")[0].strip()) // 1024


def sync(canvas: np.memmap) -> None:
    """Сбрасывает страницы полотна на диск и освобождает память."""
    canvas.flush()
    canvas._mmap.madvise(mmap.MADV_DONTNEED)


def match_seam(canvas: np.memmap, wall_end: int, ramp: int = 700) -> None:
    """Сводит тон стены и фотоблока, чтобы стык не читался линией."""
    if wall_end <= ramp:
        return
    a = canvas[FACE_Y0 + wall_end - 64:FACE_Y0 + wall_end].mean(axis=0).astype(np.float32)
    b = canvas[FACE_Y0 + wall_end:FACE_Y0 + wall_end + 64].mean(axis=0).astype(np.float32)
    diff = cv2.GaussianBlur((b - a).reshape(-1, 1, 3), (0, 0), 80).reshape(-1, 3)[FACE_X0:FACE_X1]
    for i, y in enumerate(range(wall_end - ramp, wall_end)):
        t = (i + 1) / ramp
        region = canvas[FACE_Y0 + y, FACE_X0:FACE_X1]
        region[:] = np.clip(region.astype(np.float32) + diff * t, 0, 255).astype(np.uint8)


def blend(canvas: np.ndarray, arr: np.ndarray, ox: int, oy: int, y0: int, y1: int) -> None:
    """Накладывает слой (RGBA, premultiplied) на полосу лица."""
    oy0, oy1 = max(oy, y0), min(oy + arr.shape[0], y1)
    if oy1 <= oy0:
        return
    ox0, ox1 = max(ox, 0), min(ox + arr.shape[1], FACE_W)
    if ox1 <= ox0:
        return
    sub = arr[oy0 - oy:oy1 - oy, ox0 - ox:ox1 - ox]
    a = sub[:, :, 3:4].astype(np.float32) / 255.0
    region = canvas[FACE_Y0 + oy0:FACE_Y0 + oy1, FACE_X0 + ox0:FACE_X0 + ox1]
    region[:] = (sub[:, :, :3].astype(np.float32) * a
                 + region.astype(np.float32) * (1.0 - a)).astype(np.uint8)


def build_face(key: str, plate: np.ndarray, layers, canvas: np.memmap) -> None:
    """Заполняет лицевую панель 220 × 250 см."""
    plate, segs = face_segments(key, plate)
    wall_end = segs[0][3] if len(segs) > 1 else None
    s = FACE_W / plate.shape[1]

    for src_y0, src_y1, dst_y0, dst_y1 in segs:
        for y0 in range(dst_y0, dst_y1, BAND):
            y1 = min(dst_y1, y0 + BAND)
            hh = y1 - y0
            top = src_y0 + int(round((y0 - dst_y0) / s))
            bot = src_y0 + int(round((y1 - dst_y0) / s))
            img = resample(plate, top, bot, FACE_W, hh)
            canvas[FACE_Y0 + y0:FACE_Y0 + y1, FACE_X0:FACE_X1] = np.asarray(img)
            for arr, ox, oy in layers:
                blend(canvas, arr, ox, oy, y0, y1)
            sync(canvas)
        print(f"  полоса лица {dst_y0}–{dst_y1} готова (RSS {rss_mb()} МБ)")
    if wall_end:
        match_seam(canvas, wall_end)
        sync(canvas)
        print(f"  стык стены и фото сведён по тону (RSS {rss_mb()} МБ)")


def finish_canvas(canvas: np.memmap) -> None:
    """Достраивает полотно: загибы сверху/снизу и уши по бокам."""
    # Загибы: зеркало верхних и нижних строк лица.
    for dst_y0, src_y0 in ((0, FOLD), (FACE_Y1, FACE_Y1 - FOLD)):
        for k in range(0, FOLD, BAND):
            k1 = min(FOLD, k + BAND)
            canvas[dst_y0 + k:dst_y0 + k1] = canvas[src_y0 + k:src_y0 + k1][::-1]
        sync(canvas)
    print(f"  загибы готовы (RSS {rss_mb()} МБ)")

    # Уши: зеркало крайних полос лица.
    for y0 in range(0, H, BAND):
        y1 = min(H, y0 + BAND)
        canvas[y0:y1, 0:EAR] = canvas[y0:y1, FACE_X0:FACE_X0 + EAR][:, ::-1]
        canvas[y0:y1, FACE_X1:W] = canvas[y0:y1, FACE_X1 - EAR:FACE_X1][:, ::-1]
        sync(canvas)
        print(f"  уши {y0}–{y1} (RSS {rss_mb()} МБ)")


def write_master(raw: Path, out: Path, quality: int = 92) -> None:
    """Пишет печатный мастер из сырого полотна (потоково, через libvips)."""
    img = pyvips.Image.rawload(str(raw), W, H, 3, access="sequential")
    img.write_to_file(str(out), Q=quality, subsample_mode="off", strip=True)
    dpi = jfif.ensure_dpi(out, DPI)
    print(f"  мастер: {out.name} {W}×{H} px ({W / PX_CM:.0f}×{H / PX_CM:.0f} см, "
          f"{out.stat().st_size // 1024 // 1024} МБ, Q{quality}, {dpi})")


def build_derivatives(raw: Path, key: str, suffix: str = "") -> None:
    """Web- и social-версии — те же параметры, что у всей серии."""
    img = pyvips.Image.rawload(str(raw), W, H, 3, access="sequential")
    WEB_DIR.mkdir(parents=True, exist_ok=True)
    SOCIAL_DIR.mkdir(parents=True, exist_ok=True)

    web = img.resize(1600 / W, kernel="lanczos3")
    web.write_to_file(str(WEB_DIR / f"{key}-300x270{suffix}.jpg"), Q=84, strip=True)
    web.write_to_file(str(WEB_DIR / f"{key}-300x270{suffix}.webp"), Q=80, strip=True)

    bg = [float(c.avg()) for c in img.crop(0, 0, 1, 1).bandsplit()]
    for name, tw, th in (("1080x1920", 1080, 1920), ("1080x1350", 1080, 1350),
                         ("1080x1080", 1080, 1080), ("1920x1080", 1920, 1080)):
        scale = min(tw / W, th / H)
        nw, nh = round(W * scale), round(H * scale)
        small = img.resize(scale, kernel="lanczos3")
        small = small.embed((tw - nw) // 2, (th - nh) // 2, tw, th,
                            extend="background", background=bg)
        small.write_to_file(str(SOCIAL_DIR / f"{key}-300x270{suffix}-{name}.jpg"),
                            Q=86, strip=True)
    print(f"  производные: {key}-300x270{suffix} (web 1600 px + 4 social)")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=list(SOURCES), help="собрать только один макет")
    ap.add_argument("--bare", action="store_true",
                    help="чистые макеты: без подписей, логотипа и QR-кодов")
    ap.add_argument("--quality", type=int, default=92,
                    help="качество JPEG мастера (92 — максимум, 78 — влезает в лимит GitHub)")
    ap.add_argument("--keep-work", action="store_true")
    args = ap.parse_args()

    pyvips.cache_set_max_mem(256 * 1024 * 1024)
    pyvips.cache_set_max(80)

    suffix = "-bare" if args.bare else ""
    keys = [args.only] if args.only else list(SOURCES)
    work = Path(tempfile.mkdtemp(prefix="banners300-"))
    try:
        for key in keys:
            print(f"→ {key}{' (без подписей)' if args.bare else ''}")
            plate = clean_plate(key)
            logo = None
            layers = []
            if not args.bare:
                if key == "dv-production":
                    arr = np.array(Image.open(SOURCES[key]).convert("RGB"))
                    mono, _ = edp.extract_logo(arr)
                    logo = logo_block(mono, cm(32))
                layers = overlays_for(key, logo)

            raw = work / f"{key}_canvas.raw"
            canvas = np.memmap(raw, dtype=np.uint8, mode="w+", shape=(H, W, 3))
            build_face(key, plate, layers, canvas)
            del plate, layers
            gc.collect()
            finish_canvas(canvas)
            out = PRINT_DIR / f"banner-{key}-300x270{suffix}.jpg"
            write_master(raw, out, args.quality)
            build_derivatives(raw, key, suffix)
            del canvas
            raw.unlink(missing_ok=True)
    finally:
        if not args.keep_work:
            shutil.rmtree(work, ignore_errors=True)
        else:
            print("временные файлы:", work)
    return 0


if __name__ == "__main__":
    sys.exit(main())
