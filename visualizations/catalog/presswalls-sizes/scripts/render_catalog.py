#!/usr/bin/env python3
"""Render the SM Production catalog on one locked photographic background.

The original 3 x 3 m face defines a projective coordinate system in meters.
Every size uses the same projection, ground origin, depth and background.
No per-product camera zoom, centering or automatic object-fit is performed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "references/sm-production-3x3-original.jpg"
BACKGROUND = ROOT / "assets/background-locked.png"
SIZES = [(2, 2), (2, 2.5), (3, 2), (3, 2.5), (4, 2.5), (4, 3), (5, 2.5), (5, 3)]
CANVAS = (1264, 848)
DEPTH_M = 0.20  # Visual depth calibrated to the reference's visible right return.
PPM = 360
SS = 2
FRONT_PX = np.float32([[294, 154], [899, 93], [900, 733], [294, 665]])
WORLD = np.float32([[-1.5, 3], [1.5, 3], [1.5, 0], [-1.5, 0]])
H = cv2.getPerspectiveTransform(WORLD, FRONT_PX)


def camera_matrix() -> np.ndarray:
    rows, rhs = [], []
    for y, (bx, by) in [(3, (944, 114)), (0, (944, 716))]:
        p = H @ np.array([1.5, y, 1.0])
        rows.extend([[1, 0, -bx], [0, 1, -by]])
        rhs.extend([bx * p[2] - p[0], by * p[2] - p[1]])
    q = np.linalg.lstsq(np.array(rows, float), np.array(rhs, float), rcond=None)[0]
    return np.column_stack([H[:, 0], H[:, 1], q / DEPTH_M, H[:, 2]])


P = camera_matrix()


def project(points: list[list[float]]) -> np.ndarray:
    p = np.asarray(points, float)
    homogeneous = np.column_stack([p, np.ones(len(p))])
    image = (P @ homogeneous.T).T
    return image[:, :2] / image[:, 2:]


def slug(number: float) -> str:
    return f"{number:g}".replace(".", "p")


def label(w: float, h: float) -> str:
    return f"{w:g} × {h:g} м".replace(".", ",")


def name_for(w: float, h: float) -> str:
    return f"sm-production-presswall-{slug(w)}x{slug(h)}"


def read_rgb(path: Path) -> np.ndarray:
    return np.array(Image.open(path).convert("RGB"))


def save_image(image: Image.Image, path: Path) -> None:
    if path.suffix == ".png":
        image.save(path, compress_level=9)
    elif path.suffix == ".jpg":
        image.save(path, quality=95, subsampling=0, progressive=True, optimize=True)
    elif path.suffix == ".webp":
        image.save(path, quality=92, method=6)
    else:
        raise ValueError(path.suffix)


def extract_print() -> tuple[np.ndarray, Image.Image, np.ndarray]:
    """Separate the approved print's background artwork and white/gold ink.

    Only the decorative background may be adapted to a new rectangular format.
    The extracted monogram, wordmark and tagline are always scaled uniformly.
    """
    source = read_rgb(SOURCE)
    n = 3 * PPM
    target = np.float32([[0, 0], [n - 1, 0], [n - 1, n - 1], [0, n - 1]])
    transform = cv2.getPerspectiveTransform(FRONT_PX, target)
    face = cv2.warpPerspective(source, transform, (n, n), flags=cv2.INTER_CUBIC)

    region = np.zeros((n, n), np.uint8)
    region[190:468, 333:708] = 255  # Cube/monogram.
    region[527:589, 280:759] = 255  # Wordmark.
    region[598:651, 280:759] = 255  # Tagline.
    low = face.min(axis=2).astype(float)
    high = face.max(axis=2).astype(float)
    spread = high - low
    white = (low > 100) & (spread < 62)
    r, g, b = (face[:, :, c].astype(float) for c in range(3))
    gold = (r > 102) & (r > b * 1.55) & (g > b * 1.2) & (r > g * 1.07)
    ink = ((white | gold) & (region > 0)).astype(np.uint8) * 255
    removal = cv2.dilate(ink, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
    pattern = cv2.inpaint(face, removal, 6, cv2.INPAINT_TELEA)

    source_luma = face.mean(axis=2).astype(float)
    base_luma = pattern.mean(axis=2).astype(float)
    alpha = np.clip((source_luma - base_luma) / np.maximum(232 - base_luma, 1), 0, 1)
    alpha *= removal > 0
    alpha[alpha < 0.035] = 0
    logo_rgb = np.full(face.shape, [233, 232, 226], dtype=np.uint8)
    gold_region = np.zeros((n, n), np.uint8)
    gold_region[527:589, 280:382] = 1
    gold_pixels = gold & (gold_region > 0)
    gold_zone = cv2.dilate(gold_pixels.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
    logo_rgb[gold_zone] = [201, 152, 57]
    gold_alpha = np.clip((r - pattern[:, :, 0].astype(float)) / np.maximum(201 - pattern[:, :, 0].astype(float), 1), 0, 1)
    alpha[gold_zone] = gold_alpha[gold_zone]
    alpha = np.clip(alpha, 0, 1)
    # Remove faint underlying network lines from inside the extracted cube mark.
    alpha[190:468, 333:708] = np.clip((alpha[190:468, 333:708] - 0.20) / 0.80, 0, 1)
    logo = Image.fromarray(np.dstack([logo_rgb, np.rint(alpha * 255).astype(np.uint8)]), "RGBA")
    logo = logo.crop((275, 185, 765, 657))

    side_points = np.float32([[899, 93], [944, 114], [944, 716], [900, 733]])
    side_w = round(DEPTH_M * PPM)
    side_target = np.float32([[0, 0], [side_w - 1, 0], [side_w - 1, n - 1], [0, n - 1]])
    side = cv2.warpPerspective(source, cv2.getPerspectiveTransform(side_points, side_target), (side_w, n), flags=cv2.INTER_CUBIC)
    # A locally restored, tone-matched print layer prevents old-logo ghosting
    # when the artwork and its separate brand mark use different aspect ratios.
    clean_art = read_rgb(ROOT / "assets/print-pattern-clean.png")
    assert clean_art.shape == face.shape
    return clean_art, logo, side


def face_texture(w: float, h: float, pattern: np.ndarray, logo: Image.Image) -> np.ndarray:
    tw, th = round(w * PPM), round(h * PPM)
    image = Image.fromarray(cv2.resize(pattern, (tw, th), interpolation=cv2.INTER_CUBIC)).convert("RGBA")
    factor = min(w, h) / 3
    lw, lh = round(logo.width * factor), round(logo.height * factor)
    mark = logo.resize((lw, lh), Image.Resampling.LANCZOS)
    x = round(tw * 0.48 - lw / 2)
    y = round(th * 0.39 - lh / 2)
    image.alpha_composite(mark, (x, y))
    return np.array(image.convert("RGB"))


def geometry(w: float, h: float) -> tuple[np.ndarray, np.ndarray]:
    front = project([[-w / 2, h, 0], [w / 2, h, 0], [w / 2, 0, 0], [-w / 2, 0, 0]])
    side = project([[w / 2, h, 0], [w / 2, h, DEPTH_M], [w / 2, 0, DEPTH_M], [w / 2, 0, 0]])
    return front, side


def shadow_mask(w: float, h: float) -> np.ndarray:
    iw, ih = CANVAS
    size = (iw * SS, ih * SS)
    # The same left-window light direction is used for every product.
    dx, dz = 0.50 * h, 0.67 * h
    floor = [[-w / 2, 0, 0], [w / 2, 0, 0], [w / 2, 0, DEPTH_M], [-w / 2, 0, DEPTH_M]]
    cast = [[x + dx, 0, z + dz] for x, _, z in floor]
    hull = cv2.convexHull(np.rint(project(floor + cast) * SS).astype(np.int32))
    hard = np.zeros((size[1], size[0]), np.uint8)
    cv2.fillConvexPoly(hard, hull, 255, lineType=cv2.LINE_AA)
    broad = cv2.GaussianBlur(hard, (0, 0), 7 * SS).astype(float) / 255 * 0.10
    core = cv2.GaussianBlur(hard, (0, 0), 2.0 * SS).astype(float) / 255 * 0.10
    contact = np.zeros_like(hard)
    base_points = np.rint(project(floor) * SS).astype(np.int32)
    cv2.polylines(contact, [base_points], True, 255, 5 * SS, cv2.LINE_AA)
    near = cv2.GaussianBlur(contact, (0, 0), 2 * SS).astype(float) / 255 * 0.26
    shadow = 1 - (1 - broad) * (1 - core) * (1 - near)
    shadow = cv2.resize(shadow, CANVAS, interpolation=cv2.INTER_AREA)
    # Quantization gives exact zero outside the local object/shadow edit area.
    return np.rint(shadow * 255).astype(np.uint8)


def projected_product(front: np.ndarray, side: np.ndarray, front_quad: np.ndarray, side_quad: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    iw, ih = CANVAS
    size = (iw * SS, ih * SS)
    premul = np.zeros((size[1], size[0], 3), np.float32)
    coverage = np.zeros((size[1], size[0]), np.float32)
    # Paint the side return first, then the front panel.
    for texture, quad in [(side, side_quad), (front, front_quad)]:
        th, tw = texture.shape[:2]
        source_quad = np.float32([[0, 0], [tw - 1, 0], [tw - 1, th - 1], [0, th - 1]])
        transform = cv2.getPerspectiveTransform(source_quad, np.float32(quad * SS))
        color = cv2.warpPerspective(texture, transform, size, flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE).astype(np.float32)
        alpha = cv2.warpPerspective(np.full((th, tw), 255, np.uint8), transform, size, flags=cv2.INTER_LINEAR).astype(np.float32) / 255
        premul = premul * (1 - alpha[:, :, None]) + color * alpha[:, :, None]
        coverage = coverage * (1 - alpha) + alpha
    premul = cv2.resize(premul, CANVAS, interpolation=cv2.INTER_AREA)
    coverage = cv2.resize(coverage, CANVAS, interpolation=cv2.INTER_AREA)
    return premul, coverage


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    filename = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{filename}", size)


def overview() -> None:
    tile_w, tile_h, caption, gap = 632, 424, 56, 24
    header = 132
    width = tile_w * 3 + gap * 4
    height = header + (tile_h + caption) * 3 + gap * 4
    board = Image.new("RGB", (width, height), "#f3f4f6")
    draw = ImageDraw.Draw(board)
    draw.text((gap, 22), "SM PRODUCTION / КАТАЛОГ КОНСТРУКЦИЙ", font=font(17, True), fill="#99752b")
    draw.text((gap, 50), "Брус-баннеры: единая серия размеров", font=font(32, True), fill="#17283d")
    draw.text((gap, 96), "Фиксированный фон и масштаб · ширина × высота, метры", font=font(19), fill="#576579")
    order = [(2, 2), (2, 2.5), (3, 2), (3, 2.5), (3, 3), (4, 2.5), (4, 3), (5, 2.5), (5, 3)]
    for i, (w, h) in enumerate(order):
        row, col = divmod(i, 3)
        x = gap + col * (tile_w + gap)
        y = header + gap + row * (tile_h + caption + gap)
        is_ref = (w, h) == (3, 3)
        path = SOURCE if is_ref else ROOT / f"{name_for(w, h)}.png"
        photo = Image.open(path).convert("RGB").resize((tile_w, tile_h), Image.Resampling.LANCZOS)
        board.paste(photo, (x, y))
        draw.rectangle((x, y + tile_h, x + tile_w - 1, y + tile_h + caption - 1), fill="white")
        draw.text((x + 18, y + tile_h + 14), label(w, h), font=font(24, True), fill="#17283d")
        if is_ref:
            draw.text((x + 186, y + tile_h + 19), "ИСХОДНЫЙ ЭТАЛОН", font=font(15, True), fill="#99752b")
            draw.rectangle((x, y, x + tile_w - 1, y + tile_h + caption - 1), outline="#b28b3a", width=2)
    save_image(board, ROOT / "sm-production-size-comparison.jpg")


def verify() -> None:
    manifest = json.loads((ROOT / "manifest.json").read_text())
    common = np.array(Image.open(ROOT / "assets/common-background-check-mask.png").convert("L")) > 0
    background = read_rgb(BACKGROUND)
    assert background.shape[:2] == (CANVAS[1], CANVAS[0])
    assert hashlib.sha256(BACKGROUND.read_bytes()).hexdigest() == manifest["background_sha256"]
    removal = np.array(Image.open(ROOT / "assets/reference-removal-mask.png").convert("L"))
    source = read_rgb(SOURCE)
    assert np.array_equal(background[removal == 0], source[removal == 0]), "Room changed outside restoration mask"
    assert common.sum() > 100000, "Insufficient unchanged background area"
    assert {(item["width_m"], item["height_m"]) for item in manifest["items"]} == set(SIZES)
    assert np.allclose(geometry(3, 3)[0], FRONT_PX, atol=0.001), "Reference scale mismatch"
    for item in manifest["items"]:
        for ext, filename in item["files"].items():
            with Image.open(ROOT / filename) as image:
                assert image.size == CANVAS, (filename, image.size)
                image.verify()
        png = read_rgb(ROOT / item["files"]["png"])
        assert np.array_equal(png[common], background[common]), item["id"]
        # Projecting the same known physical dimensions must reproduce the saved corners.
        front, side = geometry(item["width_m"], item["height_m"])
        assert np.allclose(front, item["front_quad_px"], atol=0.001)
        assert np.allclose(side, item["side_quad_px"], atol=0.001)
        for quad in (front, side):
            assert np.all((quad[:, 0] >= 0) & (quad[:, 0] < CANVAS[0])), "Product clipped horizontally"
            assert np.all((quad[:, 1] >= 0) & (quad[:, 1] < CANVAS[1])), "Product clipped vertically"
    print(f"Verified {len(manifest['items'])} sizes / 24 image files; {int(common.sum()):,} shared background pixels are bit-identical in every PNG.")


def render() -> None:
    background = read_rgb(BACKGROUND)
    assert (background.shape[1], background.shape[0]) == CANVAS
    pattern, logo, side_source = extract_print()
    logo.save(ROOT / "assets/branding-extracted.png", compress_level=9)
    union = np.zeros((CANVAS[1], CANVAS[0]), bool)
    items = []
    for w, h in SIZES:
        base = name_for(w, h)
        front_quad, side_quad = geometry(w, h)
        front = face_texture(w, h, pattern, logo)
        side = cv2.resize(side_source, (round(DEPTH_M * PPM), round(h * PPM)), interpolation=cv2.INTER_CUBIC)
        foreground, alpha = projected_product(front, side, front_quad, side_quad)
        shadow = shadow_mask(w, h)
        shaded = background.astype(float) * (1 - shadow[:, :, None].astype(float) / 255)
        result = np.rint(shaded * (1 - alpha[:, :, None]) + foreground).clip(0, 255).astype(np.uint8)
        local_edit = (alpha > 0) | (shadow > 0)
        assert np.array_equal(result[~local_edit], background[~local_edit])
        union |= local_edit
        files = {}
        for ext in ("png", "jpg", "webp"):
            filename = f"{base}.{ext}"
            save_image(Image.fromarray(result), ROOT / filename)
            files[ext] = filename
        items.append({
            "id": f"{slug(w)}x{slug(h)}", "label": label(w, h),
            "width_m": w, "height_m": h, "depth_m_visual_assumption": DEPTH_M,
            "pixel_width": CANVAS[0], "pixel_height": CANVAS[1], "files": files,
            "front_quad_px": np.round(front_quad, 6).tolist(),
            "side_quad_px": np.round(side_quad, 6).tolist(),
        })
        print(f"Rendered {label(w, h)}: {base}")
    common = (~union).astype(np.uint8) * 255
    Image.fromarray(common).save(ROOT / "assets/common-background-check-mask.png", compress_level=9)
    manifest = {
        "title": "SM Production — catalog presswall sizes", "dimension_order": "width x height, meters",
        "canvas_px": list(CANVAS), "reference_size_m": [3, 3],
        "reference": str(SOURCE.relative_to(ROOT)), "background": str(BACKGROUND.relative_to(ROOT)),
        "background_sha256": hashlib.sha256(BACKGROUND.read_bytes()).hexdigest(),
        "camera_policy": "Fixed projective camera and floor origin. No per-item camera zoom, crop or auto-fit.",
        "front_homography_world_m_to_pixels": H.tolist(), "camera_matrix": P.tolist(),
        "floor_origin_px": project([[0, 0, 0]])[0].tolist(),
        "brand_policy": "Original white/gold ink extracted from supplied image; isotropic logo scaling, independent decorative-artwork adaptation.",
        "common_background_pixels": int((~union).sum()), "items": items,
    }
    (ROOT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    overview()
    verify()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Validate existing image outputs without regenerating")
    args = parser.parse_args()
    verify() if args.check else render()
