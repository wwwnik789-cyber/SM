#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Кубы для других автомобильных брендов: Chery, Geely, Lada, Jetour.
Логотипы накладываются программно на белые грани в перспективе,
плюс пересъёмка кадра с аксессуарами (без одежды) для серии Haval.
"""
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brand_cubes import SRC, OUT, upscale, put_logo, LOGO_B  # noqa: E402

ROOT = os.path.dirname(os.path.abspath(__file__))
BRAND = os.path.join(ROOT, 'brand')

# кадр -> (файл src, quad белой грани, логотип, uc, vc)
JOBS = [
    ('kub-18-chery.jpg', 'viz-15-chery.png',
     [(180, 405), (390, 402), (392, 588), (182, 592)],
     'chery.png', (0.18, 0.82), (0.34, 0.66)),
    ('kub-19-geely.jpg', 'viz-16-geely.png',
     [(362, 378), (612, 378), (608, 590), (360, 596)],
     'geely.png', (0.16, 0.84), (0.36, 0.64)),
    ('kub-20-lada.jpg', 'viz-17-lada.png',
     [(396, 426), (642, 432), (636, 632), (394, 648)],
     'lada.png', (0.18, 0.82), (0.36, 0.64)),
    ('kub-21-jetour.jpg', 'viz-18-jetour.png',
     [(706, 634), (892, 614), (890, 845), (706, 872)],
     'jetour.png', (0.12, 0.88), (0.42, 0.58)),
    ('kub-16-accessories.jpg', 'viz-19-accessories.png',
     [(1102, 706), (1424, 732), (1424, 945), (1104, 955)],
     None, (0.20, 0.80), (0.40, 0.56)),
]


def to_jpeg(name):
    p = os.path.join(SRC, name)
    if p.lower().endswith('.png'):
        jp = p[:-4] + '.jpg'
        Image.open(p).convert('RGB').save(jp, 'JPEG', quality=95, subsampling=0)
        return os.path.basename(jp)
    return name


def main():
    for out_name, src_name, quad, logo, uc, vc in JOBS:
        src_name = to_jpeg(src_name)
        src_path = os.path.join(SRC, src_name)
        im = Image.open(src_path).convert('RGB')
        logo_path = os.path.join(BRAND, logo) if logo else LOGO_B
        im = put_logo(im, quad, logo_path, uc=uc, vc=vc)
        dst = os.path.join(OUT, out_name)
        im.save(dst, 'JPEG', quality=95, subsampling=0, optimize=True)
        print('готово:', out_name, im.size)
    # апскейл под печать
    for out_name, *_ in JOBS:
        print(out_name, upscale(os.path.join(OUT, out_name)))


if __name__ == '__main__':
    main()
