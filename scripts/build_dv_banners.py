#!/usr/bin/env python3
"""
Сборка серии баннеров продюсерского центра «ДВ ПРОДАКШЕН».

Сцена (подиум, красная дорожка, эпатажные фигуры по краям) генерируется
отдельно и лежит в visualizations/dv-production/work/plate_*.jpg.
Скрипт накладывает на неё типографику точным шрифтом (без AI-артефактов)
и собирает готовые макеты в высоком разрешении:

    dv-production-banner-square.jpg   1:1  — главный баннер серии
    dv-production-casting-kino.jpg    3:5  — кастинг на пробы в кино (4–18)
    dv-production-casting-pokaz.jpg   2:3  — кастинг на модный показ

Если рядом с макетом положить `qr.png` (или .svg, сконвертированный в png),
он автоматически встанет вместо плашки-заглушки. Сгенерировать QR:

    /tmp/venv/bin/python scripts/make_qr.py "https://ссылка-на-форму"

Запуск:
    /tmp/venv/bin/python scripts/build_dv_banners.py

Требования: pillow, numpy.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "visualizations/dv-production/work"
OUT_DIR = ROOT / "visualizations/dv-production"
FONT_DIR = ROOT / "assets/fonts"
LOGO = ROOT / "assets/brand/dv-production-monogram.png"

# ── палитра ────────────────────────────────────────────────────────────────
CREAM = (255, 244, 231)
CHAMPAGNE = (247, 224, 191)
PLUM = (74, 24, 42)

GOLD_STOPS = [
    (0.00, (255, 249, 230)),
    (0.16, (247, 223, 170)),
    (0.34, (226, 181, 108)),
    (0.52, (176, 122, 44)),
    (0.66, (233, 192, 124)),
    (0.80, (255, 242, 208)),
    (0.90, (212, 163, 86)),
    (1.00, (140, 90, 28)),
]

DEEP_GOLD_STOPS = [
    (0.00, (196, 143, 70)),
    (0.22, (158, 102, 35)),
    (0.48, (120, 72, 20)),
    (0.70, (166, 110, 42)),
    (0.86, (205, 154, 80)),
    (1.00, (104, 60, 15)),
]

PRATA = FONT_DIR / "Prata-Regular.ttf"
MONT_VF = FONT_DIR / "Montserrat-VF.ttf"


# ── шрифты / текст ─────────────────────────────────────────────────────────
def montserrat(size: int, weight: str = "Medium") -> ImageFont.FreeTypeFont:
    fnt = ImageFont.truetype(str(MONT_VF), size)
    fnt.set_variation_by_name(weight)
    return fnt


def prata(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(PRATA), size)


def tracked_width(text: str, fnt: ImageFont.FreeTypeFont, tracking: float) -> float:
    if not text:
        return 0.0
    return sum(fnt.getlength(ch) for ch in text) + tracking * (len(text) - 1)


def draw_tracked(draw: ImageDraw.ImageDraw, xy, text, fnt, tracking, fill):
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += fnt.getlength(ch) + tracking


def tracked_mask(text, fnt, tracking, pad=40) -> Image.Image:
    w = tracked_width(text, fnt, tracking)
    asc, desc = fnt.getmetrics()
    img = Image.new("L", (int(w) + pad * 2, asc + desc + pad * 2), 0)
    draw_tracked(ImageDraw.Draw(img), (pad, pad), text, fnt, tracking, 255)
    return img


def gold_gradient(w: int, h: int, stops_src=GOLD_STOPS) -> Image.Image:
    """Вертикальный металлический градиент + диагональный блик."""
    ys = np.linspace(0, 1, h, dtype=np.float32)
    stops = np.array([s[0] for s in stops_src], dtype=np.float32)
    cols = np.array([s[1] for s in stops_src], dtype=np.float32)
    band = np.stack([np.interp(ys, stops, cols[:, c]) for c in range(3)], axis=1)
    band = np.repeat(band[:, None, :], w, axis=1)

    xs = np.linspace(0, 1, w, dtype=np.float32)[None, :]
    yy = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    sweep = np.exp(-((xs * 0.9 + yy * 0.9 - 0.55) ** 2) / (2 * 0.16 ** 2))
    band = np.clip(band * (1 + 0.22 * sweep[..., None]), 0, 255)
    return Image.fromarray(band.astype(np.uint8), "RGB")


def place_gold_text(base, center_x, top, text, fnt, tracking, *,
                    shadow=True, bevel=True, glow=0.0, stops_src=GOLD_STOPS):
    m = tracked_mask(text, fnt, tracking)
    mw, mh = m.size
    left = int(center_x - mw / 2)
    top_ = int(top - 40)  # компенсируем pad

    if glow:
        halo = m.filter(ImageFilter.GaussianBlur(30)).point(lambda p: int(p * glow))
        layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
        layer.paste(Image.new("RGBA", m.size, (255, 224, 176, 255)), (left, top_), halo)
        base.alpha_composite(layer)

    if shadow:
        sh = m.filter(ImageFilter.GaussianBlur(24)).point(lambda p: int(p * 0.40))
        layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
        layer.paste(Image.new("RGBA", m.size, (*PLUM, 255)), (left, top_ + 16), sh)
        base.alpha_composite(layer)

    grad = gold_gradient(mw, mh, stops_src).convert("RGBA")
    base.paste(grad, (left, top_), m)

    if bevel:
        hi = m.filter(ImageFilter.GaussianBlur(4))
        layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
        layer.paste(Image.new("RGBA", m.size, (255, 252, 240, 130)), (left, top_ - 7), hi)
        base.alpha_composite(layer)

        lo = m.filter(ImageFilter.GaussianBlur(5)).point(lambda p: int(p * 0.5))
        layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
        layer.paste(Image.new("RGBA", m.size, (120, 70, 20, 255)), (left, top_ + 8), lo)
        base.alpha_composite(layer)
        base.paste(grad, (left, top_), m)

    return mw, mh


def text_line(layer, center_x, top, text, fnt, tracking, fill, alpha=255, shadow=0):
    w = tracked_width(text, fnt, tracking)
    x = center_x - w / 2
    if shadow:
        sh = Image.new("RGBA", layer.size, (0, 0, 0, 0))
        draw_tracked(ImageDraw.Draw(sh), (x, top + 6), text, fnt, tracking, (*PLUM, shadow))
        layer.alpha_composite(sh.filter(ImageFilter.GaussianBlur(7)))
    draw_tracked(ImageDraw.Draw(layer), (x, top), text, fnt, tracking, (*fill, alpha))
    return w


def line_metrics(fnt, text, tracking):
    """Возвращает (top, bottom) видимых глифов относительно anchor='la'."""
    m = tracked_mask(text, fnt, tracking)
    bbox = m.point(lambda p: 255 if p > 40 else 0).getbbox()
    return bbox[1] - 40, bbox[3] - 40


def diamond(draw, cx, cy, r, fill):
    draw.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], fill=fill)


def ornament(draw, cx, cy, half_w, color):
    draw.line([(cx - half_w, cy), (cx - half_w + 30, cy)], fill=color, width=3)
    draw.line([(cx + half_w - 30, cy), (cx + half_w, cy)], fill=color, width=3)
    diamond(draw, cx, cy, 12, color)
    diamond(draw, cx - half_w - 24, cy, 5, color)
    diamond(draw, cx + half_w + 24, cy, 5, color)


def fit_font(make_font, text, max_width, start, tracking_em):
    size = start
    while size > 12:
        fnt = make_font(size)
        if tracked_width(text, fnt, size * tracking_em) <= max_width:
            return fnt
        size -= 2
    return make_font(12)


def grade(base: Image.Image, strength: float = 1.0) -> None:
    """Виньетка + мягкий розовый подтон, чтобы золото читалось на светлом фоне."""
    w, h = base.size
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    cx, cy = w / 2, h * 0.46
    r = np.sqrt(((x - cx) / (w * 0.80)) ** 2 + ((y - cy) / (h * 0.80)) ** 2)
    mask = np.clip((r - 0.58) / 0.55, 0, 1) ** 1.5
    arr = np.asarray(base.convert("RGB")).astype(np.float32)
    arr = arr * (1 - 0.22 * mask[..., None]) + np.array([120, 48, 70], np.float32) * (0.22 * mask[..., None])

    veil = np.exp(-(((x - w / 2) / (w * 0.44)) ** 2 + ((y - h * 0.30) / (h * 0.36)) ** 2))
    arr = arr * (1 - 0.08 * veil[..., None]) + np.array([160, 88, 104], np.float32) * (0.08 * veil[..., None])
    base.paste(Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB"))


def prepare_plate(path: Path, size: tuple[int, int], contrast: float = 1.0) -> Image.Image:
    plate = Image.open(path).convert("RGB")
    base = plate.resize(size, Image.LANCZOS)
    base = base.filter(ImageFilter.UnsharpMask(radius=2.2, percent=80, threshold=2))
    grade(base)
    return base


def frame(canvas: Image.Image, inset: int = 54) -> None:
    """Тонкая золотая рамка по краю макета."""
    draw = ImageDraw.Draw(canvas, "RGBA")
    w, h = canvas.size
    draw.rectangle([inset, inset, w - inset, h - inset],
                   outline=(*CHAMPAGNE, 80), width=max(2, w // 1000))
    draw.rectangle([inset + 24, inset + 24, w - inset - 24, h - inset - 24],
                   outline=(*CHAMPAGNE, 34), width=1)


def logo_lockup(canvas: Image.Image, x: int, y: int, mark_h: int,
                word_alpha: int = 252, word_track: float = 0.38) -> int:
    """Монограмма + подпись PRODUCTION. Возвращает ширину блока."""
    mark = Image.open(LOGO).convert("RGBA")
    mark_w = int(mark_h * mark.size[0] / mark.size[1])
    mark = mark.resize((mark_w, mark_h), Image.LANCZOS)

    sh = mark.split()[3].filter(ImageFilter.GaussianBlur(12)).point(lambda p: int(p * 0.32))
    canvas.paste(Image.new("RGBA", mark.size, (*PLUM, 255)), (x, y + 12), sh)
    canvas.paste(mark, (x, y), mark)

    word = "PRODUCTION"
    size = max(18, int(mark_h * 0.20))
    wf = montserrat(size, "Medium")
    tracking = size * word_track
    while tracked_width(word, wf, tracking) > mark_w * 0.99 and wf.size > 16:
        wf = montserrat(wf.size - 1, "Medium")
        tracking = wf.size * word_track
    text_line(canvas, x + mark_w / 2, y + mark_h + 30, word, wf, tracking,
              (255, 247, 236), word_alpha, shadow=150)
    return mark_w


def qr_block(canvas: Image.Image, center_x: int, center_y: int, side: int,
             src: Path | None = None, caption: str = "ССЫЛКА НА ФОРМУ") -> None:
    """Плашка под QR-код: либо готовый qr.png, либо аккуратная заглушка."""
    x0, y0 = int(center_x - side / 2), int(center_y - side / 2)

    halo = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(halo).rounded_rectangle(
        [x0 - 6, y0 + 10, x0 + side + 6, y0 + side + 26],
        radius=int(side * 0.08), fill=(*PLUM, 55))
    canvas.alpha_composite(halo.filter(ImageFilter.GaussianBlur(18)))

    draw = ImageDraw.Draw(canvas, "RGBA")
    draw.rounded_rectangle([x0, y0, x0 + side, y0 + side],
                           radius=int(side * 0.075), fill=(255, 252, 246, 242),
                           outline=(*CHAMPAGNE, 220), width=3)

    if src and src.exists():
        qr = Image.open(src).convert("RGB")
        pad = int(side * 0.10)
        qr = qr.resize((side - 2 * pad, side - 2 * pad), Image.LANCZOS)
        canvas.paste(qr, (x0 + pad, y0 + pad))
    else:
        f1 = prata(int(side * 0.20))
        f2 = montserrat(int(side * 0.045), "Medium")
        text_line(draw if False else canvas, center_x, y0 + side * 0.30, "QR",
                  f1, 4, (198, 150, 84), 235)
        text_line(canvas, center_x, y0 + side * 0.58, "МЕСТО ДЛЯ QR-КОДА",
                  f2, f2.size * 0.32, (150, 104, 72), 220)
        text_line(canvas, center_x, y0 + side * 0.70, caption,
                  f2, f2.size * 0.32, (176, 132, 96), 200)


def save(canvas: Image.Image, name: str) -> Path:
    out = OUT_DIR / name
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(out, quality=95, subsampling=0)
    print(f"✓ {out.name}  {canvas.size[0]}×{canvas.size[1]}")
    return out


def save_preview(src: Path, width: int = 1100) -> None:
    im = Image.open(src)
    w = min(width, im.size[0])
    im = im.resize((w, int(w * im.size[1] / im.size[0])), Image.LANCZOS)
    im.save(OUT_DIR / ("preview-" + src.name), quality=93, subsampling=0)


# ── 1. главный баннер 1:1 ──────────────────────────────────────────────────
def build_square() -> Path:
    SIZE = 3072
    MARGIN = 150
    base = prepare_plate(WORK / "plate-square.jpg", (SIZE, SIZE))
    canvas = base.convert("RGBA")
    frame(canvas)
    draw = ImageDraw.Draw(canvas, "RGBA")
    gold = (*CHAMPAGNE, 235)

    # логотип в верхнем левом углу
    logo_lockup(canvas, MARGIN, MARGIN, 228)

    cx = SIZE // 2
    lf = montserrat(58, "Medium")
    text_line(canvas, cx, 430, "ПРОДЮСЕРСКИЙ ЦЕНТР", lf, lf.size * 0.44, PLUM, 205)
    ornament(draw, cx, 566, 300, (*CHAMPAGNE, 160))

    tf = fit_font(prata, "ДВ ПРОДАКШЕН", SIZE - 2 * 250, 300, 0.045)
    place_gold_text(canvas, cx, 596, "ДВ ПРОДАКШЕН", tf, tf.size * 0.045, glow=0.18)

    sf = montserrat(62, "Medium")
    text_line(canvas, cx, 1008, "АКТЁРСКО-МОДЕЛЬНАЯ СТУДИЯ", sf, sf.size * 0.30, PLUM, 215)

    # блоки кастингов слева и справа
    panel_w = 720
    panels = [
        (MARGIN - 30, ["КАСТИНГ НА", "ПРОБЫ В КИНО"], "4–18 ЛЕТ"),
        (SIZE - MARGIN + 30 - panel_w, ["КАСТИНГ В", "РЕАЛИТИ-ШОУ"], "18–45 ЛЕТ"),
    ]

    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay, "RGBA")

    f = fit_font(lambda s: montserrat(s, "SemiBold"), "ПРОБЫ В КИНО", panel_w - 140, 50, 0.10)
    tr = f.size * 0.10
    line_h = max(f.getbbox(l)[3] - f.getbbox(l)[1] for l in ["КАСТИНГ НА", "ПРОБЫ В КИНО"])
    gap = 28
    af = prata(60)
    ages_h = af.getbbox("4–18 ЛЕТ")[3] - af.getbbox("4–18 ЛЕТ")[1]
    content_h = 2 * line_h + gap + 48 + 2 + 40 + ages_h
    panel_h = int(content_h + 132)
    panel_y = 1452 - panel_h

    for px, lines, ages in panels:
        odraw.rectangle([px, panel_y, px + panel_w, panel_y + panel_h],
                        fill=(255, 250, 244, 46), outline=(*CHAMPAGNE, 205), width=3)
        for dx, dy in [(0, 0), (panel_w, 0), (0, panel_h), (panel_w, panel_h)]:
            diamond(odraw, px + dx, panel_y + dy, 8, (*CHAMPAGNE, 225))

        y = panel_y + 58
        for i, ln in enumerate(lines):
            w = tracked_width(ln, f, tr)
            draw_tracked(odraw, (px + (panel_w - w) / 2, y + i * (line_h + gap)),
                         ln, f, tr, (*PLUM, 240))

        divider_y = y + 2 * line_h + gap + 46
        odraw.line([(px + 180, divider_y), (px + panel_w - 180, divider_y)],
                   fill=(*CHAMPAGNE, 190), width=2)
        diamond(odraw, px + 180 - 16, divider_y, 4, (*CHAMPAGNE, 215))
        diamond(odraw, px + panel_w - 180 + 16, divider_y, 4, (*CHAMPAGNE, 215))

    canvas.alpha_composite(overlay)

    for px, lines, ages in panels:
        place_gold_text(canvas, px + panel_w // 2, divider_y + 38, ages, af, 6,
                        shadow=True, bevel=False, stops_src=DEEP_GOLD_STOPS)

    return save(canvas, "dv-production-banner-square.jpg")


# ── 2. кастинг на пробы в кино, 3:5 ────────────────────────────────────────
def build_kino() -> Path:
    W, H = 2400, 4300
    MARGIN = 150
    base = prepare_plate(WORK / "plate-kino.jpg", (W, H))
    canvas = base.convert("RGBA")
    frame(canvas)
    draw = ImageDraw.Draw(canvas, "RGBA")

    logo_lockup(canvas, MARGIN, MARGIN, 250)
    cx = W // 2

    y = 520
    f_label = montserrat(56, "Medium")
    text_line(canvas, cx, y, "ПРОДЮСЕРСКИЙ ЦЕНТР", f_label, 56 * 0.44, PLUM, 195)
    y += line_metrics(f_label, "ПРОДЮСЕРСКИЙ ЦЕНТР", 56 * 0.44)[1] + 46

    name_f = fit_font(prata, "ДВ ПРОДАКШЕН", W - 2 * MARGIN, 168, 0.05)
    text_line(canvas, cx, y, "ДВ ПРОДАКШЕН", name_f, name_f.size * 0.05, PLUM, 232)
    y += line_metrics(name_f, "ДВ ПРОДАКШЕН", name_f.size * 0.05)[1] + 52

    f_sub = montserrat(48, "Medium")
    text_line(canvas, cx, y, "АКТЁРСКО-МОДЕЛЬНАЯ СТУДИЯ", f_sub, 48 * 0.30, PLUM, 200)
    y += line_metrics(f_sub, "АКТЁРСКО-МОДЕЛЬНАЯ СТУДИЯ", 48 * 0.30)[1] + 58
    ornament(draw, cx, y, 280, (*CHAMPAGNE, 165))

    kf = prata(196)
    root = y + 60
    place_gold_text(canvas, cx, root, "КАСТИНГ НА", kf, kf.size * 0.055, glow=0.16)
    place_gold_text(canvas, cx, root + 232, "ПРОБЫ В КИНО", kf, kf.size * 0.055, glow=0.16)

    af = prata(120)
    place_gold_text(canvas, cx, root + 500, "4–18 ЛЕТ", af, 10,
                    shadow=True, bevel=False, stops_src=DEEP_GOLD_STOPS)

    # 3:5 плашка QR — между текстом и первым рядом гостей (гости начинаются ~y 3070)
    qr_side = 700
    qr_top = root + 500 + 200
    qr_block(canvas, cx, qr_top + qr_side // 2, qr_side, src=OUT_DIR / "qr-kino.png")

    return save(canvas, "dv-production-casting-kino.jpg")


# ── 3. кастинг на модный показ, 2:3 ────────────────────────────────────────
def build_pokaz() -> Path:
    W, H = 2400, 3600
    MARGIN = 150
    base = prepare_plate(WORK / "plate-pokaz.jpg", (W, H))
    canvas = base.convert("RGBA")
    frame(canvas)
    draw = ImageDraw.Draw(canvas, "RGBA")

    logo_lockup(canvas, MARGIN, MARGIN, 236)
    cx = W // 2

    y = 470
    f_label = montserrat(52, "Medium")
    text_line(canvas, cx, y, "ПРОДЮСЕРСКИЙ ЦЕНТР", f_label, 52 * 0.44, PLUM, 195)
    y += line_metrics(f_label, "ПРОДЮСЕРСКИЙ ЦЕНТР", 52 * 0.44)[1] + 40

    name_f = fit_font(prata, "ДВ ПРОДАКШЕН", W - 2 * MARGIN, 156, 0.05)
    text_line(canvas, cx, y, "ДВ ПРОДАКШЕН", name_f, name_f.size * 0.05, PLUM, 232)
    y += line_metrics(name_f, "ДВ ПРОДАКШЕН", name_f.size * 0.05)[1] + 46

    f_sub = montserrat(44, "Medium")
    text_line(canvas, cx, y, "АКТЁРСКО-МОДЕЛЬНАЯ СТУДИЯ", f_sub, 44 * 0.30, PLUM, 200)
    y += line_metrics(f_sub, "АКТЁРСКО-МОДЕЛЬНАЯ СТУДИЯ", 44 * 0.30)[1] + 52
    ornament(draw, cx, y, 260, (*CHAMPAGNE, 165))

    kf = prata(180)
    root = y + 56
    place_gold_text(canvas, cx, root, "КАСТИНГ НА", kf, kf.size * 0.055, glow=0.16)
    place_gold_text(canvas, cx, root + 212, "МОДНЫЙ ПОКАЗ", kf, kf.size * 0.055, glow=0.16)

    qr_side = 660
    qr_top = root + 212 + 230
    qr_block(canvas, cx, qr_top + qr_side // 2, qr_side, src=OUT_DIR / "qr-pokaz.png")

    return save(canvas, "dv-production-casting-pokaz.jpg")


if __name__ == "__main__":
    for path in (build_square(), build_kino(), build_pokaz()):
        save_preview(path)
