#!/usr/bin/env python3
"""Place the four exact banner concepts on one realistic concealed frame."""

from __future__ import annotations

import io
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw
import resvg_py

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
SOURCE = ROOT / "source"
BASE = SOURCE / "hidden-frame-base-corrected.jpg"
CONCEPT_DIR = REPO / "banners" / "anikom-arena-3000x2500-concepts"

CONCEPTS = [
    ("01-arena-core", "Arena Core"),
    ("02-match-day", "Match Day"),
    ("03-arena-energy", "Arena Energy"),
    ("04-partner-photozone", "Partner Photozone"),
]

# Exact front face and wrapped right edge measured from the clean base image.
FRONT_QUAD = np.float32([[385, 127], [998, 84], [998, 671], [385, 630]])
SIDE_QUAD = np.float32([[998, 84], [1018, 96], [1018, 674], [998, 671]])


def render_svg(path: Path, width: int = 1800, height: int = 1500) -> np.ndarray:
    png = resvg_py.svg_to_bytes(
        svg_path=str(path),
        width=width,
        height=height,
        dpi=96,
    )
    image = Image.open(io.BytesIO(png)).convert("RGB")
    return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)


def prepare_print(artwork: np.ndarray, seed: int) -> np.ndarray:
    """Apply only physical print response; do not alter the approved design."""
    height, width = artwork.shape[:2]
    y = np.linspace(1.025, 0.955, height, dtype=np.float32)[:, None, None]
    x = np.linspace(1.015, 0.925, width, dtype=np.float32)[None, :, None]
    result = artwork.astype(np.float32) * y * x

    # Fine matte-vinyl texture at sub-pixel visual strength.
    rng = np.random.default_rng(seed)
    result += rng.normal(0, 0.72, result.shape).astype(np.float32)
    return np.clip(result, 0, 255).astype(np.uint8)


def warp(image: np.ndarray, quad: np.ndarray, canvas_size: tuple[int, int]):
    height, width = image.shape[:2]
    source = np.float32(
        [[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]]
    )
    matrix = cv2.getPerspectiveTransform(source, quad)
    warped = cv2.warpPerspective(
        image,
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


def composite_one(slug: str, index: int) -> Path:
    base = cv2.imread(str(BASE), cv2.IMREAD_COLOR)
    if base is None:
        raise RuntimeError(f"Cannot open {BASE}")
    canvas_height, canvas_width = base.shape[:2]
    artwork = prepare_print(render_svg(CONCEPT_DIR / f"{slug}.svg"), 20261120 + index)

    # Continue the right-most design edge around the shallow concealed frame side.
    side_strip = artwork[:, -80:, :]
    side, side_alpha = warp(side_strip, SIDE_QUAD, (canvas_width, canvas_height))
    side = np.clip(side.astype(np.float32) * 0.67, 0, 255).astype(np.uint8)
    side_mix = (side_alpha.astype(np.float32) / 255)[..., None]
    result = base.astype(np.float32) * (1 - side_mix) + side.astype(np.float32) * side_mix

    front, front_alpha = warp(artwork, FRONT_QUAD, (canvas_width, canvas_height))
    front_mix = (front_alpha.astype(np.float32) / 255)[..., None]
    result = result * (1 - front_mix) + front.astype(np.float32) * front_mix
    result = np.clip(result, 0, 255).astype(np.uint8)

    # Physical edge cues only: a narrow lit top fold and soft dark lower fold.
    cv2.polylines(
        result,
        [np.round(FRONT_QUAD[[0, 1]]).astype(np.int32)],
        False,
        (92, 99, 105),
        1,
        cv2.LINE_AA,
    )
    cv2.polylines(
        result,
        [np.round(FRONT_QUAD[[3, 2]]).astype(np.int32)],
        False,
        (5, 8, 11),
        2,
        cv2.LINE_AA,
    )

    output = ROOT / f"{slug}-hidden-frame.jpg"
    cv2.imwrite(str(output), result, [cv2.IMWRITE_JPEG_QUALITY, 96])
    return output


def build_overview(outputs: list[Path]) -> None:
    cards = [Image.open(path).convert("RGB") for path in outputs]
    card_width = 1056
    card_height = round(card_width * cards[0].height / cards[0].width)
    cards = [card.resize((card_width, card_height), Image.Resampling.LANCZOS) for card in cards]
    gutter = 24
    label_height = 70
    canvas = Image.new(
        "RGB",
        (card_width * 2 + gutter * 3, (card_height + label_height) * 2 + gutter * 3),
        "#E8E4DC",
    )
    draw = ImageDraw.Draw(canvas)
    font = None
    positions = [
        (gutter, gutter),
        (card_width + gutter * 2, gutter),
        (gutter, card_height + label_height + gutter * 2),
        (card_width + gutter * 2, card_height + label_height + gutter * 2),
    ]
    for number, ((_, title), card, (x, y)) in enumerate(zip(CONCEPTS, cards, positions), start=1):
        canvas.paste(card, (x, y))
        draw.text((x + 8, y + card_height + 17), f"{number}. {title}", fill="#081A2B", font=font)
    canvas.save(ROOT / "hidden-frame-mockups-overview.jpg", quality=94)


def main() -> None:
    outputs = [composite_one(slug, index) for index, (slug, _) in enumerate(CONCEPTS, start=1)]
    build_overview(outputs)
    print(f"Built {len(outputs)} concealed-frame mockups")
    print("Front frame members, feet and fasteners visible: none")


if __name__ == "__main__":
    main()
