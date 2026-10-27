#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Автоподбор грани куба: маска бирюзы -> ориентированный прямоугольник -> квад."""
import numpy as np
from PIL import Image
from collections import deque

def teal_mask(a):
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    mx = a.max(axis=2)
    return ((B - R) > 22) & ((G - R) > 16) & (G > 45) & (B > 55) & (mx < 215) & (R < 135)

def biggest_comp(path, minsize=2500):
    a = np.asarray(Image.open(path).convert('RGB'), np.int16)
    m = teal_mask(a)
    H, W = m.shape
    seen = np.zeros_like(m, bool); best = None; step = 2
    for y in range(0, H, step):
        for x in range(0, W, step):
            if m[y, x] and not seen[y, x]:
                q = deque([(y, x)]); seen[y, x] = True; pts = []
                while q:
                    cy, cx = q.popleft()
                    if len(pts) < 60000: pts.append((cx, cy))
                    for dy, dx in ((step,0),(-step,0),(0,step),(0,-step)):
                        ny, nx = cy+dy, cx+dx
                        if 0 <= ny < H and 0 <= nx < W and m[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True; q.append((ny, nx))
                if len(pts) > minsize and (best is None or len(pts) > len(best)):
                    best = pts
    return np.array(best), (W, H)

def min_area_rect(pts):
    best = None
    for ang in np.arange(0, 90, 0.5):
        r = np.deg2rad(ang)
        c, s = np.cos(r), np.sin(r)
        x = pts[:,0]*c + pts[:,1]*s
        y = -pts[:,0]*s + pts[:,1]*c
        w = x.max()-x.min(); h = y.max()-y.min()
        if best is None or w*h < best[0]:
            best = (w*h, ang, x.min(), y.min(), w, h)
    _, ang, x0, y0, w, h = best
    r = np.deg2rad(ang); c, s = np.cos(r), np.sin(r)
    def to_img(x, y):
        return (x*c - y*s, x*s + y*c)
    corners = [to_img(x0, y0), to_img(x0+w, y0), to_img(x0+w, y0+h), to_img(x0, y0+h)]
    return [(float(u), float(v)) for u, v in corners]

def face_quad(path, inset=0.06, minsize=2500):
    pts, size = biggest_comp(path, minsize)
    if pts is None or len(pts) == 0:
        return None
    q = min_area_rect(pts)
    cx = sum(p[0] for p in q)/4; cy = sum(p[1] for p in q)/4
    q = [((p[0]-cx)*(1-inset)+cx, (p[1]-cy)*(1-inset)+cy) for p in q]
    return q, size
