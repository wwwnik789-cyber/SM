#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сборка рекламных макетов «Автосалоны» из сгенерированных баз.

Вход:  src/base-*.png   (1536x1024)
Выход: reklama-NN-*.jpg (1600x900), social-NN-*.jpg (1080x1080), preview.jpg
Шрифты: ../../02_prezentaciya/fonts (Unbounded, Manrope)
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, 'src')
FONTS = os.path.abspath(os.path.join(ROOT, '..', '02_prezentaciya', 'fonts'))

GRAPHITE = (15, 15, 15)
WHITE = (255, 255, 255)
MINT = (114, 214, 216)
GREY = (217, 219, 223)
SUB = (226, 229, 232)

F_HEAD = os.path.join(FONTS, 'Unbounded-800.ttf')
F_KICK = os.path.join(FONTS, 'Manrope-700.ttf')
F_SUB = os.path.join(FONTS, 'Manrope-400.ttf')
F_NUM = os.path.join(FONTS, 'Manrope-600.ttf')

PHONE = '+7 495 799-00-19'
MAIL = 'sm-pro1@yandex.ru'
SITE = 'sm-production.ru'

CREATIVES = [
    dict(name='01-reception', base='composed-lounge.jpg', anchor='right',
         kicker='SM PRODUCTION · АВТОСАЛОНЫ',
         head=['Клиенту', 'есть где ждать'],
         sub=['Зона ожидания, кофе-поинт,', 'брендирование стены.', 'Продумываем визит целиком.'],
         square_x=0),
    dict(name='02-stands', base='base-stands.jpg', anchor='right',
         kicker='SM PRODUCTION · АВТОСАЛОНЫ',
         head=['Стойки', 'для зала'],
         sub=['Акрил 8–10 мм, сменный вкладыш,', 'без сверления пола.', 'Своё производство.'],
         square_x=0),
    dict(name='03-navigation', base='base-navigation.jpg', anchor='bottom',
         kicker='SM PRODUCTION · АВТОСАЛОНЫ',
         head=['Клиент', 'не заблудится'],
         sub=['Тотемы, подвесные указатели, таблички', 'и пиктограммы — по брендбуку дилера.'],
         square_x=300, scrim=236),
    dict(name='04-presswall', base='base-presswall.jpg', anchor='bottom',
         kicker='SM PRODUCTION · АВТОСАЛОНЫ',
         head=['PressWall', 'для выдачи'],
         sub=['Матовое полотно без блика, смена', 'изображения за 15 минут.'],
         square_x=120, scrim=228),
    dict(name='05-facade', base='composed-facade.jpg', anchor='bottom',
         kicker='SM PRODUCTION · АВТОСАЛОНЫ',
         head=['Ваш бренд', 'на фасаде'],
         sub=['Световой короб, объёмные буквы,', 'монтаж с автовышки. Москва и область.'],
         square_x=250, scrim=236),
    dict(name='06-reception', base='composed-reception.jpg', anchor='right',
         kicker='SM PRODUCTION · АВТОСАЛОНЫ',
         head=['Ресепшн', 'под ключ'],
         sub=['Стойка, логотип, свет, скрытая', 'проводка. Десять носителей', 'в одном стиле.'],
         square_x=0, scrim=224),
]


def cover(im, w, h, ox=0.5):
    iw, ih = im.size
    k = max(w / iw, h / ih)
    nw, nh = int(iw * k + 0.5), int(ih * k + 0.5)
    im = im.resize((nw, nh), Image.LANCZOS)
    x = int((nw - w) * ox)
    y = int((nh - h) * 0.5)
    return im.crop((x, y, x + w, y + h))


def square(im, side, ox_px=0):
    """квадрат 1024x1024 из базы 1536x1024 со сдвигом ox_px"""
    iw, ih = im.size
    box = (ox_px, 0, ox_px + ih, ih)
    return im.crop(box).resize((side, side), Image.LANCZOS)


def scrim(size, anchor, strength=205):
    """плотная подложка-панель с мягким переходом"""
    w, h = size
    a = np.zeros((h, w), np.float32)
    if anchor == 'right':
        x0 = int(w * 0.44)
        ramp = int(w * 0.24)
        x = np.arange(w, dtype=np.float32)
        t = np.clip((x - x0) / ramp, 0, 1)
        t = t * t * (3 - 2 * t)
        t = 0.35 * t + 0.65 * (t ** 2.2)
        a = np.repeat(t[None, :] * strength, h, axis=0)
    elif anchor == 'bottom':
        y0 = int(h * 0.30)
        ramp = int(h * 0.46)
        y = np.arange(h, dtype=np.float32)
        t = np.clip((y - y0) / ramp, 0, 1)
        t = t * t * (3 - 2 * t)
        a = np.repeat(t[:, None] * strength, w, axis=1)
    # нижняя полоса под контакты
    y0 = int(h * 0.80)
    y = np.arange(h, dtype=np.float32)
    t = np.clip((y - y0) / (h - y0), 0, 1)
    a = np.maximum(a, np.repeat((t[:, None] ** 0.9) * (strength * 0.85), w, axis=1))
    return Image.fromarray(a.astype(np.uint8), 'L')


def apply_scrim(im, anchor, strength):
    w, h = im.size
    m = scrim((w, h), anchor, strength)
    dark = Image.new('RGB', (w, h), (8, 9, 10))
    return Image.composite(dark, im, m)


def wrap(font, text, max_w, draw):
    words = text.split()
    lines, cur = [], ''
    for wd in words:
        t = (cur + ' ' + wd).strip()
        if draw.textlength(t, font=font) <= max_w or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


def draw_tracked(draw, xy, text, font, fill, tracking):
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += draw.textlength(ch, font=font) + tracking


def text_block(im, spec, anchor, scale=1.0):
    w, h = im.size
    d = ImageDraw.Draw(im)
    margin = int(w * 0.055)
    box_w = int(w * 0.40) if anchor == 'right' else int(w * 0.58)

    hsize = int(66 * scale)
    head = ImageFont.truetype(F_HEAD, hsize)
    for _ in range(50):
        if max(d.textlength(l, font=head) for l in spec['head']) <= box_w:
            break
        hsize -= 2
        head = ImageFont.truetype(F_HEAD, hsize)

    ssize = int(27 * scale)
    sub = ImageFont.truetype(F_SUB, ssize)
    for _ in range(40):
        if max(d.textlength(l, font=sub) for l in spec['sub']) <= box_w:
            break
        ssize -= 1
        sub = ImageFont.truetype(F_SUB, ssize)

    ksize = int(18 * scale)
    csize = int(19 * scale)
    kick = ImageFont.truetype(F_KICK, ksize)
    cont = ImageFont.truetype(F_NUM, csize)

    head_lines = []
    for line in spec['head']:
        head_lines += wrap(head, line, box_w, d)
    lh = int(hsize * 1.12)
    sub_lines = []
    for line in spec['sub']:
        sub_lines += wrap(sub, line, box_w, d)
    slh = int(ssize * 1.42)

    total = ksize + int(22 * scale) + len(head_lines) * lh + int(24 * scale) + int(4 * scale) \
        + int(30 * scale) + len(sub_lines) * slh

    if anchor == 'right':
        x = w - margin - box_w
        y = int((h - total) * 0.44)
    else:
        x = margin
        y = h - margin - int(64 * scale) - total

    kw = sum(d.textlength(ch, font=kick) + 2.2 * scale for ch in spec['kicker'])
    pad_x, pad_y = int(14 * scale), int(7 * scale)
    overlay = Image.new('RGBA', im.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rounded_rectangle([x - pad_x, y - pad_y, x + kw + pad_x, y + ksize + pad_y],
                         radius=int(4 * scale), fill=(10, 11, 12, 150))
    im = Image.alpha_composite(im.convert('RGBA'), overlay).convert('RGB')
    d = ImageDraw.Draw(im)
    draw_tracked(d, (x, y), spec['kicker'], kick, MINT, 2.2 * scale)
    y += ksize + int(22 * scale)
    for line in head_lines:
        d.text((x, y), line, font=head, fill=WHITE)
        y += lh
    y += int(24 * scale)
    d.rectangle([x, y, x + int(84 * scale), y + max(3, int(4 * scale))], fill=MINT)
    y += int(30 * scale)
    for line in sub_lines:
        d.text((x, y), line, font=sub, fill=SUB)
        y += slh

    # контакты
    cy = h - margin - int(16 * scale)
    contacts = f'{PHONE}   ·   {MAIL}   ·   {SITE}'
    draw_tracked(d, (margin, cy), contacts, cont, GREY, 0.6 * scale)
    note = 'КП — в течение дня   ·   ПН–ПТ 10:00–18:00'
    nf = ImageFont.truetype(F_SUB, int(csize * 0.86))
    d.text((w - margin - d.textlength(note, font=nf), cy + int(2 * scale)), note, font=nf, fill=(176, 182, 188))
    return im


def build():
    for spec in CREATIVES:
        src = Image.open(os.path.join(SRC, spec['base'])).convert('RGB')

        # 16:9
        big = cover(src, 1600, 900)
        strength = spec.get('scrim') or (218 if spec['anchor'] == 'right' else 232)
        big = apply_scrim(big, spec['anchor'], strength)
        big = text_block(big, spec, spec['anchor'], 1.0)
        big.save(os.path.join(ROOT, f'reklama-{spec["name"]}.jpg'), 'JPEG', quality=92,
                 subsampling=0, optimize=True)

        # 1:1
        sq = square(src, 1024, spec['square_x'])
        sq = sq.resize((1080, 1080), Image.LANCZOS)
        sq = apply_scrim(sq, 'bottom', spec.get('scrim_sq') or 225)
        sq = text_block(sq, spec, 'bottom', 0.80)
        sq.save(os.path.join(ROOT, f'social-{spec["name"]}.jpg'), 'JPEG', quality=92,
                subsampling=0, optimize=True)
        print('готово', spec['name'])


if __name__ == '__main__':
    build()
