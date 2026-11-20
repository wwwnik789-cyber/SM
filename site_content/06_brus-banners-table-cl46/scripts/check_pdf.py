#!/usr/bin/env python3
"""Check the deliverable, copyable CL46 data, links, bookmarks and page bounds."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import re

import pymupdf
from pypdf import PdfReader

FOLDER = Path(__file__).resolve().parents[1]
PDF = FOLDER / "sm-production-brus-banners-table-tilda-cl46.pdf"
SIZES = ["2 × 2", "2 × 2,5", "3 × 2", "3 × 2,5", "4 × 2,5", "4 × 3", "5 × 2,5", "5 × 3"]
OFFICIAL = {
    "https://help-ru.tilda.cc/tables",
    "https://help-ru.tilda.cc/anchor",
    "https://help-ru.tilda.cc/forms",
}


def verify(render_dir: Path | None = None):
    reader = PdfReader(PDF)
    assert not reader.is_encrypted
    assert len(reader.pages) == 6
    assert len(reader.outline) == 6
    assert [reader.get_destination_page_number(d) for d in reader.outline] == list(range(6))
    texts = [page.extract_text() for page in reader.pages]
    for i, (page, text) in enumerate(zip(reader.pages, texts), 1):
        assert abs(float(page.mediabox.width) - 595.276) < .1
        assert abs(float(page.mediabox.height) - 841.890) < .1
        assert len(text) > 700, f"Unexpectedly sparse page {i}"
        assert "SM PRODUCTION" in text
        assert f"{i} / 6" in text
        assert "\ufffd" not in text and "■" not in text
        assert "<br/>" not in text
    body = texts[1]
    rows = re.findall(r"(?m)^([2345] × [23](?:,5)?);УТОЧНИТЬ\s*$", body)
    assert rows == SIZES, f"Copyable body differs from agreed sizes: {rows}"
    assert "Размер (Ш × В), м;Стоимость, ₽" in body
    assert "60%;40%" in body
    for text in [texts[0], texts[3]]:
        positions = [text.index(size + "\n") for size in SIZES]
        assert positions == sorted(positions), "The preview/worksheet size order changed"
    all_text = "\n".join(texts)
    assert all_text.count("☐") >= 20
    for fragment in ["CL46", "ST340C", "T173", "#raschet-brus", "Цены пока не утверждены."]:
        assert fragment in all_text
    flattened = " ".join(all_text.split())
    assert "Разрешить изменение ширины таблицы на мобильных устройствах" in flattened
    assert "Автоматическая синхронизация здесь не настраивается." in flattened
    assert "никаких изменений или публикации в вашем проекте не выполнено." in flattened
    uris = []
    internal = 0
    page_refs = {page.indirect_reference.idnum for page in reader.pages}
    for page in reader.pages:
        for entry in page.get("/Annots", []):
            annotation = entry.get_object()
            if annotation.get("/Subtype") != "/Link":
                continue
            action = annotation.get("/A")
            if action and action.get("/URI"):
                uris.append(str(action["/URI"]))
            if annotation.get("/Dest"):
                target = annotation["/Dest"]
                assert target[0].idnum in page_refs
                internal += 1
    assert set(uris) == OFFICIAL
    assert len(uris) == 4 and internal == 5
    document = pymupdf.open(PDF)
    for i, page in enumerate(document, 1):
        for block in page.get_text("dict")["blocks"]:
            if "lines" not in block:
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    x0, y0, x1, y1 = span["bbox"]
                    assert 40 <= x0 <= x1 <= page.rect.width - 40, (i, span)
                    assert 15 <= y0 <= y1 <= page.rect.height - 15, (i, span)
        if render_dir:
            render_dir.mkdir(parents=True, exist_ok=True)
            page.get_pixmap(matrix=pymupdf.Matrix(1.35, 1.35), alpha=False).save(render_dir / f"page-{i}.png")
    print(f"PASS: 6 A4 pages, 6 bookmarks, {internal} internal links, {len(uris)} official-source links.")
    print("PASS: exact 8-row copyable CL46 content, 60/40 widths, readable Cyrillic, 20 checkboxes, no text beyond margins.")
    print(f"PDF: {PDF.stat().st_size:,} bytes")
    print(f"SHA256: {hashlib.sha256(PDF.read_bytes()).hexdigest()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--render-dir", type=Path, help="Optional scratch folder for six PNG previews")
    args = parser.parse_args()
    verify(args.render_dir)
