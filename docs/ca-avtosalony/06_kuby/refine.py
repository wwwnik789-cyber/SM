#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Уточнение квада грани по градиенту: каждая сторона подтягивается
к ближайшему сильному перепаду яркости (ребру куба).

Задаём грубые 4 угла, скрипт двигает стороны по нормали в пределах ±search,
берёт медианное смещение по нескольким точкам вдоль стороны.
"""
import numpy as np
from PIL import Image, ImageDraw


def _gray(im):
    a = np.asarray(im.convert('L')).astype(np.float32)
    return a


def refine_quad(path, quad, search=18, samples=9, inset=0.05):
    im = Image.open(path).convert('RGB')
    g = _gray(im)
    H, W = g.shape
    q = [np.array(p, dtype=np.float64) for p in quad]
    for i in range(4):
        a, b = q[i], q[(i + 1) % 4]
        d = b - a
        L = np.hypot(*d)
        if L < 4:
            continue
        n = np.array([-d[1], d[0]]) / L          # нормаль
        # направление наружу: от центра грани
        c = sum(q) / 4.0
        mid = (a + b) / 2
        if np.dot(n, mid - c) < 0:
            n = -n
        offsets = []
        for t in np.linspace(0.15, 0.85, samples):
            p = a + d * t
            best, bestv = 0.0, -1
            for off in np.arange(-search, search + 0.5, 0.5):
                x = p[0] + n[0] * off
                y = p[1] + n[1] * off
                xi, yi = int(round(x)), int(round(y))
                if xi < 2 or yi < 2 or xi > W - 3 or yi > H - 3:
                    continue
                # производная вдоль нормали
                v = abs(g[yi, xi + int(n[0])] - g[yi, xi - int(n[0])]) \
                    if abs(n[0]) > abs(n[1]) else \
                    abs(g[yi + int(n[1]), xi] - g[yi - int(n[1]), xi])
                if v > bestv:
                    bestv, best = v, off
            if bestv > 6:
                offsets.append(best)
        if not offsets:
            continue
        shift = float(np.median(offsets))
        q[i] = q[i] + n * shift
        q[(i + 1) % 4] = q[(i + 1) % 4] + n * shift
    c = sum(q) / 4.0
    out = []
    for p in q:
        out.append(tuple(c + (p - c) * (1 - 2 * inset)))
    return [tuple(map(float, p)) for p in out]


def draw(path, quads, out, scale=1.0, labels=None):
    im = Image.open(path).convert('RGB')
    if scale != 1.0:
        im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    for i, q in enumerate(quads):
        qq = [(x * scale, y * scale) for x, y in q]
        d.line(qq + [qq[0]], fill=(255, 0, 0), width=4)
        for p in qq:
            d.ellipse([p[0] - 5, p[1] - 5, p[0] + 5, p[1] + 5], fill=(255, 255, 0))
        if labels:
            d.text((qq[0][0] + 8, qq[0][1] - 18), labels[i], fill=(255, 255, 0))
    im.save(out)
    return out
