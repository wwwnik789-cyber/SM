#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Графика стенда строго по презентации клиента
`00_topotoon-x-comic-con.pdf` (18 страниц).

Из презентации взято:
    · «японское комбини» — прилавок, полки с товаром, витрины, будка, гача;
    · комикс-язык: полутоновые точки, взрывные стикеры, толстые чёрные рамки,
      летящие линии;
    · палитра: лайм #CCF024, лаванда #A094F0, чёрный #15171F, бумажный #F2F0E4;
    · слоган «МЫ ОТКРЫЛИСЬ!» взрывным стикером над входом (стр. 4 и 6);
    · отделы «АНИМЕ» и «ВЕБТУНЫ» с лаймовыми шапками (стр. 8–10);
    · тележка для фото на фоне плакатов (стр. 8);
    · касса с фирменной водой, флаерами и скретч-картами (стр. 14);
    · гача-автоматы лайм и фиолет (стр. 15);
    · телефонная будка с зелёной трубкой (стр. 12);
    · неоновое зеркало и вывеска 物語の世界 (стр. 11);
    · пол: тёмная плитка и лаймовая клякса с маскотом (стр. 7).

Металл — царапанное серебро, по правке заказчика (не золото и не зеркало).
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import brand

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "tex")

LIME = (204, 240, 36)          # #CCF024
LIME_BR = (107, 240, 42)       # #6BF02A — яркие плашки презентации
LAV = (160, 148, 240)          # #A094F0
LAV_D = (128, 116, 214)
INK = (21, 23, 31)             # #15171F
PAPER = (242, 240, 228)        # #F2F0E4
WHITE = (255, 255, 255)
MAGENTA = (226, 74, 148)


# ------------------------------------------------------------------ узоры
def halftone(w, h, step=14, rmax=None, angle=0.0, color=(0, 0, 0)):
    """
    Полутоновые точки — главный приём презентации.
    Градиент по диагонали: слева точки крупные, справа исчезают.
    """
    rmax = rmax or step * 0.52
    im = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(im)
    ca, sa = np.cos(angle), np.sin(angle)
    for yy in range(-int(step), h + int(step), step):
        for xx in range(-int(step), w + int(step), step):
            u = (xx / w) * ca + (yy / h) * sa
            r = rmax * max(0.0, 1.0 - u * 1.15)
            if r < 0.6:
                continue
            px = xx + (yy // step % 2) * step * 0.5
            d.ellipse([px - r, yy - r, px + r, yy + r], fill=255)
    mask = im.filter(ImageFilter.GaussianBlur(0.4))
    layer = Image.new("RGB", (w, h), color)
    return layer, mask


def paste_halftone(im, box, color=INK, step=14, alpha=210):
    x0, y0, x1, y1 = box
    w, h = int(x1 - x0), int(y1 - y0)
    if w < 4 or h < 4:
        return
    layer, mask = halftone(w, h, step, color=color)
    mask = mask.point(lambda v: int(v * alpha / 255))
    im.paste(layer, (int(x0), int(y0)), mask)


def burst(w, h, spikes=16, color=LIME, inner=0.62, seed=3):
    """Взрывная звезда-стикер из презентации."""
    rng = np.random.default_rng(seed)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, cy = w / 2, h / 2
    rx, ry = w * 0.47, h * 0.47
    pts = []
    for i in range(spikes * 2):
        a = 2 * np.pi * i / (spikes * 2)
        k = 1.0 if i % 2 == 0 else inner + 0.06 * rng.random()
        pts.append((cx + rx * k * np.cos(a), cy + ry * k * np.sin(a)))
    d.polygon(pts, fill=color + (255,))
    return im


def sticker(im, box, text_lines, fill=LIME, angle=None, text_fill=INK, fs=None):
    """Плашка-стикер с текстом, как в презентации."""
    x0, y0, x1, y1 = [int(v) for v in box]
    w, h = x1 - x0, y1 - y0
    sp = burst(w, h, spikes=18, color=fill)
    im.paste(sp, (x0, y0), sp)
    d = ImageDraw.Draw(im)
    fs = fs or int(h * 0.17)
    # кегль ужимаем так, чтобы самая длинная строка влезла в «тело» звезды
    for _ in range(24):
        f = brand.font("800", fs)
        widest = max(d.textlength(t, font=f) for t in text_lines)
        if widest <= w * 0.62:
            break
        fs = int(fs * 0.9)
    f = brand.font("800", fs)
    total = len(text_lines) * fs * 1.05
    y = y0 + h / 2 - total / 2
    for line in text_lines:
        d.text((x0 + w / 2, y + fs * 0.55), line, font=f, fill=text_fill, anchor="mm")
        y += fs * 1.05


# ------------------------------------------------------------------ лого и маскот
def logo_on(w, fg=INK, bg=LIME):
    return brand.logo(w, fg=fg, bg=bg, transparent=False)


def logo_tr(w, fg=INK):
    return brand.logo(w, fg=fg, bg=INK, transparent=True)


# ------------------------------------------------------------------ фриз
def frieze(w=2400, h=200):
    """Фриз 9 × 0,6 м: лаймовый светокороб, лого по центру, маскот справа (стр. 6)."""
    im = Image.new("RGB", (w, h), LIME)
    d = ImageDraw.Draw(im)
    lg = logo_tr(int(w * 0.30), fg=INK)
    im.paste(lg, (int(w * 0.34 - lg.width / 2), int(h / 2 - lg.height / 2)), lg)
    m = brand.mascot(int(h * 0.78), color=INK, eye=LIME)
    im.paste(m, (int(w * 0.845), int(h * 0.11)), m)
    # лёгкая полоса-блик снизу, как у светокороба
    d.rectangle([0, h * 0.90, w, h], fill=(178, 212, 30))
    return im


# ------------------------------------------------------------------ стены
def back_anime(w=2200, h=750):
    """
    Задняя стена, отдел АНИМЕ (стр. 6, 10):
    чёрная панель, полутон, лаймовая шапка «top◉toon АНИМЕ», плакаты и маскот.
    """
    im = Image.new("RGB", (w, h), INK)
    d = ImageDraw.Draw(im)
    # полутон в правой части
    paste_halftone(im, (w * 0.52, 0, w, h), color=(60, 62, 74), step=16, alpha=170)
    # шапка
    d.rectangle([0, 0, w, h * 0.155], fill=LIME)
    lg = logo_tr(int(w * 0.17), fg=INK)
    im.paste(lg, (int(w * 0.03), int(h * 0.155 / 2 - lg.height / 2)), lg)
    f = brand.font("800", int(h * 0.085))
    d.text((w * 0.30, h * 0.077), "АНИМЕ", font=f, fill=INK, anchor="lm")
    # белая плашка справа в шапке — как в презентации
    d.rectangle([w * 0.62, h * 0.028, w * 0.97, h * 0.128], fill=PAPER)
    d.text((w * 0.795, h * 0.078), "ТЕЛЕКАНАЛ TOPOTOON", font=brand.manrope(int(h * 0.045), "800"),
           fill=INK, anchor="mm")
    # сетка плакатов
    grid = brand.cover_grid(int(w * 0.44), int(h * 0.62), 3, 2, seed=71, gap_ratio=0.012, label=False)
    im.paste(grid, (int(w * 0.035), int(h * 0.235)))
    # маскот на лаймовом круге
    cx, cy, r = int(w * 0.63), int(h * 0.60), int(h * 0.27)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=LIME)
    m = brand.mascot(int(r * 1.55), color=INK, eye=LIME)
    im.paste(m, (int(cx - m.width / 2), int(cy - m.height / 2)), m)
    # слоган
    sticker(im, (w * 0.755, h * 0.36, w * 0.975, h * 0.80),
            ["МЫ", "ОТКРЫЛИСЬ"], fill=LIME, fs=int(h * 0.085))
    # нижняя лаймовая кромка
    d.rectangle([0, h * 0.965, w, h], fill=LIME)
    return im


def back_posters(w=1800, h=750):
    """
    Задняя стена у тележки (стр. 8): плотная сетка плакатов с аниме-обложками,
    фиолетовые панели и полутон.
    """
    im = Image.new("RGB", (w, h), LAV)
    d = ImageDraw.Draw(im)
    paste_halftone(im, (0, 0, w * 0.30, h), color=INK, step=15, alpha=190)
    grid = brand.cover_grid(int(w * 0.82), int(h * 0.86), 4, 3, seed=81, gap_ratio=0.010, label=False)
    im.paste(grid, (int(w * 0.10), int(h * 0.07)))
    d.rectangle([0, 0, w, h * 0.035], fill=INK)
    d.rectangle([0, h * 0.965, w, h], fill=INK)
    return im


def left_webtoons(w=1400, h=850):
    """
    Левая стена, отдел ВЕБТУНЫ (стр. 9):
    лаймовая шапка «top◉toon ВЕБТУНЫ», планшеты на стойке, плакаты, полутон.
    """
    im = Image.new("RGB", (w, h), INK)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, h * 0.145], fill=LIME)
    lg = logo_tr(int(w * 0.26), fg=INK)
    im.paste(lg, (int(w * 0.03), int(h * 0.0725 - lg.height / 2)), lg)
    d.rectangle([w * 0.44, h * 0.028, w * 0.97, h * 0.117], fill=PAPER)
    d.rectangle([w * 0.44, h * 0.028, w * 0.97, h * 0.117], outline=INK, width=3)
    d.text((w * 0.705, h * 0.0725), "ВЕБТУНЫ", font=brand.font("800", int(h * 0.050)),
           fill=INK, anchor="mm")

    # плакатная сетка
    grid = brand.cover_grid(int(w * 0.58), int(h * 0.52), 3, 3, seed=91, gap_ratio=0.012, label=False)
    im.paste(grid, (int(w * 0.035), int(h * 0.19)))

    # полка с «планшетами»
    d.rectangle([w * 0.035, h * 0.735, w * 0.62, h * 0.815], fill=(46, 48, 60))
    for i in range(3):
        x = w * (0.055 + i * 0.19)
        d.rounded_rectangle([x, h * 0.745, x + w * 0.155, h * 0.805], radius=int(h * 0.012),
                            fill=(226, 228, 234))
        d.rectangle([x + w * 0.008, h * 0.752, x + w * 0.147, h * 0.798], fill=(30, 32, 42))
    d.rectangle([w * 0.035, h * 0.815, w * 0.62, h * 0.83], fill=LIME)

    # полутон и маскот справа
    paste_halftone(im, (w * 0.64, h * 0.16, w, h * 0.62), color=(70, 72, 86), step=14, alpha=150)
    m = brand.mascot(int(h * 0.30), color=LIME, eye=INK)
    im.paste(m, (int(w * 0.70), int(h * 0.28)), m)
    d.text((w * 0.81, h * 0.72), "ЧИТАЙ", font=brand.font("800", int(h * 0.062)), fill=WHITE, anchor="mm")
    d.text((w * 0.81, h * 0.80), "ДАЛЬШЕ", font=brand.font("800", int(h * 0.062)), fill=LIME, anchor="mm")
    d.text((w * 0.81, h * 0.88), "В TOPOTOON", font=brand.manrope(int(h * 0.038), "800"), fill=WHITE, anchor="mm")
    d.rectangle([0, h * 0.965, w, h], fill=LIME)
    return im


def back_closet(w=900, h=850):
    """Тёмный объём кладовой — служебная дверь, как в презентации."""
    im = Image.new("RGB", (w, h), (24, 25, 33))
    d = ImageDraw.Draw(im)
    d.rectangle([w * 0.08, h * 0.10, w * 0.92, h * 0.94], fill=(16, 17, 22))
    d.rectangle([w * 0.08, h * 0.10, w * 0.92, h * 0.135], fill=(60, 62, 74))
    d.rectangle([w * 0.80, h * 0.50, w * 0.845, h * 0.53], fill=(150, 154, 166))
    return im


# ------------------------------------------------------------------ мебель и товар
def shelf_strip(w=1400, h=320, seed=121):
    """
    Полка-гондола комбини: три ряда «товара» — обложки историй, белые упаковки
    и бутылки с брендингом. Лаймовые ценники по кромке.
    """
    im = Image.new("RGB", (w, h), (38, 40, 50))
    d = ImageDraw.Draw(im)
    rows = 3
    rh = h / rows
    for r in range(rows):
        y0 = r * rh
        d.rectangle([0, y0 + rh * 0.86, w, y0 + rh * 0.92], fill=LIME)
        # товар
        x = w * 0.02
        rng = np.random.default_rng(seed + r)
        while x < w * 0.97:
            kind = rng.integers(0, 3)
            cw = w * (0.030 + 0.016 * rng.random())
            if kind == 0:               # обложка истории
                c = brand.cover(int(cw), int(rh * 0.72), seed + r * 17 + int(x) % 97, label=False)
                im.paste(c, (int(x), int(y0 + rh * 0.10)))
            elif kind == 1:             # белая упаковка
                d.rectangle([x, y0 + rh * 0.22, x + cw * 0.8, y0 + rh * 0.84], fill=PAPER)
                d.rectangle([x, y0 + rh * 0.22, x + cw * 0.8, y0 + rh * 0.30], fill=LIME)
            else:                       # бутылка
                d.rounded_rectangle([x, y0 + rh * 0.26, x + cw * 0.5, y0 + rh * 0.84],
                                    radius=int(cw * 0.18), fill=(236, 240, 244))
                d.rectangle([x, y0 + rh * 0.44, x + cw * 0.5, y0 + rh * 0.62], fill=LIME)
            x += cw + w * 0.006
    return im


def counter_front(w=1400, h=340):
    """Передняя панель кассы: лайм, лого, фиолетовый диагональный акцент (стр. 14)."""
    im = Image.new("RGB", (w, h), LIME)
    d = ImageDraw.Draw(im)
    d.polygon([(w * 0.72, 0), (w, 0), (w, h), (w * 0.60, h)], fill=LAV)
    d.polygon([(w * 0.70, 0), (w * 0.78, 0), (w * 0.66, h), (w * 0.58, h)], fill=INK)
    lg = logo_tr(int(w * 0.30), fg=INK)
    im.paste(lg, (int(w * 0.06), int(h / 2 - lg.height / 2)), lg)
    d.rectangle([0, h * 0.88, w, h], fill=(178, 212, 30))
    return im


def gacha_front(w=380, h=760, color=LIME):
    """Передняя панель гача-автомата с капсулами (стр. 15)."""
    im = Image.new("RGB", (w, h), color)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, h * 0.10], fill=PAPER)
    d.text((w / 2, h * 0.05), "top◉toon", font=brand.manrope(int(h * 0.030), "800"),
           fill=INK, anchor="mm")
    # окно с капсулами
    d.rounded_rectangle([w * 0.10, h * 0.14, w * 0.90, h * 0.66], radius=int(w * 0.10),
                        fill=(248, 250, 252))
    cols = [LIME, LAV, MAGENTA, (120, 220, 240), (255, 200, 90)]
    rng = np.random.default_rng(5)
    for i in range(26):
        cx = w * (0.20 + 0.60 * rng.random())
        cy = h * (0.20 + 0.40 * rng.random())
        r = w * 0.075
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=cols[i % len(cols)])
        d.ellipse([cx - r * 0.5, cy - r * 0.75, cx + r * 0.5, cy - r * 0.05], fill=(255, 255, 255, 120))
    # ручка и лоток
    d.ellipse([w * 0.34, h * 0.70, w * 0.66, h * 0.78], fill=(230, 232, 238), outline=INK, width=3)
    d.rectangle([w * 0.28, h * 0.82, w * 0.72, h * 0.90], fill=(30, 32, 42))
    d.text((w / 2, h * 0.955), "ПОДАРКИ ВНУТРИ", font=brand.manrope(int(h * 0.026), "800"),
           fill=INK, anchor="mm")
    return im


def phone_sign(w=520, h=120):
    im = Image.new("RGB", (w, h), LIME)
    d = ImageDraw.Draw(im)
    lg = logo_tr(int(w * 0.62), fg=INK)
    im.paste(lg, (int(w / 2 - lg.width / 2), int(h / 2 - lg.height / 2)), lg)
    return im


def neon_mirror(w=760, h=1000):
    """Зеркало с неоновой вывеской 物語の世界 (стр. 11)."""
    y = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
    arr = np.array([40, 42, 54], np.float32) * (1 - 0.45 * y) + np.array([70, 66, 96], np.float32) * y
    arr = np.repeat(arr, w, axis=1) / 255
    im = Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    # световая полоса — отражение
    d.rectangle([w * 0.13, 0, w * 0.19, h], fill=(58, 60, 76))
    # неоновая рамка
    for k in range(3):
        d.rectangle([w * 0.06 - k * 2, h * 0.06 - k * 2, w * 0.94 + k * 2, h * 0.94 + k * 2],
                    outline=(120, 240, 200), width=2)
    d.rectangle([w * 0.16, h * 0.14, w * 0.84, h * 0.31], fill=(96, 60, 150))
    d.text((w * 0.50, h * 0.196), "МИР ИСТОРИЙ", font=brand.font("800", int(h * 0.048)),
           fill=(238, 250, 245), anchor="mm")
    d.text((w * 0.50, h * 0.265), "MONOGATARI NO SEKAI", font=brand.manrope(int(h * 0.026), "600"),
           fill=(206, 200, 246), anchor="mm")
    d.text((w * 0.50, h * 0.80), "СЕЛФИ", font=brand.font("800", int(h * 0.040)),
           fill=LIME, anchor="mm")
    return im


def screen(w=1600, h=900, seed=77):
    """Экран «ТЕЛЕКАНАЛ TOPOTOON» 16:9 (стр. 9)."""
    im = Image.new("RGB", (w, h), INK)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, int(h * 0.115)], fill=LIME)
    lg = logo_tr(int(w * 0.20), fg=INK)
    im.paste(lg, (int(w * 0.03), int(h * 0.0575 - lg.height / 2)), lg)
    d.rectangle([w * 0.34, h * 0.026, w * 0.97, h * 0.092], fill=PAPER)
    d.text((w * 0.655, h * 0.059), "ТЕЛЕКАНАЛ TOPOTOON", font=brand.font("800", int(h * 0.040)),
           fill=INK, anchor="mm")
    grid = brand.cover_grid(int(w * 0.50), int(h * 0.66), 3, 2, seed=seed, gap_ratio=0.014, label=False)
    im.paste(grid, (int(w * 0.035), int(h * 0.20)))
    paste_halftone(im, (w * 0.58, h * 0.14, w, h * 0.86), color=(64, 66, 80), step=13, alpha=130)
    disc = Image.new("RGBA", (int(h * 0.50), int(h * 0.50)), (0, 0, 0, 0))
    dd = ImageDraw.Draw(disc)
    dd.ellipse([0, 0, disc.width - 1, disc.height - 1], fill=LIME + (255,))
    im.paste(disc, (int(w * 0.615), int(h * 0.16)), disc)
    m = brand.mascot(int(h * 0.36), color=INK, eye=LIME)
    im.paste(m, (int(w * 0.665), int(h * 0.215)), m)
    sticker(im, (int(w * 0.585), int(h * 0.60), int(w * 0.925), int(h * 0.845)),
            ["СМОТРИ", "ПРЯМО СЕЙЧАС"], fill=LIME_BR, text_fill=INK)
    return im


def ext_wall(w=1700, h=996, cols=5, rows=2, seed=64):
    """Наружная стена: лого, поле постеров, стикер «МЫ ОТКРЫЛИСЬ» (стр. 3–6)."""
    im = Image.new("RGB", (w, h), INK)
    d = ImageDraw.Draw(im)
    paste_halftone(im, (w * 0.60, 0, w, h * 0.42), color=(58, 60, 74), step=15, alpha=150)
    lg = logo_tr(int(w * 0.46), fg=LIME)
    im.paste(lg, (int(w * 0.05), int(h * 0.075)), lg)
    d.rectangle([0, h * 0.245, w * 0.52, h * 0.265], fill=LIME)

    grid = brand.cover_grid(int(w * 0.90), int(h * 0.46), cols, rows, seed=seed,
                            gap_ratio=0.014, label=False)
    im.paste(grid, (int(w * 0.05), int(h * 0.35)))
    sticker(im, (int(w * 0.62), int(h * 0.27), int(w * 0.95), int(h * 0.47)),
            ["МЫ", "ОТКРЫЛИСЬ"], fill=LIME, text_fill=INK)
    d.rectangle([0, h * 0.955, w, h], fill=LIME)
    return im


# ------------------------------------------------------------------ пол
def floor(w=1800, h=1008):
    """Тёмная плитка 600×600 и лаймовая клякса с маскотом (стр. 7)."""
    im = Image.new("RGB", (w, h), (26, 28, 36))
    d = ImageDraw.Draw(im)
    step = w / 15
    for i in range(17):
        d.line([(i * step, 0), (i * step, h)], fill=(34, 36, 46), width=2)
        d.line([(0, i * step * 0.56), (w, i * step * 0.56)], fill=(34, 36, 46), width=2)

    # клякса ~1,2 м радиусом — в PDF она локальное пятно, а не заливка пола
    cx, cy = w * 0.44, h * 0.56
    RAD = w * 0.135
    pts = []
    for i in range(180):
        a = 2 * np.pi * i / 180
        r = 1.0 + 0.10 * np.sin(a * 5) + 0.045 * np.sin(a * 11 + 1.0)
        pts.append((cx + RAD * r * np.cos(a), cy + RAD * r * np.sin(a)))
    d.polygon(pts, fill=LIME)
    rng = np.random.default_rng(7)
    for _ in range(240):
        a = rng.random() * 6.283
        rr = (0.9 + 0.75 * rng.random()) * RAD
        x = cx + rr * np.cos(a)
        y = cy + rr * np.sin(a)
        r = (0.0008 + 0.0035 * rng.random() ** 2) * w
        d.ellipse([x - r, y - r, x + r, y + r], fill=LIME)

    m = brand.mascot(int(h * 0.30), color=INK, eye=LIME)
    im.paste(m, (int(cx - m.width / 2), int(cy - m.height / 2)), m)
    lg = logo_tr(int(w * 0.13), fg=LIME)
    im.paste(lg, (int(w * 0.5 - lg.width / 2), int(h * 0.06)), lg)
    return im


def cart_posters(w=900, h=700, seed=101):
    """Плакатный задник фотозоны с тележкой (стр. 8)."""
    im = Image.new("RGB", (w, h), INK)
    grid = brand.cover_grid(w, h, 3, 2, seed=seed, gap_ratio=0.010, label=False)
    im.paste(grid, (0, 0))
    return im


# ------------------------------------------------------------------ сборка
def build():
    frieze().save(os.path.join(OUT, "cli_frieze.png"), optimize=True)
    back_anime().save(os.path.join(OUT, "cli_back_anime.png"), optimize=True)
    back_posters().save(os.path.join(OUT, "cli_back_posters.png"), optimize=True)
    left_webtoons().save(os.path.join(OUT, "cli_left_webtoons.png"), optimize=True)
    back_closet().save(os.path.join(OUT, "cli_closet.png"), optimize=True)
    # 1400×420 ≈ пропорции фронта гондолы 2,45 × 0,73
    shelf_strip(1400, 420).save(os.path.join(OUT, "cli_shelf.png"), optimize=True)
    # 1400×620 ≈ пропорции стойки 2,10 × 0,88 — без растяжения на рендере
    counter_front(1400, 620).save(os.path.join(OUT, "cli_counter.png"), optimize=True)
    gacha_front(color=LIME).save(os.path.join(OUT, "cli_gacha_lime.png"), optimize=True)
    gacha_front(color=LAV).save(os.path.join(OUT, "cli_gacha_lav.png"), optimize=True)
    phone_sign().save(os.path.join(OUT, "cli_phone.png"), optimize=True)
    neon_mirror().save(os.path.join(OUT, "cli_mirror.png"), optimize=True)
    screen().save(os.path.join(OUT, "cli_screen.png"), optimize=True)
    ext_wall(1700, 996, 5, 2).save(os.path.join(OUT, "cli_ext_left.png"), optimize=True)
    ext_wall(2400, 800, 7, 2, seed=87).save(os.path.join(OUT, "cli_ext_back.png"), optimize=True)
    floor().save(os.path.join(OUT, "cli_floor.png"), optimize=True)
    cart_posters().save(os.path.join(OUT, "cli_cart_back.png"), optimize=True)
    print("графика по презентации клиента:", len([f for f in os.listdir(OUT) if f.startswith("cli_")]),
          "файлов")


if __name__ == "__main__":
    build()
