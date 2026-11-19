#!/usr/bin/env python3
"""Four Joker tube-frame catalog images on the approved photographic set.

The room, projective camera, brand ink and calibrated people are reused from
previous catalog series. The Joker is rebuilt as an open, thin metal frame,
with an inset eyeleted banner, individual ties and two transverse tube feet.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import zipfile

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT.parent
BASE = CATALOG / "presswalls-sizes"
HUMANS = CATALOG / "presswalls-with-people"
ASSETS = ROOT / "assets"
CALIBRATION = json.loads((BASE / "manifest.json").read_text())
PEOPLE_METADATA = json.loads((HUMANS / "manifest.json").read_text())["people"]
P = np.array(CALIBRATION["camera_matrix"], float)
CANVAS = (1264, 848)
SS = 3
PPM = 360
SIZES = [(2.0, 2.0), (3.0, 2.5), (3.0, 3.0), (4.0, 3.0)]
TUBE_DIAMETER = 0.025
RADIUS = TUBE_DIAMETER / 2
BANNER_INSET = 0.055
BANNER_BOTTOM = 0.10
LOWER_BAR_Y = 0.045
FOOT_FRONT_Z = -0.18
FOOT_BACK_Z = 0.12
TIE_SPACING = 0.30
EYELET_RADIUS = 0.009


def read_rgb(path: Path) -> np.ndarray:
    return np.array(Image.open(path).convert("RGB"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def project(points: list[list[float]] | np.ndarray) -> np.ndarray:
    points = np.asarray(points, float)
    q = (P @ np.column_stack([points, np.ones(len(points))]).T).T
    return q[:, :2] / q[:, 2:]


def slug(value: float) -> str:
    return f"{value:g}".replace(".", "p")


def label(w: float, h: float) -> str:
    return f"{w:g} × {h:g} м".replace(".", ",")


def stem(w: float, h: float) -> str:
    return f"sm-production-joker-{slug(w)}x{slug(h)}-people"


def save_image(image: Image.Image, path: Path) -> None:
    if path.suffix == ".png":
        image.save(path, compress_level=9)
    elif path.suffix == ".jpg":
        image.save(path, quality=95, subsampling=0, optimize=True, progressive=True)
    elif path.suffix == ".webp":
        image.save(path, quality=92, method=6)
    else:
        raise ValueError(path.suffix)


def quad_alpha(quad: np.ndarray) -> np.ndarray:
    mask = np.zeros((CANVAS[1] * SS, CANVAS[0] * SS), np.uint8)
    cv2.fillConvexPoly(mask, np.rint(quad * SS).astype(np.int32), 255, cv2.LINE_AA)
    return cv2.resize(mask, CANVAS, interpolation=cv2.INTER_AREA).astype(float) / 255


def positions(low: float, high: float, margin: float = 0.055) -> np.ndarray:
    start, end = low + margin, high - margin
    count = max(2, int(math.ceil((end - start) / TIE_SPACING)) + 1)
    return np.linspace(start, end, count)


def banner_geometry(w: float, h: float) -> tuple[float, float, float, float]:
    return -w / 2 + BANNER_INSET, w / 2 - BANNER_INSET, BANNER_BOTTOM, h - BANNER_INSET


def banner_texture(w: float, h: float) -> np.ndarray:
    left, right, bottom, top = banner_geometry(w, h)
    pw, ph = right - left, top - bottom
    tw, th = round(pw * PPM), round(ph * PPM)
    pattern = Image.open(BASE / "assets/print-pattern-clean.png").convert("RGB")
    image = pattern.resize((tw, th), Image.Resampling.LANCZOS).convert("RGBA")
    # Reuse the supplied brand block without any independent X/Y stretching.
    logo = Image.open(BASE / "assets/branding-extracted.png").convert("RGBA")
    factor = min(w, h) / 3
    lw, lh = round(logo.width * factor), round(logo.height * factor)
    image.alpha_composite(logo.resize((lw, lh), Image.Resampling.LANCZOS),
                          (round(tw * 0.48 - lw / 2), round(th * 0.39 - lh / 2)))
    array = np.array(image.convert("RGB")).astype(float)
    # Soft, localized tension creases stop the print from looking like a rigid box.
    yy, xx = np.mgrid[:th, :tw]
    shade = np.zeros((th, tw), float)
    for x in positions(left, right):
        u = (x - left) / pw * (tw - 1)
        line = np.exp(-((xx - u) / 3.2) ** 2)
        shade += line * (np.exp(-yy / 17) + np.exp(-(th - 1 - yy) / 17)) * 0.032
    for y in positions(bottom, top):
        v = (top - y) / ph * (th - 1)
        line = np.exp(-((yy - v) / 3.2) ** 2)
        shade += line * (np.exp(-xx / 17) + np.exp(-(tw - 1 - xx) / 17)) * 0.032
    array *= (1 - shade[:, :, None])
    # A thin welded/stitched hem, not a thick side return or plinth.
    hem = np.minimum.reduce([xx, yy, tw - 1 - xx, th - 1 - yy])
    array[hem < 1.2] *= 0.76
    array[(hem >= 4) & (hem < 5)] *= 1.045
    return np.rint(array).clip(0, 255).astype(np.uint8)


class Hardware:
    """Small polished cylinders, collars, ties and eyelets, supersampled in place."""
    def __init__(self, image: Image.Image):
        self.image = image
        self.draw = ImageDraw.Draw(image)

    def px(self, points: np.ndarray) -> list[tuple[float, float]]:
        return [tuple(p * SS) for p in points]

    def tube(self, a: list[float], b: list[float], diameter: float = TUBE_DIAMETER, rubber: bool = False) -> None:
        pts = np.array([a, b], float)
        pp = project(pts)
        direction = pp[1] - pp[0]
        length = np.linalg.norm(direction)
        if length < 0.01:
            return
        normal = np.array([-direction[1], direction[0]]) / length
        if normal @ np.array([-0.8, -0.6]) < 0:
            normal *= -1
        axis = np.abs(pts[1] - pts[0])
        radial = np.array([diameter / 2, 0, 0]) if axis[1] > max(axis[0], axis[2]) else np.array([0, diameter / 2, 0])
        radii = np.linalg.norm(project(pts + radial) - project(pts - radial), axis=1) / 2
        radii = np.maximum(radii, 0.8)
        outer = [pp[0] - normal * (radii[0] + .12), pp[1] - normal * (radii[1] + .12),
                 pp[1] + normal * (radii[1] + .12), pp[0] + normal * (radii[0] + .12)]
        self.draw.polygon(self.px(np.array(outer)), fill=(48, 54, 57, 255))
        # Reflected dark room bands and a narrow daylight highlight on cylindrical metal.
        knots = np.array([-1, -.82, -.62, -.42, -.22, -.04, .12, .28, .42, .55, .70, .85, 1.])
        values = np.array([53, 120, 178, 104, 64, 84, 170, 231, 250, 211, 148, 173, 65.])
        if rubber:
            values = np.array([24, 34, 45, 48, 42, 39, 44, 59, 65, 56, 44, 38, 24.])
        bands = np.linspace(-1, 1, 43)
        for t0, t1 in zip(bands, bands[1:]):
            value = float(np.interp((t0 + t1) / 2, knots, values))
            color = (round(value * .98), round(value * .995), round(min(255, value * 1.015)), 255)
            quad = np.array([pp[0] + normal * radii[0] * t0, pp[1] + normal * radii[1] * t0,
                             pp[1] + normal * radii[1] * t1, pp[0] + normal * radii[0] * t1])
            self.draw.polygon(self.px(quad), fill=color)

    def joint(self, point: list[float], screw: bool = True) -> None:
        p = project([point])[0]
        x, y, z = point
        diameter_px = np.linalg.norm(project([[x - .018, y, z], [x + .018, y, z]])[1] -
                                     project([[x - .018, y, z], [x + .018, y, z]])[0])
        r = max(2.4, diameter_px * .53)
        self.draw.ellipse(((p[0] - r) * SS, (p[1] - r) * SS, (p[0] + r) * SS, (p[1] + r) * SS), fill=(71, 78, 81, 255))
        self.draw.ellipse(((p[0] - r + .55) * SS, (p[1] - r + .4) * SS, (p[0] + r - .45) * SS, (p[1] + r - .5) * SS), fill=(174, 181, 184, 255))
        self.draw.arc(((p[0] - r + .5) * SS, (p[1] - r + .5) * SS, (p[0] + r - .5) * SS, (p[1] + r - .5) * SS), 200, 305, fill=(247, 248, 238, 255), width=SS)
        if screw:
            self.draw.ellipse(((p[0] + .1) * SS, (p[1] - .7) * SS, (p[0] + 1.6) * SS, (p[1] + .8) * SS), fill=(49, 55, 58, 255))

    def eyelet(self, point: list[float]) -> None:
        x, y, z = point
        p = project([point])[0]
        hx = project([[x - EYELET_RADIUS, y, z], [x + EYELET_RADIUS, y, z]])
        vy = project([[x, y - EYELET_RADIUS, z], [x, y + EYELET_RADIUS, z]])
        rx = max(.9, np.linalg.norm(hx[1] - hx[0]) / 2)
        ry = max(.9, np.linalg.norm(vy[1] - vy[0]) / 2)
        bbox = ((p[0] - rx) * SS, (p[1] - ry) * SS, (p[0] + rx) * SS, (p[1] + ry) * SS)
        self.draw.ellipse(bbox, fill=(86, 96, 104, 255))
        self.draw.ellipse(((p[0] - rx + .3) * SS, (p[1] - ry + .3) * SS, (p[0] + rx - .25) * SS, (p[1] + ry - .25) * SS), fill=(209, 212, 207, 255))
        self.draw.ellipse(((p[0] - rx * .40) * SS, (p[1] - ry * .40) * SS, (p[0] + rx * .40) * SS, (p[1] + ry * .40) * SS), fill=(57, 65, 73, 255))

    def tether(self, pipe: list[float], eye: list[float]) -> None:
        a, c = project([pipe, eye])
        v = c - a
        normal = np.array([-v[1], v[0]]) / max(np.linalg.norm(v), 1)
        midpoint = (a + c) / 2 + normal * 1.0
        path = []
        for t in np.linspace(0, 1, 11):
            path.append((1-t)**2*a + 2*(1-t)*t*midpoint + t*t*c)
        # Pale individual tension ties; no giant rope lattice or closed frame face.
        self.draw.line(self.px(np.array(path)), fill=(92, 96, 95, 255), width=max(2, round(.95 * SS)), joint="curve")
        self.draw.line(self.px(np.array(path) - normal * .15), fill=(222, 222, 207, 255), width=max(1, round(.55 * SS)), joint="curve")
        # A small wrap around the tube at each attachment point.
        wrap = [a - normal * 1.65 - v * .09, a + normal * 1.65 - v * .09, a + normal * 1.65 + v * .08]
        self.draw.line(self.px(np.array(wrap)), fill=(210, 213, 201, 255), width=max(1, round(.55 * SS)))
        self.eyelet(eye)


def render_product(w: float, h: float) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict]:
    size = (CANVAS[0] * SS, CANVAS[1] * SS)
    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    hardware = Hardware(canvas)
    axis_x = [-w / 2 + RADIUS, w / 2 - RADIUS]
    # Transverse T-feet, present in the reference; no plinth or banner box.
    feet = []
    for x in axis_x:
        a, b = [x, RADIUS, FOOT_FRONT_Z], [x, RADIUS, FOOT_BACK_Z]
        hardware.tube(a, b)
        for z, sign in [(FOOT_FRONT_Z, 1), (FOOT_BACK_Z, -1)]:
            hardware.tube([x, RADIUS, z], [x, RADIUS, z + sign * .014], diameter=.028, rubber=True)
        feet += [a, b]

    left, right, bottom, top = banner_geometry(w, h)
    banner_quad = project([[left, top, 0], [right, top, 0], [right, bottom, 0], [left, bottom, 0]])
    texture = banner_texture(w, h)
    th, tw = texture.shape[:2]
    source_quad = np.float32([[0, 0], [tw - 1, 0], [tw - 1, th - 1], [0, th - 1]])
    transform = cv2.getPerspectiveTransform(source_quad, np.float32(banner_quad * SS))
    color = cv2.warpPerspective(texture, transform, size, flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    alpha = cv2.warpPerspective(np.full((th, tw), 255, np.uint8), transform, size, flags=cv2.INTER_LINEAR)
    canvas.alpha_composite(Image.fromarray(np.dstack([color, alpha])))
    hardware = Hardware(canvas)
    # Keep the tube diameter constant in meters across all sizes.
    for x in axis_x:
        hardware.tube([x, RADIUS, 0], [x, h - RADIUS, 0])
    hardware.tube([axis_x[0], h - RADIUS, 0], [axis_x[1], h - RADIUS, 0])
    hardware.tube([axis_x[0], LOWER_BAR_Y, 0], [axis_x[1], LOWER_BAR_Y, 0])
    for x in axis_x:
        hardware.joint([x, h - RADIUS, 0])
        hardware.joint([x, LOWER_BAR_Y, 0])
        # Small post collars read as modular Joker hardware, not structural walls.
        if h >= 2.5:
            hardware.tube([x, 1.45, 0], [x, 1.475, 0], diameter=.031)

    tie_count = 0
    for x in positions(left, right):
        hardware.tether([x, h - RADIUS, 0], [x, top - .014, 0])
        hardware.tether([x, LOWER_BAR_Y, 0], [x, bottom + .014, 0])
        tie_count += 2
    for y in positions(bottom, top):
        hardware.tether([axis_x[0], y, 0], [left + .014, y, 0])
        hardware.tether([axis_x[1], y, 0], [right - .014, y, 0])
        tie_count += 2

    rgba = np.array(canvas)
    a_hi = rgba[:, :, 3].astype(np.float32) / 255
    pm_hi = rgba[:, :, :3].astype(np.float32) * a_hi[:, :, None]
    pm = cv2.resize(pm_hi, CANVAS, interpolation=cv2.INTER_AREA)
    a = cv2.resize(a_hi, CANVAS, interpolation=cv2.INTER_AREA)
    banner_mask = quad_alpha(banner_quad)
    info = {
        "outer_frame_quad_px": np.round(project([[-w/2, h, 0], [w/2, h, 0], [w/2, 0, 0], [-w/2, 0, 0]]), 6).tolist(),
        "banner_quad_px": np.round(banner_quad, 6).tolist(),
        "feet_endpoints_px": np.round(project(feet), 6).tolist(),
        "eyelet_and_tie_count": tie_count,
        "banner_visible_size_m": [round(right-left, 3), round(top-bottom, 3)],
    }
    return pm, a, banner_mask, info


def product_floor_shadow(w: float, h: float) -> np.ndarray:
    size = (CANVAS[0] * SS, CANVAS[1] * SS)
    low = [[-w/2, 0, 0], [w/2, 0, 0]]
    far = [[-w/2 + .50*h, 0, .67*h], [w/2 + .50*h, 0, .67*h]]
    points = np.rint(project(low + far) * SS).astype(np.int32)
    mask = np.zeros((size[1], size[0]), np.uint8)
    cv2.fillConvexPoly(mask, cv2.convexHull(points), 255, cv2.LINE_AA)
    broad = cv2.GaussianBlur(mask, (0, 0), 6 * SS).astype(float) / 255 * .10
    core = cv2.GaussianBlur(mask, (0, 0), 2.2 * SS).astype(float) / 255 * .075
    contact = np.zeros_like(mask)
    for x in [-w/2 + RADIUS, w/2 - RADIUS]:
        feet = np.rint(project([[x, 0, FOOT_FRONT_Z], [x, 0, FOOT_BACK_Z]]) * SS).astype(np.int32)
        cv2.line(contact, tuple(feet[0]), tuple(feet[1]), 255, round(3 * SS), cv2.LINE_AA)
    local = cv2.GaussianBlur(contact, (0, 0), 1.4 * SS).astype(float) / 255 * .25
    shadow = 1 - (1 - broad) * (1 - core) * (1 - local)
    return np.rint(cv2.resize(shadow, CANVAS, interpolation=cv2.INTER_AREA) * 255).astype(np.uint8)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{name}", size)


def overview(items: list[dict]) -> None:
    tile_w, tile_h, caption, gap, header = 632, 424, 56, 24, 144
    board = Image.new("RGB", (tile_w*2 + gap*3, header + (tile_h+caption)*2 + gap*3), "#f3f4f6")
    draw = ImageDraw.Draw(board)
    draw.text((gap, 20), "SM PRODUCTION / ДЖОКЕР", font=font(17, True), fill="#99752b")
    draw.text((gap, 50), "Открытый трубный каркас — четыре размера", font=font(29, True), fill="#17283d")
    draw.text((gap, 99), "Один фон и масштаб · девушка 160 см, мужчина 185 см · ширина × высота", font=font(17), fill="#576579")
    for i, item in enumerate(items):
        row, col = divmod(i, 2)
        x = gap + col*(tile_w+gap)
        y = header + gap + row*(tile_h+caption+gap)
        image = Image.open(ROOT/item["files"]["png"]).convert("RGB").resize((tile_w, tile_h), Image.Resampling.LANCZOS)
        board.paste(image, (x, y))
        draw.rectangle((x, y+tile_h, x+tile_w-1, y+tile_h+caption-1), fill="white")
        draw.text((x+18, y+tile_h+14), item["label"], font=font(24, True), fill="#17283d")
    save_image(board, ROOT/"sm-production-joker-size-comparison.jpg")


def verify() -> None:
    manifest = json.loads((ROOT/"manifest.json").read_text())
    bg = read_rgb(BASE/"assets/background-locked.png")
    common = np.array(Image.open(ASSETS/"common-background-check-mask.png").convert("L")) > 0
    people = np.array(Image.open(HUMANS/"assets/people-layer-160-185.png").convert("RGBA"))
    opaque = people[:, :, 3] == 255
    assert {(x["width_m"], x["height_m"]) for x in manifest["items"]} == set(SIZES)
    assert sha(BASE/"assets/background-locked.png") == manifest["background_sha256"]
    assert sha(HUMANS/"assets/people-layer-160-185.png") == manifest["people_layer_sha256"]
    assert sha(ROOT/"references/joker-3x3-user-reference.jpg") == manifest["user_reference_sha256"]
    for item in manifest["items"]:
        for filename in item["files"].values():
            with Image.open(ROOT/filename) as image:
                assert image.size == CANVAS
                image.verify()
        image = read_rgb(ROOT/item["files"]["png"])
        assert np.array_equal(image[common], bg[common]), "Room changed between sizes"
        assert np.array_equal(image[opaque], people[:, :, :3][opaque]), "People changed"
        w, h = item["width_m"], item["height_m"]
        expected = project([[-w/2, h, 0], [w/2, h, 0], [w/2, 0, 0], [-w/2, 0, 0]])
        assert np.allclose(expected, item["outer_frame_quad_px"], atol=.001)
        for field in ["outer_frame_quad_px", "feet_endpoints_px"]:
            q = np.array(item[field])
            assert np.all((q[:, 0] > 0) & (q[:, 0] < CANVAS[0]))
            assert np.all((q[:, 1] > 0) & (q[:, 1] < CANVAS[1]))
        assert item["eyelet_and_tie_count"] >= 24
    print(f"Verified 4 sizes / 12 files; {int(common.sum()):,} background pixels and {int(opaque.sum()):,} person pixels are identical across every PNG.")


def package(items: list[dict]) -> None:
    files = [ROOT/name for item in items for name in item["files"].values()]
    files += [ROOT/"sm-production-joker-size-comparison.jpg", ROOT/"manifest.json", ROOT/"DOWNLOAD-NOTES.txt"]
    archive = ROOT/"sm-production-joker-catalog.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for path in files:
            z.write(path, path.name)
    with zipfile.ZipFile(archive) as z:
        assert len(z.namelist()) == 15
        assert z.testzip() is None
    print(f"Archive CRC passed: {archive.name}, {archive.stat().st_size:,} bytes.")


def render() -> None:
    bg_path = BASE/"assets/background-locked.png"
    people_path = HUMANS/"assets/people-layer-160-185.png"
    bg = read_rgb(bg_path)
    people = np.array(Image.open(people_path).convert("RGBA"))
    pa = people[:, :, 3].astype(float)/255
    ppm = people[:, :, :3].astype(float)*pa[:, :, None]
    people_floor = np.array(Image.open(HUMANS/"assets/people-floor-shadow.png").convert("L")).astype(float)/255
    people_wall = np.array(Image.open(HUMANS/"assets/people-wall-shadow.png").convert("L")).astype(float)/255
    union = pa > 0
    items = []
    for w, h in SIZES:
        pm, a, paper, geometry = render_product(w, h)
        product_shadow = product_floor_shadow(w, h).astype(float)/255
        # Contact shadows stay on the floor; figure shadows only darken banner cloth.
        shade = 1 - (1-product_shadow)*(1-people_floor*(1-a))
        shaded_bg = bg.astype(float)*(1-shade[:, :, None])
        subject = pm*(1-(people_wall*paper)[:, :, None]) + shaded_bg*(1-a[:, :, None])
        final = np.rint(subject*(1-pa[:, :, None])+ppm).clip(0, 255).astype(np.uint8)
        local = (a > 0) | (product_shadow > 0) | ((people_floor*(1-a)) > .001) | (pa > 0)
        assert np.array_equal(final[~local], bg[~local])
        union |= local
        files = {}
        for ext in ["png", "jpg", "webp"]:
            filename = f"{stem(w,h)}.{ext}"
            save_image(Image.fromarray(final), ROOT/filename)
            files[ext] = filename
        items.append({"id": f"{slug(w)}x{slug(h)}", "label": label(w,h), "width_m": w,
                      "height_m": h, "canvas_px": list(CANVAS), "files": files, **geometry})
        print(f"Rendered Joker {label(w,h)}, {geometry['eyelet_and_tie_count']} eyelets/ties, two T-feet.")
    common = (~union).astype(np.uint8)*255
    Image.fromarray(common).save(ASSETS/"common-background-check-mask.png", compress_level=9)
    manifest = {
        "title": "SM Production — Joker tube-frame photozones, four sizes",
        "dimension_order": "outer frame width x height, meters", "canvas_px": list(CANVAS),
        "reference_size_m": [3,3], "user_reference": "references/joker-3x3-user-reference.jpg",
        "user_reference_sha256": sha(ROOT/"references/joker-3x3-user-reference.jpg"),
        "background": "../presswalls-sizes/assets/background-locked.png", "background_sha256": sha(bg_path),
        "people_layer": "../presswalls-with-people/assets/people-layer-160-185.png", "people_layer_sha256": sha(people_path),
        "people_heights_cm": [160,185], "people": PEOPLE_METADATA, "camera_matrix": P.tolist(),
        "camera_policy": "Same camera, room, ground origin and people as the approved wooden-frame catalog. No per-item zoom or crop.",
        "construction": {"type": "open Joker chrome tube frame, eyeleted tension banner, two transverse T-feet",
                         "tube_diameter_m_visual_assumption": TUBE_DIAMETER,
                         "foot_depth_m_visual_assumption": FOOT_BACK_Z-FOOT_FRONT_Z,
                         "maximum_eyelet_spacing_m_visual_assumption": TIE_SPACING,
                         "note": "Visual hardware dimensions are inferred, not fabrication measurements. Requested sizes refer to outer frame."},
        "common_background_pixels": int((~union).sum()), "items": items,
    }
    (ROOT/"manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n")
    overview(items)
    verify()
    package(items)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Validate existing outputs without rerendering")
    args = parser.parse_args()
    verify() if args.check else render()
