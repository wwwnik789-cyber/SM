#!/usr/bin/env python3
"""План и фасад стенда Рег.ру — точные чертежи в миллиметрах.

Строит:
  plan/plan-1-50.svg          план сверху с размерами и нумерацией зон
  plan/plan-1-50.png          то же в растре
  plan/front-elevation.svg    фасад 6000 мм с высотами
  plan/front-elevation.png

1 единица SVG = 1 мм стенда, а физический размер листа выставлен как 1:50 —
файл печатается «как есть», без масштабирования: план 214 × 144 мм,
фасад 158 × 100 мм (обе влезают в A4 горизонтально с полями).
В цех уходит SVG, PNG — для писем и превью.

Запуск из корня репозитория:
    .venv/bin/python docs/proekty/regru-stand-2026/plan/build_plan.py
"""

from __future__ import annotations

import re
from math import cos, radians, sin
from pathlib import Path

import resvg_py

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
FONT = REPO / "banners/anikom-arena-3000x2500-concepts/source/Montserrat-Variable.ttf"

# ── габариты, мм ────────────────────────────────────────────────────────────
W, D = 6000.0, 4000.0
H_WALL = 3000.0
H_TOP = 3200.0
TH = 120.0

INK = "#16222e"
MUTED = "#7b8794"
LINE = "#ccd5db"
GREEN = "#1f9d55"
GREEN_D = "#14663a"
GREEN_L = "#e2f4e9"
LILAC = "#b9a7e0"
LILAC_L = "#efe9f9"
YELLOW = "#efc14a"
YELLOW_L = "#fbf1cf"
GREY = "#ccd5db"
FLOOR = "#f8fafb"

# ── зоны: (x1, y1, x2, y2), Y вверх от переднего края ───────────────────────
MEETING = (0, 2600, 2400, 4000)
STORAGE = (2560, 2560, 3560, 4000)
LED = (3760, 3930, 5660, 4000)
COUNTER = (2050, 520, 3850, 1220)
KIOSK_A = (1450, 1600, 1850, 2000)
KIOSK_B = (4000, 1600, 4400, 2000)
TABLE_C = (5150, 2750)
TABLE_D = 1100
PHOTO = (5880, 700, 6000, 3100)
NICHE_W, NICHE_H = 460, 300
NICHE_Y = [240, 800, 1360, 1920]
NICHE_NAMES = ["ДОМЕНЫ", "ХОСТИНГ", "SSL", "РЕГ.ОБЛАКО"]
STOOLS = [(2350, 300), (2950, 300), (3550, 300)]


# ── примитивы ───────────────────────────────────────────────────────────────

def head(width: float, height: float) -> list[str]:
    return [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width / 50:g}mm" '
        f'height="{height / 50:g}mm" viewBox="0 0 {width:g} {height:g}" version="1.1">',
        "  <style>",
        "    text{font-family:'Montserrat','DejaVu Sans',Arial,sans-serif;fill:" + INK + "}",
        "    .title{font-size:190px;font-weight:600;letter-spacing:-2px}",
        "    .sub{font-size:104px;fill:" + MUTED + "}",
        "    .zone{font-size:120px;font-weight:600;letter-spacing:2px}",
        "    .label{font-size:100px}",
        "    .small{font-size:86px;fill:" + MUTED + "}",
        "    .dim{font-size:88px;fill:" + MUTED + "}",
        "    .num{font-size:96px;font-weight:700;fill:#ffffff}",
        "  </style>",
    ]


def rect(x, y, w, h, fill="none", stroke=INK, sw=9, extra=""):
    return (f'  <rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{sw:g}" {extra}/>')


def line(x1, y1, x2, y2, stroke=INK, sw=9, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'  <line x1="{x1:g}" y1="{y1:g}" x2="{x2:g}" y2="{y2:g}" stroke="{stroke}" '
            f'stroke-width="{sw:g}"{d}/>')


def text(x, y, value, cls="label", anchor="start", fill=None, rotate=None):
    extra = f' text-anchor="{anchor}"'
    if fill:
        extra += f' fill="{fill}"'
    if rotate:
        extra += f' transform="rotate({rotate} {x:g} {y:g})"'
    return f'  <text x="{x:g}" y="{y:g}" class="{cls}"{extra}>{value}</text>'


def circle(cx, cy, r, fill="none", stroke=MUTED, sw=8):
    return (f'  <circle cx="{cx:g}" cy="{cy:g}" r="{r:g}" fill="{fill}" stroke="{stroke}" '
            f'stroke-width="{sw:g}"/>')


def badge(cx, cy, number):
    return [circle(cx, cy, 115, GREEN, "#ffffff", 0),
            text(cx, cy + 36, f"{number:02d}", "num", "middle")]


def hdim(x1, x2, y, value, above=True) -> list[str]:
    out = [line(x1, y, x2, y, MUTED, 5),
           line(x1, y - 60, x1, y + 60, MUTED, 5),
           line(x2, y - 60, x2, y + 60, MUTED, 5)]
    out.append(text((x1 + x2) / 2, y - 60 if above else y + 175, value, "dim", "middle"))
    return out


def vdim(y1, y2, x, value) -> list[str]:
    out = [line(x, y1, x, y2, MUTED, 5),
           line(x - 60, y1, x + 60, y1, MUTED, 5),
           line(x - 60, y2, x + 60, y2, MUTED, 5)]
    out.append(text(x - 55, (y1 + y2) / 2, value, "dim", "middle", rotate=-90))
    return out


# ── план ────────────────────────────────────────────────────────────────────

ZONES = [
    (GREEN_L, "Переговорка 2,4 × 1,4 м · стекло, 4 места"),
    (LILAC_L, "LED-стена 1,9 × 1,07 м на задней стене"),
    ("#eef1f3", "Стена продуктов: 4 ниши по 1,0 × 0,8 м"),
    ("#ffffff", "Стойка регистрации 1,8 × 0,7 м, 2 экрана"),
    (GREEN, "Киоски самообслуживания 0,4 × 0,4 м"),
    ("#ffffff", "Демо-стол Ø1,1 м, 4 посадочных места"),
    (YELLOW_L, "Фотозона: бренд-стена 2,4 × 2,6 м, контражур"),
    ("#eef1f3", "Кладовая 1,0 × 1,44 м под стеллаж"),
]


def build_plan() -> str:
    pad_l, pad_r, pad_t, pad_b = 1250.0, 3450.0, 1450.0, 1750.0
    width = W + pad_l + pad_r
    height = D + pad_t + pad_b
    ox, oy = pad_l, pad_t + D

    def X(x):  # noqa: N802
        return ox + x

    def Y(y):  # noqa: N802
        return oy - y

    body = head(width, height)
    body.append(rect(0, 0, width, height, "#ffffff", "#ffffff", 0))
    body.append(text(X(0), 430, "СТЕНД «РЕГ.РУ» · ПЛАН 1:50", "title"))
    body.append(text(X(0), 610, "6 000 × 4 000 мм · стены 3 000 · пилоны и фриз 3 200 · "
                                "размеры в миллиметрах", "sub"))

    # пол, стены
    body.append(rect(X(0), Y(D), W, D, FLOOR, INK, 13))
    body.append(rect(X(0), Y(D), W, TH, GREY, INK, 9))
    body.append(rect(X(0), Y(D), TH, D, GREY, INK, 9))

    # сетка
    for gx in range(1000, int(W), 1000):
        body.append(line(X(gx), Y(D) + TH, X(gx), Y(0), LINE, 4, "44 44"))
    for gy in range(1000, int(D), 1000):
        body.append(line(X(0) + TH, Y(gy), X(W), Y(gy), LINE, 4, "44 44"))

    # 01 переговорка
    mx1, my1, mx2, my2 = MEETING
    body.append(rect(X(mx1), Y(my2), mx2 - mx1, my2 - my1, LILAC_L, LILAC, 14))
    body.append(line(X(mx1), Y(my1), X(mx2), Y(my1), LILAC, 20, "70 34"))
    body.append(line(X(mx2 - TH), Y(my1), X(mx2 - TH), Y(my2), LILAC, 20, "70 34"))
    body.append(circle(X(mx1 + 760), Y(my2 - 780), 250, "#ffffff", LILAC, 11))
    body.append(circle(X(mx1 + 760), Y(my2 - 780), 105, "#ffffff", LILAC, 9))
    for seat in (-1.5, -0.5, 0.5, 1.5):
        body.append(circle(X(mx1 + 760 + seat * 320), Y(my2 - 780 - 430), 85, LILAC_L, LILAC, 7))
        body.append(circle(X(mx1 + 760 + seat * 320), Y(my2 - 780 + 430), 85, LILAC_L, LILAC, 7))
    # раздвижная дверь
    body.append(line(X(mx2 - 1050), Y(my1), X(mx2 - 140), Y(my1), "#ffffff", 28))
    body.append(line(X(mx2 - 1050), Y(my1), X(mx2 - 1050), Y(my1 - 860), LILAC, 9, "34 26"))

    # 08 кладовая
    sx1, sy1, sx2, sy2 = STORAGE
    body.append(rect(X(sx1), Y(sy2), sx2 - sx1, sy2 - sy1, "#eef1f3", INK, 13))
    body.append(line(X(sx1 + 130), Y(sy1), X(sx2 - 90), Y(sy1), "#ffffff", 24))
    # стеллаж
    for shelf in range(3):
        body.append(line(X(sx1 + 120), Y(sy1 + 300 + shelf * 380), X(sx2 - 120),
                         Y(sy1 + 300 + shelf * 380), GREY, 8))

    # 02 LED-стена
    lx1, ly1, lx2, ly2 = LED
    body.append(rect(X(lx1), Y(ly2), lx2 - lx1, 80, INK, INK, 0))

    # 03 стена продуктов
    for index, ny in enumerate(NICHE_Y):
        body.append(rect(X(TH), Y(ny + NICHE_H), NICHE_W, NICHE_H, GREEN_L, GREEN, 11))
        body.append(text(X(TH + NICHE_W + 130), Y(ny + NICHE_H / 2 + 34),
                         NICHE_NAMES[index], "label", fill=GREEN_D))

    # 04 стойка
    cx1, cy1, cx2, cy2 = COUNTER
    body.append(rect(X(cx1), Y(cy2), cx2 - cx1, cy2 - cy1, "#ffffff", INK, 13))
    body.append(rect(X(cx1), Y(cy2), cx2 - cx1, 80, GREEN, GREEN, 0))
    for index in range(2):
        body.append(rect(X(cx1 + 1180 + index * 420), Y(cy1 + 300), 230, 150, LINE, MUTED, 6))
    for sx, sy in STOOLS:
        body.append(circle(X(sx), Y(sy), 165, "#ffffff", MUTED, 10))

    # 05 киоски
    for kx1, ky1, kx2, ky2 in (KIOSK_A, KIOSK_B):
        body.append(rect(X(kx1), Y(ky2), kx2 - kx1, ky2 - ky1, GREEN, GREEN, 6))
        body.append(text(X((kx1 + kx2) / 2), Y((ky1 + ky2) / 2 + 40), "Т", "label",
                         "middle", fill="#ffffff"))

    # 06 демо-стол
    tx, ty = TABLE_C
    body.append(circle(X(tx), Y(ty), TABLE_D / 2, "#ffffff", INK, 13))
    body.append(text(X(tx), Y(ty + 140), "ДЕМО", "zone", "middle"))
    body.append(text(X(tx), Y(ty - 40), "Рег.решения", "small", "middle"))
    for angle in (30, 120, 210, 300):
        dx = cos(radians(angle)) * (TABLE_D / 2 + 330)
        dy = sin(radians(angle)) * (TABLE_D / 2 + 330)
        body.append(circle(X(tx + dx), Y(ty + dy), 165, "#ffffff", MUTED, 10))

    # 07 фотозона
    px1, py1, px2, py2 = PHOTO
    body.append(rect(X(px1), Y(py2), px2 - px1, py2 - py1, YELLOW_L, YELLOW, 14))

    # нумерация зон
    for cx, cy, num in (
        (mx2 - 330, my2 - 330, 1),
        ((lx1 + lx2) / 2, ly2 - 250, 2),
        (TH + NICHE_W / 2, NICHE_Y[3] + NICHE_H + 210, 3),
        (cx1 + 300, cy2 - 330, 4),
        (KIOSK_A[2] + 320, KIOSK_A[3] + 240, 5),
        (tx - TABLE_D / 2 - 380, ty, 6),
        (px1 + (px2 - px1) / 2, py2 - 300, 7),
        (sx2 - 340, sy2 - 340, 8),
    ):
        for part in badge(X(cx), Y(cy), num):
            body.append(part)

    # размеры сверху и по цепочке
    for part in hdim(X(0), X(W), Y(D) - 430, "6 000"):
        body.append(part)
    chain = Y(0) + 520
    for part in hdim(X(0), X(2050), chain, "2 050"):
        body.append(part)
    for part in hdim(X(2050), X(3850), chain, "1 800"):
        body.append(part)
    for part in hdim(X(3850), X(W), chain, "2 150"):
        body.append(part)
    for part in hdim(X(0), X(W), chain + 420, "6 000"):
        body.append(part)

    # вертикальные размеры
    for part in vdim(Y(0), Y(D), X(0) - 430, "4 000"):
        body.append(part)
    for part in vdim(Y(0), Y(my1), X(0) - 180, "2 600"):
        body.append(part)

    # вход и ось
    body.append(text(X(W - 80), Y(200), "ВХОД", "zone", "end", fill=MUTED))
    body.append(text(X(W - 80), Y(60), "открытая сторона", "small", "end"))
    body.append(line(X(W / 2), Y(0) + 1050, X(W / 2), Y(D) - 640, "#d64545", 5, "160 70 32 70"))
    body.append(circle(X(W / 2), Y(D) - 700, 46, "#d64545", "#d64545", 0))

    # таблица зон справа
    tx0 = X(W) + 520
    ty0 = Y(D) + 60
    body.append(text(tx0, ty0, "ЗОНЫ", "zone", fill=GREEN_D))
    body.append(line(tx0, ty0 + 60, tx0 + 2000, ty0 + 60, GREEN, 8))
    for index, (colour, caption) in enumerate(ZONES):
        yy = ty0 + 200 + index * 430
        body.append(rect(tx0, yy, 190, 120, colour, INK, 7))
        body.append(text(tx0 + 80, yy + 92, f"{index + 1:02d}", "label", "middle", fill=INK))
        # перенос подписи по смыслу на две строки
        head_part, _, tail = caption.partition(" · ")
        body.append(text(tx0 + 300, yy + 70, head_part, "label"))
        if tail:
            body.append(text(tx0 + 300, yy + 175, tail, "small"))
        else:
            body.append(text(tx0 + 300, yy + 165, "", "small"))

    body.append(text(X(0), Y(0) + 1180,
                     "Наружные размеры — по внешним граням, внутренние — до чистовых "
                     "поверхностей. Стены: каркас брус 100×100, обшивка ПВХ, натяжка.", "small"))
    body.append("</svg>")
    return "\n".join(body)


# ── фасад ───────────────────────────────────────────────────────────────────

def build_elevation() -> str:
    """Фасад с открытой стороны: пилоны, фриз, ниши, стойка, фотозона."""
    pad = 950.0
    width = W + pad * 2
    height = H_TOP + pad + 850
    base = pad + H_TOP
    body = head(width, height)

    def X(x):  # noqa: N802
        return pad + x

    body.append(rect(0, 0, width, height, "#ffffff", "#ffffff", 0))
    body.append(text(X(0), 400, "СТЕНД «РЕГ.РУ» · ФАСАД 1:50", "title"))
    body.append(text(X(0), 575, "вид с открытой стороны · 6 000 × 3 200 мм · размеры в мм", "sub"))

    PYLONS = [0.0, 1480.0, 3800.0, W - 240]
    PYLON_W = 240.0

    # стена и фриз
    body.append(rect(X(0), base - H_WALL, W, H_WALL, "#eef2f4", INK, 11))
    body.append(rect(X(0), base - H_TOP, W, H_TOP - H_WALL, GREEN, GREEN, 0))

    # надпись на фризе — в пролётах между пилонами
    slots = [(PYLONS[0] + PYLON_W, PYLONS[1]), (PYLONS[1] + PYLON_W, PYLONS[2]),
             (PYLONS[2] + PYLON_W, PYLONS[3])]
    captions = ["РЕГ.РУ", "СДЕЛАЙТЕ САМИ", "РЕГ.РЕШЕНИЯ"]
    for (x1, x2), caption in zip(slots, captions):
        body.append(text(X((x1 + x2) / 2), base - H_TOP + 165, caption, "zone", "middle",
                         fill="#ffffff"))

    # пилоны
    for px in PYLONS:
        body.append(rect(X(px), base - H_TOP, PYLON_W, H_TOP, "#e3e8ec", INK, 9))

    # ниши продуктов — в первом пролёте, по 4 в ряд
    niche_w, niche_h = 265, 1180
    start_x = PYLONS[0] + PYLON_W + 60
    for index in range(len(NICHE_NAMES)):
        nx = start_x + index * (niche_w + 25)
        body.append(rect(X(nx), base - 2680, niche_w, niche_h, "#ffffff", GREEN, 9))
        body.append(text(X(nx + niche_w / 2), base - 2520, f"0{index + 1}", "small",
                         "middle", fill=GREEN_D))
    # расшифровка ниш — строкой под рядом, чтобы подписи не наезжали
    body.append(text(X(start_x), base - 1330,
                     "01 домены · 02 хостинг · 03 SSL · 04 Рег.облако", "small", fill=GREEN_D))

    # кромка пола
    body.append(line(X(-160), base, X(W + 160), base, INK, 10))

    # стойка регистрации
    body.append(rect(X(1600), base - 1080, 1900, 1080, "#ffffff", INK, 13))
    body.append(rect(X(1600), base - 1080, 1900, 60, GREEN, GREEN, 0))
    body.append(text(X(1740), base - 880, "СТОЙКА", "label"))
    body.append(text(X(1740), base - 740, "проверка домена · 2 экрана", "small"))
    body.append(text(X(1740), base - 300, "1 900 × 1 080", "small"))

    # фотозона на правом пролёте
    body.append(rect(X(4080), base - 2600, 1180, 2600, YELLOW_L, YELLOW, 13))
    body.append(text(X(4670), base - 1980, "ФОТОЗОНА", "zone", "middle", fill="#8a6d1a"))
    body.append(text(X(4670), base - 1820, "2,4 × 2,6 м", "small", "middle", fill="#8a6d1a"))

    # киоск самообслуживания — отдельно, справа от стойки
    body.append(rect(X(3660), base - 980, 300, 980, GREEN, GREEN, 6))
    body.append(text(X(3810), base - 560, "Т", "zone", "middle", fill="#ffffff"))
    body.append(text(X(3810), base + 120, "киоск", "small", "middle", fill=MUTED))

    # высоты слева
    for value, yy, label in ((0, base, "0"), (H_WALL, base - H_WALL, "3 000"),
                             (H_TOP, base - H_TOP, "3 200")):
        body.append(line(X(-300), yy, X(W + 160), yy, MUTED, 5))
        body.append(text(X(-360), yy + 36, label, "dim", "end"))

    # размеры снизу
    for part in hdim(X(0), X(W), base + 300, "6 000"):
        body.append(part)
    for part in hdim(X(PYLONS[0]), X(PYLONS[1]), base + 660, "1 480"):
        body.append(part)
    for part in hdim(X(PYLONS[1]), X(PYLONS[2]), base + 660, "2 320"):
        body.append(part)
    for part in hdim(X(PYLONS[2]), X(PYLONS[3]), base + 660, "1 960"):
        body.append(part)

    body.append("</svg>")
    return "\n".join(body)


def rasterise(svg_path: Path, png_path: Path, width_px: int) -> None:
    markup = svg_path.read_text(encoding="utf-8")
    # 1 единица = 1 мм; физический размер листа (1:50) для растра не нужен
    markup = re.sub(r'(<svg[^>]*?) width="[\d.]+mm" height="[\d.]+mm"', r'\1', markup, count=1)
    png = bytes(resvg_py.svg_to_bytes(svg_string=markup, width=width_px,
                                      font_files=[str(FONT)], font_family="Montserrat"))
    png_path.write_bytes(png)


def main() -> None:
    HERE.mkdir(parents=True, exist_ok=True)
    (HERE / "plan-1-50.svg").write_text(build_plan(), encoding="utf-8")
    (HERE / "front-elevation.svg").write_text(build_elevation(), encoding="utf-8")
    rasterise(HERE / "plan-1-50.svg", HERE / "plan-1-50.png", 2400)
    rasterise(HERE / "front-elevation.svg", HERE / "front-elevation.png", 2400)
    for name in ("plan-1-50.png", "front-elevation.png"):
        print(f"  {name}: {(HERE / name).stat().st_size // 1024} КБ")


if __name__ == "__main__":
    main()
