#!/usr/bin/env python3
"""Рендер детали из ПВХ и вставка её в фотографию интерьера.

Не «наклейка поверх кадра», а маленькая физическая модель:

  * маска контура → карта высот (эрозия/дистанция до края);
  * по карте высот считаются нормали и освещение: рассеянный свет + блик;
  * кромка получает фаску, поэтому деталь читается как толщина, а не как заливка;
  * под деталью — контактная тень (резкая, у самой кромки) и отброшенная
    (мягкая, смещена по направлению света);
  * цвет и яркость подтягиваются под сцену: белый ПВХ не «выжигает» глаз,
    если стена в кадре тёплая и в тени;
  * дальние детали слегка размываются, как и всё на той же глубине.

Всё это в `render_pvc.py`, сцены и раскладка — в `build_scenes.py`.
"""

from __future__ import annotations

from io import BytesIO

import numpy as np
import resvg_py
from PIL import Image, ImageFilter
from scipy.ndimage import distance_transform_edt, gaussian_filter

# ── деталь ───────────────────────────────────────────────────────────────────


def render_alpha(poly, px: int) -> Image.Image:
    """Антиалиасинговая маска контура: белое на прозрачном, ширина px."""
    from shapely import affinity

    min_x, min_y, max_x, max_y = poly.bounds
    width, height = max_x - min_x, max_y - min_y
    shifted = affinity.translate(poly, -min_x, -min_y)

    def ring(coords):
        pts = [(x, height - y) for x, y in coords]
        head = f"M{pts[0][0]:.3f} {pts[0][1]:.3f}"
        return head + "".join(f"L{x:.3f} {y:.3f}" for x, y in pts[1:]) + "Z"

    path = ring(shifted.exterior.coords)
    for interior in shifted.interiors:
        path += " " + ring(interior.coords)

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.3f}" height="{height:.3f}" '
        f'viewBox="0 0 {width:.3f} {height:.3f}">'
        f'<path d="{path}" fill="#ffffff" fill-rule="evenodd"/></svg>'
    )
    png = bytes(resvg_py.svg_to_bytes(svg_string=svg, width=px))
    return Image.open(BytesIO(png)).convert("L")


def _normalise(vector: np.ndarray) -> np.ndarray:
    return vector / (np.linalg.norm(vector) + 1e-9)


def shade(
    alpha: Image.Image,
    tint: tuple[float, float, float],
    light: tuple[float, float, float],
    bevel_px: float,
    ambient: float = 0.52,
    diffuse: float = 0.70,
    specular: float = 0.10,
    sheen: float = 26.0,
    brightness: float = 1.0,
    roughness: float = 0.0,
    seed: int = 0,
) -> Image.Image:
    """Заливка детали с фаской, светом и бликом.

    Возвращает RGBA: цвет уже «освещён», альфа — исходная маска.
    """
    mask = np.asarray(alpha, np.float32) / 255.0
    solid = mask > 0.5

    if not solid.any():
        return Image.new("RGBA", alpha.size, (0, 0, 0, 0))

    # высота: плоская полка в центре, фаска у кромки
    distance = distance_transform_edt(solid)
    height = np.clip(distance / max(bevel_px, 0.8), 0.0, 1.0)
    height = gaussian_filter(height, 1.0)

    grad_y, grad_x = np.gradient(height)
    nx, ny, nz = -grad_x, -grad_y, np.full_like(height, 1.0)
    norm = np.sqrt(nx * nx + ny * ny + nz * nz) + 1e-9
    nx, ny, nz = nx / norm, ny / norm, nz / norm

    lx, ly, lz = _normalise(np.array(light, np.float32))
    lambert = np.clip(nx * lx + ny * ly + nz * lz, 0.0, 1.0)

    # блик по Блинну: половинный вектор между светом и взглядом (0,0,1)
    half = _normalise(np.array([lx, ly, lz + 1.0], np.float32))
    gloss = np.clip(nx * half[0] + ny * half[1] + nz * half[2], 0.0, 1.0) ** sheen

    rng = np.random.default_rng(seed)
    grain = rng.normal(0.0, 1.0 + roughness * 4.0, height.shape).astype(np.float32)

    base = np.array(tint, np.float32)
    lit = ambient + diffuse * lambert
    lit = lit * brightness

    rgb = base[None, None, :] * lit[..., None]
    rgb += 255.0 * specular * gloss[..., None]
    rgb += grain[..., None] * (1.6 + roughness * 3.0)

    # фаска чуть темнее полки — читается толщина материала
    rgb *= (1.0 - 0.045 * (1.0 - height))[..., None]

    out = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    out.putalpha(alpha)
    return out


# ── вставка в сцену ──────────────────────────────────────────────────────────


def _homography(dst, src) -> tuple[float, ...]:
    matrix, vector = [], []
    for (x, y), (u, v) in zip(dst, src):
        matrix.append([x, y, 1, 0, 0, 0, -u * x, -u * y])
        matrix.append([0, 0, 0, x, y, 1, -v * x, -v * y])
        vector += [u, v]
    return tuple(np.linalg.solve(np.array(matrix, float), np.array(vector, float)))


def quad_center(quad):
    xs = [point[0] for point in quad]
    ys = [point[1] for point in quad]
    return (min(xs), min(ys), max(xs), max(ys))


def scene_light(scene: Image.Image, box, shrink: float = 0.25) -> tuple[float, float, float]:
    """Средний цвет сцены под деталью: по нему подтягиваем цвет и яркость."""
    left, top, right, bottom = box
    patch = scene.crop((int(left), int(top), int(right), int(bottom)))
    if patch.width < 2 or patch.height < 2:
        return (0.85, 0.85, 0.85)
    data = np.asarray(patch.resize((12, 12), Image.BILINEAR), np.float32) / 255.0
    mean = data.reshape(-1, 3).mean(axis=0)
    luma = float(mean @ np.array([0.2126, 0.7152, 0.0722]))
    if luma < 1e-3:
        return (0.85, 0.85, 0.85)
    return tuple(np.clip(mean / luma * min(luma * 1.15, 1.0), 0.25, 1.25))


def scene_lightmap(scene: Image.Image, sigma: float = 26.0) -> np.ndarray:
    """Размытая карта яркости кадра: деталь должна жить в том же свете.

    Без неё заливка выглядит ровной и «цифровой»: на стене с пятном света
    от софита деталь обязана темнеть к краю пятна, а не светиться одинаково.
    """
    data = np.asarray(scene.convert("RGB").resize((scene.width // 4, scene.height // 4),
                                                  Image.BILINEAR), np.float32) / 255.0
    luma = data @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    luma = gaussian_filter(luma, sigma / 4.0)
    mean = float(luma.mean()) or 1.0
    return np.clip((luma / mean) ** 0.85, 0.55, 1.35)


def _sample(lightmap: np.ndarray, quad, size) -> np.ndarray:
    """Вырезаем карту света под место детали и растягиваем на её размер."""
    height, width = lightmap.shape
    left, top, right, bottom = quad_center(quad)
    x0 = int(np.clip(left / 4, 0, width - 2))
    x1 = int(np.clip(right / 4, x0 + 1, width))
    y0 = int(np.clip(top / 4, 0, height - 2))
    y1 = int(np.clip(bottom / 4, y0 + 1, height))
    patch = Image.fromarray(np.clip(lightmap[y0:y1, x0:x1] * 255, 0, 255).astype(np.uint8))
    patch = patch.resize(size, Image.BICUBIC)
    return np.asarray(patch, np.float32) / 255.0


def _shift(mask: np.ndarray, dx: int, dy: int) -> np.ndarray:
    out = np.zeros_like(mask)
    height, width = mask.shape
    src_y0, src_y1 = max(0, -dy), min(height, height - dy)
    src_x0, src_x1 = max(0, -dx), min(width, width - dx)
    if src_y1 <= src_y0 or src_x1 <= src_x0:
        return out
    out[src_y0 + dy:src_y1 + dy, src_x0 + dx:src_x1 + dx] = mask[src_y0:src_y1, src_x0:src_x1]
    return out


def extrude(mask: np.ndarray, dx: float, dy: float, depth_px: int,
            tint: np.ndarray, ambient: float) -> tuple[np.ndarray, np.ndarray]:
    """Боковина детали: сдвигаем маску и запоминаем, на какой шаг она «вылезла».

    Возвращает (alpha боковины, цвет боковины). Цвет темнее полки — так читается
    толщина материала, и деталь перестаёт выглядеть плоской наклейкой.
    """
    height, width = mask.shape
    covered = mask.copy()
    side = np.zeros_like(mask)
    shade_map = np.zeros_like(mask)

    step_x = dx / max(depth_px, 1)
    step_y = dy / max(depth_px, 1)

    for step in range(1, depth_px + 1):
        shifted = _shift(mask, int(round(step_x * step)), int(round(step_y * step)))
        new = (shifted > 0.4) & (covered < 0.4)
        if not new.any():
            continue
        side[new] = 1.0
        shade_map[new] = 1.0 - (step - 1) / max(depth_px, 1)
        covered = np.maximum(covered, shifted)

    colour = tint[None, None, :] * (0.80 + 0.10 * shade_map)[..., None]
    return side, colour


def white_balance(scene: Image.Image) -> np.ndarray:
    """Оценка баланса белого кадра по самым светлым участкам.

    Белый ПВХ в тёплом зале выглядит тёплым, в холодном — холодным.
    Если красить его «как в палитре», он выпадает из кадра.
    """
    data = np.asarray(scene.convert("RGB").resize((160, 90), Image.BILINEAR), np.float32) / 255.0
    luma = data @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    threshold = np.quantile(luma, 0.92)
    sample = data[luma >= threshold]
    mean = sample.mean(axis=0) if len(sample) > 40 else data.reshape(-1, 3).mean(axis=0)
    mean = np.clip(mean, 0.05, 1.0)
    return mean / max(float(mean.mean()), 1e-6)


def place(
    scene: Image.Image,
    sprite: Image.Image,
    quad,
    *,
    light: tuple[float, float] = (-0.45, -0.35),
    thickness_px: float = 1.0,
    standoff_px: float = 0.0,
    shadow: float = 0.30,
    contact: float = 0.45,
    blur: float = 0.0,
    grain: float = 1.4,
    bounce: float = 0.10,
    edge_line: float = 0.0,
    strings=(),
) -> Image.Image:
    """Кладём деталь в четырёхугольник сцены.

    Тень считается не «на глаз», а от выноса от плоскости: деталь, прикрученная
    к стене вплотную, даёт только тонкое затемнение по кромке, а деталь на
    дистанционных держателях — мягкую тень со смещением.
    """
    canvas = scene.convert("RGBA")
    size = canvas.size

    left, top, right, bottom = quad_center(quad)
    target_w = max(8, int(right - left))
    target_h = max(8, int(bottom - top))
    if sprite.width > target_w * 1.15:
        scale = min(target_w / sprite.width, target_h / sprite.height)
        sprite = sprite.resize((max(8, int(sprite.width * scale)),
                                max(8, int(sprite.height * scale))), Image.LANCZOS)
    if blur > 0:
        sprite = sprite.filter(ImageFilter.GaussianBlur(blur))

    coeffs = _homography(quad, [(0, 0), (sprite.width, 0),
                                (sprite.width, sprite.height), (0, sprite.height)])
    warped = sprite.transform(size, Image.PERSPECTIVE, coeffs, Image.BICUBIC)
    alpha = np.asarray(warped.getchannel("A"), np.float32) / 255.0
    if not (alpha > 0.02).any():
        return scene

    # локальная яркость фона: деталь в тени не должна «светиться»
    patch = np.asarray(scene.crop((int(max(0, left)), int(max(0, top)),
                                   int(min(scene.width, right)), int(min(scene.height, bottom)))),
                       np.float32) / 255.0
    luma = float(patch.reshape(-1, 3).mean()) if patch.size else 0.8
    face = np.asarray(warped.convert("RGB"), np.float32)
    face = face * float(np.clip(0.62 + luma * 0.46, 0.55, 1.08))

    # тёплый/холодный сдвиг кадра — деталь живёт в том же свете
    balance = white_balance(scene)
    balance = 1.0 + (balance - 1.0) * 0.55
    face = face * balance[None, None, :]

    lightmap = scene_lightmap(scene)
    face = face * _sample(lightmap, quad, (face.shape[1], face.shape[0]))[..., None]

    # отражённый свет от окружения
    if bounce > 0 and patch.size:
        wall = patch.reshape(-1, 3).mean(axis=0) * 255.0
        face = face * (1.0 - bounce) + wall[None, None, :] * bounce

    base_px = np.asarray(canvas.convert("RGB"), np.float32)

    # 1. отброшенная тень: только если деталь вынесена от плоскости
    if standoff_px > 0.3 and shadow > 0:
        offset = standoff_px * 1.5
        dx = int(round(-light[0] * offset))
        dy = int(round(-light[1] * offset))
        cast = gaussian_filter(_shift(alpha, dx, dy), 1.2 + standoff_px * 0.9)
        base_px = base_px * (1.0 - np.clip(cast * shadow, 0, 1)[..., None])

    # 2. контактное затемнение: тонкая тёмная линия по кромке и мягкий ореол
    if contact > 0:
        tight = np.clip(alpha - gaussian_filter(alpha, 0.9), 0, 1)
        halo = np.clip(gaussian_filter(alpha, 2.6) - alpha, 0, 1)
        occlusion = np.clip(tight * 1.0 + halo * 0.55, 0, 1) * contact
        base_px = base_px * (1.0 - occlusion[..., None] * 0.55)

    # 3. боковина: реальная толщина материала в пикселях
    depth = int(round(thickness_px))
    if depth > 0:
        dir_x = -light[0] * 0.7
        dir_y = -light[1] * 0.7
        side, side_colour = extrude(alpha, dir_x * depth, dir_y * depth, depth,
                                    np.array([252.0, 250.0, 244.0]), ambient=0.8)
        base_px = base_px * (1.0 - side[..., None]) + side_colour * side[..., None]

    # 4. тёмная линия по кромке: тонкий зазор между деталью и плоскостью
    if edge_line > 0:
        outline = np.clip(alpha - gaussian_filter(alpha, 0.7), 0, 1)
        outline = np.clip(gaussian_filter(outline, 0.6) * edge_line, 0, 1)
        base_px = base_px * (1.0 - outline[..., None] * 0.55)

    # 5. лицевая часть
    base_px = base_px * (1.0 - alpha[..., None]) + face * alpha[..., None]

    canvas = Image.fromarray(np.clip(base_px, 0, 255).astype(np.uint8)).convert("RGBA")

    if strings:
        from PIL import ImageDraw

        draw = ImageDraw.Draw(canvas)
        for start_pt, end_pt in strings:
            draw.line([start_pt, end_pt], fill=(230, 228, 220, 195), width=1)

    if grain > 0:
        rgb = np.asarray(canvas.convert("RGB"), np.float32)
        rng = np.random.default_rng(11)
        noise = rng.normal(0.0, grain, (rgb.shape[0], rgb.shape[1], 1)).astype(np.float32)
        area = (alpha > 0.06)[..., None]
        rgb = np.where(area, rgb + noise, rgb)
        canvas = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).convert("RGBA")

    scene.paste(canvas.convert("RGB"))
    return scene


def load_scene(path, width: int, height: int) -> Image.Image:
    image = Image.open(path).convert("RGB")
    ratio = width / height
    if image.width / image.height > ratio:
        crop_w = int(image.height * ratio)
        left = (image.width - crop_w) // 2
        image = image.crop((left, 0, left + crop_w, image.height))
    else:
        crop_h = int(image.width / ratio)
        top = (image.height - crop_h) // 2
        image = image.crop((0, top, image.width, top + crop_h))
    return image.resize((width, height), Image.LANCZOS)
