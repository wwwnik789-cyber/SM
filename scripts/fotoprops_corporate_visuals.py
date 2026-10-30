"""Генератор серии 3 «Корпоративные фотопропсы».

Создаёт пять концепт-визуализаций 1200×672 без внешних API.
Требуется Pillow: python -m pip install Pillow
Запуск из корня репозитория:
    python scripts/fotoprops_corporate_visuals.py
"""
from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "visualizations" / "fotoprops"
OUT.mkdir(parents=True, exist_ok=True)

W, H = 1200, 672
NAVY = "#0f3460"
NAVY_DARK = "#071a31"
ORANGE = "#ff4d1c"
WHITE = "#f6f4ee"
ACID = "#d8ff3e"
INK = "#11151d"
EDGE = "#aeb6c3"

FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def font(size: int, bold: bool = False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)


def gradient_scene(seed: int, accent: str = ORANGE) -> Image.Image:
    """Тёмный event-интерьер с тёплым светом, сценой и боке."""
    random.seed(seed)
    im = Image.new("RGB", (W, H), "#080b11")
    px = im.load()
    for y in range(H):
        t = y / (H - 1)
        horizon = math.exp(-((y - 365) / 180) ** 2)
        for x in range(W):
            side = 1 - 0.18 * abs(x - W / 2) / (W / 2)
            r = int((7 + 20 * t + 13 * horizon) * side)
            g = int((10 + 12 * t + 6 * horizon) * side)
            b = int((17 + 16 * t + 4 * horizon) * side)
            px[x, y] = (r, g, b)

    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow, "RGBA")
    # Верхние софиты.
    for x in (120, 330, 600, 870, 1080):
        gd.polygon([(x - 18, 0), (x + 18, 0), (x + 125, 490), (x - 125, 490)], fill=(255, 189, 92, 14))
    # Гирлянды и мягкое боке.
    for row, yy in enumerate((78, 118, 176)):
        for i in range(16 + row * 2):
            x = int((i + 0.5) * W / (16 + row * 2) + random.randint(-18, 18))
            y = yy + int(22 * math.sin(i * 0.72 + row)) + random.randint(-5, 5)
            rad = random.randint(4, 9)
            gd.ellipse((x-rad, y-rad, x+rad, y+rad), fill=(255, 215, 137, 205))
            gd.ellipse((x-rad*3, y-rad*3, x+rad*3, y+rad*3), fill=(255, 167, 65, 20))
    for _ in range(44):
        x = random.randint(20, W - 20)
        y = random.randint(210, 470)
        rad = random.randint(3, 13)
        color = (255, 176, 76, random.randint(28, 95))
        gd.ellipse((x-rad, y-rad, x+rad, y+rad), fill=color)
    glow = glow.filter(ImageFilter.GaussianBlur(5))
    im = Image.alpha_composite(im.convert("RGBA"), glow)

    # Условная аудитория по краям — только силуэты, чтобы объект был главным.
    people = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(people, "RGBA")
    for side in (-1, 1):
        base = 120 if side == -1 else 1080
        for i in range(4):
            x = base + side * (i - 1) * 54 + random.randint(-12, 12)
            y = 340 + random.randint(-18, 28)
            rr = random.randint(16, 24)
            pd.ellipse((x-rr, y-rr*2, x+rr, y), fill=(3, 5, 9, 185))
            pd.rounded_rectangle((x-rr*2, y-4, x+rr*2, H+40), radius=rr, fill=(3, 5, 9, 175))
    people = people.filter(ImageFilter.GaussianBlur(2.5))
    im = Image.alpha_composite(im, people)

    # Пол и световой акцент в центре.
    floor = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fd = ImageDraw.Draw(floor, "RGBA")
    fd.rectangle((0, 470, W, H), fill=(5, 8, 13, 110))
    for i in range(7):
        yy = 488 + i * 31
        fd.line((0, yy, W, yy), fill=(255, 255, 255, max(4, 18-i*2)), width=1)
    for x in range(-200, 1400, 160):
        fd.line((W//2, 470, x, H), fill=(255, 255, 255, 8), width=1)
    fd.ellipse((270, 470, 930, 650), fill=(255, 77, 28, 16))
    floor = floor.filter(ImageFilter.GaussianBlur(3))
    return Image.alpha_composite(im, floor)


def add_header(im: Image.Image, num: str, title: str):
    """Небольшая системная подпись — вне изделия, без рекламной перегрузки."""
    d = ImageDraw.Draw(im, "RGBA")
    d.rounded_rectangle((42, 36, 288, 72), radius=18, fill=(8, 11, 17, 180), outline=(255,255,255,36), width=1)
    d.ellipse((59, 50, 67, 58), fill=ACID)
    d.text((78, 45), "SM PRODUCTION · ПРОПСЫ", font=font(12, True), fill=(246,244,238,225))
    d.text((43, 89), num, font=font(13, True), fill=ORANGE)
    d.text((43, 111), title, font=font(28, True), fill=WHITE)


def mask_layer() -> Image.Image:
    return Image.new("L", (W, H), 0)


def panel(im: Image.Image, mask: Image.Image, fill=WHITE, edge=EDGE, depth=(12, 15), outline=WHITE):
    """Рендер плоского ПВХ с тенью, торцом, лёгким градиентом и бликом."""
    # Контактная и падающая тень.
    shadow_mask = Image.new("L", (W, H), 0)
    shadow_mask.paste(mask, depth)
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    shadow.putalpha(shadow_mask.filter(ImageFilter.GaussianBlur(18)).point(lambda x: int(x * 0.62)))
    im.alpha_composite(shadow)

    # Видимый торец.
    edge_layer = Image.new("RGBA", (W, H), edge)
    edge_mask = Image.new("L", (W, H), 0)
    edge_mask.paste(mask, depth)
    edge_layer.putalpha(edge_mask)
    im.alpha_composite(edge_layer)

    # Лицевая поверхность с вертикальным градиентом.
    face = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    base = Image.new("RGB", (W, H), fill)
    bp = base.load()
    rgb = tuple(int(fill.lstrip("#")[i:i+2], 16) for i in (0,2,4)) if isinstance(fill, str) else fill[:3]
    for y in range(H):
        k = 1.06 - 0.13 * y/H
        c = tuple(max(0, min(255, int(v*k))) for v in rgb)
        for x in range(W):
            bp[x,y] = c
    face.paste(base, (0,0), mask)
    im.alpha_composite(face)

    # Тонкая светлая кромка.
    expanded = mask.filter(ImageFilter.MaxFilter(7))
    border = Image.eval(expanded, lambda x: x)
    # border = expanded - mask
    import PIL.ImageChops as Chops
    border = Chops.subtract(expanded, mask)
    ol = Image.new("RGBA", (W,H), outline)
    ol.putalpha(border.point(lambda x: int(x*0.7)))
    im.alpha_composite(ol)

    # Отражение на полу.
    bbox = mask.getbbox()
    if bbox:
        crop = face.crop(bbox).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        crop = crop.resize((crop.width, max(1, int(crop.height*0.22))))
        alpha = Image.new("L", crop.size)
        ap = alpha.load()
        for yy in range(alpha.height):
            a = int(38 * (1 - yy/max(1,alpha.height-1)) ** 1.7)
            for xx in range(alpha.width): ap[xx,yy] = a
        crop.putalpha(alpha.filter(ImageFilter.GaussianBlur(3)))
        im.alpha_composite(crop, (bbox[0], min(H-crop.height, bbox[3]+12)))


def cut(mask: Image.Image, shapes):
    d = ImageDraw.Draw(mask)
    for kind, coords, kwargs in shapes:
        getattr(d, kind)(coords, fill=0, **kwargs)


def brand_mark(im, xy, scale=1.0, dark=False):
    x,y = xy
    d = ImageDraw.Draw(im, "RGBA")
    f = font(int(32*scale), True)
    color = WHITE if dark else NAVY
    d.text((x,y), "SM", font=f, fill=color)
    box = d.textbbox((x,y), "SM", font=f)
    d.ellipse((box[2]+5, y+int(17*scale), box[2]+int(13*scale), y+int(25*scale)), fill=ORANGE)


def save(im, name):
    # Небольшая зернистость объединяет программный рендер и фон.
    noise = Image.effect_noise((W,H), 7).convert("L")
    grain = Image.new("RGBA", (W,H), (255,255,255,0))
    grain.putalpha(noise.point(lambda x: max(0, int((x-118)*0.10))))
    im = Image.alpha_composite(im, grain)
    im.convert("RGB").save(OUT/name, quality=91, optimize=True, progressive=True)
    print(OUT/name)


def giant_key():
    im = gradient_scene(31)
    add_header(im, "СЕРИЯ 3 · ПРОПС 19", "Церемониальный ключ")
    m = mask_layer(); d = ImageDraw.Draw(m)
    # Головка, стержень и зубцы — единое полотно ПВХ.
    d.ellipse((190, 235, 500, 545), fill=255)
    d.rounded_rectangle((390, 333, 985, 454), radius=42, fill=255)
    d.polygon([(880,430),(1040,430),(1040,520),(982,520),(982,478),(928,478),(928,510),(880,510)], fill=255)
    # Кольцо и две ручки.
    cut(m, [("ellipse", (265,310,425,470), {}), ("rounded_rectangle", (512,363,612,423), {"radius":25}), ("rounded_rectangle", (650,363,750,423), {"radius":25})])
    panel(im,m,fill=WHITE,edge="#9aa4b0",depth=(13,16),outline="#ffffff")
    # Цветные лицевые зоны.
    art = Image.new("RGBA",(W,H),(0,0,0,0)); ad=ImageDraw.Draw(art,"RGBA")
    ad.arc((206,251,484,529),30,330,fill=NAVY,width=25)
    ad.rounded_rectangle((405,344,870,443),radius=35,fill=NAVY)
    ad.polygon([(875,443),(1027,443),(1027,504),(995,504),(995,466),(940,466),(940,495),(885,495)],fill=ORANGE)
    art.putalpha(Image.composite(art.getchannel('A'),Image.new('L',(W,H),0),m))
    im.alpha_composite(art)
    brand_mark(im,(790,367),0.62,dark=True)
    save(im,"sm-fp3-giant-key-pvc.jpg")


def trophy():
    im = gradient_scene(32)
    add_header(im, "СЕРИЯ 3 · ПРОПС 20", "Кубок победителя")
    m=mask_layer(); d=ImageDraw.Draw(m)
    d.polygon([(410,225),(790,225),(742,405),(654,456),(654,515),(790,515),(825,565),(375,565),(410,515),(546,515),(546,456),(458,405)],fill=255)
    d.ellipse((332,252,490,420),fill=255); d.ellipse((710,252,868,420),fill=255)
    cut(m,[("ellipse",(360,282,482,392),{}),("ellipse",(718,282,840,392),{}),("rounded_rectangle",(550,510,650,550),{"radius":18})])
    panel(im,m,fill=WHITE,edge="#9ba5b2",depth=(12,16))
    art=Image.new("RGBA",(W,H),(0,0,0,0)); a=ImageDraw.Draw(art,"RGBA")
    a.polygon([(430,243),(770,243),(726,382),(640,433),(560,433),(474,382)],fill=NAVY)
    # Звезда.
    pts=[]
    for i in range(10):
        ang=-math.pi/2+i*math.pi/5; r=76 if i%2==0 else 34
        pts.append((600+math.cos(ang)*r,330+math.sin(ang)*r))
    a.polygon(pts,fill=ORANGE)
    a.rounded_rectangle((435,526,765,554),radius=12,fill=NAVY)
    im.alpha_composite(art)
    brand_mark(im,(570,370),0.72,dark=True)
    save(im,"sm-fp3-trophy-pvc.jpg")


def medal():
    im=gradient_scene(33)
    add_header(im,"СЕРИЯ 3 · ПРОПС 21","Гигантская медаль")
    m=mask_layer(); d=ImageDraw.Draw(m)
    d.polygon([(450,185),(545,185),(600,330),(500,350)],fill=255)
    d.polygon([(655,185),(750,185),(700,350),(600,330)],fill=255)
    d.ellipse((365,282,835,620),fill=255)
    cut(m,[("rounded_rectangle",(548,538,652,594),{"radius":26})])
    panel(im,m,fill=WHITE,edge="#929daa",depth=(12,15))
    art=Image.new("RGBA",(W,H),(0,0,0,0)); a=ImageDraw.Draw(art,"RGBA")
    a.polygon([(468,199),(533,199),(588,342),(514,357)],fill=NAVY)
    a.polygon([(667,199),(732,199),(686,357),(612,342)],fill=ORANGE)
    a.ellipse((386,303,814,598),fill=NAVY,outline=WHITE,width=12)
    a.ellipse((430,340,770,568),outline=ORANGE,width=10)
    a.text((548,355),"1",font=font(150,True),fill=WHITE)
    im.alpha_composite(art)
    brand_mark(im,(562,508),0.6,dark=True)
    save(im,"sm-fp3-medal-pvc.jpg")


def clapperboard():
    im=gradient_scene(34)
    add_header(im,"СЕРИЯ 3 · ПРОПС 22","Кинохлопушка")
    # Основная панель.
    m=mask_layer(); d=ImageDraw.Draw(m)
    d.rounded_rectangle((280,290,920,575),radius=24,fill=255)
    d.polygon([(280,250),(905,180),(920,270),(295,340)],fill=255)
    cut(m,[("rounded_rectangle",(350,495,465,552),{"radius":25}),("rounded_rectangle",(735,495,850,552),{"radius":25})])
    panel(im,m,fill=WHITE,edge="#909aa7",depth=(13,17))
    art=Image.new("RGBA",(W,H),(0,0,0,0)); a=ImageDraw.Draw(art,"RGBA")
    a.rounded_rectangle((294,304,906,560),radius=18,fill=NAVY)
    # Верхняя планка и полосы.
    a.polygon([(288,259),(897,191),(908,259),(300,328)],fill=WHITE)
    for x in range(300,940,118):
        a.polygon([(x,258),(x+55,252),(x+106,280),(x+50,287)],fill=ORANGE)
    a.line((314,385,890,385),fill=(255,255,255,120),width=3)
    a.text((417,405),"START",font=font(62,True),fill=WHITE)
    a.ellipse((310,282,334,306),fill=ORANGE)
    im.alpha_composite(art)
    brand_mark(im,(314,332),0.72,dark=True)
    save(im,"sm-fp3-clapperboard-pvc.jpg")


def smartphone():
    im=gradient_scene(35)
    add_header(im,"СЕРИЯ 3 · ПРОПС 23","Смартфон-рамка с QR")
    m=mask_layer(); d=ImageDraw.Draw(m)
    d.rounded_rectangle((390,150,810,610),radius=58,fill=255)
    d.rounded_rectangle((342,585,520,630),radius=16,fill=255)
    d.rounded_rectangle((680,585,858,630),radius=16,fill=255)
    cut(m,[("rounded_rectangle",(425,205,775,486),{"radius":28}), ("rounded_rectangle",(458,528,548,576),{"radius":20}), ("rounded_rectangle",(652,528,742,576),{"radius":20})])
    panel(im,m,fill=WHITE,edge="#929ca9",depth=(12,15))
    art=Image.new("RGBA",(W,H),(0,0,0,0)); a=ImageDraw.Draw(art,"RGBA")
    a.rounded_rectangle((400,160,800,600),radius=51,outline=NAVY,width=18)
    a.rounded_rectangle((425,205,775,486),radius=28,outline=ORANGE,width=10)
    a.rounded_rectangle((535,174,665,189),radius=7,fill=NAVY)
    a.text((470,491),"#EVENT",font=font(34,True),fill=NAVY)
    # Декоративный QR, гарантированно не ведущий на адрес.
    qx,qy,cell=675,496,8
    pattern=["1110111","1000101","1011101","1010011","1110101","0011010","1110111"]
    a.rectangle((qx-8,qy-8,qx+7*cell+8,qy+7*cell+8),fill=WHITE)
    for yy,row in enumerate(pattern):
        for xx,v in enumerate(row):
            if v=="1": a.rectangle((qx+xx*cell,qy+yy*cell,qx+(xx+1)*cell-1,qy+(yy+1)*cell-1),fill=INK)
    im.alpha_composite(art)
    brand_mark(im,(426,493),0.7,dark=False)
    save(im,"sm-fp3-smartphone-qr-pvc.jpg")


if __name__ == "__main__":
    giant_key()
    trophy()
    medal()
    clapperboard()
    smartphone()
