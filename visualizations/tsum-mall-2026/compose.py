#!/usr/bin/env python3
"""Стойка TSUM Beauty Days в интерьерах универмага — фотореалистичный композит.

Стойка — готовый рендер (`source/render-concept.jpg`), вырезанный по маске.
Он честнее складских фото: чистая графика, окно с шарами и объём. Но у рендера
одна ошибка — корпус повёрнут на ~7°, нижняя кромка уходит по y = 0.121·x.
Из-за этого стойка тонет в пол углом; при вырезании наклон снимается сдвигом
строк (вертикали остаются вертикальными).

Масштаб считается физически. Для объекта высотой h при камере на высоте c:

    высота на кадре = (h / c) · (y_пола − y_горизонта)

Габарит 1800 мм, камера 1600 мм → коэффициент 1,125. Ничего не подбирается
на глаз: линия глаз взята по сходу перспективы в фоне.

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
SS = 2  # во сколько раз крупнее фона собирается кадр

BG = Path("visualizations/tsum-beauty-days-2026/raw")


# ------------------------------------------------------------------ спрайт
def cut_kiosk() -> Image.Image:
    """Вырезает стойку с рендера и снимает наклон нижней кромки.

    Фон лабораторно-белый, стойка насыщенно-оранжевая, поэтому маска по
    насыщенности чистая. Мягкая серая тень на «столе» под стойкой в маску
    не попадает (её насыщенность < 40) — она нам не нужна, тень считаем свою.
    """
    im = Image.open(SOURCE / "render-concept.jpg").convert("RGB")
    a = np.asarray(im).astype(np.float32)
    sat = a.max(2) - a.min(2)

    m = sat > 40
    m = ndi.binary_closing(m, np.ones((7, 7)))
    m = ndi.binary_opening(m, np.ones((3, 3)))
    lab, n = ndi.label(m)
    sizes = ndi.sum(m, lab, range(1, n + 1))
    m = ndi.binary_fill_holes(lab == (1 + int(np.argmax(sizes))))

    # наклон нижней кромки, замер по 87 точкам: y = 0.1208·x + 1117.5
    k, x0 = 0.1208, 124.0
    w, h = im.size
    h2 = int(h + k * w) + 8
    aff = (1, 0, 0, k, 1, -k * x0)

    sprite = im.transform((w, h2), Image.AFFINE, aff,
                          resample=Image.BICUBIC, fillcolor=(255, 255, 255))
    mask = Image.fromarray((m * 255).astype(np.uint8)).transform(
        (w, h2), Image.AFFINE, aff, resample=Image.BICUBIC, fillcolor=0)
    sprite = sprite.convert("RGBA")
    sprite.putalpha(mask.filter(ImageFilter.GaussianBlur(0.7)))

    box = sprite.split()[3].point(lambda v: 255 if v > 8 else 0).getbbox()
    return sprite.crop(box)


# ------------------------------------------------------------------ сцена
def _soft(size, box, blur, shape="ellipse"):
    layer = Image.new("L", size, 0)
    d = ImageDraw.Draw(layer)
    (d.ellipse if shape == "ellipse" else d.polygon)(box, fill=255)
    return np.asarray(layer.filter(ImageFilter.GaussianBlur(blur))).astype(np.float32) / 255.0


def _grade_under_scene(sprite: Image.Image, warmth: float, base_dark: float,
                       ambient=(1.0, 1.0, 1.0)) -> Image.Image:
    """Ставит стойку в свет зала.

    Рендер снят в студии: ровный холодноватый свет и максимум насыщенности.
    В зале верх стойки ловит свет с потолка, низ уходит в тень и в отражение
    пола, а общий оттенок задаёт окружение — тёплый в историческом зале,
    холодный у окна.
    """
    arr = np.asarray(sprite).astype(np.float32)
    rgb, alpha = arr[..., :3], arr[..., 3:]
    h = rgb.shape[0]
    t = np.arange(h, dtype=np.float32)[:, None] / max(h - 1, 1)      # 0 сверху, 1 снизу

    fall = 1.0 - (1.0 - base_dark) * (t ** 1.5)                       # спад к полу
    rgb = rgb * fall[..., None]

    # боковая моделировка: свет падает не строго сверху
    rgb[..., 0] *= 1.0 + 0.05 * warmth
    rgb[..., 1] *= 1.0 + 0.012 * warmth
    rgb[..., 2] *= 1.0 - 0.045 * warmth

    rgb *= np.array(ambient, dtype=np.float32)

    # снимаем студийную «звонкость»: приглушаем самые светлые пиксели
    mx = rgb.max(-1, keepdims=True)
    over = np.clip((mx - 215.0) / 40.0, 0, 1)
    rgb = rgb - (rgb - rgb * 0.88) * over

    out = np.concatenate([np.clip(rgb, 0, 255), alpha], -1)
    return Image.fromarray(out.astype(np.uint8), "RGBA")


def match_environment(sprite: Image.Image, bg: Image.Image, box, strength: float = 0.6):
    """Согласует яркость и насыщенность спрайта с локальным окружением.

    Поканальная подгонка здесь недопустима: в пятно попадают тёмные витрины и
    синие окна, и белые элементы графики уезжают в бирюзу. Поэтому трогаем
    только светлоту (один коэффициент на все каналы) и чуть приглушаем
    насыщенность — студийный рендер иначе «звенит» на фоне зала.
    """
    patch = np.asarray(bg.crop(box)).astype(np.float32)
    arr = np.asarray(sprite).astype(np.float32)
    rgb, alpha = arr[..., :3], arr[..., 3:]
    m = alpha[..., 0] > 8

    lum = lambda x: 0.299 * x[..., 0] + 0.587 * x[..., 1] + 0.114 * x[..., 2]
    src = float(lum(rgb)[m].mean())
    dst = float(lum(patch).mean())
    ratio = np.clip(dst / max(src, 1e-3), 0.78, 1.12)
    gain = 1.0 + (ratio - 1.0) * strength

    rgb = rgb * gain
    grey = lum(rgb)[..., None]
    rgb = grey + (rgb - grey) * (1.0 - 0.14 * strength)      # насыщенность вниз
    return Image.fromarray(np.concatenate([np.clip(rgb, 0, 255), alpha], -1).astype(np.uint8), "RGBA")


def composite(bg_name: str, sprite: Image.Image, out_name: str, *,
              cx: float, floor: float, horizon: float,
              shadow: float = 0.55, reflect: float = 0.32,
              warmth: float = 1.0, base_dark: float = 0.80, ambient=(1.0, 1.0, 1.0),
              sprite_blur: float = 0.5, bg_sharpen: float = 1.0, env_strength: float = 0.72,
              final_width: int = 1920, caption: str = "") -> tuple[Image.Image, dict]:
    bg = Image.open(BG / bg_name).convert("RGB")
    bg = bg.resize((bg.width * SS, bg.height * SS), Image.LANCZOS)
    if bg_sharpen != 1.0:
        bg = bg.filter(ImageFilter.UnsharpMask(radius=1.8, percent=int(30 * bg_sharpen), threshold=2))
    W, H = bg.size

    h_px = round(KIOSK_H_MM / CAMERA_H_MM * (floor - horizon) * H)
    spr = sprite.resize((max(1, round(sprite.width * h_px / sprite.height)), h_px), Image.LANCZOS)
    scale = sprite.height / h_px                      # во сколько раз уменьшили спрайт
    blur = max(sprite_blur, scale * 0.45)             # спрайт не должен быть резче фона
    if blur:
        spr = spr.filter(ImageFilter.GaussianBlur(blur))
    spr = _grade_under_scene(spr, warmth, base_dark, ambient)

    base = round(floor * H)
    left = round(cx * W - spr.width / 2)
    top = base - spr.height
    sw = spr.width

    arr = np.asarray(bg).astype(np.float32)

    # 1. падающая тень: свет сверху, чуть сбоку — пятно короткое и широкое
    quad = [(left + sw * 0.02, base - 2), (left + sw * 0.98, base - 2),
            (left + sw * 1.10, base + H * 0.022), (left - sw * 0.06, base + H * 0.022)]
    sh = _soft((W, H), quad, max(8, sw * 0.055), shape="polygon") * shadow * 0.50

    # 2. контактная тень: узкая полоса под опорой
    ry = max(4, int(sw * 0.030))
    sh += _soft((W, H), [left - sw * 0.02, base - ry * 1.4, left + sw * 1.02, base + ry * 2.0],
                max(3, sw * 0.014)) * shadow * 1.15

    # 3. общее затемнение пола вокруг опоры
    sh += _soft((W, H), [left - sw * 0.30, base - H * 0.022,
                         left + sw * 1.30, base + H * 0.040], sw * 0.16) * shadow * 0.20
    arr *= (1.0 - np.clip(sh, 0, 1))[..., None]

    out = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")

    # 4. отражение в полированном полу: тянется ниже и затухает
    if reflect > 0:
        rh = int(spr.height * 0.26)
        ref = spr.transpose(Image.FLIP_TOP_BOTTOM).crop((0, spr.height - rh, sw, spr.height))
        ref = ref.filter(ImageFilter.GaussianBlur(max(2.2, rh * 0.075)))
        av = np.asarray(ref.split()[3]).astype(np.float32) / 255.0
        fade = (np.linspace(1.0, 0.0, rh, dtype=np.float32) ** 1.7) * reflect * 0.62
        ref.putalpha(Image.fromarray((av * fade[:, None] * 255).astype(np.uint8)))
        out.alpha_composite(ref, (left, base))

    # 5. сама стойка: сначала подтягиваем цвет к окружению, потом ставим
    pad = int(sw * 0.9)
    env_box = (max(0, left - pad), max(0, base - spr.height - pad // 2),
               min(W, left + sw + pad), min(H, base + pad))
    spr = match_environment(spr, bg, env_box, strength=env_strength)
    out.alpha_composite(spr, (left, top))

    sil = Image.new("L", (W, H), 0)
    sil.paste(spr.split()[3], (left, top))
    sil_a = np.asarray(sil).astype(np.float32) / 255.0

    canvas = np.asarray(out).astype(np.float32)

    # 6. отражение окружения на ламинированной поверхности
    env = bg.filter(ImageFilter.GaussianBlur(max(8, sw * 0.06)))
    env = env.crop((left, top, left + sw, base)).transpose(Image.FLIP_TOP_BOTTOM)
    env_a = np.asarray(env).astype(np.float32)
    m = sil_a[top:top + spr.height, left:left + sw][..., None]
    foot = np.clip((np.arange(spr.height, dtype=np.float32) - spr.height * 0.90)
                   / (spr.height * 0.10), 0, 1) ** 1.3
    canvas[top:top + spr.height, left:left + sw, :3] *= (1.0 - 0.16 * foot[:, None, None])
    grad = np.linspace(0.55, 1.0, spr.height, dtype=np.float32)[:, None, None]
    sub = canvas[top:top + spr.height, left:left + sw, :3]
    mix = 0.10 * m * grad
    canvas[top:top + spr.height, left:left + sw, :3] = sub * (1 - mix) + env_a * mix

    # 7. AO по контуру — стык с фоном не должен «звенеть»
    glow = np.asarray(sil.filter(ImageFilter.GaussianBlur(max(2, sw * 0.022)))).astype(np.float32) / 255.0
    ring = np.clip(glow - sil_a, 0, 1)
    canvas[..., :3] *= (1.0 - ring * 0.20)[..., None]

    img = Image.fromarray(np.clip(canvas, 0, 255).astype(np.uint8), "RGBA").convert("RGB")

    # 8. зерно кадра, чтобы стойка жила в одной «плёночной» текстуре с фоном
    g = np.asarray(img).astype(np.float32)
    rng = np.random.default_rng(5)
    g += rng.normal(0, 2.2, g.shape[:2])[..., None]
    g += rng.normal(0, 1.1, g.shape)
    img = Image.fromarray(np.clip(g, 0, 255).astype(np.uint8))

    if final_width and final_width < img.width:
        img = img.resize((final_width, round(img.height * final_width / img.width)), Image.LANCZOS)
        img = img.filter(ImageFilter.UnsharpMask(radius=1.2, percent=40, threshold=2))

    img.save(OUT / out_name, quality=94, optimize=True, progressive=True)
    pct = 100 * h_px / H
    print(f"  ✓ {out_name}  {img.size[0]}×{img.size[1]} · стойка {round(sw/SS)}×{round(h_px/SS)} px "
          f"в фоне 1:1 ({pct:.1f} % кадра) · {caption}")
    return img, dict(h_px=h_px, pct=pct)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)
    sprite = cut_kiosk()
    sprite.save(WORK / "kiosk.png")
    print(f"  спрайт {sprite.width}×{sprite.height} px, ш/в {sprite.width / sprite.height:.3f}")

    # 1. парадный зал с окнами: стойка в среднем плане, высокий полированный пол
    hall, a = composite("bg-hall-empty.png", sprite, "01-zal-okna.jpg",
                        cx=0.44, floor=0.900, horizon=0.600,
                        shadow=0.62, reflect=0.30, warmth=0.55, base_dark=0.80,
                        ambient=(1.005, 1.0, 0.995), env_strength=0.95,
                        caption="зал с окнами")

    # 2. тот же зал с гостями: стойка ближе, люди вокруг
    people, b = composite("bg-hall-people.png", sprite, "02-zal-gosti.jpg",
                          cx=0.62, floor=0.930, horizon=0.520,
                          shadow=0.62, reflect=0.34, warmth=1.55, base_dark=0.58,
                          ambient=(0.96, 0.93, 0.90), caption="гости на приёме")

    # 3. атриум с балюстрадой — общий план
    _, c = composite("bg-atrium-empty.png", sprite, "03-atrium.jpg",
                     cx=0.50, floor=0.905, horizon=0.610,
                     shadow=0.55, reflect=0.22, warmth=0.85, base_dark=0.78,
                     ambient=(1.0, 0.995, 0.985), env_strength=0.95,
                     caption="атриум")

    # 4. крупный кадр: кроп кадра с гостями — эквивалент длинного объектива
    hero = people.crop((int(people.width * 0.30), int(people.height * 0.02),
                        int(people.width * 0.88), int(people.height * 0.99)))
    hero = hero.resize((1500, round(hero.height * 1500 / hero.width)), Image.LANCZOS)
    hero = hero.filter(ImageFilter.UnsharpMask(radius=1.4, percent=45, threshold=2))
    hero.save(OUT / "04-krupno.jpg", quality=94, optimize=True, progressive=True)
    print(f"  ✓ 04-krupno.jpg  {hero.size[0]}×{hero.size[1]} · кроп кадра 02")

    print("\n  масштабы:", f"зал {a['pct']:.1f} %, гости {b['pct']:.1f} %, "
          f"атриум {c['pct']:.1f} %")
    preview()
    return 0


def preview() -> None:
    from PIL import ImageFont
    files = ["01-zal-okna.jpg", "02-zal-gosti.jpg", "03-atrium.jpg", "04-krupno.jpg"]
    caps = ["1 · Зал с окнами", "2 · Гости на приёме", "3 · Атриум", "4 · Крупный кадр"]
    tw, gap, pad, band = 640, 20, 26, 50
    th = round(tw * 9 / 16)
    w = tw * 2 + gap + pad * 2
    h = (th + band) * 2 + gap + pad * 2
    grid = Image.new("RGB", (w, h), (250, 248, 245))
    d = ImageDraw.Draw(grid)
    f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 23)
    for i, (name, cap) in enumerate(zip(files, caps)):
        x = pad + (i % 2) * (tw + gap)
        y = pad + (i // 2) * (th + band + gap)
        grid.paste(Image.open(OUT / name).resize((tw, th), Image.LANCZOS), (x, y))
        d.text((x, y + th + 14), cap, font=f, fill=(28, 26, 24))
    grid.save(OUT / "preview-set.jpg", quality=92, optimize=True, progressive=True)
    print(f"  ✓ preview-set.jpg {grid.size[0]}×{grid.size[1]}")


if __name__ == "__main__":
    sys.exit(main())
