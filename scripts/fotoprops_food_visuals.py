"""Генератор четырёх концепт-визуализаций фотопропсов.

Позиции: круассан, стаканчик кофе, очки и губы.
Требуется Pillow. Запуск из корня репозитория:
    python scripts/fotoprops_food_visuals.py
"""
from __future__ import annotations

import math

from PIL import Image, ImageDraw, ImageFilter

from fotoprops_corporate_visuals import (
    W, H, WHITE, NAVY, ORANGE, EDGE, font, gradient_scene,
    add_header, mask_layer, panel, cut, brand_mark, save,
)

GOLD = "#d99532"
GOLD_LIGHT = "#f3bd58"
RED = "#ed3d45"
RED_DARK = "#9e1e32"


def croissant():
    im = gradient_scene(51)
    add_header(im, "СЕРИЯ 4 · ПРОПС 24", "Гигантский круассан")
    m = mask_layer(); d = ImageDraw.Draw(m)
    # Полумесяц с широкими округлыми концами.
    d.ellipse((278, 222, 922, 610), fill=255)
    d.ellipse((365, 145, 835, 488), fill=0)
    d.ellipse((276, 362, 430, 548), fill=255)
    d.ellipse((770, 362, 924, 548), fill=255)
    cut(m, [
        ("rounded_rectangle", (486, 492, 574, 548), {"radius": 24}),
        ("rounded_rectangle", (626, 492, 714, 548), {"radius": 24}),
    ])
    panel(im, m, fill=GOLD_LIGHT, edge="#9b6427", depth=(13, 16), outline="#ffd887")

    art = Image.new("RGBA", (W, H), (0, 0, 0, 0)); a = ImageDraw.Draw(art, "RGBA")
    # Слои теста — дуги повторяют форму.
    for i, box in enumerate(((324,260,876,585),(360,285,840,570),(405,320,795,555))):
        a.arc(box, 18, 162, fill=(152, 86, 28, 210), width=12-i*2)
    for x in (410, 505, 600, 695, 790):
        a.arc((x-78, 300, x+78, 570), 52, 128, fill=(255, 226, 152, 150), width=8)
    art.putalpha(Image.composite(art.getchannel("A"), Image.new("L", (W,H), 0), m))
    im.alpha_composite(art)
    brand_mark(im, (571, 430), 0.62, dark=False)
    save(im, "sm-fp5-croissant-pvc.jpg")


def coffee_cup():
    im = gradient_scene(52)
    add_header(im, "СЕРИЯ 4 · ПРОПС 25", "Стаканчик кофе с брендингом")
    m = mask_layer(); d = ImageDraw.Draw(m)
    # Крышка и сужающийся стакан — единое жёсткое полотно.
    d.rounded_rectangle((370, 195, 830, 270), radius=30, fill=255)
    d.rounded_rectangle((405, 164, 795, 222), radius=25, fill=255)
    d.polygon([(400,245),(800,245),(750,595),(450,595)], fill=255)
    d.rounded_rectangle((452, 560, 748, 620), radius=24, fill=255)
    cut(m, [
        ("rounded_rectangle", (475, 414, 568, 472), {"radius": 25}),
        ("rounded_rectangle", (632, 414, 725, 472), {"radius": 25}),
    ])
    panel(im, m, fill=WHITE, edge="#aab1bb", depth=(13,16), outline="#ffffff")

    art = Image.new("RGBA", (W,H), (0,0,0,0)); a = ImageDraw.Draw(art, "RGBA")
    a.rounded_rectangle((382,205,818,261), radius=24, fill=ORANGE)
    a.rounded_rectangle((418,174,782,215), radius=20, fill="#ff7652")
    a.polygon([(416,348),(784,348),(763,500),(437,500)], fill=NAVY)
    a.line((456,536,744,536), fill=(15,52,96,80), width=4)
    im.alpha_composite(art)
    brand_mark(im, (548, 376), 1.18, dark=True)
    # Пар как отдельная декоративная печатная/акриловая деталь.
    steam = Image.new("RGBA", (W,H), (0,0,0,0)); sd=ImageDraw.Draw(steam,"RGBA")
    for x in (515,600,685):
        sd.arc((x-34,92,x+34,200), 80, 275, fill=(246,244,238,115), width=8)
    steam = steam.filter(ImageFilter.GaussianBlur(1.5))
    im.alpha_composite(steam)
    save(im, "sm-fp5-coffee-cup-pvc.jpg")


def glasses():
    im = gradient_scene(53)
    add_header(im, "СЕРИЯ 4 · ПРОПС 26", "Гигантские очки")
    m = mask_layer(); d = ImageDraw.Draw(m)
    d.ellipse((245, 270, 570, 545), fill=255)
    d.ellipse((630, 270, 955, 545), fill=255)
    d.rounded_rectangle((535, 365, 665, 425), radius=28, fill=255)
    d.polygon([(255,350),(110,300),(95,345),(255,420)], fill=255)
    d.polygon([(945,350),(1090,300),(1105,345),(945,420)], fill=255)
    cut(m, [
        ("ellipse", (294,310,526,505), {}),
        ("ellipse", (674,310,906,505), {}),
        ("rounded_rectangle", (146,324,225,382), {"radius":24}),
        ("rounded_rectangle", (975,324,1054,382), {"radius":24}),
    ])
    panel(im, m, fill=NAVY, edge="#07192e", depth=(12,15), outline="#f6f4ee")

    # Прозрачные линзы поверх вырезов.
    lens = Image.new("RGBA", (W,H), (0,0,0,0)); l=ImageDraw.Draw(lens,"RGBA")
    l.ellipse((294,310,526,505), fill=(127,212,255,34), outline=(246,244,238,95), width=4)
    l.ellipse((674,310,906,505), fill=(127,212,255,34), outline=(246,244,238,95), width=4)
    l.arc((310,325,510,487), 205, 320, fill=(255,255,255,90), width=6)
    l.arc((690,325,890,487), 205, 320, fill=(255,255,255,90), width=6)
    l.rounded_rectangle((548,376,652,408), radius=15, fill=ORANGE)
    im.alpha_composite(lens)
    brand_mark(im, (902, 400), 0.56, dark=True)
    save(im, "sm-fp5-glasses-pvc.jpg")


def lips():
    im = gradient_scene(54)
    add_header(im, "СЕРИЯ 4 · ПРОПС 27", "Гигантские губы")
    m = mask_layer(); d = ImageDraw.Draw(m)
    top = [(250,420),(340,335),(455,350),(600,280),(745,350),(860,335),(950,420),(820,500),(690,548),(600,555),(510,548),(380,500)]
    bottom = [(250,420),(380,450),(500,435),(600,465),(700,435),(820,450),(950,420),(835,545),(690,605),(600,615),(510,605),(365,545)]
    d.polygon(top, fill=255); d.polygon(bottom, fill=255)
    # Скругляем общий силуэт.
    m = m.filter(ImageFilter.GaussianBlur(9)).point(lambda x: 255 if x > 100 else 0)
    cut(m, [("rounded_rectangle", (553, 535, 647, 590), {"radius":24})])
    panel(im, m, fill=RED, edge=RED_DARK, depth=(12,15), outline="#ff9b9f")

    art = Image.new("RGBA", (W,H), (0,0,0,0)); a=ImageDraw.Draw(art,"RGBA")
    a.line((276,424,390,442,500,423,600,454,700,423,810,442,924,424), fill=RED_DARK, width=10, joint="curve")
    a.arc((360,325,620,500), 195, 310, fill=(255,182,174,170), width=13)
    a.arc((540,425,840,595), 25, 150, fill=(120,15,38,125), width=9)
    im.alpha_composite(art)
    brand_mark(im, (820, 472), 0.58, dark=True)
    save(im, "sm-fp5-lips-pvc.jpg")


if __name__ == "__main__":
    croissant()
    coffee_cup()
    glasses()
    lips()
