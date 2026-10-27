#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Брендирование кубов на визуализациях: HAVAL и надписи по граням в перспективе."""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, 'src')
OUT = os.path.join(ROOT, 'vizualizacii')
FONTS = os.path.abspath(os.path.join(ROOT, '..', '02_prezentaciya', 'fonts'))
LOGO_W = os.path.abspath(os.path.join(ROOT, '..', '04_haval', 'brand', 'haval-white.png'))
LOGO_B = os.path.abspath(os.path.join(ROOT, '..', '04_haval', 'brand', 'haval-black.png'))
F_HEAD = os.path.join(FONTS, 'Manrope-800.ttf')
F_SUB = os.path.join(FONTS, 'Manrope-600.ttf')
os.makedirs(OUT, exist_ok=True)


def upscale(path, k=1.75):
    """апскейл под печать: ×1,75 + мягкая резкость"""
    im = Image.open(path).convert('RGB')
    w, h = im.size
    up = im.resize((int(w * k), int(h * k)), Image.LANCZOS).filter(
        ImageFilter.UnsharpMask(radius=1.5, percent=50, threshold=2))
    up.save(path, 'JPEG', quality=94, subsampling=0, optimize=True)
    return up.size


def find_coeffs(pa, pb):
    M = []
    for p1, p2 in zip(pa, pb):
        M.append([p1[0], p1[1], 1, 0, 0, 0, -p2[0] * p1[0], -p2[0] * p1[1]])
        M.append([0, 0, 0, p1[0], p1[1], 1, -p2[1] * p1[0], -p2[1] * p1[1]])
    A = np.matrix(M, dtype=float)
    B = np.array(pb).reshape(8)
    return np.array(np.dot(np.linalg.inv(A.T * A) * A.T, B)).reshape(8)


def face_size(quad):
    TL, TR, BR, BL = quad
    w = (np.hypot(TR[0] - TL[0], TR[1] - TL[1]) + np.hypot(BR[0] - BL[0], BR[1] - BL[1])) / 2
    h = (np.hypot(BL[0] - TL[0], BL[1] - TL[1]) + np.hypot(BR[0] - TR[0], BR[1] - TR[1])) / 2
    return int(w), int(h)


def put_text(base, quad, lines, size_frac=0.13, color=(255, 255, 255), align='left',
             pad=(0.10, 0.12), shadow=None, tracking=0.0, line_gap=1.18):
    W, H = base.size
    w, h = face_size(quad)
    canvas = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(canvas)
    fs = max(8, int(h * size_frac))
    font = ImageFont.truetype(F_HEAD, fs)
    # автоподбор кегля под ширину грани
    maxw = w * (1 - 2 * pad[0])
    for _ in range(40):
        if max(d.textlength(l, font=font) for l in lines) <= maxw:
            break
        fs -= 1
        font = ImageFont.truetype(F_HEAD, fs)
    lh = int(fs * line_gap)
    total = lh * len(lines)
    y = int(h * pad[1]) if align != 'center' else int((h - total) / 2)
    for line in lines:
        txt_w = d.textlength(line, font=font)
        x = int(w * pad[0]) if align == 'left' else int((w - txt_w) / 2)
        if tracking:
            for ch in line:
                if shadow:
                    d.text((x + 1, y + 2), ch, font=font, fill=shadow)
                d.text((x, y), ch, font=font, fill=color)
                x += d.textlength(ch, font=font) + tracking
        else:
            if shadow:
                d.text((x + 1, y + 2), line, font=font, fill=shadow)
            d.text((x, y), line, font=font, fill=color)
        y += lh
    return _warp(base, canvas, quad)


def put_logo(base, quad, logo_path, uc=(0.5, 0.5), vc=(0.5, 0.5)):
    """логотип по центру грани с заданными долями"""
    W, H = base.size
    w, h = face_size(quad)
    logo = Image.open(logo_path).convert('RGBA')
    lw = int(w * (uc[1] - uc[0]))
    lh = int(lw * logo.size[1] / logo.size[0])
    canvas = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    canvas.alpha_composite(logo.resize((lw, lh), Image.LANCZOS),
                           (int(w * uc[0]), int(h * vc[0] - lh / 2 + (vc[1] - vc[0]) * h / 2)))
    return _warp(base, canvas, quad)


def _warp(base, canvas, quad):
    W, H = base.size
    cw, ch = canvas.size
    c = find_coeffs(quad, [(0, 0), (cw, 0), (cw, ch), (0, ch)])
    warped = canvas.transform((W, H), Image.PERSPECTIVE, c, Image.BICUBIC)
    out = base.convert('RGBA')
    out.alpha_composite(warped)
    return out.convert('RGB')


def _brand_hero():
    im = Image.open(os.path.join(SRC, 'viz-01-hero.jpg')).convert('RGB')
    # нижний куб: бирюзовая грань
    im = put_text(im, [(457, 1101), (697, 1127), (695, 1378), (457, 1337)],
                  ['СДЕЛАНО', 'В РОССИИ'], size_frac=0.16, pad=(0.12, 0.12))
    # четвёртый снизу (тёмный): текст белым
    im = put_text(im, [(504, 358), (686, 351), (686, 586), (504, 596)],
                  ['СИСТЕМЫ', 'ПОМОЩИ', 'ВОДИТЕЛЮ'], size_frac=0.12, pad=(0.11, 0.14))
    im.save(os.path.join(OUT, 'kub-06-hero.jpg'), 'JPEG', quality=94, subsampling=0, optimize=True)
    print('hero готово')



def _brand_extra():
    # фасад: бирюзовый нижний куб
    im = Image.open(os.path.join(SRC, 'viz-05-facade.jpg')).convert('RGB')
    im = put_text(im, [(905, 760), (1118, 762), (1122, 898), (903, 905)],
                  ['СДЕЛАНО', 'В РОССИИ'], size_frac=0.16, pad=(0.13, 0.14))
    im.save(os.path.join(OUT, 'kub-07-facade.jpg'), 'JPEG', quality=94, subsampling=0, optimize=True)
    print('фасад готово')

    # производство: бирюзовый куб на столе
    im = Image.open(os.path.join(SRC, 'viz-06-production.jpg')).convert('RGB')
    im = put_text(im, [(96, 190), (455, 186), (452, 560), (100, 578)],
                  ['СДЕЛАНО', 'В РОССИИ'], size_frac=0.14, pad=(0.12, 0.16))
    im.save(os.path.join(OUT, 'kub-08-production.jpg'), 'JPEG', quality=94, subsampling=0, optimize=True)
    print('производство готово')

    # навигация: бирюзовый куб-указатель
    im = Image.open(os.path.join(SRC, 'viz-04-navigation.jpg')).convert('RGB')
    im = put_text(im, [(120, 1060), (434, 1052), (452, 1300), (118, 1312)],
                  ['HAVAL'], size_frac=0.18, pad=(0.14, 0.16), align='center')
    im.save(os.path.join(OUT, 'kub-09-navigation.jpg'), 'JPEG', quality=94, subsampling=0, optimize=True)
    print('навигация готово')



# --- вторая серия: интерьеры разных автосалонов -----------------------------
FACES = {
    'viz-07-premium-dark.jpg|kub-10-premium-dark.jpg': dict(text=['СДЕЛАНО', 'В РОССИИ'],
        quad=[(531, 721), (676, 670), (760, 910), (616, 961)]),
    'viz-08-minimal.jpg|kub-11-minimal.jpg': dict(text=['СИСТЕМЫ', 'ПОМОЩИ', 'ВОДИТЕЛЮ'],
        quad=[(306, 434), (528, 440), (528, 658), (306, 666)]),
    'viz-09-coffee.jpg|kub-12-coffee.jpg': dict(text=['6 ПОДУШЕК', 'БЕЗОПАСНОСТИ'],
        quad=[(83, 603), (368, 550), (418, 822), (133, 875)]),
    'viz-10-loft.jpg|kub-13-loft.jpg': dict(text=['СДЕЛАНО', 'В РОССИИ'],
        quad=[(268, 745), (452, 752), (452, 962), (268, 955)]),
    'viz-11-delivery.jpg|kub-14-delivery.jpg': dict(text=['ЭКОНОМИЧНЫЙ', 'ДВИГАТЕЛЬ'],
        quad=[(362, 655), (627, 660), (624, 986), (362, 983)]),
    'viz-12-family.jpg|kub-15-family.jpg': dict(text=['СДЕЛАНО', 'В РОССИИ'],
        quad=[(238, 632), (554, 622), (448, 876), (236, 858)]),
    'viz-13-accessories.jpg|kub-16-accessories.jpg': dict(text=['HAVAL'], logo=True,
        quad=[(370, 520), (760, 520), (760, 890), (370, 918)]),
    'viz-14-ev.jpg|kub-17-ev.jpg': dict(text=['СДЕЛАНО', 'В РОССИИ'],
        quad=[(708, 556), (918, 556), (912, 903), (706, 893)]),
}


def _brand_second():
    for fname, spec in FACES.items():
        im = Image.open(os.path.join(SRC, fname.split('|')[0])).convert('RGB')
        if spec.get('logo'):
            im = put_logo(im, spec['quad'], LOGO_B, uc=(0.20, 0.80), vc=(0.40, 0.60))
        else:
            im = put_text(im, spec['quad'], spec['text'], size_frac=0.13, pad=(0.11, 0.13))
        out = fname.split('|')[1]
        im.save(os.path.join(OUT, out), 'JPEG', quality=94, subsampling=0, optimize=True)
        print(out, 'готово')


if __name__ == '__main__':
    # 02 — деталь: бирюзовая грань с надписью
    im = Image.open(os.path.join(SRC, 'viz-02-detail.jpg')).convert('RGB')
    im = put_text(im, [(277, 76), (596, 107), (596, 518), (277, 487)],
                  ['СДЕЛАНО', 'В РОССИИ'], size_frac=0.15, pad=(0.12, 0.10))
    # серая грань: логотип
    im = put_logo(im, [(596, 107), (866, 76), (866, 500), (596, 518)], LOGO_B,
                  uc=(0.18, 0.82), vc=(0.40, 0.60))
    im.save(os.path.join(OUT, 'kub-04-detail.jpg'), 'JPEG', quality=94, subsampling=0, optimize=True)
    print('02 готово')

    # 03 — лаунж: надписи на бирюзовой и графитовой гранях
    im = Image.open(os.path.join(SRC, 'viz-03-lounge.jpg')).convert('RGB')
    im = put_text(im, [(185, 637), (470, 648), (470, 962), (185, 952)],
                  ['СДЕЛАНО', 'В РОССИИ'], size_frac=0.15, pad=(0.12, 0.10))
    im = put_text(im, [(470, 648), (765, 662), (765, 975), (470, 962)],
                  ['6 ПОДУШЕК', 'БЕЗОПАСНОСТИ'], size_frac=0.13, pad=(0.12, 0.10))
    im.save(os.path.join(OUT, 'kub-05-lounge.jpg'), 'JPEG', quality=94, subsampling=0, optimize=True)
    print('03 готово')

    _brand_hero()
    _brand_extra()
    _brand_second()
    import glob
    for f in sorted(glob.glob(os.path.join(OUT, '*.jpg'))):
        print(os.path.basename(f), '->', upscale(f))
