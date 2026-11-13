#!/usr/bin/env python3
"""Локальное размытие чужих вывесок в кадре с гостями.

Прямоугольники подобраны по превью 1408×768; края маски растушёваны,
чтобы размытие не читалось как «заплатка».
"""

from pathlib import Path

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
TARGET = HERE / "frames" / "03-gosti-u-stojki.png"

# (x0, y0, x1, y1, sigma)
BOXES = [
    (0, 170, 150, 255, 12),        # GUERLAIN слева
    (160, 195, 260, 250, 10),      # остаток GERLAIN
    (140, 320, 320, 385, 9),       # CHA... на кассе
    (310, 395, 430, 455, 9),       # остаток CHA на кассе
    (840, 150, 1010, 260, 12),     # CHANEL
    (1085, 175, 1215, 265, 12),    # DIOR / GUERLAIN справа
    (1200, 300, 1408, 420, 8),     # правые витрины
]


def soften_blur(img: np.ndarray, box, sigma: float, feather: int = 18) -> np.ndarray:
    x0, y0, x1, y1 = [int(v) for v in box]
    h, w = img.shape[:2]
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(w, x1), min(h, y1)
    if x1 <= x0 or y1 <= y0:
        return img

    blurred = cv2.GaussianBlur(img, (0, 0), sigma)
    mask = np.zeros((h, w), np.float32)
    mask[y0:y1, x0:x1] = 1.0
    mask = cv2.GaussianBlur(mask, (0, 0), feather)[:, :, None]
    return (img.astype(np.float32) * (1 - mask) + blurred.astype(np.float32) * mask
            ).clip(0, 255).astype(np.uint8)


def main() -> None:
    img = cv2.imread(str(TARGET))
    if img is None:
        raise SystemExit(f"нет файла {TARGET}")
    for box in BOXES:
        img = soften_blur(img, box[:4], box[4])
    cv2.imwrite(str(TARGET), img)
    print(f"  размыто {len(BOXES)} вывесок в {TARGET.name}")


if __name__ == "__main__":
    main()
