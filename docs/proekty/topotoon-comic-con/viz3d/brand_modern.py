#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Графика современной версии стенда Topotoon.

Тот же бренд — лайм #CCF024, фиолет #9060FC, лого top◉toon, маскот —
но подан сдержанно: светлые натуральные поверхности, крупная типографика,
много воздуха. Лайм работает как единственный акцент, а не как заливка.

Собирает:
    tex/mod_back.png    — задняя стена 9 × 3 м, подсвеченный текстиль
    tex/mod_left.png    — левая стена 5,04 × 3 м, панели с нишами
    tex/mod_floor.png   — пол 9 × 5,04 м, светлый микроцемент
    tex/mod_covers.png  — полоса обложек для ниш
    tex/mod_plinth.png  — узкая лаймовая линия-инкрустация
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import brand

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "tex")
LIME = brand.LIME
VIOLET = brand.VIOLET
INK = (24, 25, 28)

STONE = (238, 234, 226)
STONE_D = (216, 211, 202)
DARK = (26, 27, 31)


def noise(w, h, scale, seed, lo=0.0, hi=1.0):
    r = np.random.default_rng(seed)
    small = r.random((max(2, h // scale), max(2, w // scale))).astype(np.float32)
    im = Image.fromarray((small * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
    n = np.asarray(im, np.float32) / 255
    n = (n - n.min()) / max(n.max() - n.min(), 1e-6)
    return lo + n * (hi - lo)


def microcement(w, h, base=(206, 201, 192), seed=1, amp=0.030):
    """
    Светлый микроцемент: почти ровная поверхность, тонкое зерно и еле заметные
    облака. Пятнистость держим низкой — иначе пол читается как грязный бетон.
    """
    n1 = noise(w, h, max(4, w // 40), seed)          # очень мягкие облака
    n2 = noise(w, h, max(2, w // 220), seed + 1)     # мелкая крупа
    n3 = np.random.default_rng(seed + 2).standard_normal((h, w)).astype(np.float32) * 0.006
    tone = 1.0 + amp * (n1 - 0.5) * 2.0 + amp * 0.55 * (n2 - 0.5) * 2.0 + n3
    arr = np.array(base, np.float32)[None, None, :] * tone[..., None]
    return np.clip(arr / 255.0, 0, 1)


def tex_from_rgb(arr):
    return Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8), "RGB")


# ------------------------------------------------------------------ пол
def floor(w=1800, h=1008):
    """
    Светлый микроцемент, швы плит 3 × 3 м, лаймовая линия-инкрустация от входа
    к центру и небольшой логотип у порога. Всё остальное — воздух.
    """
    arr = microcement(w, h, (214, 209, 200), seed=11, amp=0.022)
    im = tex_from_rgb(arr)
    d = ImageDraw.Draw(im)

    # швы: 3 × 3 м
    for i in (1, 2):
        x = w * i / 3
        d.line([(x, 0), (x, h)], fill=(190, 185, 176), width=3)
    for j in (1,):
        y = h * j / 2
        d.line([(0, y), (w, y)], fill=(190, 185, 176), width=3)

    # лаймовая линия-инкрустация: от входа (низ) к центру
    lw = max(6, int(w * 0.006))
    d.line([(w * 0.5, h), (w * 0.5, h * 0.58)], fill=LIME, width=lw)
    d.line([(w * 0.5, h * 0.58), (w * 0.5, h * 0.42)], fill=(178, 210, 32), width=max(3, lw // 2))

    # лого у порога — мелко, как в бутике
    lg = brand.logo(int(w * 0.085), fg=(120, 122, 126), bg=(0, 0, 0, 0), transparent=True)
    im.paste(lg, (int(w * 0.5 - lg.width / 2), int(h * 0.885)), lg)
    return im


# ------------------------------------------------------------------ задняя стена
def back_wall(w=2700, h=900):
    """
    Подсвеченный текстиль 9 × 3 м: тёплый градиент, огромный логотип по центру,
    тонкая строка снизу, справа — деликатный силуэт маскота.
    """
    y = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
    top = np.array([246, 243, 236], np.float32) / 255
    bot = np.array([226, 221, 212], np.float32) / 255
    arr = top * (1 - y) + bot * y
    arr = np.repeat(arr, w, axis=1)
    im = tex_from_rgb(arr)
    d = ImageDraw.Draw(im)

    # тонкая лаймовая линия по низу — «подсветка плинтуса»
    d.rectangle([0, h * 0.972, w, h], fill=LIME)
    d.rectangle([0, 0, w, h * 0.012], fill=(214, 209, 200))

    lg = brand.logo(int(w * 0.30), fg=INK, bg=(0, 0, 0, 0), transparent=True)
    lg_top = int(h * 0.315)
    im.paste(lg, (int(w / 2 - lg.width / 2), lg_top), lg)

    f = brand.manrope(int(h * 0.038), "600")
    txt = "сервис аниме и вебтунов  ·  comic con игромир 2026"
    tw = d.textlength(txt, font=f)
    d.text((w / 2 - tw / 2, lg_top + lg.height + h * 0.055), txt, font=f, fill=(126, 128, 132))

    # силуэт маскота справа, очень деликатный
    m = brand.mascot(int(h * 0.60), color=(232, 227, 217), eye=(246, 243, 236))
    im.paste(m, (int(w * 0.885 - m.width / 2), int(h * 0.16)), m)

    # лаймовая вертикаль слева — единственный цветной акцент
    d.rectangle([w * 0.062, h * 0.12, w * 0.062 + max(5, w * 0.0022), h * 0.88], fill=LIME)
    return im


# ------------------------------------------------------------------ левая стена
def left_wall(w=1512, h=900):
    """
    Левая стена 5,04 × 3 м: панели тёплого камня с вертикальными швами,
    встроенные ниши с обложками, лаймовая полка-подсветка.
    """
    arr = microcement(w, h, (234, 229, 220), seed=21, amp=0.018)
    im = tex_from_rgb(arr)
    d = ImageDraw.Draw(im)

    # вертикальные швы панелей
    for i in range(1, 9):
        x = w * i / 9
        d.line([(x, 0), (x, h)], fill=(206, 200, 190), width=3)
        d.line([(x + 3, 0), (x + 3, h)], fill=(244, 240, 233), width=2)

    # ниша с обложками: рамка и подложка ровно под размер полосы
    nx0, nx1 = int(w * 0.062), int(w * 0.938)
    ny0, ny1 = int(h * 0.315), int(h * 0.695)
    d.rectangle([nx0 - 6, ny0 - 6, nx1 + 6, ny1 + 6], fill=(242, 238, 231))
    d.rectangle([nx0, ny0, nx1, ny1], fill=(26, 27, 31))
    covers = brand.cover_grid(nx1 - nx0, ny1 - ny0, 5, 2, seed=31, gap_ratio=0.008, label=False)
    im.paste(covers, (nx0, ny0))
    # лаймовая подсветка полки
    d.rectangle([nx0 - 6, ny1 + 6, nx1 + 6, ny1 + 6 + max(4, int(h * 0.006))], fill=LIME)

    f = brand.manrope(int(h * 0.030), "700")
    d.text((w * 0.062, h * 0.232), "WEBTOONS", font=f, fill=(94, 96, 100))
    f2 = brand.manrope(int(h * 0.023), "600")
    d.text((w * 0.062, ny1 + h * 0.055), "читать дальше в top◉toon", font=f2,
           fill=(124, 126, 130))
    return im


# ------------------------------------------------------------------ ниши и плашки
def covers_strip(w=1200, h=420):
    return brand.cover_grid(w, h, 5, 2, seed=41, gap_ratio=0.006)


def plinth(w=1200, h=60):
    im = Image.new("RGB", (w, h), LIME)
    return im


def build():
    floor().save(os.path.join(OUT, "mod_floor.png"), optimize=True)
    back_wall().save(os.path.join(OUT, "mod_back.png"), optimize=True)
    left_wall().save(os.path.join(OUT, "mod_left.png"), optimize=True)
    covers_strip().save(os.path.join(OUT, "mod_covers.png"), optimize=True)
    plinth().save(os.path.join(OUT, "mod_plinth.png"), optimize=True)
    frieze_modern().save(os.path.join(OUT, "mod_frieze.png"), optimize=True)
    print("графика современной версии готова:", 5, "файлов")


def frieze_modern(w=2048, h=248):
    """Фриз 9 × 0,5 м: светлая полоса, тонкий логотип по центру, лаймовая линия снизу."""
    im = Image.new("RGB", (w, h), (246, 244, 239))
    d = ImageDraw.Draw(im)
    d.rectangle([0, h * 0.90, w, h], fill=(206, 240, 40))
    lg = brand.logo(int(w * 0.30), fg=(26, 27, 31), bg=(0, 0, 0, 0), transparent=True)
    im.paste(lg, (int(w / 2 - lg.width / 2), int(h * 0.16)), lg)
    f = brand.manrope(int(h * 0.10), "600")
    txt = "comic con игромир 2026"
    tw = d.textlength(txt, font=f)
    d.text((w / 2 - tw / 2, h * 0.70), txt, font=f, fill=(132, 134, 138))
    return im


if __name__ == "__main__":
    build()
