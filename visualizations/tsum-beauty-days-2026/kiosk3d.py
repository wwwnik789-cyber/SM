#!/usr/bin/env python3
"""Стойка TSUM Beauty Days — 3D-модель и профиль по чертежу.

Профиль (вид сбоку), координаты: z — глубина (0 = спинка), y — высота:

    спинка      вертикальная, z = 0, y = 0..180
    верх        y = 180, z = 0..30
    скос        20 × 20 под 45°, от (z=30, y=180) к (z=50, y=160);
                диагональ = 28,3 см — совпадает с чертежом
    перед       z = 65 внизу, z = 50 на высоте 160 → вынос 15 см;
                длина грани 160,7 см ≈ 78,5 + 81,4 = 159,9 см
    низ         y = 0, z = 0..65

Окно на передней грани — 48 × 48 см со скруглениями R7, низ на 92 см.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
FONT = Path("/home/user/SM/banners/anikom-arena-3000x2500-concepts/source/Montserrat-Variable.ttf")
OUT = HERE / "render"

# габариты, см
W, H, D = 87.0, 180.0, 65.0
CHAM_V, CHAM_D = 20.0, 20.0
TOP_D = 30.0
FRONT_TOP_Y = H - CHAM_V          # 160
FRONT_LEAN = 15.0                 # насколько низ выступает вперёд
SHELF_Y = 78.5
BACK_Z = 30.0                     # задняя стенка камеры

WIN_X0, WIN_X1 = 17.0, 70.0
WIN_Y0, WIN_Y1 = 90.0, 148.0
WIN_R = 8.0

C_DARK = np.array([176, 38, 12], np.float32)
C_MID = np.array([224, 72, 26], np.float32)
C_LIT = np.array([244, 112, 42], np.float32)


def zf(y: float) -> float:
    """Глубина передней грани на высоте y."""
    return D - FRONT_LEAN * (y / FRONT_TOP_Y)


# ---------------------------------------------------------------- текстуры
def silk(w: int, h: int, seed=3, gain=1.0) -> Image.Image:
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    u, v = xx / w, yy / h
    t = np.clip(v, 0, 1)[:, :, None]
    base = C_LIT[None, None, :] * t + C_DARK[None, None, :] * (1 - t)
    s = np.zeros((h, w), np.float32)
    for amp, fx, fy, ph in ((0.10, 1.1, 1.6, 0.0), (0.07, 2.3, -1.1, 1.7),
                            (0.04, 4.0, 2.4, 4.1)):
        s += amp * np.sin(2 * math.pi * (fx * u + fy * v) + ph + rng.normal(0, 0.05))
    out = base * (1.0 + np.clip(s, -0.4, 0.4)[:, :, None] * 0.6)
    out *= (1.0 - 0.08 * (u - 0.5) ** 2)[:, :, None]
    return Image.fromarray(np.clip(out * gain, 0, 255).astype(np.uint8))


def tracked(d, text, font, cx, y, track, fill):
    widths = [d.textlength(ch, font=font) for ch in text]
    total = sum(widths) + track * (len(text) - 1)
    x = cx - total / 2
    for ch, cw in zip(text, widths):
        d.text((x, y), ch, font=font, fill=fill)
        x += cw + track


def block(img: Image.Image, lines, cx_img, top_img, cap_px, color, track_ratio=0.10,
          gap=0.30, alpha=235):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f = ImageFont.truetype(str(FONT), int(cap_px))
    f.set_variation_by_name("SemiBold")
    step = cap_px * (1 + gap)
    for i, line in enumerate(lines):
        tracked(d, line, f, cx_img, top_img + i * step, cap_px * track_ratio,
                tuple(color) + (alpha,))
    return Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")


PPC = 6.0


def plaque_image(w_px: int) -> Image.Image:
    """Белая плашка с монограммой: рисуем прямо в текстуру."""
    h_px = int(w_px * 0.42)
    img = Image.new("RGB", (w_px, h_px), (252, 251, 249))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w_px - 1, h_px - 1], outline=(30, 26, 22), width=max(1, w_px // 90))
    f = ImageFont.truetype(str(FONT), int(h_px * 0.42))
    f.set_variation_by_name("Medium")
    widths = [d.textlength(ch, font=f) for ch in "ЦУМ"]
    track = h_px * 0.05
    total = sum(widths) + track * 2
    x = (w_px - total) / 2
    for ch, cw in zip("ЦУМ", widths):
        d.text((x, h_px * 0.10), ch, font=f, fill=(24, 20, 17))
        x += cw + track
    fs = ImageFont.truetype(str(FONT), int(h_px * 0.115))
    fs.set_variation_by_name("Medium")
    t = "TSUM MOSCOW"
    cw = [d.textlength(c, font=fs) for c in t]
    tr = h_px * 0.022
    tot = sum(cw) + tr * (len(t) - 1)
    x = (w_px - tot) / 2
    for c, w_ in zip(t, cw):
        d.text((x, h_px * 0.70), c, font=fs, fill=(40, 35, 30))
        x += w_ + tr
    return img


def tex_front() -> Image.Image:
    """Передняя грань: (x, высота от низа) -> (u, 1-v)."""
    w_px, h_px = int(W * PPC), int(FRONT_TOP_Y * PPC)
    img = silk(w_px, h_px, seed=5)
    # пластика: тень у пола и мягкий свет сверху
    a = np.asarray(img, np.float32)
    v = np.linspace(0, 1, h_px, dtype=np.float32)[:, None, None]
    a *= (0.80 + 0.24 * v)
    # лёгкий вертикальный блик по центру
    u = np.linspace(-1, 1, w_px, dtype=np.float32)[None, :, None]
    a *= (1.0 - 0.05 * u ** 2)
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

    # нижняя панель: крупный блок в три строки, левее центра
    cap = 11.5 * PPC
    top = h_px - (60.0 * PPC)
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f = ImageFont.truetype(str(FONT), int(cap))
    f.set_variation_by_name("SemiBold")
    for i, line in enumerate(["TSUM", "BEAUTY", "DAYS"]):
        d.text((11.0 * PPC, top + i * cap * 1.24), line, font=f,
               fill=(250, 245, 237, 245))
    # даты справа от первой строки
    fd = ImageFont.truetype(str(FONT), int(3.9 * PPC))
    fd.set_variation_by_name("Medium")
    dates = "08.10 – 11.10"
    dw = d.textlength(dates, font=fd)
    d.text((W * PPC - 6.0 * PPC - dw, top + cap * 0.46), dates, font=fd,
           fill=(250, 245, 237, 230))
    img = Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")

    # плашка внизу по центру
    pl = plaque_image(int(20.0 * PPC))
    img.paste(pl, (int((W / 2) * PPC - pl.width / 2), h_px - int(11.0 * PPC)))

    # датчик Wi-Fi слева от окна
    sx, sy = 7.0 * PPC, h_px - (136.0 * PPC)
    d2 = ImageDraw.Draw(img)
    d2.rounded_rectangle([sx, sy, sx + 7.4 * PPC, sy + 5.2 * PPC], radius=int(1.0 * PPC),
                         fill=(214, 214, 210), outline=(150, 150, 146), width=2)
    d2.text((sx + 0.8 * PPC, sy + 1.5 * PPC), "WIR",
            font=ImageFont.truetype(str(FONT), int(2.0 * PPC)), fill=(60, 60, 58))
    return img


def tex_side() -> Image.Image:
    w_px, h_px = int(D * PPC), int(167 * PPC)
    img = silk(w_px, h_px, seed=9, gain=0.97)
    cap = 7.6 * PPC
    top = h_px - (112.0 * PPC)
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f = ImageFont.truetype(str(FONT), int(cap))
    f.set_variation_by_name("SemiBold")
    for i, line in enumerate(["TSUM", "BEAUTY", "DAYS"]):
        d.text((7.0 * PPC, top + i * cap * 1.22), line, font=f, fill=(250, 245, 237, 235))
    fd = ImageFont.truetype(str(FONT), int(3.6 * PPC))
    fd.set_variation_by_name("Medium")
    d.text((7.0 * PPC, top + 3 * cap * 1.22 + 1.6 * PPC), "08.10 – 11.10", font=fd,
           fill=(250, 245, 237, 215))
    img = Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")
    pl = plaque_image(int(16.0 * PPC))
    img.paste(pl, (int(7.0 * PPC), h_px - int(13.0 * PPC)))
    return img


def tex_back_wall() -> Image.Image:
    """Задняя стенка камеры: крупный текст + плашка, как в концепте."""
    hh = FRONT_TOP_Y - SHELF_Y
    img = silk(int(W * PPC), int(hh * PPC), seed=17, gain=1.06)
    cap = 7.6 * PPC
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f = ImageFont.truetype(str(FONT), int(cap))
    f.set_variation_by_name("SemiBold")
    x0 = 21.0 * PPC
    y0 = int(hh * PPC) - (58.0 * PPC)
    for i, line in enumerate(["TSUM", "BEAUTY", "DAYS"]):
        d.text((x0, y0 + i * cap * 1.24), line, font=f, fill=(252, 248, 242, 250))
    img = Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")
    pl = plaque_image(int(15.0 * PPC))
    img.paste(pl, (int(30.0 * PPC), int(hh * PPC) - int(22.0 * PPC)))
    return img


def flat(rgb, size=48) -> Image.Image:
    return Image.new("RGB", (size, size), rgb)


# ---------------------------------------------------------------- каркас
class Camera:
    def __init__(self, eye, target, fov=32.0):
        self.eye = np.array(eye, np.float32)
        f = np.array(target, np.float32) - self.eye
        self.f = f / np.linalg.norm(f)
        r = np.cross(self.f, np.array([0, 1, 0], np.float32))
        self.r = r / np.linalg.norm(r)
        self.u = np.cross(self.r, self.f)
        self.tan = math.tan(math.radians(fov) / 2)

    def project(self, pts, w, h):
        d = pts - self.eye
        z = np.maximum(d @ self.f, 1e-4)
        x = d @ self.r
        y = d @ self.u
        aspect = w / h
        return np.stack([(x / (z * self.tan * aspect) * 0.5 + 0.5) * w,
                         (0.5 - y / (z * self.tan) * 0.5) * h], -1), np.maximum(d @ self.f, 1e-4)


class Scene:
    def __init__(self):
        self.tris = []
        self.balls = []

    def tri(self, a, b, c, uva, uvb, uvc, mat):
        self.tris.append((np.array(a, np.float32), np.array(b, np.float32),
                          np.array(c, np.float32), np.array(uva, np.float32),
                          np.array(uvb, np.float32), np.array(uvc, np.float32), mat))

    def quad(self, a, b, c, d, mat, uvs=((0, 0), (1, 0), (1, 1), (0, 1))):
        self.tri(a, b, c, uvs[0], uvs[1], uvs[2], mat)
        self.tri(a, c, d, uvs[0], uvs[2], uvs[3], mat)


def build() -> Scene:
    s = Scene()
    fuv = lambda x, y: (x / W, 1.0 - y / FRONT_TOP_Y)
    suv = lambda z, y: (z / D, 1.0 - y / 167.0)

    # спинка
    s.quad((0, 0, 0), (W, 0, 0), (W, H, 0), (0, H, 0), "shell",
           ((0, 1), (1, 1), (1, 0), (0, 0)))

    # боковины: выпуклый профиль -> веер треугольников от центроида
    prof = [(0, 0), (D, 0), (D, FRONT_TOP_Y), (TOP_D + CHAM_D, H), (TOP_D, H), (0, H)]
    cz = sum(p[0] for p in prof) / len(prof)
    cy = sum(p[1] for p in prof) / len(prof)
    for x in (0.0, W):
        for i in range(len(prof)):
            z0, y0 = prof[i]
            z1, y1 = prof[(i + 1) % len(prof)]
            s.tri((x, cy, cz), (x, y0, z0), (x, y1, z1),
                  suv(cz, cy), suv(z0, y0), suv(z1, y1),
                  "side" if x == 0.0 else "side_r")

    # верх и скос
    s.quad((0, H, 0), (W, H, 0), (W, H, TOP_D), (0, H, TOP_D), "top")
    s.quad((0, H, TOP_D), (W, H, TOP_D), (W, FRONT_TOP_Y, TOP_D + CHAM_D), (0, FRONT_TOP_Y, TOP_D + CHAM_D), "shell")

    # низ
    s.quad((0, 0, 0), (0, 0, D), (W, 0, D), (W, 0, 0), "shell")

    P = lambda x, y: (x, y, zf(y))
    def fq(x0, y0, x1, y1):
        s.quad(P(x0, y0), P(x1, y0), P(x1, y1), P(x0, y1), "front",
               (fuv(x0, y0), fuv(x1, y0), fuv(x1, y1), fuv(x0, y1)))

    fq(0, 0, W, WIN_Y0)
    fq(0, WIN_Y1, W, FRONT_TOP_Y)
    fq(0, WIN_Y0, WIN_X0, WIN_Y1)
    fq(WIN_X1, WIN_Y0, W, WIN_Y1)

    # скругления окна
    seg = 8
    for cx, cy, a0 in ((WIN_X0 + WIN_R, WIN_Y0 + WIN_R, 180),
                       (WIN_X1 - WIN_R, WIN_Y0 + WIN_R, 270),
                       (WIN_X1 - WIN_R, WIN_Y1 - WIN_R, 0),
                       (WIN_X0 + WIN_R, WIN_Y1 - WIN_R, 90)):
        corner = (cx + (-WIN_R if a0 in (180, 90) else WIN_R),
                  cy + (-WIN_R if a0 in (180, 270) else WIN_R))
        for i in range(seg):
            t0 = math.radians(a0 + 90 * i / seg)
            t1 = math.radians(a0 + 90 * (i + 1) / seg)
            p0 = (cx + WIN_R * math.cos(t0), cy + WIN_R * math.sin(t0))
            p1 = (cx + WIN_R * math.cos(t1), cy + WIN_R * math.sin(t1))
            s.tri(P(*corner), P(*p0), P(*p1), fuv(*corner), fuv(*p0), fuv(*p1), "front")

    # откос окна 1,5 см
    t = 1.5
    q = lambda x, y, dy=0.0: (x, y + dy, zf(y) - t)
    s.quad(q(WIN_X0, WIN_Y1), q(WIN_X1, WIN_Y1), q(WIN_X1, WIN_Y1, -t), q(WIN_X0, WIN_Y1, -t), "white")
    s.quad(q(WIN_X0, WIN_Y0), q(WIN_X0, WIN_Y0, t), q(WIN_X1, WIN_Y0, t), q(WIN_X1, WIN_Y0), "white")
    # боковые откосы окна
    s.quad(q(WIN_X0, WIN_Y0), q(WIN_X0, WIN_Y1), q(WIN_X0, WIN_Y1, -t), q(WIN_X0, WIN_Y0, -t), "white")
    s.quad(q(WIN_X1, WIN_Y0), q(WIN_X1, WIN_Y0, -t), q(WIN_X1, WIN_Y1, -t), q(WIN_X1, WIN_Y1), "white")

    # камера
    z_in_front = zf(WIN_Y1) - 4.0
    xi0, xi1 = 0.7, W - 0.7
    zb = BACK_Z + 0.7
    s.quad((xi0, FRONT_TOP_Y, zb), (xi1, FRONT_TOP_Y, zb), (xi1, SHELF_Y, zb), (xi0, SHELF_Y, zb), "backwall")
    s.quad((xi0, SHELF_Y, zb), (xi0, SHELF_Y, z_in_front), (xi0, FRONT_TOP_Y, z_in_front), (xi0, FRONT_TOP_Y, zb), "white")
    s.quad((xi1, SHELF_Y, zb), (xi1, FRONT_TOP_Y, zb), (xi1, FRONT_TOP_Y, z_in_front), (xi1, SHELF_Y, z_in_front), "white")
    s.quad((xi0, SHELF_Y, zb), (xi1, SHELF_Y, zb), (xi1, SHELF_Y, z_in_front), (xi0, SHELF_Y, z_in_front), "shelf")
    s.quad((xi0, FRONT_TOP_Y, zb), (xi0, FRONT_TOP_Y, z_in_front), (xi1, FRONT_TOP_Y, z_in_front), (xi1, FRONT_TOP_Y, zb), "white")

    # белая панель с круглым вырезом на правой стенке камеры (по фото)
    dx = xi1 - 0.05
    s.quad((dx, SHELF_Y + 8, 38), (dx, FRONT_TOP_Y - 8, 38), (dx, FRONT_TOP_Y - 8, 56), (dx, SHELF_Y + 8, 56), "door")

    # акриловая капсула
    ax0, ax1, az0, az1 = 25.0, 56.0, 36.0, 55.0
    ay0, ay1 = SHELF_Y + 0.2, SHELF_Y + 25.0
    for quad in (((ax0, ay0, az0), (ax1, ay0, az0), (ax1, ay1, az0), (ax0, ay1, az0)),
                 ((ax0, ay0, az1), (ax1, ay0, az1), (ax1, ay1, az1), (ax0, ay1, az1)),
                 ((ax0, ay0, az0), (ax0, ay1, az0), (ax0, ay1, az1), (ax0, ay0, az1)),
                 ((ax1, ay0, az0), (ax1, ay0, az1), (ax1, ay1, az1), (ax1, ay1, az0))):
        s.quad(*quad, "acrylic")

    # шарики в капсуле
    rng = np.random.default_rng(4)
    r = 1.15
    z, y = az0 + r + 0.1, ay0 + r + 0.1
    while y < ay1 - r - 1.0:
        x = ax0 + r + 0.1 + (0.6 * r if int((y - ay0) / (2 * r)) % 2 else 0)
        while x < ax1 - r - 0.1:
            s.balls.append((x + rng.normal(0, 0.12), y + rng.normal(0, 0.12),
                            z + rng.normal(0, 0.12), r))
            x += 2 * r * 1.02
        y += 2 * r * 0.90
        z += rng.normal(0, 0.35)
        z = float(np.clip(z, az0 + r + 0.1, az1 - r - 0.1))
    return s


# ---------------------------------------------------------------- материалы
def materials() -> dict:
    door = Image.new("RGB", (240, 420), (243, 241, 237))
    d = ImageDraw.Draw(door)
    d.ellipse([70, 120, 170, 220], outline=(120, 116, 110), width=3)
    d.line([0, 60, 240, 60], fill=(200, 196, 190), width=3)
    return {
        "front":    dict(tex=tex_front(), ks=0.22, shine=16, amb=0.30),
        "side":     dict(tex=tex_side(), ks=0.20, shine=16, amb=0.34),
        "side_r":   dict(tex=tex_side().transpose(Image.FLIP_LEFT_RIGHT), ks=0.20, shine=16, amb=0.34),
        "shell":    dict(tex=silk(200, 200, 11), ks=0.22, shine=16, amb=0.30),
        "top":      dict(tex=silk(200, 200, 13, 0.92), ks=0.20, shine=14, amb=0.34),
        "backwall": dict(tex=tex_back_wall(), ks=0.04, shine=4, amb=0.74),
        "white":    dict(tex=flat((246, 244, 240)), ks=0.04, shine=4, amb=0.80),
        "door":     dict(tex=door, ks=0.04, shine=4, amb=0.82),
        "shelf":    dict(tex=flat((250, 248, 244)), ks=0.05, shine=5, amb=0.86),
        "acrylic":  dict(tex=flat((255, 255, 255)), ks=0.9, shine=70, alpha=0.12, amb=0.9),
    }


LIGHTS = [
    (np.array([-0.52, 0.68, 0.52]), np.array([1.00, 0.97, 0.93]), 0.70),
    (np.array([0.80, 0.30, 0.50]), np.array([0.90, 0.93, 1.00]), 0.30),
    (np.array([0.10, 0.20, 1.00]), np.array([1.00, 0.97, 0.92]), 0.30),   # свет в камеру
]


def render(scene: Scene, cam: Camera, w=1200, h=1500, ss=1.6) -> np.ndarray:
    Wp, Hp = int(w * ss), int(h * ss)
    color = np.zeros((Hp, Wp, 3), np.float32)
    alpha = np.zeros((Hp, Wp), np.float32)
    depth = np.full((Hp, Wp), np.inf, np.float32)

    mats = materials()
    verts, owner = [], []
    for i, t in enumerate(scene.tris):
        verts.extend(t[:3])
        owner.append(i)
    verts = np.array(verts, np.float32)
    scr, zz = cam.project(verts, Wp, Hp)

    order = []
    for i, t in enumerate(scene.tris):
        c = (t[0] + t[1] + t[2]) / 3.0
        order.append((np.linalg.norm(c - cam.eye), i))
    order.sort(reverse=True)

    for _, i in order:
        p0, p1, p2, uv0, uv1, uv2, matname = scene.tris[i]
        mat = mats[matname]
        s0, s1, s2 = scr[i * 3], scr[i * 3 + 1], scr[i * 3 + 2]
        z0, z1, z2 = zz[i * 3], zz[i * 3 + 1], zz[i * 3 + 2]
        if min(z0, z1, z2) <= 0:
            continue
        xmin = max(0, int(math.floor(min(s0[0], s1[0], s2[0]))))
        xmax = min(Wp - 1, int(math.ceil(max(s0[0], s1[0], s2[0]))))
        ymin = max(0, int(math.floor(min(s0[1], s1[1], s2[1]))))
        ymax = min(Hp - 1, int(math.ceil(max(s0[1], s1[1], s2[1]))))
        if xmax <= xmin or ymax <= ymin:
            continue
        X, Y = np.meshgrid(np.arange(xmin, xmax + 1, dtype=np.float32) + 0.5,
                           np.arange(ymin, ymax + 1, dtype=np.float32) + 0.5)
        den = (s1[0] - s0[0]) * (s2[1] - s0[1]) - (s2[0] - s0[0]) * (s1[1] - s0[1])
        if abs(den) < 1e-9:
            continue
        w0 = ((s1[0] - X) * (s2[1] - Y) - (s2[0] - X) * (s1[1] - Y)) / den
        w1 = ((s2[0] - X) * (s0[1] - Y) - (s0[0] - X) * (s2[1] - Y)) / den
        w2 = 1.0 - w0 - w1
        inside = (w0 >= -2e-4) & (w1 >= -2e-4) & (w2 >= -2e-4)
        if not inside.any():
            continue
        iz = 1.0 / np.maximum(w0 / z0 + w1 / z1 + w2 / z2, 1e-9)
        sub = depth[ymin:ymax + 1, xmin:xmax + 1]
        mask = inside & (iz < sub)
        if not mask.any():
            continue

        u = (w0 * uv0[0] / z0 + w1 * uv1[0] / z1 + w2 * uv2[0] / z2) * iz
        v = (w0 * uv0[1] / z0 + w1 * uv1[1] / z1 + w2 * uv2[1] / z2) * iz
        tex = np.asarray(mat["tex"], np.float32)
        th, tw = tex.shape[:2]
        tx = np.clip((u * (tw - 1)).astype(np.int32), 0, tw - 1)
        ty = np.clip((v * (th - 1)).astype(np.int32), 0, th - 1)
        sample = tex[ty, tx]

        n = np.cross(p1 - p0, p2 - p0)
        centre = (p0 + p1 + p2) / 3.0
        vd = cam.eye - centre
        vd /= np.linalg.norm(vd) + 1e-9
        if float(n @ vd) < 0:
            n = -n
        n /= np.linalg.norm(n) + 1e-9

        amb = mat["amb"]
        light = np.array([amb, amb, amb], np.float32)
        spec = 0.0
        inside_box = centre[2] > BACK_Z - 2 and centre[1] < FRONT_TOP_Y - 1
        for ldir, lcol, power in LIGHTS:
            if inside_box is False and ldir is LIGHTS[2][0]:
                continue
            l = ldir / np.linalg.norm(ldir)
            diff = max(0.0, float(n @ l))
            light = light + lcol * diff * power
            hvec = l + vd
            hvec /= np.linalg.norm(hvec) + 1e-9
            spec += power * max(0.0, float(n @ hvec)) ** mat["shine"]

        raw = np.clip(sample * light[None, None, :] + spec * mat["ks"] * 200.0, 0, 255)
        lit = 255.0 * (1.0 - np.exp(-raw / 255.0 * 1.35))
        lit = np.clip(lit, 0, 255)
        a = mat.get("alpha", 1.0)
        dst = color[ymin:ymax + 1, xmin:xmax + 1]
        da = alpha[ymin:ymax + 1, xmin:xmax + 1]
        blended = dst * (1 - a) + lit * a
        dst[mask] = blended[mask]
        da[mask] = np.clip(a + da[mask] * (1 - a), 0, 1)
        sub[mask] = iz[mask]

    # шарики
    draw_balls(scene, cam, color, alpha, depth, Wp, Hp, ss)

    out = np.dstack([np.clip(color, 0, 255), np.clip(alpha * 255, 0, 255)]).astype(np.uint8)
    img = Image.fromarray(out, "RGBA").resize((w, h), Image.LANCZOS)
    return np.asarray(img)


def draw_balls(scene, cam, color, alpha, depth, Wp, Hp, ss):
    if not scene.balls:
        return
    pts = np.array([[b[0], b[1], b[2]] for b in scene.balls], np.float32)
    scr, zz = cam.project(pts, Wp, Hp)
    order = np.argsort(-zz)
    for i in order:
        cx, cy = scr[i]
        z = zz[i]
        r = scene.balls[i][3]
        rpx = r * (Hp / 2) / (z * cam.tan)
        if rpx < 0.8:
            continue
        x0, x1 = int(cx - rpx), int(cx + rpx) + 1
        y0, y1 = int(cy - rpx), int(cy + rpx) + 1
        if x1 <= 0 or y1 <= 0 or x0 >= Wp or y0 >= Hp:
            continue
        x0, y0 = max(0, x0), max(0, y0)
        x1, y1 = min(Wp, x1), min(Hp, y1)
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / max(rpx, 1e-3)
        inside = d <= 1.0
        if not inside.any():
            continue
        sub = depth[y0:y1, x0:x1]
        vis = inside & (z < sub + 4)
        if not vis.any():
            continue
        # сфера: блик сверху-слева, тень снизу
        nx = (xx - cx) / max(rpx, 1e-3)
        ny = (yy - cy) / max(rpx, 1e-3)
        nz = np.sqrt(np.clip(1 - nx ** 2 - ny ** 2, 0, 1))
        shade = 0.62 + 0.45 * np.clip(-0.45 * nx - 0.65 * ny + 0.6 * nz, 0, 1)
        spec = np.clip(nx * -0.45 + ny * -0.6 + nz * 0.66, 0, 1) ** 12
        col = np.clip(232 * shade + 190 * spec, 0, 255)
        dst = color[y0:y1, x0:x1]
        da = alpha[y0:y1, x0:x1]
        blend = 0.92
        dst[vis] = dst[vis] * (1 - blend) + np.stack([col, col * 1.01, col * 1.03], -1)[vis] * blend
        da[vis] = np.maximum(da[vis], 0.95)
        sub[vis] = z - 1.0


def framed_camera(scene: Scene, target, fov=32.0, aspect=0.8, margin=0.90,
                  direction=(0.62, 0.30, 0.78)) -> Camera:
    """Подбирает дистанцию так, чтобы стойка занимала margin высоты кадра."""
    t = np.array(target, np.float32)
    d = np.array(direction, np.float32)
    d /= np.linalg.norm(d)
    pts = np.array([[x, y, z] for x in (0, W) for y in (0, H) for z in (0, D)], np.float32)

    lo, hi = 60.0, 2000.0
    cam = Camera(t + d * 400.0, t, fov)
    for _ in range(40):
        mid = (lo + hi) / 2
        cam = Camera(t + d * mid, t, fov)
        scr, _ = cam.project(pts, 1000, 1000)
        ext = max((scr[:, 1].max() - scr[:, 1].min()), (scr[:, 0].max() - scr[:, 0].min()) * aspect) / 1000
        if ext > margin:
            lo = mid
        else:
            hi = mid
    return Camera(t + d * hi, t, fov)


def over(bg_rgb: np.ndarray, rgba: np.ndarray) -> Image.Image:
    bg = Image.fromarray(bg_rgb).convert("RGBA")
    fg = Image.fromarray(rgba, "RGBA")
    if fg.size != bg.size:
        fg = fg.resize(bg.size, Image.LANCZOS)
    bg.alpha_composite(fg)
    return bg.convert("RGB")
