#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Мини-рендерер для визуализаций стенда Topotoon.

Без Blender и OpenGL: сцена собирается из параллелепипедов и плоскостей,
растеризуется в numpy по-пиксельно. Даёт честную перспективу, сортировку
по глубине, освещение по нормали, туман и текстуры — этого достаточно,
чтобы показать заказчику объём, материалы и свет.

Координаты стенда:
    x — вдоль фронта 9 м, от 0 (левый угол) до 9
    y — глубина, 0 — линия фронта, 5.04 — задняя стена
    z — высота, 0 — пол, 3.0 — низ верхней обвязки
"""
import numpy as np
from PIL import Image

# ------------------------------------------------------------------ камера
class Camera:
    def __init__(self, pos, look, fov=48, w=1600, h=900, roll=0.0):
        self.pos = np.array(pos, np.float64)
        self.w, self.h = w, h
        fwd = np.array(look, np.float64) - self.pos
        fwd /= np.linalg.norm(fwd)
        up = np.array([0.0, 0.0, 1.0])
        right = np.cross(fwd, up)
        right /= np.linalg.norm(right)
        up2 = np.cross(right, fwd)
        if roll:
            c, s = np.cos(roll), np.sin(roll)
            right, up2 = right * c + up2 * s, -right * s + up2 * c
        self.fwd, self.right, self.up = fwd, right, up2
        self.f = (w / 2) / np.tan(np.radians(fov) / 2)

    def project(self, P):
        """P: (N,3) мировые точки → (N,2) пиксели, (N,) глубина."""
        d = P - self.pos
        cam = np.stack([d @ self.right, d @ self.up, d @ self.fwd], -1)
        z = np.maximum(cam[:, 2], 1e-4)
        sx = self.w / 2 + cam[:, 0] / z * self.f
        sy = self.h / 2 - cam[:, 1] / z * self.f
        return np.stack([sx, sy], -1), cam[:, 2]


# ------------------------------------------------------------------ объекты
class Quad:
    """Плоский четырёхугольник с текстурой; текстура может быть однотонной."""
    __slots__ = ("pts", "normal", "tex", "emissive", "tint", "uv", "blur", "refl")

    def __init__(self, pts, tex=None, color=(0.5, 0.5, 0.5), emissive=0.0,
                 tint=1.0, blur=0.0, refl=0.0):
        self.pts = np.array(pts, np.float64)
        n = np.cross(self.pts[1] - self.pts[0], self.pts[3] - self.pts[0])
        self.normal = n / (np.linalg.norm(n) + 1e-9)
        self.tex = tex if tex is not None else np.array(color, np.float32)
        self.emissive = emissive
        self.tint = tint
        self.blur = blur
        self.refl = refl
        # uv по умолчанию — натянуть текстуру на весь четырёхугольник
        self.uv = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], np.float32)


class Box:
    """Параллелепипед: 6 граней, каждая — Quad."""
    def __init__(self, x0, y0, z0, x1, y1, z1, color=(0.6, 0.6, 0.62),
                 top=None, side=None, emissive=0.0, tex_top=None,
                 tex_front=None, tex_back=None, tint=1.0):
        top_c = top if top is not None else color
        side_c = side if side is not None else color
        self.quads = []
        # верх
        self.quads.append(Quad([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)],
                               tex=tex_top, color=top_c, emissive=emissive, tint=tint))
        # низ
        self.quads.append(Quad([(x0, y1, z0), (x1, y1, z0), (x1, y0, z0), (x0, y0, z0)],
                               color=side_c, tint=tint))
        # фронт (y0)
        self.quads.append(Quad([(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)],
                               tex=tex_front, color=side_c, emissive=emissive, tint=tint))
        # тыл (y1)
        self.quads.append(Quad([(x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1)],
                               tex=tex_back, color=side_c, emissive=emissive, tint=tint))
        # левый (x0)
        self.quads.append(Quad([(x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1)],
                               color=side_c, emissive=emissive, tint=tint))
        # правый (x1)
        self.quads.append(Quad([(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)],
                               color=side_c, emissive=emissive, tint=tint))


def plane(x0, y0, x1, y1, z, tex=None, color=(0.5, 0.5, 0.5), emissive=0.0, tint=1.0):
    """Горизонтальная плоскость."""
    return Quad([(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)],
                tex=tex, color=color, emissive=emissive, tint=tint)


def wall_y(y, x0, x1, z0, z1, tex=None, color=(0.5, 0.5, 0.5), emissive=0.0, tint=1.0):
    """Стена, перпендикулярная y (плоскость xz)."""
    return Quad([(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)],
                tex=tex, color=color, emissive=emissive, tint=tint)


def wall_x(x, y0, y1, z0, z1, tex=None, color=(0.5, 0.5, 0.5), emissive=0.0, tint=1.0):
    """Стена, перпендикулярная x (плоскость yz)."""
    return Quad([(x, y0, z0), (x, y1, z0), (x, y1, z1), (x, y0, z1)],
                tex=tex, color=color, emissive=emissive, tint=tint)


def disc(cx, cy, r, z, seg=28, color=(0.8, 0.8, 0.8), emissive=0.0):
    """Горизонтальный круг — столешницы, пуфы, капсулы."""
    quads = []
    for i in range(seg):
        a0 = 2 * np.pi * i / seg
        a1 = 2 * np.pi * (i + 1) / seg
        quads.append(Quad([(cx, cy, z),
                           (cx + r * np.cos(a0), cy + r * np.sin(a0), z),
                           (cx + r * np.cos(a1), cy + r * np.sin(a1), z),
                           (cx + r * np.cos(a1) * 0.02 + cx * 0.98, cy + r * np.sin(a1) * 0.02, z)],
                          color=color, emissive=emissive))
    return quads


def cylinder(cx, cy, r, z0, z1, seg=24, color=(0.8, 0.8, 0.8), cap=True):
    """Вертикальный цилиндр из боковых полос."""
    quads = []
    for i in range(seg):
        a0 = 2 * np.pi * i / seg
        a1 = 2 * np.pi * (i + 1) / seg
        p0 = (cx + r * np.cos(a0), cy + r * np.sin(a0))
        p1 = (cx + r * np.cos(a1), cy + r * np.sin(a1))
        quads.append(Quad([(p0[0], p0[1], z0), (p1[0], p1[1], z0),
                           (p1[0], p1[1], z1), (p0[0], p0[1], z1)], color=color))
    if cap:
        quads.append(Quad([(cx - r, cy - r * 0.02, z1), (cx + r, cy - r * 0.02, z1),
                           (cx + r, cy + r * 0.02, z1), (cx - r, cy + r * 0.02, z1)],
                          color=color))
    return quads


# ------------------------------------------------------------------ свет
DEFAULT_SUN = dict(dir=np.array([-0.35, 0.55, -0.76]), color=np.array([1.0, 0.95, 0.88]),
                   amb=(0.16, 0.17, 0.22), bounce=(0.18, 0.19, 0.16))


def shade(normal, base, sun=DEFAULT_SUN, emissive=0.0, fog=0.0):
    n = normal
    lam = max(0.0, float(-(n @ sun["dir"])))
    amb = np.array(sun["amb"], np.float32)
    lit = base * (amb + sun["color"].astype(np.float32) * (0.35 + 0.85 * lam))
    # подсветка снизу от светящегося пола/фриза
    bounce = np.array(sun["bounce"], np.float32)
    lit = lit + base * bounce * (0.5 + 0.5 * float(n[2]))
    if emissive:
        lit = lit * (1 - emissive) + base * emissive * 1.25
    return lit


# ------------------------------------------------------------------ растр
def _bbox(cam, pts, w, h, pad=2):
    p, z = cam.project(pts)
    if np.any(z <= 0.05):
        return None
    x0 = int(np.floor(p[:, 0].min())) - pad
    x1 = int(np.ceil(p[:, 0].max())) + pad
    y0 = int(np.floor(p[:, 1].min())) - pad
    y1 = int(np.ceil(p[:, 1].max())) + pad
    if x1 < 0 or y1 < 0 or x0 >= w or y0 >= h:
        return None
    return x0, x1, y0, y1, p, z


def _sample(tex, u, v):
    """Билинейная выборка текстуры (или плоский цвет)."""
    if tex.ndim == 1:
        return np.broadcast_to(tex.astype(np.float32), u.shape + (3,))
    th, tw = tex.shape[:2]
    x = np.clip(u * (tw - 1), 0, tw - 1)
    y = np.clip((1.0 - v) * (th - 1), 0, th - 1)
    x0 = np.floor(x).astype(np.int32)
    y0 = np.floor(y).astype(np.int32)
    x1 = np.minimum(x0 + 1, tw - 1)
    y1 = np.minimum(y0 + 1, th - 1)
    fx = (x - x0)[..., None]
    fy = (y - y0)[..., None]
    a = tex[y0, x0].astype(np.float32)
    b = tex[y0, x1].astype(np.float32)
    c = tex[y1, x0].astype(np.float32)
    d = tex[y1, x1].astype(np.float32)
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def render(scene, cam, bg=(0.035, 0.038, 0.05), sun=None, fog_col=(0.075, 0.075, 0.10),
           fog_start=16.0, fog_amt=0.5, glow_spots=(), grain=0.006, shadows=None,
           lights=None, occluders=None):
    """
    scene — список Quad/Box/списки. glow_spots — [(x, y, z, r, color, strength)].
    shadows — callable(wx, wy, z) → множитель, рисует тени от ламелей на полу.
    """
    sun = sun or DEFAULT_SUN
    w, h = cam.w, cam.h
    buf = np.empty((h, w, 3), np.float32)
    buf[:] = np.array(bg, np.float32)
    zbuf = np.full((h, w), 1e9, np.float32)

    quads = []
    for item in scene:
        if isinstance(item, Quad):
            quads.append(item)
        elif isinstance(item, (list, tuple)):
            quads.extend(item)
        else:
            quads.extend(item.quads)

    quads.sort(key=lambda q: -np.linalg.norm(q.pts.mean(0) - cam.pos))
    for q in quads:
        # тени только на горизонтальные поверхности
        sh = shadows if (shadows is not None and q.normal[2] > 0.7) else None
        _raster_quad(q, cam, buf, zbuf, sun, fog_col, fog_start, fog_amt, sh, lights, occluders)

    if glow_spots:
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        for (gx, gy, gz, r, color, strength) in glow_spots:
            p, z = cam.project(np.array([[gx, gy, gz]], np.float64))
            if z[0] <= 0.1:
                continue
            cx, cy = p[0]
            rad = max(6.0, r * cam.f / z[0])
            g = np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * rad ** 2)))
            buf += np.array(color, np.float32)[None, None, :] * g[..., None] * strength

    if grain:
        rng = np.random.default_rng(1)
        buf += rng.standard_normal((h, w, 1)).astype(np.float32) * grain
    return np.clip(buf, 0, 1)


def tonemap(img, exposure=1.0, contrast=1.06, lift=0.012):
    """Плёночный грейд: экспозиция, мягкая S-кривая, лёгкий подъём теней."""
    x = np.clip(img * exposure, 0, 4)
    x = x / (1 + x * 0.55) * 1.55           # мягкое сжатие светов
    x = np.clip((x - 0.5) * contrast + 0.5, 0, 1)
    x = x ** (1 / 1.02) * (1 - lift) + lift
    return np.clip(x, 0, 1)


def post(img, bloom=0.35, bloom_thresh=0.72):
    """Блум на светящихся участках — «светящийся остров» в тёмном зале."""
    if bloom <= 0:
        return img
    bright = np.clip(img - bloom_thresh, 0, None)
    sm = Image.fromarray((np.clip(bright, 0, 1) * 255).astype(np.uint8))
    sm = np.asarray(sm.filter(__import__("PIL.ImageFilter", fromlist=["x"]).GaussianBlur(18)),
                    np.float32) / 255
    sm2 = np.asarray(Image.fromarray((np.clip(bright, 0, 1) * 255).astype(np.uint8)).filter(
        __import__("PIL.ImageFilter", fromlist=["x"]).GaussianBlur(5)), np.float32) / 255
    return np.clip(img + sm * bloom * 1.4 + sm2 * bloom * 0.6, 0, 1)


def to_img(arr):
    return Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8))


def save(arr, path, quality=94):
    to_img(arr).save(path, quality=quality, optimize=True, progressive=True, subsampling=0)




# ------------------------------------------------------------------ свет (попиксельный)
class Light:
    """Точечный источник: позиция, цвет, мощность, радиус затухания."""
    __slots__ = ("pos", "color", "power", "radius", "down")

    def __init__(self, pos, color=(1.0, 0.95, 0.85), power=1.0, radius=6.0, down=0.0):
        self.pos = np.array(pos, np.float32)
        self.color = np.array(color, np.float32)
        self.power = float(power)
        self.radius = float(radius)
        self.down = float(down)          # 1.0 — светит строго вниз (спот)


def shade_px(normal, albedo, wp, lights, amb=(0.05, 0.055, 0.075),
             emissive=0.0, sun=None):
    """
    Освещение в точке: сумма точечных источников с затуханием + мягкий «солнечный»
    заполняющий свет + подъём от пола. Считается на каждый пиксель, поэтому
    на стенах появляются световые пятна, а не ровная заливка.
    """
    n = normal.astype(np.float32)
    base = albedo.astype(np.float32)
    out = base * np.array(amb, np.float32)[None, :]

    for L in lights:
        d = L.pos[None, :] - wp
        dist2 = np.maximum((d * d).sum(-1), 1e-4)
        dist = np.sqrt(dist2)
        ndl = (d @ n) / (dist + 1e-6)
        if L.down > 0:
            # спот: прижимаем к вертикали, чтобы не светил на потолок
            ndl = ndl * (1.0 - L.down) + L.down * np.clip(-(d[:, 2]) / (dist + 1e-6), 0, 1)
        ndl = np.clip(ndl, 0, 1)
        fall = L.power / (1.0 + dist2 / (L.radius ** 2))
        out = out + base * L.color[None, :] * (ndl * fall)[..., None]

    if sun is not None:
        lam = max(0.0, float(-(n @ sun["dir"])))
        out = out + base * np.array(sun["color"], np.float32)[None, :] * lam * 0.30
        # подсветка снизу от светящегося пола
        if n[2] < -0.3:
            out = out + base * np.array(sun["bounce"], np.float32)[None, :] * 0.5

    if emissive:
        out = out * (1 - emissive) + base * emissive * 1.15
    return out


def _raster_quad(q, cam, buf, zbuf, sun, fog_col, fog_start=16.0, fog_amt=0.5, shadow=None,
                 lights=None, occluders=None):
    """Растеризация одного четырёхугольника с необязательными тенями сквозь сетку."""
    w, h = cam.w, cam.h
    box = _bbox(cam, q.pts, w, h)
    if box is None:
        return
    x0, x1, y0, y1, p, z = box
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(w, x1), min(h, y1)
    if x1 <= x0 or y1 <= y0:
        return

    A, B, C, D = p
    for tri in ((A, B, C, 0, 1, 2), (A, C, D, 0, 2, 3)):
        (ax, ay), (bx, by), (cx, cy) = tri[0], tri[1], tri[2]
        i0, i1, i2 = tri[3], tri[4], tri[5]
        gx, gy = np.meshgrid(np.arange(x0, x1) + 0.5, np.arange(y0, y1) + 0.5)
        det = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        if abs(det) < 1e-9:
            continue
        l0 = ((by - cy) * (gx - cx) + (cx - bx) * (gy - cy)) / det
        l1 = ((cy - ay) * (gx - cx) + (ax - cx) * (gy - cy)) / det
        l2 = 1.0 - l0 - l1
        m = (l0 >= -0.0004) & (l1 >= -0.0004) & (l2 >= -0.0004)
        if not m.any():
            continue

        uv = q.uv
        u = l0 * uv[i0, 0] + l1 * uv[i1, 0] + l2 * uv[i2, 0]
        v = l0 * uv[i0, 1] + l1 * uv[i1, 1] + l2 * uv[i2, 1]
        col = _sample(q.tex, u, v)

        zz = 1.0 / (l0 / max(z[i0], 1e-3) + l1 / max(z[i1], 1e-3) + l2 / max(z[i2], 1e-3))
        sub_z = zbuf[y0:y1, x0:x1]
        take = m & (zz < sub_z)
        if not take.any():
            continue

        if lights:
            wp = (l0[..., None] * q.pts[i0] + l1[..., None] * q.pts[i1] +
                  l2[..., None] * q.pts[i2]).astype(np.float32)
            hh, ww = u.shape
            base = shade_px(q.normal, col.reshape(-1, 3), wp.reshape(-1, 3), lights,
                            emissive=q.emissive, sun=sun)
            base = base.reshape(hh, ww, 3).astype(np.float32) * q.tint
        else:
            base = shade(q.normal, col, sun, q.emissive).astype(np.float32) * q.tint
        if occluders and q.normal[2] > 0.7:
            wx = l0 * q.pts[i0, 0] + l1 * q.pts[i1, 0] + l2 * q.pts[i2, 0]
            wy = l0 * q.pts[i0, 1] + l1 * q.pts[i1, 1] + l2 * q.pts[i2, 1]
            soft = np.ones(wx.shape, np.float32)
            for (ox, oy, rx, ry, st) in occluders:
                d = ((wx - ox) / max(rx, 1e-3)) ** 2 + ((wy - oy) / max(ry, 1e-3)) ** 2
                soft = soft * (1.0 - st * np.exp(-d * 1.6))
            base = base * soft[..., None]
        if shadow is not None:
            # тень от ламельного потолка: вертикальная проекция на пол
            wx = l0 * q.pts[i0, 0] + l1 * q.pts[i1, 0] + l2 * q.pts[i2, 0]
            wy = l0 * q.pts[i0, 1] + l1 * q.pts[i1, 1] + l2 * q.pts[i2, 1]
            base = base * shadow(wx, wy, zz)
        fg = np.clip((zz - fog_start) / 24.0, 0, 1) * fog_amt
        base = base * (1 - fg[..., None]) + np.array(fog_col, np.float32) * fg[..., None]

        sub = buf[y0:y1, x0:x1]
        sub[take] = base[take]
        sub_z[take] = zz[take]


def lamella_shadow(x0, x1, y0, y1, z_lam=3.16, step=0.30, width=0.06, soft=0.05):
    """
    Функция тени от ламелей: ламели идут вдоль x с шагом step по y.
    Возвращает callable(wx, wy, z) → множитель яркости.
    """
    def f(wx, wy, z):
        # параллакс: чем ниже точка, тем дальше смещается тень
        shift = (z_lam - np.clip(z, 0.05, z_lam)) * 0.0
        v = (wy + shift - y0) / step
        d = np.abs(v - np.round(v)) * step
        in_zone = ((wx > x0) & (wx < x1) & (wy > y0) & (wy < y1)).astype(np.float32)
        dark = 1.0 - 0.55 * in_zone * np.clip(1.0 - (d - width * 0.5) / soft, 0, 1)
        return dark[..., None] if dark.ndim == 2 else dark
    return f
