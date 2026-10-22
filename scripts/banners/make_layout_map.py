#!/usr/bin/env python3
"""
Схема раскладки печатного файла 300 × 270 см для серии «Кастинг».

Рисует техническую карту конструкции: полотно, видимое лицо, загибы
по периметру и боковые уши с размерами.

Запуск:
  python3 scripts/banners/make_layout_map.py
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "banners/casting-series/preview/casting-300x270-layout.jpg"

CANVAS_W_CM, CANVAS_H_CM = 300, 270
EAR_CM, FOLD_CM = 40, 10
FACE_W_CM, FACE_H_CM = 220, 250

INK = (26, 22, 30)
PAPER = (247, 244, 240)
MUTED = (122, 112, 126)
FACE_C = (236, 226, 218)
FOLD_C = (211, 193, 203)
EAR_C = (245, 238, 231)
ACCENT = (150, 22, 74)
GOLD = (186, 132, 48)

FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
F_REG = FONT_DIR / "DejaVuSans.ttf"
F_BOLD = FONT_DIR / "DejaVuSans-Bold.ttf"


def main() -> int:
    w, h = 2000, 1250
    img = Image.new("RGB", (w, h), PAPER)
    d = ImageDraw.Draw(img)

    f_title = ImageFont.truetype(str(F_BOLD), 38)
    f_sub = ImageFont.truetype(str(F_REG), 25)
    f_label = ImageFont.truetype(str(F_BOLD), 28)
    f_small = ImageFont.truetype(str(F_REG), 21)
    f_num = ImageFont.truetype(str(F_BOLD), 26)

    d.text((70, 52), "СЕРИЯ «КАСТИНГ» · РАСКЛАДКА ПОД КОНСТРУКЦИЮ 300 × 270 СМ",
           font=f_title, fill=INK)
    d.text((70, 104), "Печатный файл 300 × 270 см · видимое лицо 220 × 250 см · "
                      "загибы 10 см по периметру · уши 40 см по бокам",
           font=f_sub, fill=MUTED)

    # рабочее поле схемы
    mx, my = 70, 170
    mw, mh = 1180, 950
    scale = min(mw / CANVAS_W_CM, mh / CANVAS_H_CM)
    ox = mx + (mw - CANVAS_W_CM * scale) / 2
    oy = my + (mh - CANVAS_H_CM * scale) / 2

    def box(x0, y0, x1, y1):
        return [ox + x0 * scale, oy + y0 * scale, ox + x1 * scale, oy + y1 * scale]

    def label(x0, y0, x1, y1, text, font, fill=INK):
        d.text(((x0 + x1) / 2, (y0 + y1) / 2), text, font=font, fill=fill, anchor="mm")

    def label_v(cx, cy, text, font, fill=MUTED):
        """Вертикальная подпись (поворот на 90°) для узких полос загибов."""
        tmp = Image.new("RGBA", (700, 140), (0, 0, 0, 0))
        ImageDraw.Draw(tmp).text((350, 70), text, font=font, fill=fill, anchor="mm")
        tmp = tmp.rotate(90, expand=True)
        img.paste(tmp, (int(cx - tmp.width / 2), int(cy - tmp.height / 2)), tmp)

    canvas = box(0, 0, CANVAS_W_CM, CANVAS_H_CM)
    d.rectangle(canvas, fill=(240, 233, 229), outline=INK, width=3)

    # уши: 40 см с каждой стороны (10 см загиб + 30 см видимая часть)
    d.rectangle(box(0, 0, EAR_CM, CANVAS_H_CM), fill=EAR_C, outline=MUTED, width=2)
    d.rectangle(box(CANVAS_W_CM - EAR_CM, 0, CANVAS_W_CM, CANVAS_H_CM), fill=EAR_C,
                outline=MUTED, width=2)

    # загибы: 10 см по периметру (полосы идут вплотную к лицу)
    lfold = box(EAR_CM - FOLD_CM, 0, EAR_CM, CANVAS_H_CM)
    rfold = box(CANVAS_W_CM - EAR_CM, 0, CANVAS_W_CM - EAR_CM + FOLD_CM, CANVAS_H_CM)
    d.rectangle(lfold, fill=FOLD_C, outline=MUTED, width=2)
    d.rectangle(rfold, fill=FOLD_C, outline=MUTED, width=2)
    d.rectangle(box(EAR_CM - FOLD_CM, 0, CANVAS_W_CM - EAR_CM + FOLD_CM, FOLD_CM),
                fill=FOLD_C, outline=MUTED, width=2)
    d.rectangle(box(EAR_CM - FOLD_CM, CANVAS_H_CM - FOLD_CM,
                    CANVAS_W_CM - EAR_CM + FOLD_CM, CANVAS_H_CM), fill=FOLD_C, outline=MUTED, width=2)

    # лицо
    face = box(EAR_CM, FOLD_CM, EAR_CM + FACE_W_CM, FOLD_CM + FACE_H_CM)
    d.rectangle(face, fill=FACE_C, outline=ACCENT, width=4)

    label(*face, "ВИДИМОЕ ЛИЦО\n220 × 250 см", f_label, INK)
    d.text((face[0] + 30, face[1] + 20), "зона печати «в раму»", font=f_small, fill=ACCENT)
    d.text((face[2] - 30, face[3] - 24), "все элементы — внутри лица", font=f_small,
           fill=MUTED, anchor="rs")

    # боковые загибы — вертикальные подписи в узких полосах
    label_v((lfold[0] + lfold[2]) / 2, (lfold[1] + lfold[3]) / 2, "ЗАГИБ 10 см", f_small)
    label_v((rfold[0] + rfold[2]) / 2, (rfold[1] + rfold[3]) / 2, "ЗАГИБ 10 см", f_small)

    label(*box(EAR_CM, 0, CANVAS_W_CM - EAR_CM, FOLD_CM), "ЗАГИБ 10 см — ПОДГИБ К РАМЕ",
          f_small, MUTED)
    label(*box(EAR_CM, CANVAS_H_CM - FOLD_CM, CANVAS_W_CM - EAR_CM, CANVAS_H_CM),
          "ЗАГИБ 10 см — ПОДГИБ К РАМЕ", f_small, MUTED)
    label(*box(0, 14, EAR_CM - FOLD_CM, 34), "УХО\n30 см", f_small, MUTED)
    label(*box(CANVAS_W_CM - EAR_CM + FOLD_CM, 14, CANVAS_W_CM, 34), "УХО\n30 см", f_small, MUTED)

    # размерные линии
    def dim_h(x0, x1, y, text):
        d.line([x0, y, x1, y], fill=GOLD, width=3)
        for x in (x0, x1):
            d.line([x, y - 9, x, y + 9], fill=GOLD, width=3)
        d.text(((x0 + x1) / 2, y - 16), text, font=f_num, fill=GOLD, anchor="ms")

    def dim_v(y0, y1, x, text, side="right"):
        d.line([x, y0, x, y1], fill=GOLD, width=3)
        for y in (y0, y1):
            d.line([x - 9, y, x + 9, y], fill=GOLD, width=3)
        anchor = "rm" if side == "right" else "lm"
        off = -14 if side == "right" else 14
        d.text((x + off, (y0 + y1) / 2), text, font=f_num, fill=GOLD, anchor=anchor)

    dim_h(canvas[0], canvas[2], canvas[3] + 74, "300 см")
    dim_v(canvas[1], canvas[3], canvas[2] + 56, "270 см")
    dim_h(face[0], face[2], face[3] - 66, "220 см")
    dim_v(face[1], face[3], face[2] - 18, "250 см")

    # легенда справа
    lx = 1320
    ly = 210
    d.text((lx, ly), "ЧТО ГДЕ", font=f_title, fill=INK)
    ly += 60
    legend = [
        ((240, 233, 229), "Полотно печати 300 × 270 см — единый файл под конструкцию"),
        ((236, 226, 218), "Видимое лицо 220 × 250 см — то, что видит зритель"),
        ((211, 193, 203), "Загиб 10 см по периметру — уходит на подгиб к раме"),
        ((245, 238, 231), "Ухо 40 см: 10 см загиб + 30 см видимая боковая часть"),
    ]
    for color, text in legend:
        d.rectangle([lx, ly, lx + 30, ly + 24], fill=color, outline=MUTED, width=2)
        words = text.split()
        line = ""
        for word in words:
            if d.textlength(line + " " + word, font=f_small) > 560:
                d.text((lx + 46, ly - 2), line, font=f_small, fill=INK)
                ly += 28
                line = word
            else:
                line = (line + " " + word).strip()
        if line:
            d.text((lx + 46, ly - 2), line, font=f_small, fill=INK)
            ly += 28
        ly += 14

    ly += 20
    d.text((lx, ly), "ПЕЧАТЬ", font=f_title, fill=INK)
    ly += 52
    for text in ("300 dpi, sRGB, 4:4:4", "без вылетов, единый файл",
                 "цвет и адрес QR — на усмотрение клиента",
                 "QR в файле: https://model.dvkino.ru"):
        d.text((lx, ly), "· " + text, font=f_small, fill=INK)
        ly += 30

    d.text((70, h - 78), "Сборка: scripts/banners/build_300x270.py · "
                         "схема: scripts/banners/make_layout_map.py",
           font=f_small, fill=MUTED)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, quality=92, subsampling=0)
    print(f"Схема: {OUT.relative_to(ROOT)} ({img.size[0]}×{img.size[1]}, "
          f"{OUT.stat().st_size // 1024} КБ)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
