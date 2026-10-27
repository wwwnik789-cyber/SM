#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Макет страницы «Сотрудничество» для BAK MASTERS.

Собирает один вертикальный макет: реальные тексты + фото + пометки,
каким блоком Tilda собирать каждый экран.
"""
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.abspath(os.path.join(
    HERE, '..', '..', 'docs', 'ca-avtosalony', '02_prezentaciya', 'fonts'))
F_H = os.path.join(FONTS, 'Manrope-800.ttf')
F_S = os.path.join(FONTS, 'Manrope-700.ttf')
F_B = os.path.join(FONTS, 'Manrope-400.ttf')
F_M = os.path.join(FONTS, 'Manrope-600.ttf')

BG = (246, 241, 233)
CARD = (255, 255, 255)
INK = (43, 38, 33)
MUTED = (122, 111, 99)
ACC = (47, 111, 107)
DARK = (35, 32, 29)
LINE = (228, 219, 205)

W = 1600
M = 120          # поля
CW = W - 2 * M   # ширина контента 1360
TOP = 90

img = Image.new('RGB', (W, 9600), BG)
d = ImageDraw.Draw(img)


def font(path, size):
    return ImageFont.truetype(path, size)


def wrap(text, f, maxw):
    words = text.split()
    lines, cur = [], ''
    for w_ in words:
        t = (cur + ' ' + w_).strip()
        if d.textlength(t, font=f) <= maxw:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


def para(text, f, color, maxw, x, y, lh=1.55, draw=img):
    dd = ImageDraw.Draw(draw)
    for line in wrap(text, f, maxw):
        dd.text((x, y), line, font=f, fill=color)
        y += int(f.size * lh)
    return y


def section_label(y, num, block, name):
    f = font(F_S, 15)
    txt = f'БЛОК {num}  ·  {block}  —  {name}'
    tw = d.textlength(txt, font=f)
    d.rounded_rectangle([M, y, M + tw + 32, y + 34], 6, fill=(232, 240, 238))
    d.text((M + 16, y + 9), txt, font=f, fill=ACC)
    return y + 34 + 42


def h2(y, text):
    para(text, font(F_H, 40), INK, CW, M, y, lh=1.25)
    return y + 40 * 1.25 * len(wrap(text, font(F_H, 40), CW)) + 30


def card(x, y, w, h, title, text, num=None):
    d.rounded_rectangle([x, y, x + w, y + h], 14, fill=CARD, outline=LINE, width=1)
    yy = y + 26
    if num:
        d.rounded_rectangle([x + 24, yy, x + 24 + 34, yy + 34], 8, fill=ACC)
        d.text((x + 34, yy + 6), num, font=font(F_S, 18), fill=CARD)
        yy += 34 + 16
    for line in wrap(title, font(F_S, 21), w - 48):
        d.text((x + 24, yy), line, font=font(F_S, 21), fill=INK)
        yy += 21 * 1.3
    yy += 8
    para(text, font(F_B, 16), MUTED, w - 48, x + 24, yy, lh=1.5)
    return y + h


# ============================== 1. ОБЛОЖКА ==============================
cover_h = 780
hero = Image.open(os.path.join(HERE, 'foto-01-hero.jpg')).convert('RGB')
# сначала подрезаем под пропорцию 1600x780, затем ресайз — без чёрных полей
tgt_ratio = W / cover_h
if hero.width / hero.height > tgt_ratio:
    nh = hero.height
    nw = int(nh * tgt_ratio)
    x0 = (hero.width - nw) // 2
    hero = hero.crop((x0, 0, x0 + nw, nh))
else:
    nw = hero.width
    nh = int(nw / tgt_ratio)
    y0 = (hero.height - nh) // 2
    hero = hero.crop((0, y0, nw, y0 + nh))
hero = hero.resize((W, cover_h), Image.LANCZOS)
img.paste(hero, (0, 0))
scrim = Image.new('RGBA', (W, cover_h), (0, 0, 0, 0))
sd = ImageDraw.Draw(scrim)
for i in range(cover_h):
    a = int(150 * (i / cover_h) ** 1.4)
    sd.line([(0, i), (W, i)], fill=(20, 17, 14, a))
img.paste(Image.alpha_composite(img.crop((0, 0, W, cover_h)).convert('RGBA'), scrim).convert('RGB'), (0, 0))

y = 150
d.text((M, y), 'BAK MASTERS · СОТРУДНИЧЕСТВО', font=font(F_S, 16), fill=(255, 255, 255))
y += 44
h1_lines = wrap('Сотрудничество с дизайнерами интерьера', font(F_H, 58), 1000)
for line in h1_lines:
    d.text((M, y), line, font=font(F_H, 58), fill=CARD)
    y += 58 * 1.18
y += 26
y = para('Делаем изделия из дерева и эпоксидной смолы по вашему проекту: размер, порода, '
         'оттенок смолы, металл подстолья. Присылаем образцы и материалы для презентации '
         'клиенту, работаем под этапы объекта.',
         font(F_B, 21), (238, 233, 226), 780, M, y, lh=1.5)
y += 44

# кнопки
d.rounded_rectangle([M, y, M + 250, y + 60], 10, fill=ACC)
d.text((M + 34, y + 18), 'Обсудить проект', font=font(F_S, 19), fill=CARD)
d.rounded_rectangle([M + 272, y, M + 566, y + 60], 10, outline=(255, 255, 255), width=2)
d.text((M + 302, y + 18), 'Написать в WhatsApp', font=font(F_S, 19), fill=CARD)

y = cover_h + 40
for i, t in enumerate(['Партии от (уточнить)', 'Образцы до заказа',
                       'Материалы для презентации', 'Москва · доставка по РФ']):
    f = font(F_B, 16)
    tw = d.textlength(t, font=f)
    x = M + i * 340
    d.rounded_rectangle([x, y, x + tw + 36, y + 40], 20, fill=CARD, outline=LINE)
    d.text((x + 18, y + 11), t, font=f, fill=INK)
y += 40 + 80

# ============================== 2. ШЕСТЬ ПРИЧИН ==============================
y = section_label(y, '2', 'T-cards', 'шесть причин отдать изделие нам')
y = h2(y, 'Шесть причин отдать изделие нам')
cards = [
    ('1', 'Изделие под проект, а не «что было»',
     'Размер под нишу, высота под диван, оттенок под палитру помещения. Не подгоняем проект под каталог.'),
    ('2', 'Повторяемость',
     'Нужно 6 одинаковых подставок или добор через полгода, когда разбили одну? Повторим по образцу.'),
    ('3', 'Материалы для презентации',
     'Фото в высоком разрешении, размеры, вес, покрытие. Отдаём папкой, а не по одной картинке в переписке.'),
    ('4', 'Образцы до заказа',
     'Породы и оттенки смолы можно посмотреть вживую — до счёта и до согласования с клиентом.'),
    ('5', 'Сроки под этапы объекта',
     'Финишные предметы нужны к сдаче, а не через месяц после. Срок фиксируем датой в счёте.'),
    ('6', 'Ваш клиент остаётся вашим',
     'Не выходим на заказчика без вашего согласия и не предлагаем «сделать дешевле без посредника».'),
]
cw3 = (CW - 2 * 24) // 3
for i, (n, t, tx) in enumerate(cards):
    cx = M + (i % 3) * (cw3 + 24)
    cy = y + (i // 3) * 236
    card(cx, cy, cw3, 216, t, tx, n)
y += 2 * 236 + 40

# ============================== 3. ТАБЛИЦА ==============================
y = section_label(y, '3', 'T-table', 'что можно включить в проект')
y = h2(y, 'Что можно включить в проект')
rows = [
    ('Придвижной столик из спила', 'у дивана, в изголовье, в лаунж-зоне', '10–20 дней'),
    ('Журнальный / кофейный столик', 'гостиная, холл, лобби', '15–25 дней'),
    ('Чайный столик, чабань', 'чайная зона, переговорная, спа', '10–20 дней'),
    ('Кухонный борд', 'кухня-остров, фартук, подача', '7–14 дней'),
    ('Борд для подачи', 'столовая, сервировка, фотосъёмка', '7–14 дней'),
    ('Подсвечник, шотница, пепельница', 'консоль, бар, терраса', '7–14 дней'),
]
colx = [M + 24, M + 560, M + 1080]
d.rounded_rectangle([M, y, M + CW, y + 56], 0, fill=(238, 231, 219))
for i, t in enumerate(['Изделие', 'Где работает в интерьере', 'Срок']):
    d.text((colx[i], y + 16), t, font=font(F_S, 16), fill=MUTED)
y += 56
for i, r in enumerate(rows):
    hh = 64
    if i % 2 == 0:
        d.rectangle([M, y, M + CW, y + hh], fill=CARD)
    for j, t in enumerate(r):
        d.text((colx[j], y + 20), t, font=font(F_B if j else F_M, 17), fill=INK if j != 2 else ACC)
    d.line([(M, y + hh), (M + CW, y + hh)], fill=LINE)
    y += hh
y += 26
para('Столешницы-слэбы, обеденные столы и крупные формы — обсуждаем отдельно.', font(F_B, 15), MUTED, CW, M, y)
y += 90

# ============================== 4. МАТЕРИАЛЫ ==============================
y = section_label(y, '4', 'T-two-columns', 'материалы и палитра — спецификация для альбома')
y = h2(y, 'Из чего можно выбирать')
left_w = 760
spec = [
    ('Породы дерева', 'абрикос · груша · тутовник · каповый тополь · дуб'),
    ('Оттенки смолы', 'прозрачный · молочный · чёрный · синий · бирюзовый · охра · сизый'),
    ('Подстолье', 'металл с порошковой покраской · дерево'),
    ('Покрытие', 'масло-воск, обновление раз в N лет'),
    ('Кромка и форма', 'живой край спила, скруглённая, фигурная'),
    ('Максимальный размер', 'указать — влияет на выбор объекта'),
]
sy = y
for i, (k, v) in enumerate(spec):
    d.text((M, sy + 6), k, font=font(F_S, 16), fill=MUTED)
    para(v, font(F_B, 17), INK, left_w - 240, M + 240, sy, lh=1.4)
    sy += 74
    d.line([(M, sy - 22), (M + left_w, sy - 22)], fill=LINE)
pal = Image.open(os.path.join(HERE, 'foto-03-palitra.jpg')).convert('RGB')
pw = int(CW - left_w - 50)
ph = int(pal.height * float(pw) / pal.width)
pal = pal.resize((pw, ph), Image.LANCZOS)
img.paste(pal, (int(M + left_w + 50), int(y)))
y = max(sy, y + ph) + 90

# ============================== 5. ШАГИ ==============================
y = section_label(y, '5', 'T-timeline', 'шесть шагов работы над проектом')
y = h2(y, 'Шесть шагов — от вашего чертежа до объекта')
steps = [
    ('1', 'Бриф', 'Чертёж, референс или фото интерьера, размеры ниши, срок сдачи и бюджет.'),
    ('2', 'Материалы и образцы', 'Отдаём фото, размеры и спецификацию для альбома, показываем породы и оттенки.'),
    ('3', 'Эскиз и смета', 'Считаем стоимость и срок. Смету можно показать клиенту как есть.'),
    ('4', 'Согласование и счёт', 'Фиксируем размеры, колер, подстолье и дату готовности. Предоплата 50 %.'),
    ('5', 'Производство с фотоотчётом', 'Заливка, шлифовка, масло. Присылаем фото с этапов — объект под контролем.'),
    ('6', 'Передача', 'Фото готового изделия, жёсткая упаковка, доставка СДЭК или ТК.'),
]
sty = y
d.line([(M + 25, y + 30), (M + 25, y + 6 * 92 - 30)], fill=LINE, width=2)
for i, (n, t, tx) in enumerate(steps):
    cy = y + i * 92
    d.ellipse([M, cy + 6, M + 50, cy + 56], fill=ACC)
    d.text((M + 17, cy + 20), n, font=font(F_S, 20), fill=CARD)
    d.text((M + 76, cy + 8), t, font=font(F_S, 21), fill=INK)
    para(tx, font(F_B, 16), MUTED, 900, M + 76, cy + 42, lh=1.4)
y += 6 * 92 + 40

# ============================== 6. ЧТО ПРИСЛАТЬ ==============================
y = section_label(y, '6', 'T-two-columns', 'минимум данных для расчёта')
y = h2(y, 'Минимум, чтобы мы посчитали')
checks = ['вид изделия и количество',
          'размеры — можно диапазоном',
          'порода и оттенок смолы, если выбраны',
          'фото интерьера или референс',
          'к какому числу нужен объект',
          'бюджет, в который нужно попасть']
cy = y
for t in checks:
    d.rounded_rectangle([M, cy + 6, M + 22, cy + 28], 4, fill=ACC)
    d.text((M + 36, cy), t, font=font(F_B, 18), fill=INK)
    cy += 46
d.rounded_rectangle([M + 760, y - 10, M + CW, y + 200], 14, fill=CARD, outline=LINE)
para('Если половины данных нет — присылайте что есть,\nостальное уточним в переписке.\n\nРасчёт — в течение рабочего дня',
     font(F_B, 17), MUTED, 480, M + 790, y + 22, lh=1.5)
y = max(cy, y + 210) + 80

# ============================== 7. ПАРТНЁРСКИЕ УСЛОВИЯ ==============================
y = section_label(y, '7', 'T-cards', 'главный коммерческий блок')
y = h2(y, 'Как мы считаем для дизайнеров')
p3 = [('Скидка от розницы', 'Указать процент или шкалу. Без цифры дизайнер не понимает свою маржу.'),
      ('Комиссия от заказа', 'Если удобнее получать вознаграждение, а клиенту показывать розничную цену.'),
      ('Спеццена под объект', 'Для комплектов и повторяющихся позиций — влияет объём и переналадка.')]
for i, (t, tx) in enumerate(p3):
    card(M + i * (cw3 + 24), y, cw3, 200, t, tx)
y += 200 + 24
para('Договор с вами или с клиентом — как удобнее. Образцы и выкладки для студий — уточнить условия.',
     font(F_B, 15), MUTED, CW, M, y)
y += 90

# ============================== 8. ФОРМАТЫ ==============================
y = section_label(y, '8', 'T-cards', 'три формата работы')
y = h2(y, 'От одного предмета до постоянного партнёрства')
f3 = [('Разовый предмет', 'Акцент в проект: столик, борд, подсвечник. Один расчёт, один срок.'),
      ('Комплект под объект', '5–30 предметов в единой палитре: столовая группа, бар, ресепшн.'),
      ('Постоянное партнёрство', 'Держим вашу спецификацию, повторяем позиции, подставляем сроки.')]
for i, (t, tx) in enumerate(f3):
    card(M + i * (cw3 + 24), y, cw3, 180, t, tx)
y += 180 + 80

# ============================== 9. ПРОЕКТЫ ==============================
y = section_label(y, '9', 'T-gallery', 'проекты и подборка по интерьерам')
y = h2(y, 'Что уже сделано')
gal = [('foto-01-hero.jpg', 'Гостиная · придвижной столик, абрикос, бирюзовая смола'),
       ('foto-06-bord.jpg', 'Столовая · борд для подачи, торец + смола'),
       ('foto-05-razmer.jpg', 'Ниша 480 мм · попали в размер без подгонки')]
gw = (CW - 2 * 20) // 3
for i, (fn, cap) in enumerate(gal):
    im = Image.open(os.path.join(HERE, fn)).convert('RGB')
    gh = int(gw * 0.72)
    im = im.resize((gw, int(im.height * gw / im.width)), Image.LANCZOS)
    im = im.crop((0, max(0, (im.height - gh) // 2), gw, max(gh, (im.height - gh) // 2 + gh)))
    gx = int(M + i * (gw + 20))
    img.paste(im, (gx, int(y)))
    para(cap, font(F_B, 15), MUTED, gw, gx, int(y + gh + 12), lh=1.4)
y += int(gw * 0.72) + 100

# ============================== 10. ДРУГИМ ==============================
y = section_label(y, '10', 'T-cards', 'остальные направления — компактно')
y = h2(y, 'Работаем не только с дизайнерами')
o4 = [('Ресторанам, барам, кофейням', 'Борды, чабани, шотницы, пепельницы комплектами под посадки.'),
      ('Отелям и спа', 'Подносы, борды, подсвечники для номеров, лобби и спа-зон.'),
      ('Корпоративные подарки', 'Тиражи с гравировкой и упаковкой, документы для компании.'),
      ('Магазинам и маркетплейсам', 'Поставки и витрина: фото и описания для карточек.')]
cw4 = (CW - 3 * 20) // 4
for i, (t, tx) in enumerate(o4):
    card(M + i * (cw4 + 20), y, cw4, 176, t, tx)
y += 176 + 80

# ============================== 11. FAQ ==============================
y = section_label(y, '11', 'T-accordion + JSON-LD', 'вопросы дизайнера')
y = h2(y, 'Частые вопросы')
faq = ['Вы работаете по чертежу дизайнера?',
       'Попадёте в конкретный размер?',
       'Дадите материалы для презентации клиенту?',
       'Вы выйдете на моего клиента без меня?',
       'Успеете к сдаче объекта?']
for q in faq:
    d.rounded_rectangle([M, y, M + CW, y + 66], 10, fill=CARD, outline=LINE)
    d.text((M + 28, y + 21), q, font=font(F_M, 19), fill=INK)
    d.text((M + CW - 46, y + 18), '+', font=font(F_B, 26), fill=ACC)
    y += 76
y += 60

# ============================== 12. ФОРМА ==============================
y = section_label(y, '12', 'T-form', 'заявка с загрузкой файла')
y = h2(y, 'Расскажите о проекте')
fields = [('Имя', 0), ('Студия или бюро', 1), ('Телефон или мессенджер', 0), ('Email', 1),
          ('Направление — список', 2), ('Что нужно и сколько', 3),
          ('Размеры и срок сдачи объекта', 2), ('Файл: чертёж, референс, ТЗ', 3)]
fy = y
for label, kind in fields:
    if label == 'Направление — список':
        d.text((M, fy), label, font=font(F_B, 15), fill=MUTED)
        fy += 26
        opts = ['дизайн-проект', 'HoReCa', 'отель, спа', 'подарки', 'магазин', 'другое']
        for j, o in enumerate(opts):
            ox = M + j * 210
            d.rounded_rectangle([ox, fy, ox + 196, fy + 44], 8, fill=CARD if j else ACC, outline=LINE)
            d.text((ox + 16, fy + 13), o, font=font(F_B, 15), fill=INK if j else CARD)
        fy += 44 + 26
        continue
    d.text((M, fy), label, font=font(F_B, 15), fill=MUTED)
    hh = 60 if kind != 3 else 110
    d.rounded_rectangle([M, fy + 24, M + CW, fy + 24 + hh], 8, fill=CARD, outline=LINE)
    fy += 24 + hh + 26
d.text((M, fy + 6), '☐  Согласие на обработку данных со ссылкой на /privacypolicy',
       font=font(F_B, 15), fill=MUTED)
fy += 56
d.rounded_rectangle([M, fy, M + 260, fy + 58], 10, fill=ACC)
d.text((M + 62, fy + 16), 'Отправить заявку', font=font(F_S, 19), fill=CARD)
y = fy + 58 + 80

# ============================== 13. ФИНАЛ ==============================
fh = 380
d.rectangle([0, y, W, y + fh], fill=DARK)
para('Пришлите чертёж — ответим цифрами', font(F_H, 40), CARD, 900, M, y + 70, lh=1.25)
para('Размер, порода, оттенок — и мы скажем стоимость, срок и что технологически возможно. '
     'Без брифа на десять страниц.', font(F_B, 19), (214, 206, 196), 820, M, y + 140, lh=1.5)
d.rounded_rectangle([M, y + 236, M + 250, y + 294], 10, fill=ACC)
d.text((M + 32, y + 252), 'Написать в WhatsApp', font=font(F_S, 18), fill=CARD)
d.text((M + 280, y + 254), '+7 (926) 160-91-10', font=font(F_S, 19), fill=CARD)
d.text((M, y + 330), 'ИП Бабаева Кристина Горхмазовна · ИНН 572501343152 · ОГРНИП 322574900004165',
       font=font(F_B, 14), fill=(150, 142, 132))
y += fh

# ---- обрезка по контенту ----
arr = img.crop((0, 0, W, y))
arr.save(os.path.join(HERE, 'MAKET-stranicy.jpg'), 'JPEG', quality=90, optimize=True)
print('макет:', arr.size)
