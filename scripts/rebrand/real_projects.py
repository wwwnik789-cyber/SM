"""
Ребрендинг РЕАЛЬНЫХ фото реализованных конструкций SM Production под фирменный стиль.

Принцип тот же, что в composite.py: логотип и графика берутся из мастер-баннера
пиксель-в-пиксель, нейросеть ничего не рисует. Разница — вместо хромакея поверхности
выделяются на фото по цвету / по заданным контурам, а реальные пропорции поверхностей
восстанавливаются по точкам схода (фокусное расстояние камеры).

Запуск:  python3 scripts/rebrand/real_projects.py
Исходники: visualizations/rebrand-2026/real-projects/originals/
Результат: visualizations/rebrand-2026/real-projects/*.jpg (+ сравнения «было/стало»)
"""
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import geom as G  # noqa: E402
import layouts as L  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "visualizations/rebrand-2026/real-projects/originals"
OUT = ROOT / "visualizations/rebrand-2026/real-projects"
FONTS = ROOT / "scripts/rebrand/fonts"

# Фирменная палитра (BGR)
NAVY_DARK = (81, 59, 47)      # #2F3B51
NAVY_MID = (116, 82, 59)      # #3B5274
NAVY_EDGE = (68, 42, 30)      # #1E2A44 — торцы
GOLD = (25, 155, 209)         # #D19B19
WHITE = (255, 255, 255)

_master = L.load_master()
_clean, _logo, _ = L.extract_logo(_master)


# ---------------------------------------------------------------- фирменные элементы
def logo_parts():
    a = _logo[..., 3]
    cube = _logo[0:284, 72:567]
    text = _logo[368:482, :]
    return cube, text, a


def logo_horizontal():
    """Горизонтальный логотип: куб слева, SMPRODUCTION + слоган справа (для полос)."""
    cube, text, _ = logo_parts()
    gap = 70
    h = cube.shape[0]
    w = cube.shape[1] + gap + text.shape[1]
    out = np.zeros((h, w, 4), np.uint8)
    out[:, :cube.shape[1]] = cube
    ty = (h - text.shape[0]) // 2 + 6
    out[ty:ty + text.shape[0], cube.shape[1] + gap:] = text
    return out


def bg_strip(width, height):
    """Бесшовная полоса фирменного фона: центральная горизонтальная полоса баннера,
    повторённая с зеркалированием."""
    inner = _clean[L.INSET:-L.INSET, L.INSET:-L.INSET]
    h = inner.shape[0]
    band = inner[int(h * 0.30):int(h * 0.80)]
    tile = cv2.resize(band, (int(band.shape[1] * height / band.shape[0]), height),
                      interpolation=cv2.INTER_AREA)
    tiles, k = [], 0
    while sum(t.shape[1] for t in tiles) < width:
        tiles.append(tile if k % 2 == 0 else cv2.flip(tile, 1))
        k += 1
    return np.hstack(tiles)[:, :width].copy()


def strip_with_logos(aspect, height=420, every=4.5, logo_h=0.62, frame=True):
    """Длинная полоса (боковина подиума, раус): фон + горизонтальные логотипы с шагом."""
    width = int(height * aspect)
    strip = bg_strip(width, height)
    lg = logo_horizontal()
    s = height * logo_h / lg.shape[0]
    lw = int(lg.shape[1] * s)
    step = int(height * every) + lw
    n = max(1, width // step)
    x0 = (width - (n - 1) * step - lw) // 2
    for i in range(n):
        L.paste_rgba(strip, lg, x0 + i * step, int(height * (1 - logo_h) / 2), s)
    if frame:
        th = max(2, height // 110)
        cv2.line(strip, (0, th * 3), (width, th * 3), GOLD, th, cv2.LINE_AA)
        cv2.line(strip, (0, height - th * 3), (width, height - th * 3), GOLD, th, cv2.LINE_AA)
    return strip


def bg_only(ratio, long_side=2400):
    inner = _clean[L.INSET:-L.INSET, L.INSET:-L.INSET]
    bg = L.crop_to_ratio(inner, ratio)
    w = long_side if ratio >= 1 else int(long_side * ratio)
    return cv2.resize(bg, (w, int(round(w / ratio))), interpolation=cv2.INTER_AREA)


# ---------------------------------------------------------------- наложение
def feather(mask, px=1.2, grow=1):
    m = mask.astype(np.uint8)
    if grow:
        m = cv2.dilate(m, np.ones((2 * grow + 1, 2 * grow + 1), np.uint8))
    return cv2.GaussianBlur(m.astype(np.float32), (0, 0), px)


def shading_from(img, mask, lo=0.45, hi=1.35, blur=5, gamma=1.0):
    """Карта света по яркости исходной поверхности (сохраняет складки, тени, блики)."""
    v = img.max(axis=2).astype(np.float32)
    m = mask > 0
    ref = np.median(v[m]) if m.any() else 1
    sh = np.where(m, v / max(ref, 1), 1.0).astype(np.float32)
    if blur:
        sh = cv2.GaussianBlur(sh, (0, 0), blur)
    return np.clip(sh, lo, hi) ** gamma


def warp_to_quad(tex, quad, shape):
    h, w = shape[:2]
    quad = np.asarray(quad, np.float32)
    qw = max(np.linalg.norm(quad[1] - quad[0]), np.linalg.norm(quad[2] - quad[3]))
    qh = max(np.linalg.norm(quad[3] - quad[0]), np.linalg.norm(quad[2] - quad[1]))
    if tex.shape[1] > 2 * qw and tex.shape[0] > 2 * qh:
        tex = cv2.resize(tex, (int(2 * qw), int(2 * qh)), interpolation=cv2.INTER_AREA)
    th, tw = tex.shape[:2]
    src = np.array([[0, 0], [tw - 1, 0], [tw - 1, th - 1], [0, th - 1]], np.float32)
    M = cv2.getPerspectiveTransform(src, quad)
    return cv2.warpPerspective(tex, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)


def apply_texture(img, mask, quad, tex, shade=None, shade_gamma=0.9, emissive=False):
    warped = warp_to_quad(tex, quad, img.shape).astype(np.float32)
    if not emissive:
        sh = shade if shade is not None else shading_from(img, mask)
        warped *= sh[..., None] ** shade_gamma
    a = feather(mask)[..., None]
    return (img.astype(np.float32) * (1 - a) + warped * a).clip(0, 255).astype(np.uint8)


def apply_color(img, mask, bgr, shade_gamma=1.0, blur=2):
    sh = shading_from(img, mask, blur=blur, lo=0.35, hi=1.6)
    col = np.array(bgr, np.float32)[None, None, :] * sh[..., None] ** shade_gamma
    a = feather(mask)[..., None]
    return (img.astype(np.float32) * (1 - a) + col * a).clip(0, 255).astype(np.uint8)


def add_reflection(out, src, tex, quad, depth, strength=0.5, blur=5, only_bright=150):
    """Отражение панели в глянцевом полу: зеркальная копия текстуры под нижней
    кромкой, затухающая по глубине. depth — (слева, справа) в пикселях."""
    q = np.asarray(quad, np.float32)
    bl, br = q[3], q[2]
    rq = np.float32([bl, br, br + [0, depth[1]], bl + [0, depth[0]]])
    flipped = cv2.flip(tex, 0)
    warped = warp_to_quad(flipped, rq, out.shape).astype(np.float32)
    warped = cv2.GaussianBlur(warped, (0, 0), blur)
    th, tw = 256, 4
    grad = np.tile(np.linspace(1, 0, th, dtype=np.float32)[:, None] ** 1.6, (1, tw))
    src_q = np.float32([[0, 0], [tw - 1, 0], [tw - 1, th - 1], [0, th - 1]])
    M = cv2.getPerspectiveTransform(src_q, rq)
    a = cv2.warpPerspective(grad, M, (out.shape[1], out.shape[0]))
    a *= (src.max(axis=2) > only_bright).astype(np.float32)
    a = cv2.GaussianBlur(a, (0, 0), 1.5)[..., None] * strength
    base = out.astype(np.float32)
    return (base * (1 - a) + (base * 0.35 + warped * 0.65) * a).clip(0, 255).astype(np.uint8)


def biggest(mask, k=1, min_area=0):
    m = mask.astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    idx = sorted(range(1, n), key=lambda i: -st[i, 4])[:k]
    return [(lab == i).astype(np.uint8) for i in idx if st[i, 4] > min_area]


def fill_holes(mask):
    cnts, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    out = np.zeros_like(mask, np.uint8)
    cv2.drawContours(out, cnts, -1, 1, -1)
    return out


def poly_mask(shape, pts):
    m = np.zeros(shape[:2], np.uint8)
    cv2.fillPoly(m, [np.int32(pts)], 1)
    return m


def hsv_planes(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    return [hsv[..., i].astype(np.int32) for i in range(3)]


# ================================================================ 1. Подиум (runway)
def podium():
    img = cv2.imread(str(SRC / "podium-runway.jpg"))
    h, w = img.shape[:2]
    c = np.array([w / 2, h / 2])
    H, S, V = hsv_planes(img)
    red = biggest(((H < 10) | (H > 165)) & (S > 90) & (V > 35))[0]   # вкл. тёмный кант
    purple = biggest((H > 118) & (H < 150) & (S > 90) & (V > 50))[0]
    greens = biggest((H > 28) & (H < 55) & (S > 110) & (V > 60), k=3, min_area=800)
    front, backs = greens[0], greens[1:]

    # геометрия: прямые по кромкам → углы и реальные пропорции
    pt = G.fit_line(G.edge_points(purple, "top", 520, 1040))
    pb = G.fit_line(G.edge_points(purple, "bottom", 520, 1040))
    pr = G.fit_line(G.edge_points(purple, "right", 1560, 1800))
    x_far = int(np.flatnonzero(purple.any(0)).min())
    gt = G.fit_line(G.edge_points(front, "top", 1100, 1600))
    gb = G.fit_line(G.edge_points(front, "bottom", 1100, 1380))
    gl = G.fit_line(G.edge_points(front, "left", 1560, 1800))
    f = G.focal_from_vps(G.meet(pt, pb), G.meet(gt, gb), c) or 0.6 * np.hypot(w, h)
    side_q = G.quad_from_lines(pt, pr, pb, G.vline(x_far - 2))
    front_q = G.quad_from_lines(gt, G.vline(w - 1), gb, gl)
    side_ar = G.metric_aspect(side_q, f, c)
    front_ar = G.metric_aspect(front_q, f, c)

    out = img.copy()
    # покрытие подиума — глубокий графитово-синий, складки ткани сохраняются
    out = apply_color(out, red, (70, 50, 40))
    # боковина — фирменная полоса с логотипами
    out = apply_texture(out, purple, side_q, strip_with_logos(side_ar, every=3.2), shade_gamma=0.8)
    # торец — баннер с логотипом (видимая часть торца)
    front_tex = (L.horizontal(_master, front_ar, frame=False).astype(np.float32) * 0.86).astype(np.uint8)
    out = apply_texture(out, front, front_q, front_tex, shade_gamma=0.7)
    # дальние торцы у сцены — тёмно-синие
    for m in backs:
        out = apply_color(out, m, NAVY_EDGE)
    return img, out, dict(f=round(f), side_aspect=round(side_ar, 1), front_aspect=round(front_ar, 2))


# ================================================================ 2. Каше + раус + экран
def stage():
    img = cv2.imread(str(SRC / "stage-cache-riser.jpg"))
    h, w = img.shape[:2]
    c = np.array([w / 2, h / 2])
    f = 0.75 * np.hypot(w, h)          # телефон, ~26 мм экв.
    H, S, V = hsv_planes(img)
    beige = ((H >= 8) & (H <= 32) & (S >= 12) & (S <= 75) & (V > 105)).astype(np.uint8)

    # --- каше: внешний контур (плоская панель), экран — «дыра» в бежевом
    cache_q = np.float32([[476, 320], [1700, 383], [1700, 906], [497, 970]])
    cache_poly = poly_mask(img.shape, cache_q)
    hole = ((1 - beige) * cache_poly).astype(np.uint8)
    hole = cv2.morphologyEx(hole, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(hole)
    screen = fill_holes((lab == lab[600, 1100]).astype(np.uint8))
    st_ = G.edge_points
    s_top = G.fit_line(st_(screen, "top", 800, 1450))
    s_bot = G.fit_line(st_(screen, "bottom", 1250, 1500))     # слева внизу — иконка у кромки
    s_l = G.fit_line(st_(screen, "left", 400, 820))
    s_r = G.fit_line(st_(screen, "right", 420, 800))
    screen_q = G.quad_from_lines(s_top, s_r, s_bot, s_l)
    screen_m = poly_mask(img.shape, screen_q)
    cache_m = (cache_poly & (1 - cv2.dilate(screen_m, np.ones((3, 3), np.uint8))) & beige)
    cache_m = cv2.morphologyEx(cache_m, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)) & cache_poly

    # боковой торец каше справа (подсвечен оранжевым) — в тёмно-синий
    ret_poly = poly_mask(img.shape, [[1701, 386], [1738, 392], [1738, 905], [1701, 906]])
    ret_m = (ret_poly & (V > 110)).astype(np.uint8)

    # --- раус: лицевая панель подиума (углы сняты по увеличенным фрагментам:
    # светлый пол по цвету близок к бежевому, автоматика тут ненадёжна)
    riser_q = np.float32([[487, 1089], [2052, 982], [2046, 1104], [499, 1233]])
    riser_m = poly_mask(img.shape, riser_q) & (V > 60).astype(np.uint8)
    riser_ar = G.metric_aspect(riser_q, f, c)
    cache_ar = G.metric_aspect(cache_q, f, c)
    screen_ar = G.metric_aspect(screen_q, f, c)

    out = img.copy()
    out = apply_texture(out, cache_m, cache_q, bg_only(cache_ar), shade_gamma=0.85)
    out = apply_color(out, ret_m, NAVY_EDGE)
    riser_tex = strip_with_logos(riser_ar, every=2.6, logo_h=0.56)
    out = apply_texture(out, riser_m, riser_q, riser_tex, shade_gamma=0.85)
    out = add_reflection(out, img, riser_tex, riser_q, depth=(70, 45), strength=0.35)
    # экран — светится сам, свет сцены не применяем
    screen_tex = L.horizontal(_master, screen_ar)
    out = apply_texture(out, screen_m, screen_q, screen_tex, emissive=True)
    return img, out, dict(screen_aspect=round(screen_ar, 2), riser_aspect=round(riser_ar, 1),
                          cache_aspect=round(cache_ar, 2))


# ================================================================ 3. Навигационная стела
from PIL import Image, ImageDraw, ImageFont  # noqa: E402


def font(name, size):
    return ImageFont.truetype(str(FONTS / name), size)


def draw_texts(canvas_bgr, items):
    """items: [(text, font_name, size, (x, y), bgr, anchor)]"""
    im = Image.fromarray(cv2.cvtColor(canvas_bgr, cv2.COLOR_BGR2RGB))
    d = ImageDraw.Draw(im)
    for text, fname, size, xy, bgr, anchor in items:
        d.text(xy, text, font=font(fname, size), fill=tuple(int(v) for v in bgr[::-1]), anchor=anchor)
    return cv2.cvtColor(np.asarray(im), cv2.COLOR_RGB2BGR)


def inset_polygon(pts, d):
    """Сдвиг каждой стороны выпуклого многоугольника внутрь на d пикселей."""
    pts = np.asarray(pts, np.float64)
    n = len(pts)
    area = 0.5 * np.sum(pts[:, 0] * np.roll(pts[:, 1], -1) - np.roll(pts[:, 0], -1) * pts[:, 1])
    sgn = 1 if area > 0 else -1
    lines = []
    for i in range(n):
        p, q = pts[i], pts[(i + 1) % n]
        t = (q - p) / np.linalg.norm(q - p)
        nrm = np.array([-t[1], t[0]]) * sgn
        lines.append(G.line_through(p + nrm * d, q + nrm * d))
    return np.array([G.meet(lines[i - 1], lines[i]) for i in range(n)], np.float32)


def shading_robust(img, mask, tol=28, blur=14, lo=0.35, hi=1.4):
    """Свет только по «фоновым» пикселям поверхности (текст/логотипы исключаются),
    иначе старые надписи просвечивают сквозь новую графику."""
    v = img.max(axis=2).astype(np.float32)
    m = mask > 0
    med = np.median(v[m])
    keep = m & (np.abs(v - med) < tol)
    sh = np.where(keep, v / max(med, 1), 1.0).astype(np.float32)
    holes = (~keep).astype(np.uint8) * 255
    small = cv2.resize(sh, None, fx=0.25, fy=0.25, interpolation=cv2.INTER_AREA)
    hs = cv2.resize(holes, (small.shape[1], small.shape[0]), interpolation=cv2.INTER_NEAREST)
    small = cv2.inpaint(np.clip(small * 127, 0, 255).astype(np.uint8), hs, 7, cv2.INPAINT_TELEA)
    sh2 = cv2.resize(small.astype(np.float32) / 127, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_CUBIC)
    sh = np.where(keep, sh, sh2)
    return np.clip(cv2.GaussianBlur(sh, (0, 0), blur), lo, hi)


def arrow_glyph(canvas, x, y, length, size, color, th, left=False):
    """Тонкая линейная стрелка в стиле логотипа (как штрихи куба)."""
    s = -1 if left else 1
    tip = (int(x + s * length), int(y))
    cv2.line(canvas, (int(x), int(y)), tip, color, th, cv2.LINE_AA)
    cv2.line(canvas, tip, (int(tip[0] - s * size), int(y - size)), color, th, cv2.LINE_AA)
    cv2.line(canvas, tip, (int(tip[0] - s * size), int(y + size)), color, th, cv2.LINE_AA)


def sign_top(ar, W=1800):
    """Верхний указатель: фирменный тёмно-синий фон, золотой круг со стрелкой."""
    Hh = int(W / ar)
    tex = (bg_strip(W, Hh).astype(np.float32) * 0.62 + np.array(NAVY_DARK, np.float32) * 0.38).astype(np.uint8)
    pad = int(Hh * 0.16)
    tex = draw_texts(tex, [
        ("Конференц-зал", "Unbounded_500Medium.ttf", int(Hh * 0.25), (pad, int(Hh * 0.42)), WHITE, "ls"),
        ("Главная сцена · 2 этаж", "Manrope_400Regular.ttf", int(Hh * 0.17), (pad, int(Hh * 0.72)), (230, 225, 220), "ls"),
    ])
    r = int(Hh * 0.30)
    cx, cy = W - pad - r, Hh // 2
    cv2.circle(tex, (cx, cy), r, GOLD, -1, cv2.LINE_AA)
    arrow_glyph(tex, cx - r * 0.45, cy, r * 0.9, r * 0.32, NAVY_EDGE, max(3, r // 9))
    th = max(2, Hh // 90)
    cv2.line(tex, (pad, Hh - int(pad * 0.6)), (W - pad, Hh - int(pad * 0.6)), GOLD, th, cv2.LINE_AA)
    return tex


def sign_arrow(Wr, Hh, tw, ty):
    """Стрелка-указатель (влево): золото, тёмно-синий кант и текст."""
    W = int(Wr + tw)
    tex = np.zeros((Hh, W, 3), np.uint8)
    tex[:] = GOLD
    poly = np.float32([[0, ty], [tw, 0], [W - 1, 0], [W - 1, Hh - 1], [tw, Hh - 1]])
    inner = inset_polygon(poly, Hh * 0.055)
    cv2.polylines(tex, [np.int32(inner)], True, NAVY_EDGE, max(3, Hh // 70), cv2.LINE_AA)
    x = tw + (W - tw) * 0.10
    tex = draw_texts(tex, [
        ("Кофе-брейк", "Unbounded_500Medium.ttf", int(Hh * 0.22), (x, int(Hh * 0.45)), NAVY_EDGE, "ls"),
        ("Перезагрузка для мозга", "Manrope_600SemiBold.ttf", int(Hh * 0.15), (x, int(Hh * 0.72)), NAVY_EDGE, "ls"),
    ])
    return tex


def sign_bottom(ar, W=1800):
    """Нижний указатель: светлый, тёмно-синий текст, золотая линейная стрелка."""
    Hh = int(W / ar)
    tex = np.zeros((Hh, W, 3), np.uint8)
    tex[:] = (238, 240, 242)
    pad = int(Hh * 0.13)
    tex = draw_texts(tex, [
        ("Регистрация", "Unbounded_500Medium.ttf", int(Hh * 0.20), (pad, int(Hh * 0.38)), NAVY_EDGE, "ls"),
        ("Бейджи и welcome-пакеты", "Manrope_400Regular.ttf", int(Hh * 0.13), (pad, int(Hh * 0.62)), NAVY_MID, "ls"),
    ])
    arrow_glyph(tex, W * 0.70, Hh * 0.50, W * 0.18, Hh * 0.13, GOLD, max(4, Hh // 45))
    cv2.rectangle(tex, (0, 0), (W - 1, int(Hh * 0.035)), NAVY_DARK, -1)
    return tex


def pillar():
    img = cv2.imread(str(SRC / "navigation-pillar.jpg"))
    h, w = img.shape[:2]
    c = np.array([w / 2, h / 2])
    f = 0.75 * np.hypot(w, h)
    H, S, V = hsv_planes(img)
    out = img.copy()

    # --- верхний указатель (тёмно-синий) — нужен раньше щита: он его перекрывает
    top_q = np.float32([[170, 448], [892, 162], [902, 465], [178, 690]])
    top_m = poly_mask(img.shape, top_q)
    top_ar = G.metric_aspect(top_q, f, c)

    # --- щит: геометрический контур (верх частично в тени указателя) минус указатель
    # и стойка; логотип Positive внутри контура заменяется целиком
    top = G.line_through((850, 551), (1130, 557))
    left = G.line_through((269, 682), (216, 1242))
    bottom = G.line_through((216, 1242), (795, 1379))
    right = G.line_through((1151, 612), (1080, 1105))
    board_q = G.quad_from_lines(top, right, bottom, left)
    cut = G.line_through((1080, 1105), (795, 1379))          # скос вдоль стойки
    shape = [board_q[0], board_q[1], G.meet(right, cut), G.meet(bottom, cut), board_q[3]]
    board = poly_mask(img.shape, shape) & (1 - cv2.dilate(top_m, np.ones((5, 5), np.uint8)))
    post = ((S > 70) & (H > 100) & (H < 135) & (V < 120)).astype(np.uint8)
    post = cv2.morphologyEx(post, cv2.MORPH_OPEN, np.ones((9, 9), np.uint8))
    board &= 1 - biggest(post)[0]
    board_ar = G.metric_aspect(board_q, f, c)
    board_tex = L.recompose(_clean, _logo, board_ar, long_side=2400, logo_rel_w=0.50, logo_rel_y=0.19)
    # свет: только по серому фону щита (вкл. тень от указателя), логотип исключён
    sh = shading_robust(img, board & (S < 60).astype(np.uint8), tol=70, blur=10) * 0.82
    out = apply_texture(out, board, board_q, board_tex, shade=sh, shade_gamma=1.0)

    sh = shading_robust(img, top_m, tol=22) * 0.92
    out = apply_texture(out, top_m, top_q, sign_top(top_ar), shade=sh, shade_gamma=1.0)

    # --- стрелка (была красной): маска по цвету + заливка текста
    r = (((H < 10) | (H > 168)) & (S > 140) & (V > 40)).astype(np.uint8)
    r = sum(biggest(r, k=3, min_area=3000)).astype(np.uint8)
    red = fill_holes(biggest(cv2.morphologyEx(r, cv2.MORPH_CLOSE, np.ones((21, 21), np.uint8)))[0])
    cnt = max(cv2.findContours(red, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0], key=cv2.contourArea)
    hull = cv2.convexHull(cnt)
    ap = cv2.approxPolyDP(hull, 0.01 * cv2.arcLength(hull, True), True).reshape(-1, 2).astype(np.float32)
    tip = ap[np.argmin(ap[:, 0])]
    rest = sorted([p for p in ap if not np.allclose(p, tip)], key=lambda p: p[0])
    ul, ll = sorted(rest[:2], key=lambda p: p[1])
    tr, br = sorted(rest[2:], key=lambda p: p[1])
    rect_q = np.float32([ul, tr, br, ll])
    ar_rect = G.metric_aspect(rect_q, f, c)
    Hh = 900
    Wr = int(Hh * ar_rect)
    Hm = cv2.getPerspectiveTransform(np.float32([[0, 0], [Wr, 0], [Wr, Hh], [0, Hh]]), rect_q)
    t = cv2.perspectiveTransform(tip.reshape(1, 1, 2), np.linalg.inv(Hm)).ravel()
    tw, ty = -t[0], t[1]
    arrow_tex = sign_arrow(Wr, Hh, tw, ty)
    full_q = cv2.perspectiveTransform(np.float32([[[-tw, 0], [Wr, 0], [Wr, Hh], [-tw, Hh]]]), Hm)[0]
    sh = shading_robust(img, red, tol=20) * 0.80
    out = apply_texture(out, red, full_q, arrow_tex, shade=sh, shade_gamma=1.0)

    # --- нижний указатель (светлый)
    bot_q = np.float32([[400, 1880], [1160, 2062], [1150, 2417], [386, 2153]])
    bot_m = poly_mask(img.shape, bot_q)
    bot_ar = G.metric_aspect(bot_q, f, c)
    sh = shading_robust(img, bot_m, tol=20) * 0.66      # белый пластик в этом свете ≈ серый
    out = apply_texture(out, bot_m, bot_q, sign_bottom(bot_ar), shade=sh, shade_gamma=1.0)
    return img, out, dict(board_aspect=round(board_ar, 2), top_aspect=round(top_ar, 2),
                          arrow_rect_aspect=round(ar_rect, 2), bottom_aspect=round(bot_ar, 2))


# ================================================================ сборка
JOBS = {
    "sm-real-podium-runway": (podium, "Подиум (раннвей) — покрытие, боковина, торец"),
    "sm-real-stage-cache-riser": (stage, "Сцена — каше, экран, раус"),
    "sm-real-navigation-pillar": (pillar, "Навигационная стела — щит и указатели"),
}


def label(img, text, sub=None):
    h, w = img.shape[:2]
    bar = int(max(h, w) * 0.045)
    out = img.copy()
    over = out.copy()
    cv2.rectangle(over, (0, 0), (w, bar), NAVY_EDGE, -1)
    out = cv2.addWeighted(over, 0.85, out, 0.15, 0)
    items = [(text, "Unbounded_500Medium.ttf", int(bar * 0.48), (int(bar * 0.4), int(bar * 0.68)), GOLD, "ls")]
    if sub:
        items.append((sub, "Manrope_400Regular.ttf", int(bar * 0.36), (w - int(bar * 0.4), int(bar * 0.66)),
                      (235, 235, 235), "rs"))
    return draw_texts(out, items)


def before_after(a, b, title):
    gap = 16
    if a.shape[0] >= a.shape[1]:       # вертикальные фото — рядом
        h = 1600
        a2 = cv2.resize(a, (int(a.shape[1] * h / a.shape[0]), h), interpolation=cv2.INTER_AREA)
        b2 = cv2.resize(b, (a2.shape[1], h), interpolation=cv2.INTER_AREA)
        a2, b2 = label(a2, "БЫЛО"), label(b2, "СТАЛО", "SM Production")
        sheet = np.full((h, a2.shape[1] * 2 + gap, 3), NAVY_EDGE, np.uint8)
        sheet[:, :a2.shape[1]] = a2
        sheet[:, a2.shape[1] + gap:] = b2
    else:                              # горизонтальные — друг под другом
        w = 1800
        a2 = cv2.resize(a, (w, int(a.shape[0] * w / a.shape[1])), interpolation=cv2.INTER_AREA)
        b2 = cv2.resize(b, (w, a2.shape[0]), interpolation=cv2.INTER_AREA)
        a2, b2 = label(a2, "БЫЛО"), label(b2, "СТАЛО", "SM Production")
        sheet = np.full((a2.shape[0] * 2 + gap, w, 3), NAVY_EDGE, np.uint8)
        sheet[:a2.shape[0]] = a2
        sheet[a2.shape[0] + gap:] = b2
    return sheet


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    results = []
    for name, (fn, title) in JOBS.items():
        a, b, info = fn()
        cv2.imwrite(str(OUT / f"{name}.jpg"), b, [cv2.IMWRITE_JPEG_QUALITY, 90])
        cv2.imwrite(str(OUT / f"{name}_before-after.jpg"), before_after(a, b, title),
                    [cv2.IMWRITE_JPEG_QUALITY, 86])
        results.append(b)
        print("✓", name, info)
    # обзорный лист: три «стало» в ряд по высоте
    H = 1200
    ims = [cv2.resize(r, (int(r.shape[1] * H / r.shape[0]), H), interpolation=cv2.INTER_AREA) for r in results]
    gap = 16
    W = sum(i.shape[1] for i in ims) + gap * (len(ims) + 1)
    head = 110
    sheet = np.full((H + head + gap, W, 3), NAVY_DARK, np.uint8)
    x = gap
    for im in ims:
        sheet[head:head + H, x:x + im.shape[1]] = im
        x += im.shape[1] + gap
    lg = _logo
    s = 80 / lg.shape[0]
    L.paste_rgba(sheet, lg, gap, 15, s)
    sheet = draw_texts(sheet, [("Ребрендинг реализованных проектов в фирменном стиле", "Unbounded_500Medium.ttf",
                                34, (gap + int(lg.shape[1] * s) + 30, 68), WHITE, "ls")])
    cv2.imwrite(str(OUT / "sm-real-projects-overview.jpg"), sheet, [cv2.IMWRITE_JPEG_QUALITY, 88])
    print("✓ overview", sheet.shape)


if __name__ == "__main__":
    main()
