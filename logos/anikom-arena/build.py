#!/usr/bin/env python3
"""Build a clean, font-outline reconstruction of the ANIKOM ARENA logo."""

from __future__ import annotations

import io
import math
import tempfile
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

import cv2
import numpy as np
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont
from scipy.optimize import differential_evolution

import resvg_py
import vtracer

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "source" / "anikom-arena-logo.png"
FONT_SOURCE = ROOT / "source" / "Montserrat-Variable.ttf"
TIGHT_SVG = ROOT / "anikom-arena-logo-vector.svg"
ORIGINAL_CANVAS_SVG = ROOT / "anikom-arena-logo-vector-original-canvas.svg"
PREVIEW = ROOT / "preview-black-background.png"
QA_REPORT = ROOT / "qa-report.txt"
SVG_NS = "http://www.w3.org/2000/svg"

# Each item maps a connected component in the source PNG to its real character.
OUTER_TOP = [
    (31, "А"), (24, "Н"), (17, "И"), (8, "К"), (7, "О"), (5, "М"),
    (3, "А"), (1, "Р"), (2, "Е"), (4, "Н"), (6, "А"),
]
OUTER_BOTTOM = [
    (32, "А"), (37, "Н"), (45, "И"), (52, "К"), (56, "О"), (58, "М"),
    (60, "А"), (61, "Р"), (59, "Е"), (57, "Н"), (55, "А"),
]
MAIN_WORD = [(34, "А"), (33, "Р"), (29, "Е"), (22, "Н"), (19, "А")]
UPPER_LINE = [
    (30, "А"), (28, "Н"), (27, "И"), (26, "К"), (25, "О"), (23, "М"),
    (21, "А"), (20, "Р"), (16, "Е"), (12, "Н"), (10, "А"),
]
SMALL_LINE = [(18, "О"), (14, "С"), (11, "Н"), (13, ".")]
BOTTOM_LINE = [
    (54, "А"), (50, "Н"), (48, "И"), (46, "К"), (44, "О"), (43, "М"),
    (41, "А"), (40, "Р"), (39, "Е"), (36, "Н"), (35, "А"),
]
YEAR = [(53, "2"), (51, "0"), (49, "2"), (47, "5")]
CUSTOM_MARK_COMPONENTS = {9, 15, 38, 42}
GROUP_ORDER = [
    "outer-ring", "small-line", "upper-line", "main-word", "custom-marks",
    "bottom-line", "year",
]


class LogoBuilder:
    def __init__(self) -> None:
        self.source_image = Image.open(SOURCE).convert("RGBA")
        if self.source_image.size != (880, 1184):
            raise RuntimeError(f"Unexpected source size: {self.source_image.size}")
        self.source_alpha = np.array(self.source_image.getchannel("A"))
        binary = (self.source_alpha >= 128).astype(np.uint8)
        (
            self.component_count,
            self.labels,
            self.stats,
            self.centroids,
        ) = cv2.connectedComponentsWithStats(binary, 8)
        if self.component_count - 1 != 61:
            raise RuntimeError(f"Expected 61 source components, found {self.component_count - 1}")

        self.render_cache: dict[tuple[int, str], tuple[np.ndarray, tuple[int, ...], float, float, float, float]] = {}
        self.glyph_cache: dict[tuple[int, str], str] = {}
        self.glyph_sets: dict[int, tuple[TTFont, object, dict[int, str]]] = {}
        self.objects: dict[str, list[dict[str, str]]] = defaultdict(list)

    def rendered_glyph(self, weight: int, character: str):
        key = (weight, character)
        if key in self.render_cache:
            return self.render_cache[key]

        font = ImageFont.truetype(FONT_SOURCE, 1000)
        font.set_variation_by_axes([weight])
        bbox = font.getbbox(character, anchor="ls")
        image = Image.new("L", (bbox[2] - bbox[0] + 8, bbox[3] - bbox[1] + 8), 0)
        ImageDraw.Draw(image).text(
            (4 - bbox[0], 4 - bbox[1]),
            character,
            font=font,
            fill=255,
            anchor="ls",
        )
        alpha = np.array(image)
        y_grid, x_grid = np.indices(alpha.shape)
        weights = alpha.astype(float)
        total = weights.sum()
        pixel_cx = float((x_grid * weights).sum() / total)
        pixel_cy = float((y_grid * weights).sum() / total)
        # Centroid in font coordinates, with Y increasing down from the baseline.
        font_cx = pixel_cx + bbox[0] - 4
        font_cy = pixel_cy + bbox[1] - 4
        result = alpha, bbox, pixel_cx, pixel_cy, font_cx, font_cy
        self.render_cache[key] = result
        return result

    def glyph_path(self, weight: int, character: str) -> str:
        key = (weight, character)
        if key in self.glyph_cache:
            return self.glyph_cache[key]
        if weight not in self.glyph_sets:
            font = TTFont(FONT_SOURCE)
            glyph_set = font.getGlyphSet(location={"wght": weight})
            self.glyph_sets[weight] = (font, glyph_set, font.getBestCmap())
        _, glyph_set, cmap = self.glyph_sets[weight]
        glyph_name = cmap[ord(character)]
        pen = SVGPathPen(glyph_set)
        glyph_set[glyph_name].draw(pen)
        path = pen.getCommands()
        self.glyph_cache[key] = path
        return path

    def fit_character(
        self,
        component: int,
        character: str,
        weight: int,
        nominal_angle: float,
        angle_range: float,
        padding: int = 8,
    ) -> tuple[float, float, float, float]:
        x, y, width, height, area = self.stats[component]
        x0 = max(0, x - padding)
        y0 = max(0, y - padding)
        x1 = min(self.source_image.width, x + width + padding)
        y1 = min(self.source_image.height, y + height + padding)

        target = self.source_alpha[y0:y1, x0:x1].astype(np.float32) / 255
        local_labels = self.labels[y0:y1, x0:x1]
        target[(local_labels != 0) & (local_labels != component)] = 0
        y_grid, x_grid = np.indices(target.shape)
        total = target.sum()
        target_cx = float((x_grid * target).sum() / total)
        target_cy = float((y_grid * target).sum() / total)

        glyph, _, pixel_cx, pixel_cy, font_cx, font_cy = self.rendered_glyph(weight, character)
        initial_scale = math.sqrt(area / int((glyph >= 128).sum()))

        def render(parameters: np.ndarray) -> np.ndarray:
            scale, angle = parameters
            radians = math.radians(angle)
            cosine = math.cos(radians)
            sine = math.sin(radians)
            matrix = np.array(
                [
                    [
                        scale * cosine,
                        -scale * sine,
                        target_cx - scale * (cosine * pixel_cx - sine * pixel_cy),
                    ],
                    [
                        scale * sine,
                        scale * cosine,
                        target_cy - scale * (sine * pixel_cx + cosine * pixel_cy),
                    ],
                ],
                np.float32,
            )
            return cv2.warpAffine(
                glyph,
                matrix,
                (target.shape[1], target.shape[0]),
                flags=cv2.INTER_AREA,
                borderValue=0,
            ).astype(np.float32) / 255

        def objective(parameters: np.ndarray) -> float:
            candidate = render(parameters)
            alpha_error = np.mean(np.abs(target - candidate))
            binary_error = np.mean((target >= 0.5) != (candidate >= 0.5))
            return float(alpha_error + 0.12 * binary_error)

        result = differential_evolution(
            objective,
            [
                (initial_scale * 0.78, initial_scale * 1.22),
                (nominal_angle - angle_range, nominal_angle + angle_range),
            ],
            tol=0.004,
            popsize=7,
            maxiter=20,
            polish=True,
            seed=component,
            workers=1,
        )
        scale, angle = result.x
        radians = math.radians(angle)
        cosine = math.cos(radians)
        sine = math.sin(radians)
        global_cx = x0 + target_cx
        global_cy = y0 + target_cy
        translate_x = global_cx - scale * (cosine * font_cx - sine * font_cy)
        translate_y = global_cy - scale * (sine * font_cx + cosine * font_cy)
        return float(scale), float(angle), float(translate_x), float(translate_y)

    def add_text_component(
        self,
        group: str,
        component: int,
        character: str,
        weight: int,
        nominal_angle: float,
        angle_range: float,
    ) -> None:
        scale, angle, translate_x, translate_y = self.fit_character(
            component,
            character,
            weight,
            nominal_angle,
            angle_range,
        )
        radians = math.radians(angle)
        cosine = math.cos(radians)
        sine = math.sin(radians)
        # Font paths use Y-up coordinates. This matrix flips Y, rotates, scales,
        # and translates each clean outline into its measured source position.
        matrix = (
            f"matrix({scale * cosine:.7f} {scale * sine:.7f} "
            f"{scale * sine:.7f} {-scale * cosine:.7f} "
            f"{translate_x:.4f} {translate_y:.4f})"
        )
        self.objects[group].append(
            {
                "d": self.glyph_path(weight, character),
                "transform": matrix,
                "data-source-component": str(component),
            }
        )

    def add_main_word_component(
        self,
        component: int,
        character: str,
        scale_x: float,
        scale_y: float,
        angle: float,
    ) -> None:
        """Place one main-word glyph with a shared cap height and angle.

        The source artwork uses condensed main lettering. Horizontal scale is
        measured per glyph to preserve its source width, while every letter
        shares one vertical scale, weight and angle. This prevents a narrow
        glyph such as Е from being enlarged to compensate for its area.
        """
        _, _, _, _, font_cx, font_cy = self.rendered_glyph(750, character)
        target_cx, target_cy = self.centroids[component]
        radians = math.radians(angle)
        cosine = math.cos(radians)
        sine = math.sin(radians)
        translate_x = target_cx - (
            cosine * scale_x * font_cx - sine * scale_y * font_cy
        )
        translate_y = target_cy - (
            sine * scale_x * font_cx + cosine * scale_y * font_cy
        )
        # Font paths are Y-up. Horizontal/vertical scaling is applied before
        # rotation, then the Y axis is flipped into SVG screen coordinates.
        matrix = (
            f"matrix({cosine * scale_x:.7f} {sine * scale_x:.7f} "
            f"{sine * scale_y:.7f} {-cosine * scale_y:.7f} "
            f"{translate_x:.4f} {translate_y:.4f})"
        )
        self.objects["main-word"].append(
            {
                "d": self.glyph_path(750, character),
                "transform": matrix,
                "data-source-component": str(component),
            }
        )

    def trace_custom_marks(self) -> None:
        selected = np.isin(self.labels, list(CUSTOM_MARK_COMPONENTS)).astype(np.uint8)
        # Include the original antialiasing just outside the thresholded components.
        neighborhood = cv2.dilate(selected, np.ones((3, 3), np.uint8))
        custom_alpha = np.where(neighborhood, self.source_alpha, 0).astype(np.uint8)
        upscaled = Image.fromarray(custom_alpha).resize(
            (self.source_image.width * 4, self.source_image.height * 4),
            Image.Resampling.LANCZOS,
        )
        binary = upscaled.point(lambda value: 255 if value >= 128 else 0)
        trace_input = Image.new("L", upscaled.size, 255)
        trace_input.paste(0, mask=binary)

        with tempfile.TemporaryDirectory(prefix="anikom-arena-marks-") as tmpdir:
            input_path = Path(tmpdir) / "marks.png"
            output_path = Path(tmpdir) / "marks.svg"
            trace_input.save(input_path)
            vtracer.convert_image_to_svg_py(
                str(input_path),
                str(output_path),
                colormode="binary",
                hierarchical="stacked",
                mode="spline",
                filter_speckle=4,
                corner_threshold=60,
                length_threshold=8,
                max_iterations=10,
                splice_threshold=45,
                path_precision=3,
            )
            traced_root = ET.parse(output_path).getroot()

        traced = traced_root.findall(f"{{{SVG_NS}}}path")
        if len(traced) != 4:
            raise RuntimeError(f"Expected four custom mark paths, found {len(traced)}")
        for path in traced:
            attributes = {
                key: value
                for key, value in path.attrib.items()
                if key in {"d", "transform"}
            }
            self.objects["custom-marks"].append(attributes)

    def reconstruct(self) -> None:
        ring_center = (440, 585)
        for component, character in OUTER_TOP + OUTER_BOTTOM:
            center_x, center_y = self.centroids[component]
            angle = math.degrees(
                math.atan2(center_y - ring_center[1], center_x - ring_center[0])
            ) + 90
            while angle > 180:
                angle -= 360
            while angle <= -180:
                angle += 360
            self.add_text_component(
                "outer-ring", component, character, 800, angle, 5
            )

        # One coherent typographic system for АРЕНА: common weight, cap height
        # and angle. Only horizontal condensation differs to match the measured
        # width of each source glyph without changing its height.
        main_scale_x = {
            34: 0.13806,
            33: 0.14184,
            29: 0.16461,
            22: 0.15441,
            19: 0.14846,
        }
        for component, character in MAIN_WORD:
            self.add_main_word_component(
                component,
                character,
                main_scale_x[component],
                scale_y=0.20732,
                angle=-27.25064,
            )
        for component, character in UPPER_LINE:
            self.add_text_component(
                "upper-line", component, character, 850, -29, 5
            )
        for component, character in SMALL_LINE:
            self.add_text_component(
                "small-line", component, character, 800, -23.3, 5
            )
        for component, character in BOTTOM_LINE:
            self.add_text_component(
                "bottom-line", component, character, 850, -24.2, 5
            )
        for component, character in YEAR:
            self.add_text_component(
                "year", component, character, 750, -24.5, 5
            )
        self.trace_custom_marks()

    def serialize(
        self,
        *,
        width: int,
        height: int,
        view_box: tuple[int, int, int, int],
        description: str,
    ) -> str:
        svg = ET.Element(
            "svg",
            {
                "xmlns": SVG_NS,
                "version": "1.1",
                "width": str(width),
                "height": str(height),
                "viewBox": " ".join(str(value) for value in view_box),
                "role": "img",
                "aria-labelledby": "logo-title logo-description",
                "shape-rendering": "geometricPrecision",
            },
        )
        title = ET.SubElement(svg, "title", {"id": "logo-title"})
        title.text = "ANIKOM ARENA"
        desc = ET.SubElement(svg, "desc", {"id": "logo-description"})
        desc.text = description
        for group_name in GROUP_ORDER:
            attributes = {"id": group_name, "fill": "#FFFFFF"}
            if group_name == "custom-marks":
                attributes["transform"] = "scale(0.25)"
            group = ET.SubElement(svg, "g", attributes)
            for path_attributes in self.objects[group_name]:
                ET.SubElement(group, "path", path_attributes)
        ET.indent(svg, space="  ")
        body = ET.tostring(svg, encoding="unicode", short_empty_elements=True)
        return '<?xml version="1.0" encoding="UTF-8"?>\n' + body + "\n"


def assert_vector_only(svg_text: str) -> None:
    forbidden = (
        "<image", "<text", "<foreignObject", "data:image", "@font-face",
        "<rect", "<clipPath", "<mask",
    )
    for token in forbidden:
        if token in svg_text:
            raise RuntimeError(f"Non-vector or unwanted SVG content found: {token}")


def render(svg_path: Path, width: int, height: int) -> Image.Image:
    data = resvg_py.svg_to_bytes(
        svg_path=str(svg_path),
        width=width,
        height=height,
        dpi=96,
    )
    return Image.open(io.BytesIO(data)).convert("RGBA")


def component_metrics(source_alpha: np.ndarray, vector_alpha: np.ndarray):
    _, _, source_stats, source_centers = cv2.connectedComponentsWithStats(
        (source_alpha >= 128).astype(np.uint8), 8
    )
    vector_count, vector_labels, vector_stats, vector_centers = cv2.connectedComponentsWithStats(
        (vector_alpha >= 128).astype(np.uint8), 8
    )
    if vector_count - 1 != 61:
        raise RuntimeError(f"Expected 61 vector components, found {vector_count - 1}")

    available = set(range(1, vector_count))
    distances: list[float] = []
    area_ratios: list[float] = []
    matches: dict[int, int] = {}
    for source_index, source_center in enumerate(source_centers[1:], start=1):
        distance, vector_index = min(
            (
                float(np.linalg.norm(source_center - vector_centers[index])),
                index,
            )
            for index in available
        )
        available.remove(vector_index)
        matches[source_index] = vector_index
        distances.append(distance)
        area_ratios.append(
            float(
                vector_stats[vector_index, cv2.CC_STAT_AREA]
                / source_stats[source_index, cv2.CC_STAT_AREA]
            )
        )
    return distances, area_ratios, matches, vector_labels


def main() -> None:
    builder = LogoBuilder()
    builder.reconstruct()
    visible_bbox = builder.source_image.getchannel("A").getbbox()
    if visible_bbox is None:
        raise RuntimeError("Source contains no visible artwork")
    left, top, right, bottom = visible_bbox
    crop_width, crop_height = right - left, bottom - top

    original_svg = builder.serialize(
        width=builder.source_image.width,
        height=builder.source_image.height,
        view_box=(0, 0, builder.source_image.width, builder.source_image.height),
        description="Clean white vector reconstruction on the original transparent canvas.",
    )
    tight_svg = builder.serialize(
        width=crop_width,
        height=crop_height,
        view_box=(left, top, crop_width, crop_height),
        description="Clean white vector reconstruction on a closely cropped transparent canvas.",
    )
    assert_vector_only(original_svg)
    assert_vector_only(tight_svg)
    ORIGINAL_CANVAS_SVG.write_text(original_svg, encoding="utf-8")
    TIGHT_SVG.write_text(tight_svg, encoding="utf-8")

    vector_native = render(
        ORIGINAL_CANVAS_SVG,
        builder.source_image.width,
        builder.source_image.height,
    )
    vector_alpha = np.array(vector_native.getchannel("A"))
    distances, area_ratios, matches, vector_labels = component_metrics(
        builder.source_alpha, vector_alpha
    )
    if max(distances) > 1.5:
        raise RuntimeError(f"Component alignment outside tolerance: {max(distances):.3f}px")

    # Confirm that every letter in АРЕНА has exactly the same projected cap
    # height after rotation. This specifically guards against an oversized Е.
    angle = math.radians(27.25064)
    cosine, sine = math.cos(angle), math.sin(angle)
    main_cap_heights: list[float] = []
    for source_component, _ in MAIN_WORD:
        vector_component = matches[source_component]
        y_points, x_points = np.where(vector_labels == vector_component)
        projected_y = sine * x_points + cosine * y_points
        main_cap_heights.append(float(projected_y.max() - projected_y.min() + 1))
    if max(main_cap_heights) - min(main_cap_heights) > 0.2:
        raise RuntimeError(f"Main-word cap heights are inconsistent: {main_cap_heights}")

    preview_width = 1200
    preview_height = round(preview_width * builder.source_image.height / builder.source_image.width)
    preview_logo = render(ORIGINAL_CANVAS_SVG, preview_width, preview_height)
    preview = Image.new("RGBA", preview_logo.size, "#080808")
    preview.alpha_composite(preview_logo)
    preview.convert("RGB").save(PREVIEW, quality=96)

    vector_bbox = vector_native.getchannel("A").getbbox()
    total_paths = sum(len(paths) for paths in builder.objects.values())
    QA_REPORT.write_text(
        "\n".join(
            [
                "ANIKOM ARENA clean vector reconstruction QA",
                "============================================",
                f"Source canvas: {builder.source_image.width} × {builder.source_image.height} px",
                f"Source visible alpha bounds: {visible_bbox}",
                f"Vector visible alpha bounds: {vector_bbox}",
                f"Tight vector canvas: {crop_width} × {crop_height}",
                f"Vector paths: {total_paths}",
                "Source/vector connected components: 61 / 61",
                f"Mean component-center drift: {np.mean(distances):.3f} px",
                f"Maximum component-center drift: {max(distances):.3f} px",
                f"Mean white-area ratio: {np.mean(area_ratios):.3f}",
                (
                    "Main-word projected cap-height range: "
                    f"{min(main_cap_heights):.2f}–{max(main_cap_heights):.2f} px"
                ),
                "Typography: rebuilt as clean Montserrat outlines",
                "Custom bracket marks: 4 oversampled spline outlines",
                "Embedded raster images: none",
                "Live text/font dependencies: none",
                "Background: transparent",
                "Artwork fill: #FFFFFF",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(QA_REPORT.read_text(encoding="utf-8"), end="")


if __name__ == "__main__":
    main()
