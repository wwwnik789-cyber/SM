#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Один архив со всеми сгенерированными кадрами по автосалонам.

Что попадает внутрь:
  01 — стандартные позиции брендирования (03_vizualizacii)
  02 — Haval, версия 2 (04_haval)
  03 — кубы, 32 визуализации (06_kuby/vizualizacii)
  04 — реклама 16:9 (05_reklama/reklama-*)
  05 — реклама 1:1 (05_reklama/social-*)
  06 — контактные листы наборов
  07 — исходные кадры до брендирования (без кубов и без текста)

Не попадает: реальные фото клиента (02_prezentaciya/img/as-*,
04_haval/izdeliya, 06_kuby/istochniki, 06_kuby/foto-posle) и логотипы брендов —
это не сгенерированные кадры.
"""
import os
import shutil
import subprocess
import zipfile

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, '02_prezentaciya', 'fonts')
BUILD = '/tmp/arhiv-avtosalony'
OUT_ZIP = os.path.join(HERE, '..', '..', 'docs',
                       'SM-Avtosalony-vse-foto-28-10.zip')

INK = (43, 38, 33)
MUTED = (122, 111, 99)
ACC = (255, 77, 28)
BG = (18, 18, 20)
CARD = (32, 32, 36)

SECTIONS = [
    ('01-standartnye-pozicii', 'СТАНДАРТНЫЕ ПОЗИЦИИ · 10 кадров',
     os.path.join(HERE, '03_vizualizacii'),
     ['00-hero.jpg', '03-01-reception.jpg', '03-02-logotipy.jpg',
      '03-03-brand-paneli.jpg', '03-04-navigaciya.jpg', '03-05-podvesy.jpg',
      '03-06-info-stoyki.jpg', '03-07-presswall.jpg', '03-08-fotozona.jpg',
      '03-09-elektro.jpg']),
    ('02-haval', 'HAVAL · ВЕРСИЯ 2 · 10 кадров',
     os.path.join(HERE, '04_haval'),
     ['00-hero.jpg', '04-01-reception.jpg', '04-02-logotipy.jpg',
      '04-03-brand-paneli.jpg', '04-04-navigaciya.jpg', '04-05-podvesy.jpg',
      '04-06-info-stoyki.jpg', '04-07-presswall.jpg', '04-08-fotozona.jpg',
      '04-09-fasad.jpg']),
    ('03-kuby', 'КУБЫ · 32 кадра',
     os.path.join(HERE, '06_kuby', 'vizualizacii'),
     sorted(os.listdir(os.path.join(HERE, '06_kuby', 'vizualizacii')))),
    ('04-reklama-16x9', 'РЕКЛАМА 16:9 · 6 макетов',
     os.path.join(HERE, '05_reklama'),
     ['reklama-01-reception.jpg', 'reklama-02-stands.jpg',
      'reklama-03-navigation.jpg', 'reklama-04-presswall.jpg',
      'reklama-05-facade.jpg', 'reklama-06-reception.jpg']),
    ('05-reklama-1x1', 'РЕКЛАМА 1:1 · 6 квадратов',
     os.path.join(HERE, '05_reklama'),
     ['social-01-reception.jpg', 'social-02-stands.jpg',
      'social-03-navigation.jpg', 'social-04-presswall.jpg',
      'social-05-facade.jpg', 'social-06-reception.jpg']),
]

PREVIEWS = [
    ('preview-standartnye.jpg', os.path.join(HERE, '03_vizualizacii', 'preview.jpg')),
    ('preview-haval.jpg', os.path.join(HERE, '04_haval', 'preview.jpg')),
    ('preview-kuby.jpg', os.path.join(HERE, '06_kuby', 'preview.jpg')),
    ('preview-reklama.jpg', os.path.join(HERE, '05_reklama', 'preview.jpg')),
]

SOURCES = [
    (os.path.join(HERE, '06_kuby', 'src'), 'kub-'),
    (os.path.join(HERE, '05_reklama', 'src'), 'reklama-'),
]


def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size)


def cover(im, w, h):
    """вписать в рамку с обрезкой по центру"""
    im = im.convert('RGB')
    sw, sh = im.size
    k = max(w / sw, h / sh)
    im = im.resize((max(1, int(sw * k)), max(1, int(sh * k))), Image.LANCZOS)
    sw, sh = im.size
    x = (sw - w) // 2
    y = (sh - h) // 2
    return im.crop((x, y, x + w, y + h))


def build_obzor(path):
    """сводный контактный лист всех финальных кадров"""
    import math

    cell_w, cell_h = 330, 210
    pad, gap = 60, 18
    cols = 6
    head_h = 70
    row_h = cell_h + gap + 26

    # высота считается по фактическим рядам, а не по числу файлов
    h = pad
    for _, _, _, files in SECTIONS:
        h += head_h + math.ceil(len(files) / cols) * row_h
    h += pad + 70
    w = pad * 2 + cols * cell_w + (cols - 1) * gap

    canvas = Image.new('RGB', (w, h), BG)
    d = ImageDraw.Draw(canvas)

    f_head = font('Manrope-800.ttf', 34)
    f_cap = font('Manrope-600.ttf', 16)
    f_num = font('Manrope-700.ttf', 15)

    y = pad
    n = 0
    for _, title, base, files in SECTIONS:
        # заголовок секции
        d.rectangle([pad, y + 4, pad + 8, y + 42], fill=ACC)
        d.text((pad + 24, y + 6), title, font=f_head, fill=(255, 255, 255))
        tw = d.textlength(title, font=f_head)
        d.text((pad + 24 + tw + 18, y + 20), 'в папке %d' % len(files),
               font=f_cap, fill=(140, 140, 145))
        y += head_h

        for i, f in enumerate(files):
            col = i % cols
            if col == 0 and i:
                y += row_h
            x = pad + col * (cell_w + gap)
            src = os.path.join(base, f)
            if not os.path.exists(src):
                continue
            n += 1
            canvas.paste(cover(Image.open(src), cell_w, cell_h), (x, y))
            d.rectangle([x, y, x + 46, y + 26], fill=ACC)
            d.text((x + 10, y + 4), '%02d' % n, font=f_num, fill=(255, 255, 255))
            d.text((x, y + cell_h + 7), f.replace('.jpg', ''), font=f_cap,
                   fill=(150, 150, 156))
        y += row_h

    d.text((pad, h - pad - 46),
           'SM-PRODUCTION · все сгенерированные кадры по автосалонам · %d файлов · октябрь 2026' % n,
           font=font('Manrope-600.ttf', 22), fill=(150, 150, 156))
    canvas.save(path, 'JPEG', quality=90, optimize=True)
    print('обзор:', canvas.size, n, 'кадров')
    return n


README = '''SM-PRODUCTION · БРЕНДИНГ АВТОСАЛОНОВ
Все сгенерированные кадры одним архивом
Октябрь 2026

================================================================
ЧТО ВНУТРИ
================================================================

00-obzor.jpg                  сводный контактный лист: все кадры с номерами
00-README.txt                 этот файл

01-standartnye-pozicii/       10 кадров: ресепшн, логотипы, бренд-панели,
                              навигация, подвесы, инфостойки, presswall,
                              фотозона, зона электромобилей + общий вид
02-haval/                     10 кадров того же набора под бренд Haval:
                              премиальный светлый шоурум, логотип на носителях
03-kuby/                      32 кадра: брендированные кубы в разных салонах,
                              зонах аксессуаров, ресепшн, под бренды
                              Chery, Geely, Lada, Jetour
04-reklama-16x9/              6 рекламных макетов 1600 × 900 с текстами
05-reklama-1x1/               6 тех же макетов квадратом 1080 × 1080
06-kontaktnye-listy/          контактные листы наборов (для письма и соцсетей)
07-ishodnye-kadry/            кадры до брендирования: 19 сцен под кубы и
                              9 фонов под рекламу. Нужны, если захотите
                              собрать свой вариант носителя на той же сцене

Всего файлов: {total}

================================================================
ВАЖНО
================================================================

Это ВИЗУАЛИЗАЦИИ, а не фотографии готовых объектов.
Кадры сгенерированы, чтобы показать, как будет выглядеть решение.
Для коммерческих предложений и сайта они подходят как «пример решения»,
но выдавать их за реализованный объект нельзя.

Реальные фото ваших объектов лежат отдельно, в папке
docs/ca-avtosalony/02_prezentaciya/img/ (файлы as-*.jpg):
OMODA C5, HAVAL F7, KGM SsangYong, HONGQI HQ9, TENET T4/T8,
БАЛТАВТОТРЕЙД-М. Их и стоит ставить в портфолио.

Логотипы брендов (Haval, Chery, Geely, Lada, Jetour) в архив не входят:
это не сгенерированные кадры, а векторные знаки. Лежат в
docs/ca-avtosalony/04_haval/brand/ и 06_kuby/brand/.

================================================================
РАЗМЕРЫ И ФОРМАТ
================================================================

01, 02   — 2675 × 1459, JPEG q94 (общий вид — 2268 × 1702)
03       — 2688 × 1792, часть вертикальные 1792 × 2688
04       — 1600 × 900
05       — 1080 × 1080
07       — 1536 × 1024

================================================================
КОНТАКТЫ
================================================================

+7 495 799-00-19 (круглосуточно) · sm-pro1@yandex.ru · sm-production.ru
Москва, Остаповский проезд — центральное производство
'''


def main():
    if os.path.isdir(BUILD):
        shutil.rmtree(BUILD)
    os.makedirs(BUILD)

    total = 0
    for folder, _, base, files in SECTIONS:
        dst = os.path.join(BUILD, folder)
        os.makedirs(dst)
        for f in files:
            src = os.path.join(base, f)
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(dst, f))
                total += 1

    dst = os.path.join(BUILD, '06-kontaktnye-listy')
    os.makedirs(dst)
    for name, src in PREVIEWS:
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(dst, name))
            total += 1

    dst = os.path.join(BUILD, '07-ishodnye-kadry')
    os.makedirs(dst)
    for base, prefix in SOURCES:
        for f in sorted(os.listdir(base)):
            if f.lower().endswith('.jpg'):
                shutil.copy2(os.path.join(base, f), os.path.join(dst, prefix + f))
                total += 1

    n = build_obzor(os.path.join(BUILD, '00-obzor.jpg'))
    print('обзорный лист:', n, 'кадров')

    with open(os.path.join(BUILD, '00-README.txt'), 'w', encoding='utf-8') as fh:
        fh.write(README.format(total=total))

    if os.path.exists(OUT_ZIP):
        os.remove(OUT_ZIP)
    subprocess.run(['zip', '-q', '-r', OUT_ZIP, '.'], cwd=BUILD, check=True)
    size = os.path.getsize(OUT_ZIP)
    print('готово:', OUT_ZIP, round(size / 1e6, 1), 'МБ,', total, 'файлов')
    print('файлов в архиве:', len(zipfile.ZipFile(OUT_ZIP).namelist()))


if __name__ == '__main__':
    main()
