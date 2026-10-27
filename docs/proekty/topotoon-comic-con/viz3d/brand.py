#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Бренд-графика Topotoon для визуализаций стенда.

Рисуется по бренд-киту 03_brend-kit.md: лайм #CCF024, фиолет #9060FC,
чёрный #151720, белый. Логотип — top◉toon, маскот — пламя-капля с глазами.

Всё генерится процедурно, никаких внешних картинок: обложки «вебтунов»
рисуются как цветные градиенты с силуэтом, поэтому на рендере читаются
как постеры, а не как пустые плитки.
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(BASE, "..", "..", "..", "ca-avtosalony", "02_prezentaciya", "fonts")
OUT = os.path.join(BASE, "tex")
os.makedirs(OUT, exist_ok=True)

LIME = (204, 240, 36)
VIOLET = (144, 96, 252)
BLACK = (21, 23, 32)
WHITE = (245, 245, 242)
PINK = (255, 92, 150)
TEAL = (64, 226, 214)


def font(weight="800", size=100):
    name = {"800": "Unbounded-800.ttf", "700": "Unbounded-700.ttf", "400": "Unbounded-400.ttf"}[weight]
    return ImageFont.truetype(os.path.join(FONTS, name), size)


def manrope(size=60, weight="700"):
    return ImageFont.truetype(os.path.join(FONTS, f"Manrope-{weight}.ttf"), size)


# ------------------------------------------------------------------ логотип
def _glyph(d, cx, cy, size, fg, bg):
    """«◉» логотипа: скруглённый квадрат с точкой внутри."""
    r = size * 0.26
    d.rounded_rectangle([cx - size / 2, cy - size / 2, cx + size / 2, cy + size / 2],
                        radius=r, fill=fg)
    rr = size * 0.17
    d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=bg)


def logo(width=1600, fg=BLACK, bg=LIME, transparent=True):
    """
    top◉toon в одну строку. Кегль подбирается так, чтобы надпись целиком
    уложилась в width — иначе логотип обрезается по краям.
    """
    probe = Image.new("RGBA", (10, 10))
    pd = ImageDraw.Draw(probe)
    size = 200
    for _ in range(24):                      # бинарный подбор кегля
        f = font("800", size)
        w1 = pd.textlength("top", font=f)
        w2 = pd.textlength("toon", font=f)
        glyph = size * 0.52
        gap = size * 0.13
        total = w1 + w2 + glyph + gap * 2
        if abs(total - width * 0.94) < width * 0.01:
            break
        size = max(8, int(size * (width * 0.94) / total))

    f = font("800", size)
    w1 = pd.textlength("top", font=f)
    w2 = pd.textlength("toon", font=f)
    glyph = size * 0.52
    gap = size * 0.13
    total = w1 + w2 + glyph + gap * 2
    H = int(size * 1.42)
    W = int(total + size * 0.30)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0) if transparent else bg + (255,))
    d = ImageDraw.Draw(im)
    cy = H / 2
    x = (W - total) / 2
    d.text((x, cy), "top", font=f, fill=fg, anchor="lm")
    x += w1 + gap
    _glyph(d, x + glyph / 2, cy, glyph, fg, (0, 0, 0, 0) if transparent else bg)
    x += glyph + gap
    d.text((x, cy), "toon", font=f, fill=fg, anchor="lm")

    if transparent:
        # точка внутри глифа должна быть прозрачной дыркой, а не чёрным кругом
        px = int(glyph * 0.17)
        hole = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        hd = ImageDraw.Draw(hole)
        gx = (W - total) / 2 + w1 + gap + glyph / 2
        hd.ellipse([gx - px, cy - px, gx + px, cy + px], fill=(255, 255, 255, 255))
        arr = np.asarray(im).copy()
        m = np.asarray(hole)[..., 3] > 0
        arr[m, 3] = 0
        im = Image.fromarray(arr, "RGBA")

    return im.crop(im.getbbox())


def logo_file(name, fg, bg, size=1400):
    im = logo(size, fg=fg, bg=bg)
    im.save(os.path.join(OUT, name))
    return im


# ------------------------------------------------------------------ маскот
def mascot(size=900, color=LIME, eye=BLACK, tongue=VIOLET):
    """Пламя-капля с глазами: широкая капля, острый шип влево-вверх, два глаза."""
    S = size
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, cy = S * 0.52, S * 0.56
    rx, ry = S * 0.42, S * 0.40
    # тело — капля
    body = []
    for i in range(180):
        a = 2 * np.pi * i / 180
        r = 1.0
        # сужение к верхнему левому углу — «хвост пламени»
        k = np.cos(a - np.pi * 1.15)
        r = 1.0 - 0.28 * max(0.0, k) ** 2
        body.append((cx + rx * r * np.cos(a), cy + ry * r * np.sin(a)))
    d.polygon(body, fill=color + (255,))
    # шип
    d.polygon([(cx - rx * 0.55, cy - ry * 0.75),
               (cx - rx * 1.62, cy - ry * 1.25),
               (cx - rx * 0.30, cy - ry * 1.02)], fill=color + (255,))
    # глаза
    for sx in (-1, 1):
        ex = cx + sx * rx * 0.36
        ey = cy + ry * 0.02
        ew, eh = rx * 0.20, ry * 0.30
        d.ellipse([ex - ew, ey - eh, ex + ew, ey + eh], fill=eye + (255,))
        d.ellipse([ex - ew * 0.42, ey - eh * 0.55, ex + ew * 0.42, ey + eh * 0.35],
                  fill=color + (255,))
    return im


def mascot_file(name, **kw):
    mascot(**kw).save(os.path.join(OUT, name))


# ------------------------------------------------------------------ обложки
COVER_PAIRS = [
    (VIOLET, PINK), (TEAL, VIOLET), (PINK, (255, 170, 90)),
    ((120, 200, 255), (150, 110, 250)), ((255, 210, 80), PINK),
    ((90, 240, 170), (40, 130, 200)), ((255, 120, 120), VIOLET),
    ((180, 150, 255), (60, 220, 240)),
]


def cover(w, h, seed, pair=None, label=True):
    """Обложка вебтуна: вертикальный градиент, силуэт, полоса с названием."""
    rng = np.random.default_rng(seed)
    a, b = pair or COVER_PAIRS[seed % len(COVER_PAIRS)]
    y = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
    top = np.array(a, np.float32) / 255
    bot = np.array(b, np.float32) / 255
    arr = top * (1 - y) + bot * y
    arr = np.repeat(arr, w, axis=1)

    # мягкое свечение сверху
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    g = np.exp(-(((xx - w * (0.3 + 0.4 * rng.random())) / (w * 0.45)) ** 2 +
                ((yy - h * 0.25) / (h * 0.35)) ** 2))
    arr = arr + g[..., None] * 0.28

    im = Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8), "RGB").convert("RGBA")
    d = ImageDraw.Draw(im)
    # силуэт персонажа: голова + плечи, чуть повёрнут
    hx = w * (0.35 + 0.3 * rng.random())
    hy = h * 0.52
    hr = w * 0.20
    d.ellipse([hx - hr, hy - hr * 1.15, hx + hr, hy + hr * 1.05], fill=(20, 20, 28, 235))
    d.ellipse([hx - hr * 0.72, hy - hr * 0.95, hx + hr * 0.72, hy + hr * 0.42],
              fill=(226, 226, 236, 235))          # лицо
    d.ellipse([hx - hr * 0.62, hy - hr * 1.30, hx + hr * 0.80, hy - hr * 0.30],
              fill=(28, 28, 36, 245))             # волосы
    d.chord([hx - hr * 2.1, hy + hr * 0.35, hx + hr * 2.1, hy + hr * 3.2], 180, 360,
            fill=(20, 20, 28, 235))               # плечи
    # блики-«молнии»
    for _ in range(int(rng.integers(2, 4))):
        sx, sy = rng.random() * w, rng.random() * h * 0.6
        d.polygon([(sx, sy), (sx + w * 0.10, sy + h * 0.02),
                   (sx + w * 0.04, sy + h * 0.05), (sx + w * 0.11, sy + h * 0.05),
                   (sx - w * 0.02, sy + h * 0.12), (sx + w * 0.02, sy + h * 0.06)],
                  fill=(255, 255, 255, 60))
    if label:
        # нижняя плашка с «названием»
        d.rectangle([0, h * 0.80, w, h], fill=(12, 12, 18, 225))
        d.rectangle([0, h * 0.80, w, h * 0.822], fill=LIME + (255,))
        f = manrope(int(h * 0.055), "800")
        d.text((w * 0.06, h * 0.885), ["ТВОЯ ИСТОРИЯ", "ГЛАВА 12", "НОВЫЙ СЕЗОН",
                                       "ТОП-10", "ПРОДОЛЖЕНИЕ"][seed % 5],
               font=f, fill=(240, 240, 245, 255))
        d.text((w * 0.06, h * 0.945), "top◉toon", font=manrope(int(h * 0.038), "700"),
               fill=LIME + (255,))
    return im


def cover_grid(w, h, cols, rows, seed=0, gap_ratio=0.012):
    """Сетка обложек одного размера — текстура для стены/витрины."""
    im = Image.new("RGBA", (w, h), (16, 16, 22, 255))
    gx = int(w * gap_ratio)
    gy = int(h * gap_ratio)
    cw = (w - gx * (cols + 1)) / cols
    ch = (h - gy * (rows + 1)) / rows
    for j in range(rows):
        for i in range(cols):
            c = cover(int(cw), int(ch), seed + j * cols + i)
            im.alpha_composite(c, (int(gx + i * (cw + gx)), int(gy + j * (ch + gy))))
    return im


# ------------------------------------------------------------------ билборды
def frieze(w=2048, h=256):
    """Световой короб по фронту: лайм, лого по центру, маскот справа."""
    im = Image.new("RGBA", (w, h), LIME + (255,))
    d = ImageDraw.Draw(im)
    lg = logo(int(w * 0.42), fg=BLACK, bg=LIME)
    im.alpha_composite(lg, (int(w * 0.29), int(h / 2 - lg.height / 2)))
    m = mascot(int(h * 0.92), color=BLACK, eye=LIME)
    im.alpha_composite(m, (int(w * 0.80), int(h * 0.04)))
    return im


def banner_back(w=3072, h=1024):
    """Задняя стена 9 × 3 м: три смысловые части, один бренд-язык."""
    im = Image.new("RGBA", (w, h), BLACK + (255,))
    d = ImageDraw.Draw(im)
    # верхняя лаймовая полоса
    d.rectangle([0, 0, w, h * 0.085], fill=LIME + (255,))
    lg = logo(int(w * 0.10), fg=BLACK, bg=LIME)
    im.alpha_composite(lg, (int(w * 0.012), int(h * 0.011)))

    # левая треть — ANIME
    d.text((w * 0.035, h * 0.145), "ANIME", font=font("800", int(h * 0.115)), fill=LIME + (255,))
    grid = cover_grid(int(w * 0.27), int(h * 0.56), 3, 2, seed=3)
    im.alpha_composite(grid, (int(w * 0.035), int(h * 0.30)))
    d.text((w * 0.035, h * 0.895), "СМОТРИ И ЧИТАЙ", font=manrope(int(h * 0.042), "700"),
           fill=(210, 210, 218, 255))

    # центр — маскот и главный слоган
    cx = w * 0.50
    m = mascot(int(h * 0.52), color=LIME, eye=BLACK)
    im.alpha_composite(m, (int(cx - m.width * 0.5), int(h * 0.16)))
    d.text((cx, h * 0.70), "МЫ ОТКРЫЛИСЬ!", font=font("800", int(h * 0.085)),
           fill=WHITE + (255,), anchor="mm")
    d.text((cx, h * 0.815), "ТВОЯ СЛЕДУЮЩАЯ ИСТОРИЯ", font=manrope(int(h * 0.048), "800"),
           fill=LIME + (255,), anchor="mm")

    # правая треть — гача-анонс
    d.rectangle([w * 0.70, h * 0.20, w * 0.975, h * 0.80], fill=VIOLET + (255,))
    d.text((w * 0.8375, h * 0.29), "ПОДАРКИ", font=font("800", int(h * 0.062)),
           fill=WHITE + (255,), anchor="mm")
    d.text((w * 0.8375, h * 0.385), "ВНУТРИ", font=font("800", int(h * 0.062)),
           fill=WHITE + (255,), anchor="mm")
    for k in range(3):
        cy = h * (0.53 + k * 0.085)
        d.ellipse([w * 0.765, cy - h * 0.028, w * 0.765 + h * 0.056, cy + h * 0.028],
                  fill=(255, 255, 255, 45), outline=WHITE + (200,), width=4)
        d.text((w * 0.785, cy), ["капсула", "жетон", "мерч"][k],
               font=manrope(int(h * 0.036), "600"), fill=WHITE + (230,), anchor="lm")
    d.text((w * 0.8375, h * 0.88), "TOPOTOON × COMIC CON", font=manrope(int(h * 0.032), "700"),
           fill=(190, 190, 200, 255), anchor="mm")
    return im


def banner_left(w=1792, h=1024):
    """Левая стена 5 × 3 м: витрина вебтунов + вертикальный брендинг."""
    im = Image.new("RGBA", (w, h), (18, 18, 24, 255))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w * 0.5, h], fill=(26, 26, 34, 255))
    # шапка
    d.rectangle([0, 0, w, h * 0.10], fill=LIME + (255,))
    lg = logo(int(w * 0.20), fg=BLACK, bg=LIME)
    im.alpha_composite(lg, (int(w * 0.02), int(h * 0.014)))
    d.text((w * 0.97, h * 0.048), "WEBTOONS", font=font("800", int(h * 0.048)),
           fill=BLACK + (255,), anchor="rm")

    # витрина: 4 × 3 обложки
    grid = cover_grid(int(w * 0.52), int(h * 0.76), 4, 3, seed=11)
    im.alpha_composite(grid, (int(w * 0.03), int(h * 0.135)))

    # правая часть — вертикальный слоган
    d.rectangle([w * 0.60, h * 0.13, w * 0.97, h * 0.97], fill=(12, 12, 17, 255))
    m = mascot(int(h * 0.36), color=VIOLET, eye=BLACK)
    im.alpha_composite(m, (int(w * 0.62), int(h * 0.16)))
    for i, line in enumerate(["ЧИТАЙ", "ДАЛЬШЕ", "В TOPOTOON"]):
        d.text((w * 0.785, h * (0.60 + i * 0.105)), line, font=font("800", int(h * 0.072)),
               fill=(LIME if i == 2 else WHITE) + (255,), anchor="mm")
    return im


def floor_art(w=2048, h=1152):
    """Напольная печать: маскот на лаймовом кляксе-брызге."""
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    rng = np.random.default_rng(7)
    d = ImageDraw.Draw(im)
    # лужа
    pts = []
    for i in range(140):
        a = 2 * np.pi * i / 140
        r = 1.0 + 0.10 * np.sin(a * 5) + 0.06 * np.sin(a * 11)
        pts.append((w * 0.5 + w * 0.36 * r * np.cos(a), h * 0.5 + h * 0.40 * r * np.sin(a)))
    d.polygon(pts, fill=LIME + (255,))
    # брызги
    for _ in range(260):
        a = rng.random() * 6.283
        rr = 0.40 + 0.20 * rng.random()
        x = w * 0.5 + w * rr * np.cos(a)
        y = h * 0.5 + h * rr * np.sin(a)
        r = (0.004 + 0.016 * rng.random() ** 2) * w
        d.ellipse([x - r, y - r, x + r, y + r], fill=LIME + (255,))
    # маскот чёрным по лайму
    mm = mascot(int(h * 0.92), color=BLACK, eye=LIME)
    im.alpha_composite(mm, (int(w * 0.5 - mm.width * 0.5), int(h * 0.5 - mm.height * 0.5)))
    return im


def screen_art(w=1600, h=900, seed=5):
    """Кадр на экране: постер-превью сервиса."""
    im = cover(w, h, seed, pair=((28, 34, 70), (150, 90, 240)), label=False)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, h * 0.08], fill=(8, 8, 12, 210))
    for i, c in enumerate([(255, 90, 90), (255, 200, 60), (90, 220, 120)]):
        d.ellipse([w * 0.015 + i * w * 0.028, h * 0.022,
                   w * 0.015 + i * w * 0.028 + h * 0.030, h * 0.058], fill=c + (255,))
    lg = logo(int(w * 0.20), fg=LIME, bg=(0, 0, 0, 0))
    im.alpha_composite(lg, (int(w * 0.04), int(h * 0.13)))
    d.text((w * 0.04, h * 0.72), "ТВОЯ СЛЕДУЮЩАЯ", font=font("800", int(h * 0.075)), fill=WHITE + (255,))
    d.text((w * 0.04, h * 0.815), "ИСТОРИЯ", font=font("800", int(h * 0.075)), fill=LIME + (255,))
    d.rectangle([w * 0.04, h * 0.925, w * 0.30, h * 0.955], fill=VIOLET + (255,))
    d.text((w * 0.05, h * 0.94), "СМОТРЕТЬ", font=manrope(int(h * 0.022), "800"),
           fill=WHITE + (255,), anchor="lm")
    return im


def silver_scratches(w=1024, h=1024, seed=3):
    """Текстура царапанного серебра: мелкие направленные штрихи + пятна."""
    rng = np.random.default_rng(seed)
    base = np.full((h, w), 0.62, np.float32)
    # крупные пятна
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    base += 0.03 * np.sin(xx / 90.0 + np.sin(yy / 140.0) * 2.0)
    im = Image.fromarray((np.clip(base, 0, 1) * 255).astype(np.uint8), "L")
    d = ImageDraw.Draw(im)
    for _ in range(9000):
        x, y = rng.random() * w, rng.random() * h
        ln = 2 + rng.random() * 26
        a = rng.random() * 0.5 - 0.25 + (0.0 if rng.random() > 0.15 else 1.57)
        c = int(np.clip(150 + rng.random() * 105, 0, 255))
        d.line([x, y, x + np.cos(a) * ln, y + np.sin(a) * ln], fill=c, width=1)
    im = im.filter(ImageFilter.GaussianBlur(0.4))
    arr = np.asarray(im, np.float32) / 255
    rgb = np.stack([arr * 0.98, arr * 0.99, arr * 1.01], -1)
    return rgb


# ------------------------------------------------------------------ сборка
def build_all():
    made = {}
    for name, fg, bg in (("logo_black.png", BLACK, LIME), ("logo_lime.png", LIME, BLACK),
                         ("logo_white.png", WHITE, BLACK)):
        logo_file(name, fg, bg)
        made[name] = 1
    mascot_file("mascot_lime.png", color=LIME, eye=BLACK)
    mascot_file("mascot_violet.png", color=VIOLET, eye=BLACK)
    mascot_file("mascot_black.png", color=BLACK, eye=LIME)
    frieze().save(os.path.join(OUT, "frieze.png"))
    banner_back().save(os.path.join(OUT, "banner_back.png"))
    banner_left().save(os.path.join(OUT, "banner_left.png"))
    floor_art().save(os.path.join(OUT, "floor_art.png"))
    screen_art().save(os.path.join(OUT, "screen.png"))
    cover_grid(900, 1200, 2, 3, seed=21).save(os.path.join(OUT, "covers_vert.png"))
    for i in range(4):
        cover(700, 900, seed=i).save(os.path.join(OUT, f"cover_{i}.png"))
    print("графика бренда собрана:", len(os.listdir(OUT)), "файлов")




def floor_texture(w=1800, h=1008):
    """
    Пол 9 × 5,04 м: тёмный винил, лаймовая клякса с маскотом у входа.
    Клякса занимает примерно треть площади — она акцент, а не заливка.
    """
    im = Image.new("RGB", (w, h), (13, 13, 17))
    d = ImageDraw.Draw(im)
    step = w / 15.0
    for i in range(16):
        d.line([(i * step, 0), (i * step, h)], fill=(19, 19, 24), width=2)
        d.line([(0, i * step * 0.56), (w, i * step * 0.56)], fill=(19, 19, 24), width=2)

    cx, cy = w * 0.50, h * 0.52
    # клякса
    pts = []
    for i in range(160):
        a = 2 * np.pi * i / 160
        r = 1.0 + 0.09 * np.sin(a * 5) + 0.045 * np.sin(a * 11 + 1.0)
        pts.append((cx + w * 0.215 * r * np.cos(a),
                    cy + h * 0.255 * r * np.sin(a)))
    d.polygon(pts, fill=(178, 210, 30))
    rng = np.random.default_rng(4)
    for _ in range(220):
        a = rng.random() * 6.283
        rr = 0.24 + 0.15 * rng.random()
        x = cx + w * rr * np.cos(a)
        y = cy + h * rr * np.sin(a)
        r = (0.0015 + 0.006 * rng.random() ** 2) * w
        d.ellipse([x - r, y - r, x + r, y + r], fill=(170, 202, 26))

    m = mascot(int(h * 0.60), color=BLACK, eye=(178, 210, 30))
    im.paste(m, (int(cx - m.width / 2), int(cy - m.height / 2)), m)

    lg = logo(int(w * 0.13), fg=(168, 198, 28), bg=BLACK, transparent=True)
    im.paste(lg, (int(cx - lg.width / 2), int(h * 0.055)), lg)
    return im


def chair_art(w=300, h=380, color=LIME):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([w * 0.05, h * 0.05, w * 0.95, h * 0.72], radius=w * 0.10,
                        fill=color + (255,))
    d.rectangle([w * 0.05, h * 0.30, w * 0.95, h * 0.40], fill=(30, 30, 38, 255))
    return im


def save_extra():
    floor_texture().save(os.path.join(OUT, "floor.png"), optimize=True)
    Image.fromarray((np.clip(silver_scratches(1024, 1024), 0, 1) * 255).astype(np.uint8)).save(
        os.path.join(OUT, "silver.png"), optimize=True)
    print("текстуры пола и серебра готовы")


if __name__ == "__main__":
    save_extra()


if __name__ == "__main__":
    build_all()
    save_extra()
