#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Фоновые изображения SM-Production — серия «Многоугольники».

Каждый фон собран из полигонов: грани с фаской, направленный свет,
случайная яркость каждой плиты. Никакого растягивания готовой картинки,
всё считается в numpy — поэтому резко на любом разрешении, вплоть до 4K.

Пять разных приёмов:
  · мозаика Вороного по дрожащей сетке — живые пяти-семиугольники;
  · пол в перспективе с уходящей к горизонту подсветкой;
  · низкополи: плоские треугольные грани в объёме;
  · вытянутые вертикальные плиты;
  · гранёные кристаллы в глубине кадра.

Запуск:  python3 build_poly.py
Итог:    poli/*.jpg (1920×1080) · poli-2x/*.jpg (2560×1440) · preview.jpg
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "poli")
OUT2 = os.path.join(BASE, "poli-2x")

# фирменная палитра
INK = np.array([244, 242, 236], np.float32) / 255
ACCENT = np.array([255, 77, 28], np.float32) / 255
ACID = np.array([216, 255, 62], np.float32) / 255
DARK = np.array([10, 10, 13], np.float32) / 255

FACE = np.array([74, 76, 86], np.float32) / 255       # грань плитки
GAP = np.array([16, 16, 21], np.float32) / 255        # шов
FACE_L = np.array([238, 235, 228], np.float32) / 255  # светлый материал
GAP_L = np.array([176, 173, 166], np.float32) / 255


# ---------------------------------------------------------------- помощники
def smoothstep(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def ramp(v, a, b):
    return smoothstep((v - a) / max(b - a, 1e-6))


def norm(v):
    return v / max(np.linalg.norm(v), 1e-6)


def vignette(x, y, strength=0.0, power=1.8):
    d = np.sqrt((x - 0.5) ** 2 + (y - 0.5) ** 2) / 0.7071
    return 1.0 - strength * smoothstep(d) ** power


def glow(rgb, x, y, cx, cy, r, color, strength, squash=1.0):
    d = np.sqrt(((x - cx) * squash) ** 2 + (y - cy) ** 2) / max(r, 1e-6)
    m = np.exp(-(d ** 2) * 2.2) * strength
    return rgb + color[None, None, :] * m[..., None]


def noise_field(h, w, scale, seed):
    """Гладкий шум для вариаций яркости."""
    r = np.random.default_rng(seed)
    small = r.random((max(2, h // scale), max(2, w // scale))).astype(np.float32)
    im = Image.fromarray((small * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
    n = np.asarray(im, np.float32) / 255.0
    return (n - n.min()) / max(n.max() - n.min(), 1e-6)


def finish(rgb, seed, vig=0.32, vig_power=1.7, grain=0.016):
    """Виньетка, зерно против бандинга, приведение к uint8."""
    x = np.linspace(0, 1, rgb.shape[1], dtype=np.float32)[None, :]
    y = np.linspace(0, 1, rgb.shape[0], dtype=np.float32)[:, None]
    v = vignette(x, y, vig, vig_power)
    out = rgb * v[..., None]
    if grain > 0:
        r = np.random.default_rng(seed)
        out = out + (r.standard_normal(out.shape[:2]).astype(np.float32) * grain)[..., None]
    return (np.clip(out, 0, 1) * 255).astype(np.uint8)


def save(arr, path, quality=95):
    Image.fromarray(arr).save(path, quality=quality, optimize=True,
                              progressive=True, subsampling=1)


# ---------------------------------------------------------------- многоугольники
def poly_fields(X, Y, ax, ay, jitter, seed):
    """
    Диаграмма Вороного по дрожащей сетке.
    X, Y — координаты пикселей в любых единицах (пиксели или мировые метры),
    ax, ay — размер ячейки в тех же единицах (ay > ax даёт вытянутые многоугольники).
    Возвращает: d1 (до своего центра), зазор до соседа (d2-d1),
    случайную яркость грани и наклон грани по осям.
    """
    rng = np.random.default_rng(seed)
    h, w = X.shape

    # сетка строится по фактическому диапазону координат, а не по размеру кадра,
    # поэтому функция годится и для перспективы, где мировые координаты уплывают
    x0, y0 = float(X.min()), float(Y.min())
    gw = int(np.ceil((float(X.max()) - x0) / ax)) + 5
    gh = int(np.ceil((float(Y.max()) - y0) / ay)) + 5

    jx = (rng.random((gh, gw)) - 0.5) * jitter
    jy = (rng.random((gh, gw)) - 0.5) * jitter
    val = rng.random((gh, gw)).astype(np.float32)
    tx = (rng.random((gh, gw)) - 0.5).astype(np.float32)
    ty = (rng.random((gh, gw)) - 0.5).astype(np.float32)

    gx = (X - x0) / ax
    gy = (Y - y0) / ay
    bx = np.floor(gx).astype(np.int32)
    by = np.floor(gy).astype(np.int32)

    d1 = np.full((h, w), 1e30, np.float32)
    d2 = np.full((h, w), 1e30, np.float32)
    fv = np.zeros((h, w), np.float32)
    ftx = np.zeros((h, w), np.float32)
    fty = np.zeros((h, w), np.float32)

    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            cx = np.clip(bx + dx + 2, 0, gw - 1)
            cy = np.clip(by + dy + 2, 0, gh - 1)
            px = x0 + (bx + dx + 0.5 + jx[cy, cx]) * ax
            py = y0 + (by + dy + 0.5 + jy[cy, cx]) * ay
            dist = np.sqrt((X - px) ** 2 + (Y - py) ** 2)
            m = dist < d1
            d2 = np.where(m, d1, np.minimum(d2, dist))
            fv = np.where(m, val[cy, cx], fv)
            ftx = np.where(m, tx[cy, cx], ftx)
            fty = np.where(m, ty[cy, cx], fty)
            d1 = np.where(m, dist, d1)

    return d1, d2 - d1, fv, ftx, fty


def poly_rgb(d1, edge, fv, ftx, fty, w, face=FACE, gap=GAP,
             bevel=None, gapw=None, light=(-0.42, -0.91),
             depth=1.0, tint=None, aa=None):
    """
    Окраска многоугольной мозаики: грань + фаска со светом + тёмный шов.
    bevel, gapw — в единицах d1 (по умолчанию в пикселях от ширины кадра).
    aa — массив «сколько пикселей в одной единице d1» для перспективы:
    без него шов вдали превращается в муар, а на переднем плане — в чёрные полосы.
    """
    if bevel is None:
        bevel = w / 190.0
    if gapw is None:
        gapw = w / 1400.0

    if aa is not None:
        # не даём фаске и шву стать тоньше пикселя: расширяем в единицах d1
        bevel = np.maximum(bevel, 1.1 / np.maximum(aa, 1e-6))
        gapw = np.maximum(gapw, 0.9 / np.maximum(aa, 1e-6))

    # базовая яркость грани: случайная + наклон к свету
    tilt = (ftx * light[0] + fty * light[1])
    shade = (0.74 + 0.26 * fv + 0.22 * tilt)[..., None]
    col = face[None, None, :] * shade

    # фаска: у кромки наклон к свету — светлее, от света — темнее
    gy, gx = np.gradient(d1)
    gl = np.sqrt(gx * gx + gy * gy) + 1e-6
    lit = np.clip(-(gx * light[0] + gy * light[1]) / gl, 0.0, 1.0)
    t = 1.0 - smoothstep(edge / (bevel * 2.1 + 1e-6))
    col = col * (1.0 + 0.72 * t * lit)[..., None]
    col = col * (1.0 - 0.42 * t * (1.0 - lit))[..., None]

    # тёмный шов между плитками
    g = 1.0 - smoothstep(edge / (gapw * 2.1 + 1e-6))
    if aa is not None:
        # шов уже́ пикселя — гасим его пропорционально площади, иначе муар
        g = g * np.clip(gapw * 2.1 * aa, 0.0, 1.0)
    col = col * (1.0 - g)[..., None] + gap[None, None, :] * g[..., None]

    if depth != 1.0:
        col = col ** np.float32(depth)
    if tint is not None:
        col = col * tint[None, None, :]
    return np.clip(col, 0, 4)


# ---------------------------------------------------------------- 01 мозаика
def bg_mosaic(w, h, seed=101):
    Y, X = np.mgrid[0:h, 0:w].astype(np.float32)
    cell = w / 13.5
    d1, edge, fv, ftx, fty = poly_fields(X, Y, cell, cell, 0.62, seed)
    rgb = poly_rgb(d1, edge, fv, ftx, fty, w, depth=1.18)

    xn, yn = X / w, Y / h
    # мягкая световая волна сверху слева
    rgb = glow(rgb, xn, yn, 0.18, -0.12, 0.95, np.array([0.30, 0.30, 0.34], np.float32), 0.55)
    rgb = glow(rgb, xn, yn, 0.92, 1.12, 0.85, np.array([0.55, 0.18, 0.06], np.float32), 0.22)
    rgb = rgb * (0.55 + 0.75 * ramp(xn + yn * 0.35, -0.12, 1.05))[..., None]
    return finish(rgb, seed, vig=0.34)


# ---------------------------------------------------------------- 02 перспектива
def bg_perspective(w, h, seed=202):
    """
    Пол из многоугольных плит в перспективе — уходит к светящемуся горизонту.
    Камера на высоте 4.5 м, плита 1.6 м: вблизи читаются грани, вдали шов тает.
    Выше горизонта — тёмный задник, полосы из пола туда не попадают.
    """
    Y, X = np.mgrid[0:h, 0:w].astype(np.float32)
    horizon = h * 0.40
    f = 1.90 * w
    cam = 4.5
    dy = np.maximum(Y - horizon, 0.8)
    Z = f * cam / dy                             # без обрезки: иначе у горизонта всё слипается
    wx = (X - w * 0.5) * Z / f

    cell = 2.10                                  # плита, м
    scale = np.maximum(cell * f / Z, 1e-3)       # пикселей на плиту

    d1, edge, fv, ftx, fty = poly_fields(wx, Z, cell, cell, 0.40, seed)
    d1 = d1 / cell                               # в единицах плиты
    edge = edge / cell

    face = np.array([0.52, 0.53, 0.58], np.float32)
    floor = poly_rgb(d1, edge, fv, ftx, fty, w,
                     bevel=0.075, gapw=0.020, aa=scale,
                     light=(-0.30, -0.95), depth=0.72, face=face)

    # вдали плитка мельче пикселя — уходим в ровный тон, чтобы не было муара
    detail = smoothstep((scale - 5.0) / 12.0)[..., None]
    floor = face[None, None, :] * 0.50 * (1 - detail) + floor * detail

    floor = floor * 0.52                                          # тёмный пол
    floor = floor * (1.0 - 0.50 * ramp(Y, h * 0.66, h * 1.02))[..., None]   # ближний план в тени
    # у самого горизонта пол растворяется в дымке по расстоянию, а не по экрану
    fog = smoothstep((Z - 46.0) / 70.0) * 0.92
    halo = np.array([0.16, 0.10, 0.06], np.float32)[None, None, :]
    floor = floor * (1 - fog)[..., None] + halo * fog[..., None] * 0.55

    # задник: глубокий тёмный, с тёплым свечением у горизонта по центру
    xn, yn = X / w, Y / h
    backdrop = np.array([0.042, 0.043, 0.052], np.float32)[None, None, :] * \
        (0.55 + 1.1 * (1 - np.abs(xn - 0.5) * 1.25))[..., None] * \
        (0.75 + 0.55 * ramp(yn, 0.0, horizon / h))[..., None]
    backdrop = glow(backdrop, xn, yn, 0.50, horizon / h, 0.34,
                    np.array([0.60, 0.33, 0.15], np.float32), 0.70)
    backdrop = glow(backdrop, xn, yn, 0.50, horizon / h, 0.10,
                    np.array([0.92, 0.72, 0.48], np.float32), 0.95)

    # световая дорожка по полу от источника
    track = np.exp(-((xn - 0.5) ** 2) / (2 * 0.16 ** 2)) * ramp(Y, horizon, h * 1.0) ** 0.6
    track = track * (1 - ramp(Y, h * 0.80, h * 1.05))
    floor = floor + np.array([0.32, 0.20, 0.10], np.float32)[None, None, :] * track[..., None] * 0.55

    m = ramp(Y, horizon - 8.0, horizon + 20.0)[..., None]          # мягкая граница стыка
    rgb = backdrop * (1 - m) + floor * m
    return finish(rgb, seed, vig=0.22)


# ---------------------------------------------------------------- 03 низкополи
def bg_lowpoly(w, h, seed=303, cols=15, rows=9):
    rng = np.random.default_rng(seed)
    xs = np.linspace(-0.08 * w, 1.08 * w, cols + 1)
    ys = np.linspace(-0.08 * h, 1.08 * h, rows + 1)
    pxx, pyy = np.meshgrid(xs, ys)
    pxx = pxx + (rng.random(pxx.shape) - 0.5) * (w / cols) * 0.55
    pyy = pyy + (rng.random(pyy.shape) - 0.5) * (h / rows) * 0.55
    zz = rng.random(pxx.shape).astype(np.float32) ** 1.35
    zscale = (w / cols) * 0.62

    light = norm(np.array([-0.45, -0.75, 0.72], np.float32))
    rgb = np.tile(DARK, (h, w, 1)).astype(np.float32)

    for j in range(rows):
        for i in range(cols):
            quad = [(j, i), (j, i + 1), (j + 1, i + 1), (j + 1, i)]
            tris = [(quad[0], quad[1], quad[2]), (quad[0], quad[2], quad[3])]
            for tri in tris:
                p = np.array([[pxx[a, b], pyy[a, b], zz[a, b] * zscale] for a, b in tri], np.float32)
                x0 = int(max(0, np.floor(p[:, 0].min()) - 1))
                x1 = int(min(w, np.ceil(p[:, 0].max()) + 2))
                y0 = int(max(0, np.floor(p[:, 1].min()) - 1))
                y1 = int(min(h, np.ceil(p[:, 1].max()) + 2))
                if x1 <= x0 or y1 <= y0:
                    continue
                gx, gy = np.meshgrid(np.arange(x0, x1, dtype=np.float32),
                                     np.arange(y0, y1, dtype=np.float32))
                bx, by = p[0, 0], p[0, 1]
                v0 = p[1, :2] - p[0, :2]
                v1 = p[2, :2] - p[0, :2]
                den = v0[0] * v1[1] - v1[0] * v0[1]
                if abs(den) < 1e-6:
                    continue
                dx = gx - bx
                dy = gy - by
                u = (dx * v1[1] - v1[0] * dy) / den
                v = (v0[0] * dy - dx * v0[1]) / den
                inside = (u >= -0.002) & (v >= -0.002) & (u + v <= 1.002)

                n = np.cross(p[1] - p[0], p[2] - p[0])
                n = n / max(np.linalg.norm(n), 1e-6)
                if n[2] < 0:
                    n = -n
                lum = float(np.clip(np.dot(n, light), 0, 1))
                hz = float((zz[tri[0][0], tri[0][1]] + zz[tri[1][0], tri[1][1]] +
                            zz[tri[2][0], tri[2][1]]) / 3.0)

                base = np.array([0.30, 0.32, 0.39], np.float32) * (0.10 + 1.05 * lum ** 1.6) * (0.40 + 1.05 * hz)
                # тонкая светлая кромка грани
                be = np.minimum(np.minimum(u, v), 1 - u - v)
                rim = 1.0 - smoothstep(be / 0.005)
                col = base[None, None, :] * (1 + 0.65 * rim[..., None])
                col = np.clip(col, 0, 1)

                sub = rgb[y0:y1, x0:x1]
                sub[inside] = col[inside]

    xn = np.linspace(0, 1, w, np.float32)[None, :]
    yn = np.linspace(0, 1, h, np.float32)[:, None]
    rgb = glow(rgb, xn, yn, 0.5, 0.06, 0.85, np.array([0.34, 0.33, 0.36], np.float32), 0.55)
    rgb = glow(rgb, xn, yn, 0.84, 0.96, 0.70, np.array([0.55, 0.22, 0.08], np.float32), 0.18)
    return finish(rgb, seed, vig=0.40)


# ---------------------------------------------------------------- 04 свет по диагонали
def bg_lightbeam(w, h, seed=404):
    Y, X = np.mgrid[0:h, 0:w].astype(np.float32)
    cell = w / 15.0
    d1, edge, fv, ftx, fty = poly_fields(X, Y, cell, cell, 0.55, seed)
    rgb = poly_rgb(d1, edge, fv, ftx, fty, w, depth=1.0)

    xn, yn = X / w, Y / h
    # полоса света под углом ~35°
    s = (xn * 0.86 + yn * 0.50)
    beam = np.exp(-((s - 0.42) ** 2) / (2 * 0.085 ** 2))
    rgb = rgb * (0.42 + 0.30 * ramp(xn + yn, 0.1, 1.0))[..., None]
    rgb = rgb + np.array([0.55, 0.54, 0.52], np.float32)[None, None, :] * beam[..., None] * 0.55
    # глубокая тень под текст слева
    shadow = ramp(xn * 1.25 + yn * 0.55, 0.10, 0.72)
    rgb = rgb * (0.10 + 0.90 * shadow)[..., None]
    rgb = glow(rgb, xn, yn, 0.86, 0.22, 0.5, np.array([0.85, 0.30, 0.08], np.float32), 0.20)
    return finish(rgb, seed, vig=0.30)


# ---------------------------------------------------------------- 05 вытянутые
def bg_vertical(w, h, seed=505):
    Y, X = np.mgrid[0:h, 0:w].astype(np.float32)
    ax, ay = w / 17.0, w / 6.4
    d1, edge, fv, ftx, fty = poly_fields(X, Y, ax, ay, 0.58, seed)
    rgb = poly_rgb(d1, edge, fv, ftx, fty, w, bevel=w / 210.0, gapw=w / 1500.0,
                   light=(-0.55, -0.83), depth=0.85)

    xn, yn = X / w, Y / h
    rgb = rgb * (0.38 + 0.70 * ramp(yn, -0.1, 0.9))[..., None]
    rgb = glow(rgb, xn, yn, 0.5, 1.05, 0.8, np.array([0.55, 0.24, 0.09], np.float32), 0.26)
    rgb = glow(rgb, xn, yn, 0.5, -0.15, 0.75, np.array([0.24, 0.24, 0.28], np.float32), 0.45)
    return finish(rgb, seed, vig=0.38)


# ---------------------------------------------------------------- 06 осколки
def bg_crystals(w, h, seed=606):
    """Многоугольные кристаллы в глубине: три плана резкости, свет сверху слева."""
    rng = np.random.default_rng(seed)

    y = np.linspace(0, 1, h, np.float32)[:, None, None]
    x = np.linspace(0, 1, w, np.float32)[None, :, None]
    d = np.sqrt((x - 0.44) ** 2 + (y - 0.38) ** 2)
    base = np.array([0.045, 0.047, 0.057], np.float32)[None, None, :] * (0.40 + 1.25 * (1 - d))

    light = norm(np.array([-0.42, -0.70, 0.58], np.float32))
    S = 2
    plans = [   # (штук, rmin, rmax, размытие, alpha, яркость)
        (22, 0.020, 0.048, 620, 175, 0.50),
        (12, 0.036, 0.078, 1300, 200, 0.72),
        (6, 0.060, 0.115, 2400, 225, 1.00),
    ]

    layers = []
    for count, rmin, rmax, blur_div, alpha, bright in plans:
        im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
        dr = ImageDraw.Draw(im)
        for _ in range(count):
            cx, cy = rng.random() * w * S, rng.random() * h * S
            rad = (rmin + (rmax - rmin) * rng.random()) * w * S
            n = int(rng.integers(5, 8))
            rot = rng.random() * 6.283
            pts = []
            for k in range(n):
                a = rot + 6.283 * k / n
                rr = rad * (0.74 + 0.46 * rng.random())
                pts.append((cx + rr * np.cos(a), cy + rr * np.sin(a)))

            warm = rng.random() < 0.10
            apex = rad * 0.40
            for k in range(n):
                a0, b0 = pts[k], pts[(k + 1) % n]
                nrm = np.cross(np.array([a0[0] - cx, a0[1] - cy, apex]),
                               np.array([b0[0] - cx, b0[1] - cy, apex]))
                ln = np.linalg.norm(nrm)
                if ln < 1e-6:
                    continue
                nrm = nrm / ln
                if nrm[2] < 0:
                    nrm = -nrm
                lum = float(np.clip(np.dot(nrm, light), 0, 1))
                col = np.array([0.30, 0.32, 0.38], np.float32)
                if warm:
                    col = col * 0.45 + np.array([0.52, 0.23, 0.11], np.float32) * 0.55
                col = np.clip(col * (0.16 + 0.95 * lum ** 1.3) * bright, 0, 1)
                dr.polygon([(cx, cy), a0, b0], fill=tuple(int(c * 255) for c in col) + (alpha,))

            edge = (255, 150, 105, 150) if warm else (146, 152, 170, 135)
            dr.line(list(pts) + [pts[0]], fill=edge, width=max(1, S), joint="curve")

        im = im.resize((w, h), Image.LANCZOS).filter(ImageFilter.GaussianBlur(w / blur_div))
        layers.append(im)

    canvas = Image.fromarray((np.clip(base, 0, 1) * 255).astype(np.uint8)).convert("RGBA")
    for im in layers:
        canvas.alpha_composite(im)
    arr = np.asarray(canvas.convert("RGB"), np.float32) / 255

    xn = np.linspace(0, 1, w, np.float32)[None, :]
    yn = np.linspace(0, 1, h, np.float32)[:, None]
    arr = glow(arr, xn, yn, 0.22, 0.14, 0.42, np.array([0.40, 0.43, 0.52], np.float32), 0.32)
    arr = glow(arr, xn, yn, 0.88, 0.88, 0.50, np.array([0.72, 0.28, 0.08], np.float32), 0.22)
    arr = glow(arr, xn, yn, 0.5, 0.5, 0.95, np.array([0.05, 0.05, 0.07], np.float32), 0.60)
    return finish(arr, seed, vig=0.36)


# ---------------------------------------------------------------- 07 светлая
def bg_light(w, h, seed=707):
    Y, X = np.mgrid[0:h, 0:w].astype(np.float32)
    cell = w / 13.0
    d1, edge, fv, ftx, fty = poly_fields(X, Y, cell, cell, 0.60, seed)
    rgb = poly_rgb(d1, edge, fv, ftx, fty, w, face=FACE_L, gap=GAP_L,
                   bevel=w / 165.0, gapw=w / 1200.0,
                   light=(-0.40, -0.90), depth=1.15)

    xn, yn = X / w, Y / h
    rgb = rgb * (0.72 + 0.22 * ramp(xn + yn, -0.2, 1.15))[..., None]
    rgb = rgb * (1.0 - 0.16 * ramp(xn + yn, 0.85, 1.75))[..., None]
    return finish(rgb, seed, vig=0.20, grain=0.010)


# ---------------------------------------------------------------- 08 акцент
def bg_accent(w, h, seed=808):
    Y, X = np.mgrid[0:h, 0:w].astype(np.float32)
    cell = w / 14.5
    d1, edge, fv, ftx, fty = poly_fields(X, Y, cell, cell, 0.60, seed)
    xn, yn = X / w, Y / h

    rgb = poly_rgb(d1, edge, fv, ftx, fty, w, depth=1.05)
    # правый край — оранжевый свет внутри граней
    heat = ramp(xn, 0.42, 1.02) ** 1.5
    rgb = rgb * (1 - heat)[..., None] + (rgb * 0.72 + ACCENT[None, None, :] * 1.15 * rgb.mean(axis=2, keepdims=True)) * heat[..., None]
    rgb = rgb * (0.55 + 0.45 * ramp(xn * 0.7 + yn * 0.5, 0.0, 1.1))[..., None]
    rgb = glow(rgb, xn, yn, 1.02, 0.45, 0.62, ACCENT, 0.45)
    return finish(rgb, seed, vig=0.34)


# ---------------------------------------------------------------- контраст
def _luminance(rgb):
    c = np.clip(rgb, 0, 1)
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * c[..., 0] + 0.7152 * c[..., 1] + 0.0722 * c[..., 2]


def _rel_lum(color):
    c = np.array(color, np.float32)
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return float(0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2])


# в какой зоне и каким текстом работать на каждом фоне
TEXT_ZONES = {
    "01-poli-mozaika":     ("белый", [(0.04, 0.46, 0.10, 0.90), (0.54, 0.96, 0.10, 0.90)]),
    "02-poli-perspektiva": ("белый", [(0.06, 0.94, 0.03, 0.26), (0.06, 0.94, 0.62, 0.94)]),
    "03-nizkopoli":        ("белый", [(0.04, 0.96, 0.06, 0.94)]),
    "04-svet-diagonal":    ("белый", [(0.05, 0.44, 0.12, 0.88)]),
    "05-plitka-vertikal":  ("белый", [(0.04, 0.96, 0.08, 0.92)]),
    "06-obemnye-skol":     ("белый", [(0.04, 0.96, 0.06, 0.94)]),
    "07-svetlyy":          ("тёмный", [(0.04, 0.96, 0.06, 0.94)]),
    "08-akcent":           ("белый", [(0.04, 0.48, 0.10, 0.90)]),
}


def contrast_report(paths):
    ink_light = _rel_lum([0.957, 0.949, 0.925])   # #F4F2EC
    ink_dark = _rel_lum([0.039, 0.039, 0.051])    # #0A0A0D
    print("\nконтраст текста в рабочих зонах (WCAG: ≥4.5 для текста, ≥3.0 для крупного):")
    worst_all = 99.0
    for p in paths:
        name = os.path.basename(p)[:-4]
        kind, zones = TEXT_ZONES.get(name, ("белый", [(0.05, 0.95, 0.05, 0.95)]))
        L1 = ink_light if kind == "белый" else ink_dark
        a = np.asarray(Image.open(p).convert("RGB"), np.float32) / 255
        h, w = a.shape[:2]
        # текст садится на локальное среднее, а не на отдельный блик — сглаживаем,
        # иначе метрика ловит пиксели фасок и швов между плитками
        blur = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).filter(
            ImageFilter.BoxBlur(max(3, int(h / 42))))
        L = _luminance(np.asarray(blur, np.float32) / 255)
        worst = 99.0
        for (x0, x1, y0, y1) in zones:
            zone = L[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)]
            # самый светлый участок зоны (для белого текста) — по 95-му процентилю
            L2 = float(np.percentile(zone, 95 if kind == "белый" else 8))
            ratio = (L1 + 0.05) / (L2 + 0.05) if kind == "белый" else (L2 + 0.05) / (L1 + 0.05)
            worst = min(worst, ratio)
        worst_all = min(worst_all, worst)
        mark = "OK" if worst >= 4.5 else ("крупный текст" if worst >= 3.0 else "ВНИМАНИЕ")
        print(f"  {name:22s} {kind:7s} {worst:5.1f}:1  {mark}")
    print(f"  худший по набору: {worst_all:.1f}:1")


# ---------------------------------------------------------------- сборка
def build(w, h, seed_off=0):
    return {
        "01-poli-mozaika":    bg_mosaic(w, h, 101 + seed_off),
        "02-poli-perspektiva": bg_perspective(w, h, 202 + seed_off),
        "03-nizkopoli":       bg_lowpoly(w, h, 303 + seed_off),
        "04-svet-diagonal":   bg_lightbeam(w, h, 404 + seed_off),
        "05-plitka-vertikal": bg_vertical(w, h, 505 + seed_off),
        "06-obemnye-skol":    bg_crystals(w, h, 606 + seed_off),
        "07-svetlyy":         bg_light(w, h, 707 + seed_off),
        "08-akcent":          bg_accent(w, h, 808 + seed_off),
    }


def preview(files, path, cols=4, tw=620, th=349, pad=8):
    """Контактный лист для быстрого выбора фона."""
    thumbs = [Image.open(f).convert("RGB").resize((tw, th), Image.LANCZOS) for f in files]
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw + pad * (cols + 1), rows * th + pad * (rows + 1)), (0, 0, 0))
    for i, im in enumerate(thumbs):
        sheet.paste(im, (pad + (i % cols) * (tw + pad), pad + (i // cols) * (th + pad)))
    sheet.save(path, quality=92, optimize=True, progressive=True)
    print("контактный лист:", os.path.basename(path), f"{sheet.size[0]}×{sheet.size[1]}")


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(OUT2, exist_ok=True)
    for folder, (w, h) in ((OUT, (1920, 1080)), (OUT2, (2560, 1440))):
        made = build(w, h)
        for name, arr in made.items():
            p = os.path.join(folder, name + ".jpg")
            save(arr, p)
            print(f"  {w}×{h}  {name}.jpg  {os.path.getsize(p) // 1024} КБ")
    preview([os.path.join(OUT, f) for f in sorted(os.listdir(OUT))],
            os.path.join(BASE, "preview.jpg"))
    contrast_report([os.path.join(OUT, f) for f in sorted(os.listdir(OUT))])


if __name__ == "__main__":
    main()
