#!/usr/bin/env python3
"""
Концепция «КАСТИНГ-ЛИСТ» — альтернативный стиль серии «Кастинг».

Вместо сценического маджента с золотом — редакционная «бумага»:
тёплый off-white, глубокий сине-чёрный, вермильон как акцент.
Фотографии всех трёх макетов приводятся к одному дуотону
(сине-чёрные тени → кремовые света), поэтому разные исходники читаются
как один визуальный ряд.

Композиция лица 220 × 250 см:
  • шапка: монограмма + слово PRODUCTION слева, «ЛИСТ 01 / 03» справа;
  • фотополоса во всю ширину (в уши уходит зеркальным продолжением);
  • подпись под полосой;
  • крупный заголовок в три ступени: кикер / огромное слово / подпись;
  • QR-карточка справа;
  • таблица данных внизу (формат / площадка / город / статус).

Весь текст держится в безопасной зоне 40…180 см: уши — зеркало крайних
40 см лица, и текст там читался бы задом наперёд.

Запуск (превью лица, быстро):
  python3 scripts/banners/concept_sheet.py preview
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import segno

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FONTS = HERE / "fonts"
PRINT_DIR = ROOT / "banners/casting-series/print"

# --------------------------------------------------------------------------
# Палитра и геометрия
# --------------------------------------------------------------------------
PAPER = (243, 238, 228)
INK = (20, 23, 41)
ACCENT = (226, 58, 32)
MUTED = (124, 121, 114)
PHOTO_SHADOW = (21, 26, 46)
PHOTO_LIGHT = (246, 240, 226)

FACE_W_CM, FACE_H_CM = 220, 250
SAFE_L, SAFE_R = 40.0, 180.0

HEADER_Y = 8.0
RULE_Y = 17.6
BAND_Y0, BAND_Y1 = 20.0, 153.0
CAPTION_Y = 156.6
RULE2_Y = 165.0
KICKER_Y = 170.0
HUGE_Y = 178.0
SUB_Y = 205.0
DATA_RULE_Y = 214.0
DATA_LABEL_Y = 216.5
DATA_VALUE_Y = 221.0
QR_Y0, QR_SIZE = 214.0, 21.0
QR_MODULE_CM = 0.55
QR_CAPTION_Y = 236.0
DATA_RIGHT = 152.0
BOTTOM_SAFE = 238.0

QR_TARGET = "https://model.dvkino.ru"

# --------------------------------------------------------------------------
# Содержание трёх листов
# --------------------------------------------------------------------------
CONTENT = {
    "kino": {
        "index": "01",
        "kicker": "ОТКРЫТЫЙ КАСТИНГ",
        "huge": ["ПРОБЫ"],
        "huge_size": 19.0,
        "sub": "в кино · кинопробы на новые роли",
        "caption_l": "КАДР · ЗРИТЕЛЬНЫЙ ЗАЛ",
        "caption_r": "КИНО · МОСКВА",
        "data": [("ФОРМАТ", "КИНО"), ("ПЛОЩАДКА", "ПРОБЫ"),
                 ("ГОРОД", "МОСКВА · СПБ"), ("СТАТУС", "ОТКРЫТО")],
        "status_accent": True,
        "src": (0, 4560, 4608, 7320),
    },
    "pokaz": {
        "index": "02",
        "kicker": "ОТКРЫТЫЙ КАСТИНГ",
        "huge": ["ПОКАЗ"],
        "huge_size": 19.0,
        "sub": "модный показ · съёмки для каталога",
        "caption_l": "КАДР · ПОДИУМ",
        "caption_r": "ПОКАЗ · МОСКВА",
        "data": [("ФОРМАТ", "ПОКАЗ"), ("ПЛОЩАДКА", "СЪЁМКА"),
                 ("ГОРОД", "МОСКВА · СПБ"), ("СТАТУС", "ОТКРЫТО")],
        "status_accent": True,
        "src": (0, 4070, 5088, 7146),
    },
    "dv-production": {
        "index": "03",
        "kicker": "ПРОДЮСЕРСЬКИЙ ЦЕНТР",
        "huge": ["ДВ ПРОДАКШЕН"],
        "huge_size": 12.0,
        "sub": "актёрско-модельная студия",
        "caption_l": "КАДР · СЦЕНА",
        "caption_r": "СТУДИЯ · МОСКВА",
        "data": [("ФОРМАТ", "СТУДИЯ"), ("ПЛОЩАДКА", "ПРОДАКШЕН"),
                 ("ГОРОД", "МОСКВА · СПБ"), ("СТАТУС", "РАБОТАЕТ")],
        "status_accent": False,
        "src": (819, 3420, 5325, 6144),
    },
}

SOURCES = {
    "kino": PRINT_DIR / "banner-kasting-proby-v-kino-4608x8256.jpg",
    "pokaz": PRINT_DIR / "banner-kasting-modnyy-pokaz-5088x7584.jpg",
    "dv-production": PRINT_DIR / "banner-dv-production-original-6144x6144.jpg",
}

CYR = set("АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдежзийклмнопрстуфхцчшщъыьэюя"
          "ЁёЄєІіЇїҐґ")


# --------------------------------------------------------------------------
# Текст со смешанными шрифтами: кириллица и латиница из разных сабсетов
# --------------------------------------------------------------------------
def _font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONTS / name), size)


def _pick(ch: str, cyr: ImageFont.FreeTypeFont, lat: ImageFont.FreeTypeFont):
    return cyr if ch in CYR else lat


def text_mask(lines, size: int, tracking: int, line_gap: float = 1.18,
              fonts=("Unbounded-700.ttf", "Unbounded-700-latin.ttf"),
              align: str = "left") -> Image.Image:
    """Маска набора со трекингом. lines — список строк."""
    cyr = _font(fonts[0], size)
    lat = _font(fonts[1], size)
    probe = ImageDraw.Draw(Image.new("L", (8, 8)))

    widths = []
    for line in lines:
        w = sum(probe.textlength(ch, font=_pick(ch, cyr, lat)) for ch in line)
        widths.append(w + tracking * max(0, len(line) - 1))

    line_h = int(size * line_gap)
    width = int(max(widths)) + 2
    height = int(line_h * (len(lines) - 1) + size * 1.35)
    mask = Image.new("L", (width, height), 0)
    d = ImageDraw.Draw(mask)
    for i, line in enumerate(lines):
        if align == "left":
            x = 0.0
        elif align == "right":
            x = width - widths[i]
        else:
            x = (width - widths[i]) / 2
        y = size * 1.02 + i * line_h
        for ch in line:
            f = _pick(ch, cyr, lat)
            d.text((x, y), ch, font=f, fill=255, anchor="ls")
            x += probe.textlength(ch, font=f) + tracking
    return mask


def text_layer(lines, size: int, tracking: int, color, line_gap: float = 1.18,
               fonts=("Unbounded-700.ttf", "Unbounded-700-latin.ttf"),
               align: str = "left") -> Image.Image:
    """Цветной слой с набором (RGBA)."""
    mask = text_mask(lines, size, tracking, line_gap, fonts, align)
    layer = Image.new("RGBA", mask.size, color + (255,))
    layer.putalpha(mask)
    return layer


def rule(x0: float, x1: float, y: float, thickness: float, color,
         S: float) -> Image.Image:
    """Волосяная линия (RGBA)."""
    w = max(1, int(round((x1 - x0) * S)))
    h = max(1, int(round(thickness * S)))
    return Image.new("RGBA", (w, h), color + (255,))


def qr_card(size: int, module_px: int, url: str = QR_TARGET) -> Image.Image:
    """QR на белой карточке: чёрные модули, тихая зона, поля."""
    code = segno.make(url, error="m", version=3)
    m = code.matrix
    n = len(m)
    border = 3
    pad = max(4, size // 14)
    img = Image.new("L", (n, n), 0)
    for y in range(n):
        for x in range(n):
            img.putpixel((x, y), 255 if m[y][x] else 0)
    img = img.resize((n * module_px, n * module_px), Image.NEAREST)
    card = Image.new("RGB", (size, size), (255, 255, 255))
    card.paste(Image.new("RGB", img.size, INK), (pad, pad), img.convert("L"))
    return card


# --------------------------------------------------------------------------
# Фото: дуотон
# --------------------------------------------------------------------------
def duotone(arr: np.ndarray, shadow=PHOTO_SHADOW, light=PHOTO_LIGHT,
             contrast: float = 1.32, gamma: float = 0.98) -> np.ndarray:
    """Серый → дуотон: тени в сине-чёрный, света в кремовый."""
    g = (0.2126 * arr[:, :, 0] + 0.7152 * arr[:, :, 1]
         + 0.0722 * arr[:, :, 2]).astype(np.float32) / 255.0
    g = np.clip((g - 0.5) * contrast + 0.5, 0, 1)
    g = g * g * (3 - 2 * g)
    g = np.clip(g, 0, 1) ** gamma
    out = np.empty_like(arr, dtype=np.float32)
    for c in range(3):
        out[:, :, c] = shadow[c] + (light[c] - shadow[c]) * g
    return np.clip(out, 0, 255).astype(np.uint8)


def photo_slice(arr: np.ndarray, src_rect, dst_y0: float, dst_y1: float,
                band_y0: float, band_y1: float, S: float, tone: bool = True):
    """Полоса фотопластины под текущий диапазон строк лица.

    Возвращает (картинка, верх полосы в px лица) или (None, None).
    Высота подгоняется точно под пиксельный диапазон полосы — иначе
    между полосами остаётся бумажный шов в 1 px.
    tone=True — привести строки к дуотону прямо здесь (экономит память:
    для мастера обрабатывается только нужная полоса исходника).
    """
    sx0, sy0, sx1, sy1 = src_rect
    band_h = dst_y1 - dst_y0
    # Кадр подгоняется под пропорции полосы (220 см × band_h см) по центру.
    target = FACE_W_CM / band_h
    cur_w, cur_h = sx1 - sx0, sy1 - sy0
    if cur_w / cur_h > target:
        nw = int(round(cur_h * target))
        sx0 += (cur_w - nw) // 2
        sx1 = sx0 + nw
    else:
        nh = int(round(cur_w / target))
        sy0 += (cur_h - nh) // 2
        sy1 = sy0 + nh

    d0, d1 = max(band_y0, dst_y0), min(band_y1, dst_y1)
    if d1 <= d0:
        return None, None
    src_per_cm = (sy1 - sy0) / band_h
    p0 = int(round(d0 * S))
    p1 = int(round(d1 * S))
    top = sy0 + (d0 - dst_y0) * src_per_cm
    bot = sy0 + (d1 - dst_y0) * src_per_cm
    y0 = max(0, int(np.floor(top)))
    y1 = min(arr.shape[0], int(np.ceil(bot)))
    sub = arr[y0:y1, sx0:sx1]
    if tone:
        sub = duotone(sub)
    src = Image.fromarray(sub)
    out_w = int(round(FACE_W_CM * S))
    out_h = max(1, p1 - p0)
    return src.resize((out_w, out_h), Image.LANCZOS), p0


# --------------------------------------------------------------------------
# Слои макета
# --------------------------------------------------------------------------
def build_layers(key: str, S: float, logo=None):
    """Все элементы лица: список (RGBA-картинка, x_px, y_px).

    logo — пара (монограмма, слово PRODUCTION) в RGBA или None.
    """
    c = CONTENT[key]
    layers = []

    def add(img: Image.Image, x_cm: float, y_cm: float, anchor: str = "lt"):
        if anchor == "rt":
            x_cm -= img.width / S
        elif anchor == "mb":
            y_cm -= img.height / S
        layers.append((img, int(round(x_cm * S)), int(round(y_cm * S))))

    # шапка: монограмма + PRODUCTION
    if logo is not None:
        mono_src, word_src = logo
        mono_h = 5.0
        mono_w = mono_h * mono_src.width / mono_src.height
        mono = mono_src.resize((int(round(mono_w * S)), int(mono_h * S)),
                               Image.LANCZOS)
        ink_mono = Image.new("RGBA", mono.size, INK + (255,))
        ink_mono.putalpha(mono.getchannel("A"))
        add(ink_mono, SAFE_L, HEADER_Y)

        word_h = 1.25
        word_w = word_h * word_src.width / word_src.height
        word_img = word_src.resize((int(round(word_w * S)), int(word_h * S)),
                                   Image.LANCZOS)
        ink_word = Image.new("RGBA", word_img.size, INK + (255,))
        ink_word.putalpha(word_img.getchannel("A"))
        add(ink_word, SAFE_L + mono_w + 1.8, HEADER_Y + mono_h - word_h, anchor="mb")
    else:
        head = text_layer(["ДВ ПРОДАКШЕН"], int(2.6 * S), int(0.22 * S), INK,
                          fonts=("Unbounded-700.ttf", "Unbounded-700-latin.ttf"))
        add(head, SAFE_L, HEADER_Y)

    # шапка справа: номер листа
    idx = text_layer([c["index"]], int(6.0 * S), 0, ACCENT,
                     fonts=("Unbounded-700.ttf", "Unbounded-700-latin.ttf"))
    add(idx, SAFE_R, HEADER_Y - 1.0, anchor="rt")
    of = text_layer([f"/ 03"], int(2.0 * S), 0, MUTED,
                    fonts=("Unbounded-700.ttf", "Unbounded-700-latin.ttf"))
    add(of, SAFE_R, HEADER_Y + 5.0, anchor="rt")

    # линейки
    add(rule(SAFE_L, SAFE_R, RULE_Y, 0.12, INK, S), SAFE_L, RULE_Y)
    add(rule(0, FACE_W_CM, BAND_Y1, 0.22, INK, S), 0, BAND_Y1)
    add(rule(SAFE_L, SAFE_R, RULE2_Y, 0.10, MUTED, S), SAFE_L, RULE2_Y)

    # подпись под фотополосой
    cap_fonts = ("Manrope-500.ttf", "Manrope-500-latin.ttf")
    add(text_layer([c["caption_l"]], int(1.7 * S), int(0.3 * S), MUTED, fonts=cap_fonts),
        SAFE_L, CAPTION_Y)
    add(text_layer([c["caption_r"]], int(1.7 * S), int(0.3 * S), MUTED, fonts=cap_fonts),
        SAFE_R, CAPTION_Y, anchor="rt")

    # кикер
    add(text_layer([c["kicker"]], int(2.9 * S), int(0.42 * S), ACCENT,
                   fonts=("Manrope-500.ttf", "Manrope-500-latin.ttf")), SAFE_L, KICKER_Y)

    # огромное слово
    huge = text_layer(c["huge"], int(c["huge_size"] * S), int(0.2 * S), INK,
                      fonts=("Unbounded-700.ttf", "Unbounded-700-latin.ttf"))
    add(huge, SAFE_L, HUGE_Y)

    # подпись под заголовком
    add(text_layer([c["sub"]], int(3.6 * S), int(0.12 * S), MUTED, fonts=cap_fonts),
        SAFE_L, SUB_Y)

    # QR-карточка — в правом нижнем углу, на одной линии с таблицей
    qr = qr_card(int(QR_SIZE * S), max(2, int(round(QR_MODULE_CM * S))))
    add(qr, SAFE_R - QR_SIZE, QR_Y0)
    add(text_layer(["СКАНИРУЙТЕ, ЧТОБЫ ЗАПИСАТЬСЯ"], int(1.05 * S), int(0.10 * S), INK,
                   fonts=cap_fonts), SAFE_R - QR_SIZE, QR_CAPTION_Y)

    # таблица данных
    add(rule(SAFE_L, DATA_RIGHT, DATA_RULE_Y, 0.10, INK, S), SAFE_L, DATA_RULE_Y)
    col_w = (DATA_RIGHT - SAFE_L) / len(c["data"])
    for i, (label, value) in enumerate(c["data"]):
        x = SAFE_L + i * col_w
        add(text_layer([label], int(1.5 * S), int(0.3 * S), MUTED, fonts=cap_fonts),
            x, DATA_LABEL_Y)
        color = ACCENT if (c["status_accent"] and label == "СТАТУС") else INK
        add(text_layer([value], int(3.1 * S), int(0.1 * S), color, fonts=cap_fonts),
            x, DATA_VALUE_Y)

    # метки реза в углах безопасной зоны (уголки)
    m_len, m_th = 2.2, 0.09
    for x, y, dx, dy in ((SAFE_L, HEADER_Y, 1, 1), (SAFE_R, HEADER_Y, -1, 1),
                         (SAFE_L, BOTTOM_SAFE, 1, -1), (SAFE_R, BOTTOM_SAFE, -1, -1)):
        add(rule(0, m_len, 0, m_th, MUTED, S), x if dx > 0 else x - m_len, y)
        add(rule(0, m_th, 0, m_len, MUTED, S), x if dx > 0 else x - m_th,
            y if dy > 0 else y - m_len)

    return layers


def load_logo():
    """Монограмма и слово PRODUCTION из исходника ДВ ПРОДАКШЕН (RGBA)."""
    sys.path.insert(0, str(HERE))
    from edit_dv_production import extract_logo  # noqa: E402

    src = PRINT_DIR / "banner-dv-production-original-6144x6144.jpg"
    arr = np.array(Image.open(src).convert("RGB"))
    return extract_logo(arr)


def render_face(key: str, arr: np.ndarray, S: float, band_cm: float = 8.0,
                logo=None, emit=None):
    """Собирает лицо полосами. emit(y0_cm, y1_cm, image) — вывод полосы."""
    c = CONTENT[key]
    layers = build_layers(key, S, logo)
    face_w = int(round(FACE_W_CM * S))
    y = 0.0
    while y < FACE_H_CM:
        y1 = min(FACE_H_CM, y + band_cm)
        y0px, y1px = int(round(y * S)), int(round(y1 * S))
        img = Image.new("RGB", (face_w, y1px - y0px), PAPER)

        sl, top_px = photo_slice(arr, c["src"], BAND_Y0, BAND_Y1, y, y1, S)
        if sl is not None:
            img.paste(sl, (0, top_px - y0px))

        for tile, x, ty in layers:
            if ty + tile.height < y0px or ty > y1px:
                continue
            if tile.mode != "RGBA":
                tile = tile.convert("RGBA")
            img.paste(tile.convert("RGB"), (x, ty - y0px), tile.getchannel("A"))

        if emit is not None:
            emit(y, y1, img)
        y = y1


# --------------------------------------------------------------------------
# Сборка лица прямо в печатное полотно
# --------------------------------------------------------------------------
def blit(canvas: np.ndarray, tile: Image.Image, px: int, py: int,
         X0: int, Y0: int, face_w: int, face_h: int, chunk: int = 256) -> None:
    """Кладёт RGBA-слой на полотно с альфа-композитингом (по полосам).

    px, py — координаты слоя в полотне; X0, Y0 — левый верхний угол лица.
    """
    a = np.asarray(tile.convert("RGBA"))
    h, w = a.shape[:2]
    x0, x1 = max(px, X0), min(px + w, X0 + face_w)
    y0, y1 = max(py, Y0), min(py + h, Y0 + face_h)
    if x1 <= x0 or y1 <= y0:
        return
    for yy in range(y0, y1, chunk):
        yc = min(y1, yy + chunk)
        sub = a[yy - py:yc - py, x0 - px:x1 - px]
        alpha = sub[:, :, 3:4].astype(np.float32) / 255.0
        region = canvas[yy:yc, x0:x1]
        region[:] = (sub[:, :, :3].astype(np.float32) * alpha
                     + region.astype(np.float32) * (1.0 - alpha)).astype(np.uint8)


def build_face_canvas(key: str, canvas: np.ndarray, X0: int, Y0: int, S: float,
                      logo=None, band_cm: float = 8.0, text: bool = True) -> None:
    """Лицо 220 × 250 см в печатном полотне (numpy memmap).

    X0, Y0 — левый верхний угол лица в полотне; S — пикселей на сантиметр.
    """
    face_w = int(round(FACE_W_CM * S))
    face_h = int(round(FACE_H_CM * S))
    canvas[Y0:Y0 + face_h, X0:X0 + face_w] = PAPER

    arr = np.array(Image.open(SOURCES[key]).convert("RGB"))
    c = CONTENT[key]
    y = 0.0
    while y < FACE_H_CM:
        y1 = min(FACE_H_CM, y + band_cm)
        sl, top_px = photo_slice(arr, c["src"], BAND_Y0, BAND_Y1, y, y1, S)
        if sl is not None:
            canvas[Y0 + top_px:Y0 + top_px + sl.height,
                   X0:X0 + face_w] = np.asarray(sl)
        y = y1
    del arr

    if not text:
        return

    for tile, x, ty in build_layers(key, S, logo):
        blit(canvas, tile, X0 + x, Y0 + ty, X0, Y0, face_w, face_h)


def preview(key: str, S: float = 11.8, logo=None) -> Image.Image:
    """Быстрое превью лица (для правок макета)."""
    arr = np.array(Image.open(SOURCES[key]).convert("RGB"))
    rows = []

    def collect(y0, y1, img):
        rows.append(img)

    render_face(key, arr, S, band_cm=16.0, logo=logo, emit=collect)
    return _merge(rows)


def _merge(rows) -> Image.Image:
    out = Image.new("RGB", (rows[0].width, sum(r.height for r in rows)), PAPER)
    y = 0
    for r in rows:
        out.paste(r, (0, y))
        y += r.height
    return out


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "preview"
    if cmd == "preview":
        out_dir = Path("/home/user/proto")
        out_dir.mkdir(parents=True, exist_ok=True)
        logo = load_logo()
        for k in CONTENT:
            im = preview(k, logo=logo)
            p = out_dir / f"sheet-{k}.jpg"
            im.save(p, quality=92)
            print(f"{k}: {p} {im.size}")
