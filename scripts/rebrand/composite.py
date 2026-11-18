"""
Наложение фирменных макетов SM Production на рендеры конструкций.

Рендеры-подложки (visualizations/rebrand-2026/_plates/*.jpg) сгенерированы с лицевой
поверхностью цвета хромакей (#00FF00). Скрипт:
  1. находит зелёную поверхность и её 4 угла (или берёт углы из SCENES вручную),
  2. натягивает макет с перспективой (логотип — исходные пиксели, без перерисовки),
  3. переносит освещение сцены (яркость зелёного = карта света) на печать,
  4. сохраняет предметы/людей перед конструкцией (маска по зелёному),
  5. перекрашивает зелёные отсветы на полу в фирменный синий.

Запуск:  python3 scripts/rebrand/composite.py [--debug]
Результат: visualizations/rebrand-2026/*.jpg
"""
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import layouts  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
PLATES = ROOT / "visualizations/rebrand-2026/_plates"
OUT = ROOT / "visualizations/rebrand-2026"
DBG = ROOT / ".cache/rebrand-debug"

# Цвет отсветов вместо зелёного: средний тон баннера (BGR, 0..1)
SPILL_TINT = np.array([0.95, 0.62, 0.42], np.float32)

# имя подложки: (имя результата, макет(ы), ручные углы или None)
# углы: [[TL],[TR],[BR],[BL]] в пикселях подложки; если None — ищутся автоматически.
# Для нескольких поверхностей (ролл-апы) — список макетов, поверхности сортируются слева направо.
SCENES = {
    "presswall-5x3": ("sm-presswall-5x3", ["5x3_presswall"], None),
    # Для сцен, где угол перекрыт (трибуна, стойка), углы считаются как пересечение
    # прямых, подогнанных по видимым участкам кромок: {сторона: (от, до)} —
    # диапазон строк (left/right) или столбцов (top/bottom) подложки.
    "stage-6x3": ("sm-stage-backdrop-6x3", ["6x3_stage"],
                  {"left": (150, 360), "bottom": (420, 900)}),
    "registration-4x2": ("sm-registration-4x2.5", ["4x2.5_registration"],
                         {"right": (180, 268), "bottom": (395, 560)}),
    "expo-stand": ("sm-expo-stand-back-wall", ["3x2_expo"],
                   {"right": (240, 470), "bottom": (520, 960)}),
    "lightbox": ("sm-lightbox-2.5x1.5", ["5x3_presswall"], None),
    "rollups": ("sm-rollup-pair", ["0.85x2_rollup", "0.85x2_rollup"], None),
}


def green_measure(img):
    f = img.astype(np.float32)
    b, g, r = f[..., 0], f[..., 1], f[..., 2]
    return g - np.maximum(r, b)          # «насколько пиксель зелёный»


def face_masks(img, min_area=0.004):
    gd = green_measure(img)
    hard = (gd > 60).astype(np.uint8)
    hard = cv2.morphologyEx(hard, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    hard = cv2.morphologyEx(hard, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(hard)
    total = img.shape[0] * img.shape[1]
    comps = [i for i in range(1, n) if stats[i, cv2.CC_STAT_AREA] > min_area * total]
    comps.sort(key=lambda i: stats[i, cv2.CC_STAT_LEFT])
    return [(lab == i).astype(np.uint8) for i in comps], gd


def order_corners(pts):
    pts = np.asarray(pts, np.float32).reshape(-1, 2)
    s, d = pts.sum(1), pts[:, 1] - pts[:, 0]
    return np.array([pts[np.argmin(s)], pts[np.argmin(d)], pts[np.argmax(s)], pts[np.argmax(d)]],
                    np.float32)


def fit_quad(mask):
    """4 угла поверхности: аппроксимация выпуклой оболочки четырёхугольником."""
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    hull = cv2.convexHull(max(cnts, key=cv2.contourArea))
    peri = cv2.arcLength(hull, True)
    for eps in np.linspace(0.005, 0.08, 60):
        approx = cv2.approxPolyDP(hull, eps * peri, True)
        if len(approx) == 4:
            return order_corners(approx)
    # запасной вариант — минимальный прямоугольник
    return order_corners(cv2.boxPoints(cv2.minAreaRect(hull)))


def _edge_points(mask, side, lo, hi):
    pts = []
    if side in ("left", "right"):
        for y in range(lo, hi):
            xs = np.flatnonzero(mask[y])
            if xs.size:
                pts.append((xs[0] if side == "left" else xs[-1], y))
    else:
        for x in range(lo, hi):
            ys = np.flatnonzero(mask[:, x])
            if ys.size:
                pts.append((x, ys[0] if side == "top" else ys[-1]))
    return np.array(pts, np.float32)


def _intersect(l1, l2):
    (vx1, vy1, x1, y1), (vx2, vy2, x2, y2) = l1, l2
    A = np.array([[vx1, -vx2], [vy1, -vy2]], np.float64)
    t = np.linalg.solve(A, np.array([x2 - x1, y2 - y1], np.float64))
    return np.array([x1 + t[0] * vx1, y1 + t[0] * vy1], np.float32)


def fit_quad_lines(mask, ranges):
    """Углы = пересечения прямых по 4 кромкам. ranges задаёт видимые участки
    перекрытых кромок; для остальных берётся средние 80% стороны."""
    init = fit_quad(mask)
    tl, tr, br, bl = init
    default = {
        "top": (int(tl[0] + 0.1 * (tr[0] - tl[0])), int(tr[0] - 0.1 * (tr[0] - tl[0]))),
        "bottom": (int(bl[0] + 0.1 * (br[0] - bl[0])), int(br[0] - 0.1 * (br[0] - bl[0]))),
        "left": (int(tl[1] + 0.1 * (bl[1] - tl[1])), int(bl[1] - 0.1 * (bl[1] - tl[1]))),
        "right": (int(tr[1] + 0.1 * (br[1] - tr[1])), int(br[1] - 0.1 * (br[1] - tr[1]))),
    }
    default.update(ranges or {})
    lines = {}
    for side, (lo, hi) in default.items():
        pts = _edge_points(mask, side, lo, hi)
        lines[side] = cv2.fitLine(pts, cv2.DIST_HUBER, 0, 0.01, 0.01).ravel()
    return np.array([_intersect(lines["top"], lines["left"]), _intersect(lines["top"], lines["right"]),
                     _intersect(lines["bottom"], lines["right"]), _intersect(lines["bottom"], lines["left"])],
                    np.float32)


def lighting_map(img, mask, gd):
    """Карта освещения из яркости зелёного канала внутри поверхности."""
    g = img[..., 1].astype(np.float32)
    m = mask > 0
    ref = np.percentile(g[m], 70)
    shade = np.where(m, g / max(ref, 1), 1.0).astype(np.float32)
    # заполняем дыры (предметы перед поверхностью) и сглаживаем шум
    shade = cv2.inpaint(np.clip(shade * 127, 0, 255).astype(np.uint8),
                        (~m).astype(np.uint8) * 255, 9, cv2.INPAINT_TELEA).astype(np.float32) / 127
    shade = cv2.GaussianBlur(shade, (0, 0), 9)
    return np.clip(shade, 0.45, 1.25)


def warp_layout(layout, quad, shape):
    h, w = shape[:2]
    # предварительное уменьшение до размера поверхности — без муара на тонких линиях
    qw = max(np.linalg.norm(quad[1] - quad[0]), np.linalg.norm(quad[2] - quad[3]))
    qh = max(np.linalg.norm(quad[3] - quad[0]), np.linalg.norm(quad[2] - quad[1]))
    tw, th = int(qw * 2), int(qh * 2)
    if tw < layout.shape[1]:
        layout = cv2.resize(layout, (tw, th), interpolation=cv2.INTER_AREA)
    lh, lw = layout.shape[:2]
    src = np.array([[0, 0], [lw - 1, 0], [lw - 1, lh - 1], [0, lh - 1]], np.float32)
    M = cv2.getPerspectiveTransform(src, quad.astype(np.float32))
    warped = cv2.warpPerspective(layout, M, (w, h), flags=cv2.INTER_LINEAR,
                                 borderMode=cv2.BORDER_CONSTANT)
    cover = cv2.warpPerspective(np.full((lh, lw), 255, np.uint8), M, (w, h), flags=cv2.INTER_LINEAR)
    return warped, cover.astype(np.float32) / 255


def composite(plate, layouts_list, quads=None, debug_name=None):
    img = plate.copy()
    masks, gd = face_masks(img)
    if quads is None:
        quads = [fit_quad(m) for m in masks]
    elif isinstance(quads, dict):
        quads = [fit_quad_lines(m, quads) for m in masks]
    if len(quads) != len(layouts_list):
        raise RuntimeError(f"Найдено поверхностей: {len(quads)}, макетов: {len(layouts_list)}")

    out = img.astype(np.float32)
    all_face = np.zeros(img.shape[:2], np.float32)
    for lay, quad, mask in zip(layouts_list, quads, masks):
        warped, cover = warp_layout(lay, np.asarray(quad, np.float32), img.shape)
        shade = lighting_map(img, mask, gd)
        printed = warped.astype(np.float32) * shade[..., None] ** 0.85
        # мягкая маска «где виден зелёный» — предметы перед поверхностью сохраняются
        soft = np.clip((gd - 25) / 45, 0, 1)
        near = cv2.dilate(mask, np.ones((7, 7), np.uint8)).astype(np.float32)
        a = (soft * near * cover)[..., None]
        out = out * (1 - a) + printed * a
        all_face = np.maximum(all_face, near * cover)

    # despill: остатки зелёного на краях и отсветы на полу/стенах → фирменный синий
    b, g, r = out[..., 0], out[..., 1], out[..., 2]
    spill = np.clip(g - np.maximum(r, b), 0, None)
    spill *= (1 - 0.0 * all_face)
    out[..., 1] -= spill
    out += spill[..., None] * SPILL_TINT[None, None, :] * 0.9
    res = np.clip(out, 0, 255).astype(np.uint8)

    if debug_name:
        DBG.mkdir(parents=True, exist_ok=True)
        dbg = plate.copy()
        for q in quads:
            cv2.polylines(dbg, [np.int32(q)], True, (0, 0, 255), 2)
            for k, p in enumerate(q):
                cv2.putText(dbg, str(k), tuple(np.int32(p)), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        cv2.imwrite(str(DBG / f"{debug_name}_quad.jpg"), dbg)
        print(debug_name, [np.round(q).astype(int).tolist() for q in quads])
    return res


# Доп. перекраска элементов конструкции, которые генератор сделал зелёными
# (например, боковина стенда): зелёные пиксели в box → цвет стены из точки ref.
RECOLOR = {
    "expo-stand": {"box": (420, 220, 487, 600), "ref": (350, 400)},
}


def recolor_green(img, box, ref):
    x0, y0, x1, y1 = box
    roi = img[y0:y1, x0:x1].astype(np.float32)
    gd = roi[..., 1] - np.maximum(roi[..., 0], roi[..., 2])
    m = np.clip((gd - 6) / 12, 0, 1)[..., None]
    lum = roi.mean(2, keepdims=True)
    ref_px = img[ref[1], ref[0]].astype(np.float32)
    green_lum = np.median(lum[m[..., 0] > 0.9]) if (m > 0.9).any() else lum.mean()
    target = ref_px[None, None, :] * (lum / max(green_lum, 1))
    img[y0:y1, x0:x1] = np.clip(roi * (1 - m) + target * m, 0, 255).astype(np.uint8)
    return img


def main():
    debug = "--debug" in sys.argv
    lays = layouts.build_all()
    OUT.mkdir(parents=True, exist_ok=True)
    for plate_name, (out_name, lay_names, quads) in SCENES.items():
        plate = cv2.imread(str(PLATES / f"{plate_name}.jpg"))
        if plate is None:
            print("нет подложки", plate_name)
            continue
        if plate_name in RECOLOR:
            plate = recolor_green(plate.copy(), **RECOLOR[plate_name])
        res = composite(plate, [lays[n] for n in lay_names], quads,
                        debug_name=plate_name if debug else None)
        cv2.imwrite(str(OUT / f"{out_name}.jpg"), res, [cv2.IMWRITE_JPEG_QUALITY, 92])
        print("✓", out_name)


if __name__ == "__main__":
    main()
