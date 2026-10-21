#!/usr/bin/env python3
"""Логотип «ДВ PRODUCTION» — векторная реконструкция для отдельного слоя на баннере.

Клиент прислал логотип в низком качестве (500 × 500, с фоном и артефактами) —
его можно поставить на баннер только «как есть», и качество не годится.

Скрипт собирает чистый векторный логотип:

  * источник формы — плоская версия клиента (`logo.jpg`, 500 × 500, ровный
    маджентовый фон, золото без бликов и тени) либо исходник 6144 × 6144
    (монограмма 1944 × 1431, надпись 1830 × 317);
  * матты строятся по тону: золото отделяется от мадженты, светлая надпись —
    от стены; случайные пиксели вычищаются, мелкие «прожжённые» лучом места
    закрываются;
  * контуры аппроксимируются (Douglas–Peucker) и сглаживаются (Чакин) —
    получаются настоящие векторные пути, а не растр;
  * собирается SVG с золотым градиентом клиента (#FCE9A1 → #A76F20)
    и тёплым белым «PRODUCTION»;
  * рендерится печатный PNG с прозрачностью (libvips/librsvg) + CMYK-версия
    с профилем FOGRA39 и альфа-каналом.

Пример:
  python3 scripts/banners/logo_vector.py --profile client --out-dir /home/user/print-logo
"""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np
import pyvips
from PIL import Image

REPO = Path(__file__).resolve().parents[2]
ICC_DIR = Path(__file__).resolve().parent / "icc"

ORIGINAL = REPO / "banners/casting-series/print/banner-dv-production-original-6144x6144.jpg"
CLIENT_FLAT = Path("/tmp/arena-coding-uploads/logo.jpg")

# Профили источника: рамки (x0, y0, x1, y1), увеличение перед трассировкой,
# сглаживание маты, порог заливки мелких дыр, допуск аппроксимации.
PROFILES = {
    "client": {
        "src": CLIENT_FLAT,
        "mono": (97, 105, 405, 319),
        "word": (95, 358, 405, 398),
        "upscale": 4.0,
        "blur": 0.9,
        "fill_mono": 40_000,
        "fill_word": 8_000,
        "eps_mono": 1.6,
        "eps_word": 1.0,
        "min_comp_mono": 4_000,
        "min_comp_word": 400,
        "smooth_mono": 1.2,
        "smooth_word": 0.8,
    },
    "original": {
        "src": ORIGINAL,
        "mono": (2174, 1584, 4118, 3015),
        "word": (2199, 3113, 4029, 3430),
        "upscale": 2.0,
        "blur": 1.1,
        "fill_mono": 170_000,
        "fill_word": 40_000,
        "eps_mono": 1.2,
        "eps_word": 0.8,
        "min_comp_mono": 8_000,
        "min_comp_word": 800,
        "smooth_mono": 2.6,
        "smooth_word": 2.2,
    },
}

GOLD_STOPS = [(0.00, "#FCE9A1"), (0.26, "#F0D994"), (0.62, "#CC9C34"), (1.00, "#A76F20")]
WORD_COLOR = "#FCF1D4"                  # тёплый белый из плоской версии клиента
DPI = 300


# ------------------------------------------------------------------ утилиты ---

def smoothstep(e0: float, e1: float, x: np.ndarray) -> np.ndarray:
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def load_box(path: Path, box: tuple[int, int, int, int], scale: float = 1.0) -> np.ndarray:
    x0, y0, x1, y1 = box
    im = pyvips.Image.new_from_file(str(path), access="random")
    a = np.array(im.crop(x0, y0, x1 - x0, y1 - y0).write_to_memory())
    a = a.reshape(y1 - y0, x1 - x0, im.bands)
    if scale != 1.0:
        big = cv2.resize(a, None, fx=scale, fy=scale, interpolation=cv2.INTER_LANCZOS4)
        a = big
    return a


# -------------------------------------------------------------------- маты ----

def gold_matte(rgb: np.ndarray) -> np.ndarray:
    """Золото монограммы: тон 20…60°, насыщенность и яркость выше порога."""
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    h = hsv[:, :, 0].astype(np.float32) * 2.0
    s = hsv[:, :, 1].astype(np.float32) / 255.0
    v = hsv[:, :, 2].astype(np.float32) / 255.0
    d = np.abs(((h - 40.0 + 180.0) % 360.0) - 180.0)
    a = (1.0 - smoothstep(14.0, 30.0, d))
    # мягкий порог по насыщенности: пересвеченные лучом участки золота
    # остаются в мате, иначе на стволе появляется вырез
    a *= smoothstep(0.10, 0.22, s)
    a *= smoothstep(0.20, 0.32, v)
    return np.clip(a, 0.0, 1.0)


def word_matte(rgb: np.ndarray) -> np.ndarray:
    """Светлая надпись: яркая и почти бесцветная."""
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    s = hsv[:, :, 1].astype(np.float32) / 255.0
    v = hsv[:, :, 2].astype(np.float32) / 255.0
    a = smoothstep(0.45, 0.62, v)
    # порог по насыщенности задаёт толщину штриха надписи (в оригинале
    # отношение штриха к высоте букв — около 0.10)
    a *= (1.0 - smoothstep(0.28, 0.44, s))
    return np.clip(a, 0.0, 1.0)


def clean_mask(alpha: np.ndarray, min_component: int, fill_holes_max: int,
               open_r: int = 3, blur: float = 2.4) -> np.ndarray:
    """Бинарная маска: убрать мусор, закрыть прожжённые лучом места, сгладить."""
    if blur > 0:
        # размытие маты перед порогом — край логотипа гладкий, без «ступенек» шума
        alpha = cv2.GaussianBlur(alpha, (0, 0), blur)
    binary = (alpha > 0.50).astype(np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN,
                              cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE,
                              cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))

    # оставляем все значимые компоненты (у надписи каждая буква — отдельная)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(binary, 8)
    keep = np.zeros_like(binary)
    for i in range(1, n):
        if stats[i, 4] >= min_component:
            keep[lab == i] = 1
    binary = keep
    if binary.any():
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE,
                                  cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))

    # дыры: маленькие — артефакты света (закрываем), большие — счётные зоны логотипа
    contours, hier = cv2.findContours(binary, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    if hier is not None:
        filled = binary.copy()
        for i, h in enumerate(hier[0]):
            if h[3] != -1:
                if cv2.contourArea(contours[i]) <= fill_holes_max:
                    cv2.drawContours(filled, [contours[i]], -1, 1, thickness=cv2.FILLED)
        binary = filled

    if open_r:
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (open_r * 2 + 1, open_r * 2 + 1))
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, k)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, k)
    return binary


# ------------------------------------------------------------- трассировка ----

def chaikin(points: np.ndarray, iterations: int = 2) -> np.ndarray:
    """Сглаживание ломаной (Чакин) — дуги становятся по-настоящему гладкими."""
    pts = points.astype(np.float64)
    for _ in range(iterations):
        if len(pts) < 3:
            break
        a, b = pts[:-1], pts[1:]
        q = 0.75 * a + 0.25 * b
        r = 0.25 * a + 0.75 * b
        out = np.empty((len(q) * 2 + 2, 2), dtype=np.float64)
        out[0] = pts[0]
        out[1:-1:2] = q
        out[2:-1:2] = r
        out[-1] = pts[-1]
        pts = out
    return pts


def resample_closed(pts: np.ndarray, factor: int = 4) -> np.ndarray:
    """Равномерная передискретизация замкнутой кривой по длине дуги."""
    closed = np.vstack([pts, pts[:1]])
    seg = np.linalg.norm(np.diff(closed, axis=0), axis=1)
    cum = np.concatenate([[0.0], np.cumsum(seg)])
    total = float(cum[-1])
    n = max(48, int(len(pts) * factor))
    s = np.linspace(0.0, total, n, endpoint=False)
    x = np.interp(s, cum, closed[:, 0])
    y = np.interp(s, cum, closed[:, 1])
    return np.stack([x, y], axis=1)


def corner_indices(pts: np.ndarray, angle_deg: float = 35.0,
                   window: int = 10, min_sep: int = 30) -> np.ndarray:
    """Углы логотипа — вершины, где ломаная поворачивает резко.

    Поворот считается на окне ±window точек: угол в оригинале слегка
    скруглён, и по одной вершине его не видно. Эти точки нельзя двигать —
    иначе прямые углы монограммы превращаются в скруглённые.
    """
    n = len(pts)
    w = max(1, min(window, n // 8))
    prev = pts - np.roll(pts, w, axis=0)          # вектор (i-w) -> i
    nxt = np.roll(pts, -w, axis=0) - pts          # вектор i -> (i+w)
    a_in = np.arctan2(prev[:, 1], prev[:, 0])
    a_out = np.arctan2(nxt[:, 1], nxt[:, 0])
    turn = np.abs((a_out - a_in + np.pi) % (2 * np.pi) - np.pi)
    thr = np.deg2rad(angle_deg)
    pinned: list[int] = []
    for i in np.nonzero(turn > thr)[0]:
        i = int(i)
        if all(min(abs(i - j), n - abs(i - j)) > min_sep for j in pinned):
            pinned.append(i)
    return np.array(sorted(pinned), dtype=int)


def taubin_smooth(pts: np.ndarray, pinned: np.ndarray | np.ndarray,
                  iters: int = 14) -> np.ndarray:
    """Сглаживание Лапласа/Таубина с закреплёнными углами.

    Убирает «дрожь» края, но прямые углы логотипа остаются прямыми:
    закреплённые вершины не смещаются, форма в целом не садится.
    """
    p = pts.astype(np.float64).copy()
    free = ~np.asarray(pinned, dtype=bool)
    for _ in range(max(0, iters)):
        for weight in (0.5, -0.54):
            neigh = np.roll(p, 1, axis=0) + np.roll(p, -1, axis=0)
            new = 0.5 * p + 0.25 * neigh
            p[free] = new[free]
    return p


def straighten_edges(pts: np.ndarray, corners: np.ndarray, tol: float = 8.0,
                     min_len: float = 120.0, margin: float = 40.0) -> np.ndarray:
    """Прямые участки между углами прищёлкиваются к точной прямой.

    Исходник (AI-рендер) даёт по краю ломаной волну ±3–4 px — в плоской
    заливке это видно. Вершины углов и переходы рядом с ними остаются
    нетронутыми, выпрямляются только длинные прямые пролёты.
    """
    out = pts.copy()
    if len(corners) < 2:
        return out
    n = len(pts)
    cs = [int(c) for c in corners]
    for k in range(len(cs)):
        i0, i1 = cs[k], cs[(k + 1) % len(cs)]
        if i1 <= i0:
            idx = np.concatenate([np.arange(i0, n), np.arange(0, i1 + 1)])
        else:
            idx = np.arange(i0, i1 + 1)
        if len(idx) < 8:
            continue
        seg = pts[idx]
        m = int(margin)
        core = seg[m:-m] if len(seg) > 2 * m + 4 else seg
        if len(core) < 4:
            continue
        ctr = core.mean(axis=0)
        _, _, vt = np.linalg.svd(core - ctr, full_matrices=False)
        u = vt[0]
        nrm = np.array([-u[1], u[0]])
        dev = np.abs((core - ctr) @ nrm)
        length = float((core[-1] - core[0]) @ u)
        if length < min_len or dev.max() > tol:
            continue
        proj = ctr + np.outer((seg - ctr) @ u, u)
        keep = idx[1:-1]          # вершины углов не трогаем
        out[keep, 0] = proj[1:-1, 0]
        out[keep, 1] = proj[1:-1, 1]
    return out


def gaussian_curve(pts: np.ndarray, sigma: float, free: np.ndarray) -> np.ndarray:
    """Низкочастотное сглаживание вдоль кривой — только по незакреплённым точкам."""
    if sigma <= 0:
        return pts
    r = max(1, int(3 * sigma))
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2)
    k /= k.sum()
    out = pts.copy()
    for c in range(2):
        ext = np.concatenate([pts[-r:, c], pts[:, c], pts[:r, c]])
        sm = np.convolve(ext, k, mode="same")[r:r + len(pts)]
        out[:, c] = np.where(free, sm, pts[:, c])
    return out


def trace_paths(binary: np.ndarray, eps: float, smooth: int = 0,
                curve_sigma: float = 0.0, corner_angle: float = 30.0,
                pin_radius: int = 26) -> list[np.ndarray]:
    """Контуры маски → список замкнутых ломаных (внешние + дыры).

    Сглаживание идёт только между углами: углы логотипа не меняются.
    """
    contours, _ = cv2.findContours(binary, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    paths: list[np.ndarray] = []
    for c in contours:
        if cv2.contourArea(c) < 30:
            continue
        ap = cv2.approxPolyDP(c, eps, True).reshape(-1, 2)
        if len(ap) < 3:
            continue
        if curve_sigma > 0:
            fine = resample_closed(ap, factor=6)
            corners = corner_indices(fine, angle_deg=corner_angle)
            # вокруг каждого угла замораживаем cluster вершин: так скругление
            # угла остаётся таким, как в оригинале, и не расплывается
            frozen = np.zeros(len(fine), dtype=bool)
            if len(corners):
                for i in corners:
                    d = np.abs(np.arange(len(fine)) - i)
                    d = np.minimum(d, len(fine) - d)
                    frozen[d <= pin_radius] = True
            ap = taubin_smooth(fine, frozen, iters=int(round(curve_sigma * 6)))
            ap = gaussian_curve(ap, curve_sigma * 5.0, ~frozen)
            ap = straighten_edges(ap, corners)
            ap = cv2.approxPolyDP(ap.reshape(-1, 1, 2).astype(np.float32),
                                   max(0.4, eps * 0.35), True).reshape(-1, 2)
            if len(ap) < 3:
                continue
        if smooth > 0:
            ap = chaikin(ap, smooth)
        paths.append(ap)
    return paths


def paths_to_svg(paths: list[np.ndarray], scale: float = 1.0,
                 dx: float = 0.0, dy: float = 0.0) -> str:
    """Пути в SVG-строке. scale — масштаб, dx/dy — сдвиг в системе лок-апа."""
    parts: list[str] = []
    for pts in paths:
        p = pts * scale + np.array([dx, dy])
        seg = [f"M{p[0][0]:.2f},{p[0][1]:.2f}"]
        seg += [f"L{x:.2f},{y:.2f}" for x, y in p[1:]]
        seg.append("Z")
        parts.append("".join(seg))
    return "".join(parts)


# ------------------------------------------------------------------ сборка ----

def build_lockup(mono_paths: list[np.ndarray], word_paths: list[np.ndarray],
                 gap_ratio: float = 0.2, word_ratio: float = 0.935
                 ) -> tuple[str, str, float, float]:
    """Возвращает (svg-путь монограммы, svg-путь надписи, ширина, высота)."""

    def bbox(paths):
        pts = np.vstack(paths)
        return pts[:, 0].min(), pts[:, 1].min(), pts[:, 0].max(), pts[:, 1].max()

    mx0, my0, mx1, my1 = bbox(mono_paths)
    wx0, wy0, wx1, wy1 = bbox(word_paths)

    mono_w, mono_h = mx1 - mx0, my1 - my0
    # пропорции локапа взяты из исходника: надпись уже монограммы (0.935) и
    # прижата к её левому краю, зазор — 0.2 высоты монограммы
    word_w = word_ratio * mono_w
    s = word_w / (wx1 - wx0)
    word_h = (wy1 - wy0) * s
    gap = gap_ratio * mono_h
    pad = 0.02 * mono_w
    total_w = mono_w + 2 * pad
    total_h = mono_h + gap + word_h + 2 * pad

    mono_svg = paths_to_svg(mono_paths, 1.0, pad - mx0, pad - my0)
    word_svg = paths_to_svg(word_paths, s,
                            pad - wx0 * s,
                            pad + mono_h + gap - wy0 * s)
    return mono_svg, word_svg, total_w, total_h


def svg_document(mono_d: str, word_d: str, w: float, h: float, width_mm: float) -> str:
    height_mm = width_mm * h / w
    stops = "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in GOLD_STOPS)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width_mm:.2f}mm" height="{height_mm:.2f}mm"
     viewBox="0 0 {w:.2f} {h:.2f}">
  <title>ДВ PRODUCTION</title>
  <defs>
    <linearGradient id="gold" x1="0.08" y1="0" x2="0.86" y2="1">
      {stops}
    </linearGradient>
  </defs>
  <path d="{mono_d}" fill="url(#gold)" fill-rule="evenodd"/>
  <path d="{word_d}" fill="{WORD_COLOR}" fill-rule="evenodd"/>
</svg>
"""


# ----------------------------------------------------------------- рендер -----

def render_svg(svg: Path, out_png: Path, width_cm: float, dpi: int = DPI) -> tuple[int, int]:
    """Рендер SVG в PNG нужного физического размера (1 px = 1/300 дюйма)."""
    target = width_cm / 2.54 * dpi
    base = pyvips.Image.new_from_file(str(svg), dpi=72, access="random")
    scale = target / base.width
    im = pyvips.Image.new_from_file(str(svg), dpi=72, scale=scale, access="random")
    # плотность 300 dpi: pHYs-сегмент PNG (px на миллиметр)
    im = im.copy(xres=dpi / 25.4, yres=dpi / 25.4)
    im.write_to_file(str(out_png), compression=6)
    return im.width, im.height


def make_cmyk(png: Path, out_tif: Path, profile: Path) -> None:
    im = pyvips.Image.new_from_file(str(png), access="sequential")
    cmyk = im.icc_transform(str(profile), pcs="lab", intent="relative",
                             black_point_compensation=True, input_profile="srgb", depth=8)
    cmyk = cmyk.copy(xres=im.get("xres"), yres=im.get("yres"))
    cmyk.write_to_file(str(out_tif), compression="lzw", predictor="horizontal")


def preview(png: Path, out: Path, bg: tuple[int, int, int], width: int = 1400) -> None:
    """Превью на подложке: ресайз через libvips (файл большой — PIL не тянет)."""
    im = pyvips.Image.new_from_file(str(png), access="random")
    flat = im.resize(width / im.width, kernel="lanczos3").flatten(background=list(bg))
    flat.write_to_file(str(out), Q=92)


def main() -> int:
    ap = argparse.ArgumentParser(description="Векторный логотип «ДВ PRODUCTION»")
    ap.add_argument("--profile", choices=list(PROFILES), default="original",
                    help="original — исходник 6144×6144 (полная монограмма, "
                         "клиентский файл обрезан); client — плоская версия "
                         "клиента (обрезана по краям)")
    ap.add_argument("--src", type=Path, help="переопределить файл-источник")
    ap.add_argument("--out-dir", type=Path, default=Path("/home/user/print-logo"))
    ap.add_argument("--width-cm", type=float, default=32.0,
                    help="ширина печатного PNG в см (лого-блок на баннере — 32 см)")
    ap.add_argument("--dpi", type=int, default=DPI)
    ap.add_argument("--no-cmyk", action="store_true")
    ap.add_argument("--profile-icc", type=Path,
                    default=ICC_DIR / "Coated_Fogra39L_VIGC_300.icc")
    args = ap.parse_args()

    pyvips.cache_set_max_mem(256 * 1024 * 1024)
    pyvips.cache_set_max(40)

    prof = PROFILES[args.profile]
    src = args.src or prof["src"]
    if not src.exists():
        print(f"нет источника: {src}")
        return 1

    args.out_dir.mkdir(parents=True, exist_ok=True)
    mono_rgb = load_box(src, prof["mono"], prof["upscale"])
    word_rgb = load_box(src, prof["word"], prof["upscale"])

    mono_bin = clean_mask(gold_matte(mono_rgb), prof["min_comp_mono"],
                           prof["fill_mono"], blur=prof["blur"])
    word_bin = clean_mask(word_matte(word_rgb), prof["min_comp_word"],
                           prof["fill_word"], open_r=2, blur=prof["blur"])

    mono_paths = trace_paths(mono_bin, prof["eps_mono"],
                              curve_sigma=prof.get("smooth_mono", 0.0))
    word_paths = trace_paths(word_bin, prof["eps_word"],
                              curve_sigma=prof.get("smooth_word", 0.0))
    print(f"источник: {src.name} ({args.profile}) — контуров: "
          f"монограмма {len(mono_paths)}, надпись {len(word_paths)}")

    mono_d, word_d, w, h = build_lockup(mono_paths, word_paths)
    svg_path = args.out_dir / "logo-dv-production.svg"
    svg_path.write_text(svg_document(mono_d, word_d, w, h, args.width_cm * 10.0),
                        encoding="utf-8")
    print(f"SVG: {svg_path.name} — {w:.0f}×{h:.0f} ед., ширина {args.width_cm:.0f} см")

    png = args.out_dir / f"logo-dv-production-{args.width_cm:.0f}cm-300dpi.png"
    pw, ph = render_svg(svg_path, png, args.width_cm, args.dpi)
    print(f"PNG: {png.name} {pw}×{ph} px, {png.stat().st_size // 1024} КБ, RGBA")

    if not args.no_cmyk and args.profile_icc.exists():
        tif = args.out_dir / f"logo-dv-production-{args.width_cm:.0f}cm-300dpi-cmyk-fogra39.tif"
        make_cmyk(png, tif, args.profile_icc)
        print(f"CMYK: {tif.name} {tif.stat().st_size // 1024 // 1024} МБ")

    preview(png, args.out_dir / "logo-dv-production-preview-magenta.jpg", (0x97, 0x1A, 0x81))
    preview(png, args.out_dir / "logo-dv-production-preview-dark.jpg", (24, 16, 26))
    print("превью: на мадженте и на тёмном фоне")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
