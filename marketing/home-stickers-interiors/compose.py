"""Наклейки в интерьерах московских квартир.

Интерьеры — фотореалистичные кадры (raw/). Наклейки — настоящие, из
production/home-stickers-bilingual: рисуются тем же вектором, что уходит
в печать, в 1200 dpi, и накладываются на плоскость с тенью.

ГЛАВНОЕ: масштаб. Наклейка 35 мм на общем плане комнаты — это 10–40 пикселей,
её физически не видно. Поэтому каждая сцена — крупный план: кадр обрезан так,
что его ширина равна известной реальной ширине (30–35 см). Тогда 35 мм
наклейки занимает 10–12 % кадра — как на настоящей фотографии.

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

OUT_W, OUT_H = 1408, 768          # 16:9, как остальные материалы проекта
DPI = 1200                        # рендер наклейки до наложения

# ── сцены ───────────────────────────────────────────────────────────────────
# room_w   — реальная ширина кадра в сантиметрах (задаём сами кропом)
# px_per_cm — сколько пикселей исходника приходится на 1 см (по предмету-эталону)
# crop     — рамка в пикселях исходника, пропорции 16:9
# sticker  — центр наклейки в долях кропа (0..1), от левого верхнего угла
SCENES = [
    # Кадр — крупный план: ширина кадра в сантиметрах задана кропом и известна
    # по предмету-эталону. Наклейка 35 мм всегда 3,5 см, её размер в пикселях
    # считается из этого, а не подбирается на глаз.
    dict(
        src="int-09-fridge-macro.jpg",
        out="01-kitchen-fridge.jpg",
        px_per_cm=15.9,                    # дверь холодильника 60 см ≈ 955 px
        crop=(600, 210, 1315, 600),        # 715×390 → кадр 45 см
        sticker=("Холодильник", 0.40, 0.53),
        caption="Кухня · дверь холодильника",
        note="Гладкая эмаль. Обезжирить, прижать от центра к краям.",
    ),
    dict(
        src="int-10-nightstand-macro.jpg",
        out="02-bedroom-nightstand.jpg",
        px_per_cm=16.2,                    # ящик тумбочки 45 см ≈ 730 px
        crop=(0, 215, 795, 649),           # 795×434 → кадр 49 см
        sticker=("Тумбочка", 0.66, 0.50),
        caption="Спальня · тумбочка",
        note="Крашеное дерево. Снимается без следа, если прогреть феном.",
    ),
    dict(
        src="int-03-bathroom.jpg",
        out="03-bathroom-sink.jpg",
        px_per_cm=5.4,                     # раковина 60 см ≈ 326 px
        crop=(430, 320, 754, 497),         # 324×177 → кадр 60 см
        sticker=("Раковина", 0.34, 0.52),
        caption="Ванная · раковина и плитка",
        note="Влажная зона: только с матовой ламинацией, иначе вода убьёт печать.",
    ),
]

# ── отрисовка наклейки ──────────────────────────────────────────────────────
def render_sticker(ru: str, path: Path) -> Image.Image:
    """Наклейка с прозрачным фоном: PDF → растр 1200 dpi → вырезание белого."""
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

    arr = np.asarray(img).astype(np.int16)
    dist = 255 - arr.min(axis=2)
    alpha = np.clip(dist * 42, 0, 255).astype(np.uint8)
    alpha = Image.fromarray(alpha).filter(ImageFilter.GaussianBlur(0.4))
    img.putalpha(alpha)
    doc.close()
    return img


# ── геометрия ───────────────────────────────────────────────────────────────
def quad_for(cx, cy, size, taper=0.0, sqz=1.0):
    """Четырёхугольник: слегка уже сверху (taper) и сжат по вертикали (sqz)."""
    hw, hh = size / 2, size / 2 * sqz
    tw, bw = 1 - taper, 1 + taper
    return [(cx - hw * tw, cy - hh), (cx + hw * tw, cy - hh),
            (cx + hw * bw, cy + hh), (cx - hw * bw, cy + hh)]


def perspective_coeffs(src_w, src_h, quad):
    dst = np.array([quad[0], quad[3], quad[2], quad[1]], dtype=float)
    src = np.array([[0, 0], [0, src_h], [src_w, src_h], [src_w, 0]], dtype=float)
    A, b = [], []
    for (x, y), (u, v) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); b.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); b.append(v)
    return np.linalg.solve(np.array(A), np.array(b)).tolist()


def paste_sticker(base: Image.Image, sticker: Image.Image, quad,
                  shadow: float = 0.24, blur: float = 3.6,
                  light=(-1, 1), gloss: float = 0.05,
                  focus: float = 0.5, tint: float = 0.28) -> Image.Image:
    w, h = sticker.size
    coeffs = perspective_coeffs(w, h, quad)

    mask = sticker.split()[-1].transform(base.size, Image.PERSPECTIVE, coeffs, Image.BICUBIC)
    art = sticker.convert("RGB").transform(base.size, Image.PERSPECTIVE, coeffs, Image.BICUBIC)

    tight = Image.new("L", base.size, 0)
    tight.paste(mask, (int(light[0] * 2), int(light[1] * 2)))
    tight = tight.filter(ImageFilter.GaussianBlur(blur * 0.5))

    wide = Image.new("L", base.size, 0)
    wide.paste(mask, (int(light[0] * blur * 1.6), int(light[1] * blur * 1.6)))
    wide = wide.filter(ImageFilter.GaussianBlur(blur * 1.9))

    sh = (np.asarray(tight).astype(np.float32) * shadow * 0.85 +
          np.asarray(wide).astype(np.float32) * shadow * 0.45)
    sh = Image.fromarray(np.clip(sh, 0, 255).astype(np.uint8))

    base = base.copy()
    base.paste(Image.new("RGB", base.size, (0, 0, 0)), (0, 0), sh)

    # резкость: наклейка не должна быть резче фона
    art = art.filter(ImageFilter.GaussianBlur(focus))

    # локальный свет: наклейка впитывает цвет и яркость поверхности под собой
    if tint > 0:
        bg = np.asarray(base.filter(ImageFilter.GaussianBlur(28))).astype(np.float32)
        m = np.asarray(mask).astype(np.float32) / 255.0
        wsum = m.sum()
        if wsum > 0:
            local = (bg * m[..., None]).sum(axis=(0, 1)) / wsum
            a = np.asarray(art).astype(np.float32)
            # белый кружок должен стать чуть темнее/теплее в тёплом свете
            gain = 1.0 + (local / 255.0 - 0.75) * tint
            art = Image.fromarray(np.clip(a * gain, 0, 255).astype(np.uint8))

    if gloss > 0:
        g = np.asarray(mask).astype(np.float32) / 255.0
        grad = np.linspace(1.0, 0.0, base.size[1])[:, None]
        gl = (g * grad * gloss * 255).astype(np.uint8)
        art = Image.composite(Image.new("RGB", base.size, (255, 255, 255)), art,
                              Image.fromarray(gl))

    base.paste(art, (0, 0), mask)
    return base


def add_grain(img: Image.Image, amount: float = 2.2) -> Image.Image:
    """Фотографическое зерно: убирает «наклеенность» ровного рендера."""
    a = np.asarray(img).astype(np.float32)
    rng = np.random.default_rng(7)
    n = rng.normal(0, amount, (a.shape[0], a.shape[1], 1))
    a = a + n + rng.normal(0, amount * 0.6, a.shape)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def preview() -> None:
    """Полоса 3 в ряд с подписями: комната + честный масштаб в кадре."""
    from PIL import ImageDraw, ImageFont

    bs.register_fonts()
    fdir = Path("/tmp/fonts-stickers")
    f_cap = ImageFont.truetype(str(fdir / "Montserrat-SemiBold.ttf"), 26)
    f_sub = ImageFont.truetype(str(fdir / "Montserrat-Regular.ttf"), 20)

    tw, gap, band, pad = 620, 26, 66, 34
    th = round(tw * OUT_H / OUT_W)
    w = tw * len(SCENES) + gap * (len(SCENES) - 1) + pad * 2
    h = th + band + pad * 2
    grid = Image.new("RGB", (w, h), (250, 247, 243))
    d = ImageDraw.Draw(grid)

    for i, sc in enumerate(SCENES):
        crop = sc["crop"]
        frame_cm = (crop[2] - crop[0]) / sc["px_per_cm"]
        x = pad + i * (tw + gap)
        tile = Image.open(OUT / sc["out"]).resize((tw, th), Image.LANCZOS)
        grid.paste(tile, (x, pad))
        d.text((x, pad + th + 12), sc["caption"], font=f_cap, fill=(27, 26, 24))
        d.text((x, pad + th + 38), f"Ø 35 мм · кадр {frame_cm:.0f} см", font=f_sub,
               fill=(126, 120, 112))
    grid.save(OUT / "preview-set.jpg", quality=90, optimize=True, progressive=True)
    print(f"  preview-set.jpg  {grid.size[0]}×{grid.size[1]}")


# ── сборка ──────────────────────────────────────────────────────────────────
def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(exist_ok=True)
    cache: dict[str, Image.Image] = {}

    def sticker_for(ru: str) -> Image.Image:
        if ru not in cache:
            cache[ru] = render_sticker(ru, WORK / f"st-{abs(hash(ru)) % 10**6}.pdf")
        return cache[ru]

    for sc in SCENES:
        crop = sc["crop"]
        cw, ch = crop[2] - crop[0], crop[3] - crop[1]
        aspect = cw / ch
        if abs(aspect - OUT_W / OUT_H) > 0.02:
            print(f"  ! {sc['out']}: пропорции кропа {aspect:.2f}, нужно "
                  f"{OUT_W / OUT_H:.2f} — кадр будет растянут")

        img = Image.open(RAW / sc["src"]).convert("RGB").crop(crop)
        img = img.resize((OUT_W, OUT_H), Image.LANCZOS)
        img = img.filter(ImageFilter.UnsharpMask(radius=1.6, percent=70, threshold=2))

        frame_cm = cw / sc["px_per_cm"]           # реальная ширина кадра
        d_px = 3.5 / frame_cm * OUT_W             # наклейка 3,5 см в кадре

        ru, rx, ry = sc["sticker"]
        cx, cy = rx * OUT_W, ry * OUT_H
        quad = quad_for(cx, cy, d_px, taper=0.02, sqz=0.97)

        img = paste_sticker(img, sticker_for(ru), quad)
        img = add_grain(img, 2.2)
        img.save(OUT / sc["out"], quality=92, optimize=True, progressive=True)
        print(f"  {sc['out']:24} кадр {frame_cm:.0f} см · наклейка {d_px:.0f} px "
              f"= {3.5 / frame_cm * 100:.1f} % ширины · апскейл {OUT_W / cw:.1f}×")

    preview()

    return 0


if __name__ == "__main__":
    sys.exit(main())
