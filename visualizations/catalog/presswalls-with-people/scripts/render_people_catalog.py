#!/usr/bin/env python3
"""Add the same calibrated 160 cm woman and 185 cm man to eight catalog images.

The approved empty images are read-only inputs. One shared people layer is
projected using their existing camera calibration, never resized per product.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import zipfile

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT.parent / "presswalls-sizes"
ASSETS = ROOT / "assets"
CANVAS = (1264, 848)
SS = 2
FRONT_OFFSET = -0.35
# Frame the central branding while keeping both people in front of the 2 m wall.
FOOT_X = {"woman": 430.0, "man": 690.0}
BASE_MANIFEST = json.loads((BASE / "manifest.json").read_text())
PEOPLE_ASSETS = json.loads((ASSETS / "people-assets.json").read_text())
P = np.array(BASE_MANIFEST["camera_matrix"], float)
K = -P[2, 0] / P[2, 2]


def rgb(path: Path) -> np.ndarray:
    return np.array(Image.open(path).convert("RGB"))


def project(points: list[list[float]]) -> np.ndarray:
    p = np.asarray(points, float)
    q = (P @ np.column_stack([p, np.ones(len(p))]).T).T
    return q[:, :2] / q[:, 2:]


def source_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_image(image: Image.Image, path: Path) -> None:
    if path.suffix == ".png":
        image.save(path, compress_level=9)
    elif path.suffix == ".jpg":
        image.save(path, quality=95, subsampling=0, optimize=True, progressive=True)
    elif path.suffix == ".webp":
        image.save(path, quality=92, method=6)
    else:
        raise ValueError(path.suffix)


def placement(asset: dict) -> dict:
    # Pick an X,Z point on a line of equal camera depth. This avoids enlarging
    # the man just because he is on the nearer side of the original oblique wall.
    denominator = 1 + P[2, 2] * FRONT_OFFSET
    slope = (P[0, 0] + P[0, 2] * K) / denominator
    intercept = (P[0, 2] * FRONT_OFFSET + P[0, 3]) / denominator
    x = (FOOT_X[asset["id"]] - intercept) / slope
    z = FRONT_OFFSET + K * x
    assert z < 0, "The person must stand in front of the photozone"
    height = asset["height_m"]
    head, foot = project([[x, height, z], [x, 0, z]])
    vertical = foot - head
    scale = np.linalg.norm(vertical) / (asset["ground_y_px"] - asset["crown_y_px"])
    v = vertical / np.linalg.norm(vertical)
    horizontal = np.array([v[1], -v[0]])
    linear = np.column_stack([horizontal, v]) * scale
    crown = np.array([asset["ground_anchor_x_px"], asset["crown_y_px"]])
    transform = np.column_stack([linear, head - linear @ crown])
    return {
        **asset, "world_foot_m": [float(x), 0.0, float(z)],
        "head_px": head.tolist(), "foot_px": foot.tolist(),
        "height_px": float(np.linalg.norm(vertical)), "uniform_scale": float(scale),
        "transform": transform.tolist(), "screen_x_per_world_x": float(slope),
    }


def people_layers() -> tuple[np.ndarray, np.ndarray, np.ndarray, list[dict]]:
    w, h = CANVAS
    hi_size = (w * SS, h * SS)
    premul = np.zeros((h * SS, w * SS, 3), np.float32)
    coverage = np.zeros((h * SS, w * SS), np.float32)
    floor = np.zeros((h * SS, w * SS), np.float32)
    placements = []
    for asset in PEOPLE_ASSETS["assets"]:
        spec = placement(asset)
        placements.append(spec)
        image = np.array(Image.open(ASSETS / asset["file"]).convert("RGBA"))
        alpha = image[:, :, 3].astype(np.float32) / 255
        color = image[:, :, :3].astype(np.float32) * alpha[:, :, None]
        matrix = np.array(spec["transform"], np.float32)
        large = matrix.copy() * SS
        pm = cv2.warpAffine(color, large, hi_size, flags=cv2.INTER_CUBIC)
        am = np.clip(cv2.warpAffine(alpha, large, hi_size, flags=cv2.INTER_CUBIC), 0, 1)
        pm = np.clip(pm, 0, am[:, :, None] * 255)
        premul = premul * (1 - am[:, :, None]) + pm
        coverage = coverage * (1 - am) + am

        # Project the silhouette onto the floor using one left-window light.
        sh, sw = alpha.shape
        x, _, z = spec["world_foot_m"]
        per_source_x = spec["uniform_scale"] / spec["screen_x_per_world_x"]
        dx_left = -asset["ground_anchor_x_px"] * per_source_x
        dx_right = (sw - 1 - asset["ground_anchor_x_px"]) * per_source_x
        height = asset["height_m"]
        light_x, light_z = 0.45 * height, 0.65 * height
        ground_quad = project([
            [x + dx_left + light_x, 0, z + K * dx_left + light_z],
            [x + dx_right + light_x, 0, z + K * dx_right + light_z],
            [x + dx_right, 0, z + K * dx_right],
            [x + dx_left, 0, z + K * dx_left],
        ])
        source_quad = np.float32([
            [0, asset["crown_y_px"]], [sw - 1, asset["crown_y_px"]],
            [sw - 1, asset["ground_y_px"]], [0, asset["ground_y_px"]],
        ])
        H = cv2.getPerspectiveTransform(source_quad, np.float32(ground_quad * SS))
        cast = cv2.warpPerspective(alpha, H, hi_size, flags=cv2.INTER_LINEAR)
        cast = cv2.GaussianBlur(cast, (0, 0), 4.0 * SS) * 0.16
        floor = 1 - (1 - floor) * (1 - cast)

        # Two subtle contact patches follow the actual shoes, not a generic oval.
        bottom = (alpha > 0.3).astype(np.uint8)
        bottom[:max(0, asset["ground_y_px"] - 35)] = 0
        n, labels, stats, centers = cv2.connectedComponentsWithStats(bottom, 8)
        shoe_ids = sorted(range(1, n), key=lambda i: stats[i, cv2.CC_STAT_AREA], reverse=True)[:2]
        contact = np.zeros_like(floor)
        for shoe_id in shoe_ids:
            ys, xs = np.where(labels == shoe_id)
            center_source = np.array([float(xs.mean()), float(ys.max()), 1.0])
            center = matrix @ center_source
            radius_x = max(4, (xs.max() - xs.min()) * spec["uniform_scale"] * 0.56)
            cv2.ellipse(contact, tuple(np.rint((center + [0, 1]) * SS).astype(int)),
                        (round(radius_x * SS), 3 * SS), 0, 0, 360, 0.32, -1, cv2.LINE_AA)
        contact = cv2.GaussianBlur(contact, (0, 0), 1.2 * SS)
        floor = 1 - (1 - floor) * (1 - contact)

    premul = cv2.resize(premul, CANVAS, interpolation=cv2.INTER_AREA)
    coverage = np.clip(cv2.resize(coverage, CANVAS, interpolation=cv2.INTER_AREA), 0, 1)
    # Save one reusable transparent pair layer for this series and future builds.
    straight = np.zeros_like(premul)
    visible = coverage > 0.001
    straight[visible] = premul[visible] / coverage[visible, None]
    rgba = np.dstack([np.rint(straight).clip(0, 255).astype(np.uint8), np.rint(coverage * 255).astype(np.uint8)])
    Image.fromarray(rgba).save(ASSETS / "people-layer-160-185.png", compress_level=9)
    coverage = rgba[:, :, 3].astype(np.float32) / 255
    premul = rgba[:, :, :3].astype(np.float32) * coverage[:, :, None]
    floor = np.clip(cv2.resize(floor, CANVAS, interpolation=cv2.INTER_AREA), 0, 1)
    floor_u8 = np.rint(floor * 255).astype(np.uint8)
    Image.fromarray(floor_u8).save(ASSETS / "people-floor-shadow.png", compress_level=9)
    wall = cv2.warpAffine(coverage, np.float32([[1, 0, 14], [0, 1, 4]]), CANVAS, flags=cv2.INTER_LINEAR)
    wall = cv2.GaussianBlur(wall, (0, 0), 4.5) * 0.14
    wall_u8 = np.rint(wall * 255).astype(np.uint8)
    Image.fromarray(wall_u8).save(ASSETS / "people-wall-shadow.png", compress_level=9)
    return premul, coverage, floor_u8, placements


def quad_mask(quad: list[list[float]]) -> np.ndarray:
    mask = np.zeros((CANVAS[1] * SS, CANVAS[0] * SS), np.uint8)
    cv2.fillConvexPoly(mask, np.rint(np.array(quad) * SS).astype(np.int32), 255, cv2.LINE_AA)
    return cv2.resize(mask, CANVAS, interpolation=cv2.INTER_AREA).astype(float) / 255


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    filename = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{filename}", size)


def overview(items: list[dict]) -> None:
    tw, th, caption, gap, header = 632, 424, 56, 24, 144
    width = 2 * tw + 3 * gap
    height = header + 4 * (th + caption) + 5 * gap
    board = Image.new("RGB", (width, height), "#f3f4f6")
    draw = ImageDraw.Draw(board)
    draw.text((gap, 20), "SM PRODUCTION / ФОТОЗОНЫ С ЛЮДЬМИ", font=font(17, True), fill="#99752b")
    draw.text((gap, 49), "Девушка 160 см · мужчина 185 см", font=font(31, True), fill="#17283d")
    draw.text((gap, 98), "Одна пара, фон и камера · размеры конструкции: ширина × высота", font=font(18), fill="#576579")
    for i, item in enumerate(items):
        row, col = divmod(i, 2)
        x = gap + col * (tw + gap)
        y = header + gap + row * (th + caption + gap)
        image = Image.open(ROOT / item["files"]["png"]).convert("RGB").resize((tw, th), Image.Resampling.LANCZOS)
        board.paste(image, (x, y))
        draw.rectangle((x, y + th, x + tw - 1, y + th + caption - 1), fill="white")
        draw.text((x + 18, y + th + 14), item["label"], font=font(24, True), fill="#17283d")
    save_image(board, ROOT / "sm-production-people-size-comparison.jpg")


def verify() -> None:
    manifest = json.loads((ROOT / "manifest.json").read_text())
    edit = np.array(Image.open(ASSETS / "series-people-edit-mask.png").convert("L")) > 0
    people = np.array(Image.open(ASSETS / "people-layer-160-185.png").convert("RGBA"))
    opaque = people[:, :, 3] == 255
    assert len(manifest["items"]) == 8
    assert len(manifest["people"]) == 2
    assert {p["height_m"] for p in manifest["people"]} == {1.6, 1.85}
    baseline_people = None
    for spec in manifest["people"]:
        x, _, z = spec["world_foot_m"]
        head, foot = project([[x, spec["height_m"], z], [x, 0, z]])
        assert z < 0
        assert np.allclose(head, spec["head_px"], atol=0.001)
        assert np.allclose(foot, spec["foot_px"], atol=0.001)
        transform = np.array(spec["transform"])
        assert np.allclose(transform @ [spec["ground_anchor_x_px"], spec["crown_y_px"], 1], head)
        assert np.allclose(transform @ [spec["ground_anchor_x_px"], spec["ground_y_px"], 1], foot)
        s = transform[:, :2].T @ transform[:, :2]
        assert np.allclose(s, np.eye(2) * spec["uniform_scale"] ** 2), "Non-uniform human scaling"
    n, components, stats, centers = cv2.connectedComponentsWithStats((people[:, :, 3] > 76).astype(np.uint8), 8)
    ids = sorted(range(1, n), key=lambda i: stats[i, cv2.CC_STAT_AREA], reverse=True)[:2]
    ids.sort(key=lambda i: centers[i, 0])
    assert len(ids) == 2, "Expected two separate full-length figures"
    for spec, component in zip(manifest["people"], ids):
        ys, _ = np.where(components == component)
        assert abs(float(ys.min()) - spec["head_px"][1]) < 2, "Visible crown misaligned"
        assert abs(float(ys.max()) - spec["foot_px"][1]) < 2, "Visible sole misaligned"
    for item in manifest["items"]:
        source = BASE / item["source_png"]
        assert source_hash(source) == item["source_sha256"], "An approved empty render changed"
        base = rgb(source)
        for filename in item["files"].values():
            with Image.open(ROOT / filename) as image:
                assert image.size == CANVAS
                image.verify()
        image = rgb(ROOT / item["files"]["png"])
        assert np.array_equal(image[~edit], base[~edit]), item["id"]
        assert np.array_equal(image[opaque], people[:, :, :3][opaque]), "People layer mismatch"
        if baseline_people is None:
            baseline_people = image[opaque]
        else:
            assert np.array_equal(image[opaque], baseline_people), "People changed between products"
    print(f"Verified 8 sizes / 24 image files. All {int((~edit).sum()):,} pixels outside people/shadows retain each approved source exactly.")
    print(f"The same {int(opaque.sum()):,} opaque figure pixels are identical in all 8 PNGs. Heights: 160 and 185 cm, projected with the original camera.")


def package(items: list[dict]) -> None:
    archive = ROOT / "sm-production-presswalls-with-people.zip"
    paths = [ROOT / filename for item in items for filename in item["files"].values()]
    paths += [ROOT / "sm-production-people-size-comparison.jpg", ROOT / "manifest.json", ROOT / "DOWNLOAD-NOTES.txt"]
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for path in paths:
            z.write(path, path.name)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert len(z.namelist()) == 27
    print(f"Archive verified: {archive.name}, {archive.stat().st_size:,} bytes.")


def render() -> None:
    premul, alpha, floor_u8, people = people_layers()
    floor = floor_u8.astype(float) / 255
    wall = np.array(Image.open(ASSETS / "people-wall-shadow.png").convert("L")).astype(float) / 255
    edit = alpha > 0
    items = []
    for source in BASE_MANIFEST["items"]:
        path = BASE / source["files"]["png"]
        approved = rgb(path)
        front = quad_mask(source["front_quad_px"])
        side = quad_mask(source["side_quad_px"])
        product = np.maximum(front, side)
        # Ground shadows do not paint over the product; soft wall shadows stay on its face.
        shadow = 1 - (1 - floor * (1 - product)) * (1 - wall * front)
        shadow = np.rint(shadow * 255).astype(np.uint8)
        shade = shadow.astype(float) / 255
        shaded = approved.astype(float) * (1 - shade[:, :, None])
        image = np.rint(shaded * (1 - alpha[:, :, None]) + premul).clip(0, 255).astype(np.uint8)
        local = (alpha > 0) | (shadow > 0)
        assert np.array_equal(image[~local], approved[~local])
        edit |= local
        stem = Path(source["files"]["png"]).stem + "-people"
        files = {}
        for ext in ("png", "jpg", "webp"):
            filename = f"{stem}.{ext}"
            save_image(Image.fromarray(image), ROOT / filename)
            files[ext] = filename
        items.append({
            "id": source["id"], "label": source["label"],
            "width_m": source["width_m"], "height_m": source["height_m"],
            "canvas_px": list(CANVAS), "source_png": path.name,
            "source_sha256": source_hash(path), "files": files,
        })
        print(f"Rendered {source['label']} with the fixed 160/185 cm pair.")
    Image.fromarray(edit.astype(np.uint8) * 255).save(ASSETS / "series-people-edit-mask.png", compress_level=9)
    manifest = {
        "title": "SM Production — eight presswalls with a 160 cm woman and 185 cm man",
        "dimension_order": "width x height, meters", "canvas_px": list(CANVAS),
        "source_series": "../presswalls-sizes", "original_reference_size_m": [3, 3],
        "camera_matrix": P.tolist(),
        "people_policy": "One pair of fictional adults, a fixed ground position and fixed isotropic scale in every frame. Heights calibrated crown-to-sole using the existing projective camera. Woman wears flat shoes.",
        "people": people, "pixels_outside_people_and_shadows": int((~edit).sum()), "items": items,
    }
    (ROOT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    overview(items)
    verify()
    package(items)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Validate existing images without rendering")
    args = parser.parse_args()
    verify() if args.check else render()
