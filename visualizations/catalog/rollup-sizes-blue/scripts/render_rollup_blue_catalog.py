#!/usr/bin/env python3
"""Four RollUps in the earlier blue SM branding, preserving the approved scene.

Reuse the existing RollUp hardware renderer in memory. Replace only its vinyl
print texture with the saved blue geometric artwork and original white/gold
SM brand block. The white logo-grid series is never overwritten.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import zipfile

import cv2
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
WHITE = ROOT.parent / "rollup-sizes"
ASSETS = ROOT / "assets"
SOURCE_RENDERER = WHITE / "scripts/render_rollup_catalog.py"
spec = importlib.util.spec_from_file_location("sm_rollup_base", SOURCE_RENDERER)
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
PATTERN = base.BASE / "assets/print-pattern-clean.png"
LOGO = base.BASE / "assets/branding-extracted.png"
LOGO_WIDTH_M = 0.70
LOGO_CENTER_U = 0.50
LOGO_CENTER_V = 0.40
COMPARISON = "sm-production-rollup-blue-size-comparison.jpg"


def stem(wc: int, hc: int) -> str:
    return f"sm-production-rollup-{wc}x{hc}-blue-people"


def blue_layout(w: float, h: float) -> dict:
    with Image.open(LOGO) as logo:
        logo_height = LOGO_WIDTH_M * logo.height / logo.width
    assert LOGO_WIDTH_M < w
    assert logo_height < h
    return {"type": "one original white/gold SM cube, wordmark and tagline",
            "logo_width_m": LOGO_WIDTH_M, "logo_height_m": round(logo_height, 6),
            "center_uv": [LOGO_CENTER_U, LOGO_CENTER_V],
            "scaling": "uniform; same physical logo size in all four RollUps"}


def blue_texture(w: float, h: float) -> np.ndarray:
    tw, th = round(w * base.PPM), round(h * base.PPM)
    # Decorative artwork may fit the media; the separate logo is never stretched.
    image = Image.open(PATTERN).convert("RGB").resize((tw, th), Image.Resampling.LANCZOS).convert("RGBA")
    logo = Image.open(LOGO).convert("RGBA")
    lw = round(LOGO_WIDTH_M * base.PPM)
    lh = round(lw * logo.height / logo.width)
    image.alpha_composite(logo.resize((lw, lh), Image.Resampling.LANCZOS),
                          (round(tw * LOGO_CENTER_U - lw / 2), round(th * LOGO_CENTER_V - lh / 2)))
    rgb = np.array(image.convert("RGB")).astype(float)
    yy, xx = np.mgrid[:th, :tw]
    illumination = 1 - .022 * xx / max(tw-1, 1) - .018 * yy / max(th-1, 1)
    edge = np.exp(-xx/9) + np.exp(-(tw-1-xx)/9)
    lower = np.exp(-(th-1-yy)/20)
    illumination *= 1 - .020 * edge - .016 * lower
    rgb *= illumination[:, :, None]
    return np.rint(rgb).clip(0, 255).astype(np.uint8)


def render_product(w: float, h: float):
    previous = base.banner_texture
    base.banner_texture = blue_texture
    try:
        pm, alpha, paper, geometry = base.render_product(w, h)
    finally:
        base.banner_texture = previous
    geometry["print_layout"] = blue_layout(w, h)
    return pm, alpha, paper, geometry


def overview(items: list[dict]) -> None:
    tw, th, caption, gap, header = 632, 424, 56, 24, 144
    board = Image.new("RGB", (tw*2 + gap*3, header + (th+caption)*2 + gap*3), "#f3f4f6")
    draw = ImageDraw.Draw(board)
    draw.text((gap, 20), "SM PRODUCTION / ROLLUP", font=base.font(17, True), fill="#99752b")
    draw.text((gap, 50), "Прежний синий брендинг — четыре размера", font=base.font(29, True), fill="#17283d")
    draw.text((gap, 99), "Один фон и масштаб · девушка 160 см, мужчина 185 см · размер полотна", font=base.font(17), fill="#576579")
    for i, item in enumerate(items):
        row, col = divmod(i, 2)
        x = gap + col * (tw+gap)
        y = header + gap + row * (th+caption+gap)
        tile = Image.open(ROOT/item["files"]["png"]).convert("RGB").resize((tw, th), Image.Resampling.LANCZOS)
        board.paste(tile, (x, y))
        draw.rectangle((x, y+th, x+tw-1, y+th+caption-1), fill="white")
        draw.text((x+18, y+th+14), item["label"], font=base.font(24, True), fill="#17283d")
    base.save_image(board, ROOT/COMPARISON)


def verify() -> None:
    manifest = json.loads((ROOT/"manifest.json").read_text())
    original = json.loads((WHITE/"manifest.json").read_text())
    assert base.sha(WHITE/"manifest.json") == manifest["source_white_manifest_sha256"]
    assert base.sha(SOURCE_RENDERER) == manifest["source_renderer_sha256"]
    assert manifest["camera_matrix"] == original["camera_matrix"] == base.CALIBRATION["camera_matrix"]
    assert manifest["people"] == original["people"] == base.PEOPLE_METADATA
    assert manifest["construction"] == original["construction"]
    assert [(i["width_cm"], i["height_cm"]) for i in manifest["items"]] == base.SIZES_CM
    assert base.sha(base.BACKGROUND) == manifest["background_sha256"]
    assert base.sha(base.PEOPLE) == manifest["people_layer_sha256"]
    assert base.sha(PATTERN) == manifest["banner_design"]["pattern_sha256"]
    assert base.sha(LOGO) == manifest["banner_design"]["logo_sha256"]
    bg = base.read_rgb(base.BACKGROUND)
    common = np.array(Image.open(ASSETS/"common-background-check-mask.png").convert("L")) > 0
    people = np.array(Image.open(base.PEOPLE).convert("RGBA"))
    opaque = people[:, :, 3] == 255
    report = []
    for item, source in zip(manifest["items"], original["items"]):
        assert item["id"] == source["id"]
        for filename in item["files"].values():
            with Image.open(ROOT/filename) as image:
                assert image.size == base.CANVAS
                image.verify()
        for field in ["banner_quad_px", "cassette_extent_px", "feet_endpoints_px",
                      "print_bottom_above_floor_m_visual_assumption", "top_of_assembly_m_visual_assumption"]:
            assert item[field] == source[field], field
        current = base.read_rgb(ROOT/item["files"]["png"])
        previous = base.read_rgb(WHITE/source["files"]["png"])
        assert np.array_equal(current[common], bg[common]), "Room changed"
        assert np.array_equal(current[opaque], people[:, :, :3][opaque]), "People changed"
        assert np.array_equal(current[opaque], previous[opaque]), "People differ from the white version"
        allowed = np.zeros(current.shape[:2], np.uint8)
        cv2.fillConvexPoly(allowed, np.rint(item["banner_quad_px"]).astype(np.int32), 255)
        # Permit the subpixel boundary blend, but never the cassette, feet or room.
        allowed = cv2.dilate(allowed, np.ones((7, 7), np.uint8)) > 0
        difference = np.any(current != previous, axis=2)
        assert not np.any(difference & ~allowed), "Changes outside the banner artwork"
        assert int(difference.sum()) > 30000
        assert item["print_layout"] == blue_layout(item["width_m"], item["height_m"])
        assert base.sha(WHITE/source["files"]["png"]) == item["source_white_png_sha256"]
        report.append({"size": item["label"], "changed_banner_pixels": int(difference.sum()),
                       "changed_pixels_outside_banner": 0})
    assert int(common.sum()) == manifest["common_background_pixels"] == original["common_background_pixels"]
    print(f"Verified 4 sizes / 12 files: {int(common.sum()):,} room pixels and {int(opaque.sum()):,} opaque person pixels are unchanged.")
    print(json.dumps(report, ensure_ascii=False))


def package(items: list[dict]) -> None:
    members = [ROOT/name for item in items for name in item["files"].values()]
    members += [ROOT/COMPARISON, ROOT/"manifest.json", ROOT/"DOWNLOAD-NOTES.txt"]
    for filename, files in [("sm-production-rollup-blue-catalog.zip", members),
                             ("sm-production-rollup-blue-jpg.zip", [ROOT/i["files"]["jpg"] for i in items])]:
        with zipfile.ZipFile(ROOT/filename, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
            for path in files:
                z.write(path, path.name)
        with zipfile.ZipFile(ROOT/filename) as z:
            assert len(z.namelist()) == len(files)
            assert z.testzip() is None
            assert all(z.read(path.name) == path.read_bytes() for path in files)
        print(f"ZIP CRC passed: {filename}, {len(files)} entries, {(ROOT/filename).stat().st_size:,} bytes.")


def render() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    original = json.loads((WHITE/"manifest.json").read_text())
    bg = base.read_rgb(base.BACKGROUND)
    people = np.array(Image.open(base.PEOPLE).convert("RGBA"))
    pa = people[:, :, 3].astype(float)/255
    ppm = people[:, :, :3].astype(float)*pa[:, :, None]
    pf = np.array(Image.open(base.HUMANS/"assets/people-floor-shadow.png").convert("L")).astype(float)/255
    pw = np.array(Image.open(base.HUMANS/"assets/people-wall-shadow.png").convert("L")).astype(float)/255
    union = pa > 0
    items = []
    for (wc, hc), source in zip(base.SIZES_CM, original["items"]):
        w, h = wc/100, hc/100
        pm, alpha, paper, geometry = render_product(w, h)
        ps = base.floor_shadow(w, base.PRINT_BOTTOM+h).astype(float)/255
        shade = 1-(1-ps)*(1-pf*(1-alpha))
        shaded_bg = bg.astype(float)*(1-shade[:, :, None])
        subject = pm*(1-(pw*paper)[:, :, None]) + shaded_bg*(1-alpha[:, :, None])
        final = np.rint(subject*(1-pa[:, :, None])+ppm).clip(0, 255).astype(np.uint8)
        local = (alpha > 0) | (ps > 0) | ((pf*(1-alpha)) > .001) | (pa > 0)
        assert np.array_equal(final[~local], bg[~local])
        union |= local
        files = {}
        for ext in ["png", "jpg", "webp"]:
            filename = f"{stem(wc, hc)}.{ext}"
            base.save_image(Image.fromarray(final), ROOT/filename)
            files[ext] = filename
        items.append({"id": f"{wc}x{hc}", "label": base.label(wc, hc),
                      "width_cm": wc, "height_cm": hc, "width_m": w, "height_m": h,
                      "canvas_px": list(base.CANVAS), "files": files,
                      "source_white_png": f"../rollup-sizes/{source['files']['png']}",
                      "source_white_png_sha256": base.sha(WHITE/source["files"]["png"]), **geometry})
        print(f"Rendered blue RollUp {base.label(wc, hc)}; original logo, uniform scaling.")
    Image.fromarray((~union).astype(np.uint8)*255).save(ASSETS/"common-background-check-mask.png", compress_level=9)
    manifest = {
        "title": "SM Production — four RollUps with the previous blue geometric branding",
        "dimension_order": original["dimension_order"], "canvas_px": list(base.CANVAS),
        "source_white_series": "../rollup-sizes", "source_white_manifest_sha256": base.sha(WHITE/"manifest.json"),
        "source_renderer": "../rollup-sizes/scripts/render_rollup_catalog.py", "source_renderer_sha256": base.sha(SOURCE_RENDERER),
        "camera_matrix": original["camera_matrix"], "camera_policy": original["camera_policy"],
        "background": original["background"], "background_sha256": base.sha(base.BACKGROUND),
        "people_layer": original["people_layer"], "people_layer_sha256": base.sha(base.PEOPLE),
        "people_heights_cm": [160, 185], "people": original["people"],
        "construction": original["construction"],
        "banner_design": {
            "style": "Previous dark-blue geometric SM artwork with one large white/gold cube, SM PRODUCTION wordmark and tagline",
            "pattern": "../presswalls-sizes/assets/print-pattern-clean.png", "pattern_sha256": base.sha(PATTERN),
            "logo": "../presswalls-sizes/assets/branding-extracted.png", "logo_sha256": base.sha(LOGO),
            "logo_width_m": LOGO_WIDTH_M, "logo_center_uv": [LOGO_CENTER_U, LOGO_CENTER_V],
            "logo_policy": "Original saved alpha and colors; uniform scaling only. Do not use the white PressWall logo grid.",
            "scope": "Only printed banner artwork changes. Geometry, cassette, feet, room, people and camera are locked to the previous RollUp exports."
        },
        "common_background_pixels": int((~union).sum()), "items": items
    }
    (ROOT/"manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n")
    overview(items)
    verify()
    package(items)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Check files and compare pixel scope against the preserved white version")
    args = parser.parse_args()
    verify() if args.check else render()
