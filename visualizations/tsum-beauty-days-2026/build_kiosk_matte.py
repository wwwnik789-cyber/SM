#!/usr/bin/env python3
"""Маска стойки TSUM из чистого рендера: силуэт по насыщенным и тёмным пикселям."""

from pathlib import Path

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
SRC = HERE / "source" / "02-render-concept.jpg"
OUT = HERE / "kiosk-rgba.png"


def main() -> None:
    img = cv2.imread(str(SRC), cv2.IMREAD_COLOR)
    h, w = img.shape[:2]
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    sat, val = hsv[:, :, 1].astype(np.int16), hsv[:, :, 2].astype(np.int16)

    # тело стойки: насыщенный оранжевый либо тёмные детали
    core = ((sat > 60) | (val < 120)).astype(np.uint8) * 255
    core = cv2.morphologyEx(core, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))

    # выпуклая оболочка закрывает белые участки (верхняя грань, окно)
    contours, _ = cv2.findContours(core, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    big = max(contours, key=cv2.contourArea)
    hull = cv2.convexHull(big)
    mask = np.zeros((h, w), np.uint8)
    cv2.drawContours(mask, [hull], -1, 255, -1)
    mask = cv2.erode(mask, np.ones((3, 3), np.uint8))

    # мягкий край
    alpha = cv2.GaussianBlur(mask, (3, 3), 0)
    ys, xs = np.where(mask > 0)
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()

    rgba = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
    rgba[:, :, 3] = alpha
    crop = rgba[y0:y1 + 1, x0:x1 + 1]
    cv2.imwrite(str(OUT), crop)
    print(f"  {OUT.name}: {crop.shape[1]}×{crop.shape[0]}, доля заливки "
          f"{(mask > 0).sum() / mask.size:.2%}")


if __name__ == "__main__":
    main()
