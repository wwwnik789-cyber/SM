#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Современная версия визуализаций стенда Topotoon — по тем же чертежам.

Геометрия ровно та же, что в `scene.py`:
    9,00 × 5,04 м · 11 столбов 100×100 · высота по столбам 3 000 · обвязка 3 240 ·
    подиум 50 мм · открытый фронт 9 м · глухие левая и задняя стены.

Меняется только язык подачи:
    · светлое натуральное окружение, стены цвета тёплого камня;
    · столбы — анодированный алюминий, без «зеркального» блеска;
    · потолок — линейные светильники в ламелях, холоднее и тоньше;
    · лайм — один точный акцент (линия на полу, подсветка полок), а не заливка;
    · крупная типографика на задней стене, много воздуха;
    · мягкие контактные тени под мебелью.

Стенды клиента — те же и на тех же местах, что в классической версии.
"""
import os
import sys
import numpy as np
from PIL import Image

from engine import (Camera, Box, plane, wall_x, wall_y, cylinder,
                    render, tonemap, post, to_img, Light)

BASE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(BASE, "tex")
OUT = os.path.join(BASE, "..", "renders3d-modern")

W, D, H = 9.00, 5.04, 3.00
BEAM = 0.10
TOP = H + BEAM
POD = 0.05

LIME = np.array([0.80, 0.94, 0.14], np.float32)
VIOLET = np.array([0.56, 0.38, 0.99], np.float32)
ALU = np.array([0.76, 0.77, 0.79], np.float32)          # анодированный алюминий
ALU_D = np.array([0.62, 0.63, 0.66], np.float32)
STONE = np.array([0.90, 0.885, 0.862], np.float32)      # тёплый камень
WHITE = np.array([0.94, 0.935, 0.925], np.float32)

SUN = dict(dir=np.array([-0.22, 0.38, -0.90]),
           color=np.array([1.0, 0.97, 0.92]),
           amb=(0.34, 0.345, 0.375),                       # светлый зал
           bounce=(0.22, 0.21, 0.19))


def load(name, maxw=None):
    im = Image.open(os.path.join(TEX, name)).convert("RGB")
    if maxw and im.width > maxw:
        im = im.resize((maxw, int(im.height * maxw / im.width)), Image.LANCZOS)
    return np.asarray(im, np.float32) / 255


class Scene:
    def __init__(self):
        self.q = []
        self.glows = []
        self.occ = []          # контактные тени: (x, y, rx, ry, сила)

    def add(self, *items):
        for it in items:
            if isinstance(it, (list, tuple)):
                self.q.extend(it)
            else:
                self.q.append(it)

    def glow(self, x, y, z, r, color, s):
        self.glows.append((x, y, z, r, color, s))

    def shadow(self, x, y, rx, ry, strength=0.45):
        self.occ.append((x, y, rx, ry, strength))


# ------------------------------------------------------------------ каркас
def build_frame(s):
    tex_floor = load("mod_floor.png", 1600)

    # пол: светлый микроцемент с лаймовой инкрустацией
    s.add(plane(0, 0, W, D, POD, tex=tex_floor, tint=1.12))
    s.add(Box(0, -0.012, 0, W, 0.012, POD, color=(0.86, 0.85, 0.83)))

    # 11 столбов — анодированный алюминий, тонкий профиль
    posts = [(0, 0), (3, 0), (6, 0), (9, 0),
             (0, 2.52), (9, 2.52),
             (0, D), (3, D), (6, D), (9, D), (4.5, 2.52)]
    for (px, py) in posts:
        s.add(Box(px - BEAM / 2, py - BEAM / 2, POD, px + BEAM / 2, py + BEAM / 2, H,
                  color=tuple(ALU), top=tuple(ALU), side=tuple(ALU_D)))
        s.shadow(px, py, 0.30, 0.30, 0.42)

    # обвязка
    for (x0, y0, x1, y1) in ((-BEAM / 2, -BEAM / 2, W + BEAM / 2, BEAM / 2),
                             (-BEAM / 2, D - BEAM / 2, W + BEAM / 2, D + BEAM / 2),
                             (-BEAM / 2, -BEAM / 2, BEAM / 2, D + BEAM / 2),
                             (W - BEAM / 2, -BEAM / 2, W + BEAM / 2, D + BEAM / 2)):
        s.add(Box(x0, y0, H, x1, y1, TOP, color=tuple(ALU), side=tuple(ALU_D),
                  top=tuple(ALU)))

    # подвесная рамка-портал над входом — современный акцент вместо арки
    for (x0, x1) in ((0.55, 0.63), (8.37, 8.45)):
        s.add(Box(x0, 0.08, POD, x1, -0.05 + 0.13, TOP + 0.32,
                  color=tuple(ALU), side=tuple(ALU_D)))
    s.add(Box(0.55, 0.02, TOP + 0.26, 8.45, 0.15, TOP + 0.34,
              color=tuple(ALU), side=tuple(ALU_D)))

    # потолок: ламели реже, между ними — линейные светильники
    y = 0.34
    while y < D - 0.24:
        s.add(Box(0.05, y - 0.022, TOP - 0.012, W - 0.05, y + 0.022, TOP + 0.075,
                  color=tuple(ALU), side=tuple(ALU_D)))
        y += 0.42
    return s


# ------------------------------------------------------------------ стены
def build_walls(s):
    tex_back = load("mod_back.png", 1800)
    tex_left = load("mod_left.png", 1100)

    # задняя стена 9 × 3 м — светлый текстиль с крупным лого
    s.add(wall_y(D - 0.02, -BEAM / 2, W + BEAM / 2, POD, H, tex=tex_back, tint=1.06))
    # левая стена 5,04 × 3 м — панели с нишей обложек
    s.add(wall_x(0.02, -BEAM / 2, D, POD, H, tex=tex_left, tint=1.06))
    # наружные грани — та же графика, без зеркал
    s.add(wall_x(-0.015, -BEAM / 2, D, POD, H, tex=tex_left[:, ::-1], tint=0.90))
    s.add(wall_y(D + 0.012, -BEAM / 2, W + BEAM / 2, POD, H,
                 tex=tex_back[:, ::-1], tint=0.88))

    # правая стена — глухая часть за кладовой, тон в тон камню
    s.add(wall_x(W - 0.02, D, 3.30, POD, H, color=tuple(STONE * 0.88)))

    # фриз: тонкая светлая полоса с лого — сдержанно, высота 0,30 м
    tex_fr = load("mod_frieze.png", 1500)
    s.add(wall_y(-BEAM / 2 - 0.012, 0, W, TOP + 0.02, TOP + 0.32,
                 tex=tex_fr, emissive=0.26))
    s.add(wall_x(-BEAM / 2 - 0.012, -0.05, 0, TOP + 0.02, TOP + 0.32,
                 color=tuple(WHITE), emissive=0.24))
    s.add(wall_x(W + BEAM / 2 + 0.012, 0, -0.05, TOP + 0.02, TOP + 0.32,
                 color=tuple(WHITE), emissive=0.24))


# ------------------------------------------------------------------ зоны
def build_zones(s):
    covers = load("mod_covers.png", 900)

    # --- ЛЕВО: длинный низкий стеллаж-витрина вдоль стены (современно: одна линия)
    s.add(Box(0.10, 1.00, POD, 0.46, 3.45, 0.78, color=tuple(WHITE),
              top=tuple(WHITE * 1.02)))
    s.add(wall_x(0.47, 1.02, 3.43, 0.20, 0.74, tex=covers, emissive=0.06))
    s.add(Box(0.10, 1.00, 0.78, 0.47, 3.45, 0.82, color=tuple(LIME), emissive=0.18))
    s.shadow(0.30, 2.22, 0.55, 1.55, 0.40)

    # --- ЗАДНЯЯ стена слева: большой экран в тонкой чёрной раме
    s.add(Box(1.15, D - 0.10, 1.42, 3.30, D - 0.06, 2.52, color=(0.09, 0.09, 0.10)))
    s.add(wall_y(D - 0.11, 1.19, 3.26, 1.46, 2.48, tex=load("screen.png", 800),
                 emissive=0.28))

    # лаунж: низкая платформа и мягкие пуфы в двух оттенках
    s.add(Box(1.10, 3.55, POD, 3.40, 4.75, POD + 0.14, color=tuple(WHITE * 0.99)))
    s.shadow(2.25, 4.15, 1.35, 0.75, 0.32)
    for (px, py, col) in ((1.55, 4.22, VIOLET), (2.42, 4.22, LIME),
                          (1.55, 3.62, LIME), (2.42, 3.62, VIOLET)):
        s.add(cylinder(px, py, 0.27, POD + 0.14, 0.44, seg=22, color=tuple(col)))
        s.shadow(px, py, 0.34, 0.34, 0.28)

    # --- ЗАДНЯЯ стена справа: витрина постеров в тонкой раме
    s.add(Box(3.60, D - 0.10, 1.40, 5.30, D - 0.06, 2.50, color=(0.09, 0.09, 0.10)))
    s.add(wall_y(D - 0.11, 3.64, 5.26, 1.44, 2.46, tex=covers, emissive=0.05))

    # --- тележка-корзина на колёсах
    s.add(Box(5.15, 4.05, POD + 0.46, 6.00, 4.52, 0.96, color=(0.84, 0.85, 0.86)))
    for dx in (-0.38, 0.38):
        s.add(Box(5.20 + dx, 4.10, POD, 5.27 + dx, 4.47, POD + 0.46,
                  color=(0.55, 0.56, 0.58)))
    s.shadow(5.57, 4.28, 0.62, 0.42, 0.34)

    # --- телефонная будка: алюминиевый каркас, прозрачное стекло, лаймовая шапка
    bx, by = 8.35, 2.85
    hw, hd = 0.42, 0.34
    s.add(Box(bx - hw, by - hd, POD, bx + hw, by + hd, POD + 0.05, color=tuple(ALU_D)))
    for dx in (-hw, hw):
        for dy in (-hd, hd):
            s.add(Box(bx + dx - 0.018, by + dy - 0.018, POD + 0.05,
                      bx + dx + 0.018, by + dy + 0.018, 2.24, color=tuple(ALU)))
    for (yy, x0, x1) in ((by - hd, bx - hw, bx + hw), (by + hd, bx - hw, bx + hw)):
        s.add(wall_y(yy, x0, x1, POD + 0.08, 2.20, color=(0.86, 0.90, 0.90), emissive=0.14))
    for (xx, y0, y1) in ((bx - hw, by - hd, by + hd), (bx + hw, by - hd, by + hd)):
        s.add(wall_x(xx, y0, y1, POD + 0.08, 2.20, color=(0.86, 0.90, 0.90), emissive=0.14))
    s.add(Box(bx - hw - 0.05, by - hd - 0.05, 2.24, bx + hw + 0.05, by + hd + 0.05, 2.40,
              color=tuple(LIME), top=tuple(LIME), emissive=0.30))
    s.shadow(bx, by, 0.56, 0.48, 0.34)

    # --- кладовая: тёмный объём в дальнем правом углу, матовый
    s.add(Box(7.55, 3.35, POD, 8.98, D - 0.03, 2.98, color=(0.20, 0.205, 0.215)))
    s.shadow(8.26, 4.16, 0.85, 0.95, 0.30)

    # --- гача: два автомата, чистые формы
    for i, col in enumerate((LIME, VIOLET)):
        gy = 2.35 - i * 0.66
        s.add(Box(8.28, gy, POD, 8.92, gy + 0.52, 1.58, color=tuple(col),
                  top=tuple(col), emissive=0.10))
        s.add(wall_y(gy - 0.012, 8.32, 8.88, 0.94, 1.42,
                     color=(0.96, 0.97, 0.97), emissive=0.18))
        s.shadow(8.60, gy + 0.26, 0.42, 0.36, 0.30)

    # --- касса: длинная стойка с каменной столешницей
    s.add(Box(2.30, 2.00, POD, 4.40, 2.50, 0.98, color=(0.95, 0.945, 0.935)))
    s.add(Box(2.26, 1.96, 0.98, 4.44, 2.54, 1.03, color=(0.86, 0.85, 0.83),
              top=(0.88, 0.87, 0.85)))
    s.add(Box(3.00, 2.12, 1.03, 3.28, 2.36, 1.32, color=(0.10, 0.10, 0.11)))
    s.add(Box(4.58, 2.10, POD, 5.18, 2.40, 1.30, color=tuple(WHITE),
              top=tuple(LIME)))
    s.shadow(3.35, 2.25, 1.30, 0.55, 0.40)
    s.shadow(4.88, 2.25, 0.42, 0.32, 0.30)

    # --- стеллаж-вертушка у входа
    s.add(cylinder(1.15, 1.65, 0.22, POD, 1.62, seg=18, color=tuple(ALU_D)))
    s.shadow(1.15, 1.65, 0.34, 0.34, 0.32)

    # --- барные стулья: тонкий металл, светлое сиденье
    for i in range(3):
        yy = 1.35 + i * 0.55
        s.add(cylinder(0.96, yy, 0.15, POD + 0.60, 0.68, seg=14, color=tuple(WHITE)))
        s.add(cylinder(0.96, yy, 0.025, POD, POD + 0.60, seg=8, color=tuple(ALU_D)))
        s.shadow(0.96, yy, 0.24, 0.24, 0.26)


# ------------------------------------------------------------------ свет
def scene_lights():
    L = [Light((4.5, -3.2, 4.4), color=(0.86, 0.90, 1.0), power=0.30, radius=10.0)]
    # линейные светильники в потолке
    for x in (1.6, 4.5, 7.4):
        for y in (1.2, 3.2):
            L.append(Light((x, y, TOP - 0.06), color=(1.0, 0.97, 0.92),
                           power=0.34, radius=3.2, down=0.6))
    # подсветка полок и ниши
    L.append(Light((0.45, 2.2, 0.80), color=(0.80, 0.95, 0.25), power=0.26, radius=1.9))
    L.append(Light((0.20, 2.2, 2.10), color=(1.0, 0.97, 0.92), power=0.22, radius=2.2))
    # стена и экран
    L.append(Light((2.2, 4.55, 2.70), color=(1.0, 0.96, 0.90), power=0.24, radius=3.2))
    L.append(Light((4.5, 4.55, 2.70), color=(1.0, 0.96, 0.90), power=0.20, radius=3.0))
    # будка и гача
    L.append(Light((8.35, 2.85, 2.30), color=(0.85, 0.98, 0.35), power=0.24, radius=2.2))
    L.append(Light((8.60, 1.8, 1.40), color=(0.85, 0.80, 1.0), power=0.22, radius=2.4))
    return L


def build_scene():
    s = Scene()
    build_frame(s)
    build_walls(s)
    build_zones(s)
    return s


# ------------------------------------------------------------------ кадры
SHOTS = {
    "01-hero":    dict(pos=(-4.6, -9.4, 2.9), look=(4.6, 2.5, 1.62), fov=45),
    "02-front":   dict(pos=(4.5, -9.0, 1.75), look=(4.5, 1.8, 1.70), fov=50),
    "03-inside":  dict(pos=(1.35, -0.9, 1.65), look=(4.9, 4.2, 1.45), fov=70),
    "04-lounge":  dict(pos=(4.15, 0.75, 1.62), look=(1.75, 4.55, 1.58), fov=56),
    "05-cashier": dict(pos=(6.35, 4.35, 1.66), look=(2.05, 2.35, 1.22), fov=50),
    "06-booth":   dict(pos=(1.90, -1.30, 1.62), look=(7.6, 3.4, 1.35), fov=58),
}


def shot(name, pos, look, fov=52, w=1920, h=1080, exposure=0.88, bloom=0.12):
    s = build_scene()
    cam = Camera(pos, look, fov=fov, w=w, h=h)
    img = render(s.q, cam, bg=(0.115, 0.118, 0.125), sun=SUN,
                 glow_spots=s.glows, fog_col=(0.20, 0.20, 0.215),
                 fog_start=15.0, fog_amt=0.34, lights=scene_lights(),
                 occluders=s.occ, grain=0.004)
    img = tonemap(img, exposure=exposure, contrast=1.03, lift=0.020)
    img = post(img, bloom=bloom, bloom_thresh=0.82)
    os.makedirs(OUT, exist_ok=True)
    to_img(img).save(os.path.join(OUT, name + ".png"), quality=95, optimize=True)
    return img


def main():
    only = sys.argv[1:] or list(SHOTS)
    for k in only:
        shot(k, **SHOTS[k])
        print("  готов", k)


if __name__ == "__main__":
    main()
