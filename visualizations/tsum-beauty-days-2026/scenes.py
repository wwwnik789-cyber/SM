#!/usr/bin/env python3
"""Сцены: 3D-стойка в интерьере универмага.

Стойка рендерится в RGBA, ставится на пол по масштабу (высота 180 см против
роста человека), получает контактную тень, отражение и цветовую подгонку
под свет интерьера.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import kiosk3d as k3  # noqa: E402

RAW = HERE / "raw"
OUT = HERE / "frames"
SOURCE = HERE / "source"


# ------------------------------------------------------------------ утилиты
def render_kiosk(view: str, px_h: int = 1500) -> Image.Image:
    scene = k3.build()
    kw = {
        "front": dict(target=(43, 88, 26), fov=22, aspect=0.80, margin=0.96,
                      direction=(0.06, 0.07, 1.0)),
        "three_quarter": dict(target=(43, 88, 24), fov=26, aspect=0.80, margin=0.96,
                              direction=(0.50, 0.13, 0.86)),
        "side": dict(target=(43, 90, 34), fov=24, aspect=0.80, margin=0.96,
                     direction=(0.95, 0.10, 0.30)),
    }[view]
    cam = k3.framed_camera(scene, **kw)
    rgba = Image.fromarray(k3.render(scene, cam, int(px_h * 0.80), px_h, ss=1.6), "RGBA")
    return rgba


def contact_shadow(size, cx, cy, rx, ry, blur, strength) -> Image.Image:
    layer = Image.new("L", size, 0)
    d = ImageDraw.Draw(layer)
    d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=255)
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    return layer.point(lambda v: int(v * strength))


def reflection(sprite: Image.Image, height_px: int, opacity: float) -> Image.Image:
    """Отражение в глянцевом полу: вертикальный флип с затуханием."""
    h = int(sprite.height * 0.42)
    ref = sprite.transpose(Image.FLIP_TOP_BOTTOM).crop((0, sprite.height - h, sprite.width, sprite.height))
    ref = ref.filter(ImageFilter.GaussianBlur(2.2))
    alpha = np.asarray(ref.split()[3], np.float32) / 255.0
    fade = np.linspace(opacity, 0.0, h, dtype=np.float32)[:, None]
    alpha = (alpha * fade * 255).astype(np.uint8)
    ref.putalpha(Image.fromarray(alpha, "L"))
    return ref


def match_light(sprite: Image.Image, region: Image.Image, amount=0.55) -> Image.Image:
    """Подтягивает цвет стойки к свету сцены под ней."""
    arr = np.asarray(sprite, np.float32)
    rr = np.asarray(region.convert("RGB"), np.float32).reshape(-1, 3).mean(axis=0)
    sr = arr[..., :3][arr[..., 3] > 200].mean(axis=0)
    ratio = np.clip(rr / np.maximum(sr, 1.0), 0.55, 1.35)
    ratio = 1.0 + (ratio - 1.0) * amount
    arr[..., :3] *= ratio
    arr[..., :3] = arr[..., :3] * 0.94 + 10
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")


def composite(bg: Image.Image, sprite: Image.Image, cx: int, base_y: int,
              shadow=(1.0, 0.20), reflect=0.30, light_dir=(-0.55, 0.55)) -> Image.Image:
    """Ставит стойку: падающая тень по свету -> отражение -> стойка -> AO."""
    out = bg.convert("RGBA")
    w, h = out.size
    sw = sprite.width

    # 1) падающая тень: трапеция, сдвинутая по направлению света
    sh_layer = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(sh_layer)
    skew = int(sw * 0.55 * light_dir[0])
    depth = int(sw * 0.34)
    d.polygon([
        (cx - sw // 2 + int(sw * 0.06), base_y - 2),
        (cx + sw // 2 - int(sw * 0.02), base_y - 2),
        (cx + sw // 2 + skew, base_y + depth),
        (cx - sw // 2 + skew + int(sw * 0.30), base_y + depth),
    ], fill=255)
    sh_layer = sh_layer.filter(ImageFilter.GaussianBlur(max(18, sw * 0.075)))

    # 2) контактная тень под корпусом
    contact = Image.new("L", (w, h), 0)
    dc = ImageDraw.Draw(contact)
    ry = max(5, int(sw * 0.09))
    dc.ellipse([cx - int(sw * 0.50), base_y - ry // 2, cx + int(sw * 0.50), base_y + ry], fill=255)
    contact = contact.filter(ImageFilter.GaussianBlur(max(4, sw * 0.022)))

    occ = np.asarray(sh_layer, np.float32) * shadow[1] * 0.72 \
        + np.asarray(contact, np.float32) * shadow[1] * 1.05
    occ = np.clip(occ, 0, 235) / 255.0
    arr = np.asarray(out, np.float32)
    arr[..., :3] *= (1.0 - occ)[:, :, None]
    out = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")

    # 3) отражение
    if reflect > 0:
        ref = reflection(sprite, sprite.height, reflect)
        out.alpha_composite(ref, (cx - ref.width // 2, base_y))

    # 4) стойка
    out.alpha_composite(sprite, (cx - sw // 2, base_y - sprite.height))

    # 5) AO по силуэту
    sil = Image.new("L", (w, h), 0)
    ImageDraw.Draw(sil).rectangle(
        [cx - sw // 2, base_y - sprite.height, cx + sw // 2, base_y], fill=255)
    sil = sil.filter(ImageFilter.GaussianBlur(max(2, sw * 0.012)))
    edge = np.asarray(sil, np.float32) - np.asarray(
        sil.filter(ImageFilter.MinFilter(5)), np.float32)
    edge = np.clip(edge, 0, 255) / 255.0
    arr = np.asarray(out, np.float32)
    arr[..., :3] *= (1.0 - edge * 0.30)[:, :, None]
    out = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")
    return out.convert("RGB")


def warm(img: Image.Image, k=1.0) -> Image.Image:
    a = np.asarray(img, np.float32)
    a[..., 0] *= 1.0 + 0.035 * k
    a[..., 2] *= 1.0 - 0.02 * k
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def grain(img: Image.Image, amount=2.2, seed=5) -> Image.Image:
    rng = np.random.default_rng(seed)
    a = np.asarray(img, np.float32)
    a += rng.normal(0, amount, a.shape[:2])[:, :, None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


# ------------------------------------------------------------------ сцены
def scene_atrium(people: bool) -> Image.Image:
    bg = Image.open(RAW / "bg-atrium-empty.png").convert("RGB")

    # стойка стоит в центре прохода; высота 180 см ≈ 470 px на этом плане
    sprite = render_kiosk("three_quarter", 1500)
    target_h = 470
    sprite = sprite.resize((int(sprite.width * target_h / sprite.height), target_h), Image.LANCZOS)

    cx = int(bg.width * 0.44)
    base_y = int(bg.height * 0.905)
    sprite = match_light(sprite, bg.crop((cx - 200, base_y - 60, cx + 200, base_y + 40)))
    out = composite(bg, sprite, cx, base_y, shadow=(1.15, 0.30), reflect=0.22)
    out = grain(warm(out, 0.6))
    return out
