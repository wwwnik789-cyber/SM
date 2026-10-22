"""Вектор монограммы «Д» (верхняя часть логотипа) — один SVG с ровными контурами.

Ключевое отличие от logo_vector.py: контуры не ломаная, а подогнанные
кубические кривые Безье с гладкостью (регуляризация по вторым разностям
опорных точек). Углы остаются острыми: концы каждой кривой жёстко
закреплены на вершинах углов, поэтому в точке стыка двух кривых касательные
не совпадают — угол остаётся углом.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import cv2
import numpy as np
import pyvips

import logo_vector as lv

PROFILE = lv.PROFILES["original"]


# ----------------------------------------------------------------- геометрия --

def resample_uniform(pts: np.ndarray, step: float = 1.5) -> np.ndarray:
    """Передискретизация по длине дуги с постоянным шагом."""
    closed = np.vstack([pts, pts[:1]])
    seg = np.linalg.norm(np.diff(closed, axis=0), axis=1)
    s = np.concatenate([[0.0], np.cumsum(seg)])
    total = s[-1]
    n = max(16, int(round(total / step)))
    t = np.linspace(0.0, total, n, endpoint=False)
    x = np.interp(t, s, closed[:, 0])
    y = np.interp(t, s, closed[:, 1])
    return np.stack([x, y], axis=1)


def detect_corners(pts: np.ndarray, angle_deg: float = 32.0,
                   window: int = 12, min_sep: int = 40) -> np.ndarray:
    """Вершины углов: места, где кривая резко меняет направление."""
    n = len(pts)
    prev = pts - np.roll(pts, window, axis=0)
    nxt = np.roll(pts, -window, axis=0) - pts
    a1 = np.arctan2(prev[:, 1], prev[:, 0])
    a2 = np.arctan2(nxt[:, 1], nxt[:, 0])
    turn = np.abs((a2 - a1 + np.pi) % (2 * np.pi) - np.pi)
    cand = np.nonzero(turn > np.radians(angle_deg))[0]
    # самая «острая» точка в каждом скоплении
    picked: list[int] = []
    for i in cand:
        if picked and (i - picked[-1]) < min_sep:
            if turn[i] > turn[picked[-1]]:
                picked[-1] = int(i)
        else:
            picked.append(int(i))
    return np.array(picked, dtype=int)


def _basis_funs(span: int, u: float, knots: np.ndarray, degree: int) -> np.ndarray:
    """Локальные базисные функции B-сплайна (алгоритм The NURBS Book)."""
    N = np.zeros(degree + 1)
    left = np.zeros(degree + 1)
    right = np.zeros(degree + 1)
    N[0] = 1.0
    for j in range(1, degree + 1):
        left[j] = u - knots[span + 1 - j]
        right[j] = knots[span + j] - u
        saved = 0.0
        for r in range(j):
            den = right[r + 1] + left[j - r]
            temp = N[r] / den if den != 0.0 else 0.0
            N[r] = saved + right[r + 1] * temp
            saved = left[j - r] * temp
        N[j] = saved
    return N


def bspline_matrix(t: np.ndarray, n_ctrl: int, degree: int = 3) -> np.ndarray:
    """Матрица базиса равномерного B-сплайна с зажатыми концами."""
    n_seg = max(1, n_ctrl - degree)
    knots = np.concatenate([np.zeros(degree + 1),
                            np.arange(1, n_seg) / n_seg,
                            np.ones(degree + 1)])
    B = np.zeros((len(t), n_ctrl))
    for i, u in enumerate(t):
        u = min(max(u, 0.0), 1.0)
        span = int(np.searchsorted(knots, u, side="right")) - 1
        # допустимые сегменты: от degree до n_ctrl (зажатые концы)
        span = min(max(span, degree), n_ctrl - 1)
        N = _basis_funs(span, u, knots, degree)
        for k in range(degree + 1):
            B[i, span - degree + k] += N[k]
    return B


def fit_bezier_chain(pts: np.ndarray, seg_len: float = 26.0,
                     lam: float = 0.35, straight_tol: float = 1.2,
                     straight_min_len: float = 120.0) -> np.ndarray:
    """Подгонка цепочки кубических кривых по точкам контура.

    Базис — равномерный кубический B-сплайн; целевая функция штрафует
    вторые разности опорных точек, поэтому кривая получается ровной
    (максимум кривизны сглажен), а не «дрожащей» копией пиксельной маски.
    Концы кривой закреплены на первой и последней точке — это вершины углов.
    """
    if len(pts) < 6:
        return np.array([pts[0], pts[-1]], dtype=np.float64)
    d = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    s = np.concatenate([[0.0], np.cumsum(d)])
    if s[-1] <= 0:
        return np.array([pts[0], pts[-1]], dtype=np.float64)
    t = s / s[-1]
    n_ctrl = int(round(s[-1] / seg_len)) + 3
    n_ctrl = max(4, min(n_ctrl, len(pts) - 2))
    B = bspline_matrix(t, n_ctrl)
    D = np.zeros((max(0, n_ctrl - 2), n_ctrl))
    for i in range(n_ctrl - 2):
        D[i, i:i + 3] = (1.0, -2.0, 1.0)
    A = B.T @ B + lam * len(pts) * (D.T @ D)
    rhs = B.T @ pts
    try:
        Q = np.linalg.solve(A, rhs)
        if not np.all(np.isfinite(Q)):
            raise np.linalg.LinAlgError
    except np.linalg.LinAlgError:
        Q = np.linalg.lstsq(B, pts, rcond=None)[0]
    # кривая не должна уходить дальше самого ребра
    if float(np.abs(Q - Q[0]).max()) > 3.0 * s[-1]:
        return np.array([pts[0], pts[-1]], dtype=np.float64)
    Q[0] = pts[0]
    Q[-1] = pts[-1]
    # касательные на концах ребра задаём по исходной кривой: иначе у вершины
    # угла возникает «клюв» — кривая входит в угол не по своей касательной
    step_px = max(s[-1] / len(pts), 1e-6)
    span = int(min(max(2, round(25.0 / step_px)), len(pts) - 1))
    d0 = pts[span] - pts[0]
    d1 = pts[-1] - pts[-1 - span]
    n0 = float(np.hypot(d0[0], d0[1]))
    n1 = float(np.hypot(d1[0], d1[1]))
    if n0 > 0 and len(Q) > 3:
        h0 = min(float(np.linalg.norm(Q[1] - Q[0])), n0)
        Q[1] = Q[0] + d0 / n0 * h0
    if n1 > 0 and len(Q) > 3:
        h1 = min(float(np.linalg.norm(Q[-2] - Q[-1])), n1)
        Q[-2] = Q[-1] - d1 / n1 * h1
    # ровные прямые: прямые участки (в том числе внутри смешанных рёбер)
    # прищёлкиваются к точной прямой — уходит «дрожь» края от AI-рендера
    Q = flatten_straight_runs(Q, tol=straight_tol, min_len=straight_min_len)
    return Q


def flatten_straight_runs(ctrl: np.ndarray, tol: float = 1.2,
                          min_len: float = 120.0, ramp: int = 4
                          ) -> np.ndarray:
    """Прямые участки опорных точек прищёлкиваются к точной прямой.

    Ищутся скользящим окном (TLS-аппроксимация); на границах участка вес
    нарастает плавно, поэтому в месте перехода не появляется «ступенька».
    """
    n = len(ctrl)
    if n < 6:
        return ctrl
    out = ctrl.copy()
    i = 0
    while i < n:
        best = None
        j = i + 4
        while j < min(n, i + 400):
            seg = ctrl[i:j + 1]
            ctr = seg.mean(axis=0)
            _, _, vt = np.linalg.svd(seg - ctr, full_matrices=False)
            u = vt[0]
            nrm = np.array([-u[1], u[0]])
            dev = np.abs((seg - ctr) @ nrm)
            L = abs(float((seg[-1] - seg[0]) @ u))
            if dev.max() > tol:
                break
            if L >= min_len:
                best = (j, ctr, u)
            j += 1
        if best is None:
            i += 1
            continue
        j, ctr, u = best
        nrm = np.array([-u[1], u[0]])
        proj = ctr + np.outer((ctrl - ctr) @ u, u)
        a = max(0, i - ramp)
        b = min(n, j + 1 + ramp)
        w = np.ones(b - a)
        if i - a > 0:
            w[:i - a] = np.linspace(0.0, 1.0, i - a + 1)[:-1]
        if b - (j + 1) > 0:
            w[j + 1 - a:] = np.linspace(1.0, 0.0, b - j)[1:]
        out[a:b, 0] = ctrl[a:b, 0] + (proj[a:b, 0] - ctrl[a:b, 0]) * w
        out[a:b, 1] = ctrl[a:b, 1] + (proj[a:b, 1] - ctrl[a:b, 1]) * w
        i = j + 1
    return out


def chain_to_path(ctrl: np.ndarray, first: bool) -> str:
    """Опорные точки B-сплайна -> сегменты кубической Безье (строка SVG)."""
    n = len(ctrl)
    if n < 2:
        return ""
    if n < 4:
        p0, p1 = ctrl[0], ctrl[-1]
        head = f"M{p0[0]:.2f},{p0[1]:.2f}" if first else ""
        return f"{head} L{p1[0]:.2f},{p1[1]:.2f}"
    parts: list[str] = []
    for j in range(n - 3):
        Q0, Q1, Q2, Q3 = ctrl[j], ctrl[j + 1], ctrl[j + 2], ctrl[j + 3]
        if j == 0:
            b1 = Q0 + (Q1 - Q0) / 3.0
        else:
            b1 = Q0 + (Q1 - ctrl[j - 1]) / 6.0
        if j + 4 < n:
            b2 = Q1 - (ctrl[j + 3] - Q0) / 6.0
        else:
            b2 = Q1 - (Q1 - Q0) / 3.0
        p0, p3 = Q0, Q1
        if j == 0 and first:
            parts.append(f"M{p0[0]:.2f},{p0[1]:.2f}")
        parts.append(f"C{b1[0]:.2f},{b1[1]:.2f} {b2[0]:.2f},{b2[1]:.2f} "
                     f"{p3[0]:.2f},{p3[1]:.2f}")
    return " ".join(parts)


def contour_to_path(raw: np.ndarray, seg_len: float = 26.0,
                    lam: float = 0.35, step: float = 1.5,
                    angle: float = 32.0, window: int = 12,
                    min_sep: int = 40, straight_tol: float = 1.2,
                    straight_min_len: float = 120.0) -> str:
    """Контур -> путь SVG: острые углы + ровные дуги (кубические Безье)."""
    pts = resample_uniform(raw, step=step)
    corners = detect_corners(pts, angle_deg=angle, window=window, min_sep=min_sep)
    n = len(pts)
    cs = [int(c) for c in corners]
    if not cs:
        ctrl = fit_bezier_chain(pts, seg_len, lam, straight_tol, straight_min_len)
        return chain_to_path(ctrl, True) + " Z"
    pieces: list[str] = []
    for k in range(len(cs)):
        i0, i1 = cs[k], cs[(k + 1) % len(cs)]
        if i1 <= i0:
            idx = np.concatenate([np.arange(i0, n), np.arange(0, i1 + 1)])
        else:
            idx = np.arange(i0, i1 + 1)
        edge = pts[idx]
        ctrl = fit_bezier_chain(edge, seg_len, lam, straight_tol, straight_min_len)
        pieces.append(chain_to_path(ctrl, k == 0))
    return " ".join(pieces) + " Z"


def _svg_doc(body: str, w: float, h: float, width_mm: float, title: str) -> str:
    height_mm = width_mm * h / w
    stops = "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in lv.GOLD_STOPS)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width_mm:.2f}mm" height="{height_mm:.2f}mm"
     viewBox="0 0 {w:.2f} {h:.2f}">
  <title>{title}</title>
  <defs>
    <linearGradient id="gold" x1="0.08" y1="0" x2="0.86" y2="1">
      {stops}
    </linearGradient>
  </defs>
  {body}
</svg>
"""


def build_mark_svg(mono_paths: list[np.ndarray], width_mm: float,
                   seg_len: float, lam: float) -> tuple[str, float, float]:
    """SVG монограммы — верхняя часть логотипа, без надписи."""
    all_pts = np.vstack(mono_paths)
    x0, y0 = all_pts.min(axis=0)
    x1, y1 = all_pts.max(axis=0)
    pad = 0.02 * (x1 - x0)
    x0, y0, x1, y1 = x0 - pad, y0 - pad, x1 + pad, y1 + pad
    w, h = x1 - x0, y1 - y0
    d = " ".join(contour_to_path(raw - np.array([x0, y0]), seg_len, lam)
                 for raw in mono_paths)
    body = f'<path d="{d}" fill="url(#gold)" fill-rule="evenodd"/>'
    return _svg_doc(body, w, h, width_mm, "ДВ PRODUCTION — монограмма"), w, h


def build_lockup_svg(mono_paths: list[np.ndarray], word_paths: list[np.ndarray],
                     width_mm: float, seg_len: float, lam: float,
                     gap_ratio: float = 0.2, word_ratio: float = 0.935
                     ) -> tuple[str, float, float]:
    """SVG полного локапа: монограмма + надпись PRODUCTION."""
    mp = np.vstack(mono_paths)
    wp = np.vstack(word_paths)
    mx0, my0 = mp.min(axis=0)
    mx1, my1 = mp.max(axis=0)
    wx0, wy0 = wp.min(axis=0)
    wx1, wy1 = wp.max(axis=0)
    mono_w, mono_h = mx1 - mx0, my1 - my0
    word_w = word_ratio * mono_w
    s = word_w / (wx1 - wx0)
    word_h = (wy1 - wy0) * s
    gap = gap_ratio * mono_h
    pad = 0.02 * mono_w
    w = mono_w + 2 * pad
    h = mono_h + gap + word_h + 2 * pad

    d_mono = " ".join(contour_to_path(raw - np.array([mx0, my0]), seg_len, lam)
                      for raw in mono_paths)
    d_word = " ".join(
        contour_to_path((raw - np.array([wx0, wy0])) * s
                        + np.array([pad, pad + mono_h + gap]),
                        seg_len * 0.55, lam, step=0.9, angle=28.0, window=7,
                        min_sep=14, straight_tol=1.0, straight_min_len=60.0)
        for raw in word_paths)
    body = (f'<path d="{d_mono}" fill="url(#gold)" fill-rule="evenodd"/>\n'
            f'  <path d="{d_word}" fill="{lv.WORD_COLOR}" fill-rule="evenodd"/>')
    return _svg_doc(body, w, h, width_mm, "ДВ PRODUCTION"), w, h


# ------------------------------------------------------------------- вывод --

def render_svg(svg: Path, out_png: Path, width_cm: float, dpi: int) -> tuple[int, int]:
    target = width_cm / 2.54 * dpi
    base = pyvips.Image.new_from_file(str(svg), dpi=72, access="random")
    scale = target / base.width
    im = pyvips.Image.new_from_file(str(svg), dpi=72, scale=scale, access="random")
    im = im.copy(xres=dpi / 25.4, yres=dpi / 25.4)
    im.write_to_file(str(out_png), compression=6)
    return im.width, im.height


def make_cmyk(png: Path, out_tif: Path, profile: Path) -> None:
    im = pyvips.Image.new_from_file(str(png), access="sequential")
    im = im.icc_transform(profile, intent="relative", depth=8,
                          black_point_compensation=True)
    im.write_to_file(str(out_tif), compression="lzw", predictor="horizontal")


def _contours(mask: np.ndarray, all_components: bool = False) -> list[np.ndarray]:
    """Контуры маски: внешний + дыры (или все компоненты, если all_components).

    Для монограммы берём один внешний контур и его счётные зоны; для надписи —
    все буквы, каждая со своими счётными зонами.
    """
    contours, hier = cv2.findContours(mask.astype(np.uint8) * 255,
                                      cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    hier = hier[0]
    paths: list[np.ndarray] = []
    if all_components:
        for i, hrow in enumerate(hier):
            if hrow[3] == -1:                      # верхний уровень
                paths.append(contours[i].reshape(-1, 2).astype(np.float64))
                for j, h2 in enumerate(hier):
                    if h2[3] == i:                 # дыри этой буквы
                        paths.append(contours[j].reshape(-1, 2).astype(np.float64))
    else:
        outer = int(np.argmax([cv2.contourArea(c) for c in contours]))
        paths.append(contours[outer].reshape(-1, 2).astype(np.float64))
        for i, hrow in enumerate(hier):
            if hrow[3] == outer:
                paths.append(contours[i].reshape(-1, 2).astype(np.float64))

    def area(p: np.ndarray) -> float:
        x, y = p[:, 0], p[:, 1]
        return 0.5 * abs(float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1))))

    paths.sort(key=lambda p: -area(p))
    return paths


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Вектор логотипа «ДВ PRODUCTION»: монограмма и полный локап")
    ap.add_argument("--out-dir", type=Path, default=Path("/home/user/print-mark"))
    ap.add_argument("--width-cm", type=float, default=32.0)
    ap.add_argument("--dpi", type=int, default=300)
    ap.add_argument("--seg-len", type=float, default=26.0,
                    help="длина сегмента Безье в единицах исходника (2×)")
    ap.add_argument("--lam", type=float, default=0.35, help="вес гладкости")
    ap.add_argument("--only", choices=["mark", "lockup", "both"], default="both")
    ap.add_argument("--profile-icc", type=Path,
                    default=lv.ICC_DIR / "Coated_Fogra39L_VIGC_300.icc")
    args = ap.parse_args()

    pyvips.cache_set_max_mem(256 * 1024 * 1024)
    pyvips.cache_set_max(40)

    prof = lv.PROFILES["original"]
    mono = lv.load_box(prof["src"], prof["mono"], prof["upscale"])
    mono_paths = _contours(lv.clean_mask(lv.gold_matte(mono), prof["min_comp_mono"],
                                          prof["fill_mono"], blur=prof["blur"]))
    word = lv.load_box(prof["src"], prof["word"], prof["upscale"])
    word_paths = _contours(lv.clean_mask(lv.word_matte(word), prof["min_comp_word"],
                                          prof["fill_word"], open_r=2, blur=prof["blur"]),
                           all_components=True)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    jobs = []
    if args.only in ("mark", "both"):
        jobs.append(("mark", "logo-dv-production-mark",
                     lambda: build_mark_svg(mono_paths, args.width_cm * 10.0,
                                            args.seg_len, args.lam)))
    if args.only in ("lockup", "both"):
        jobs.append(("lockup", "logo-dv-production",
                     lambda: build_lockup_svg(mono_paths, word_paths,
                                              args.width_cm * 10.0, args.seg_len,
                                              args.lam)))

    for kind, name, builder in jobs:
        svg, w, h = builder()
        svg_path = args.out_dir / f"{name}.svg"
        svg_path.write_text(svg, encoding="utf-8")
        n_seg = svg.count("C")
        print(f"SVG: {svg_path.name}  viewBox {w:.1f}×{h:.1f} ед., "
              f"{args.width_cm * 10:.0f}×{args.width_cm * 10 * h / w:.1f} мм, "
              f"{n_seg} сегментов Безье, {len(svg) // 1024} КБ")

        png = args.out_dir / f"{name}-32cm-300dpi.png"
        pw, ph = render_svg(svg_path, png, args.width_cm, args.dpi)
        print(f"PNG: {png.name} {pw}×{ph} px, RGBA, {args.dpi} dpi")

        if args.profile_icc.exists():
            tif = args.out_dir / f"{name}-32cm-300dpi-cmyk-fogra39.tif"
            make_cmyk(png, tif, args.profile_icc)
            print(f"CMYK: {tif.name} (FOGRA39)")
        else:
            print("CMYK: нет ICC-профиля, пропущено")

        for bname, bg in (("preview-magenta", (151, 26, 128)),
                          ("preview-dark", (18, 18, 20))):
            im = pyvips.Image.new_from_file(str(png), access="random")
            flat = im.resize(1400 / im.width, kernel="lanczos3").flatten(background=list(bg))
            flat.write_to_file(str(args.out_dir / f"{name}-{bname}.jpg"), Q=92)
        print("превью: на мадженте и на тёмном фоне")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
