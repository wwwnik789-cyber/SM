#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Поиск бирюзовых граней кубов на визуализациях: компоненты + углы."""
import sys, glob, os
import numpy as np
from PIL import Image
from collections import deque

def teal_mask(a):
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    mx = a.max(axis=2)
    return ((B - R) > 22) & ((G - R) > 16) & (G > 45) & (B > 55) & (mx < 210) & (R < 130)

def components(path, minsize=2500):
    im = Image.open(path).convert('RGB')
    a = np.asarray(im, np.int16)
    m = teal_mask(a)
    H, W = m.shape
    seen = np.zeros_like(m, bool); out = []; step = 2
    for y in range(0, H, step):
        for x in range(0, W, step):
            if m[y, x] and not seen[y, x]:
                q = deque([(y, x)]); seen[y, x] = True; n = 0
                y0 = y1 = y; x0 = x1 = x; pts = []
                while q:
                    cy, cx = q.popleft(); n += 1
                    y0 = min(y0, cy); y1 = max(y1, cy); x0 = min(x0, cx); x1 = max(x1, cx)
                    if n < 40000: pts.append((cx, cy))
                    for dy, dx in ((step,0),(-step,0),(0,step),(0,-step)):
                        ny, nx = cy+dy, cx+dx
                        if 0 <= ny < H and 0 <= nx < W and m[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True; q.append((ny, nx))
                if n > minsize:
                    p = np.array(pts)
                    s = p[:,0] + p[:,1]; d = p[:,0] - p[:,1]
                    cs = [tuple(int(v) for v in p[np.argmin(s)]), tuple(int(v) for v in p[np.argmax(d)]),
                          tuple(int(v) for v in p[np.argmax(s)]), tuple(int(v) for v in p[np.argmin(d)])]
                    out.append((n, (x0,y0,x1,y1), cs, (W,H)))
    out.sort(reverse=True)
    return out

if __name__ == '__main__':
    pats = sys.argv[1:] or ['src/viz-*.png', 'src/viz-*.jpg']
    files = []
    for p in pats: files += glob.glob(p)
    for f in sorted(set(files)):
        res = components(f)
        print(os.path.basename(f), 'компонент:', len(res))
        for n, bb, cs, sz in res[:4]:
            print('   n=%6d bbox=%s  TL%s TR%s BR%s BL%s' % (n, bb, cs[0], cs[1], cs[2], cs[3]))
