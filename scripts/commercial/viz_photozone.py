#!/usr/bin/env python3
"""Визуализации фотозоны «РОЛЬФ» — программный 3D-рендер (numpy + PIL).

Сцена по техзаданию:
  * фотозона 12000 × 3500 мм — плоская стена из АКП GROSSBOND 3 мм, 9937 G;
  * объёмный каркас 2500 × 7000 × 2500 мм (фотобокс) у правого края;
  * 10 лайтбоксов 300 × 2000 мм на стене, 6000 К, по 300 Вт (диффузор);
  * фальш-потолок 5000 × 7000 мм с линейной подсветкой над фотобоксом;
  * объёмные буквы «РОЛЬФ» 1500 × 400 мм над рядом лайтбоксов;
  * фигуры-люди для масштаба.

Рендер: перспективная камера, z-буфер, плоское затенение Ламберта + эмиссия
+ мягкие источники от лайтбоксов, отражение в полу, свечение (bloom), виньетка.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = Path("/home/user/SM/docs/kommerciya/2026-10-22-rohl-fotozona/viz")
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_DISPLAY = "scripts/banners/fonts/Unbounded-Variable.ttf"
FONT_TEXT = "scripts/banners/fonts/Manrope-Variable.ttf"


def var_font(path, size, weight):
    """Шрифт с полной кириллицей: Unbounded / Manrope (variable)."""
    f = ImageFont.truetype(path, size)
    try:
        f.set_variation_by_axes([weight])
    except Exception:
        pass
    return f

# ─────────────────────────── палитра сцены ───────────────────────────
ACP = (0.42, 0.43, 0.44)          # АКП 9937 G (условный тон)
ACP_EDGE = (0.34, 0.35, 0.36)
BOX_IN = (0.38, 0.39, 0.40)       # внутренние поверхности фотобокса
STEEL = (0.13, 0.135, 0.14)         # стальной каркас
FLOOR = (0.27, 0.265, 0.26)
LETTER = (0.97, 0.97, 0.965)        # белые буквы
PERSON = (0.22, 0.225, 0.235)
EMIT = (1.0, 0.985, 0.93)           # 6000 К, тёплый белый
CEIL = (0.26, 0.265, 0.27)


# ─────────────────────────── векторная математика ─────────────────────
def look_at(eye, target, up=(0.0, 0.0, 1.0)):
    eye = np.array(eye, float)
    f = np.array(target, float) - eye
    f /= np.linalg.norm(f)
    up = np.array(up, float)
    s = np.cross(f, up)
    s /= np.linalg.norm(s)
    u = np.cross(s, f)
    m = np.eye(4)
    m[0, :3], m[1, :3], m[2, :3] = s, u, -f
    m[:3, 3] = -m[:3, :3] @ eye
    return m


def perspective(fov_deg, aspect, near, far):
    f = 1.0 / math.tan(math.radians(fov_deg) / 2.0)
    m = np.zeros((4, 4))
    m[0, 0] = f / aspect
    m[1, 1] = f
    m[2, 2] = (far + near) / (near - far)
    m[2, 3] = 2 * far * near / (near - far)
    m[3, 2] = -1.0
    return m


def clip_near(verts):
    """Отсечение полигона по ближней плоскости (z_view > -near)."""
    out = []
    n = len(verts)
    for i in range(n):
        a = verts[i]
        b = verts[(i + 1) % n]
        ain = a[2] <= -0.05
        bin_ = b[2] <= -0.05
        if ain:
            out.append(a)
        if ain != bin_:
            t = (-0.05 - a[2]) / (b[2] - a[2])
            out.append(a + t * (b - a))
    return out


# ─────────────────────────── геометрия ────────────────────────────────
class Mesh:
    """Набор полигонов: (точки Nx3, цвет, эмиссия, alpha, двусторонний)."""

    def __init__(self):
        self.faces = []

    def add(self, pts, color, emit=0.0, alpha=1.0, two_sided=False):
        self.faces.append((np.array(pts, float), np.array(color, float),
                           emit, alpha, two_sided))

    def box(self, x0, x1, y0, y1, z0, z1, color, emit=0.0, top=None,
            front=None, alpha=1.0):
        c = np.array(color, float)
        top = c if top is None else np.array(top, float)
        front = c if front is None else np.array(front, float)
        # левая, правая, задняя (Y=0), передняя, низ, верх
        self.add([(x0, y0, z0), (x0, y1, z0), (x0, y1, z1), (x0, y0, z1)], c)
        self.add([(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)], c)
        self.add([(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)], c)
        self.add([(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)], front)
        self.add([(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)], c * 0.55)
        self.add([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], top)


def extrude_polygon(poly2d, y_back, depth, color, emit=0.0):
    """Плоская фигура (в плоскости XZ) с экструзией в сторону +Y."""
    m = Mesh()
    n = len(poly2d)
    front = [(p[0], y_back - depth, p[1]) for p in poly2d]
    m.add(front, color, emit)
    for i in range(n):
        a = poly2d[i]
        b = poly2d[(i + 1) % n]
        m.add([(a[0], y_back, a[1]), (b[0], y_back, b[1]),
               (b[0], y_back - depth, b[1]), (a[0], y_back - depth, a[1])],
              np.array(color, float) * 0.82)
    return m


def person_polygon(scale=1.0, cx=0.0):
    """Силуэт человека во фронтальной проекции (масштаб: рост 1,75 м)."""
    h = 1.75 * scale
    w = 0.46 * scale
    head_r = 0.105 * scale
    top = h
    head_top = top - 0.02
    head_bot = head_top - 2 * head_r
    shoulder = head_bot - 0.06 * scale
    waist = shoulder - 0.45 * scale
    hip = waist - 0.08 * scale
    knee = hip - 0.42 * scale
    foot = 0.0
    pts = []
    # голова (восьмиугольник)
    for k in range(8):
        a = math.pi / 8 + k * math.pi / 4
        pts.append((cx + head_r * math.cos(a),
                    head_top - head_r + head_r * math.sin(a)))
    # плечи и корпус
    pts += [(cx - w * 0.52, shoulder), (cx - w * 0.42, waist),
            (cx - w * 0.40, hip), (cx - w * 0.16, hip),
            (cx - w * 0.14, knee), (cx - w * 0.20, foot),
            (cx + w * 0.20, foot), (cx + w * 0.14, knee),
            (cx + w * 0.16, hip), (cx + w * 0.40, hip),
            (cx + w * 0.42, waist), (cx + w * 0.52, shoulder)]
    return pts


def wordmark_mask(text, font_path=None, aspect=None):
    """Маска надписи (белым по чёрному), при необходимости — подгонка пропорций."""
    size = 400
    img = Image.new("L", (2600, 900), 0)
    d = ImageDraw.Draw(img)
    font = var_font(font_path or FONT_DISPLAY, size, 700)
    d.text((60, 40), text, font=font, fill=255)
    arr = np.array(img)
    ys, xs = np.nonzero(arr > 0)
    img = img.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
    if aspect:
        w, h = img.size
        if w / h < aspect:      # шире нужного — добавляем поля по бокам
            nw = int(round(h * aspect))
            out = Image.new("L", (nw, h), 0)
            out.paste(img, ((nw - w) // 2, 0))
            img = out
        else:                   # уже — обрезаем по высоте
            nh = int(round(w / aspect))
            out = Image.new("L", (w, nh), 0)
            out.paste(img, (0, (nh - h) // 2))
            img = out
    return img


def text_polygons(text, height_m, font_path=FONT_BOLD):
    """Объёмные буквы: контуры текста → полигоны в плоскости XZ."""
    import cv2

    size = 400
    img = Image.new("L", (2400, 700), 0)
    d = ImageDraw.Draw(img)
    font = ImageFont.truetype(font_path, size)
    d.text((60, 40), text, font=font, fill=255)
    arr = np.array(img)
    ys, xs = np.nonzero(arr > 0)
    bbox_h = ys.max() - ys.min() + 1
    bbox_x0 = xs.min()
    scale = height_m / bbox_h
    cnts, _ = cv2.findContours(arr, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    polys = []
    for c in cnts:
        if cv2.contourArea(c) < 400:
            continue
        p = c.reshape(-1, 2).astype(float)
        p = p - np.array([bbox_x0, ys.max() + 1])
        # ось Y в растровой картинке растёт вниз → переворачиваем,
        # ось X зеркалим: смотрим на стену с лицевой стороны
        p = np.stack([-p[:, 0] * scale, -p[:, 1] * scale], axis=1)
        polys.append(p)
    return polys


# ─────────────────────────── рендер ───────────────────────────────────
class Renderer:
    def __init__(self, width, height, eye, target, fov=38.0, near=0.1, far=200.0):
        self.w, self.h = width, height
        self.eye = np.array(eye, float)
        self.view = look_at(eye, target)
        self.proj = perspective(fov, width / height, near, far)
        self.mvp = self.proj @ self.view
        self.color = np.zeros((height, width, 3), np.float32)
        self.depth = np.zeros((height, width), np.float32)
        self.emissive = np.zeros((height, width, 3), np.float32)
        self.lights = []
        self.bg_top = np.array([0.16, 0.17, 0.19])
        self.bg_bottom = np.array([0.36, 0.365, 0.375])
        self.gradient()

    def gradient(self):
        t = np.linspace(0, 1, self.h, dtype=np.float32)[:, None]
        bg = self.bg_top[None, None, :] * (1 - t[:, :, None]) + \
            self.bg_bottom[None, None, :] * t[:, :, None]
        self.color[:] = np.repeat(bg, self.w, axis=1)

    def project(self, pts):
        """Мировые точки → экранные координаты и глубина в пространстве камеры."""
        arr = np.asarray(pts, float)
        hom = np.concatenate([arr, np.ones((len(arr), 1))], axis=1)
        v = (self.view @ hom.T).T
        p = (self.proj @ v.T).T
        w = p[:, 3:4]
        ndc = p[:, :2] / w
        sx = (ndc[:, 0] * 0.5 + 0.5) * self.w
        sy = (0.5 - ndc[:, 1] * 0.5) * self.h
        return sx, sy, v[:, 2]

    def add_light(self, pos, color, power, radius=4.0):
        self.lights.append((np.array(pos, float), np.array(color, float),
                             power, radius))

    def shade(self, normal, world_pts, base, emit):
        n = normal
        # нормаль всегда разворачивается к камере — геометрия двусторонняя
        to_cam = self.eye - world_pts.mean(axis=0)
        if float(n @ to_cam) < 0:
            n = -n
        col = np.zeros(3)
        # мягкое окружение: небо сверху, отражение от пола снизу
        sky = 0.40 + 0.16 * max(0.0, n[2])
        ground = 0.20 + 0.10 * max(0.0, -n[2])
        col += base * (sky + ground)
        # ключевой направленный источник (фронт-верх-лево)
        key = np.array([-0.35, 0.80, 0.49])
        key /= np.linalg.norm(key)
        d = max(0.0, float(n @ key))
        col += base * 0.70 * d
        # заполняющий контровой
        fill = np.array([0.75, 0.30, -0.20])
        fill /= np.linalg.norm(fill)
        col += base * 0.28 * max(0.0, float(n @ fill))
        # лайтбоксы как ближние источники
        c = world_pts.mean(axis=0)
        for pos, lc, power, radius in self.lights:
            v = pos - c
            dist = np.linalg.norm(v)
            if dist > radius:
                continue
            v /= dist
            fall = max(0.0, float(n @ v))
            att = power * (1.0 - dist / radius) ** 2
            col += base * lc * fall * att
        if emit > 0:
            col += base * emit
        return np.clip(col, 0, 1)

    def draw_face(self, pts, base, emit=0.0, alpha=1.0, two_sided=False):
        if len(pts) < 3:
            return
        sx, sy, vz = self.project(pts)
        poly = list(zip(sx, sy))
        vz = list(vz)
        # отсечение по ближней плоскости в пространстве камеры
        if min(vz) > -0.05:
            return
        # Sutherland–Hodgman по z_view = -0.05 (в экранных координатах
        # используем интерполяцию исходных 3D-точек)
        clipped = []
        n = len(pts)
        for i in range(n):
            a, b = pts[i], pts[(i + 1) % n]
            za, zb = vz[i], vz[(i + 1) % n]
            ain = za <= -0.05
            bin_ = zb <= -0.05
            if ain:
                clipped.append((a, za))
            if ain != bin_:
                t = (-0.05 - za) / (zb - za)
                clipped.append((a + t * (b - a), -0.05))
        if len(clipped) < 3:
            return
        cpts = np.array([p[0] for p in clipped], float)
        cz = np.array([p[1] for p in clipped], float)
        csx, csy, _ = self.project(cpts)
        # нормаль
        e1 = pts[1] - pts[0]
        e2 = pts[2] - pts[0]
        nrm = np.cross(e1, e2)
        ln = np.linalg.norm(nrm)
        if ln < 1e-12:
            return
        nrm /= ln
        if two_sided:
            pass
        shaded = self.shade(nrm, pts, np.array(base, float), emit)
        # растеризация веером: каждый треугольник со своими экранными вершинами
        for i in range(1, len(cpts) - 1):
            self.triangle((0, i, i + 1), csx, csy, cz, shaded, emit, alpha)

    def triangle(self, idx, sx, sy, sz, shaded, emit, alpha):
        i0, i1, i2 = idx
        x0, y0 = sx[i0], sy[i0]
        x1, y1 = sx[i1], sy[i1]
        x2, y2 = sx[i2], sy[i2]
        minx = max(0, int(min(x0, x1, x2)))
        maxx = min(self.w - 1, int(max(x0, x1, x2)) + 1)
        miny = max(0, int(min(y0, y1, y2)))
        maxy = min(self.h - 1, int(max(y0, y1, y2)) + 1)
        if minx > maxx or miny > maxy:
            return
        den = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        if abs(den) < 1e-9:
            return
        xs = np.arange(minx, maxx + 1) + 0.5
        ys = np.arange(miny, maxy + 1) + 0.5
        gx, gy = np.meshgrid(xs, ys)
        l0 = ((y1 - y2) * (gx - x2) + (x2 - x1) * (gy - y2)) / den
        l1 = ((y2 - y0) * (gx - x2) + (x0 - x2) * (gy - y2)) / den
        l2 = 1.0 - l0 - l1
        inside = (l0 >= -1e-6) & (l1 >= -1e-6) & (l2 >= -1e-6)
        if not inside.any():
            return
        # перспективно-корректная глубина: q = 1/(-z_view), больше = ближе
        q0, q1, q2 = (-1.0 / sz[i0]), (-1.0 / sz[i1]), (-1.0 / sz[i2])
        q = l0 * q0 + l1 * q1 + l2 * q2
        sub = self.depth[miny:maxy + 1, minx:maxx + 1]
        upd = inside & (q > sub)
        if not upd.any():
            return
        self.depth[miny:maxy + 1, minx:maxx + 1][upd] = q[upd]
        tgt = self.color[miny:maxy + 1, minx:maxx + 1]
        tgt[upd] = np.array(shaded, np.float32)
        # карта свечения: перекрытая пиксель обнуляем
        e = self.emissive[miny:maxy + 1, minx:maxx + 1]
        e[upd] = (np.array(shaded, np.float32) * emit) if emit > 0 else 0.0

    def render(self, mesh: Mesh):
        for pts, color, emit, alpha, two_sided in mesh.faces:
            self.draw_face(pts, color, emit, alpha, two_sided)

    def decal(self, mask, x0, x1, z0, z1, plane_y=0.0, color=LETTER,
              emit=0.0, depth_bias=0.0, alpha=1.0):
        """Проекция изображения (маски) на вертикальную плоскость Y = plane_y.

        Нужна для надписей: контуры букв невыпуклые, веерная триангуляция
        их ломает, поэтому буквы наносим обратной проекцией.
        """
        mw, mh = mask.size
        m = np.asarray(mask, np.float32) / 255.0
        inv = np.linalg.inv(self.mvp)

        def unproject(ndc_x, ndc_y, ndc_z):
            sh = np.broadcast(ndc_x, ndc_y).shape
            v = np.stack([np.broadcast_to(ndc_x, sh), np.broadcast_to(ndc_y, sh),
                          np.broadcast_to(ndc_z, sh), np.ones(sh)], axis=-1)
            p = v @ inv.T
            return p[..., :3] / p[..., 3:4]

        corners = np.array([[x0, plane_y, z0], [x1, plane_y, z0],
                            [x1, plane_y, z1], [x0, plane_y, z1]], float)
        csx, csy, _ = self.project(corners)
        minx = max(0, int(np.floor(csx.min())))
        maxx = min(self.w - 1, int(np.ceil(csx.max())))
        miny = max(0, int(np.floor(csy.min())))
        maxy = min(self.h - 1, int(np.ceil(csy.max())))
        if minx > maxx or miny > maxy:
            return
        px = np.arange(minx, maxx + 1) + 0.5
        py = np.arange(miny, maxy + 1) + 0.5
        gx, gy = np.meshgrid(px, py)
        ndc_x = 2.0 * gx / self.w - 1.0
        ndc_y = 1.0 - 2.0 * gy / self.h
        p_far = unproject(ndc_x, ndc_y, 1.0)
        p_near = unproject(ndc_x, ndc_y, -1.0)
        d = p_far - p_near
        with np.errstate(divide="ignore", invalid="ignore"):
            t = (plane_y - self.eye[1]) / d[..., 1]
        hit_x = self.eye[0] + t * d[..., 0]
        hit_z = self.eye[2] + t * d[..., 2]
        u = 1.0 - (hit_x - x0) / (x1 - x0)
        v = (z1 - hit_z) / (z1 - z0)
        inside = (u >= 0) & (u <= 1) & (v >= 0) & (v <= 1) & (t > 0)
        if not inside.any():
            return
        mi = np.clip((v * (mh - 1)).astype(np.int32), 0, mh - 1)
        mj = np.clip((u * (mw - 1)).astype(np.int32), 0, mw - 1)
        val = m[mi, mj] * inside
        if val.max() <= 0.01:
            return
        # глубина в буфере: q = 1/(-z_view) для точки попадания
        hit = np.stack([hit_x, np.full_like(hit_x, plane_y), hit_z], axis=-1)
        hom = np.concatenate([hit, np.ones(hit.shape[:2] + (1,))], axis=2)
        vz = (self.view @ hom.reshape(-1, 4).T).T[:, 2].reshape(hit.shape[:2])
        q = 1.0 / np.maximum(-vz, 1e-3)
        sub = self.depth[miny:maxy + 1, minx:maxx + 1]
        upd = (val > 0.02) & (q > sub - 1e-6)
        if not upd.any():
            return
        self.depth[miny:maxy + 1, minx:maxx + 1][upd] = q[upd]
        col = np.array(color, float)
        # освещение по реальным точкам попадания (нормаль стены — в сторону зала)
        nrm = np.array([0.0, 1.0, 0.0])
        if float(nrm @ (self.eye - np.array([0.0, plane_y, 0.0]))) < 0:
            nrm = -nrm
        c = world_pts = np.stack([hit_x, np.full_like(hit_x, plane_y), hit_z], axis=-1)
        c = c.reshape(-1, 3)[upd.reshape(-1)].mean(axis=0)
        shaded = self.shade(nrm, np.array([c]), col, emit)
        tgt = self.color[miny:maxy + 1, minx:maxx + 1]
        a = (val * alpha)[..., None] * upd[..., None]
        tgt[:] = tgt * (1.0 - a) + np.array(shaded, np.float32) * a
        em = self.emissive[miny:maxy + 1, minx:maxx + 1]
        em[:] = em * (1.0 - a) + (np.array(shaded, np.float32) * emit * alpha) * a


# ─────────────────────────── сборка сцены ─────────────────────────────
WALL_LEN, WALL_H = 12.0, 3.5
BOX_X0, BOX_X1, BOX_D, BOX_H = 5.0, 12.0, 2.5, 2.5
CEIL_X0, CEIL_X1 = 5.0, 12.0
CEIL_Y0, CEIL_Y1 = 0.0, 5.0
CEIL_Z = 3.20
LB_COUNT = 10
LB_PITCH = 0.65
LB_W, LB_H, LB_D = 0.3, 2.0, 0.12
LB_X0 = 5.35
LB_Z0 = 0.3
LETTER_X0, LETTER_Z0 = 7.25, 2.62
LETTER_W, LETTER_H = 1.5, 0.4


def build_scene() -> Mesh:
    m = Mesh()
    # пол
    m.add([(-14, 0, 0), (26, 0, 0), (26, 22, 0), (-14, 22, 0)], FLOOR)
    # стена: панели АКП с декоративными швами
    x = 0.0
    panel = 1.0
    while x < WALL_LEN - 1e-6:
        w = min(panel, WALL_LEN - x)
        m.add([(x, 0, 0), (x + w, 0, 0), (x + w, 0, WALL_H), (x, 0, WALL_H)], ACP)
        x += w
        if x < WALL_LEN - 1e-6:
            m.add([(x, 0, 0), (x + 0.012, 0, 0), (x + 0.012, 0, WALL_H),
                   (x, 0, WALL_H)], ACP_EDGE)
            x += 0.012
    # верхняя и нижняя кромки стены
    m.add([(0, -0.02, WALL_H), (WALL_LEN, -0.02, WALL_H),
           (WALL_LEN, 0, WALL_H), (0, 0, WALL_H)], STEEL)
    # фотобокс (объёмный каркас 7 000 × 2 500 × 2 500): открыт в зал,
    # задняя плоскость — светящаяся стена фотозоны
    t = 0.12
    m.add([(BOX_X0, 0, 0), (BOX_X0, BOX_D, 0), (BOX_X0, BOX_D, BOX_H),
           (BOX_X0, 0, BOX_H)], BOX_IN)                      # боковая стойка
    m.add([(BOX_X1, 0, 0), (BOX_X1, BOX_D, 0), (BOX_X1, BOX_D, BOX_H),
           (BOX_X1, 0, BOX_H)], BOX_IN)                      # боковая стойка
    # каркас открытый: стойки и обвязка по периметру верхнего пояса
    for xx in (BOX_X0, 6.3, 9.7, BOX_X1):                   # стойки внутри
        m.add([(xx - 0.05, BOX_D - 0.05, 0), (xx + 0.05, BOX_D - 0.05, 0),
               (xx + 0.05, BOX_D - 0.05, BOX_H), (xx - 0.05, BOX_D - 0.05, BOX_H)],
              STEEL)
    # верхняя обвязка фермы — по краям и стойкам (глухой прогоны нет,
    # иначе он проходил бы перед надписью «РОЛЬФ»)
    for xx in (BOX_X0, 6.3, 9.7, BOX_X1):                   # поперечины
        m.add([(xx - 0.04, 0.0, BOX_H - 0.11), (xx + 0.04, 0.0, BOX_H - 0.11),
               (xx + 0.04, BOX_D, BOX_H - 0.11), (xx - 0.04, BOX_D, BOX_H - 0.11)],
              STEEL)
    # фальш-потолок 5000 × 7000
    m.add([(CEIL_X0, CEIL_Y0, CEIL_Z), (CEIL_X1, CEIL_Y0, CEIL_Z),
           (CEIL_X1, CEIL_Y1, CEIL_Z), (CEIL_X0, CEIL_Y1, CEIL_Z)], CEIL)
    # линейная подсветка в фальш-потолке (3 линии вдоль Y)
    for xx in (6.6, 8.5, 10.4):
        m.add([(xx - 0.06, 0.4, CEIL_Z - 0.05), (xx + 0.06, 0.4, CEIL_Z - 0.05),
               (xx + 0.06, 4.6, CEIL_Z - 0.05), (xx - 0.06, 4.6, CEIL_Z - 0.05)],
              EMIT, emit=1.5)
    # подвесы потолка к перекрытию
    for xx in (5.4, 8.5, 11.6):
        m.add([(xx - 0.02, 0.35, CEIL_Z), (xx + 0.02, 0.35, CEIL_Z),
               (xx + 0.02, 0.35, 4.2), (xx - 0.02, 0.35, 4.2)], STEEL)
    # лайтбоксы на стене (внутри фотобокса)
    for i in range(LB_COUNT):
        x0 = LB_X0 + i * LB_PITCH
        m.add([(x0, 0.02, LB_Z0), (x0 + LB_W, 0.02, LB_Z0),
               (x0 + LB_W, 0.02, LB_Z0 + LB_H), (x0, 0.02, LB_Z0 + LB_H)],
              EMIT, emit=0.95)
        # корпус
        m.add([(x0, 0.02, LB_Z0), (x0 + LB_W, 0.02, LB_Z0),
               (x0 + LB_W, LB_D, LB_Z0), (x0, LB_D, LB_Z0)], (0.34, 0.35, 0.36))
        # рамка корпуса (передняя плоскость закрывать нельзя — светит лицевая)
        fr = 0.02
        m.add([(x0, LB_D, LB_Z0), (x0 + LB_W, LB_D, LB_Z0),
               (x0 + LB_W, LB_D, LB_Z0 + fr), (x0, LB_D, LB_Z0 + fr)], (0.34, 0.35, 0.36))
        m.add([(x0, LB_D, LB_Z0 + LB_H - fr), (x0 + LB_W, LB_D, LB_Z0 + LB_H - fr),
               (x0 + LB_W, LB_D, LB_Z0 + LB_H), (x0, LB_D, LB_Z0 + LB_H)], (0.34, 0.35, 0.36))
        m.add([(x0, LB_D, LB_Z0), (x0 + fr, LB_D, LB_Z0),
               (x0 + fr, LB_D, LB_Z0 + LB_H), (x0, LB_D, LB_Z0 + LB_H)], (0.34, 0.35, 0.36))
        m.add([(x0 + LB_W - fr, LB_D, LB_Z0), (x0 + LB_W, LB_D, LB_Z0),
               (x0 + LB_W, LB_D, LB_Z0 + LB_H), (x0 + LB_W - fr, LB_D, LB_Z0 + LB_H)],
              (0.34, 0.35, 0.36))
    # фигуры для масштаба
    for cx, yy in ((6.6, 1.15), (9.4, 1.65)):
        poly = person_polygon(1.0, cx)
        sub = extrude_polygon(poly, yy, 0.16, PERSON)
        for f in sub.faces:
            m.faces.append(f)
    return m


def add_lights(r: Renderer):
    for i in range(LB_COUNT):
        x0 = LB_X0 + i * LB_PITCH + LB_W / 2
        r.add_light((x0, 0.45, LB_Z0 + LB_H / 2), np.array([1.0, 0.97, 0.92]),
                    0.18, radius=3.0)
    r.add_light((8.5, 1.6, CEIL_Z - 0.35), np.array([0.95, 0.96, 1.0]),
                0.45, radius=6.0)


# ─────────────────────────── пост-обработка ──────────────────────────
def post(r: Renderer, path: Path, glow=1.0, vignette=0.35, label=None,
         sub=None, fog=0.55):
    img = r.color.copy()
    # свечение от эмиссивных поверхностей
    if glow > 0:
        em = r.emissive.copy() * 0.55
        if em.max() > 0:
            g = Image.fromarray(np.clip(em, 0, 1).__mul__(255).astype(np.uint8))
            g = g.filter(ImageFilter.GaussianBlur(26))
            g = np.asarray(g, np.float32) / 255.0
            img = 1.0 - (1.0 - np.clip(img, 0, 1)) * (1.0 - g * 0.22 * glow)
    # отражение в полу: зеркалим нижнюю часть кадра
    h = r.h
    refl = img[h - 1::-1].copy()
    fade = np.linspace(0.0, 0.30, refl.shape[0], dtype=np.float32)[:, None]
    refl *= fade[:, :, None]
    refl[: int(h * 0.62)] = 0
    img[int(h * 0.62):] = np.maximum(img[int(h * 0.62):], refl[int(h * 0.62):])
    # воздушная перспектива: дальние поверхности уходят в фон
    if fog > 0 and r.depth is not None:
        q = r.depth
        dist = np.where(q > 0, 1.0 / np.maximum(q, 1e-6), 1e6)
        f = np.clip((dist - 12.0) / 26.0, 0.0, 1.0)[:, :, None] * fog
        bgcol = np.array([0.26, 0.27, 0.29], np.float32)
        img = img * (1.0 - f) + bgcol * f
    # виньетка
    yy, xx = np.mgrid[0:h, 0:r.w]
    cx, cy = r.w / 2, h / 2
    d = np.sqrt(((xx - cx) / cx) ** 2 + ((yy - cy) / cy) ** 2) / 1.414
    img *= (1.0 - vignette * d ** 2)[..., None]
    # гамма и лёгкая насыщенность
    img = np.clip(img, 0, 1) ** (1 / 1.05)
    lum = img.mean(axis=2, keepdims=True)
    img = np.clip(lum + (img - lum) * 1.08, 0, 1)
    out = Image.fromarray((img * 255).astype(np.uint8))
    if label or sub:
        d = ImageDraw.Draw(out, "RGBA")
        f1 = var_font(FONT_DISPLAY, 38, 600)
        f2 = var_font(FONT_TEXT, 27, 500)
        if label:
            d.rectangle([0, 0, out.size[0], 78], fill=(0, 0, 0, 120))
            d.text((36, 18), label, font=f1, fill=(255, 255, 255, 255))
        if sub:
            d.rectangle([0, out.size[1] - 62, out.size[0], out.size[1]],
                        fill=(0, 0, 0, 120))
            d.text((36, out.size[1] - 50), sub, font=f2, fill=(235, 235, 235, 255))
    out.save(path, quality=94)
    print("saved", path)


def apply_decals(r):
    """Надпись «РОЛЬФ» наносится обратной проекцией на плоскость стены."""
    mask = wordmark_mask("РОЛЬФ", aspect=LETTER_W / LETTER_H)
    # мягкая тень от объёмных букв на стене
    from PIL import ImageFilter
    shadow = mask.filter(ImageFilter.GaussianBlur(9))
    r.decal(shadow, LETTER_X0 + 0.025, LETTER_X0 + LETTER_W + 0.025,
            LETTER_Z0 - 0.03, LETTER_Z0 + LETTER_H - 0.03,
            plane_y=0.03, color=(0.14, 0.14, 0.15), emit=0.0, alpha=0.55)
    # боковая грань объёмных букв (смещение вниз-вправо)
    r.decal(mask, LETTER_X0 + 0.012, LETTER_X0 + LETTER_W + 0.012,
            LETTER_Z0 - 0.012, LETTER_Z0 + LETTER_H - 0.012,
            plane_y=0.055, color=(0.62, 0.62, 0.63), emit=0.0)
    # лицевая плоскость букв
    r.decal(mask, LETTER_X0, LETTER_X0 + LETTER_W, LETTER_Z0, LETTER_Z0 + LETTER_H,
            plane_y=0.07, color=LETTER, emit=0.30)


def render_view(name, eye, target, fov, label, sub, size=(2400, 1350), ss=2):
    w, h = size[0] * ss, size[1] * ss
    r = Renderer(w, h, eye, target, fov=fov)
    add_lights(r)
    r.render(build_scene())
    apply_decals(r)
    img = r.color
    if ss > 1:
        img = img.reshape(size[1], ss, size[0], ss, 3).mean(axis=(1, 3))
    # компактный рендер для пост-обработки
    small = Renderer(size[0], size[1], eye, target, fov=fov)
    small.color = img.astype(np.float32)
    small.emissive = r.emissive.reshape(size[1], ss, size[0], ss, 3).mean(axis=(1, 3))
    qd = r.depth.reshape(size[1], ss, size[0], ss).max(axis=(1, 3))
    small.depth = qd.astype(np.float32)
    post(small, OUT / name, label=label, sub=sub)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    # 1. основная перспектива — весь объём: стена, фотобокс, фальш-потолок
    render_view(
        "01_perspektiva.jpg",
        eye=(2.4, 10.4, 2.00), target=(8.3, 0.7, 1.50), fov=44,
        label="Фотозона «РОЛЬФ» — 12,0 × 3,5 м",
        sub="АКП GROSSBOND 9937 G · фотобокс 7 000 × 2 500 × 2 500 мм · "
            "фальш-потолок 5 000 × 7 000 мм · 10 лайтбоксов 300 × 2 000 мм, 6000 К",
        size=(2400, 1350),
    )
    # 2. фронтальный разворот
    render_view(
        "02_razvorot.jpg",
        eye=(8.5, 11.5, 2.00), target=(8.5, 0.0, 1.55), fov=42,
        label="Разворот фотозоны",
        sub="Стена 12 000 × 3 500 мм · фотобокс 7 000 × 2 500 × 2 500 мм · "
            "фальш-потолок 5 000 × 7 000 мм, подвес +3 200",
        size=(2400, 1350),
    )
    # 3. вид из фотобокса — светящаяся стена с лайтбоксами и буквами
    render_view(
        "03_fotobox.jpg",
        eye=(8.4, 7.7, 1.30), target=(8.3, 0.0, 1.90), fov=40,
        label="Вид из фотобокса",
        sub="Ряд лайтбоксов 300 × 2 000 мм (10 шт., 3 кВт суммарно) и "
            "объёмные буквы «РОЛЬФ» 1 500 × 400 мм",
        size=(2400, 1350),
    )
    # 4. техническая схема (2D)
    scheme()


# ─────────────────────────── схема плана (2D) ─────────────────────────
def scheme():
    """Схема: план + фронтальный вид с размерами."""
    W, H = 2800, 1620
    img = Image.new("RGB", (W, H), (250, 249, 247))
    d = ImageDraw.Draw(img)

    INK = (24, 24, 28)
    ACC = (176, 132, 26)
    WALL_C = (196, 198, 200)

    f_h1 = var_font(FONT_DISPLAY, 46, 600)
    f_h2 = var_font(FONT_DISPLAY, 25, 500)
    f_b = var_font(FONT_TEXT, 25, 700)
    f_s = var_font(FONT_TEXT, 22, 500)
    f_t = var_font(FONT_TEXT, 19, 500)

    # ── шапка ────────────────────────────────────────────────
    d.rectangle([0, 0, W, 240], fill=(28, 28, 32))
    d.text((70, 50), "Фотозона «РОЛЬФ» — схема плана и развёртки",
           font=f_h1, fill=(255, 255, 255))
    d.text((74, 118), "Ясенево, 40-й км МКАД, вл. 1, стр. 2  ·  монтаж 26–28.11.2026",
           font=f_h2, fill=(198, 198, 202))
    d.text((74, 166), "Все размеры в миллиметрах  ·  обшивка стены — АКП GROSSBOND 3 мм, 9937 G, окраска в обе стороны",
           font=f_s, fill=(152, 152, 158))

    # ── ПЛАН (слева) ─────────────────────────────────────────
    sc = 100  # px на метр
    ox, oy = 150, 430

    def X(mx):
        return ox + mx * sc

    def Y(my):
        return oy + my * sc

    d.text((70, 282), "ПЛАН · вид сверху", font=f_h2, fill=INK)
    d.rectangle([X(-1.0), Y(-0.35), X(13.0), Y(6.3)], fill=(240, 238, 234))
    # фальш-потолок — подвесной, рисуем пунктиром
    d.rectangle([X(5), Y(0.3), X(12), Y(5.3)], fill=(246, 243, 236))
    for seg in range(0, 70):
        x = X(5) + seg * (7.0 * sc / 70.0)
        d.line([x, Y(0.3), x + 10, Y(0.3)], fill=ACC, width=3)
        d.line([x, Y(5.3), x + 10, Y(5.3)], fill=ACC, width=3)
    for seg in range(0, 50):
        y = Y(0.3) + seg * (5.0 * sc / 50.0)
        d.line([X(5), y, X(5), y + 10], fill=ACC, width=3)
        d.line([X(12), y, X(12), y + 10], fill=ACC, width=3)
    d.text((X(6.25), Y(4.0)), "ФАЛЬШ-ПОТОЛОК 5 000 × 7 000 (подвес +3 200)",
           font=f_b, fill=(140, 106, 18))
    d.text((X(6.25), Y(4.4)), "АКП 9937 G + Oracal 641 073M, линейная подсветка",
           font=f_t, fill=(176, 148, 66))
    # стена 12 000 (в плане — полоса 250)
    d.rectangle([X(0), Y(0), X(12), Y(0.25)], fill=WALL_C, outline=(120, 122, 124), width=2)
    # фотобокс 7 000 × 2 500 (открыт в зал)
    d.rectangle([X(5), Y(0.25), X(12), Y(2.75)], fill=(228, 230, 232),
                outline=(120, 122, 124), width=3)
    for xx in (5.0, 6.3, 9.7, 12.0):
        d.rectangle([X(xx) - 4, Y(0.25), X(xx) + 4, Y(2.75)], fill=(90, 92, 96))
    d.text((X(9.35), Y(1.05)), "ОБЪЁМНЫЙ", font=f_b, fill=(84, 86, 90))
    d.text((X(9.35), Y(1.42)), "КАРКАС", font=f_b, fill=(84, 86, 90))
    d.text((X(9.35), Y(1.85)), "7 000 × 2 500 × 2 500", font=f_t, fill=(118, 120, 124))
    d.text((X(9.35), Y(2.16)), "сталь, 4 стойки, открыт", font=f_t, fill=(142, 144, 148))
    # подписи элементов на стене — внутри фотобокса
    d.text((X(5.35), Y(0.85)), "10 × лайтбокс 300 × 2 000 мм", font=f_b,
           fill=(150, 120, 30))
    d.text((X(5.35), Y(1.2)), "шаг 650, 6000 К, 3 кВт", font=f_t, fill=(176, 148, 66))
    d.text((X(5.35), Y(1.72)), "«РОЛЬФ» 1 500 × 400", font=f_b, fill=(70, 70, 74))
    d.text((X(5.35), Y(2.07)), "объёмные, белые, над лайтбоксами", font=f_t,
           fill=(120, 120, 126))
    for xm in (5.5, 8.0):
        d.line([X(xm), Y(0.45), X(xm), Y(0.75)], fill=(150, 150, 156), width=2)
    # лайтбоксы на стене (внутри фотобокса)
    for i in range(LB_COUNT):
        x0 = LB_X0 + i * LB_PITCH
        d.rectangle([X(x0), Y(0.25), X(x0 + 0.3), Y(0.42)],
                    fill=(252, 240, 200), outline=(190, 156, 40), width=2)
    # буквы «РОЛЬФ» — в плане проецируются на стену над лайтбоксами
    d.rectangle([X(LETTER_X0), Y(0.25), X(LETTER_X0 + LETTER_W), Y(0.40)],
                fill=(255, 255, 255), outline=(60, 60, 64), width=2)

    def leader(x0, y0, x1, y1, label, color, font=f_b):
        d.line([X(x0), Y(y0), X(x1), Y(y1)], fill=color, width=2)
        d.ellipse([X(x0) - 4, Y(y0) - 4, X(x0) + 4, Y(y0) + 4], fill=color)
        tw = d.textlength(label, font=font)
        d.rectangle([X(x1) - tw / 2 - 6, Y(y1) - 15, X(x1) + tw / 2 + 6, Y(y1) + 4],
                    fill=(240, 238, 234))
        d.text((X(x1) - tw / 2, Y(y1) - 14), label, font=font, fill=color)


    def dim_h(x0, x1, y, label):
        d.line([X(x0), Y(y), X(x1), Y(y)], fill=(70, 70, 70), width=2)
        for xx in (x0, x1):
            d.line([X(xx), Y(y) - 9, X(xx), Y(y) + 9], fill=(70, 70, 70), width=2)
        w = d.textlength(label, font=f_b)
        cxm = (X(x0) + X(x1)) / 2
        d.rectangle([cxm - w / 2 - 8, Y(y) - 17, cxm + w / 2 + 8, Y(y) + 5],
                    fill=(250, 249, 247))
        d.text((cxm - w / 2, Y(y) - 16), label, font=f_b, fill=(50, 50, 50))

    def dim_v(y0, y1, x, label):
        d.line([X(x), Y(y0), X(x), Y(y1)], fill=(70, 70, 70), width=2)
        for yy in (y0, y1):
            d.line([X(x) - 9, Y(yy), X(x) + 9, Y(yy)], fill=(70, 70, 70), width=2)
        w = d.textlength(label, font=f_b)
        cym = (Y(y0) + Y(y1)) / 2
        d.rectangle([X(x) - w / 2 - 8, cym - 15, X(x) + w / 2 + 8, cym + 7],
                    fill=(250, 249, 247))
        d.text((X(x) - w / 2, cym - 14), label, font=f_b, fill=(50, 50, 50))

    dim_h(0, 12, 6.7, "12 000")
    dim_h(5, 12, 2.95, "7 000")
    dim_v(0, 5.3, 12.55, "5 000")
    dim_v(0, 2.75, -0.6, "2 500")

    # ── ФРОНТ (справа) ──────────────────────────────────────
    fx, fy = 1660, 700
    fs = 84

    def FX(mx):
        return fx + mx * fs

    def FZ(mz):
        return fy - mz * fs

    d.text((1620, 282), "ФРОНТ · вид с фотозоны", font=f_h2, fill=INK)
    d.rectangle([FX(0), FZ(3.5), FX(12), FZ(0)], fill=WALL_C, outline=(120, 122, 124), width=3)
    for xx in (5.0, 6.3, 9.7, 12.0):
        d.line([FX(xx), FZ(0), FX(xx), FZ(2.5)], fill=(128, 130, 134), width=5)
    d.line([FX(5), FZ(2.39), FX(12), FZ(2.39)], fill=(128, 130, 134), width=5)
    for i in range(LB_COUNT):
        x0 = LB_X0 + i * LB_PITCH
        d.rectangle([FX(x0), FZ(LB_Z0 + LB_H), FX(x0 + 0.3), FZ(LB_Z0)],
                    fill=(255, 252, 238), outline=(190, 156, 40), width=2)
    # буквы «РОЛЬФ» — объёмные, белые, на стене над лайтбоксами
    d.rectangle([FX(LETTER_X0), FZ(LETTER_Z0 + LETTER_H),
                 FX(LETTER_X0 + LETTER_W), FZ(LETTER_Z0)], fill=(252, 252, 252),
                outline=(72, 72, 76), width=2)
    d.text((FX(LETTER_X0) + 14, FZ(LETTER_Z0 + 0.235)), "РОЛЬФ", font=f_s,
           fill=(48, 48, 52))
    # фальш-потолок — плоскость на отметке +3 200
    d.rectangle([FX(5), FZ(3.32), FX(12), FZ(3.20)], fill=(238, 232, 214),
                outline=ACC, width=3)
    # отметка подвеса фальш-потолка
    for seg in range(0, 36):
        x = FX(2.75) + seg * (9.1 * fs / 36.0)
        d.line([x, FZ(3.2), x + 12, FZ(3.2)], fill=(150, 122, 30), width=2)
    d.text((FX(0.2), FZ(3.16)), "фальш-потолок", font=f_t, fill=(150, 122, 30))
    d.text((FX(0.2), FZ(2.88)), "подвес +3 200", font=f_t, fill=(150, 122, 30))
    d.line([FX(-0.4), FZ(0), FX(12.4), FZ(0)], fill=(70, 70, 70), width=3)

    def fdim_h(x0, x1, z, label):
        d.line([FX(x0), FZ(z), FX(x1), FZ(z)], fill=(70, 70, 70), width=2)
        for xx in (x0, x1):
            d.line([FX(xx), FZ(z) - 9, FX(xx), FZ(z) + 9], fill=(70, 70, 70), width=2)
        w = d.textlength(label, font=f_b)
        cxm = (FX(x0) + FX(x1)) / 2
        d.rectangle([cxm - w / 2 - 8, FZ(z) - 17, cxm + w / 2 + 8, FZ(z) + 5],
                    fill=(250, 249, 247))
        d.text((cxm - w / 2, FZ(z) - 16), label, font=f_b, fill=(50, 50, 50))

    def fdim_v(z0, z1, x, label):
        d.line([FX(x), FZ(z0), FX(x), FZ(z1)], fill=(70, 70, 70), width=2)
        for zz in (z0, z1):
            d.line([FX(x) - 9, FZ(zz), FX(x) + 9, FZ(zz)], fill=(70, 70, 70), width=2)
        w = d.textlength(label, font=f_b)
        cym = (FZ(z0) + FZ(z1)) / 2
        d.rectangle([FX(x) - w / 2 - 8, cym - 15, FX(x) + w / 2 + 8, cym + 7],
                    fill=(250, 249, 247))
        d.text((FX(x) - w / 2, cym - 14), label, font=f_b, fill=(50, 50, 50))

    fdim_h(0, 12, -0.85, "12 000")
    fdim_v(0, 3.5, 12.5, "3 500")
    fdim_v(0.3, 2.3, 4.45, "2 000")
    fdim_h(LB_X0, LB_X0 + 9 * LB_PITCH + LB_W, -0.3, "6 150 · шаг 650")

    # ── легенда ─────────────────────────────────────────────
    lx, ly = 1560, 900
    d.rounded_rectangle([lx, ly, 2700, 1560], 12, fill=(255, 255, 255),
                        outline=(224, 222, 218), width=2)
    d.text((lx + 30, ly + 24), "Состав фотозоны", font=f_h2, fill=INK)
    items = [
        ("Стена фотозоны", "12 000 × 3 500, стальной каркас из труб, обшивка АКП GROSSBOND 3 мм, 9937 G, окраска с двух сторон"),
        ("Объёмный каркас (фотобокс)", "7 000 × 2 500 × 2 500, сталь в окраске, 4 стойки, открыт в зал"),
        ("Лайтбоксы", "10 шт. 300 × 2 000, ПВХ, молочный акрил, 6000 К, суммарно 3 кВт, диммер на каждую линию"),
        ("Фальш-потолок", "5 000 × 7 000, каркас и обшивка АКП 9937 G, оклейка Oracal 641 073M, линейная подсветка"),
        ("Буквы «РОЛЬФ»", "1 500 × 400, объёмный ПВХ, белые, без подсветки, монтаж на разметку"),
    ]
    yy = ly + 78
    for name, val in items:
        d.text((lx + 30, yy), "• " + name, font=f_b, fill=(30, 30, 34))
        d.text((lx + 46, yy + 30), val, font=f_s, fill=(112, 112, 118))
        yy += 78

    d.text((150, 1548), "Визуализация носит ознакомительный характер. Финальная геометрия — по рабочим чертежам.",
           font=f_t, fill=(150, 150, 156))

    img.save(OUT / "04_shema.jpg", quality=94)
    print("saved", OUT / "04_shema.jpg")


if __name__ == "__main__":
    main()
