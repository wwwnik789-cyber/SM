#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Демонстрация применения фонов: 6 слайдов 1920×1080 с реальным текстом SM-Production.
Показывает, что читаемость в рабочих зонах соблюдена.

Запуск:  python3 build_demo.py
Итог:    SM-Fony-demo.pdf
"""
import os
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor, Color

BASE = os.path.dirname(os.path.abspath(__file__))
FON = os.path.join(BASE, "fon")
FONTS = os.path.abspath(os.path.join(BASE, "..", "ca-avtosalony", "02_prezentaciya", "fonts"))
OUT = os.path.join(BASE, "SM-Fony-demo.pdf")

W, H = 1920.0, 1080.0
INK = HexColor("#f4f2ec")
MUT = HexColor("#98989f")
MUT2 = HexColor("#d9d6cd")
ACC = HexColor("#ff4d1c")
ACID = HexColor("#d8ff3e")
DARK_INK = HexColor("#0a0a0d")

for name, f in [("Unb-XB", "Unbounded-800.ttf"), ("Unb-B", "Unbounded-700.ttf"),
                ("Man", "Manrope-400.ttf"), ("Man-SB", "Manrope-600.ttf"), ("Man-B", "Manrope-700.ttf")]:
    pdfmetrics.registerFont(TTFont(name, os.path.join(FONTS, f)))

GOAL = Image.open(os.path.join(BASE, "..", "ca-avtosalony", "02_prezentaciya", "img", "logo-smproduction.png"))


def txt(c, x, y, s, font="Man", size=20, color=INK, anchor="l"):
    c.setFont(font, size)
    c.setFillColor(color)
    f = {"l": c.drawString, "r": c.drawRightString, "c": c.drawCentredString}[anchor]
    f(x, H - y, s)


def bg(c, name):
    p = os.path.join(FON, name + ".jpg")
    c.drawImage(p, 0, 0, W, H)


def logo(c, x, y, h=46, dark=False):
    p = os.path.join(BASE, "_logo_cache.png")
    if not os.path.exists(p):
        GOAL.save(p)
    w = h * GOAL.width / GOAL.height
    c.drawImage(p, x, H - y - h, w, h, mask="auto")


# ------------------------------------------------------------------ слайды
def s1(c):
    bg(c, "01-oblozhka")
    logo(c, 120, 92, 54)
    txt(c, 120, 210, "ПРЕЗЕНТАЦИЯ ДЛЯ ДИЛЕРСКИХ ЦЕНТРОВ", "Man-B", 15, ACC)
    txt(c, 120, 300, "Новогоднее", "Unb-XB", 84, INK)
    txt(c, 120, 396, "оформление", "Unb-XB", 84, ACC)
    txt(c, 120, 452, "фотозоны · ресепшн · офисы · витрины", "Man-SB", 24, MUT2)
    txt(c, 120, 520, "Собственное производство в Москве. Монтаж ночью,", "Man", 20, MUT)
    txt(c, 120, 550, "демонтаж после праздников.", "Man", 20, MUT)
    c.setFillColor(ACID)
    c.roundRect(120, H - 640, 340, 52, 26, stroke=0, fill=1)
    txt(c, 290, 617, "заезды с 15 ноября", "Man-B", 17, DARK_INK, "c")


def s2(c):
    bg(c, "02-razdel")
    txt(c, 160, 330, "02", "Unb-XB", 190, Color(1, 0.30, 0.11, alpha=0.85))
    txt(c, 160, 420, "Что делаем на Новый год", "Unb-XB", 66, INK)
    txt(c, 160, 486, "фотозоны · ресепшн · офисы · витрины и входные группы",
        "Man-SB", 24, MUT2)
    c.setFillColor(Color(1, 0.30, 0.11, alpha=0.9))
    c.rect(160, H - 552, 140, 3, stroke=0, fill=1)


def s3(c):
    bg(c, "03-tekst-levo")
    txt(c, 120, 200, "ПОЧЕМУ ЭТО РАБОТАЕТ", "Man-B", 15, ACC)
    txt(c, 120, 268, "Один производственный", "Unb-XB", 46, INK)
    txt(c, 120, 322, "цикл", "Unb-XB", 46, INK)
    y = 396
    for head, body in [
        ("Каркас, печать, свет", "Делаем сами — в пик сезона не зависим от подрядчиков."),
        ("Монтаж ночью", "К открытию офиса всё собрано и убрано."),
        ("Хранение между сезонами", "На следующий год меняем только полотно — до 40% экономии."),
    ]:
        txt(c, 120, y, head, "Man-B", 21, ACID)
        txt(c, 120, y + 30, body, "Man", 19, MUT2)
        y += 96


def s4(c):
    bg(c, "06-cifry")
    txt(c, 120, 190, "ЦИФРЫ", "Man-B", 15, ACC)
    txt(c, 120, 256, "Производство в масштабе", "Unb-XB", 44, INK)
    data = [("90%", "площадок Москвы и МО знаем по заездам"), ("24 ч", "изготовление фотозоны"),
            ("2 ч", "сборка на площадке"), ("6", "городов в один день")]
    y = 360
    for v, l in data:
        txt(c, 120, y, v, "Unb-XB", 58, ACID)
        txt(c, 330, y, l, "Man", 20, MUT2)
        y += 116


def s5(c):
    bg(c, "05-tablicy")
    txt(c, 120, 180, "ЦЕНЫ", "Man-B", 15, ACC)
    txt(c, 120, 246, "Ориентировочные цены", "Unb-XB", 44, INK)
    rows = [("Фотозона 2 × 2 м", "24 900 ₽"), ("Фотозона 4 × 3 м", "53 500 ₽"),
            ("Брус-баннер 5 × 3 м", "32 500 ₽"), ("Зона ресепшн под ключ", "250 000 ₽"),
            ("Офис до 200 м²", "450 000 ₽")]
    y = 340
    for i, (a, b) in enumerate(rows):
        if i % 2 == 0:
            c.setFillColor(Color(1, 1, 1, alpha=0.045))
            c.rect(120, H - y - 16, 1680, 52, stroke=0, fill=1)
        txt(c, 144, y, a, "Man-SB", 22, INK)
        txt(c, 1776, y, b, "Man-B", 22, ACID, "r")
        y += 56
    txt(c, 120, y + 30, "Точная смета — после замера и согласования макета.", "Man", 17, MUT)


def s6(c):
    bg(c, "10-final")
    txt(c, 960, 470, "Соберём смету", "Unb-XB", 66, INK, "c")
    txt(c, 960, 546, "на новогоднее оформление", "Unb-XB", 66, INK, "c")
    txt(c, 960, 612, "Пришлите фото пространства и площадь — предложим 2–3 варианта",
        "Man", 22, MUT2, "c")
    txt(c, 960, 646, "и назовём свободные даты заезда.", "Man", 22, MUT2, "c")
    txt(c, 960, 760, "+7 495 799-00-19   ·   sm-pro1@yandex.ru   ·   sm-production.ru",
        "Man-B", 24, ACID, "c")


def build():
    c = canvas.Canvas(OUT, pagesize=(W, H))
    c.setTitle("SM-Production — фоны на гексагональной текстуре, демонстрация")
    c.setAuthor("SM-Production")
    for fn in (s1, s2, s3, s4, s5, s6):
        fn(c)
        c.showPage()
    c.save()
    p = os.path.join(BASE, "_logo_cache.png")
    if os.path.exists(p):
        os.remove(p)
    print("PDF:", OUT, round(os.path.getsize(OUT) / 1048576, 2), "МБ")


if __name__ == "__main__":
    build()
