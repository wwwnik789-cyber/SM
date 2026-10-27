#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Зоны аксессуаров и ресепшн: брендирование кубов HAVAL + текст в перспективе."""
import json
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from brand_cubes import SRC, OUT, upscale, put_logo, put_text, LOGO_B  # noqa: E402

QUADS = json.load(open('/tmp/quads_auto.json', encoding='utf-8'))
REF = json.load(open('/tmp/quads_ref.json', encoding='utf-8')) if os.path.exists('/tmp/quads_ref.json') else {}
QUADS.update(REF)

# src -> (выход, логотип/надпись, тип, uc, vc)
JOBS = [
    ('viz-20-acc-wheels', 'kub-22-accessories-wheels', 'logo', (0.18, 0.82), (0.34, 0.66)),
    ('viz-21-acc-winter', 'kub-23-accessories-winter', 'logo', (0.18, 0.82), (0.34, 0.66)),
    ('viz-22-acc-travel', 'kub-24-accessories-travel', 'logo', (0.18, 0.82), (0.34, 0.66)),
    ('viz-23-acc-vitrina', 'kub-25-accessories-vitrina', 'logo', (0.20, 0.80), (0.36, 0.64)),
    ('viz-24-rcp-light', 'kub-26-reception-light', 'text', (0.0, 0.0), (0.0, 0.0)),
    ('viz-25-rcp-dark', 'kub-27-reception-dark', 'logo', (0.20, 0.80), (0.36, 0.64)),
    ('viz-26-rcp-loft', 'kub-28-reception-loft', 'logo', (0.18, 0.82), (0.36, 0.64)),
    ('viz-27-rcp-minimal', 'kub-29-reception-minimal', 'logo', (0.20, 0.80), (0.36, 0.64)),
    ('viz-28-rcp-portrait', 'kub-30-reception-portrait', 'logo', (0.18, 0.82), (0.34, 0.66)),
]


def main():
    for src, dst, kind, uc, vc in JOBS:
        im = Image.open(os.path.join(SRC, src + '.png')).convert('RGB')
        q = QUADS[src]
        if kind == 'logo':
            im = put_logo(im, q, LOGO_B, uc=uc, vc=vc)
        else:
            im = put_text(im, q, ['HAVAL'], size_frac=0.20, pad=(0.10, 0.10),
                          align='center', color=(31, 31, 31))
        p = os.path.join(OUT, dst + '.jpg')
        im.save(p, 'JPEG', quality=95, subsampling=0, optimize=True)
        print('готово:', dst, im.size)
    for _, dst, *_ in JOBS:
        print(dst, upscale(os.path.join(OUT, dst + '.jpg')))


if __name__ == '__main__':
    main()
