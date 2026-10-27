#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Сцена стенда Topotoon 9,00 × 5,04 м по модели заказчика (Topooton stand4.png).

Геометрия — строго по модели:
  · подиум 9,00 × 5,04 м, верх 0,05 м;
  · столбы 100×100: низ 0,05, верх 3,00 (высота по внутренним столбам);
  · верхняя обвязка 100×100: низ 3,00, верх 3,24;
  · ламели 60×120 по потолку, шаг 0,30 по глубине;
  · открытый фронт — сторона 9 м (y = 0);
  · левая стена x = 0 и задняя y = 5,04 — глухие, под баннеры с брендингом;
  · правая стена — только дальняя часть, за кладовой.

Стенды клиента расставлены по его же плану (viz/stand-plan-top.png).
"""
import os
import numpy as np
from PIL import Image

from engine import (Camera, Quad, Box, plane, wall_x, wall_y, cylinder,
                    render, tonemap, post, to_img, Light)

BASE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(BASE, "tex")

W, D, H = 9.00, 5.04, 3.00
BEAM = 0.10
TOP = H + BEAM                  # 3.24
POD = 0.05                      # подиум

LIME = np.array([0.80, 0.94, 0.14], np.float32)
VIOLET = np.array([0.56, 0.38, 0.99], np.float32)
SILVER = np.array([0.62, 0.635, 0.66], np.float32)
SILVER_D = np.array([0.44, 0.45, 0.48], np.float32)

SUN = dict(dir=np.array([-0.30, 0.50, -0.81]),
           color=np.array([1.0, 0.95, 0.88]),
           amb=(0.085, 0.09, 0.125),
           bounce=(0.10, 0.105, 0.10))


def load(name, maxw=None):
    im = Image.open(os.path.join(TEX, name)).convert("RGB")
    if maxw and im.width > maxw:
        im = im.resize((maxw, int(im.height * maxw / im.width)), Image.LANCZOS)
    return np.asarray(im, np.float32) / 255


def verticalize(arr):
    return arr[::-1].copy()


class Scene:
    def __init__(self):
        self.q = []
        self.glows = []

    def add(self, *items):
        for it in items:
            if isinstance(it, (list, tuple)):
                self.q.extend(it)
            else:
                self.q.append(it)

    def glow(self, x, y, z, r, color, s):
        self.glows.append((x, y, z, r, color, s))


# ------------------------------------------------------------------ каркас
def build_frame(s):
    tex_floor = load("floor.png", 1500)
    tex_silver = load("silver.png", 512)

    # пол: винил с напольной печатью маскота
    s.add(plane(0, 0, W, D, POD, tex=tex_floor, tint=0.78))
    # кромка подиума
    s.add(Box(0, -0.01, 0, W, 0.015, POD, color=(0.16, 0.165, 0.18)))

    # 10 столбов по краям + 1 внутренний — как в модели
    posts = [(0, 0), (3, 0), (6, 0), (9, 0),
             (0, 2.52), (9, 2.52),
             (0, 5.04), (3, 5.04), (6, 5.04), (9, 5.04),
             (4.5, 2.52)]
    for (px, py) in posts:
        s.add(Box(px - BEAM / 2, py - BEAM / 2, POD, px + BEAM / 2, py + BEAM / 2, H,
                  color=tuple(SILVER), top=tuple(SILVER), side=tuple(SILVER_D)))

    # верхняя обвязка по периметру — верхняя плоскость с царапкой
    for (x0, y0, x1, y1) in ((-BEAM / 2, -BEAM / 2, W + BEAM / 2, BEAM / 2),
                             (-BEAM / 2, D - BEAM / 2, W + BEAM / 2, D + BEAM / 2),
                             (-BEAM / 2, -BEAM / 2, BEAM / 2, D + BEAM / 2),
                             (W - BEAM / 2, -BEAM / 2, W + BEAM / 2, D + BEAM / 2)):
        s.add(Box(x0, y0, H, x1, y1, TOP, color=tuple(SILVER), side=tuple(SILVER_D),
                  tex_top=tex_silver))

    # ламели: 60×120, шаг 0,30 по глубине, вдоль длинной стороны
    y = 0.30
    while y < D - 0.20:
        s.add(Box(0.05, y - 0.03, TOP - 0.015, W - 0.05, y + 0.03, TOP + 0.10,
                  color=tuple(SILVER), side=tuple(SILVER_D), tex_top=tex_silver))
        y += 0.30
    return s


# ------------------------------------------------------------------ баннеры
def build_walls(s):
    """
    Задняя стена 9 × 3 м и левая 5,04 × 3 м — баннеры с брендингом клиента.
    Обе стены — изнутри, поэтому текстуры развёрнуты правильной стороной.
    """
    tex_back = load("banner_back.png", 1600)
    tex_left = load("banner_left.png", 1100)

    # задняя стена: вершины слева→справа, нормаль в −y (на зрителя). Без зеркал.
    s.add(wall_y(D - 0.02, -BEAM / 2, W + BEAM / 2, POD, H, tex=tex_back, tint=0.95))
    # левая стена: вершины от фронта в глубину, нормаль в +x (внутрь)
    s.add(wall_x(0.02, -BEAM / 2, D, POD, H, tex=tex_left, tint=0.95))
    # левая стена, наружная грань: тот же порядок вершин, но текстура зеркалится —
    # снаружи зал видит брендинг, а не перевёрнутую надпись
    s.add(wall_x(-0.015, -BEAM / 2, D, POD, H, tex=tex_left[:, ::-1], tint=0.80))
    # задняя стена, наружная грань
    s.add(wall_y(D + 0.012, -BEAM / 2, W + BEAM / 2, POD, H,
                 tex=tex_back[:, ::-1], tint=0.78))
    # правая стена — глухая часть за кладовой
    s.add(wall_x(W - 0.02, D, 3.30, POD, H, color=(0.10, 0.105, 0.125)))

    # фриз по фронту — световой короб во всю ширину 9 м
    tex_fr = load("frieze.png", 1500)
    s.add(wall_y(-BEAM / 2 - 0.012, 0, W, TOP + 0.06, TOP + 0.66,
                 tex=tex_fr, emissive=0.12))
    # торцы фриза
    s.add(wall_x(-BEAM / 2 - 0.012, -0.06, 0, TOP + 0.06, TOP + 0.66,
                 color=tuple(LIME), emissive=0.40))
    s.add(wall_x(W + BEAM / 2 + 0.012, 0, -0.06, TOP + 0.06, TOP + 0.66,
                 color=tuple(LIME), emissive=0.40))


# ------------------------------------------------------------------ зоны
def build_zones(s):
    cover_v = verticalize(load("covers_vert.png", 420))
    screen = load("screen.png", 760)

    # --- ЛЕВО: витрина вебтунов вдоль левой стены
    s.add(Box(0.12, 0.95, POD, 0.52, 3.50, 2.32, color=(0.12, 0.125, 0.15)))
    s.add(wall_x(0.53, 0.97, 3.48, 0.72, 2.24, tex=cover_v, emissive=0.06))
    s.add(Box(0.12, 0.95, 2.32, 0.52, 3.50, 2.44, color=tuple(LIME), emissive=0.5))

    # --- ЗАДНЯЯ СТЕНА слева: экран аниме-лаунжа
    s.add(wall_y(D - 0.07, 1.10, 3.35, 1.30, 2.55, tex=screen, emissive=0.22))
    s.add(Box(1.00, D - 0.12, 1.22, 3.45, D - 0.02, 1.30, color=(0.10, 0.10, 0.12)))

    # пуфы
    for (px, py, col) in ((1.55, 4.25, VIOLET), (2.45, 4.25, LIME),
                          (1.55, 3.60, LIME), (2.45, 3.60, VIOLET)):
        s.add(cylinder(px, py, 0.30, POD, 0.40, seg=18, color=tuple(col)))

    # --- ЗАДНЯЯ СТЕНА справа: витрина постеров
    s.add(wall_y(D - 0.07, 3.65, 5.35, 1.32, 2.56, tex=cover_v, emissive=0.05))
    s.add(Box(3.58, D - 0.13, 1.24, 5.42, D - 0.02, 1.32, color=tuple(LIME), emissive=0.3))

    # тележка
    s.add(Box(5.05, 4.10, POD + 0.45, 5.95, 4.58, 0.98, color=(0.58, 0.59, 0.63)))
    for dx in (-0.40, 0.40):
        s.add(Box(5.10 + dx, 4.14, POD, 5.18 + dx, 4.54, POD + 0.45,
                  color=(0.34, 0.35, 0.37)))

    # --- телефонная будка: каркас, стекло, шапка — как в концепции клиента
    bx, by = 8.35, 2.85
    hw, hd = 0.42, 0.34
    # цоколь
    s.add(Box(bx - hw, by - hd, POD, bx + hw, by + hd, POD + 0.06,
              color=(0.18, 0.19, 0.22)))
    # стойки каркаса
    for dx in (-hw, hw):
        for dy in (-hd, hd):
            s.add(Box(bx + dx - 0.02, by + dy - 0.02, POD + 0.06,
                      bx + dx + 0.02, by + dy + 0.02, 2.20,
                      color=(0.30, 0.31, 0.34)))
    # стекло: полупрозрачное, с лёгким свечением
    for (y0, y1, x0, x1) in ((by - hd, by + hd, bx - hw, bx + hw),):
        s.add(wall_y(by - hd, x0 + 0.02, x1 - 0.02, POD + 0.10, 2.14,
                     color=(0.30, 0.42, 0.34), emissive=0.10))
        s.add(wall_y(by + hd, x1 - 0.02, x0 + 0.02, POD + 0.10, 2.14,
                     color=(0.26, 0.36, 0.30), emissive=0.08))
        s.add(wall_x(bx - hw, y0 + 0.02, y1 - 0.02, POD + 0.10, 2.14,
                     color=(0.30, 0.42, 0.34), emissive=0.10))
        s.add(wall_x(bx + hw, y1 - 0.02, y0 + 0.02, POD + 0.10, 2.14,
                     color=(0.26, 0.36, 0.30), emissive=0.08))
    # аппарат внутри
    s.add(Box(bx + 0.16, by - 0.10, 0.90, bx + 0.26, by + 0.10, 1.55,
              color=(0.10, 0.10, 0.12)))
    # шапка-светокороб
    s.add(Box(bx - hw - 0.06, by - hd - 0.06, 2.20, bx + hw + 0.06, by + hd + 0.06, 2.42,
              color=tuple(LIME), top=tuple(LIME), emissive=0.42))

    # --- кладовая: тёмный объём в правом дальнем углу
    s.add(Box(7.55, 3.35, POD, 8.98, D - 0.03, 2.98, color=(0.075, 0.078, 0.092)))

    # --- гача-автоматы у фронта справа
    for i in range(2):
        gy = 2.35 - i * 0.66
        col = LIME if i == 0 else VIOLET
        s.add(Box(8.28, gy, POD, 8.92, gy + 0.52, 1.62, color=tuple(col),
                  top=tuple(col), emissive=0.22))
        s.add(wall_y(gy - 0.012, 8.32, 8.88, 0.92, 1.44,
                     color=(0.86, 0.88, 0.93), emissive=0.16))

    # --- касса-островок (в глубине, ближе к центру — как на плане клиента)
    s.add(Box(2.35, 2.05, POD, 4.35, 2.55, 1.02, color=(0.15, 0.16, 0.19),
              top=(0.60, 0.61, 0.65)))
    s.add(wall_y(2.04, 2.40, 4.30, 0.30, 0.88, color=(0.62, 0.64, 0.68), emissive=0.10))
    s.add(Box(3.05, 2.18, 1.02, 3.32, 2.42, 1.30, color=(0.09, 0.09, 0.11)))
    s.add(Box(4.55, 2.15, POD, 5.15, 2.45, 1.36, color=tuple(LIME), emissive=0.2))

    # --- стеллаж-вертушка у входа слева
    s.add(cylinder(1.15, 1.65, 0.24, POD, 1.72, seg=16, color=(0.28, 0.29, 0.32)))
    # --- барные стулья у витрины
    for i in range(3):
        yy = 1.35 + i * 0.55
        s.add(cylinder(0.98, yy, 0.16, POD, 0.74, seg=12, color=tuple(LIME)))
        s.add(cylinder(0.98, yy, 0.02, POD, 0.74, seg=6, color=(0.28, 0.28, 0.30)))


# ------------------------------------------------------------------ свет
def scene_lights():
    """
    Свет зала: тёплый заполняющий, трековые споты по сетке, лаймовые акценты.
    Всё попиксельно — на стенах получаются настоящие световые пятна.
    """
    L = []
    L.append(Light((4.5, -3.0, 4.2), color=(0.62, 0.70, 0.80), power=0.55, radius=9.0))
    # трековые споты под обвязкой
    for x in (1.5, 4.5, 7.5):
        for y in (1.1, 3.3):
            L.append(Light((x, y, TOP - 0.12), color=(1.0, 0.88, 0.72),
                           power=1.15, radius=3.2, down=0.55))
    # лаймовая заливка от фриза (светит внутрь)
    L.append(Light((4.5, 0.15, TOP + 0.30), color=(0.72, 0.90, 0.18),
                   power=0.85, radius=5.0))
    # подсветка витрины вебтунов и лаунжа
    L.append(Light((0.9, 2.3, 2.35), color=(0.85, 0.95, 0.35), power=0.55, radius=2.6))
    L.append(Light((2.3, 4.3, 2.35), color=(0.80, 0.75, 1.00), power=0.45, radius=3.0))
    # подсветка заднего баннера — чтобы глубина не проваливалась в темноту
    L.append(Light((3.0, 4.6, 2.55), color=(1.0, 0.92, 0.80), power=0.65, radius=3.4))
    L.append(Light((6.0, 4.6, 2.55), color=(1.0, 0.92, 0.80), power=0.55, radius=3.2))
    # подсветка заднего баннера — чтобы глубина не проваливалась в темноту
    L.append(Light((2.6, 4.55, 2.60), color=(1.0, 0.92, 0.80), power=0.70, radius=3.6))
    L.append(Light((6.2, 4.55, 2.60), color=(1.0, 0.92, 0.80), power=0.55, radius=3.4))
    # будка и гача
    L.append(Light((7.15, 3.95, 2.25), color=(0.75, 0.95, 0.35), power=0.75, radius=2.8))
    L.append(Light((8.55, 1.6, 1.45), color=(0.80, 0.70, 1.00), power=0.45, radius=2.6))
    return L


def build_lights(s):
    for x in (1.6, 4.5, 7.4):
        for y in (1.3, 3.5):
            s.add(Box(x - 0.06, y - 0.06, TOP - 0.14, x + 0.06, y + 0.06, TOP - 0.02,
                      color=(0.10, 0.10, 0.11)))
    s.glow(4.5, -0.05, TOP + 0.35, 1.4, (0.55, 0.62, 0.10), 0.45)
    s.glow(2.2, 4.4, 1.9, 0.9, (0.35, 0.26, 0.10), 0.22)
    s.glow(7.2, 3.9, 2.28, 0.8, (0.55, 0.68, 0.12), 0.35)
    s.glow(8.6, 1.6, 0.9, 0.9, (0.55, 0.45, 0.90), 0.22)
    s.glow(0.5, 2.2, 2.30, 0.7, (0.55, 0.62, 0.12), 0.25)


def build_scene():
    s = Scene()
    build_frame(s)
    build_walls(s)
    build_zones(s)
    build_lights(s)
    return s


# ------------------------------------------------------------------ кадры
SHOTS = {
    # снаружи ¾ — как модель заказчика, весь стенд в кадре
    "01-hero":      dict(pos=(-4.6, -9.4, 2.9), look=(4.6, 2.5, 1.62), fov=45),
    # фронт-портал: шапка и вход целиком
    "02-front":     dict(pos=(4.5, -9.0, 1.75), look=(4.5, 1.8, 1.70), fov=50),
    # изнутри от входа — единое пространство
    "03-inside":    dict(pos=(1.35, -0.9, 1.65), look=(4.9, 4.2, 1.45), fov=70),
    # аниме-лаунж в глубине слева: смотрим от кассы на экран и пуфы
    "04-lounge":    dict(pos=(4.15, 0.75, 1.62), look=(1.75, 4.55, 1.58), fov=56),
    # касса и витрина вебтунов: смотрим от входа вглубь налево
    "05-cashier":   dict(pos=(6.35, 4.35, 1.66), look=(2.05, 2.35, 1.22), fov=50),
    # будка и гача: смотрим от лаунжа вправо-вперёд
    "06-booth":     dict(pos=(1.90, -1.30, 1.62), look=(7.6, 3.4, 1.35), fov=58),
}


def shot(name, pos, look, fov=52, w=1920, h=1080, sun=SUN, exposure=1.15, bloom=0.32):
    s = build_scene()
    cam = Camera(pos, look, fov=fov, w=w, h=h)
    img = render(s.q, cam, glow_spots=s.glows, sun=sun, fog_start=12.0, fog_amt=0.5,
                 lights=scene_lights())
    img = tonemap(img, exposure=exposure, contrast=1.10, lift=0.016)
    img = post(img, bloom=bloom)
    out = os.path.join(BASE, "..", "renders3d")
    os.makedirs(out, exist_ok=True)
    to_img(img).save(os.path.join(out, name + ".png"), quality=95, optimize=True)
    return img


def main():
    import sys
    only = sys.argv[1:] or list(SHOTS)
    for k in only:
        shot(k, **SHOTS[k])
        print("  готов", k)


if __name__ == "__main__":
    main()
