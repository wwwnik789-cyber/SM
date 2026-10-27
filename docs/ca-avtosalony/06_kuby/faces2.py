#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Автопоиск белой грани куба по точке-затравке.

Маска «белое» (высокая яркость, низкая насыщенность) → компонента связности,
содержащая затравку → минимальный описанный прямоугольник (перебор углов) →
квад по четырём углам. В отличие от прежнего autoface.py ищет не бирюзу,
а светлые грани, куда ставится логотип бренда.
"""
import numpy as np
from PIL import Image
from scipy import ndimage


def white_mask(im, vmin=140, smax=0.20):
    a = np.asarray(im.convert('RGB')).astype(np.float32) / 255.0
    mx = a.max(2)
    mn = a.min(2)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    return (mx > vmin / 255.0) & (sat < smax)


def pick_component(mask, seed):
    lab, n = ndimage.label(mask)
    x, y = seed
    tag = lab[y, x]
    if tag == 0:
        # ближайшая ненулевая метка в радиусе 25 px
        for r in range(1, 26):
            y0, y1 = max(0, y - r), min(mask.shape[0], y + r + 1)
            x0, x1 = max(0, x - r), min(mask.shape[1], x + r + 1)
            sub = lab[y0:y1, x0:x1]
            vals = sub[sub > 0]
            if vals.size:
                tag = np.bincount(vals).argmax()
                break
    if tag == 0:
        return None
    return lab == tag


def min_area_rect(points):
    """перебор углов: минимальный по площади прямоугольник вокруг точек"""
    pts = points.astype(np.float32)
    best = None
    for deg in np.arange(0, 90, 0.25):
        t = np.deg2rad(deg)
        c, s = np.cos(t), np.sin(t)
        xr = pts[:, 0] * c + pts[:, 1] * s
        yr = -pts[:, 0] * s + pts[:, 1] * c
        w = xr.max() - xr.min()
        h = yr.max() - yr.min()
        area = w * h
        if best is None or area < best[0]:
            best = (area, deg, xr.min(), yr.min(), w, h)
    area, deg, x0, y0, w, h = best
    t = np.deg2rad(deg)
    c, s = np.cos(t), np.sin(t)
    corners = []
    for (u, v) in [(x0, y0), (x0 + w, y0), (x0 + w, y0 + h), (x0, y0 + h)]:
        corners.append((u * c - v * s, u * s + v * c))
    return np.array(corners), area, deg


def face_quad(path, seed, inset=0.05, tol=6, vmin=140, smax=0.20):
    """квад белой грани по затравке; inset — отступ внутрь, доля стороны"""
    im = Image.open(path).convert('RGB')
    mask = white_mask(im, vmin, smax)
    comp = pick_component(mask, seed)
    if comp is None:
        raise ValueError('нет компоненты для затравки %s' % (seed,))
    yy, xx = np.nonzero(comp)
    corners, area, deg = min_area_rect(np.stack([xx, yy], 1))
    c0 = corners.mean(0)
    q = []
    for p in corners:
        d = p - c0
        q.append(tuple(c0 + d * (1 - 2 * inset)))
    # порядок: TL, TR, BR, BL по часовой от левого верхнего
    q.sort(key=lambda p: p[0] + p[1])
    tl = q[0]
    br = q[3]
    tr = q[1] if q[1][1] < q[2][1] else q[2]
    bl = q[2] if q[1][1] < q[2][1] else q[1]
    return [tuple(map(float, tl)), tuple(map(float, tr)),
            tuple(map(float, br)), tuple(map(float, bl))], area, deg, int(xx.size)


def preview(path, quads, out, box=None, scale=2):
    """нарисовать квады для проверки глазами"""
    from PIL import ImageDraw
    im = Image.open(path).convert('RGB')
    if box:
        im = im.crop(box)
        quads = [[(x - box[0], y - box[1]) for x, y in q] for q in quads]
    im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    for q in quads:
        qq = [(x * scale, y * scale) for x, y in q]
        d.line(qq + [qq[0]], fill=(255, 0, 0), width=3)
        d.line([qq[0], qq[2]], fill=(255, 160, 0), width=1)
    im.save(out)
    return out
