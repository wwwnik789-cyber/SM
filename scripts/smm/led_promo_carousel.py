"""Карусель для поста «Освещение в подарок при заказе имиджевой фотозоны» (акция до 15 декабря).

7 слайдов 4:5 (1440×1800) в стиле баннера SM: реальные фото проектов с LED-барами +
фирменные плашки, точный логотип (из мастер-баннера), шрифты Unbounded/Manrope.

Запуск: python3 scripts/smm/led_promo_carousel.py
Результат: smm/posts/led-bars-gift-carousel/slide-01…07.jpg и обзорный лист.
"""
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/rebrand"))
import real_projects as RP  # noqa: E402  (логотип, фон баннера, контакты)

OUT = ROOT / "smm/posts/led-bars-gift-carousel"
SRC = OUT / "src"
REAL = ROOT / "visualizations/rebrand-2026/real-projects/originals"
FONTS = ROOT / "scripts/rebrand/fonts"
W, H = 1440, 1800
N = 7

NAVY0 = (20, 28, 46)
NAVY1 = (30, 42, 68)
NAVY2 = (47, 59, 81)
STEEL_L = (169, 188, 211)
GOLD = (212, 160, 39)
GOLD_L = (240, 199, 90)
WHITE = (255, 255, 255)
PHONE = "+7 (495) 799-00-19"
SITE = RP.SITE
DEADLINE = "до 15 декабря"


def F(name, size):
    return ImageFont.truetype(str(FONTS / {"u": "Unbounded_500Medium.ttf", "m": "Manrope_400Regular.ttf",
                                            "ms": "Manrope_600SemiBold.ttf"}[name]), int(size))


def rgba_logo(kind="full"):
    lg = RP.logo_horizontal() if kind == "h" else RP._logo
    return Image.fromarray(cv2.cvtColor(lg, cv2.COLOR_BGRA2RGBA))


def brand_bg(w, h):
    bg = RP.bg_only(w / h, long_side=max(w, h))
    bg = cv2.resize(bg, (w, h), interpolation=cv2.INTER_AREA)
    return Image.fromarray(cv2.cvtColor(bg, cv2.COLOR_BGR2RGB))


def cover_crop(img, w, h, fx=0.5, fy=0.5):
    """Масштаб «cover» + кадрирование с фокусом (fx, fy в долях)."""
    s = max(w / img.width, h / img.height)
    im = img.resize((round(img.width * s), round(img.height * s)), Image.LANCZOS)
    x = int((im.width - w) * fx)
    y = int((im.height - h) * fy)
    return im.crop((x, y, x + w, y + h))


def wrap(text, font, max_w, draw):
    lines, cur = [], ""
    for word in text.split():
        t = (cur + " " + word).strip()
        if draw.textlength(t, font=font) <= max_w:
            cur = t
        else:
            lines.append(cur)
            cur = word
    lines.append(cur)
    return lines


def vgrad(w, h, top_a, bot_a, color=NAVY0, power=1.0):
    a = np.linspace(top_a, bot_a, h) ** power
    arr = np.zeros((h, w, 4), np.uint8)
    arr[..., :3] = color
    arr[..., 3] = (a[:, None] * 255).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


def pill(d, x, y, text, font, fill, tcolor, padx=26, h=None, anchor="l"):
    tw = d.textlength(text, font=font)
    h = h or int(font.size * 1.9)
    w = tw + 2 * padx
    if anchor == "c":
        x -= w / 2
    d.rounded_rectangle((x, y, x + w, y + h), radius=h / 2, fill=fill)
    d.text((x + w / 2, y + h / 2), text, font=font, fill=tcolor, anchor="mm")
    return w


def chrome(img, idx, dark_top=True):
    """Общие элементы: логотип слева сверху, счётчик справа, нижняя полоса акции."""
    if dark_top:
        img.alpha_composite(vgrad(W, 260, 0.75, 0.0, power=1.2), (0, 0))
    lg = rgba_logo("h")
    s = 330 / lg.width
    lg = lg.resize((330, round(lg.height * s)), Image.LANCZOS)
    img.alpha_composite(lg, (64, 58))
    d = ImageDraw.Draw(img)
    d.text((W - 64, 58 + lg.height / 2), f"{idx:02d} / {N:02d}", font=F("u", 26), fill=WHITE, anchor="rm")
    # нижняя полоса
    d.rectangle((0, H - 96, W, H), fill=NAVY0 + (255,))
    d.line((0, H - 96, W, H - 96), fill=GOLD, width=3)
    d.text((64, H - 48), f"Акция SM {DEADLINE}", font=F("u", 26), fill=GOLD_L, anchor="lm")
    d.text((W - 64, H - 48), f"{SITE}  ·  {PHONE}", font=F("ms", 28), fill=STEEL_L, anchor="rm")


def text_block(img, y, kicker, title, body, title_size=72, body_size=36, max_w=W - 128):
    d = ImageDraw.Draw(img)
    pill(d, 64, y, kicker, F("u", 22), GOLD, NAVY0, padx=22, h=46)
    y += 78
    ft = F("u", title_size)
    for line in wrap(title, ft, max_w, d):
        d.text((62, y), line, font=ft, fill=WHITE)
        y += int(title_size * 1.22)
    y += 14
    fb = F("m", body_size)
    for line in wrap(body, fb, max_w, d):
        d.text((64, y), line, font=fb, fill=STEEL_L)
        y += int(body_size * 1.45)
    return y


def gift_badge(img, cx, cy, r=118):
    """Золотой круглый бейдж «3 LED-бара в подарок»."""
    d = ImageDraw.Draw(img)
    d.ellipse((cx - r - 8, cy - r - 8, cx + r + 8, cy + r + 8), fill=GOLD_L + (90,))
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=GOLD)
    d.text((cx, cy - 46), "3", font=F("u", 84), fill=NAVY0, anchor="mm")
    d.text((cx, cy + 22), "LED-бара", font=F("u", 24), fill=NAVY0, anchor="mm")
    d.text((cx, cy + 58), "в подарок", font=F("ms", 26), fill=NAVY0, anchor="mm")


# ------------------------------------------------------------------ фото монтажа: SM-лого на футболках
INSTALL_SRC = SRC / "install-nloto.jpg"           # монтаж фотозоны + 3 LED-бара (присланное фото)
INSTALL_OUT = SRC / "install-nloto-sm.jpg"        # обработанная версия


def _print_on_shirt(img, center, width, angle, color_bgr, shirt_mask, tilt=0.0, ink=1.0):
    """Печать логотипа SM на спине футболки: поворот, лёгкая перспектива, складки ткани из яркости."""
    lg = RP._logo.copy()
    a = lg[..., 3].astype(np.float32) / 255
    gold = (lg[..., 2].astype(int) - lg[..., 0].astype(int)) > 60      # «SM» в SMPRODUCTION — золото
    col = np.zeros(lg.shape[:2] + (3,), np.float32)
    col[:] = color_bgr
    col[gold] = (25, 155, 209)
    h0, w0 = lg.shape[:2]
    hh = width * h0 / w0
    cx, cy = center
    src = np.float32([[0, 0], [w0, 0], [w0, h0], [0, h0]])
    loc = np.float32([[-width / 2, -hh / 2], [width / 2, -hh / 2 * (1 - tilt)],
                      [width / 2, hh / 2 * (1 - tilt)], [-width / 2, hh / 2]])
    r = np.deg2rad(angle)
    R = np.float32([[np.cos(r), -np.sin(r)], [np.sin(r), np.cos(r)]])
    dst = loc @ R.T + np.float32([cx, cy])
    M = cv2.getPerspectiveTransform(src, dst)
    H_, W_ = img.shape[:2]
    wa = cv2.warpPerspective(a, M, (W_, H_), flags=cv2.INTER_AREA)
    wc = cv2.warpPerspective(col, M, (W_, H_), flags=cv2.INTER_AREA)
    wa = cv2.GaussianBlur(wa, (0, 0), 0.7) * shirt_mask * ink
    # складки: отношение локальной яркости к сглаженной
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    fine = cv2.GaussianBlur(g, (0, 0), 1.5)
    coarse = cv2.GaussianBlur(g, (0, 0), 40)
    sh = np.clip((fine + 8) / (coarse + 8), 0.55, 1.25)
    big = np.clip(coarse / np.median(coarse[shirt_mask > 0.5]), 0.75, 1.15)
    wc = wc * (sh * big)[..., None]
    out = img.astype(np.float32) * (1 - wa[..., None]) + wc * wa[..., None]
    return np.clip(out, 0, 255).astype(np.uint8)


def prepare_install():
    img = cv2.imread(str(INSTALL_SRC))
    # маски спин (вручную по фото): печать не заходит на руки и голову
    def back(pts):
        m = np.zeros(img.shape[:2], np.uint8)
        cv2.fillPoly(m, [np.int32(pts)], 1)
        return cv2.GaussianBlur(m.astype(np.float32), (0, 0), 2)
    # белая футболка (стоящий монтажник) — тёмно-синяя печать
    img = _print_on_shirt(img, (2182, 1600), 188, 1.5, (81, 59, 47),
                          back([(2058, 1470), (2318, 1485), (2318, 1760), (2052, 1760)]), tilt=0.03)
    # чёрная футболка (присевший монтажник) — белая печать
    img = _print_on_shirt(img, (2532, 2088), 190, 10, (232, 234, 236),
                          back([(2385, 1965), (2510, 1925), (2645, 1980), (2695, 2210), (2395, 2235)]), ink=0.93)
    # «красиво»: мягкий контраст, сочность, чуть глубины
    f = img.astype(np.float32) / 255
    f = 0.5 + (f - 0.5) * 1.06
    hsv = cv2.cvtColor(np.clip(f, 0, 1).astype(np.float32), cv2.COLOR_BGR2HSV)
    hsv[..., 1] = np.clip(hsv[..., 1] * 1.12, 0, 1)
    f = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    blur = cv2.GaussianBlur(f, (0, 0), 6)
    f = np.clip(f + (f - blur) * 0.35, 0, 1)                      # микроконтраст
    yy, xx = np.mgrid[0:f.shape[0], 0:f.shape[1]].astype(np.float32)
    vig = 1 - 0.18 * (((xx / f.shape[1] - 0.6) ** 2 + (yy / f.shape[0] - 0.5) ** 2) / 0.5)
    f = f * np.clip(vig, 0.8, 1)[..., None]
    out = Image.fromarray(cv2.cvtColor((f * 255).astype(np.uint8), cv2.COLOR_BGR2RGB))
    return out


# ------------------------------------------------------------------ слайды
def install_photo():
    """Обработанное фото монтажа (кэш в src/, пересоздаётся при отсутствии)."""
    if not INSTALL_OUT.exists() or INSTALL_OUT.stat().st_mtime < Path(__file__).stat().st_mtime:
        prepare_install().save(INSTALL_OUT, quality=90)
    return Image.open(INSTALL_OUT).convert("RGB")


def slide_cover():
    """Обложка: реальная фотозона на монтаже + 3 LED-бара на полу, монтажники SM."""
    img = brand_bg(W, H).convert("RGBA")
    ph = install_photo()
    s = W / ph.width
    ph = ph.resize((W, round(ph.height * s)), Image.LANCZOS)
    top = (H - 96) - ph.height                       # низ фото = верх нижней полосы
    img.alpha_composite(ph.convert("RGBA"), (0, top))
    # верх: тёмный фирменный градиент под заголовок (потолок и верх стенда)
    img.alpha_composite(vgrad(W, 620, 0.96, 0.0, power=0.9), (0, 0))
    # низ: лёгкое затемнение пола под подписью
    img.alpha_composite(vgrad(W, 260, 0.0, 0.88, power=1.3), (0, H - 96 - 260))
    d = ImageDraw.Draw(img)
    y = 190
    pill(d, 64, y, f"АКЦИЯ {DEADLINE.upper()}", F("u", 26), GOLD, NAVY0, padx=26, h=56)
    d.text((60, y + 84), "ОСВЕЩЕНИЕ", font=F("u", 104), fill=WHITE)
    d.text((60, y + 212), "В ПОДАРОК", font=F("u", 104), fill=GOLD)
    d.text((64, H - 96 - 118), "при заказе имиджевой фотозоны", font=F("ms", 46), fill=WHITE)
    d.text((64, H - 96 - 58), "3 LED-бара на 1–2 дня — бесплатно", font=F("m", 38), fill=STEEL_L)
    gift_badge(img, 230, 760, r=112)
    chrome(img, 1)
    return img


def slide_terms():
    img = brand_bg(W, H).convert("RGBA")
    # полоса с баром внизу
    ph = cover_crop(install_photo().crop((0, 2380, 3092, 3800)), W, 560, 0.5, 0.75).convert("RGBA")
    img.alpha_composite(ph, (0, H - 96 - 560))
    img.alpha_composite(vgrad(W, 300, 1.0, 0.0, color=NAVY1, power=1.3), (0, H - 96 - 560))
    d = ImageDraw.Draw(img)
    pill(d, 64, 230, "УСЛОВИЯ АКЦИИ", F("u", 22), GOLD, NAVY0, padx=22, h=46)
    d.text((62, 310), "Что входит", font=F("u", 76), fill=WHITE)
    d.text((62, 404), "в подарок", font=F("u", 76), fill=GOLD)
    rows = [("3", "LED-бара", "мощная заливка фотозоны светом снизу"),
            ("1–2", "дня аренды", "на весь срок вашего мероприятия"),
            ("0 ₽", "за аренду", "при заказе имиджевой фотозоны")]
    y = 560
    for big, title, sub in rows:
        d.rounded_rectangle((64, y, W - 64, y + 150), radius=28, fill=NAVY0 + (225,), outline=GOLD + (255,), width=2)
        d.text((112, y + 75), big, font=F("u", 72), fill=GOLD_L, anchor="lm")
        d.text((360, y + 52), title, font=F("u", 38), fill=WHITE, anchor="lm")
        d.text((360, y + 106), sub, font=F("m", 32), fill=STEEL_L, anchor="lm")
        y += 176
    d.text((64, y + 30), "Привезём, установим и подключим.", font=F("ms", 40), fill=WHITE)
    d.text((64, y + 88), "Нужна только розетка 220 V на площадке.", font=F("m", 36), fill=STEEL_L)
    chrome(img, 2, dark_top=False)
    return img


def slide_photo(idx, path, ph_h, fx, fy, kicker, title, body, badge=None):
    img = brand_bg(W, H).convert("RGBA")
    ph = cover_crop(Image.open(path).convert("RGB"), W, ph_h, fx, fy).convert("RGBA")
    img.alpha_composite(ph, (0, 0))
    img.alpha_composite(vgrad(W, 300, 0.0, 1.0, power=1.4), (0, ph_h - 300))
    text_block(img, ph_h - 64, kicker, title, body, title_size=70, body_size=38)
    if badge:
        gift_badge(img, *badge, r=105)
    chrome(img, idx)
    return img


def slide_what():
    img = brand_bg(W, H).convert("RGBA")
    d = ImageDraw.Draw(img)
    pill(d, 64, 230, "ИМИДЖЕВАЯ ФОТОЗОНА", F("u", 22), GOLD, NAVY0, padx=22, h=46)
    d.text((62, 310), "Не просто фон,", font=F("u", 70), fill=WHITE)
    d.text((62, 398), "а инсталляция", font=F("u", 70), fill=GOLD)
    fb = F("m", 36)
    y = 520
    for line in wrap("Центр притяжения гостей и вирусный контент для соцсетей. В неё могут входить:", fb, W - 128, d):
        d.text((64, y), line, font=fb, fill=STEEL_L)
        y += 52
    y += 30
    items = ["Многоуровневые конструкции и подиум", "Объёмные буквы и логотипы", "Световые короба и световые элементы",
             "Зеркало бесконечности и зеркальные полы", "Декор и арт-объекты под тематику"]
    for it in items:
        d.rounded_rectangle((64, y, W - 64, y + 118), radius=26, fill=NAVY0 + (215,), outline=(98, 124, 154, 255), width=2)
        d.rounded_rectangle((96, y + 41, 132, y + 77), radius=8, fill=GOLD)
        d.line((104, y + 59, 112, y + 68, 125, y + 49), fill=NAVY0, width=5, joint="curve")
        d.text((162, y + 59), it, font=F("ms", 40), fill=WHITE, anchor="lm")
        y += 140
    y += 20
    d.text((64, y), "А LED-бары сделают её ещё эффектнее —", font=F("ms", 38), fill=GOLD_L)
    d.text((64, y + 54), f"в подарок {DEADLINE}.", font=F("ms", 38), fill=GOLD_L)
    chrome(img, 6, dark_top=False)
    return img


def slide_cta():
    img = brand_bg(W, H).convert("RGBA")
    d = ImageDraw.Draw(img)
    lg = rgba_logo("full")
    s = 520 / lg.width
    lg = lg.resize((520, round(lg.height * s)), Image.LANCZOS)
    img.alpha_composite(lg, ((W - lg.width) // 2, 200))
    y = 200 + lg.height + 70
    d.text((W / 2, y), "Как и всегда", font=F("u", 56), fill=WHITE, anchor="mt")
    y += 110
    items = [("Собственное производство", "в Москве и Санкт-Петербурге"),
             ("Концепция и 3D-визуализация", "ещё до начала производства"),
             ("Доставка, монтаж и демонтаж", "силами нашей команды"),
             ("Техническая поддержка", "во время мероприятия")]
    for t, sub in items:
        d.rounded_rectangle((120, y, W - 120, y + 118), radius=26, fill=NAVY0 + (215,), outline=(98, 124, 154, 255), width=2)
        d.ellipse((156, y + 47, 180, y + 71), fill=GOLD)
        d.text((212, y + 40), t, font=F("ms", 38), fill=WHITE, anchor="lm")
        d.text((212, y + 84), sub, font=F("m", 30), fill=STEEL_L, anchor="lm")
        y += 140
    y += 40
    d.rounded_rectangle((120, y, W - 120, y + 230), radius=34, fill=GOLD)
    d.text((W / 2, y + 62), "Рассчитаем фотозону за день", font=F("u", 40), fill=NAVY0, anchor="mm")
    d.text((W / 2, y + 128), PHONE, font=F("u", 50), fill=NAVY0, anchor="mm")
    d.text((W / 2, y + 186), "пишите в личные сообщения", font=F("ms", 32), fill=NAVY0, anchor="mm")
    chrome(img, 7, dark_top=False)
    return img


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    slides = [
        slide_cover(),
        slide_terms(),
        slide_photo(3, REAL / "presswall-uplight.jpg", 1340, 0.25, 0.7, "ЦВЕТНАЯ ПОДСВЕТКА",
                    "Фотозона играет цветом", "Подсветка снизу рисует градиент и выделяет логотипы — "
                    "фото эффектные даже в тёмном зале.", badge=(W - 190, 360)),
        slide_photo(4, SRC / "kinescope-edtech-awards.jpg", 1300, 0.3, 0.5, "РОВНЫЙ СВЕТ",
                    "Логотипы читаются на каждом фото", "Свет по всей ширине фотозоны — без тёмных углов "
                    "и провалов, партнёры довольны."),
        slide_photo(5, REAL / "brus-banner-msu.jpg", 1340, 0.5, 1.0, "ОБЪЁМ И ГЛУБИНА",
                    "Конструкция выглядит дороже", "LED-бары подчёркивают форму и фактуру — даже днём "
                    "в светлом холле."),
        slide_what(),
        slide_cta(),
    ]
    paths = []
    for i, s in enumerate(slides, 1):
        p = OUT / f"slide-{i:02d}.jpg"
        s.convert("RGB").save(p, quality=92)
        paths.append(p)
        print("✓", p.name)
    # обзорный лист
    th = [Image.open(p).resize((360, 450), Image.LANCZOS) for p in paths]
    sheet = Image.new("RGB", (len(th) * 376 + 16, 482), NAVY0)
    for i, t in enumerate(th):
        sheet.paste(t, (16 + i * 376, 16))
    sheet.save(OUT / "carousel-overview.jpg", quality=88)
    print("✓ carousel-overview.jpg")


if __name__ == "__main__":
    build()
