#!/usr/bin/env python3
"""
Правка квадратного макета серии «Кастинг» по правкам клиента.

Было:  «Я звезда!» + крупный логотип по центру + подпись PRODUCTION.
Стало: логотип перенесён в верхний левый угол, заголовок —
        «Продюсерський центр ДВ ПРОДАКШЕН», по центру —
        «актёрско-модельная студия».

Как это сделано:
  1. Из исходника вырезается логотип (монограмма + PRODUCTION) по маске
     «золото», с обратным premultiply — без маджентовой каймы.
  2. Старый заголовок, монограмма и подпись PRODUCTION удаляются: фон
     восстанавливается полиномиальной моделью (степень 3) + сглаженным
     остатком + зерном, подобранным по фону.
  3. Логотип ставится в верхний угол, новый заголовок и подпись рисуются
     в стиле исходника: золотой градиент, мягкая тень.

Запуск:
  python3 scripts/banners/edit_dv_production.py            # печатный мастер
  python3 scripts/banners/edit_dv_production.py --preview  # + превью 1600 px
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[2]
PRINT_DIR = ROOT / "banners/casting-series/print"
SOURCE = PRINT_DIR / "banner-dv-production-original-6144x6144.jpg"
OUT = PRINT_DIR / "banner-dv-production-6144x6144.jpg"
FONTS = Path(__file__).resolve().parent / "fonts"

CANVAS = 6144
DPI = 300

# Блоки в исходнике (координаты мастера 6144×6144). Границы взяты с запасом
# на падающую тень букв — иначе вокруг заливки остаётся тёмный ореол.
HEAD_BOX = (1724, 791, 4420, 1396)     # «Я звезда!»
MONO_BOX = (2174, 1584, 4118, 3015)    # монограмма
WORD_BOX = (2199, 3113, 4029, 3430)    # «PRODUCTION»

# Новая композиция.
LOGO_SCALE = 0.50
LOGO_X, LOGO_Y = 1210, 150

DESC_TEXT = "ПРОДЮСЕРСЬКИЙ ЦЕНТР"
DESC_FONT, DESC_SIZE, DESC_TRACK, DESC_BASELINE = "Unbounded-600.ttf", 205, 24, 1400
BRAND_TEXT = "ДВ ПРОДАКШЕН"
BRAND_FONT, BRAND_SIZE, BRAND_TRACK, BRAND_BASELINE = "Unbounded-700.ttf", 335, 14, 2180
SUB_TEXT = "актёрско-модельная студия"
SUB_FONT, SUB_SIZE, SUB_TRACK, SUB_BASELINE = "Manrope-500.ttf", 150, 20, 3060

GOLD_TOP, GOLD_BOTTOM = (248, 226, 180), (196, 142, 58)
CREAM = (246, 239, 228)
SHADOW = (48, 8, 34)

# Знаки, которых нет в кириллическом сабсете, берём из латинского.
FALLBACK_CHARS = {"-", "–", "—", "‑"}
LATIN = {
    "Unbounded-600.ttf": "Unbounded-600-latin.ttf",
    "Unbounded-700.ttf": "Unbounded-700-latin.ttf",
    "Manrope-500.ttf": "Manrope-500-latin.ttf",
}


# --------------------------------------------------------------------------
# Фон
# --------------------------------------------------------------------------
def _smooth_axis0(v: np.ndarray, sigma: float) -> np.ndarray:
    """Сглаживание профиля вдоль оси 0 (гауссово, раздельное по каналам)."""
    k = int(sigma * 4) | 1
    x = np.arange(k) - k // 2
    ker = np.exp(-(x ** 2) / (2 * sigma ** 2))
    ker /= ker.sum()
    out = np.empty_like(v)
    for c in range(v.shape[1]):
        out[:, c] = np.convolve(v[:, c], ker, mode="same")
    return out


def _directional_fill(arr: np.ndarray, box, axis: str = "v") -> np.ndarray:
    """
    Заливка прямоугольника фоновым градиентом.

    Ось 'v': для каждой колонки берутся чистые строки над и под блоком,
    между ними — плавный переход (smoothstep). Фон сцены меняется прежде
    всего сверху вниз (лучи сверху гаснут), поэтому вертикальная
    интерполяция попадает в тон окружения, а горизонтальная дала бы
    «залитый» прямоугольник.
    """
    h, w = arr.shape[:2]
    x0, y0, x1, y1 = box
    if axis == "v":
        top = np.median(arr[max(0, y0 - 40):y0, x0:x1].astype(np.float32), axis=0)
        bot = np.median(arr[y1:min(h, y1 + 40), x0:x1].astype(np.float32), axis=0)
        # сглаживаем профили по горизонтали — убираем «полосы» от бликов
        top = _smooth_axis0(top, 18)
        bot = _smooth_axis0(bot, 18)
        t = ((np.arange(y0, y1) - y0 + 0.5) / (y1 - y0)).reshape(-1, 1, 1)
        t = t * t * (3 - 2 * t)
        return top[None, :, :] * (1 - t) + bot[None, :, :] * t
    left = np.median(arr[y0:y1, max(0, x0 - 40):x0].astype(np.float32), axis=1)
    right = np.median(arr[y0:y1, x1:min(w, x1 + 40)].astype(np.float32), axis=1)
    left = _smooth_axis0(left, 18)
    right = _smooth_axis0(right, 18)
    t = ((np.arange(x0, x1) - x0 + 0.5) / (x1 - x0)).reshape(1, -1, 1)
    t = t * t * (3 - 2 * t)
    return left[:, None, :] * (1 - t) + right[:, None, :] * t


def build_background(arr: np.ndarray, mask: np.ndarray, regions) -> np.ndarray:
    """Собирает новый фон: вырезанные блоки заливаются градиентом сцены."""
    h, w = arr.shape[:2]
    out = arr.astype(np.float32)

    for box, axis in regions:
        x0, y0, x1, y1 = box
        fill = _directional_fill(arr, box, axis)
        # По краям блока заливка плавно сходит с исходным фоном —
        # так не остаётся видимой рамки.
        band = 70
        ramp = np.ones(x1 - x0, np.float32)
        ramp[:band] = np.linspace(0, 1, band, dtype=np.float32)
        ramp[-band:] = np.linspace(1, 0, band, dtype=np.float32)
        ramp = (ramp * ramp * (3 - 2 * ramp)).reshape(1, -1, 1)
        blended = out[y0:y1, x0:x1] * (1 - ramp) + fill * ramp
        out[y0:y1, x0:x1] = blended

    # Зерно фона — по образцу чистых участков.
    hole = mask > 0
    hsv = cv2.cvtColor(arr, cv2.COLOR_RGB2HSV)
    grain = float(np.std(arr[(~hole) & (hsv[:, :, 2] < 215)][:400000].astype(np.float32)))
    del hsv
    rng = np.random.default_rng(21)
    for ch in range(3):
        noise = rng.normal(0, grain * 0.6, size=(h, w)).astype(np.float32)
        layer = out[:, :, ch]
        layer[hole] += noise[hole]
        out[:, :, ch] = layer
    return np.clip(out, 0, 255).astype(np.uint8)


def repair(arr: np.ndarray) -> np.ndarray:
    """Убирает «Я звезда!», монограмму и PRODUCTION, восстанавливает фон."""
    h, w = arr.shape[:2]
    mask = np.zeros((h, w), np.uint8)
    for box in (HEAD_BOX, MONO_BOX, WORD_BOX):
        x0, y0, x1, y1 = box
        mask[y0:y1, x0:x1] = 255
    regions = (
        (HEAD_BOX, "v"),
        (MONO_BOX, "v"),
        (WORD_BOX, "v"),
    )
    return build_background(arr, mask, regions)


# --------------------------------------------------------------------------
# Логотип
# --------------------------------------------------------------------------
def extract_logo(arr: np.ndarray) -> tuple[Image.Image, Image.Image]:
    """Достаёт монограмму и подпись PRODUCTION как RGBA (с обрезкой по альфе)."""
    hsv = cv2.cvtColor(arr, cv2.COLOR_RGB2HSV)

    def cut(box, keep):
        x0, y0, x1, y1 = box
        sub = arr[y0:y1, x0:x1].astype(np.float32)
        m = keep(hsv[y0:y1, x0:x1]).astype(np.uint8) * 255
        alpha = cv2.GaussianBlur(m, (0, 0), 4).astype(np.float32) / 255.0
        bgpix = sub[alpha < 0.2]
        bg = np.median(bgpix, axis=0) if len(bgpix) else sub.mean(axis=(0, 1))
        a = np.clip(alpha, 0.12, 1.0)[..., None]
        rgb = np.clip((sub - bg * (1 - a)) / a, 0, 255)
        rgba = np.dstack([rgb, alpha * 255]).astype(np.uint8)
        img = Image.fromarray(rgba, "RGBA")
        # обрезка по содержимому
        bbox = img.getbbox()
        return img.crop(bbox) if bbox else img

    mono = cut(MONO_BOX, lambda h: (h[:, :, 0] >= 10) & (h[:, :, 0] <= 50)
               & (h[:, :, 1] >= 45) & (h[:, :, 2] >= 35))
    word = cut(WORD_BOX, lambda h: (h[:, :, 2] > 165) & (h[:, :, 1] < 90))
    return mono, word


def place_logo(bg: Image.Image, mono: Image.Image, word: Image.Image) -> Image.Image:
    scale = LOGO_SCALE
    m = mono.resize((int(mono.width * scale), int(mono.height * scale)), Image.LANCZOS)
    w_img = word.resize((int(word.width * scale), int(word.height * scale)), Image.LANCZOS)

    block_w = max(m.width, w_img.width)
    m_x = LOGO_X + (block_w - m.width) // 2
    m_y = LOGO_Y
    w_x = LOGO_X + (block_w - w_img.width) // 2
    w_y = LOGO_Y + m.height + 86

    # Тень повторяет форму логотипа, а не его прямоугольник.
    alpha = Image.new("L", bg.size, 0)
    alpha.paste(m.getchannel("A"), (m_x, m_y))
    alpha.paste(w_img.getchannel("A"), (w_x, w_y))
    shadow = alpha.filter(ImageFilter.GaussianBlur(30)).point(lambda v: int(v * 0.42))
    bg = Image.composite(Image.new("RGB", bg.size, SHADOW), bg, shadow)

    bg.paste(m, (m_x, m_y), m)
    bg.paste(w_img, (w_x, w_y), w_img)
    return bg


# --------------------------------------------------------------------------
# Текст
# --------------------------------------------------------------------------
def text_mask(text, font, track, size_wh, center_x, baseline, fallback=None) -> Image.Image:
    """Маска строки с трекингом; y — базовая линия.

    fallback — шрифт для знаков, которых нет в кириллическом сабсете
    (например, дефис: он есть только в латинской части гарнитуры).
    """
    w, h = size_wh
    tmp = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(tmp)
    widths = []
    for ch in text:
        f = font
        if fallback is not None and ch in FALLBACK_CHARS:
            f = fallback
        widths.append(d.textlength(ch, font=f))
    total = sum(widths) + track * (len(text) - 1)
    x = center_x - total / 2
    for ch, cw in zip(text, widths):
        f = fallback if (fallback is not None and ch in FALLBACK_CHARS) else font
        d.text((x, baseline), ch, font=f, fill=255, anchor="ls")
        x += cw + track
    return tmp


def _offset(img: Image.Image, dx: int, dy: int) -> Image.Image:
    return img.transform(img.size, Image.AFFINE, (1, 0, -dx, 0, 1, -dy), resample=Image.BILINEAR)


def gradient_text(bg: Image.Image, text, font_file, size, track, baseline,
                  top, bottom, center_x=None) -> Image.Image:
    w, h = bg.size
    font = ImageFont.truetype(str(FONTS / font_file), size)
    fallback = ImageFont.truetype(str(FONTS / LATIN.get(font_file, "")), size) \
        if LATIN.get(font_file) else None
    mask = text_mask(text, font, track, (w, h),
                     center_x if center_x is not None else w / 2, baseline, fallback)

    sh = _offset(mask.filter(ImageFilter.GaussianBlur(size * 0.09)), 0, int(size * 0.05))
    sh = sh.point(lambda v: int(v * 0.5))
    bg = Image.composite(Image.new("RGB", (w, h), SHADOW), bg, sh)

    span = size * 0.78
    grad = Image.new("RGB", (w, h))
    gd = ImageDraw.Draw(grad)
    for y in range(h):
        t = min(1.0, max(0.0, (y - (baseline - span)) / span))
        gd.line([(0, y), (w, y)], fill=tuple(int(top[c] + (bottom[c] - top[c]) * t) for c in range(3)))
    bg.paste(grad, (0, 0), mask)
    return bg


def solid_text(bg: Image.Image, text, font_file, size, track, baseline, color,
               center_x=None) -> Image.Image:
    w, h = bg.size
    font = ImageFont.truetype(str(FONTS / font_file), size)
    fallback = ImageFont.truetype(str(FONTS / LATIN.get(font_file, "")), size) \
        if LATIN.get(font_file) else None
    mask = text_mask(text, font, track, (w, h),
                     center_x if center_x is not None else w / 2, baseline, fallback)
    sh = _offset(mask.filter(ImageFilter.GaussianBlur(size * 0.08)), 0, int(size * 0.04))
    sh = sh.point(lambda v: int(v * 0.42))
    bg = Image.composite(Image.new("RGB", (w, h), SHADOW), bg, sh)
    bg.paste(Image.new("RGB", (w, h), color), (0, 0), mask)
    return bg


def build_derivatives(master: Path, key: str) -> None:
    """Web- и social-версии макета — те же параметры, что и у всей серии."""
    web_dir = ROOT / "public/media/banners"
    social_dir = web_dir / "social"
    im = Image.open(master).convert("RGB")
    w, h = im.size

    web_w = min(1400, w)
    web = im.resize((web_w, round(h * web_w / w)), Image.LANCZOS)
    web_path = web_dir / f"{key}.jpg"
    web_path.parent.mkdir(parents=True, exist_ok=True)
    web.save(web_path, quality=82, optimize=True, progressive=True)
    webp_path = web_dir / f"{key}.webp"
    web.save(webp_path, quality=80, method=6)
    print(f"  web: {web_path.relative_to(ROOT)} ({web.size[0]}×{web.size[1]}, "
          f"{web_path.stat().st_size // 1024} КБ) + webp {webp_path.stat().st_size // 1024} КБ")

    for name, tw, th in (("1080x1920", 1080, 1920), ("1080x1350", 1080, 1350),
                         ("1080x1080", 1080, 1080), ("1920x1080", 1920, 1080)):
        if w / h > tw / th:
            nh, nw = th, round(w * th / h)
        else:
            nw, nh = tw, round(h * tw / w)
        resized = im.resize((nw, nh), Image.LANCZOS)
        bg = Image.new("RGB", (tw, th), resized.getpixel((0, 0)))
        bg.paste(resized, ((tw - nw) // 2, (th - nh) // 2))
        p = social_dir / f"{key}-{name}.jpg"
        p.parent.mkdir(parents=True, exist_ok=True)
        bg.save(p, quality=86, optimize=True, progressive=True)
        print(f"  social: {p.relative_to(ROOT)} ({tw}×{th}, {p.stat().st_size // 1024} КБ)")


# --------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true", help="дополнительно собрать превью 1600 px")
    ap.add_argument("--no-derivatives", action="store_true", help="не пересобирать web/social")
    args = ap.parse_args()

    if not SOURCE.exists():
        print(f"Нет исходника: {SOURCE}", file=sys.stderr)
        return 1

    arr = np.array(Image.open(SOURCE).convert("RGB"))
    print(f"Исходник: {SOURCE.name} {arr.shape[1]}×{arr.shape[0]}")

    mono, word = extract_logo(arr)
    print(f"Логотип: монограмма {mono.size}, подпись {word.size}")

    fixed = repair(arr)
    bg = Image.fromarray(fixed, "RGB")

    bg = place_logo(bg, mono, word)
    bg = gradient_text(bg, DESC_TEXT, DESC_FONT, DESC_SIZE, DESC_TRACK, DESC_BASELINE,
                       GOLD_TOP, GOLD_BOTTOM)
    bg = gradient_text(bg, BRAND_TEXT, BRAND_FONT, BRAND_SIZE, BRAND_TRACK, BRAND_BASELINE,
                       GOLD_TOP, GOLD_BOTTOM)
    bg = solid_text(bg, SUB_TEXT, SUB_FONT, SUB_SIZE, SUB_TRACK, SUB_BASELINE, CREAM)

    PRINT_DIR.mkdir(parents=True, exist_ok=True)
    bg.save(OUT, quality=95, subsampling=0, optimize=True, progressive=True, dpi=(DPI, DPI))
    print(f"Мастер: {OUT.relative_to(ROOT)} ({OUT.stat().st_size // 1024} КБ, {DPI} dpi)")

    if not args.no_derivatives:
        print("→ Собираю web/social-версии")
        build_derivatives(OUT, "dv-production")

    if args.preview:
        p = ROOT / "banners/casting-series/preview/dv-production-edit-preview.jpg"
        p.parent.mkdir(parents=True, exist_ok=True)
        bg.resize((1600, 1600), Image.LANCZOS).save(p, quality=92, subsampling=0)
        print(f"Превью: {p.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
