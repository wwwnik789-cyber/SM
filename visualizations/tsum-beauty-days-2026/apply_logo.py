#!/usr/bin/env python3
"""Наложение логотипа TSUM на пустую плашку стойки по перспективе.

Углы плашки уточняются автоматически внутри заданного прямоугольника:
ищем чёрную рамку + белое поле, берём четырёхугольник. Затем гомография
переносит векторную плашку в плоскость грани.
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
RAW = HERE / "raw"
OUT = HERE / "frames"
PLAQUE = HERE / "assets" / "plaque-tsum.png"

# кадр -> (x0, y0, x1, y1) поисковый прямоугольник вокруг плашки
ROIS = {
    "s1-hall.png": (670, 555, 885, 685),
    "s2-atrium.png": (695, 545, 835, 665),
    "s3-people-hall.png": (600, 530, 800, 685),
}
# ручные углы там, где автодетекция сбивается на бликах (TL, TR, BR, BL)
OVERRIDES = {
    "s3-people-hall.png": [(615, 556), (775, 542), (774, 660), (614, 672)],
}
OUT_NAMES = {
    "s1-hall.png": "01-vitrina-bez-lyudej.png",
    "s2-atrium.png": "02-atrium-bez-lyudej.png",
    "s3-people-hall.png": "03-gosti-u-stojki.png",
}


def order_corners(pts: np.ndarray) -> np.ndarray:
    """TL, TR, BR, BL по сумме и разности координат."""
    s = pts.sum(axis=1)
    d = np.diff(pts, axis=1).ravel()
    return np.array([
        pts[np.argmin(s)], pts[np.argmin(d)],
        pts[np.argmax(s)], pts[np.argmax(d)],
    ], dtype=np.float32)


def find_plaque(img: np.ndarray, roi: tuple[int, int, int, int]) -> np.ndarray:
    x0, y0, x1, y1 = roi
    patch = img[y0:y1, x0:x1]
    gray = cv2.cvtColor(patch, cv2.COLOR_BGR2GRAY)
    # плашка светлая, рамка тёмная -> порог по светлому полю
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, mask = cv2.threshold(blur, 175, 255, cv2.THRESH_BINARY)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        raise RuntimeError(f"плашка не найдена в {roi}")
    c = max(cnts, key=cv2.contourArea)
    peri = cv2.arcLength(c, True)
    for eps in (0.02, 0.03, 0.05, 0.08):
        ap = cv2.approxPolyDP(c, eps * peri, True)
        if len(ap) == 4:
            pts = ap.reshape(4, 2).astype(np.float32)
            pts += np.array([x0, y0], np.float32)
            return order_corners(pts)
    rect = cv2.minAreaRect(c)
    pts = cv2.boxPoints(rect).astype(np.float32) + np.array([x0, y0], np.float32)
    return order_corners(pts)


def paste_logo(img: np.ndarray, corners: np.ndarray, plaque: np.ndarray) -> np.ndarray:
    """Печатаем только тёмные штрихи: белое поле плашки остаётся родным.

    Так логотип наследует освещение, отражения и цвет полки в кадре.
    """
    ph, pw = plaque.shape[:2]
    ctr = corners.mean(axis=0)
    corners = ctr + (corners - ctr) * 0.90     # внутрь рамки

    dst = np.array([[0, 0], [pw - 1, 0], [pw - 1, ph - 1], [0, ph - 1]], np.float32)
    M = cv2.getPerspectiveTransform(dst, corners)
    warped = cv2.warpPerspective(plaque, M, (img.shape[1], img.shape[0]),
                                 flags=cv2.INTER_AREA, borderMode=cv2.BORDER_REPLICATE)

    # плотность штриха: 1 там, где плашка чёрная; 0 на белом поле
    ink = 1.0 - warped.astype(np.float32).mean(axis=2) / 255.0
    # мягкий край, чтобы штрихи не «звенели» после даунскейла
    ink = cv2.GaussianBlur(ink, (0, 0), 0.6)
    ink = np.clip((ink - 0.18) / 0.82, 0, 1)[:, :, None]

    # multiply: тёмная краска затемняет то, что уже есть в кадре
    out = img.astype(np.float32) * (1.0 - 0.93 * ink)
    return np.clip(out, 0, 255).astype(np.uint8)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    plaque = cv2.imread(str(PLAQUE), cv2.IMREAD_COLOR)
    for name, roi in ROIS.items():
        img = cv2.imread(str(RAW / name), cv2.IMREAD_COLOR)
        if name in OVERRIDES:
            corners = np.array(OVERRIDES[name], np.float32)
        else:
            corners = find_plaque(img, roi)
        res = paste_logo(img, corners, plaque)
        dst = OUT / OUT_NAMES[name]
        cv2.imwrite(str(dst), res)
        print(f"  {dst.name}: плашка по {', '.join(f'({int(x)},{int(y)})' for x, y in corners)}")


if __name__ == "__main__":
    main()
