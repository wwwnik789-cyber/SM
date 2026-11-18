"""
Адаптация фирменного баннера SM Production под разные форматы конструкций.

Источник: assets/brand/sm-banner-master.jpg (2067x1240, 5:3).
Логотип в макетах не перерисовывается — используются исходные пиксели баннера,
поэтому кубик SM, надпись SMPRODUCTION и слоган остаются 1-в-1.

Запуск:  python3 scripts/rebrand/layouts.py
Результат: assets/brand/layouts/*.jpg + assets/brand/sm-logo-extracted.png
"""
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
MASTER = ROOT / "assets/brand/sm-banner-master.jpg"
OUT = ROOT / "assets/brand/layouts"

INSET = 26                      # отрезаем исходную тонкую рамку по краю
LOGO_BOX = (690, 225, 1385, 755)  # x0, y0, x1, y1 — блок логотипа на мастере
GOLD = np.array([39, 160, 212], np.float32)   # BGR, буквы «SM»
WHITE = np.array([250, 250, 250], np.float32)
FRAME_BGR = (205, 185, 160)     # светлая сине-серая линия рамки, как на мастере


def load_master():
    img = cv2.imread(str(MASTER), cv2.IMREAD_COLOR)
    if img is None:
        raise SystemExit(f"Нет файла {MASTER}")
    return img


def logo_core_mask(img):
    """Бинарная маска штрихов логотипа (белые линии + золотые буквы SM)."""
    x0, y0, x1, y1 = LOGO_BOX
    roi = img[y0:y1, x0:x1].astype(np.int32)
    b, g, r = roi[..., 0], roi[..., 1], roi[..., 2]
    lum = roi.mean(axis=2)
    white = lum > 180            # тонкие линии «сети» темнее (~150) и не попадают
    gold = (r > 140) & (r - b > 60)
    core = (white | gold).astype(np.uint8)
    # убираем мелкие точки «сети» на фоне, но оставляем мелкие элементы букв
    # (точка над «i»), которые лежат вплотную к крупным штрихам
    n, lab, stats, _ = cv2.connectedComponentsWithStats(core, connectivity=8)
    big = np.zeros_like(core)
    for i in range(1, n):
        if stats[i, cv2.CC_STAT_AREA] >= 40:
            big[lab == i] = 1
    near = cv2.dilate(big, np.ones((25, 25), np.uint8))
    keep = big.copy()
    for i in range(1, n):
        if stats[i, cv2.CC_STAT_AREA] < 40 and near[lab == i].any():
            keep[lab == i] = 1
    full = np.zeros(img.shape[:2], np.uint8)
    full[y0:y1, x0:x1] = keep
    gold_full = np.zeros(img.shape[:2], np.uint8)
    gold_full[y0:y1, x0:x1] = (gold & (keep > 0)).astype(np.uint8)
    return full, gold_full


def extract_logo(img):
    """Возвращает (clean_bg, logo_rgba_crop, logo_offset)."""
    core, gold = logo_core_mask(img)
    zone = cv2.dilate(core, np.ones((7, 7), np.uint8))
    clean = cv2.inpaint(img, zone * 255, 6, cv2.INPAINT_TELEA)

    # альфа: насколько пиксель ближе к цвету штриха, чем к фону
    gold_zone = cv2.dilate(gold, np.ones((9, 9), np.uint8)) > 0
    fg = np.where(gold_zone[..., None], GOLD, WHITE)
    imgf, bgf = img.astype(np.float32), clean.astype(np.float32)
    num = ((imgf - bgf) * (fg - bgf)).sum(2)
    den = ((fg - bgf) ** 2).sum(2) + 1e-3
    alpha = np.clip(num / den, 0, 1) * (zone > 0)
    alpha = np.where(alpha < 0.06, 0, alpha)

    ys, xs = np.where(alpha > 0)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    rgba = np.dstack([fg[y0:y1, x0:x1], alpha[y0:y1, x0:x1, None] * 255]).astype(np.uint8)
    return clean, rgba, (x0, y0)


def draw_frame(img, rel_inset=0.0073, rel_radius=0.012):
    h, w = img.shape[:2]
    s = min(w, h)
    inset = max(4, int(round(max(w, h) * rel_inset)))
    rad = int(s * rel_radius * 2)
    th = max(1, int(round(max(w, h) / 1000)))
    overlay = img.copy()
    x0, y0, x1, y1 = inset, inset, w - inset, h - inset
    # прямые
    cv2.line(overlay, (x0 + rad, y0), (x1 - rad, y0), FRAME_BGR, th, cv2.LINE_AA)
    cv2.line(overlay, (x0 + rad, y1), (x1 - rad, y1), FRAME_BGR, th, cv2.LINE_AA)
    cv2.line(overlay, (x0, y0 + rad), (x0, y1 - rad), FRAME_BGR, th, cv2.LINE_AA)
    cv2.line(overlay, (x1, y0 + rad), (x1, y1 - rad), FRAME_BGR, th, cv2.LINE_AA)
    # скругления
    for cx, cy, a in ((x0 + rad, y0 + rad, 180), (x1 - rad, y0 + rad, 270),
                      (x1 - rad, y1 - rad, 0), (x0 + rad, y1 - rad, 90)):
        cv2.ellipse(overlay, (cx, cy), (rad, rad), a, 0, 90, FRAME_BGR, th, cv2.LINE_AA)
    return cv2.addWeighted(overlay, 0.55, img, 0.45, 0)


def crop_to_ratio(img, ratio, cy=None):
    """Обрезка по центру до соотношения w/h (cy — желаемый центр по вертикали)."""
    h, w = img.shape[:2]
    if w / h > ratio:
        nw = int(round(h * ratio))
        x0 = (w - nw) // 2
        return img[:, x0:x0 + nw]
    nh = int(round(w / ratio))
    cy = h // 2 if cy is None else cy
    y0 = int(np.clip(cy - nh // 2, 0, h - nh))
    return img[y0:y0 + nh]


def horizontal(master, ratio, long_side=3000, frame=True):
    """Горизонтальный формат: обрезаем фон, логотип остаётся исходным."""
    inner = master[INSET:-INSET, INSET:-INSET]
    h = inner.shape[0]
    logo_cy = (LOGO_BOX[1] + LOGO_BOX[3]) // 2 - INSET
    # центр кадра — между центром логотипа и центром полотна,
    # чтобы над логотипом оставался «воздух»
    cy = int(0.5 * logo_cy + 0.5 * h / 2)
    lay = crop_to_ratio(inner, ratio, cy)
    w_ = long_side if ratio >= 1 else int(long_side * ratio)
    h_ = int(round(w_ / ratio))
    lay = cv2.resize(lay, (w_, h_), interpolation=cv2.INTER_CUBIC)
    return draw_frame(lay) if frame else lay


def paste_rgba(dst, rgba, x, y, scale):
    lw, lh = int(rgba.shape[1] * scale), int(rgba.shape[0] * scale)
    logo = cv2.resize(rgba, (lw, lh), interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC)
    a = logo[..., 3:4].astype(np.float32) / 255
    roi = dst[y:y + lh, x:x + lw].astype(np.float32)
    dst[y:y + lh, x:x + lw] = (roi * (1 - a) + logo[..., :3] * a).astype(np.uint8)
    return dst


def recompose(clean, logo_rgba, ratio, long_side=3000, logo_rel_w=0.26, logo_rel_y=0.07):
    """Горизонтальный формат с логотипом в верхней части полотна — для
    конструкций, у которых низ закрыт (стойка регистрации, промостойка, мебель)."""
    inner = clean[INSET:-INSET, INSET:-INSET]
    bg = crop_to_ratio(inner, ratio)
    w, h = long_side, int(round(long_side / ratio))
    bg = cv2.resize(bg, (w, h), interpolation=cv2.INTER_CUBIC)
    scale = w * logo_rel_w / logo_rgba.shape[1]
    lx = (w - int(logo_rgba.shape[1] * scale)) // 2
    out = paste_rgba(bg.copy(), logo_rgba, lx, int(h * logo_rel_y), scale)
    return draw_frame(out)


def vertical(clean, logo_rgba, ratio, height=2400, logo_rel_w=0.80, logo_rel_y=0.20):
    """Вертикальный формат (ролл-ап, колонна): фон поворачивается на 90°,
    тёмный «кристалл» в центре становится вертикальным, логотип ставится сверху."""
    inner = clean[INSET:-INSET, INSET:-INSET]
    rot = cv2.rotate(inner, cv2.ROTATE_90_CLOCKWISE)
    bg = crop_to_ratio(rot, ratio)
    w = int(round(height * ratio))
    bg = cv2.resize(bg, (w, height), interpolation=cv2.INTER_CUBIC)
    scale = w * logo_rel_w / logo_rgba.shape[1]
    lx = (w - int(logo_rgba.shape[1] * scale)) // 2
    ly = int(height * logo_rel_y)
    out = paste_rgba(bg.copy(), logo_rgba, lx, ly, scale)
    return draw_frame(out)


FORMATS = {
    # имя: (тип, соотношение w/h, описание)
    "5x3_presswall": ("master", 5 / 3, "Пресс-волл / брус-баннер 5×3 м, лайтбокс 2,5×1,5 м"),
    "6x3_stage": ("h", 2.0, "Задник сцены / брус-баннер 6×3 м"),
    "4x2.5_registration": ("top", 1.6, "Зона регистрации 4×2,5 м (логотип выше стойки)"),
    "3x2_expo": ("h", 1.5, "Задняя стена стенда 3×2 м / 6×4 м"),
    "4x3_wall": ("h", 4 / 3, "Брус-баннер 4×3 м / лайтбокс 2×1,5 м"),
    "0.85x2_rollup": ("v", 0.85 / 2.0, "Ролл-ап 85×200 см"),
    "1x2_column": ("v", 0.5, "Колонна / вертикальный баннер 1×2 м"),
}


def build_all():
    OUT.mkdir(parents=True, exist_ok=True)
    master = load_master()
    clean, logo, _ = extract_logo(master)
    cv2.imwrite(str(ROOT / "assets/brand/sm-logo-extracted.png"), logo)  # BGRA
    result = {}
    for name, (kind, ratio, _desc) in FORMATS.items():
        if kind == "master":
            lay = master.copy()
        elif kind == "h":
            lay = horizontal(master, ratio)
        elif kind == "top":
            lay = recompose(clean, logo, ratio)
        else:
            lay = vertical(clean, logo, ratio)
        cv2.imwrite(str(OUT / f"sm-layout-{name}.jpg"), lay, [cv2.IMWRITE_JPEG_QUALITY, 92])
        result[name] = lay
    return result


if __name__ == "__main__":
    for k, v in build_all().items():
        print(f"{k:22s} {v.shape[1]}x{v.shape[0]}")
