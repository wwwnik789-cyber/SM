#!/usr/bin/env python3
"""
Проставляет плотность пикселей (dpi) в JPEG без перекодирования.

Разбираем сегменты JPEG по структуре, находим APP0/JFIF и правим в нём
поля units / Xdensity / Ydensity. Изображение остаётся байт в байт прежним —
меняется только метаданная, поэтому пережатия и потери качества нет.
"""

from __future__ import annotations

import struct
import sys
from pathlib import Path

SOI = b"\xff\xd8"
APP0 = 0xE0


def set_dpi(path: Path, dpi: int = 300) -> str:
    data = path.read_bytes()
    if not data.startswith(SOI):
        raise ValueError(f"{path.name}: не JPEG")

    pos = 2
    while pos < len(data):
        if data[pos] != 0xFF:
            pos += 1
            continue
        marker = data[pos + 1]
        if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
            pos += 2
            continue
        if marker == 0xDA:  # начало сканирования — дальше только энтропия
            break
        seg_len = struct.unpack(">H", data[pos + 2 : pos + 4])[0]
        seg = data[pos : pos + 2 + seg_len]

        if marker == APP0 and seg[4:9] == b"JFIF\x00":
            units = 1 if dpi >= 100 else 2
            value = dpi if units == 1 else int(round(dpi / 2.54))
            new_seg = bytearray(seg)
            # seg[11] — units, seg[12:14] — Xdensity, seg[14:16] — Ydensity
            new_seg[11] = units
            struct.pack_into(">H", new_seg, 12, value)
            struct.pack_into(">H", new_seg, 14, value)
            out = data[:pos] + bytes(new_seg) + data[pos + 2 + seg_len :]
            path.write_bytes(out)
            return f"{value} dpi"

        pos += 2 + seg_len

    raise ValueError(f"{path.name}: не найден сегмент APP0/JFIF")


if __name__ == "__main__":
    target = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    for p in sys.argv[2:]:
        print(f"  {p} → {set_dpi(Path(p), target)}")
