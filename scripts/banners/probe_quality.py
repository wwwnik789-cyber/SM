#!/usr/bin/env python3
"""
Тест: сколько весит мастер 300 × 270 см при разном качестве JPEG.

Нужно, чтобы файлы влезли в лимит GitHub (100 МиБ на файл) без заметной
потери качества печати. Перекодировка потоковая: исходник читается
последовательно, память не растёт.

Запуск:
  python3 scripts/banners/probe_quality.py <master.jpg> <Q> [<Q> ...]
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import pyvips

LIMIT = 100 * 1024 * 1024  # лимит GitHub на один файл


def probe(src: Path, q: int) -> tuple[int, float]:
    t0 = time.time()
    img = pyvips.Image.jpegload(str(src), access="sequential")
    out = Path("/tmp") / f"probe-{src.stem}-q{q}.jpg"
    img.write_to_file(str(out), Q=q, subsample_mode="off", strip=True)
    size = out.stat().st_size
    out.unlink(missing_ok=True)
    print(f"  Q={q:>3}: {size / 1024 / 1024:6.1f} МБ  "
          f"({'в лимите' if size <= LIMIT else 'больше лимита'})  "
          f"{time.time() - t0:.0f} с", flush=True)
    return size, time.time() - t0


def main() -> int:
    src = Path(sys.argv[1])
    qualities = [int(x) for x in sys.argv[2:]] or [88, 85, 82, 80]
    print(f"{src.name}: {src.stat().st_size / 1024 / 1024:.1f} МБ (исходник)")
    for q in qualities:
        probe(src, q)
    return 0


if __name__ == "__main__":
    sys.exit(main())
