#!/usr/bin/env python3
"""Вставка стойки TSUM в интерьер: масштаб, тень, отражение, цветовой баланс.

Масштаб задаётся высотой в пикселях; для кадра 1408×768 при съёмке с высоты
глаз 1 px ≈ 3,4 мм на переднем плане, поэтому 180 см ≈ 525 px.

Запуск из корня репозитория:
    .venv/bin/python visualizations/tsum-beauty-days-2026/compose.py
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
RAW = HERE / "raw"
OUT = HERE / "frames"
KIOSK = HERE / "kiosk-rgba.png"

H_CM = 180.0


def load_rgba(path: Path) -> np.ndarray:
    img = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if img.shape[2] == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
    return img


def match_light(sprite: np.ndarray, scene_ref: np.ndarray) -> np.ndarray:
    """Подтягиваем яркость и цвет стойки к освещению сцены."""
    rgb = sprite[:, :, :3]
    m = sprite[:, :, 3] > 200
    if m.sum() == 0:
        return sprite
    ref_mean = scene_ref.reshape(-1, 3).mean(axis=0)
    src_mean = rgb[m].mean(axis=0)
    ratio = np.clip(ref_mean / np.maximum(src_mean, 1.0), 0.55, 1.35)
    ratio = 1.0 + (ratio - 1.0) * 0.75            # подтягиваем к свету сцены
    out = sprite.copy().astype(np.float32)
    out[:, :, :3] *= ratio
    # лёгкий подъём теней, чтобы не было «вырезанного» вида
    out[:, :, :3] = out[:, :, :3] * 0.88 + 6
    return np.clip(out, 0, 255)


def place(bg: np.ndarray, kiosk: np.ndarray, x: int, base_y: int, height_px: int,
          shadow_strength=0.62, reflection=0.20, shadow_dir=1) -> np.ndarray:
    """Порядок слоёв: падающая тень -> отражение -> стойка -> AO по контуру."""
    scale = height_px / kiosk.shape[0]
    kw = max(1, int(round(kiosk.shape[1] * scale)))
    kh = max(1, int(round(kiosk.shape[0] * scale)))
    sprite = cv2.resize(kiosk, (kw, kh), interpolation=cv2.INTER_AREA)

    h, w = bg.shape[:2]
    y_a, y_b = max(0, base_y - 30), min(h, base_y + 40)
    x_a, x_b = max(0, x - 120), min(w, x + 120)
    sprite = match_light(sprite.astype(np.float32), bg[y_a:y_b, x_a:x_b].astype(np.float32))

    out = bg.astype(np.float32)
    x0, y0 = int(round(x - kw / 2)), int(round(base_y - kh))

    # --- 1. падающая тень (свет сбоку, смещение по shadow_dir)
    shadow = np.zeros((h, w), np.float32)
    shift = int(kw * 0.55) * shadow_dir
    poly = np.array([
        [x0 + int(kw * 0.05), base_y - 2],
        [x0 + kw - int(kw * 0.02), base_y - 2],
        [x0 + kw + shift, base_y + int(height_px * 0.30)],
        [x0 + int(kw * 0.30) + shift, base_y + int(height_px * 0.34)],
    ], np.int32)
    cv2.fillPoly(shadow, [poly], 1.0)
    shadow = cv2.GaussianBlur(shadow, (0, 0), max(10, height_px * 0.05))

    contact = np.zeros((h, w), np.float32)
    ay = max(5, int(height_px * 0.032))
    cv2.ellipse(contact, (int(x), int(base_y + ay * 0.15)), (int(kw * 0.50), ay), 0, 0, 360, 1.0, -1)
    contact = cv2.GaussianBlur(contact, (0, 0), max(3, height_px * 0.012))

    ground = np.clip(shadow * shadow_strength * 0.7 + contact * shadow_strength * 1.15, 0, 0.94)
    out *= (1.0 - ground)[:, :, None]

    # --- 2. отражение поверх тени (глянцевый пол)
    if reflection > 0:
        ref_h = int(min(kh * 0.40, h - base_y))
        if ref_h > 6:
            ref = np.flip(sprite, axis=0)[:ref_h]
            a = np.flip(sprite[:, :, 3:4], axis=0)[:ref_h] / 255.0
            ref_rgb = cv2.GaussianBlur(ref[:, :, :3], (0, 0), max(1.5, height_px * 0.004))
            fade = np.linspace(reflection, 0.0, ref_h, dtype=np.float32)[:, None, None]
            a = a * fade
            xs0, xs1 = max(0, x0), min(w, x0 + kw)
            if xs1 > xs0:
                fs0 = xs0 - x0
                sub = out[base_y:base_y + ref_h, xs0:xs1]
                a_sub = a[:, fs0:fs0 + (xs1 - xs0), :]
                r_sub = ref_rgb[:, fs0:fs0 + (xs1 - xs0)]
                n = min(sub.shape[0], a_sub.shape[0], r_sub.shape[0])
                out[base_y:base_y + n, xs0:xs1] = (sub[:n] * (1 - a_sub[:n])
                                                    + r_sub[:n] * a_sub[:n])

    # --- 3. сама стойка
    cx0, cy0 = max(0, x0), max(0, y0)
    cx1, cy1 = min(w, x0 + kw), min(h, y0 + kh)
    if cx1 <= cx0 or cy1 <= cy0:
        return bg
    sx0, sy0 = cx0 - x0, cy0 - y0
    patch = sprite[sy0:sy0 + (cy1 - cy0), sx0:sx0 + (cx1 - cx0)]
    alpha = patch[:, :, 3:4] / 255.0
    region = out[cy0:cy1, cx0:cx1]
    out[cy0:cy1, cx0:cx1] = region * (1 - alpha) + patch[:, :, :3] * alpha

    # --- 4. AO по силуэту
    sil = np.zeros((h, w), np.float32)
    cv2.rectangle(sil, (max(0, x0), max(0, y0)), (min(w, x0 + kw), min(h, y0 + kh)), 1.0, -1)
    sil = cv2.GaussianBlur(sil, (0, 0), max(2, height_px * 0.010))
    edge = np.clip(cv2.dilate(sil, np.ones((5, 5), np.uint8)) - sil, 0, 1)
    out *= (1.0 - edge * 0.30)[:, :, None]
    return np.clip(out, 0, 255).astype(np.uint8)


def add_grain(img: np.ndarray, amount=2.6, seed=7) -> np.ndarray:
    rng = np.random.default_rng(seed)
    noise = rng.normal(0, amount, img.shape[:2]).astype(np.float32)
    out = img.astype(np.float32) + noise[:, :, None]
    return np.clip(out, 0, 255).astype(np.uint8)


def grade(img: np.ndarray, warmth=1.0) -> np.ndarray:
    f = img.astype(np.float32)
    f[:, :, 2] *= 1.0 + (warmth - 1.0) * 0.2
    f[:, :, 0] *= 1.0 + (warmth - 1.0) * 0.5
    return np.clip(f, 0, 255).astype(np.uint8)


SCENES = [
    ("bg-01-hall.png", 470, 700, 640, 0.60, 0.30, 1.03, "hall", 1),
    ("bg-02-entrance.png", 690, 660, 600, 0.55, 0.32, 0.99, "entrance", 1),
    ("interior-atrium.png", 700, 748, 400, 0.50, 0.20, 1.02, "atrium", 1),
]


def main() -> None:
    OUT.mkdir(exist_ok=True)
    kiosk = load_rgba(KIOSK)
    for name, x, base_y, height, sh, rf, warm, tag, sdir in SCENES:
        bg = cv2.imread(str(RAW / name), cv2.IMREAD_COLOR)
        if bg.shape[1] != 1408:
            bg = cv2.resize(bg, (1408, int(bg.shape[0] * 1408 / bg.shape[1])))
        res = grade(place(bg, kiosk, x, base_y, height, sh, rf, sdir), warmth=warm)
        res = add_grain(res)
        dst = OUT / f"01-{tag}-bez-lyudej.png"
        cv2.imwrite(str(dst), res)
        print(f"  {dst.name}: {res.shape[1]}×{res.shape[0]}, стойка {height} px")


if __name__ == "__main__":
    main()
