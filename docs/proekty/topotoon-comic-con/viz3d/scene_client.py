#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Визуализации стенда Topotoon ПО ПРЕЗЕНТАЦИИ КЛИЕНТА.

В отличие от `scene_modern.py` (авторский светлый минимализм) здесь взят язык
самого клиента из `00_topotoon-x-comic-con.pdf` 18 стр.:

    «японское комбини»: Топотоон — магазинчик, где вместо товара истории.
    Лаймовые шапки отделов, чёрные панели, полутон, взрывные стикеры,
    полки-гондолы с обложками, касса, гача-автоматы, телефонная будка,
    неоновое зеркало 物語の世界 (в PDF; здесь — «МИР ИСТОРИЙ», CJK-шрифта нет).

Геометрия ровно та же, что в `scene.py` / `scene_modern.py`:
    9,00 × 5,04 м · 11 столбов 100×100 · высота по столбам 3 000 · обвязка 3 240 ·
    подиум 50 мм · открытый фронт 9 м · левая и задняя стены — брендинг.

Металл — царапанное СЕРЕБРО (в презентации золото — по ТЗ НЕ копируем).
"""
import os
import sys
import numpy as np
from PIL import Image

from engine import (Camera, Box, plane, wall_x, wall_y, cylinder, disc,
                    render, tonemap, post, to_img, Light)

BASE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(BASE, "tex")
OUT = os.path.join(BASE, "..", "renders3d-client")

W, D, H = 9.00, 5.04, 3.00
BEAM = 0.10
TOP = H + BEAM
POD = 0.05

# палитра клиента
LIME = np.array([0.800, 0.941, 0.141], np.float32)      # #CCF024
LIME_BR = np.array([0.420, 0.941, 0.165], np.float32)   # #6BF02A
LAV = np.array([0.627, 0.580, 0.941], np.float32)       # #A094F0
INK = np.array([0.082, 0.090, 0.122], np.float32)       # #15171F
PAPER = np.array([0.949, 0.941, 0.894], np.float32)     # #F2F0E4

# серебро: три оттенка, чтобы столбы читались «царапаными», а не зеркальными
SILVER = np.array([0.700, 0.712, 0.726], np.float32)
SILVER_D = np.array([0.560, 0.572, 0.590], np.float32)
SILVER_L = np.array([0.775, 0.786, 0.798], np.float32)

SUN = dict(dir=np.array([-0.24, 0.40, -0.88]),
           color=np.array([1.0, 0.975, 0.93]),
           amb=(0.36, 0.365, 0.395),
           bounce=(0.20, 0.21, 0.19))


def load(name, maxw=None):
    im = Image.open(os.path.join(TEX, name)).convert("RGB")
    if maxw and im.width > maxw:
        im = im.resize((maxw, int(im.height * maxw / im.width)), Image.LANCZOS)
    return np.asarray(im, np.float32) / 255


def fit(tex, w, h, align="center"):
    """Вписать текстуру в поле w×h без искажений. Возвращает (tex, dx, dy) в метрах."""
    ar = tex.shape[1] / tex.shape[0]
    if w / h > ar:                       # поле шире текстуры — упираемся в высоту
        th, tw = h, h * ar
    else:
        tw, th = w, w / ar
    dx, dy = (w - tw) / 2, (h - th) / 2
    if align == "bottom":
        dy = 0.0
    elif align == "top":
        dy = h - th
    return tex, dx, dy


class Scene:
    def __init__(self):
        self.q = []
        self.glows = []
        self.occ = []

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


def panel_y(s, y, x0, x1, z0, z1, name, maxw=1800, emissive=0.10, align="center",
            mirror=False):
    """Панель на стене, перпендикулярной y, с сохранением пропорций."""
    tex = load(name, maxw)
    if mirror:
        tex = tex[:, ::-1]
    tex, dx, dy = fit(tex, x1 - x0, z1 - z0, align)
    s.add(wall_y(y, x0 + dx, x1 - dx, z0 + dy, z1 - dy, tex=tex, emissive=emissive))


def panel_x(s, x, y0, y1, z0, z1, name, maxw=1400, emissive=0.10, align="center",
            mirror=False):
    tex = load(name, maxw)
    if mirror:
        tex = tex[:, ::-1]
    tex, dy, dz = fit(tex, y1 - y0, z1 - z0, align)
    s.add(wall_x(x, y0 + dy, y1 - dy, z0 + dz, z1 - dz, tex=tex, emissive=emissive))


# ------------------------------------------------------------------ каркас
def build_frame(s):
    tex_floor = load("cli_floor.png", 1800)

    # пол: тёмная плитка + лаймовая клякса с маскотом — ровно 9 × 5,04
    s.add(plane(0, 0, W, D, POD, tex=tex_floor, tint=1.0))
    s.add(Box(0, -0.012, 0, W, 0.012, POD, color=(0.10, 0.105, 0.12)))

    # 11 столбов — серебро, тонкий профиль
    posts = [(0, 0), (3, 0), (6, 0), (9, 0),
             (0, 2.52), (9, 2.52),
             (0, D), (3, D), (6, D), (9, D), (4.5, 2.52)]
    for i, (px, py) in enumerate(posts):
        col = SILVER if i % 2 == 0 else SILVER_L
        s.add(Box(px - BEAM / 2, py - BEAM / 2, POD, px + BEAM / 2, py + BEAM / 2, H,
                  color=tuple(col), top=tuple(SILVER_L), side=tuple(SILVER_D)))
        s.shadow(px, py, 0.32, 0.32, 0.46)

    # обвязка
    for (x0, y0, x1, y1) in ((-BEAM / 2, -BEAM / 2, W + BEAM / 2, BEAM / 2),
                             (-BEAM / 2, D - BEAM / 2, W + BEAM / 2, D + BEAM / 2),
                             (-BEAM / 2, -BEAM / 2, BEAM / 2, D + BEAM / 2),
                             (W - BEAM / 2, -BEAM / 2, W + BEAM / 2, D + BEAM / 2)):
        s.add(Box(x0, y0, H, x1, y1, TOP, color=tuple(SILVER), side=tuple(SILVER_D),
                  top=tuple(SILVER_L)))

    # потолок: ламели
    y = 0.34
    while y < D - 0.24:
        s.add(Box(0.05, y - 0.022, TOP - 0.012, W - 0.05, y + 0.022, TOP + 0.075,
                  color=tuple(SILVER), side=tuple(SILVER_D)))
        y += 0.42
    return s


# ------------------------------------------------------------------ стены
def build_walls(s):
    # стены — объёмом, чтобы не просвечивали и читался верхний торец
    s.add(Box(-BEAM / 2, D - 0.04, POD, W + BEAM / 2, D + 0.02, H, color=tuple(INK)))
    s.add(Box(-0.02, -BEAM / 2, POD, 0.05, D, H, color=tuple(INK)))

    # ЗАДНЯЯ: отдел «АНИМЕ» + телеканал (стр. 7, 9)
    panel_y(s, D - 0.043, 0.10, 5.10, 0.52, 2.225, "cli_back_anime.png", emissive=0.12)
    # ЗАДНЯЯ справа: экран «телеканал» в чёрной раме
    s.add(Box(5.26, D - 0.11, 1.48, 7.49, D - 0.04, 2.77, color=(0.055, 0.06, 0.07)))
    s.add(wall_y(D - 0.12, 5.30, 7.45, 1.52, 2.73,
                 tex=load("cli_screen.png", 1200), emissive=0.30))

    # ЛЕВАЯ: отдел «ВЕБТУНЫ» — почти во всю стену
    tex_l = load("cli_left_webtoons.png", 1600)
    tw, dx, dz = fit(tex_l, D, H - POD)
    s.add(wall_x(0.055, 0 + dx, D - dx, POD + dz, H - dz, tex=tex_l, emissive=0.12))

    # наружные грани — поле постеров без текста (логика читается с улицы)
    # наружные грани смотрят от зрителя — текстуры зеркалим, чтобы текст читался
    s.add(wall_x(-0.025, -BEAM / 2, D, POD, H,
                 tex=load("cli_ext_left.png", 1700)[:, ::-1], emissive=0.12))
    s.add(wall_y(D + 0.025, -BEAM / 2, W + BEAM / 2, POD, H,
                 tex=load("cli_ext_back.png", 2000)[:, ::-1], emissive=0.12))

    # правая стена — глухая часть за кладовой
    s.add(wall_x(W - 0.02, 3.30, D, POD, H, color=tuple(INK)))

    # фриз «top◉toon» по фронту и тылу, лайм
    tex_fr = load("cli_frieze.png", 2000)
    s.add(wall_y(-BEAM / 2 - 0.014, 0, W, TOP + 0.02, TOP + 0.34,
                 tex=tex_fr, emissive=0.34))
    s.add(wall_y(D + BEAM / 2 + 0.014, W, 0, TOP + 0.02, TOP + 0.34,
                 tex=tex_fr[:, ::-1], emissive=0.30))
    # борта по левой и правой стороне — фриз идёт по всему периметру
    s.add(wall_x(-BEAM / 2 - 0.014, -0.05, 0, TOP + 0.02, TOP + 0.34,
                 color=tuple(LIME), emissive=0.30))
    s.add(wall_x(W + BEAM / 2 + 0.014, 0, -0.05, TOP + 0.02, TOP + 0.34,
                 color=tuple(LIME), emissive=0.30))
    s.add(wall_x(-BEAM / 2 - 0.03, 0, D, TOP + 0.02, TOP + 0.34,
                 color=tuple(LIME), emissive=0.26))
    s.add(wall_x(W + BEAM / 2 + 0.03, 0, D, TOP + 0.02, TOP + 0.34,
                 color=tuple(LIME), emissive=0.26))


# ------------------------------------------------------------------ зоны
def build_zones(s):
    # --- ЛЕВО: полки-гондолы вдоль стены (стр. 9), лаймовая кромка
    s.add(Box(0.10, 1.00, POD, 0.46, 3.45, 0.78, color=tuple(PAPER)))
    s.add(wall_x(0.462, 1.00, 3.45, POD, 0.78,
                 tex=load("cli_shelf.png", 1200), emissive=0.14))
    s.add(Box(0.10, 0.98, 0.78, 0.465, 3.47, 0.83, color=tuple(LIME), emissive=0.22))
    s.shadow(0.30, 2.22, 0.55, 1.55, 0.46)



    # --- ЛАУНЖ у экрана: платформа и 4 пуфа лайм/фиолет (стр. 10)
    s.add(Box(1.10, 3.55, POD, 3.40, 4.75, POD + 0.14, color=tuple(INK * 1.9)))
    s.shadow(2.25, 4.15, 1.35, 0.75, 0.38)
    for (px, py, col, cap_col) in ((1.55, 4.22, LAV, LIME), (2.42, 4.22, LIME, LAV),
                                   (1.55, 3.62, LIME, LAV), (2.42, 3.62, LAV, LIME)):
        # пуф: корпус, круглая крышка и подушка контрастного цвета
        s.add(cylinder(px, py, 0.29, POD + 0.14, 0.42, seg=22, color=tuple(col)))
        s.add(disc(px, py, 0.29, 0.42, seg=22, color=tuple(col * 1.06)))
        s.add(cylinder(px, py, 0.235, 0.42, 0.50, seg=20, color=tuple(cap_col)))
        s.add(disc(px, py, 0.235, 0.50, seg=20, color=tuple(cap_col * 1.06)))
        s.shadow(px, py, 0.38, 0.38, 0.34)

    # --- ЗАДНЯЯ: фон фото-зоны за тележкой (стр. 8)
    s.add(Box(4.74, 4.68, POD, 6.41, 4.74, 1.44, color=tuple(INK)))
    tex_bk = load("cli_cart_back.png", 900)
    tb, dbx, dbz = fit(tex_bk, 1.67, 1.34)
    s.add(wall_y(4.675, 4.74 + dbx, 6.41 - dbx, POD + dbz, 1.44, tex=tex_bk, emissive=0.14))

    # --- тележка для фото (стр. 8)
    s.add(Box(5.15, 4.05, POD + 0.46, 6.00, 4.52, 0.96, color=(0.52, 0.53, 0.56)))
    s.add(Box(5.19, 4.09, POD + 0.50, 5.96, 4.48, 0.92, color=(0.78, 0.79, 0.81)))
    for dx in (-0.38, 0.38):
        s.add(Box(5.20 + dx, 4.10, POD, 5.27 + dx, 4.47, POD + 0.46,
                  color=(0.34, 0.35, 0.38)))
    s.shadow(5.57, 4.28, 0.64, 0.42, 0.38)

    # --- телефонная будка (стр. 12): серебряный каркас, лаймовая шапка
    bx, by = 8.35, 2.85
    hw, hd = 0.42, 0.34
    s.add(Box(bx - hw, by - hd, POD, bx + hw, by + hd, POD + 0.05, color=tuple(SILVER_D)))
    for dx in (-hw, hw):
        for dy in (-hd, hd):
            s.add(Box(bx + dx - 0.018, by + dy - 0.018, POD + 0.05,
                      bx + dx + 0.018, by + dy + 0.018, 2.24, color=tuple(SILVER)))
    GLASS = (0.62, 0.78, 0.26)
    for (yy, x0, x1) in ((by - hd, bx - hw, bx + hw), (by + hd, bx - hw, bx + hw)):
        s.add(wall_y(yy, x0, x1, POD + 0.08, 2.20, color=GLASS, emissive=0.16))
    for (xx, y0, y1) in ((bx - hw, by - hd, by + hd), (bx + hw, by - hd, by + hd)):
        s.add(wall_x(xx, y0, y1, POD + 0.08, 2.20, color=GLASS, emissive=0.16))
    # горизонтальные рёбра остекления
    for zz in (0.85, 1.55):
        for (yy, x0, x1) in ((by - hd - 0.006, bx - hw, bx + hw),):
            s.add(wall_y(yy, x0, x1, zz, zz + 0.035, color=tuple(SILVER), emissive=0.05))
    # зелёная трубка внутри
    s.add(cylinder(bx - 0.20, by + 0.20, 0.045, 1.10, 1.34, seg=10, color=(0.16, 0.62, 0.34)))
    s.add(Box(bx - hw - 0.05, by - hd - 0.05, 2.24, bx + hw + 0.05, by + hd + 0.05, 2.40,
              color=tuple(LIME), top=tuple(LIME), emissive=0.34))
    # вывеска top◉toon на будке
    s.add(wall_y(by - hd - 0.055, bx - 0.44, bx + 0.44, 2.42, 2.62,
                 tex=load("cli_phone.png", 520), emissive=0.34))
    s.shadow(bx, by, 0.56, 0.48, 0.38)

    # --- кладовая: чёрный объём, лого на фронте
    s.add(Box(7.55, 3.35, POD, 8.98, D - 0.03, 2.98, color=tuple(INK * 1.35)))
    panel_y(s, 3.345, 7.60, 8.93, 0.10, 2.60, "cli_closet.png", maxw=760, emissive=0.12)
    s.shadow(8.26, 4.16, 0.85, 0.95, 0.34)

    # --- гача-автоматы лайм и фиолет (стр. 15)
    for i, (col, texn) in enumerate(((LIME, "cli_gacha_lime.png"), (LAV, "cli_gacha_lav.png"))):
        gy = 2.35 - i * 0.66
        s.add(Box(8.28, gy, POD, 8.92, gy + 0.52, 1.62, color=tuple(col),
                  top=tuple(col), emissive=0.16))
        tg = load(texn, 380)
        t2, ggx, ggz = fit(tg, 0.62, 1.52, "bottom")
        s.add(wall_y(gy - 0.006, 8.28 + ggx, 8.92 - ggx, POD + ggz, 1.57,
                     tex=t2, emissive=0.22))
        s.shadow(8.60, gy + 0.26, 0.42, 0.36, 0.34)

    # --- касса (стр. 14): лаймовая стойка с лого
    s.add(Box(2.30, 2.00, POD, 4.40, 2.50, 0.98, color=tuple(LIME)))
    s.add(Box(2.26, 1.96, 0.98, 4.44, 2.54, 1.03, color=tuple(PAPER),
              top=tuple(PAPER * 0.98)))
    s.add(wall_y(1.994, 2.30, 4.40, POD, 0.93,
                 tex=load("cli_counter.png", 1400), emissive=0.18))
    # кассовый аппарат, скретч-карты, вода
    s.add(Box(3.00, 2.12, 1.03, 3.28, 2.36, 1.32, color=(0.10, 0.10, 0.11),
              top=tuple(SILVER_D)))
    s.add(Box(3.60, 2.14, 1.03, 3.90, 2.34, 1.14, color=tuple(LAV)))
    s.add(Box(2.45, 2.16, 1.03, 2.95, 2.32, 1.11, color=tuple(PAPER)))
    s.add(Box(4.58, 2.10, POD, 5.18, 2.40, 1.30, color=tuple(PAPER), top=tuple(LIME)))
    s.shadow(3.35, 2.25, 1.30, 0.55, 0.44)
    s.shadow(4.88, 2.25, 0.42, 0.32, 0.34)

    # --- неоновое зеркало «МИР ИСТОРИЙ» (стр. 11)
    s.add(Box(8.86, 0.55, POD, 8.94, 1.55, 2.16, color=tuple(INK)))
    tm = load("cli_mirror.png", 760)
    t4, mmx, mmz = fit(tm, 0.96, 2.02)
    s.add(wall_x(8.855, 0.55 + mmx, 1.55 - mmx, POD + mmz, 2.12,
                 tex=t4[:, ::-1], emissive=0.26))
    s.add(Box(8.94, 0.50, 2.16, 8.98, 1.60, 2.20, color=tuple(LIME), emissive=0.30))

    # --- стеллаж-вертушка у входа
    s.add(cylinder(1.15, 1.65, 0.22, POD, 1.62, seg=18, color=tuple(SILVER_D)))
    s.add(cylinder(1.15, 1.65, 0.235, 0.30, 1.60, seg=18, color=tuple(LAV)))
    s.shadow(1.15, 1.65, 0.34, 0.34, 0.36)

    # --- барные стулья
    for i in range(3):
        yy = 1.35 + i * 0.55
        s.add(cylinder(0.96, yy, 0.16, POD + 0.60, 0.68, seg=14, color=tuple(PAPER)))
        s.add(cylinder(0.96, yy, 0.025, POD, POD + 0.60, seg=8, color=tuple(SILVER_D)))
        s.shadow(0.96, yy, 0.24, 0.24, 0.30)


# ------------------------------------------------------------------ свет
def scene_lights():
    L = [Light((4.5, -3.4, 4.6), color=(0.90, 0.93, 1.0), power=0.34, radius=11.0)]
    for x in (1.6, 4.5, 7.4):
        for y in (1.2, 3.2):
            L.append(Light((x, y, TOP - 0.06), color=(1.0, 0.975, 0.93),
                           power=0.40, radius=3.4, down=0.6))
    # гондола и лаунж
    L.append(Light((0.55, 2.2, 0.95), color=(0.86, 0.96, 0.34), power=0.30, radius=2.1))
    L.append(Light((0.35, 2.4, 2.20), color=(0.74, 0.70, 1.0), power=0.22, radius=2.2))
    # стена отделов и экран
    L.append(Light((2.4, 4.40, 2.55), color=(0.96, 0.98, 0.90), power=0.34, radius=3.6))
    L.append(Light((3.6, 3.60, 2.60), color=(1.0, 0.97, 0.90), power=0.26, radius=3.2))
    L.append(Light((6.4, 4.30, 2.55), color=(0.80, 1.0, 0.55), power=0.22, radius=2.8))
    # касса, будка, гача, зеркало
    L.append(Light((3.3, 2.25, 1.30), color=(0.94, 1.0, 0.72), power=0.26, radius=2.4))
    L.append(Light((8.35, 2.55, 2.30), color=(0.86, 0.98, 0.40), power=0.28, radius=2.4))
    L.append(Light((8.60, 1.9, 1.40), color=(0.86, 0.82, 1.0), power=0.26, radius=2.6))
    L.append(Light((8.70, 1.05, 1.60), color=(0.62, 0.92, 0.86), power=0.22, radius=2.0))
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
    "04-lounge":  dict(pos=(2.15, 0.70, 1.78), look=(2.05, 4.40, 1.20), fov=60),
    "05-cashier": dict(pos=(6.35, 4.35, 1.66), look=(2.05, 2.35, 1.22), fov=50),
    "06-booth":   dict(pos=(3.20, 0.35, 1.60), look=(8.35, 3.05, 1.15), fov=60),
}


def shot(name, pos, look, fov=52, w=1920, h=1080, exposure=0.90, bloom=0.14):
    s = build_scene()
    cam = Camera(pos, look, fov=fov, w=w, h=h)
    img = render(s.q, cam, bg=(0.105, 0.108, 0.118), sun=SUN,
                 glow_spots=s.glows, fog_col=(0.185, 0.188, 0.205),
                 fog_start=14.0, fog_amt=0.32, lights=scene_lights(),
                 occluders=s.occ, grain=0.004)
    img = tonemap(img, exposure=exposure, contrast=1.05, lift=0.018)
    img = post(img, bloom=bloom, bloom_thresh=0.80)
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
