"""Наклейки в интерьерах московских квартир.

Интерьеры — сгенерированные фотореалистичные кадры (raw/). Наклейки —
настоящие, из production/home-stickers-bilingual: рисуются в 1200 dpi,
накладываются на плоскость с перспективой и мягкой тенью.

Почему не «попросить нейросеть нарисовать наклейки»: любой генератор врёт
в надписях. Здесь текст настоящий, потому что это наш же вектор.

    .venv/bin/python marketing/home-stickers-interiors/compose.py
"""
from __future__ import annotations

import math
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "production/home-stickers-bilingual"))

import build_stickers as bs  # noqa: E402  шрифты + отрисовка наклейки

import numpy as np  # noqa: E402
from PIL import Image, ImageFilter  # noqa: E402
from reportlab.lib.units import mm  # noqa: E402
from reportlab.pdfgen import canvas as rcanvas  # noqa: E402

RAW = HERE / "raw"
OUT = HERE / "final"
WORK = HERE / ".work"

# ── сцены ───────────────────────────────────────────────────────────────────
# quad — четыре угла наклейки на фото: левый-верх, правый-верх, правый-низ,
# левый-низ. Размеры подобраны по ширине предмета: холодильник ~60 см,
# тумбочка ~45 см, плитка 20 см, ТВ 55".
# Каждая сцена: сначала кроп исходника (приближаем к предмету), потом наклейка
# на кропе. Масштаб наклейки берём от реального размера предмета:
#   дверь холодильника 60 см, ящик тумбочки 45 см, полотенце 40 см,
#   ТВ 55" = 123 см. При таком пересчёте 35 мм — это 60–130 px, как в жизни.
# Каждая сцена: кроп исходника (приближаем камеру к предмету), затем наклейка
# на кропе. Размер наклейки считаем от реального размера предмета:
#   дверь холодильника ~45 см в кадре, ящик тумбочки ~45 см, полотенце ~40 см,
#   фасад тумбы под ТВ ~90 см. Тогда 35 мм — это 55–110 px, как в жизни.
SCENES = [
    dict(
        src="int-09-fridge-macro.jpg",
        out="01-kitchen-fridge.jpg",
        crop=(150, 40, 1150, 690),      # 1000×650 → 1408×768
        items=[("Холодильник", (560, 300), 172, 0.0, 1.0, dict(taper=0.03, sqz=0.97))],
        caption="Кухня · холодильник",
        note="Гладкая эмаль. Масштаб наклейки реальный: 35 мм по линии реза.",
    ),
    dict(
        src="int-10-nightstand-macro.jpg",
        out="02-bedroom-nightstand.jpg",
        crop=(0, 180, 900, 686),        # 900×506 → 1408×768
        items=[("Тумбочка", (330, 330), 196, 0.0, 1.0, dict(taper=0.02, sqz=0.96))],
        caption="Спальня · тумбочка",
        note="Крашеное дерево. Снимается без следа, если прогреть феном.",
    ),
    dict(
        src="int-03-bathroom.jpg",
        out="03-bathroom-towel.jpg",
        crop=(790, 330, 1230, 580),     # 440×250 → 1408×768
        items=[("Полотенце", (300, 470), 290, 0.0, 1.0, dict(taper=0.02, sqz=0.95))],
        caption="Ванная · полотенце",
        note="Влажная зона: нужна матовая ламинация, иначе вода убьёт печать.",
    ),
    dict(
        src="int-04-livingroom.jpg",
        out="04-livingroom-console.jpg",
        crop=(430, 380, 870, 630),      # 440×250 → 1408×768
        items=[("Телевизор", (520, 118), 190, 0.0, 1.0, dict(taper=0.03, sqz=0.97))],
        caption="Гостиная · телевизор",
        note="Наклейка под экраном: слово там, куда смотрит ребёнок.",
    ),
]

DPI = 1200


# ── отрисовка наклейки ──────────────────────────────────────────────────────
def render_sticker(ru: str, path: Path, px: int = 1400) -> Image.Image:
    """Наклейка с прозрачным фоном: рисуем в PDF, растеризуем с альфой."""
    import pymupdf

    item = next(it for it in bs.ITEMS if it[0] == ru)
    size = bs.R_BLEED * 2 + 2 * mm
    c = rcanvas.Canvas(str(path), pagesize=(size, size))
    bs.draw_sticker(c, size / 2, size / 2, item, show_cut=False)
    c.showPage()
    c.save()

    doc = pymupdf.open(path)
    page = doc[0]
    base = page.get_pixmap(dpi=DPI, alpha=False)
    img = Image.frombytes("RGB", (base.width, base.height), base.samples)

    # маска: всё, что не белый фон
    a = np.asarray(img).astype(np.int16)
    dist = 255 - a.min(axis=2)          # чем дальше от белого, тем «плотнее»
    alpha = np.clip(dist * 42, 0, 255).astype(np.uint8)
    alpha = Image.fromarray(alpha).filter(ImageFilter.GaussianBlur(0.4))
    img.putalpha(alpha)
    doc.close()
    return img


# ── геометрия ───────────────────────────────────────────────────────────────
def quad_for(cx, cy, size, angle_deg, flip, taper=0.0, sqz=1.0):
    """Четырёхугольник наклейки на плоскости.

    size   — ширина (по горизонтали)
    taper  — насколько дальний (верхний) край уже ближнего: 0 = без перспективы
    sqz    — сжатие по вертикали: плоскость видна под углом, круг становится эллипсом
    flip   — сжатие по горизонтали
    """
    a = math.radians(angle_deg)
    hw = size / 2
    hh = size / 2 * sqz
    top_w, bot_w = (1 - taper), (1 + taper)
    pts = [(-hw * top_w * flip, -hh), (hw * top_w * flip, -hh),
           (hw * bot_w * flip, hh), (-hw * bot_w * flip, hh)]
    out = []
    for x, y in pts:
        xr = x * math.cos(a) - y * math.sin(a)
        yr = x * math.sin(a) + y * math.cos(a)
        out.append((cx + xr, cy + yr))
    return out


def perspective_coeffs(src_w, src_h, quad):
    """Коэффициенты обратного перспективного преобразования (PIL QUAD)."""
    # PIL берёт quad как 8 чисел: (x0,y0,x1,y1,x2,y2,x3,y3) в порядке
    # левый-верх, левый-низ, правый-низ, правый-верх
    dst = np.array([quad[0], quad[3], quad[2], quad[1]], dtype=float)
    src = np.array([[0, 0], [0, src_h], [src_w, src_h], [src_w, 0]], dtype=float)

    A, b = [], []
    for (x, y), (u, v) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y])
        b.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y])
        b.append(v)
    res = np.linalg.solve(np.array(A, dtype=float), np.array(b, dtype=float))
    return res.tolist()


def paste_sticker(base: Image.Image, sticker: Image.Image, quad,
                  shadow: float = 0.26, blur: float = 6.0,
                  light=(-1, 1), gloss: float = 0.10) -> Image.Image:
    """Наклейка с перспективой, контактной тенью и лёгким блеском."""
    w, h = sticker.size
    coeffs = perspective_coeffs(w, h, quad)

    # маска наклейки, растянутая в перспективу
    mask = sticker.split()[-1].transform(base.size, Image.PERSPECTIVE, coeffs,
                                         Image.BICUBIC)
    art = sticker.convert("RGB").transform(base.size, Image.PERSPECTIVE, coeffs,
                                           Image.BICUBIC)

    # контактная тень: плотная у края, мягкая дальше (два слоя)
    tight = Image.new("L", base.size, 0)
    tight.paste(mask, (int(light[0] * 2), int(light[1] * 2)))
    tight = tight.filter(ImageFilter.GaussianBlur(blur * 0.45))

    wide = Image.new("L", base.size, 0)
    wide.paste(mask, (int(light[0] * blur * 1.5), int(light[1] * blur * 1.5)))
    wide = wide.filter(ImageFilter.GaussianBlur(blur * 1.8))

    sh = Image.new("L", base.size, 0)
    sh.paste(tight.point(lambda v: int(v * shadow)))
    sh = Image.composite(sh, Image.new("L", base.size, 0), Image.new("L", base.size, 255))
    sh_np = (np.asarray(tight).astype(np.float32) * shadow * 0.75 +
             np.asarray(wide).astype(np.float32) * shadow * 0.45)
    sh = Image.fromarray(np.clip(sh_np, 0, 255).astype(np.uint8))

    base = base.copy()
    base.paste(Image.new("RGB", base.size, (0, 0, 0)), (0, 0), sh)

    # блеск: подмешиваем белый по верхней части наклейки
    if gloss > 0:
        g = np.asarray(mask).astype(np.float32) / 255.0
        h = np.linspace(1.0, 0.0, base.size[1])[:, None]
        gl = (g * h * gloss * 255).astype(np.uint8)
        gloss_layer = Image.new("RGB", base.size, (255, 255, 255))
        art = Image.composite(Image.blend(art, gloss_layer, 1.0),
                              art, Image.fromarray(gl))

    base.paste(art, (0, 0), mask)
    return base


def add_highlight(img: Image.Image, quad, strength: int = 10) -> Image.Image:
    """Лёгкий блик: у глянцевых поверхностей наклейка чуть светлеет сверху."""
    return img


# ── сборка ──────────────────────────────────────────────────────────────────
def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(exist_ok=True)

    cache: dict[str, Image.Image] = {}

    def get(ru):
        if ru not in cache:
            p = WORK / f"st-{abs(hash(ru)) % 10**6}.pdf"
            cache[ru] = render_sticker(ru, p)
        return cache[ru]

    for sc in SCENES:
        base = Image.open(RAW / sc["src"]).convert("RGB")
        if sc.get("crop"):
            base = base.crop(sc["crop"]).resize((1408, 768), Image.LANCZOS)
        for ru, (cx, cy), size, ang, flip, *rest in reversed(sc["items"]):
            st = get(ru)
            quad = quad_for(cx, cy, size, ang, flip, **(rest[0] if rest else {}))
            base = paste_sticker(base, st, quad)

        base.save(OUT / sc["out"], quality=92, optimize=True, progressive=True)

        print(f"  {sc['out']}  {base.size[0]}×{base.size[1]}")

    # превью-сетка 2×2
    tiles = [Image.open(OUT / sc["out"]) for sc in SCENES]
    tw = 960
    th = round(tiles[0].height * tw / tiles[0].width)
    grid = Image.new("RGB", (tw * 2 + 24, th * 2 + 24), (250, 247, 243))
    for i, t in enumerate(tiles):
        t = t.resize((tw, th), Image.LANCZOS)
        grid.paste(t, ((i % 2) * (tw + 24), (i // 2) * (th + 24)))
    grid.save(OUT / "preview-set.jpg", quality=90, optimize=True, progressive=True)
    print(f"  preview-set.jpg  {grid.size[0]}×{grid.size[1]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
