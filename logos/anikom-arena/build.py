#!/usr/bin/env python3
"""Rebuild the ANIKOM ARENA logo as standalone vector SVG files."""

from __future__ import annotations

import io
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image
import resvg_py
import vtracer

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "source" / "anikom-arena-logo.png"
TIGHT_SVG = ROOT / "anikom-arena-logo-vector.svg"
ORIGINAL_CANVAS_SVG = ROOT / "anikom-arena-logo-vector-original-canvas.svg"
PREVIEW = ROOT / "preview-black-background.png"
QA_REPORT = ROOT / "qa-report.txt"

# A high-alpha contour compensates for spline expansion while retaining smooth,
# scale-independent edges. This value minimizes alpha error against the source.
ALPHA_THRESHOLD = 208
SVG_NS = "http://www.w3.org/2000/svg"


def trace_paths(source: Image.Image) -> list[dict[str, str]]:
    alpha = source.getchannel("A")
    binary_alpha = alpha.point(lambda value: 255 if value >= ALPHA_THRESHOLD else 0)
    trace_input = Image.new("L", source.size, 255)
    trace_input.paste(0, mask=binary_alpha)

    with tempfile.TemporaryDirectory(prefix="anikom-arena-trace-") as tmpdir:
        input_path = Path(tmpdir) / "trace-input.png"
        output_path = Path(tmpdir) / "trace-output.svg"
        trace_input.save(input_path)
        vtracer.convert_image_to_svg_py(
            str(input_path),
            str(output_path),
            colormode="binary",
            hierarchical="stacked",
            mode="spline",
            filter_speckle=1,
            corner_threshold=60,
            length_threshold=3,
            max_iterations=10,
            splice_threshold=45,
            path_precision=4,
        )
        traced_root = ET.parse(output_path).getroot()

    paths: list[dict[str, str]] = []
    for element in traced_root.findall(f"{{{SVG_NS}}}path"):
        attributes = {key: value for key, value in element.attrib.items() if key in {"d", "transform"}}
        if "d" in attributes:
            paths.append(attributes)
    if not paths:
        raise RuntimeError("VTracer did not return any vector paths")
    return paths


def serialize_svg(
    paths: list[dict[str, str]],
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
    group = ET.SubElement(svg, "g", {"id": "logo-artwork", "fill": "#FFFFFF"})
    for attributes in paths:
        ET.SubElement(group, "path", attributes)

    ET.indent(svg, space="  ")
    body = ET.tostring(svg, encoding="unicode", short_empty_elements=True)
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + body + "\n"


def render(svg_path: Path, width: int, height: int) -> Image.Image:
    data = resvg_py.svg_to_bytes(
        svg_path=str(svg_path),
        width=width,
        height=height,
        dpi=96,
    )
    return Image.open(io.BytesIO(data)).convert("RGBA")


def mask_metrics(source_alpha: Image.Image, vector_alpha: Image.Image) -> tuple[float, int, float]:
    source_values = list(source_alpha.get_flattened_data())
    vector_values = list(vector_alpha.get_flattened_data())
    source_mask = [value >= 128 for value in source_values]
    vector_mask = [value >= 128 for value in vector_values]
    intersection = sum(source and vector for source, vector in zip(source_mask, vector_mask))
    union = sum(source or vector for source, vector in zip(source_mask, vector_mask))
    mismatch = sum(source != vector for source, vector in zip(source_mask, vector_mask))
    mae = sum(abs(source - vector) for source, vector in zip(source_values, vector_values)) / len(source_values)
    return intersection / union, mismatch, mae


def assert_vector_only(svg_text: str) -> None:
    forbidden = ("<image", "<text", "<foreignObject", "data:image", "@font-face", "<rect")
    for token in forbidden:
        if token in svg_text:
            raise RuntimeError(f"Non-vector or unwanted SVG content found: {token}")


def main() -> None:
    source = Image.open(SOURCE).convert("RGBA")
    if source.size != (880, 1184):
        raise RuntimeError(f"Unexpected source size: {source.size}")

    alpha_bbox = source.getchannel("A").getbbox()
    if alpha_bbox is None:
        raise RuntimeError("Source contains no visible artwork")
    left, top, right, bottom = alpha_bbox
    crop_width = right - left
    crop_height = bottom - top

    paths = trace_paths(source)
    original_svg = serialize_svg(
        paths,
        width=source.width,
        height=source.height,
        view_box=(0, 0, source.width, source.height),
        description="White vector logo on a transparent background, with the original PNG canvas and proportions.",
    )
    tight_svg = serialize_svg(
        paths,
        width=crop_width,
        height=crop_height,
        view_box=(left, top, crop_width, crop_height),
        description="White vector logo on a transparent, closely cropped canvas.",
    )
    assert_vector_only(original_svg)
    assert_vector_only(tight_svg)

    ORIGINAL_CANVAS_SVG.write_text(original_svg, encoding="utf-8")
    TIGHT_SVG.write_text(tight_svg, encoding="utf-8")
    vector_original = render(ORIGINAL_CANVAS_SVG, source.width, source.height)
    vector_alpha = vector_original.getchannel("A")
    iou, mismatch, mae = mask_metrics(source.getchannel("A"), vector_alpha)
    if iou < 0.96 or mae > 1.2:
        raise RuntimeError(f"Trace fidelity outside tolerance: IoU={iou:.6f}, MAE={mae:.6f}")

    preview_width = 1200
    preview_height = round(preview_width * crop_height / crop_width)
    preview_logo = render(TIGHT_SVG, preview_width, preview_height)
    preview = Image.new("RGBA", preview_logo.size, "#080808")
    preview.alpha_composite(preview_logo)
    preview.convert("RGB").save(PREVIEW, quality=95)

    QA_REPORT.write_text(
        "\n".join(
            [
                "ANIKOM ARENA vector logo QA",
                "================================",
                f"Source canvas: {source.width} × {source.height} px",
                f"Source visible alpha bounds: {alpha_bbox}",
                f"Tight vector canvas: {crop_width} × {crop_height}",
                f"Vector paths: {len(paths)}",
                f"Threshold-mask IoU at source resolution: {iou:.6f}",
                f"Threshold-mask mismatched pixels: {mismatch}",
                f"Mean alpha error (0–255): {mae:.6f}",
                f"Rendered vector alpha bounds: {vector_alpha.getbbox()}",
                "Embedded raster images: none",
                "Text/font dependencies: none",
                "Background: transparent",
                "Artwork fill: #FFFFFF",
                "Distorting transforms: none (path-local translations only)",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(QA_REPORT.read_text(encoding="utf-8"), end="")


if __name__ == "__main__":
    main()
