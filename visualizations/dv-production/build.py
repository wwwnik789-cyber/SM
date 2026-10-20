#!/usr/bin/env python3
"""
Сборка макетов «ДВ Продакшен — актёрско-модельная студия».

Все надписи набираются шрифтами (Playfair Display + Manrope), а не
генерируются нейросетью — поэтому в русском тексте нет опечаток и
«поехавших» букв. Фон берётся из source/*.jpg.

Запуск:
    python build.py                # все макеты и все варианты фона
    python build.py horizontal     # только 16:9
    python build.py vertical       # только 4:5

Правки клиента, которые легко повторять:
    1) «более нежный фон»      → WALL_VARIANTS (или свой hex в PALETTE)
    2) «дорожка красная»       → уже красная; оттенок в PALETTE["wine"]
    3) «люди по бокам эпатажнее» → source/*.jpg (перегенерация подложки)
    4) «ДВ Продакшен»          → TEXTS["title"]
    5) «логотип в угол»        → draw_logo(), позиция в build_*()
    6) «актёрско-модельная студия» → TEXTS["studio"]
    7) «кастинг …»             → TEXTS["cast_left" / "cast_right"]
"""

from __future__ import annotations

import argparse
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(ROOT, "fonts")

PLAYFAIR = os.path.join(FONT_DIR, "PlayfairDisplay-Variable.ttf")
MANROPE = os.path.join(FONT_DIR, "Manrope-Variable.ttf")

# ----------------------------------------------------------------------------
# Тексты макета
# ----------------------------------------------------------------------------
TEXTS = {
    "eyebrow": "ПРОДЮСЕРСКИЙ ЦЕНТР",
    "title": "ДВ ПРОДАКШЕН",
    "studio": "АКТЕРСКО-МОДЕЛЬНАЯ СТУДИЯ",
    "cast_kicker": "КАСТИНГ",
    "cast_left": "НА ПРОБЫ В КИНО",
    "cast_left_age": "4–18 ЛЕТ",
    "cast_right": "В РЕАЛИТИ ШОУ",
    "cast_right_age": "18–45 ЛЕТ",
    "logo_name": "ПРОДАКШЕН",
    "logo_sub": "ПРОДЮСЕРСКИЙ ЦЕНТР",
}

# ----------------------------------------------------------------------------
# Палитра
# ----------------------------------------------------------------------------
PALETTE = {
    "ink": "#2B1C16",        # основной текст
    "gold": "#A9803E",       # фирменное золото
    "wine": "#8E1B22",       # акцент под цвет дорожки
}

# Варианты «нежного» фона: цвет + сила подмешивания.
# Люди защищены маской, поэтому лица и костюмы не выцветают.
WALL_VARIANTS = {
    "01-pudrovyj-rozovyj": ("#F8E7E3", 0.60),
    "02-shampan": ("#F8EFE3", 0.60),
    "03-holodnyj-pudrovyj": ("#F0E8ED", 0.58),
    "04-svetlyj-len": ("#F6EEE6", 0.60),
}

SS = 2  # суперсэмплинг: рисуем в 2× и уменьшаем — чистые края букв


# ----------------------------------------------------------------------------
# Утилиты
# ----------------------------------------------------------------------------
def load_font(path: str, size: int, weight: int) -> ImageFont.FreeTypeFont:
    font = ImageFont.truetype(path, size)
    try:
        font.set_variation_by_axes([weight])
    except Exception:  # статичный шрифт — просто игнорируем
        pass
    return font


def text_width(draw: ImageDraw.ImageDraw, s: str, font, tracking: float) -> float:
    return sum(draw.textlength(ch, font=font) for ch in s) + tracking * max(len(s) - 1, 0)


def draw_tracked(draw, xy, s, font, fill, tracking=0.0, anchor="la") -> float:
    """Текст с трекингом. Возвращает ширину."""
    total = text_width(draw, s, font, tracking)
    x, y = xy
    if anchor[0] == "m":
        x -= total / 2
    elif anchor[0] == "r":
        x -= total
    for ch in s:
        draw.text((x, y), ch, font=font, fill=fill, anchor="l" + anchor[1])
        x += draw.textlength(ch, font=font) + tracking
    return total


def fit_font(draw, s, path, weight, target_w, start=200):
    size = start
    for _ in range(80):
        font = load_font(path, size, weight)
        if text_width(draw, s, font, 0) <= target_w or size <= 8:
            return font
        size -= max(1, int(size * 0.02))
    return load_font(path, size, weight)


def tint_wall(img: Image.Image, color: str, amount: float, protect_columns: list[tuple],
              floor_start: float = 0.58, floor_end: float = 0.84) -> Image.Image:
    """Нежно подмешивает оттенок в стену, не трогая людей и пол.

    1) vertical fade: сверху стена — 100% тонировки, к полу плавно уходит в 0;
    2) protect_columns: колонки с людьми (доли кадра) полностью исключаются,
       маска размывается, поэтому нет видимых прямоугольных границ.
    """
    if amount <= 0:
        return img
    W, H = img.size

    # 1. мягкий вертикальный градиент
    grad = Image.new("L", (1, H))
    px = grad.load()
    for y in range(H):
        t = y / max(H - 1, 1)
        if t <= floor_start:
            v = 255
        elif t >= floor_end:
            v = 0
        else:
            f = (t - floor_start) / (floor_end - floor_start)
            v = int(255 * (1 - f * f * (3 - 2 * f)))  # smoothstep
        px[0, y] = v
    grad = grad.resize((W, H))

    # 2. защита людей
    prot = Image.new("L", (W, H), 0)
    pd = ImageDraw.Draw(prot)
    for x0, y0, x1, y1 in protect_columns:
        pd.rectangle([x0 * W, y0 * H, x1 * W, y1 * H], fill=255)
    prot = prot.filter(ImageFilter.GaussianBlur(W * 0.03))

    mask = Image.composite(Image.new("L", (W, H), 0), grad, prot)
    mask = mask.point(lambda v: int(v * amount))
    return Image.composite(Image.new("RGB", (W, H), color), img, mask)


def boost_red(img: Image.Image, rect: tuple, sat: float = 1.35) -> Image.Image:
    """Насыщеннее красный, но только там, где пиксель действительно красный.

    Маска = «красное доминирует над зелёным и синим» × мягкая область rect.
    Поэтому нет видимых прямоугольников на полу, а лица не затрагиваются
    (они вне области дорожки).
    """
    from PIL import ImageChops

    W, H = img.size
    r, g, b = img.split()
    red_dom = ImageChops.subtract(r, ImageChops.darker(g, b))
    red_mask = red_dom.point(lambda p: min(255, max(0, (p - 26) * 7)))

    region = Image.new("L", (W, H), 0)
    ImageDraw.Draw(region).rectangle(
        [rect[0] * W, rect[1] * H, rect[2] * W, rect[3] * H], fill=255)
    region = region.filter(ImageFilter.GaussianBlur(W * 0.02))

    mask = ImageChops.multiply(red_mask, region).filter(ImageFilter.GaussianBlur(W * 0.004))

    h, s_, v = img.convert("HSV").split()
    boosted = Image.merge("HSV", (h, s_.point(lambda p: min(255, int(p * sat))), v)).convert("RGB")
    return Image.composite(boosted, img, mask)


def draw_diamond(draw, cx, cy, r, fill):
    draw.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], fill=fill)


# ----------------------------------------------------------------------------
# Блоки
# ----------------------------------------------------------------------------
LOGO_FILE = os.path.join(ROOT, "assets", "dv-logo.png")


def draw_logo(img: Image.Image, draw, x, y, k, height=68.0):
    """Логотип в верхнем углу.

    Если есть assets/dv-logo.png (PNG с прозрачным фоном) — ставится он,
    высотой `height * k` px, левым верхним углом в (x, y). Иначе рисуется
    аккуратная заглушка: монограмма «ДВ» в золотой рамке + название.
    """
    if os.path.exists(LOGO_FILE):
        logo = Image.open(LOGO_FILE).convert("RGBA")
        h = int(height * k)
        w = int(logo.width * h / logo.height)
        logo = logo.resize((w, h), Image.LANCZOS)
        img.paste(logo, (int(x), int(y)), logo)
        return

    ink, gold = PALETTE["ink"], PALETTE["gold"]
    frame = height * k
    draw.rectangle([x, y, x + frame, y + frame],
                   outline=gold, width=max(1, round(1.3 * k)))
    mono = load_font(PLAYFAIR, int(frame * 0.47), 700)
    draw.text((x + frame / 2, y + frame / 2 + 2 * k), "ДВ", font=mono, fill=ink, anchor="mm")

    tx = x + frame + 16 * k
    f_name = load_font(MANROPE, int(14 * k), 800)
    f_sub = load_font(MANROPE, int(8.6 * k), 500)
    draw_tracked(draw, (tx, y + frame * 0.24), TEXTS["logo_name"], f_name, ink, tracking=4.0 * k)
    draw_tracked(draw, (tx, y + frame * 0.62), TEXTS["logo_sub"], f_sub, gold, tracking=2.6 * k)


def draw_center_block(draw, cx, k, top, scale=1.0, max_w=760.0):
    """Заголовок по центру: надзаголовок → название → студия → орнамент."""
    ink, gold = PALETTE["ink"], PALETTE["gold"]

    f_eyebrow = load_font(MANROPE, int(15.5 * k * scale), 600)
    draw_tracked(draw, (cx, top), TEXTS["eyebrow"], f_eyebrow, gold,
                 tracking=6.8 * k * scale, anchor="ma")
    eyebrow_bottom = top + f_eyebrow.size * 0.95

    f_title = fit_font(draw, TEXTS["title"], PLAYFAIR, 700, max_w * k * scale,
                       start=int(118 * k * scale))
    title_top = eyebrow_bottom + 18 * k * scale
    draw.text((cx, title_top), TEXTS["title"], font=f_title, fill=ink, anchor="ma")
    title_bottom = draw.textbbox((cx, title_top), TEXTS["title"], font=f_title, anchor="ma")[3]

    studio_top = title_bottom + 24 * k * scale
    f_studio = load_font(MANROPE, int(19 * k * scale), 600)
    draw_tracked(draw, (cx, studio_top), TEXTS["studio"], f_studio, ink,
                 tracking=6.2 * k * scale, anchor="ma")
    studio_bottom = studio_top + f_studio.size * 0.95

    oy = studio_bottom + 24 * k * scale
    span, gap = 84 * k * scale, 12 * k * scale
    lw = max(1, round(1.1 * k))
    draw.line([(cx - span, oy), (cx - gap, oy)], fill=gold, width=lw)
    draw.line([(cx + gap, oy), (cx + span, oy)], fill=gold, width=lw)
    draw_diamond(draw, cx, oy, 4.2 * k * scale, PALETTE["wine"])
    return oy


def draw_cast_block(draw, cx, top, k, line, age, scale=1.0):
    """Блок «Кастинг …»: надстрочная строка, крупная строка, возраст."""
    ink, gold, wine = PALETTE["ink"], PALETTE["gold"], PALETTE["wine"]

    f_kick = load_font(MANROPE, int(13.5 * k * scale), 700)
    w_kick = text_width(draw, TEXTS["cast_kicker"], f_kick, 5.6 * k * scale)
    yy = top - 13 * k * scale
    draw.line([(cx - w_kick / 2 - 30 * k * scale, yy), (cx - w_kick / 2 - 10 * k * scale, yy)],
              fill=gold, width=max(1, round(1 * k)))
    draw.line([(cx + w_kick / 2 + 10 * k * scale, yy), (cx + w_kick / 2 + 30 * k * scale, yy)],
              fill=gold, width=max(1, round(1 * k)))
    draw_tracked(draw, (cx, top), TEXTS["cast_kicker"], f_kick, gold,
                 tracking=5.6 * k * scale, anchor="ma")

    f_line = load_font(PLAYFAIR, int(32 * k * scale), 600)
    draw_tracked(draw, (cx, top + 23 * k * scale), line, f_line, ink,
                 tracking=0.6 * k * scale, anchor="ma")

    f_age = load_font(MANROPE, int(13 * k * scale), 800)
    draw_tracked(draw, (cx, top + 72 * k * scale), age, f_age, wine,
                 tracking=4.4 * k * scale, anchor="ma")


# ----------------------------------------------------------------------------
# Макеты
# ----------------------------------------------------------------------------
def build_horizontal(base_path, out_path, wall, amount, size=(2400, 1350)):
    base = Image.open(base_path).convert("RGB")
    w_out, h_out = size
    img = base.resize((w_out * SS, h_out * SS), Image.LANCZOS)
    k = (w_out * SS) / 1672.0  # координаты в дизайн-единицах холста 1672×941

    # люди: левая фигура и правая фигура
    img = tint_wall(img, wall, amount,
                    protect_columns=[(0.00, 0.10, 0.33, 1.00), (0.69, 0.08, 1.00, 1.00)])
    img = boost_red(img, (0.27, 0.78, 0.63, 1.00), sat=1.28)
    draw = ImageDraw.Draw(img)

    draw_logo(img, draw, 78 * k, 66 * k, k)
    draw_center_block(draw, 836 * k, k, top=104 * k, max_w=770)
    draw_cast_block(draw, 545 * k, 552 * k, k, TEXTS["cast_left"], TEXTS["cast_left_age"])
    draw_cast_block(draw, 1127 * k, 552 * k, k, TEXTS["cast_right"], TEXTS["cast_right_age"])

    out = img.resize((w_out, h_out), Image.LANCZOS).filter(
        ImageFilter.UnsharpMask(radius=1.2, percent=55, threshold=2))
    out.save(out_path, quality=94, subsampling=1, optimize=True)
    return out.size


def build_vertical(base_path, out_path, wall, amount, size=(1600, 2000)):
    base = Image.open(base_path).convert("RGB")
    w_out, h_out = size
    img = base.resize((w_out * SS, h_out * SS), Image.LANCZOS)
    k = (w_out * SS) / 1200.0

    img = tint_wall(img, wall, amount,
                    protect_columns=[(0.00, 0.40, 0.35, 1.00), (0.73, 0.40, 1.00, 1.00)])
    img = boost_red(img, (0.28, 0.80, 0.72, 1.00), sat=1.28)
    draw = ImageDraw.Draw(img)

    draw_logo(img, draw, 64 * k, 58 * k, 0.82 * k, height=72)
    draw_center_block(draw, 600 * k, 0.98 * k, top=136 * k, max_w=790)
    draw_cast_block(draw, 288 * k, 505 * k, 0.80 * k, TEXTS["cast_left"], TEXTS["cast_left_age"])
    draw_cast_block(draw, 912 * k, 505 * k, 0.80 * k, TEXTS["cast_right"], TEXTS["cast_right_age"])

    out = img.resize((w_out, h_out), Image.LANCZOS).filter(
        ImageFilter.UnsharpMask(radius=1.2, percent=55, threshold=2))
    out.save(out_path, quality=94, subsampling=1, optimize=True)
    return out.size


# ----------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("which", nargs="?", default="all",
                    choices=["all", "horizontal", "vertical"])
    args = ap.parse_args()

    hbase = os.path.join(ROOT, "source", "base-horizontal-v5.jpg")
    vbase = os.path.join(ROOT, "source", "base-vertical-v2.jpg")
    var_dir = os.path.join(ROOT, "variants")
    os.makedirs(var_dir, exist_ok=True)

    first = True
    for name, (wall, amount) in WALL_VARIANTS.items():
        if args.which in ("all", "horizontal"):
            size = build_horizontal(hbase, os.path.join(var_dir, f"16x9--{name}.jpg"),
                                    wall, amount)
            print(f"✓ 16:9 {name} {size}")
            if first:
                build_horizontal(hbase, os.path.join(ROOT, "dv-production-poster-16x9.jpg"),
                                 wall, amount)
        if args.which in ("all", "vertical"):
            size = build_vertical(vbase, os.path.join(var_dir, f"4x5--{name}.jpg"),
                                  wall, amount)
            print(f"✓ 4:5  {name} {size}")
            if first:
                build_vertical(vbase, os.path.join(ROOT, "dv-production-post-4x5.jpg"),
                               wall, amount)
        first = False
    return 0


if __name__ == "__main__":
    sys.exit(main())
