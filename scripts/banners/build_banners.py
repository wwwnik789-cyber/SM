#!/usr/bin/env python3
"""
Сборка печатных и цифровых версий серии баннеров «Кастинг».

Что делает скрипт:
  1. Находит QR-блок в макете «Кастинг на пробы в кино» (banner-1).
     В исходнике код декоративный: сетка 29×29 есть, а данные рандомные —
     камера телефона такой код не читает. Для печати это брак.
  2. Пересобирает QR с рабочим адресом model.dvkino.ru (тот же, что в
     макете «Кастинг на модный показ»), в той же сетке 29×29 и в том же
     стиле: белые модули на маджентовом фоне.
  3. Восстанавливает фон под старым кодом (мягкая инпейнтинг-заливка
     по окружающему градиенту) и накладывает новый QR.
  4. Сохраняет печатные мастеры (300 dpi, без потери качества) в banners/
     и цифровые версии для сайта и соцсетей в public/media/banners/.

Запуск:
  python3 scripts/banners/build_banners.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import cv2
import numpy as np
import segno
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
PRINT_DIR = ROOT / "banners" / "casting-series" / "print"
WEB_DIR = ROOT / "public" / "media" / "banners"
SOCIAL_DIR = WEB_DIR / "social"

# Адрес, на который ведёт QR в макете «Кастинг на модный показ».
# Для «Кастинг на пробы в кино» подставляется тот же — кастинг ведёт
# на одну посадочную страницу агентства.
QR_TARGET = "https://model.dvkino.ru"

# Оригиналы, пришедшие от клиента (кладутся рядом со скриптом вручную).
SOURCES = {
    "kino": PRINT_DIR / "banner-kasting-proby-v-kino-4608x8256.jpg",
    "dv-production": PRINT_DIR / "banner-dv-production-6144x6144.jpg",
    "pokaz": PRINT_DIR / "banner-kasting-modnyy-pokaz-5088x7584.jpg",
}

DPI = 300
JPEG_QUALITY = 95


# --------------------------------------------------------------------------
# Утилиты
# --------------------------------------------------------------------------
def load(path: Path) -> np.ndarray:
    return np.array(Image.open(path).convert("RGB"))


def save_jpeg(arr: np.ndarray, path: Path, quality: int = JPEG_QUALITY, dpi: int = DPI) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(arr).save(
        path, quality=quality, subsampling=0, optimize=True, progressive=True, dpi=(dpi, dpi)
    )


def _runs(binary_row: np.ndarray) -> list[tuple[int, int, bool]]:
    """Список (начало, длина, значение) для серий True/False в строке."""
    if binary_row.size == 0:
        return []
    change = np.flatnonzero(binary_row[1:] != binary_row[:-1]) + 1
    bounds = np.concatenate(([0], change, [binary_row.size]))
    out = []
    for i in range(len(bounds) - 1):
        out.append((int(bounds[i]), int(bounds[i + 1] - bounds[i]), bool(binary_row[bounds[i]])))
    return out


def find_qr_finders(arr: np.ndarray) -> list[dict]:
    """
    Ищет finder-паттерны QR стандартным методом: горизонтальный прогон
    белый/тёмный/белый/тёмный/белый с отношением 1:1:3:1:1, подтверждённый
    вертикальным прогоном с тем же отношением.

    Работает и для «инвертированного» кода (белые модули на тёмном фоне) —
    именно так выглядят баннеры серии.
    """
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    binary = gray > 215  # True = белый модуль
    h, w = binary.shape

    candidates: list[dict] = []
    for y in range(0, h, 2):
        row = binary[y]
        runs = _runs(row)
        if len(runs) < 5:
            continue
        for i in range(len(runs) - 4):
            w1, l1, v1 = runs[i]
            w2, l2, v2 = runs[i + 1]
            w3, l3, v3 = runs[i + 2]
            w4, l4, v4 = runs[i + 3]
            w5, l5, v5 = runs[i + 4]
            if not (v1 and v3 and v5 and not v2 and not v4):
                continue
            total = l1 + l2 + l3 + l4 + l5
            if total == 0:
                continue
            unit = total / 7.0
            # Допуск 25% — JPEG-артефакты и шум печати.
            if not (
                abs(l1 - unit) < unit * 0.25
                and abs(l2 - unit) < unit * 0.25
                and abs(l3 - 3 * unit) < unit * 0.45
                and abs(l4 - unit) < unit * 0.25
                and abs(l5 - unit) < unit * 0.25
            ):
                continue
            xc = w1 + l1 // 2
            # Центр finder-паттерна: середина центральной полосы из 3 модулей.
            fx = w1 + l1 + l2 + l3 / 2.0
            # Первая строка с отношением 1:1:3:1:1 — это 3-я строка finder-паттерна,
            # значит его верхний край на 2 модуля выше.
            fy = y - 2 * unit
            candidates.append({"x": fx, "y": fy, "unit": unit, "row": y, "xc": xc})

    if not candidates:
        return []

    # Кластеризуем кандидатов по X: одна колонка finder-паттерна даёт
    # десятки совпадений подряд, их надо схлопнуть в одну находку.
    candidates.sort(key=lambda c: (c["x"], c["y"]))
    clusters: list[dict] = []
    for c in candidates:
        if clusters and abs(c["x"] - clusters[-1]["x"]) < 40 and abs(c["y"] - clusters[-1]["y"]) < 120:
            cl = clusters[-1]
            cl["unit"] = min(cl["unit"], c["unit"])
            cl["y"] = min(cl["y"], c["y"])
            cl["n"] = cl.get("n", 1) + 1
        else:
            clusters.append({**c, "n": 1})

    # Вертикальная проверка: колонка через центр finder-паттерна должна
    # давать отношение 1:1:3:1:1 минимум в 3 подряд идущих строках
    # (строки 2, 3 и 4 сетки 7×7).
    verified: list[dict] = []
    for c in clusters:
        if c["n"] < 3:
            continue
        x, unit = c["x"], c["unit"]
        x0 = int(round(x - 3.5 * unit))
        x1 = int(round(x + 3.5 * unit))
        if x0 < 0 or x1 >= w:
            continue
        strip = binary[:, x0:x1]

        def matches(yy: int) -> bool:
            if not (0 <= yy < h):
                return False
            runs = _runs(strip[yy])
            if len(runs) < 5:
                return False
            l1, l2, l3, l4, l5 = (runs[i][1] for i in range(5))
            if not (runs[0][2] and runs[2][2] and runs[4][2] and not runs[1][2] and not runs[3][2]):
                return False
            u = (l1 + l2 + l3 + l4 + l5) / 7.0
            return abs(l3 - 3 * u) < u * 0.5 and abs(l1 - u) < u * 0.45 and abs(l5 - u) < u * 0.45

        # Ищем блок подходящих строк вокруг найденной позиции.
        y_start = int(c["y"])
        best: tuple[int, int] | None = None
        run_len = 0
        run_from = 0
        for yy in range(max(0, y_start - int(3 * unit)), min(h, y_start + int(5 * unit))):
            if matches(yy):
                if run_len == 0:
                    run_from = yy
                run_len += 1
                if best is None or run_len > best[1] - best[0]:
                    best = (run_from, yy)
            else:
                run_len = 0
        if best and (best[1] - best[0] + 1) >= 3:
            # Верхний край finder-паттерна = верх блока − 2 модуля.
            ftop = best[0] - 2 * unit
            verified.append({"x": x, "y": ftop, "unit": unit})
    return verified


def find_qr_square(arr: np.ndarray) -> tuple[int, int, int, int, float, int]:
    """
    Возвращает (x0, y0, x1, y1, модуль_px, число_модулей) по трём
    finder-паттернам: левый верхний, правый верхний, левый нижний.
    """
    finders = find_qr_finders(arr)
    if len(finders) < 3:
        raise RuntimeError(f"finder-паттерны QR не найдены (найдено {len(finders)})")

    ys = [f["y"] for f in finders]
    ymin = min(ys)
    top = sorted([f for f in finders if f["y"] < ymin + 200], key=lambda f: f["x"])
    if len(top) < 2:
        raise RuntimeError("не найдено два верхних finder-паттерна")
    left_top, right_top = top[0], top[-1]

    lefts = [f for f in finders if abs(f["x"] - left_top["x"]) < 80]
    bottom_left = max(lefts, key=lambda f: f["y"])
    if bottom_left is left_top:
        raise RuntimeError("не найден нижний левый finder-паттерн")

    unit_measured = min(left_top["unit"], right_top["unit"], bottom_left["unit"])
    dx = right_top["x"] - left_top["x"]
    dy = bottom_left["y"] - left_top["y"]

    # Перебираем допустимые размеры сетки QR и выбираем тот, при котором
    # модуль по X и по Y совпадает и близок к измеренному.
    best: tuple[float, int, float] | None = None
    for n in sorted(QR_SIZES):
        ux = dx / (n - 7)
        uy = dy / (n - 7)
        if ux <= 0 or uy <= 0:
            continue
        skew = abs(ux - uy) / max(ux, uy)
        drift = abs(ux - unit_measured) / unit_measured
        if skew > 0.12 or drift > 0.12:
            continue
        score = skew + drift
        if best is None or score < best[0]:
            best = (score, n, (ux + uy) / 2)
    if best is None:
        raise RuntimeError(
            f"не удалось определить размер сетки QR (dx={dx:.0f}, dy={dy:.0f}, "
            f"измеренный модуль={unit_measured:.1f})"
        )
    _, n, unit = best

    # Сетка начинается с внешнего левого верхнего угла finder-паттерна.
    x0 = int(round(left_top["x"] - 3.5 * unit))
    y0 = int(round(left_top["y"]))
    side = int(round(n * unit))
    return x0, y0, x0 + side, y0 + side, unit, n


def rebuild_background(arr: np.ndarray, box: tuple[int, int, int, int], mask_qr: np.ndarray) -> np.ndarray:
    """
    Восстанавливает фон под QR-кодом.

    Под кодом в макетах — гладкий маджентовый градиент со слабым виньетом.
    Фон внутри блока собирается билинейно из полос, снятых вплотную к левой
    и правой границам блока: так он гарантированно стыкуется с окружением
    (поляр для QR) и не оставляет ни размытых «призраков» старого кода,
    ни тёмных пятен.
    """
    x0, y0, x1, y1 = box
    out = arr.copy()
    h, w = arr.shape[:2]
    bw, bh = x1 - x0, y1 - y0

    strip = 90
    lx0, lx1 = max(0, x0 - strip), max(0, x0 - 6)
    rx0, rx1 = min(w, x1 + 6), min(w, x1 + strip)

    def edge_profile(xa: int, xb: int) -> np.ndarray:
        """Медианный цвет маджентового фона по каждой строке в полосе [xa, xb)."""
        band = arr[y0:y1, xa:xb].astype(np.float64)
        # Оставляем только фоновые (не белые) пиксели.
        bgmask = band[:, :, 0] < 200
        prof = np.zeros((bh, 3), dtype=np.float64)
        for r in range(bh):
            row = band[r][bgmask[r]]
            if len(row) >= 5:
                prof[r] = np.median(row, axis=0)
            else:
                prof[r] = np.median(band[r], axis=0)
        # Сглаживаем по вертикали, чтобы убрать случайные выбросы.
        prof = cv2.GaussianBlur(prof.astype(np.float32), (1, 41), 0).astype(np.float64)
        return prof

    left = edge_profile(lx0, lx1)
    right = edge_profile(rx0, rx1)

    # Билинейная интерполяция по горизонтали внутри строки.
    t = (np.arange(bw) / max(1, bw - 1))[:, None, None]
    bg = left[None, :, :] * (1 - t) + right[None, :, :] * t

    # Вертикальный сглаживающий проход — убирает полосы на стыках.
    bg = cv2.GaussianBlur(bg.astype(np.float32), (1, 31), 0).astype(np.float64)

    # Мелкая зернистость, как у печатного маджента.
    noise_sigma = float(arr[y0:y1, lx0:lx1].astype(np.float64).std()) * 0.25
    rng = np.random.default_rng(20261020)
    bg = bg + rng.normal(0.0, noise_sigma, size=bg.shape)

    region = out[y0:y1, x0:x1].astype(np.float64)
    m = (mask_qr[y0:y1, x0:x1] > 0).astype(np.float32)
    m = cv2.GaussianBlur(m, (0, 0), 2.0)
    out[y0:y1, x0:x1] = np.clip(region * (1 - m[..., None]) + bg * m[..., None], 0, 255).astype(np.uint8)
    return out


# Допустимые размеры сетки QR (число модулей) и соответствующие версии.
QR_SIZES = {21: 1, 25: 2, 29: 3, 33: 4, 37: 5, 41: 6, 45: 7, 49: 8,
            53: 9, 57: 10, 61: 11, 65: 12, 69: 13, 73: 14, 77: 15, 81: 16}


def render_qr_modules(target: str, n_modules: int, size_px: int) -> np.ndarray:
    """
    Рендерит QR белыми модулями по маджентовому фону (как в макетах серии).
    Размер сетки фиксирован, чтобы код занял ровно ту же площадь, что исходный.
    """
    version = QR_SIZES.get(n_modules)
    if version is None:
        raise RuntimeError(f"нет версии QR на {n_modules} модулей")

    qr = segno.make(target, version=version, error="h", boost_error=False)
    matrix = np.array([[1 if c else 0 for c in row] for row in qr.matrix], dtype=np.uint8)
    if matrix.shape[0] != n_modules:
        raise RuntimeError(f"segno дал {matrix.shape[0]} модулей вместо {n_modules}")

    # Рисуем модули целыми пикселями — без интерполяции, чтобы не было артефактов.
    step = size_px // n_modules
    canvas = np.full((n_modules * step, n_modules * step), 255, dtype=np.uint8)
    for r in range(n_modules):
        for c in range(n_modules):
            if not matrix[r, c]:
                canvas[r * step:(r + 1) * step, c * step:(c + 1) * step] = 0
    if step * n_modules != size_px:
        pad = size_px - step * n_modules
        canvas = np.pad(canvas, ((0, pad), (0, pad)), constant_values=0)
    return np.repeat(np.repeat(canvas[..., None], 3, axis=2), 1, axis=0)


def paste_qr(arr: np.ndarray, box: tuple[int, int, int, int], qr_img: np.ndarray) -> np.ndarray:
    x0, y0, x1, y1 = box
    out = arr.copy()
    region = out[y0:y1, x0:x1]
    mask = (qr_img > 127).any(axis=2)
    region[mask] = qr_img[mask]
    out[y0:y1, x0:x1] = region
    return out


def verify_qr(arr: np.ndarray, box: tuple[int, int, int, int], label: str) -> bool:
    x0, y0, x1, y1 = box
    crop = arr[y0:y1, x0:x1]
    gray = cv2.cvtColor(crop, cv2.COLOR_RGB2GRAY)
    ok_cv = False
    for img in (gray, 255 - gray):
        value, _, _ = cv2.QRCodeDetector().detectAndDecode(img)
        if value:
            ok_cv = True
            print(f"    cv2  [{label}] -> {value}")
            break
    try:
        import zxingcpp

        res = zxingcpp.read_barcodes(np.array(crop))
        if res:
            print(f"    zxing [{label}] -> {res[0].text}")
            ok_cv = True
    except Exception as exc:  # pragma: no cover
        print(f"    zxing недоступен: {exc}")
    if not ok_cv:
        print(f"    ⚠ QR [{label}] НЕ ЧИТАЕТСЯ")
    return ok_cv


# --------------------------------------------------------------------------
# Основной процесс
# --------------------------------------------------------------------------
def fix_kino_qr() -> Path:
    src = SOURCES["kino"]
    arr = load(src)
    x0, y0, x1, y1, unit, n_modules = find_qr_square(arr)
    side = x1 - x0
    print(f"  QR-сетка: ({x0},{y0})–({x1},{y1}), сторона {side}px, модуль {unit:.1f}px, сетка {n_modules}×{n_modules}")

    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    # Маска белых модулей старого (декоративного) кода.
    mask_qr = np.zeros(gray.shape, dtype=np.uint8)
    mask_qr[y0:y1, x0:x1] = (gray[y0:y1, x0:x1] > 215).astype(np.uint8) * 255

    fixed = rebuild_background(arr, (x0, y0, x1, y1), mask_qr)
    qr_img = render_qr_modules(QR_TARGET, n_modules=n_modules, size_px=side)
    fixed = paste_qr(fixed, (x0, y0, x1, y1), qr_img)

    out = PRINT_DIR / "banner-kasting-proby-v-kino-4608x8256.jpg"
    save_jpeg(fixed, out)
    print(f"  сохранено: {out.relative_to(ROOT)}")
    verify_qr(fixed, (x0, y0, x1, y1), "proby-v-kino")
    return out


def build_derivatives() -> None:
    """Делает web- и social-версии для сайта и соцсетей."""
    social_specs = [
        ("1080x1920", 1080, 1920),
        ("1080x1350", 1080, 1350),
        ("1080x1080", 1080, 1080),
        ("1920x1080", 1920, 1080),
    ]
    for key, src in SOURCES.items():
        if not src.exists():
            continue
        im = Image.open(src).convert("RGB")
        w, h = im.size

        # Сайт: не шире 1400px, качество 82 + WebP.
        # Баннеры — крупные градиентные заливки, на них сильно помогает WebP.
        web_w = min(1400, w)
        web = im.resize((web_w, round(h * web_w / w)), Image.LANCZOS)
        web_path = WEB_DIR / f"{key}.jpg"
        web_path.parent.mkdir(parents=True, exist_ok=True)
        web.save(web_path, quality=82, optimize=True, progressive=True)
        webp_path = WEB_DIR / f"{key}.webp"
        web.save(webp_path, quality=80, method=6)
        print(
            f"  web: {web_path.relative_to(ROOT)} ({web.size[0]}×{web.size[1]}, "
            f"{web_path.stat().st_size // 1024} КБ) + webp {webp_path.stat().st_size // 1024} КБ"
        )

        # Соцсети: вписываем с сохранением пропорций + поля исходного цвета фона.
        for name, tw, th in social_specs:
            if w / h > tw / th:
                nh = th
                nw = round(w * th / h)
            else:
                nw = tw
                nh = round(h * tw / w)
            resized = im.resize((nw, nh), Image.LANCZOS)
            bg = Image.new("RGB", (tw, th), resized.getpixel((0, 0)))
            bg.paste(resized, ((tw - nw) // 2, (th - nh) // 2))
            p = SOCIAL_DIR / f"{key}-{name}.jpg"
            p.parent.mkdir(parents=True, exist_ok=True)
            bg.save(p, quality=86, optimize=True, progressive=True)
            print(f"  social: {p.relative_to(ROOT)} ({tw}×{th}, {p.stat().st_size // 1024} КБ)")


def main() -> int:
    print("→ Чиню QR в макете «Кастинг на пробы в кино»")
    fix_kino_qr()
    print("→ Собираю web/social-версии")
    build_derivatives()
    print("✓ Готово")
    return 0


if __name__ == "__main__":
    sys.exit(main())
