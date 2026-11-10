#!/usr/bin/env python3
"""Build the exact front-view banner mockup from the supplied photo and PDF."""

from __future__ import annotations

import io
from pathlib import Path

import cv2
import numpy as np
import pymupdf
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "source"
PHOTO = SOURCE / "tower-front-original.jpg"
MARKED = SOURCE / "tower-front-placement-marked.jpg"
PDF = SOURCE / "anikom-banner-layout.pdf"
ARTWORK = ROOT / "adapted-horizontal-artwork.png"
OUTPUT = ROOT / "01-front-view.jpg"

# Corners measured from the user's red placement outline, clockwise from top-left.
TARGET_QUAD = np.float32(
    [
        [473, 1430],
        [1372, 1414],
        [1380, 1950],
        [482, 1966],
    ]
)

CORAL = np.array([217, 74, 67], dtype=np.float32)


def render_pdf(size: int = 2000) -> Image.Image:
    document = pymupdf.open(PDF)
    page = document[0]
    scale = size / page.rect.width
    pixmap = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), alpha=False)
    return Image.open(io.BytesIO(pixmap.tobytes("png"))).convert("RGB")


def build_adapted_artwork(pdf_page: Image.Image) -> Image.Image:
    """Adapt the square layout to the marked horizontal face without logo distortion."""
    width, height = 1800, 1070
    y = np.linspace(0, 1, height, dtype=np.float32)[:, None, None]
    top = np.array([8, 25, 42], dtype=np.float32)[None, None, :]
    middle = np.array([15, 40, 65], dtype=np.float32)[None, None, :]
    blend = np.clip(np.sin(np.pi * y), 0, 1) ** 1.55
    background = top * (1 - blend) + middle * blend
    background = np.repeat(background, width, axis=1)
    art = Image.fromarray(np.clip(background, 0, 255).astype(np.uint8), "RGB")

    draw = ImageDraw.Draw(art, "RGBA")
    # Tapered side fields continue the geometry from the supplied square layout.
    draw.polygon(
        [(0, 0), (365, 0), (490, 440), (440, height), (0, height)],
        fill=(45, 34, 47, 245),
    )
    draw.polygon(
        [(1435, 0), (width, 0), (width, height), (1350, height), (1310, 440)],
        fill=(28, 30, 45, 245),
    )

    # Preserve the central circular artwork from the PDF at a uniform scale.
    source_size = pdf_page.width
    crop_left = round(source_size * 0.19)
    crop_top = round(source_size * 0.19)
    crop_right = round(source_size * 0.81)
    crop_bottom = round(source_size * 0.81)
    patch = pdf_page.crop((crop_left, crop_top, crop_right, crop_bottom))
    patch_size = 700
    patch = patch.resize((patch_size, patch_size), Image.Resampling.LANCZOS)

    # Feather only the outer corners of the patch; the coral circle and logo remain exact.
    mask = Image.new("L", (patch_size, patch_size), 255)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rectangle((0, 0, patch_size - 1, patch_size - 1), outline=0, width=20)
    mask = mask.filter(ImageFilter.GaussianBlur(14))
    art.paste(patch, ((width - patch_size) // 2, (height - patch_size) // 2), mask)

    draw = ImageDraw.Draw(art)
    inset = 13
    border_width = 12
    draw.rectangle(
        (inset, inset, width - inset - 1, height - inset - 1),
        outline=tuple(CORAL.astype(np.uint8)),
        width=border_width,
    )
    return art


def expand_quad(quad: np.ndarray, amount_x: float, amount_y: float) -> np.ndarray:
    center = quad.mean(axis=0)
    expanded = quad.copy()
    for index, point in enumerate(quad):
        direction = point - center
        norm = np.array(
            [amount_x if direction[0] >= 0 else -amount_x,
             amount_y if direction[1] >= 0 else -amount_y],
            dtype=np.float32,
        )
        expanded[index] = point + norm
    return expanded


def warp_layer(layer: np.ndarray, quad: np.ndarray, canvas_size: tuple[int, int]):
    height, width = layer.shape[:2]
    source_quad = np.float32([[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]])
    matrix = cv2.getPerspectiveTransform(source_quad, quad)
    warped = cv2.warpPerspective(
        layer,
        matrix,
        canvas_size,
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=0,
    )
    alpha = cv2.warpPerspective(
        np.full((height, width), 255, dtype=np.uint8),
        matrix,
        canvas_size,
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=0,
    )
    return warped, alpha


def composite() -> None:
    photo = cv2.imread(str(PHOTO), cv2.IMREAD_COLOR)
    if photo is None:
        raise RuntimeError(f"Cannot open {PHOTO}")
    canvas_height, canvas_width = photo.shape[:2]

    pdf_page = render_pdf()
    artwork_pil = build_adapted_artwork(pdf_page)
    artwork_pil.save(ARTWORK)
    artwork = cv2.cvtColor(np.array(artwork_pil), cv2.COLOR_RGB2BGR).astype(np.float32)

    # Matte print response: retain the design while matching outdoor light.
    gradient = np.linspace(1.035, 0.94, artwork.shape[0], dtype=np.float32)[:, None, None]
    artwork *= gradient
    rng = np.random.default_rng(20261110)
    artwork += rng.normal(0, 0.85, artwork.shape).astype(np.float32)
    artwork = np.clip(artwork, 0, 255).astype(np.uint8)

    expanded_quad = expand_quad(TARGET_QUAD, 7, 7)
    frame_color = np.zeros((40, 40, 3), dtype=np.uint8)
    frame_color[:] = (24, 29, 33)
    frame, frame_alpha = warp_layer(frame_color, expanded_quad, (canvas_width, canvas_height))

    # Soft contact shadow proves that the banner is on a shallow concealed frame.
    shadow = cv2.GaussianBlur(frame_alpha, (0, 0), 8)
    shadow = np.roll(shadow, shift=(5, 6), axis=(0, 1))
    shadow_strength = (shadow.astype(np.float32) / 255 * 0.28)[..., None]
    result = photo.astype(np.float32) * (1 - shadow_strength)

    frame_mix = (frame_alpha.astype(np.float32) / 255 * 0.96)[..., None]
    result = result * (1 - frame_mix) + frame.astype(np.float32) * frame_mix

    banner, banner_alpha = warp_layer(artwork, TARGET_QUAD, (canvas_width, canvas_height))
    banner_mix = (banner_alpha.astype(np.float32) / 255)[..., None]
    result = result * (1 - banner_mix) + banner.astype(np.float32) * banner_mix

    # Restrained top-edge highlight and lower-edge shadow for 25–35 mm apparent depth.
    overlay = np.clip(result, 0, 255).astype(np.uint8)
    cv2.polylines(
        overlay,
        [np.round(TARGET_QUAD[[0, 1]]).astype(np.int32)],
        False,
        (108, 116, 121),
        2,
        cv2.LINE_AA,
    )
    cv2.polylines(
        overlay,
        [np.round(TARGET_QUAD[[3, 2]]).astype(np.int32)],
        False,
        (10, 14, 17),
        3,
        cv2.LINE_AA,
    )
    cv2.imwrite(str(OUTPUT), overlay, [cv2.IMWRITE_JPEG_QUALITY, 96])


if __name__ == "__main__":
    composite()
