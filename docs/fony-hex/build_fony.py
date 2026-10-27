#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Фоны для презентаций SM-Production на основе гексагональной текстуры заказчика.

Плитка не растягивается из исходника, а рисуется процедурно (SDF-гексагон
с фаской, светом и случайной яркостью по плиткам) — поэтому остаётся резкой
в любом разрешении. Исходник задаёт геометрию, масштаб и материал.

Запуск:  python3 build_fony.py
Итог:    fon/*.jpg (1920×1080) · fon-2x/*.jpg (2560×1440) · SM-Fony-hex.pdf
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, "source-hex.png")
OUT = os.path.join(BASE, "fon")
OUT2 = os.path.join(BASE, "fon-2x")

# фирменная палитра
BG = np.array([10, 10, 13],  dtype=np.float32) / 255
ACCENT = np.array([255, 77, 28], dtype=np.float32) / 255
ACID = np.array([216, 255, 62], dtype=np.float32) / 255

# материал плитки (в тон исходнику)
FACE_DARK = np.array([83, 84, 94], np.float32) / 255
GAP_DARK = np.array([17, 17, 22], np.float32) / 255
FACE_LIGHT = np.array([236, 234, 228], np.float32) / 255
GAP_LIGHT = np.array([196, 194, 188], np.float32) / 255

R_SEED = 20270101


# ---------------------------------------------------------------- помощники
def smoothstep(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def grid(h, w):
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    return x / (w - 1), y / (h - 1)


def ramp(v, a, b):
    return smoothstep((v - a) / max(b - a, 1e-6))


def radial(x, y, cx, cy, r, squash=1.0):
    d = np.sqrt(((x - cx) * squash) ** 2 + (y - cy) ** 2)
    return 1.0 - smoothstep(d / max(r, 1e-6))


def vignette(x, y, strength=0.0, power=1.8):
    d = np.sqrt((x - 0.5) ** 2 + (y - 0.5) ** 2) / 0.7071
    return 1.0 - strength * smoothstep(d) ** power


def smooth_noise(h, w, scale=120, seed=0):
    r = np.random.default_rng(seed)
    small = r.random((max(2, h // scale), max(2, w // scale))).astype(np.float32)
    im = Image.fromarray((small * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
    n = np.asarray(im, np.float32) / 255.0
    return (n - n.min()) / max(n.max() - n.min(), 1e-6)


# ---------------------------------------------------------------- плитка
def hex_texture(w, h, R=None, face=FACE_DARK, gap=GAP_DARK, light_from=(-0.42, -0.91), seed=R_SEED):
    """
    Плосковерхий гексагон (вершины слева и справа, горизонтальные кромки сверху/снизу).
    SDF строится по шести плоскостям, поэтому плитка стыкуется без наложений.
    Фаска подсвечена со стороны света, между плитками — тонкая тёмная щель.
    R — радиус описанной окружности, px.
    """
    if R is None:
        R = w / 24.0                        # масштаб исходника: 1360 / 56.7
    ap = R * np.sqrt(3) / 2                 # апофема
    dx, dy = 1.5 * R, np.sqrt(3) * R        # шаг решётки
    bevel = max(2.2, R * 0.13)              # ширина мягкой фаски
    aa = 1.2                                # сглаживание кромки, px
    gapw = max(0.6, R * 0.020)              # половина щели между плитками

    lx, ly = light_from
    ln = np.hypot(lx, ly); lx, ly = lx / ln, ly / ln

    # шесть нормалей плосковерхого гексагона
    normals = np.array([
        [0.0, 1.0], [0.8660254, 0.5], [0.8660254, -0.5],
        [0.0, -1.0], [-0.8660254, -0.5], [-0.8660254, 0.5],
    ], np.float32)

    rng = np.random.default_rng(seed)
    canvas = np.broadcast_to(gap, (h, w, 3)).copy()

    cols = int(w / dx) + 3
    rows = int(h / dy) + 3

    for i in range(-1, cols):
        for j in range(-1, rows):
            cx = i * dx
            cy = j * dy + (i % 2) * dy / 2
            x0 = int(max(0, cx - R - 2)); x1 = int(min(w, cx + R + 3))
            y0 = int(max(0, cy - ap - 2)); y1 = int(min(h, cy + ap + 3))
            if x1 <= x0 or y1 <= y0:
                continue
            yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
            px, py = xx - cx, yy - cy

            planes = np.stack([normals[k, 0] * px + normals[k, 1] * py for k in range(6)], axis=0)
            dmax = planes.max(axis=0)                    # расстояние до ближайшей кромки (по нормали)
            inner = (ap - gapw) - dmax                   # >0 внутри плитки
            k_edge = planes.argmax(axis=0)               # какая грань ближе

            # цвет грани по направлению света
            lit = np.clip(normals[k_edge, 0] * lx + normals[k_edge, 1] * ly, -1, 1)[..., None]
            # кромка: освещённая грань светлее, затенённая темнее
            bevel_col = face * (1.0 + 0.34 * lit) + 0.045 * np.clip(lit, 0, 1)

            # лицо плитки: лёгкая вариация по плиткам + затемнение к кромке
            tile_var = 1.0 + float(rng.normal(0.0, 0.022))
            ao = (0.90 + 0.10 * smoothstep(inner / (bevel * 2.2)))[..., None]
            face_col = face * tile_var * ao

            t_bev = (1.0 - smoothstep(inner / bevel))[..., None]   # 1 на кромке → 0 в глубине
            col = face_col * (1 - t_bev) + bevel_col * t_bev

            alpha = np.clip(inner / aa + 0.5, 0, 1)[..., None]
            target = canvas[y0:y1, x0:x1]
            canvas[y0:y1, x0:x1] = target * (1 - alpha) + col * alpha

    return np.clip(canvas, 0, 1)


def sheen(img, dx=0.55, dy=0.30, amount=0.10, lo=0.0):
    """очень мягкий световой наклон по кадру — материал смотрится объёмнее"""
    h, w = img.shape[:2]
    x, y = grid(h, w)
    v = (x * dx + y * dy)
    v = (v - v.min()) / max(v.max() - v.min(), 1e-6)
    return np.clip(img * (1 + amount * (v - lo))[..., None], 0, 1)


def vign(img, strength=0.35, power=1.9):
    h, w = img.shape[:2]
    x, y = grid(h, w)
    return np.clip(img * vignette(x, y, strength, power)[..., None], 0, 1)


def glow(img, spots):
    """spots: (cx, cy, radius, color, amount)"""
    h, w = img.shape[:2]
    x, y = grid(h, w)
    out = img.copy()
    for cx, cy, r, color, amount in spots:
        s = radial(x, y, cx, cy, r)[..., None]
        out = out + s * (np.asarray(color, np.float32) * amount)
    return np.clip(out, 0, 1)


def grain(img, amount=0.004, seed=7):
    r = np.random.default_rng(seed)
    return np.clip(img + r.normal(0, amount, img.shape).astype(np.float32), 0, 1)


def shade(img, mask, base=BG):
    """примешиваем фон по маске: 1 — текстура, 0 — чистый deep-black"""
    m = np.clip(mask, 0, 1)[..., None]
    return np.clip(base[None, None, :] * (1 - m) + img * m, 0, 1)


def save(img, name, folder, w):
    p = os.path.join(folder, name + ".jpg")
    Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)).save(
        p, quality=95, optimize=True, progressive=True, subsampling=1)
    return p


# ---------------------------------------------------------------- варианты
def build(w, h):
    x, y = grid(h, w)
    dark = hex_texture(w, h)                       # тёмный материал (один раз)
    d = lambda k=1.0: np.clip(dark * k, 0, 1)      # noqa: E731
    shots = {}

    # 01 — обложка: тень под заголовок слева, текстура живёт справа
    m = 1 - 0.86 * (1 - ramp(x, 0.06, 0.72))
    shots["01-oblozhka"] = glow(
        shade(d(0.92), m),
        [(0.10, 0.88, 0.62, ACCENT, 0.045), (0.80, 0.06, 0.55, ACID, 0.014)])

    # 02 — раздел: крупная цифра по центру, тень мягко по периметру, центр ровный
    edge = np.clip(0.55 + 0.85 * (1 - radial(x, y, 0.5, 0.5, 1.02, squash=0.86)), 0, 1)
    m = np.clip(edge, 0.45, 1.0)
    shots["02-razdel"] = glow(shade(d(0.95), m), [(0.5, 0.5, 1.15, ACCENT, 0.012)])

    # 03 — текст слева: справа текстура, слева глубокая тень
    m = 0.06 + 0.90 * ramp(x, 0.24, 0.92)
    shots["03-tekst-levo"] = glow(shade(d(0.95), m), [(0.99, 0.86, 0.55, ACCENT, 0.035)])

    # 04 — зеркальный к 03
    m = 0.06 + 0.90 * (1 - ramp(x, 0.08, 0.76))
    shots["04-tekst-spravo"] = glow(shade(d(0.95), m), [(0.01, 0.86, 0.55, ACCENT, 0.035)])

    # 05 — таблицы и графики: почти ровный тёмный, текстура еле читается
    m = 0.16 + 0.10 * smooth_noise(h, w, 150, 11)
    shots["05-tablicy"] = shade(d(0.85), m)

    # 06 — цифры: текстура сверху, акцентное свечение снизу справа
    m = (0.90 - 0.55 * ramp(y, 0.05, 0.85)) * (0.55 + 0.45 * ramp(x, 1.0, 0.15))
    shots["06-cifry"] = glow(shade(d(0.95), m), [(0.85, 0.88, 0.62, ACCENT, 0.070), (0.93, 1.0, 0.4, ACID, 0.018)])

    # 07 — цитата: свет сверху, тень снизу; текстура наверху
    m = 0.22 + 0.72 * (1 - ramp(y, 0.15, 0.92))
    shots["07-citata"] = shade(d(0.95), m)

    # 08 — светлая версия: та же плитка в тёплом светлом материале
    light = hex_texture(w, h, face=np.array([222, 219, 212], np.float32) / 255,
                        gap=np.array([168, 165, 159], np.float32) / 255, seed=R_SEED + 5)
    light = np.clip((light - 0.5) * 1.06 + 0.52, 0, 1)          # чуть больше рельефа
    m = 0.90 - 0.16 * ramp(x, 0.1, 1.0) + 0.05 * smooth_noise(h, w, 160, 3)
    shots["08-svetlyy"] = shade(light, m, base=np.array([250, 248, 244], np.float32) / 255)

    # 09 — под фото: размытая плитка, ровный тёмный фон
    blur_im = Image.fromarray((dark * 255).astype(np.uint8)).filter(ImageFilter_Gauss(9))
    blurred = np.asarray(blur_im, np.float32) / 255
    m = 0.55 + 0.35 * ramp(y, 0.0, 0.9)
    shots["09-pod-foto"] = glow(shade(blurred, m), [(0.5, 1.0, 0.75, ACCENT, 0.030)])

    # 10 — финал: тепло снизу, текстура сверху
    m = 0.16 + 0.78 * (1 - ramp(y, 0.10, 0.92))
    shots["10-final"] = glow(shade(d(0.95), m), [(0.5, 1.04, 0.72, ACCENT, 0.075), (0.5, 1.06, 0.38, ACID, 0.014)])

    # 11 — акцентная: гексы в фирменном оранжевом справа
    lum = dark.mean(axis=2, keepdims=True)                       # яркость плитки
    norm = np.clip((lum - 0.12) / 0.30, 0, 1)                    # 0 в щели, 1 на светлой грани
    tinted = ACCENT[None, None, :] * (0.10 + 0.80 * norm) + np.array([0.05, 0.02, 0.01], np.float32)
    tinted = np.clip(tinted, 0, 1)
    tinted = np.clip(tinted * 0.72 + 0.012, 0, 1)
    m = 0.05 + 0.92 * ramp(x, 0.10, 0.86)
    shots["11-akcent"] = glow(shade(tinted, m), [(0.94, 0.34, 0.42, ACCENT, 0.035)])

    # 12 — чистая плитка: без градиентов, для своих композиций
    shots["12-plitka"] = shade(d(0.95), 1.0)

    # общая доводка
    for k, v in shots.items():
        if k.startswith("08"):
            v = vign(sheen(v, 0.4, 0.2, 0.05), 0.10)
            v = grain(v, 0.0035)
        else:
            v = vign(sheen(v, 0.5, 0.28, 0.13), 0.30 if not k.startswith("12") else 0.14)
            v = grain(v, 0.005)
        shots[k] = v
    return shots


def ImageFilter_Gauss(r):
    from PIL import ImageFilter
    return ImageFilter.GaussianBlur(r)


# ---------------------------------------------------------------- предпросмотр
def preview(files, path, cols=3, tw=640):
    th = int(tw * 9 / 16)
    rows = (len(files) + cols - 1) // cols
    pad, top = 18, 86
    sheet = Image.new("RGB", (cols * tw + pad * (cols + 1), rows * th + pad * rows + top), (18, 18, 21))
    dr = ImageDraw.Draw(sheet)
    try:
        title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 34)
        small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 19)
    except Exception:
        title = small = ImageFont.load_default()
    dr.text((pad, 26), "SM-PRODUCTION · ФОНЫ ИЗ ГЕКСАГОНАЛЬНОЙ ТЕКСТУРЫ", font=title, fill=(244, 242, 236))
    for i, f in enumerate(files):
        im = Image.open(f).convert("RGB").resize((tw, th), Image.LANCZOS)
        cx = pad + (i % cols) * (tw + pad)
        cy = top + (i // cols) * (th + pad)
        sheet.paste(im, (cx, cy))
        name = os.path.basename(f).replace(".jpg", "")
        dr.text((cx + 12, cy + th - 30), name, font=small, fill=(216, 255, 62))
    sheet.save(path, quality=92, optimize=True)
    return sheet.size


def contrast_report(im, zones):
    """
    Считает контраст белого текста (#F4F2EC) на фоне в указанных зонах.
    zones: (x0, y0, x1, y1) в долях кадра. Норма WCAG AA для крупного текста — 3.0, для обычного — 4.5.
    """
    a = np.asarray(im, np.float32) / 255.0
    h, w = a.shape[:2]

    def lin(c):
        return np.where(c <= 0.03928, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)

    out = []
    for name, (x0, y0, x1, y1) in zones.items():
        crop = a[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)]
        bg = float(lin(crop.mean(axis=(0, 1))).mean())
        ink = float(lin(np.array([244, 242, 236], np.float32) / 255).mean())
        ratio = (max(ink, bg) + 0.05) / (min(ink, bg) + 0.05)
        out.append((name, ratio))
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(OUT2, exist_ok=True)
    made = []
    for folder, (w, h) in ((OUT, (1920, 1080)), (OUT2, (2560, 1440))):
        shots = build(w, h)
        for name, im in shots.items():
            p = save(im, name, folder, w)
            print(f"{os.path.relpath(p, BASE):30} {w}×{h} {os.path.getsize(p)//1024:5} КБ")
            if folder == OUT:
                made.append(p)
    print("предпросмотр:", preview(made, os.path.join(BASE, "preview.jpg")))

    # контраст белого текста в зонах, под которые эти фоны сделаны
    zones = {
        "01: заголовок слева": (0.04, 0.30, 0.52, 0.72),
        "02: центр под цифру": (0.30, 0.32, 0.70, 0.68),
        "03: текст слева": (0.04, 0.18, 0.55, 0.82),
        "04: текст справа": (0.45, 0.18, 0.96, 0.82),
        "05: вся площадь": (0.05, 0.10, 0.95, 0.90),
        "06: зона под цифры": (0.05, 0.45, 0.60, 0.90),
        "07: центр цитаты": (0.15, 0.30, 0.85, 0.70),
        "09: зона под фото": (0.10, 0.10, 0.90, 0.60),
        "10: центр финала": (0.20, 0.35, 0.80, 0.75),
        "11: текст слева": (0.04, 0.20, 0.45, 0.80),
    }
    print("\nконтраст белого текста (WCAG: ≥4.5 обычный, ≥3.0 крупный):")
    for name, im in ((n, Image.open(p)) for n, p in zip(
            ["01-oblozhka", "02-razdel", "03-tekst-levo", "04-tekst-spravo", "05-tablicy",
             "06-cifry", "07-citata", "09-pod-foto", "10-final", "11-akcent"], made)):
        pass
    results = {}
    for name, (x0, y0, x1, y1) in zones.items():
        key = name.split(":")[0]
        path = os.path.join(OUT, key + "-" + {
            "01": "oblozhka", "02": "razdel", "03": "tekst-levo", "04": "tekst-spravo",
            "05": "tablicy", "06": "cifry", "07": "citata", "09": "pod-foto",
            "10": "final", "11": "akcent"}[key] + ".jpg")
        r = contrast_report(Image.open(path).convert("RGB"), {name: (x0, y0, x1, y1)})[0][1]
        results[name] = r
        flag = "OK " if r >= 4.5 else ("крупный OK" if r >= 3.0 else "МАЛО")
        print(f"  {name:26} {r:5.1f}:1  {flag}")
    return results


if __name__ == "__main__":
    main()
