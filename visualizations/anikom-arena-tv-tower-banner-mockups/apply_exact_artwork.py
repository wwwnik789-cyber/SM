#!/usr/bin/env python3
"""Replace generated banner faces with the exact approved artwork."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent
ARTWORK = ROOT / "adapted-horizontal-artwork.png"

PLACEMENTS = {
    "02-left-three-quarter.jpg": np.float32(
        [[399, 819], [844, 847], [851, 1166], [396, 1178]]
    ),
    "03-right-three-quarter.jpg": np.float32(
        [[857, 900], [1648, 871], [1656, 1361], [854, 1339]]
    ),
}


def apply(image_path: Path, quad: np.ndarray, seed: int) -> None:
    image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
    artwork = cv2.imread(str(ARTWORK), cv2.IMREAD_COLOR)
    # The generated perspectives already contain the panel's outer frame edge.
    # Crop the artwork's transparent safety inset so its coral rule lands on
    # that existing edge instead of creating a visually false double border.
    artwork = artwork[13:-13, 13:-13].astype(np.float32)
    art_height, art_width = artwork.shape[:2]
    canvas_height, canvas_width = image.shape[:2]

    # Match matte outdoor print response without changing the supplied design.
    light = np.linspace(1.015, 0.965, art_height, dtype=np.float32)[:, None, None]
    artwork *= light
    rng = np.random.default_rng(seed)
    artwork += rng.normal(0, 0.65, artwork.shape).astype(np.float32)
    artwork = np.clip(artwork, 0, 255).astype(np.uint8)

    source = np.float32(
        [[0, 0], [art_width - 1, 0], [art_width - 1, art_height - 1], [0, art_height - 1]]
    )
    matrix = cv2.getPerspectiveTransform(source, quad)
    warped = cv2.warpPerspective(
        artwork,
        matrix,
        (canvas_width, canvas_height),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=0,
    )
    alpha = cv2.warpPerspective(
        np.full((art_height, art_width), 255, dtype=np.uint8),
        matrix,
        (canvas_width, canvas_height),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=0,
    )
    mix = (alpha.astype(np.float32) / 255)[..., None]
    result = image.astype(np.float32) * (1 - mix) + warped.astype(np.float32) * mix
    cv2.imwrite(str(image_path), np.clip(result, 0, 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 96])


if __name__ == "__main__":
    for index, (filename, quad) in enumerate(PLACEMENTS.items(), start=1):
        apply(ROOT / filename, quad, 20261110 + index)
