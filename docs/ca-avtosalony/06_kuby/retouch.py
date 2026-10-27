#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ретушь фотографий кубов: кадрирование, баланс белого, экспозиция, резкость."""
import os
import numpy as np
from PIL import Image, ImageFilter

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, 'istochniki')
OUT = os.path.join(ROOT, 'foto-posle')
os.makedirs(OUT, exist_ok=True)


def wb(img, strength=1.0):
    """серый мир по среднему"""
    a = np.asarray(img, np.float32)
    m = a.reshape(-1, 3).mean(axis=0)
    g = m.mean()
    gains = 1.0 + (g / np.maximum(m, 1e-3) - 1.0) * strength
    return np.clip(a * gains[None, None, :], 0, 255)


def curve(a, exposure=1.0, gamma=1.0, shadow=0.0, contrast=0.0, sat=1.0):
    x = np.clip(a / 255.0, 0, 1)
    x = np.clip(x * exposure, 0, 1)
    x = x ** gamma
    if shadow > 0:
        # подъём теней без выжигания светов
        x = x + shadow * (1 - x) ** 3 * x ** 0.35
    if contrast:
        x = np.clip((x - 0.5) * (1 + contrast) + 0.5, 0, 1)
    if sat != 1.0:
        g = x.mean(axis=2, keepdims=True)
        x = np.clip(g + (x - g) * sat, 0, 1)
    return np.clip(x * 255, 0, 255)


def wb_patch(a, box, target=None):
    """нейтрализация по светлой грани куба, яркость не меняется"""
    x0, y0, x1, y1 = box
    m = a[y0:y1, x0:x1].reshape(-1, 3).mean(axis=0)
    g = m.mean()
    gains = np.clip(g / np.maximum(m, 1e-3), 0.7, 1.5)
    return np.clip(a * gains[None, None, :], 0, 255)


def process(src, dst, crop=None, rotate=0, patch=None, **kw):
    im = Image.open(os.path.join(SRC, src)).convert('RGB')
    if rotate:
        im = im.rotate(rotate, expand=True)
    if crop:
        im = im.crop(crop)
    a = wb(im, kw.pop('wb_strength', 1.0))
    if patch:
        a = wb_patch(a, patch[0])
    a = curve(a, **kw)
    im = Image.fromarray(a.astype(np.uint8))
    im = im.filter(ImageFilter.UnsharpMask(radius=1.4, percent=70, threshold=2))
    im.save(os.path.join(OUT, dst), 'JPEG', quality=94, subsampling=0, optimize=True)
    print(dst, im.size, round(os.path.getsize(os.path.join(OUT, dst)) / 1e6, 2), 'МБ')


if __name__ == '__main__':
    # 01: верхние четыре куба, без шины и рюкзака
    process('IMG_20260325_184106_644.jpg', 'kub-01-shouroom.jpg',
            crop=(860, 620, 2060, 3060),
            patch=((95, 634, 285, 761),),
            exposure=1.46, gamma=1.0, shadow=0.10, contrast=0.12, sat=1.02,
            wb_strength=0.45)

    # 02: кубы у витрины, тянем тени (съёмка против света)
    process('IMG_20260325_184059_106.jpg', 'kub-02-vitrina.jpg',
            crop=(1035, 960, 1990, 3160),
            exposure=1.72, gamma=0.92, shadow=0.26, contrast=0.12, sat=0.98,
            wb_strength=0.75)

    # 03: производство, кадр повёрнут на 90° — разворачиваем и кадрируем
    process('IMG_4312.jpg', 'kub-03-proizvodstvo.jpg',
            rotate=-90,
            crop=(0, 600, 3400, 5120),
            exposure=1.16, gamma=1.0, shadow=0.08, contrast=0.06, sat=0.98,
            wb_strength=0.5)
