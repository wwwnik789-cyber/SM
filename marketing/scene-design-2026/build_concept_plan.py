"""Концепт-план оформления сцены: фото + реальные размеры в мм.

Собирает из raw/scene-01-kashe-dark.png лист формата 1920×1080:
слева — спецификация конструкции, справа — визуализация с размерными линиями.
Все размеры — проектные, не обмеры конкретной площадки.
"""
from PIL import Image, ImageDraw, ImageFont

BASE = "marketing/scene-design-2026"
SRC = f"{BASE}/raw/scene-01-kashe-dark.png"
OUT = f"{BASE}/scene-05-concept-plan-1920x1080.png"

FONT_V = "/home/user/SM/banners/anikom-arena-3000x2500-concepts/source/Montserrat-Variable.ttf"

W, H = 1920, 1080
PANEL = 615
BG = (14, 14, 16)
AMBER = (245, 170, 70)
GREY = (150, 152, 158)
WHITE = (240, 238, 234)


def font(size, weight="Bold"):
    f = ImageFont.truetype(FONT_V, size)
    try:
        f.set_variation_by_name(weight)
    except Exception:
        pass
    return f


canvas = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(canvas)

# ---- фото справа, cover-fit в область (PANEL..W, 0..H) ----
photo = Image.open(SRC).convert("RGB")
pw, ph = W - PANEL, H
scale = max(pw / photo.width, ph / photo.height)
photo = photo.resize((round(photo.width * scale), round(photo.height * scale)), Image.LANCZOS)
ox = PANEL + (pw - photo.width) // 2
oy = (ph - photo.height) // 2
canvas.paste(photo, (ox, oy))
photo_w = photo.width

# затемнение под подпись снизу и лёгкое виньетирование справа от панели
shade = Image.new("RGBA", (pw, H), (0, 0, 0, 0))
sd = ImageDraw.Draw(shade)
for i in range(150):
    a = int(190 * (i / 150) ** 1.6)
    sd.line([(0, H - 150 + i), (pw, H - 150 + i)], fill=(0, 0, 0, a))
canvas.paste(Image.new("RGB", (pw, H), (0, 0, 0)), (PANEL, 0),
             shade.split()[3].point(lambda v: v))
d = ImageDraw.Draw(canvas)



def dim_h(x1, x2, y, label, color=AMBER):
    """Горизонтальная размерная линия с засечками и подписью."""
    d.line([(x1, y), (x2, y)], fill=color, width=3)
    for x in (x1, x2):
        d.line([(x, y - 13), (x, y + 13)], fill=color, width=3)
    f = font(30)
    tw = d.textlength(label, font=f)
    bx = int((x1 + x2) / 2 - tw / 2)
    d.rectangle([bx - 16, y - 46, bx + int(tw) + 16, y - 6], fill=(10, 10, 12))
    d.text((bx, y - 44), label, font=f, fill=color)
    d.rectangle([x1 - 4, y - 2, x1 + 4, y + 2], fill=color)


def dim_v(y1, y2, x, label, color=AMBER):
    """Вертикальная размерная линия: подпись повёрнута на 90 градусов."""
    d.line([(x, y1), (x, y2)], fill=color, width=3)
    for y in (y1, y2):
        d.line([(x - 13, y), (x + 13, y)], fill=color, width=3)
    f = font(30)
    tw = int(d.textlength(label, font=f))
    tmp = Image.new("RGBA", (tw + 12, 44), (0, 0, 0, 0))
    ImageDraw.Draw(tmp).text((0, 0), label, font=f, fill=color)
    rot = tmp.rotate(90, expand=True)
    # подложка под повёрнутый текст
    bx = int(x - rot.width / 2)
    by = int((y1 + y2) / 2 - rot.height / 2)
    d.rectangle([bx - 6, by - 6, bx + rot.width + 6, by + rot.height + 6], fill=(10, 10, 12))
    canvas.paste(rot, (bx, by), rot)


def callout(px, py, bx, by, lines, color=WHITE):
    """Выноска: точка на объекте, линия к текстовому блоку."""
    f1, f2 = font(23), font(19, "Medium")
    bw = int(max(max(d.textlength(h, font=f1) for h, _ in lines),
                 max(d.textlength(s2, font=f2) for _, s2 in lines))) + 30
    bh = len(lines) * 54 + 16
    bx = min(bx, W - bw - 26)  # не выпускать блок за правый край
    d.line([(px, py), (bx + bw // 2 if by > py else bx + bw // 2, by)], fill=color, width=2)
    d.ellipse([px - 7, py - 7, px + 7, py + 7], fill=AMBER)
    d.rectangle([bx, by, bx + bw, by + bh], fill=(12, 12, 14), outline=AMBER, width=1)
    cy = by + 10
    for head, sub in lines:
        d.text((bx + 15, cy), head, font=f1, fill=AMBER)
        d.text((bx + 15, cy + 28), sub, font=f2, fill=(218, 218, 222))
        cy += 54


# ---- размерные линии по каше ----
k = photo.width / 1408  # пересчёт кадра 1408×768 на вставленный масштаб
KASHE_L, KASHE_R = ox + 382 * k, ox + 1018 * k
KASHE_T, KASHE_B = 247 * k, 562 * k

dim_h(KASHE_L, KASHE_R, KASHE_T - 40, "8000 мм")
dim_v(KASHE_T, KASHE_B, KASHE_L - 46, "4500 мм")

# ---- выноски ----
callout(KASHE_L + 6, KASHE_T + 170, 268, 430, [
    ("Каше", "композит 6 мм, фрезеровка по контуру"),
    ("LED-контур", "лента 24 В, профиль с рассеивателем"),
])
callout(1148, 886, 1240, 916, [
    ("Раус", "ткань с силиконовым кантом"),
    ("Подиум", "600 мм, ковролин в цвет бренда"),
])

# ---- подпись-дисклеймер ----
f_disc = font(24, "SemiBold")
disc = "ВИЗУАЛИЗАЦИЯ · НЕ ФОТОГРАФИЯ ОБЪЕКТА"
tw = int(d.textlength(disc, font=f_disc))
d.rectangle([W - tw - 62, 30, W - 30, 76], fill=(12, 12, 14), outline=AMBER, width=1)
d.text((W - tw - 46, 39), disc, font=f_disc, fill=AMBER)

# ---- левая панель ----
x0 = 46
d.text((x0, 58), "SM PRODUCTION", font=font(21, "SemiBold"), fill=AMBER)
d.text((x0, 96), "Концепт оформления", font=font(47), fill=WHITE)
d.text((x0, 150), "сцены", font=font(47), fill=WHITE)
d.line([(x0, 224), (PANEL - 46, 224)], fill=(60, 60, 66), width=2)

rows = [
    ("Габарит каше", "8000 × 4500 мм"),
    ("Экран в свету", "6400 × 3000 мм"),
    ("Зазор каше — экран", "200 мм"),
    ("Толщина панели", "6 мм, композит"),
    ("Глубина каркаса", "250 мм"),
    ("Высота подиума", "600 мм"),
    ("Раус", "ткань, силиконовый кант"),
    ("Ковролин", "по площади сцены"),
]
y = 252
for name, val in rows:
    d.text((x0, y), name, font=font(21, "Medium"), fill=GREY)
    d.text((x0, y + 28), val, font=font(26, "SemiBold"), fill=WHITE)
    y += 74
    d.line([(x0, y - 18), (PANEL - 46, y - 18)], fill=(38, 38, 44), width=1)

d.text((x0, 858), "Размеры проектные.", font=font(20, "Medium"), fill=GREY)
d.text((x0, 886), "Уточняются обмером площадки.", font=font(20, "Medium"), fill=GREY)
d.text((x0, 934), "+7 (495) 799-00-19", font=font(25, "Bold"), fill=AMBER)

canvas.save(OUT, optimize=True)
print("saved", OUT, canvas.size)
