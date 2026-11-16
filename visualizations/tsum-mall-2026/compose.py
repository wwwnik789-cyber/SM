#!/usr/bin/env python3
"""Визуализация стойки TSUM Beauty Days в интерьерах ТЦ.

Стойка — не сгенерированная картинка: она вырезана с реального фото со склада
(04-foto-sklad-ugol.jpg) и вставлена в сгенерированный интерьер. Поэтому окно,
графика «TSUM BEAUTY DAYS» и внутренняя полка на кадре — ровно те, что в жизни.

Масштаб считается физически. Для объекта высотой h, стоящего на полу, при
камере на высоте c:

    (низ − верх) / (низ − горизонт) = h / c

то есть высота на кадре = (h/c) · (y_пола − y_горизонта). Габарит стойки
1800 мм, камера 1600 мм → коэффициент 1,125. Никаких «на глаз».

    .venv/bin/python visualizations/tsum-mall-2026/compose.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage as ndi

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "source"
WORK = HERE / "work"
OUT = HERE / "frames"

KIOSK_H_MM = 1800.0
CAMERA_H_MM = 1600.0

# Контур стойки на фото 03 (1440×1920) — фронтальный ракурс, по пиксельным
# срезам границ. Ракурс «три четверти» (04) для вставки не годится: он снят
# с ~1 м широкоугольником, и при переносе в зал пятно опоры выглядит остриём.
POINTS = [
    (412, 199), (1110, 201), (1137, 340), (1123, 620),
    (1107, 900), (1085, 1180), (1058, 1460), (1048, 1548),
    (414, 1528), (396, 1020), (393, 296),
]

# Поля передней грани без текста: по ним замеряется перепад освещения.
MARGIN_L = (25, 70)
MARGIN_R = (-90, -45)

SS = 4  # суперсэмплинг контура


# --------------------------------------------------------------- вырезание
def cut_kiosk(photo: str = "03-foto-sklad-front.jpg") -> Image.Image:
    """Вырезает стойку по ручному контуру, сжимая его на 1,4 px внутрь."""
    im = Image.open(SOURCE / photo).convert("RGB")
    w, h = im.size

    big = Image.new("L", (w * SS, h * SS), 0)
    ImageDraw.Draw(big).polygon([(x * SS, y * SS) for x, y in POINTS], fill=255)
    m = np.asarray(big) > 127
    m = ndi.binary_erosion(m, ndi.generate_binary_structure(2, 1), iterations=int(2.4 * SS))
    m = ndi.binary_fill_holes(m)

    small = Image.fromarray((m * 255).astype(np.uint8)).resize((w, h), Image.LANCZOS)
    alpha = small.filter(ImageFilter.GaussianBlur(0.8))

    out = im.copy()
    out.putalpha(alpha)
    box = Image.fromarray(np.asarray(alpha) > 8).getbbox()
    return out.crop(box)


def relight(k: Image.Image) -> Image.Image:
    """Вытягивает тени склада и приводит цвет к печатному оранжевому.

    На складе стойка снята в темноте и с синим уклоном: передняя грань
    почти чёрная, боковина уходит в розово-серое. Поднимаем яркость и тянем
    оттенок насыщенных пикселей к 15°, не трогая белые буквы и окно.
    """
    arr = np.asarray(k).astype(np.float32)
    rgb = arr[..., :3] / 255.0
    alpha = arr[..., 3:]

    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    mx, mn = rgb.max(-1), rgb.min(-1)
    v = mx
    s = np.where(mx > 1e-5, (mx - mn) / np.maximum(mx, 1e-5), 0.0)

    # оттенок, устойчивый к серым (буквы, белая панель окна)
    hue = np.zeros_like(v)
    d = np.maximum(mx - mn, 1e-5)
    warm = mx > mn
    hue = np.where(warm & (mx == r), ((g - b) / d) % 6, hue)
    hue = np.where(warm & (mx == g), (b - r) / d + 2, hue)
    hue = np.where(warm & (mx == b), (r - g) / d + 4, hue)

    # 1. подъём теней по кривой, а не по средней яркости
    v2 = 0.055 + 0.945 * np.power(v, 0.66)

    # 2. насыщенные поверхности тянем к печатному оранжевому (≈15°)
    w = np.clip((s - 0.22) / 0.28, 0, 1)
    s2 = np.clip(s * 1.18, 0, 0.84)
    hue2 = hue * (1 - w) + (15 / 60.0) * w

    # 3. HSV → RGB
    c = v2 * s2
    x = c * (1 - np.abs(hue2 % 2 - 1))
    m_ = v2 - c
    z = np.zeros_like(c)
    r2 = np.select([hue2 < 1, hue2 < 2, hue2 < 3, hue2 < 4, hue2 < 5],
                   [c, x, z, z, x], z)
    g2 = np.select([hue2 < 1, hue2 < 2, hue2 < 3, hue2 < 4, hue2 < 5],
                   [x, c, c, x, z], z)
    b2 = np.select([hue2 < 1, hue2 < 2, hue2 < 3, hue2 < 4, hue2 < 5],
                   [z, z, x, c, c], z)
    out = np.stack([r2 + m_, g2 + m_, b2 + m_], -1)

    # 4. тёплый баланс под лампы ТЦ и лёгкая компрессия пересветов
    out = out ** 0.97
    out[..., 0] *= 1.035
    out[..., 2] *= 0.965

    res = np.concatenate([np.clip(out, 0, 1) * 255.0, alpha], -1)
    img = Image.fromarray(np.clip(res, 0, 255).astype(np.uint8))
    return flatten_lighting(img)


def flatten_lighting(img: Image.Image) -> Image.Image:
    """Выравнивает перепад освещения сверху вниз, оставляя лёгкий спад.

    Стойку на складе снимали с одной лампой: низ вдвое темнее верха, из-за
    чего нижняя надпись пропадает. Считаем поправку по замеренному профилю
    и подмешиваем её только в средне-яркие пиксели — окно и белые буквы
    не трогаем.
    """
    arr = np.asarray(img).astype(np.float32)
    rgb, alpha = arr[..., :3], arr[..., 3:4]
    h, w_ = rgb.shape[:2]

    # профиль по полям без текста, сглаженный по 60 строкам
    band = np.concatenate([rgb[:, MARGIN_L[0]:MARGIN_L[1]],
                           rgb[:, w_ + MARGIN_R[0]:w_ + MARGIN_R[1]]], axis=1)
    prof = ndi.uniform_filter1d(band.max(axis=2).mean(axis=1), size=61, mode="nearest")
    prof = np.maximum(prof, 1.0)

    ys = np.arange(h, dtype=np.float32)
    target = 202.0 * (1.0 - 0.20 * ys / h)
    gain = np.clip(target / prof, 0.80, 1.90)[:, None]

    luma = (0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]) / 255.0
    w = np.clip((0.62 - luma) / 0.18, 0, 1)
    g = 1.0 + (gain - 1.0) * w

    out = np.clip(rgb * g[..., None], 0, 255)
    return Image.fromarray(np.concatenate([out, alpha], -1).astype(np.uint8))


# ------------------------------------------------------------------ сцена
def keystone(img: Image.Image, k: float) -> Image.Image:
    """Сужает верх спрайта на долю k: верх стойки дальше от оптической оси.

    Без этого стойка выглядит наклейкой с идеально параллельными сторонами.
    """
    if k <= 0:
        return img
    arr = np.asarray(img)
    h, w = arr.shape[:2]
    out = np.zeros_like(arr)
    for y in range(h):
        s_ = 1.0 - k * (1.0 - y / (h - 1))
        sw_ = max(2, int(round(w * s_)))
        x0 = (w - sw_) // 2
        row = arr[y, x0:x0 + sw_]
        idx = (np.arange(w) * (sw_ / w)).astype(np.int32).clip(0, sw_ - 1)
        out[y] = row[idx]
    return Image.fromarray(out)


def _soft_ellipse(size, box, blur):
    layer = Image.new("L", size, 0)
    ImageDraw.Draw(layer).ellipse(box, fill=255)
    return np.asarray(layer.filter(ImageFilter.GaussianBlur(blur))).astype(np.float32) / 255.0


def _polygon_shadow(size, quad, blur):
    layer = Image.new("L", size, 0)
    ImageDraw.Draw(layer).polygon(quad, fill=255)
    return np.asarray(layer.filter(ImageFilter.GaussianBlur(blur))).astype(np.float32) / 255.0


def place(bg_name: str, kiosk: Image.Image, out_name: str, *,
          cx: float, floor: float, horizon: float,
          light_from: str = "left", shadow: float = 0.55,
          reflect: float = 0.30, grade=(1.0, 1.0, 1.0), env_mix: float = 0.11,
          scale: float = 1.5,
          caption: str = "") -> tuple[Image.Image, dict]:
    """Ставит стойку на пол в точке (cx, floor) с физически верной высотой.

    horizon — линия глаз камеры в долях высоты кадра; из неё и высоты пола
    получается размер стойки. Ничего не подгоняется вручную.
    """
    bg = Image.open(WORK / bg_name).convert("RGB")
    if scale != 1.0:
        bg = bg.resize((round(bg.width * scale), round(bg.height * scale)), Image.LANCZOS)
    W, H = bg.size

    h_px = round(KIOSK_H_MM / CAMERA_H_MM * (floor - horizon) * H)
    sprite = kiosk.resize((max(1, round(kiosk.width * h_px / kiosk.height)), h_px), Image.LANCZOS)
    sprite = keystone(sprite, 0.045)

    base = round(floor * H)
    left = round(cx * W - sprite.width / 2)
    top = base - sprite.height
    sw = sprite.width

    arr = np.asarray(bg).astype(np.float32)

    # 1. падающая тень: плотная у опоры, рассеивается в сторону от света
    sign = -1 if light_from == "left" else 1
    reach = sw * 0.50
    drop = H * 0.060
    quad = [
        (left + sw * 0.02, base - 3),
        (left + sw * 0.98, base - 3),
        (left + sw * 0.98 + sign * reach, base + drop),
        (left + sw * 0.02 + sign * reach * 0.30, base + drop),
    ]
    cast = _polygon_shadow((W, H), quad, max(8, sw * 0.05))
    fade_y = np.clip(1.0 - (np.arange(H, dtype=np.float32) - base) / max(drop, 1), 0, 1)
    fade_y = np.where(np.arange(H) < base, 1.0, fade_y) ** 1.4
    sh = cast * fade_y[:, None] * shadow * 0.80

    # 2. контактная тень: узкая и плотная, стойка не должна «висеть»
    ry = max(5, int(sw * 0.038))
    contact = _soft_ellipse((W, H), [left - sw * 0.06, base - ry,
                                     left + sw * 1.10, base + ry * 3.0], max(6, sw * 0.032))
    sh = np.clip(sh + contact * shadow * 0.60, 0, 1)

    # 2b. общая присадка пола вокруг опоры (ambient occlusion)
    ao = _soft_ellipse((W, H), [left - sw * 0.35, base - H * 0.03,
                                left + sw * 1.35, base + H * 0.045], sw * 0.22)
    sh = np.clip(sh + ao * shadow * 0.18, 0, 1)

    arr *= (1.0 - sh)[..., None]

    # 3. отражение в полированном полу
    out = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
    if reflect > 0:
        rh = int(sprite.height * 0.24)
        ref = sprite.transpose(Image.FLIP_TOP_BOTTOM).crop((0, sprite.height - rh, sw, sprite.height))
        ref = ref.filter(ImageFilter.GaussianBlur(max(1.5, rh * 0.035)))
        a = np.asarray(ref.split()[3]).astype(np.float32) / 255.0
        fade = (np.linspace(1.0, 0.0, rh, dtype=np.float32) ** 1.25) * reflect
        ref.putalpha(Image.fromarray((a * fade[:, None] * 255).astype(np.uint8)))
        out.alpha_composite(ref, (left, base))

    # 4. стойка
    out.alpha_composite(sprite, (left, top))

    # 4b. отражение окружения: глянцевый ламинат не бывает однотонным
    env = bg.filter(ImageFilter.GaussianBlur(max(6, sw * 0.05)))
    env = env.crop((left, base - sprite.height, left + sw, base))
    env = env.transpose(Image.FLIP_TOP_BOTTOM)
    env_a = np.asarray(env).astype(np.float32)

    # 5. световая «обнимающая» подсветка: левый край чуть теплее и ярче
    sil = Image.new("L", (W, H), 0)
    sil.paste(sprite.split()[3], (left, top))
    sil_a = np.asarray(sil).astype(np.float32) / 255.0
    gx = np.linspace(0, 1, sw, dtype=np.float32)[None, :]
    wrap = np.where(light_from == "left", 1.10 - 0.14 * gx, 0.96 + 0.14 * gx)

    canvas = np.asarray(out).astype(np.float32)
    sub = canvas[top:top + sprite.height, left:left + sw, :3]
    sub *= (1.0 + (wrap[..., None] - 1.0) * sil_a[top:top + sprite.height, left:left + sw][..., None])
    canvas[top:top + sprite.height, left:left + sw, :3] = sub

    # 5b. вносим отражение и легчайшее затемнение у самой опоры
    hh, ww = sprite.height, sw
    m = sil_a[top:top + hh, left:left + ww][..., None]
    grad = np.linspace(1.0, 0.45, hh, dtype=np.float32)[:, None, None]
    sub = canvas[top:top + hh, left:left + ww, :3]
    sub = sub * (1 - env_mix * m * grad) + env_a * (env_mix * m * grad)
    foot = np.clip((np.arange(hh)[:, None] - hh * 0.94) / (hh * 0.06), 0, 1)[..., None]
    sub *= (1 - 0.22 * foot * m)
    canvas[top:top + hh, left:left + ww, :3] = sub

    # 6. AO по контуру: стык с фоном не должен «звенеть»
    glow = np.asarray(sil.filter(ImageFilter.GaussianBlur(max(2, sw * 0.025)))).astype(np.float32) / 255.0
    ring = np.clip(glow - sil_a, 0, 1)
    canvas[..., :3] *= (1.0 - ring * 0.18)[..., None]

    # 7. общий грейд под сцену + зерно
    for i, k in enumerate(grade):
        canvas[..., i] *= k
    rng = np.random.default_rng(7)
    canvas[..., :3] += rng.normal(0, 1.6, canvas.shape[:2])[..., None]
    canvas[..., :3] += rng.normal(0, 1.0, canvas[..., :3].shape)

    out = Image.fromarray(np.clip(canvas, 0, 255).astype(np.uint8), "RGBA").convert("RGB")
    out.save(OUT / out_name, quality=94, optimize=True, progressive=True)
    info = dict(h_px=h_px, pct=round(100 * h_px / H, 1), bg=(W, H), caption=caption)
    print(f"  ✓ {out_name}  {W}×{H} · стойка {sprite.width}×{h_px} px "
          f"({info['pct']} % высоты кадра)")
    return out, info


def hero_crop(img: Image.Image, cx: float, floor: float, horizon: float,
              out_name: str, width_px: int = 1500) -> None:
    """Кадр «крупнее» — это кроп с той же точки съёмки, а не увеличенная вставка.

    Перспектива остаётся верной: обрезаем кадр вокруг стойки и поднимаем
    разрешение. Кроп эквивалентен более длинному объективу.
    """
    W, H = img.size
    ratio = 16 / 9
    h_px = KIOSK_H_MM / CAMERA_H_MM * (floor - horizon) * H
    ch = int(h_px * 2.05)
    cw = int(ch * ratio)
    cx_px, base = cx * W, floor * H
    l = int(np.clip(cx_px - cw * 0.48, 0, W - cw))
    t = int(np.clip(base - ch * 0.78, 0, H - ch))
    crop = img.crop((l, t, l + cw, t + ch))
    k = width_px / crop.width
    crop = crop.resize((width_px, round(crop.height * k)), Image.LANCZOS)
    crop = crop.filter(ImageFilter.UnsharpMask(radius=1.6, percent=55, threshold=3))
    crop.save(OUT / out_name, quality=94, optimize=True, progressive=True)
    print(f"  ✓ {out_name}  {crop.size[0]}×{crop.size[1]} · кроп {cw}×{ch} → ×{k:.2f}")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    kiosk = relight(cut_kiosk())
    kiosk.save(WORK / "kiosk-cut.png")
    print(f"  вырезано {kiosk.width}×{kiosk.height} px, "
          f"отношение ширины к высоте {kiosk.width / kiosk.height:.3f}")

    atrium, a = place("bg3-atrium.jpg", kiosk, "01-atrium.jpg",
                      cx=0.50, floor=0.910, horizon=0.549,
                      light_from="left", shadow=0.55, reflect=0.30,
                      grade=(1.0, 0.996, 0.986), caption="Исторический атриум")

    _, m = place("bg2-modern.jpg", kiosk, "02-modern-mall.jpg",
                 cx=0.50, floor=0.925, horizon=0.581,
                 light_from="left", shadow=0.44, reflect=0.36,
                 grade=(1.005, 1.0, 0.998), caption="Современный ТЦ")

    _, b = place("bg2-beauty.jpg", kiosk, "03-beauty-hall.jpg",
                 cx=0.45, floor=0.915, horizon=0.581,
                 light_from="left", shadow=0.50, reflect=0.32,
                 grade=(1.012, 1.0, 0.976), caption="Бьюти-холл")

    hero_crop(atrium, cx=0.50, floor=0.910, horizon=0.549,
              out_name="04-hero-close.jpg")

    _, p_ = place("bg4-atrium-people-clean.jpg", kiosk, "05-atrium-people.jpg",
                  cx=0.42, floor=0.900, horizon=0.507,
                  light_from="left", shadow=0.50, reflect=0.28,
                  grade=(0.98, 0.982, 0.982), env_mix=0.22,
                  caption="Атриум, с посетителями")

    print("\n  масштаб:", f"атриум {a['pct']} %, совр. ТЦ {m['pct']} %, "
          f"бьюти {b['pct']} %, с людьми {p_['pct']} %")
    preview()
    return 0


def preview() -> None:
    from PIL import ImageFont
    files = ["01-atrium.jpg", "02-modern-mall.jpg", "03-beauty-hall.jpg", "05-atrium-people.jpg"]
    caps = ["1 · Исторический атриум", "2 · Современный ТЦ",
            "3 · Бьюти-холл", "4 · Атриум, с посетителями"]
    tw, gap, band, pad = 700, 22, 54, 30
    th = round(tw * 9 / 16)
    w = tw * 2 + gap + pad * 2
    h = (th + band) * 2 + gap + pad * 2
    grid = Image.new("RGB", (w, h), (250, 247, 244))
    d = ImageDraw.Draw(grid)
    f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 25)
    for i, (name, cap) in enumerate(zip(files, caps)):
        x = pad + (i % 2) * (tw + gap)
        y = pad + (i // 2) * (th + band + gap)
        grid.paste(Image.open(OUT / name).resize((tw, th), Image.LANCZOS), (x, y))
        d.text((x, y + th + 14), cap, font=f, fill=(28, 26, 24))
    grid.save(OUT / "preview-set.jpg", quality=92, optimize=True, progressive=True)
    print(f"  ✓ preview-set.jpg {grid.size[0]}×{grid.size[1]}")


if __name__ == "__main__":
    sys.exit(main())
