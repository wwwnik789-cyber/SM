"""BAK MASTERS — PDF «SEO: что вставить и в какое поле».

Сделан для человека, который не работал с SEO: на каждой странице один экран
типа «страница сайта → поле в Тильде → текст для копирования».

    .venv/bin/python bakmasters/build_seo_guide.py
"""
import os
import sys

from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from reportlab.lib.colors import HexColor, Color, white
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont as RLFont
from reportlab.pdfgen import canvas

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
VAR_FONT = os.path.join(ROOT, "banners/anikom-arena-3000x2500-concepts/source/Montserrat-Variable.ttf")
FONT_DIR = "/tmp/bakmasters-fonts"
OUT = os.path.join(BASE, "pdf/BAK-MASTERS-SEO.pdf")

W, H = A4
MX = 52
TW = W - MX * 2
TOP, BOT = H - 66, 58

INK = HexColor("#1B1714")
SOFT = HexColor("#4E453E")
WOOD = HexColor("#8C5A32")
AMBER = HexColor("#C08A4A")
SAND = HexColor("#F4EEE6")
SAND2 = HexColor("#FAF6F1")
LINE = HexColor("#DCD2C6")
MUTED = HexColor("#8E837A")
DARK = HexColor("#17120E")
BLUE = HexColor("#1B4FA0")   # цвет ссылки в выдаче
GREY_TXT = HexColor("#6B6B6B")

F, FM, FSB, FB = "Montserrat", "Montserrat-Medium", "Montserrat-SemiBold", "Montserrat-Bold"
MONO = "Mono"
SYM = "DejaVu"


def prepare_fonts():
    os.makedirs(FONT_DIR, exist_ok=True)
    for name, wght in [(F, 400), (FM, 500), (FSB, 600), (FB, 700)]:
        out = os.path.join(FONT_DIR, f"{name}.ttf")
        if not os.path.exists(out):
            f = TTFont(VAR_FONT)
            axes = {"wght": wght}
            if "ital" in [a.axisTag for a in f["fvar"].axes]:
                axes["ital"] = 0
            instantiateVariableFont(f, axes, updateFontNames=True).save(out)
        pdfmetrics.registerFont(RLFont(name, out))
    pdfmetrics.registerFont(RLFont(MONO, "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"))
    pdfmetrics.registerFont(RLFont(SYM, "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
    pdfmetrics.registerFontFamily(F, normal=F, bold=FB, italic=F, boldItalic=FB)


# ------------------------------------------------------------------ утилиты
def sw(text, font, size):
    return pdfmetrics.stringWidth(text, font, size)


def wrap(text, font, size, maxw):
    lines, cur = [], ""
    for word in text.split():
        t = f"{cur} {word}".strip()
        if sw(t, font, size) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def text_block(c, x, y, text, font, size, leading, color, maxw=None, gap=0):
    """Рисует абзац сверху вниз, возвращает y под ним."""
    maxw = maxw or (TW - (x - MX))
    for i, line in enumerate(wrap(text, font, size, maxw)):
        c.setFont(font, size)
        c.setFillColor(color)
        c.drawString(x, y - i * leading, line)
    n = len(wrap(text, font, size, maxw))
    return y - (n - 1) * leading - gap


def rule(c, y, color=LINE, w=0.7, x1=MX, x2=W - MX):
    c.setStrokeColor(color)
    c.setLineWidth(w)
    c.line(x1, y, x2, y)


def page_no(c, n, title="SEO: что вставить и в какое поле"):
    c.setFont(FSB, 7.2)
    c.setFillColor(MUTED)
    c.drawString(MX, H - 38, "BAK MASTERS")
    c.setFont(F, 7.2)
    c.drawRightString(W - MX, H - 38, title)
    rule(c, H - 45)
    rule(c, BOT - 14)
    c.setFont(F, 7.2)
    c.setFillColor(MUTED)
    c.drawString(MX, BOT - 26, "bakmasters.ru · подготовлено SM Production")
    c.setFont(FSB, 8.4)
    c.setFillColor(WOOD)
    c.drawRightString(W - MX, BOT - 26, str(n))


# ------------------------------------------------------------------ данные
SITE = dict(
    title="BAK MASTERS — изделия из дерева и эпоксидной смолы ручной работы",
    desc="Мастерская в Москве: столы, чабани, кухонные доски, подсвечники и подарки "
         "из массива дерева с эпоксидной смолой. Ручная работа, доставка по России.",
)

PAGES = [
    dict(n=1, name="Главная", url="bakmasters.ru",
         title="Столы и декор из массива дерева и эпоксидной смолы — BAK MASTERS",
         desc="Авторские столы, чабани, доски, подсвечники и подарки из натурального дерева "
              "с эпоксидной смолой. Ручная работа, доставка по России, изготовление на заказ.",
         h1="BAK MASTERS — мебель и предметы интерьера из дерева",
         note="На главной сейчас нет заголовка H1 вообще: первый экран начинается с текста "
              "«Добро пожаловать в интернет-магазин…». Выделите нужную строку и назначьте ей стиль H1."),
    dict(n=2, name="Каталог", url="bakmasters.ru/shop",
         title="Каталог: столы, чабани, доски и подсвечники — BAK MASTERS",
         desc="Все изделия BAK MASTERS: столики, чабани, кухонные борды, подсвечники, шотницы "
              "и подарочные наборы. Цены, размеры и наличие — в карточках товаров.",
         h1="Изделия из дерева и эпоксидной смолы",
         note="Сейчас в Title этой страницы стоит одно слово — «Каталог»."),
    dict(n=3, name="На заказ", url="bakmasters.ru/toorder",
         title="Изготовление мебели и декора на заказ — BAK MASTERS",
         desc="Сделаем стол, чабань, борд или подсвечник по вашим размерам: подберём спил, "
              "согласуем эскиз, изготовим за 10–20 дней. Пришлите референс — рассчитаем.",
         h1="Изделия на заказ по вашим размерам",
         note=""),
    dict(n=4, name="О нас", url="bakmasters.ru/aboutus",
         title="О мастерской BAK MASTERS: дерево, смола, ручная работа",
         desc="Мастерская в Москве. Отбираем спилы ценных пород, заливаем эпоксидной смолой, "
              "шлифуем и пропитываем маслом — каждое изделие делаем вручную.",
         h1="Мастерская BAK MASTERS",
         note=""),
    dict(n=5, name="Доставка и оплата", url="bakmasters.ru/delivery_and_payment",
         title="Доставка по России и оплата заказа — BAK MASTERS",
         desc="Бесплатно до ПВЗ СДЭК по России для заказов до 25 кг и 0,1 м³. Курьер по Москве "
              "день в день, международная доставка, оплата после согласования заказа.",
         h1="Доставка и оплата",
         note="Страница новая — поля SEO у неё, скорее всего, пустые."),
    dict(n=6, name="Контакты", url="bakmasters.ru/contacts",
         title="Контакты и реквизиты — BAK MASTERS, Москва",
         desc="Телефон, почта, Telegram, VK и WhatsApp BAK MASTERS. ИП Бабаева Кристина "
              "Горхмазовна, ИНН 572501343152. Отвечаем в течение рабочего дня.",
         h1="Контакты",
         note=""),
    dict(n=7, name="Политика конфиденциальности", url="bakmasters.ru/privacypolicy",
         title="Политика конфиденциальности — BAK MASTERS",
         desc="Как BAK MASTERS обрабатывает персональные данные покупателей: какие данные "
              "собираем, зачем они нужны и как их удалить.",
         h1="Политика конфиденциальности",
         note=""),
    dict(n=8, name="Сотрудничество", url="bakmasters.ru/cooperation",
         title="Сотрудничество — BAK MASTERS: дизайнеры и HoReCa",
         desc="Делаем изделия под проект для дизайнеров интерьера, шоурумов, отелей и "
              "ресторанов: подбор спилов, образцы, серии. Пришлите запрос — рассчитаем.",
         h1="Сотрудничество",
         note="Страница ещё не опубликована. Заполните SEO до публикации — тогда она сразу "
              "попадёт в поиск с нормальным заголовком. Адрес /cooperation задаётся в "
              "настройках страницы: он лучше длинного page27….html — короче и понятнее.",
         url_note="/cooperation предложен — в Тильде адрес может быть другим. Поставьте такой же."),
    dict(n=9, name="Магазин", url="bakmasters.ru/f",
         title="Магазин BAK MASTERS — изделия из дерева ручной работы",
         desc="Каталог с ценами: столики и чабани, кухонные борды, подсвечники, шотницы, "
              "подставки для благовоний и подарочные наборы из дерева и эпоксидной смолы.",
         h1="Магазин",
         note="Это корень каталога Тильды. На него ведёт ссылка «О продукте» из каждой карточки."),
]

PRODUCTS = [
    ("ТИВДИЯ", "Подсвечник ТИВДИЯ из массива ореха — BAK MASTERS"),
    ("АМАЗОНИТА", "Подсвечник АМАЗОНИТА из шелковицы — BAK MASTERS"),
    ("КУХТИНАБАТА", "Шотница КУХТИНАБАТА с подсветкой — BAK MASTERS"),
    ("ПУТОРАНО НУАР", "Борд ПУТОРАНО НУАР, доска для подачи — BAK MASTERS"),
    ("МАЙГОТО абрикос", "Придвижной столик МАЙГОТО из абрикоса — BAK MASTERS"),
    ("САНТАЛА", "Подставка для благовоний САНТАЛА — BAK MASTERS"),
    ("САНТАЛА ДУБ", "Подставка для благовоний САНТАЛА из дуба — BAK MASTERS"),
    ("Журнальные столики", "Журнальный столик из массива дерева — BAK MASTERS"),
]

ALTS = [
    ("Главная", "первый экран",
     "стол из массива дерева с заливкой эпоксидной смолой в интерьере"),
    ("Главная", "Борды кухонные",
     "кухонная борда из массива дерева с эпоксидной смолой, ручная работа"),
    ("Главная", "Чайные столики ЧАБАНЬ",
     "чайный столик чабань из массива дерева для чайной церемонии"),
    ("Главная", "Приставной столик МАЙГОТО",
     "придвижной столик из спила абрикоса с эпоксидной смолой"),
    ("Главная", "Подсвечники",
     "подсвечник из массива дерева и эпоксидной смолы со свечой"),
    ("Главная", "Шотница в галерее",
     "шотница из дерева с подсветкой отверстий люминофором"),
    ("Главная", "Подставка для благовоний",
     "подставка для благовоний из дерева с крышкой"),
    ("Главная", "Подстаканники",
     "подстаканник из массива дерева с эпоксидной смолой"),
    ("Главная", "Доска для подачи",
     "доска для подачи из ореха с заливкой эпоксидной смолой"),
    ("Главная", "Набор изделий",
     "подарочный набор изделий из дерева и эпоксидной смолы"),
    ("Главная", "Интерьерный кадр",
     "журнальный столик из спила дерева в интерьере гостиной"),
    ("Каталог /shop", "баннер каталога",
     "изделия из дерева и эпоксидной смолы ручной работы"),
    ("О нас", "процесс в мастерской",
     "шлифовка столешницы из спила дерева в мастерской"),
    ("О нас", "заливка смолы",
     "заливка эпоксидной смолы в форму со спилом дерева"),
    ("О нас", "готовые изделия",
     "готовые изделия из дерева и смолы на полке в мастерской"),
    ("Доставка", "упаковка",
     "изделие из дерева в подарочной упаковке, подготовлено к отправке"),
    ("Доставка", "коробки",
     "посылки BAK MASTERS перед отправкой СДЭК"),
    ("Сотрудничество", "серия изделий",
     "серия подсвечников из дерева для проекта отеля"),
    ("Сотрудничество", "образцы",
     "образцы спилов и оттенков смолы для согласования с дизайнером"),
]

CHECKLIST = [
    ("Ссылки .su заменить на /shop, /toorder, /aboutus, /privacypolicy", "20 мин", True),
    ("VK и Telegram в шапке: vk.com/bak_mast и t.me/bak_masters", "10 мин", True),
    ("Один телефон и один Telegram на всех страницах", "20 мин", True),
    ("Настройки сайта: Title, Description, картинка для соцсетей", "15 мин", False),
    ("Страница «Главная» — Title, Description, H1", "5 мин", False),
    ("Страница «Каталог» — Title, Description, H1", "5 мин", False),
    ("Страница «На заказ» — Title, Description, H1", "5 мин", False),
    ("Страница «О нас» — Title, Description, H1", "5 мин", False),
    ("Страница «Доставка и оплата» — Title, Description, H1", "5 мин", False),
    ("Страница «Контакты» — Title, Description, H1", "5 мин", False),
    ("Страница «Политика» — Title, Description, H1", "5 мин", False),
    ("Страница «Сотрудничество» — Title, Description, H1", "5 мин", False),
    ("Страница «Магазин» — Title, Description, H1", "5 мин", False),
    ("Альты на главной", "20 мин", False),
    ("Альты в карточках товаров", "40 мин", False),
    ("Title и Description у 37 товаров", "1 час", False),
    ("Старые страницы page…html закрыть от индексации", "15 мин", False),
    ("Яндекс.Вебмастер: «Переезд сайта» с .su", "20 мин", False),
    ("Google Search Console: «Изменение адреса»", "20 мин", False),
]


# ------------------------------------------------------------------ элементы
def field_block(c, y, num, name, where, text, limit, kind="seo"):
    """Поле Тильды: номер, название, путь, лимит и текст для копирования."""
    x = MX
    top = y

    # бейдж
    c.setFillColor(WOOD if kind == "seo" else AMBER)
    c.roundRect(x, top - 15, 19, 19, 4, stroke=0, fill=1)
    c.setFillColor(white)
    c.setFont(FB, 10.5)
    c.drawCentredString(x + 9.5, top - 9.7, str(num))

    # название поля
    c.setFillColor(INK)
    c.setFont(FSB, 13.5)
    c.drawString(x + 28, top - 11, name)
    name_w = sw(name, FSB, 13.5)

    # лимит справа
    c.setFillColor(MUTED)
    c.setFont(F, 8.4)
    c.drawRightString(W - MX, top - 10, limit)

    # путь
    c.setFillColor(SOFT)
    c.setFont(FM, 9.2)
    c.drawString(x + 28, top - 27, where)

    # рамка с текстом
    inner = TW - 24
    lines = wrap(text, FM, 12, inner)
    lh = 18.5
    bh = len(lines) * lh + 20
    by = top - 40
    c.setFillColor(SAND2)
    c.setStrokeColor(LINE if kind == "seo" else AMBER)
    c.setLineWidth(0.8)
    c.roundRect(x, by - bh, TW, bh, 5, stroke=1, fill=1)
    c.setFillColor(AMBER if kind == "seo" else WOOD)
    c.rect(x, by - bh, 2.6, bh, stroke=0, fill=1)
    c.setFillColor(INK)
    ty = by - 20
    for line in lines:
        c.setFont(FM, 12)
        c.drawString(x + 13, ty, line)
        ty -= lh
    return by - bh - 24


def tag(c, x, y, text, color=AMBER, txt=white):
    w = sw(text, FSB, 7.6) + 14
    c.setFillColor(color)
    c.roundRect(x, y, w, 14, 2, stroke=0, fill=1)
    c.setFillColor(txt)
    c.setFont(FSB, 7.6)
    c.drawCentredString(x + w / 2, y + 4.3, text)
    return w


# ------------------------------------------------------------------ страницы
def cover(c):
    c.setFillColor(DARK)
    c.rect(0, 0, W, H, stroke=0, fill=1)
    c.setStrokeColor(HexColor("#3B2D22"))
    c.setLineWidth(0.7)
    c.rect(26, 26, W - 52, H - 52, stroke=1, fill=0)

    c.setFillColor(AMBER)
    c.setFont(FB, 11)
    c.drawString(MX, H - 118, "BAK MASTERS")
    c.setFillColor(HexColor("#6E5C4C"))
    c.setFont(F, 8.4)
    c.drawString(MX + 92, H - 118, "изделия из дерева и эпоксидной смолы")

    c.setFillColor(HexColor("#F7F2EB"))
    c.setFont(FB, 40)
    c.drawString(MX, H - 205, "Куда вставить")
    c.drawString(MX, H - 250, "этот текст")
    c.setFillColor(AMBER)
    c.setFont(FSB, 17)
    c.drawString(MX, H - 292, "пошагово для Тильды")

    c.setStrokeColor(AMBER)
    c.setLineWidth(2.4)
    c.line(MX, H - 330, MX + 74, H - 330)

    c.setFillColor(HexColor("#C3B3A2"))
    c.setFont(FM, 11.2)
    c.drawString(MX, H - 366, "Одна страница сайта — один экран.")
    c.drawString(MX, H - 385, "Три поля. Текст для копирования уже готов.")

    items = [
        ("1", "Что такое Title и Description", "1 стр."),
        ("2", "Где эти поля в Тильде", "1 стр."),
        ("3", "Настройки всего сайта", "1 стр."),
        ("4", "Девять страниц — по полям", "9 стр."),
        ("5", "Товары в магазине", "2 стр."),
        ("6", "Альты для картинок", "2 стр."),
        ("7", "Чек-лист", "1 стр."),
    ]
    y = H - 440
    c.setFillColor(HexColor("#6E5C4C"))
    c.setFont(FSB, 8.2)
    c.drawString(MX, y, "СОДЕРЖАНИЕ")
    y -= 26
    for num, name, pages in items:
        c.setFillColor(AMBER)
        c.setFont(FB, 9.6)
        c.drawString(MX, y, num)
        c.setFillColor(HexColor("#E8DED2"))
        c.setFont(FM, 10.8)
        c.drawString(MX + 26, y, name)
        c.setFillColor(HexColor("#6E5C4C"))
        c.setFont(F, 9.6)
        c.drawRightString(W - MX, y, pages)
        y -= 27

    c.setFillColor(HexColor("#8A7A6A"))
    c.setFont(F, 8.6)
    c.drawString(MX, 96, "Собрано 30 октября 2026")
    c.drawString(MX, 82, "Документ подготовлен SM Production")
    c.setFillColor(AMBER)
    c.setFont(FB, 8.6)
    c.drawRightString(W - MX, 96, "bakmasters.ru")


def page_intro(c, n):
    """Что такое Title и Description — на макете выдачи."""
    page_no(c, n)
    y = H - 96
    c.setFillColor(WOOD)
    c.setFont(FB, 22)
    c.drawString(MX, y, "Что такое Title и Description")
    y -= 16
    rule(c, y, AMBER, 1.2)
    y -= 26

    y = text_block(c, MX, y, "Поисковик показывает страницу в результатах поиска "
                             "двумя строчками:", F, 10.6, 15.5, SOFT, TW, gap=20)

    # ---- макет выдачи ----
    bx, bw = MX, TW
    bh = 150
    c.setFillColor(white)
    c.setStrokeColor(LINE)
    c.setLineWidth(0.9)
    c.roundRect(bx, y - bh, bw, bh, 6, stroke=1, fill=1)

    ix = bx + 20
    ty = y - 30
    c.setFillColor(HexColor("#1A7F37"))
    c.setFont(F, 8.4)
    c.drawString(ix, ty, "bakmasters.ru")
    c.setFillColor(GREY_TXT)
    c.drawString(ix + sw("bakmasters.ru", F, 8.4) + 8, ty, "› shop")

    ty -= 22
    c.setFillColor(BLUE)
    c.setFont(FM, 12.4)
    c.drawString(ix, ty, "Каталог: столы, чабани, доски и подсвечники — BAK MASTERS")
    # подчёркивание ссылки
    c.setStrokeColor(BLUE)
    c.setLineWidth(0.6)
    c.line(ix, ty - 3,
           ix + sw("Каталог: столы, чабани, доски и подсвечники — BAK MASTERS", FM, 12.4), ty - 3)

    ty -= 20
    c.setFillColor(GREY_TXT)
    c.setFont(F, 9.4)
    for line in wrap(PAGES[1]["desc"], F, 9.4, bw - 40)[:2]:
        c.drawString(ix, ty, line)
        ty -= 13

    # стрелки-подписи
    lab_y = y - 44
    c.setStrokeColor(AMBER)
    c.setLineWidth(1)
    c.line(W - MX - 4, lab_y + 4, W - MX + 0, lab_y + 4)

    # выноски справа от блока
    nx = W - MX + 6
    c.setFillColor(WOOD)
    c.setFont(FSB, 8)
    c.drawString(bx + 20, y - bh - 16, "↑ синяя строка — это Title (заголовок)")

    y -= bh + 34

    c.setFillColor(INK)
    c.setFont(FSB, 11.5)
    c.drawString(MX, y, "На человеческом языке:")
    y -= 22

    pairs = [
        ("Title (заголовок)", "то, что человек читает первым в поиске. Синяя строка. "
                              "От неё зависит, кликнут или пройдут мимо."),
        ("Description (описание)", "серый текст под заголовком. Здесь пишут, что внутри: "
                                   "цены, доставка, сроки."),
        ("H1", "самый крупный заголовок уже на самой странице сайта. "
               "Не в настройках — в самом тексте страницы."),
    ]
    for name, txt in pairs:
        c.setFillColor(WOOD)
        c.setFont(FSB, 10.2)
        c.drawString(MX, y, name)
        y -= 15
        y = text_block(c, MX + 12, y, txt, F, 9.8, 14, SOFT, TW - 12, gap=14)

    y -= 4
    c.setFillColor(SAND)
    c.roundRect(MX, y - 52, TW, 52, 5, stroke=0, fill=1)
    c.setFillColor(WOOD)
    c.rect(MX, y - 52, 2.6, 52, stroke=0, fill=1)
    c.setFillColor(INK)
    c.setFont(FSB, 9.6)
    c.drawString(MX + 14, y - 20, "Главное правило")
    c.setFont(F, 9.6)
    c.setFillColor(SOFT)
    c.drawString(MX + 14, y - 35, "Один заголовок — в одно поле. Не надо вписывать одно и то же")
    c.drawString(MX + 14, y - 47, "в Title, Description и H1. Поисковик считает это накруткой.")


def page_where(c, n):
    """Где поля в Тильде — схема панели."""
    page_no(c, n)
    y = H - 96
    c.setFillColor(WOOD)
    c.setFont(FB, 22)
    c.drawString(MX, y, "Где эти поля в Тильде")
    y -= 16
    rule(c, y, AMBER, 1.2)
    y -= 26

    y = text_block(c, MX, y, "Откройте нужную страницу в редакторе. В правом верхнем углу — "
                             "кнопка «Настройки страницы». В открывшейся панели переключитесь "
                             "на вкладку «SEO».", F, 10.6, 15.5, SOFT, TW, gap=22)

    # ---- схема панели ----
    pw = TW - 60
    px = MX + 10
    ph = 300
    c.setFillColor(HexColor("#EFEFEF"))
    c.setStrokeColor(HexColor("#CFCFCF"))
    c.roundRect(px, y - ph, pw, ph, 6, stroke=1, fill=1)

    # шапка панели
    c.setFillColor(white)
    c.roundRect(px, y - 34, pw, 34, 6, stroke=0, fill=1)
    c.setFillColor(INK)
    c.setFont(FSB, 9.6)
    c.drawString(px + 14, y - 22, "Настройки страницы")

    # вкладки
    tabs = ["Основное", "SEO", "Дополнительно"]
    tx = px + 14
    ty = y - 52
    for t in tabs:
        tw_ = sw(t, FSB if t == "SEO" else F, 8.8) + 20
        if t == "SEO":
            c.setFillColor(WOOD)
            c.roundRect(tx, ty - 5, tw_, 20, 3, stroke=0, fill=1)
            c.setFillColor(white)
        else:
            c.setFillColor(HexColor("#E4E4E4"))
            c.roundRect(tx, ty - 5, tw_, 20, 3, stroke=0, fill=1)
            c.setFillColor(SOFT)
        c.setFont(FSB if t == "SEO" else F, 8.8)
        c.drawString(tx + 10, ty + 1, t)
        tx += tw_ + 6

    # поле 1
    fy = y - 84
    c.setFillColor(SOFT)
    c.setFont(FM, 8.2)
    c.drawString(px + 14, fy, "Заголовок страницы (Title)")
    c.setFillColor(white)
    c.setStrokeColor(LINE)
    c.roundRect(px + 14, fy - 26, pw - 28, 22, 3, stroke=1, fill=1)
    c.setFillColor(MUTED)
    c.setFont(MONO, 7.2)
    c.drawString(px + 19, fy - 20, "Столы и декор из массива дерева…")

    # поле 2
    fy -= 52
    c.setFillColor(SOFT)
    c.setFont(FM, 8.2)
    c.drawString(px + 14, fy, "Описание страницы (Description)")
    c.setFillColor(white)
    c.roundRect(px + 14, fy - 54, pw - 28, 50, 3, stroke=1, fill=1)
    c.setFillColor(MUTED)
    c.setFont(MONO, 7.2)
    c.drawString(px + 19, fy - 18, "Авторские столы, чабани, доски,")
    c.drawString(px + 19, fy - 30, "подсвечники и подарки…")

    # чекбокс
    fy -= 76
    c.setFillColor(white)
    c.setStrokeColor(HexColor("#BFBFBF"))
    c.rect(px + 14, fy, 10, 10, stroke=1, fill=1)
    c.setFillColor(SOFT)
    c.setFont(F, 8.2)
    c.drawString(px + 30, fy + 1, "Не индексировать страницу")

    # маркеры «поле 1» / «поле 2»
    ax = px + pw + 8
    c.setFillColor(AMBER)
    c.setFont(FSB, 8.2)
    c.drawString(ax, y - 82, "ПОЛЕ 1")
    c.setFont(F, 7.6)
    c.setFillColor(SOFT)
    c.drawString(ax, y - 93, "сюда Title")

    c.setFillColor(AMBER)
    c.setFont(FSB, 8.2)
    c.drawString(ax, y - 134, "ПОЛЕ 2")
    c.setFont(F, 7.6)
    c.setFillColor(SOFT)
    c.drawString(ax, y - 145, "сюда")
    c.drawString(ax, y - 155, "Description")

    y -= ph + 30

    c.setFillColor(INK)
    c.setFont(FSB, 11.5)
    c.drawString(MX, y, "Три правила, чтобы не запутаться")
    y -= 22
    rules = [
        ("Одно поле — один текст.", "Не надо дублировать Title в Description."),
        ("Описание — до 160 знаков.", "Длиннее обрежется многоточием."),
        ("Галочку «Не индексировать» не ставить.", "Иначе страница выпадет из поиска."),
    ]
    for i, (b, t) in enumerate(rules, 1):
        c.setFillColor(AMBER)
        c.setFont(FB, 9.4)
        c.drawString(MX, y, f"{i}")
        c.setFillColor(INK)
        c.setFont(FSB, 9.8)
        c.drawString(MX + 14, y, b)
        c.setFillColor(SOFT)
        c.setFont(F, 9.8)
        c.drawString(MX + 14 + sw(b, FSB, 9.8) + 4, y, t)
        y -= 20


def page_site(c, n):
    """Настройки сайта."""
    page_no(c, n)
    y = H - 96
    c.setFillColor(WOOD)
    c.setFont(FB, 22)
    c.drawString(MX, y, "Сначала — настройки сайта")
    y -= 16
    rule(c, y, AMBER, 1.2)
    y -= 24

    y = text_block(c, MX, y, "Это делается один раз и действует на все страницы. "
                             "Настройки сайта → «Ещё» → «SEO».", F, 10.6, 15.5, SOFT, TW, gap=8)
    y = text_block(c, MX, y, "Значения отсюда поисковик берёт для страниц, у которых своих "
                             "настроек нет. Поэтому они общие, без конкретики.",
                   F, 9.6, 14, MUTED, TW, gap=24)

    y = field_block(c, y, 1, "Заголовок сайта (Title)",
                    "Настройки сайта → Ещё → SEO → первое поле",
                    SITE["title"], f"{len(SITE['title'])} знаков · лимит 65")
    y = field_block(c, y, 2, "Описание сайта (Description)",
                    "Настройки сайта → Ещё → SEO → второе поле",
                    SITE["desc"], f"{len(SITE['desc'])} знаков · лимит 160")

    # картинка для соцсетей — отдельный блок
    c.setFillColor(WOOD)
    c.roundRect(MX, y - 15, 19, 19, 4, stroke=0, fill=1)
    c.setFillColor(white)
    c.setFont(FB, 10.5)
    c.drawCentredString(MX + 9.5, y - 9.7, "3")
    c.setFillColor(INK)
    c.setFont(FSB, 13.5)
    c.drawString(MX + 28, y - 11, "Картинка для соцсетей")
    c.setFillColor(MUTED)
    c.setFont(F, 8.4)
    c.drawRightString(W - MX, y - 10, "1200 × 630 пикселей")
    c.setFillColor(SOFT)
    c.setFont(FM, 9.2)
    c.drawString(MX + 28, y - 27, "Настройки сайта → Ещё → SEO → «Изображение для соцсетей»")

    y -= 44
    c.setFillColor(SAND2)
    c.setStrokeColor(LINE)
    c.setLineWidth(0.8)
    c.roundRect(MX, y - 66, TW, 66, 5, stroke=1, fill=1)
    c.setFillColor(SOFT)
    c.setFont(F, 10.2)
    c.drawString(MX + 14, y - 22, "Нужна любая горизонтальная фотография изделия — та, что вам")
    c.drawString(MX + 14, y - 37, "нравится. Без неё при отправке ссылки в Telegram и VK вместо")
    c.drawString(MX + 14, y - 52, "превью показывается серая плашка.")
    y -= 90

    c.setFillColor(INK)
    c.setFont(FSB, 11.5)
    c.drawString(MX, y, "Зачем это нужно")
    y -= 20
    y = text_block(c, MX, y, "Ваш основной трафик идёт из соцсетей и мессенджеров. Когда человек "
                             "кидает ссылку на сайт в чат, Тильда подставляет эту картинку как "
                             "превью. Пустое поле — серая заглушка и меньше переходов.",
                   F, 9.8, 14, SOFT, TW)



def snippet_preview(c, y, url, title, desc):
    """Как страница будет выглядеть в результатах поиска."""
    if y - 108 < BOT + 8:
        return y
    c.setFillColor(MUTED)
    c.setFont(FSB, 7.6)
    c.drawString(MX, y, "ТАК ЭТО БУДЕТ ВЫГЛЯДЕТЬ В ПОИСКЕ")
    y -= 20

    bh = 96
    c.setFillColor(white)
    c.setStrokeColor(LINE)
    c.setLineWidth(0.8)
    c.roundRect(MX, y - bh, TW, bh, 5, stroke=1, fill=1)

    ix = MX + 16
    ty = y - 20
    c.setFillColor(HexColor("#1A7F37"))
    c.setFont(F, 8)
    c.drawString(ix, ty, "bakmasters.ru")
    c.setFillColor(GREY_TXT)
    path = url.replace("bakmasters.ru", "")
    if path:
        c.drawString(ix + sw("bakmasters.ru", F, 8) + 6, ty, "› " + path.strip("/"))

    ty -= 18
    c.setFillColor(BLUE)
    c.setFont(FM, 10.4)
    tl = wrap(title, FM, 10.4, TW - 32)[:2]
    for line in tl:
        c.drawString(ix, ty, line)
        ty -= 13
    c.setStrokeColor(BLUE)
    c.setLineWidth(0.5)
    c.line(ix, ty + 10.5, ix + sw(tl[0], FM, 10.4), ty + 10.5)

    ty -= 2
    c.setFillColor(GREY_TXT)
    c.setFont(F, 8.4)
    for line in wrap(desc, F, 8.4, TW - 32)[:2]:
        c.drawString(ix, ty, line)
        ty -= 11
    return y - bh - 16


def page_card(c, n, pg, total=9):
    page_no(c, n)
    y = H - 92

    c.setFillColor(AMBER)
    c.setFont(FSB, 8)
    c.drawString(MX, y, f"СТРАНИЦА {pg['n']} ИЗ {total}")
    y -= 30

    c.setFillColor(INK)
    c.setFont(FB, 27)
    name = pg["name"]
    if sw(name, FB, 27) > TW - 10:
        c.setFont(FB, 22)
    c.drawString(MX, y, name)
    y -= 20

    c.setFillColor(MUTED)
    c.setFont(MONO, 9)
    c.drawString(MX, y, pg["url"])
    y -= 12
    rule(c, y)
    y -= 30

    y = field_block(c, y, 1, "Заголовок страницы (Title)",
                    "Настройки страницы → SEO → первое поле",
                    pg["title"], f"{len(pg['title'])} знаков · лимит 65")
    y = field_block(c, y, 2, "Описание страницы (Description)",
                    "Настройки страницы → SEO → второе поле",
                    pg["desc"], f"{len(pg['desc'])} знаков · лимит 160")

    # H1 — не поле настроек
    c.setFillColor(AMBER)
    c.roundRect(MX, y - 15, 19, 19, 4, stroke=0, fill=1)
    c.setFillColor(white)
    c.setFont(FB, 10.5)
    c.drawCentredString(MX + 9.5, y - 9.7, "3")
    c.setFillColor(INK)
    c.setFont(FSB, 13.5)
    c.drawString(MX + 28, y - 11, "Заголовок H1")
    tw_ = tag(c, W - MX - sw("НЕ В НАСТРОЙКАХ", FSB, 7.6) - 14, y - 12, "НЕ В НАСТРОЙКАХ")
    c.setFillColor(SOFT)
    c.setFont(FM, 9.2)
    c.drawString(MX + 28, y - 27, "На самой странице: выделить текст → стиль H1")

    inner = TW - 24
    lines = wrap(pg["h1"], FM, 12, inner)
    lh = 18.5
    bh = len(lines) * lh + 20
    by = y - 40
    c.setFillColor(SAND)
    c.setStrokeColor(AMBER)
    c.setLineWidth(0.8)
    c.roundRect(MX, by - bh, TW, bh, 5, stroke=1, fill=1)
    c.setFillColor(INK)
    ty = by - 20
    for line in lines:
        c.setFont(FM, 12)
        c.drawString(MX + 13, ty, line)
        ty -= lh
    y = by - bh - 24

    if pg.get("note"):
        lines = wrap(pg["note"], F, 9.4, TW - 26)
        bh = len(lines) * 13.5 + 26
        c.setFillColor(HexColor("#FBF7F2"))
        c.setStrokeColor(LINE)
        c.setLineWidth(0.7)
        c.roundRect(MX, y - bh, TW, bh, 5, stroke=1, fill=1)
        c.setFillColor(AMBER)
        c.setFont(FSB, 8)
        c.drawString(MX + 14, y - 15, "ОБРАТИТЕ ВНИМАНИЕ")
        ty = y - 30
        c.setFillColor(SOFT)
        for line in lines:
            c.setFont(F, 9.4)
            c.drawString(MX + 14, ty, line)
            ty -= 13.5
        y -= bh + 22

    y = snippet_preview(c, y + 8, pg["url"], pg["title"], pg["desc"])

    # напоминание внизу
    if y - 6 > BOT + 6:
        c.setFillColor(MUTED)
        c.setFont(F, 8.4)
        c.drawString(MX, max(y, BOT + 16),
                     "Галочка «Не индексировать страницу» снята. После заполнения — "
                     "«Сохранить» и «Опубликовать».")


def page_products_1(c, n):
    page_no(c, n)
    y = H - 96
    c.setFillColor(WOOD)
    c.setFont(FB, 22)
    c.drawString(MX, y, "Товары в магазине")
    y -= 16
    rule(c, y, AMBER, 1.2)
    y -= 24

    y = text_block(c, MX, y, "В магазине 37 карточек. У каждой — те же два поля, только "
                             "лежат они внутри карточки товара.", F, 10.6, 15.5, SOFT, TW, gap=6)
    y = text_block(c, MX, y, "Магазин → открыть товар → раздел «SEO» (в некоторых версиях "
                             "он называется «Дополнительно»).", F, 9.8, 14, MUTED, TW, gap=22)

    c.setFillColor(INK)
    c.setFont(FSB, 11.5)
    c.drawString(MX, y, "Формула заголовка")
    y -= 24

    # формула
    c.setFillColor(SAND)
    c.roundRect(MX, y - 46, TW, 46, 5, stroke=0, fill=1)
    c.setFillColor(AMBER)
    c.rect(MX, y - 46, 2.6, 46, stroke=0, fill=1)
    c.setFillColor(INK)
    c.setFont(FM, 11.6)
    c.drawString(MX + 14, y - 20, "{Тип изделия}  {НАЗВАНИЕ}  из {порода}  —  BAK MASTERS")
    c.setFillColor(SOFT)
    c.setFont(F, 9)
    c.drawString(MX + 14, y - 36, "Тип — всегда первым: именно его ищут люди.")
    y -= 66

    c.setFillColor(INK)
    c.setFont(FSB, 11.5)
    c.drawString(MX, y, "Пример")
    y -= 20

    c.setFillColor(SOFT)
    c.setFont(F, 9.8)
    c.drawString(MX, y, "Было:")
    c.setFillColor(HexColor("#B03A2E"))
    c.setFont(FM, 10.4)
    c.drawString(MX + 40, y, "BAK MASTERS Подсвечник")
    y -= 18
    c.setFillColor(SOFT)
    c.setFont(F, 9.8)
    c.drawString(MX, y, "Стало:")
    c.setFillColor(HexColor("#1A7F37"))
    c.setFont(FM, 10.4)
    c.drawString(MX + 48, y, "Подсвечник ТИВДИЯ из массива ореха — BAK MASTERS")
    y -= 30

    c.setFillColor(INK)
    c.setFont(FSB, 11.5)
    c.drawString(MX, y, "Почему так")
    y -= 20
    y = text_block(c, MX, y, "Сейчас у нескольких подсвечников заголовок одинаковый — "
                             "«BAK MASTERS Подсвечник». Поисковик считает такие страницы "
                             "дублями и оставляет в поиске одну вместо пяти. Разные "
                             "заголовки — разные страницы в поиске.",
                   F, 9.8, 14.5, SOFT, TW, gap=20)

    c.setFillColor(INK)
    c.setFont(FSB, 11.5)
    c.drawString(MX, y, "Описание для товара")
    y -= 20
    c.setFillColor(SAND)
    c.roundRect(MX, y - 46, TW, 46, 5, stroke=0, fill=1)
    c.setFillColor(AMBER)
    c.rect(MX, y - 46, 2.6, 46, stroke=0, fill=1)
    c.setFillColor(INK)
    c.setFont(FM, 10.4)
    c.drawString(MX + 14, y - 19, "{Что это и из чего}. Размер {Д × Ш × В} мм.")
    c.drawString(MX + 14, y - 34, "{Для чего или кому дарят}. Ручная работа, доставка по России.")
    y -= 66

    c.setFillColor(SOFT)
    c.setFont(F, 9.8)
    c.drawString(MX, y, "Пример для подсвечника ТИВДИЯ:")
    y -= 17
    y = text_block(c, MX + 10, y, "Подсвечник из массива ореха с молочно-бежевой заливкой. "
                                  "Размер 185 × 75 × 15 мм. В комплекте свечи и подарочная "
                                  "упаковка. Ручная работа, доставка по России.",
                   F, 9.8, 14, INK, TW - 10)


def page_products_2(c, n):
    page_no(c, n)
    y = H - 96
    c.setFillColor(WOOD)
    c.setFont(FB, 22)
    c.drawString(MX, y, "Товары: готовые заголовки")
    y -= 16
    rule(c, y, AMBER, 1.2)
    y -= 22

    y = text_block(c, MX, y, "Эти восемь можно вставить как есть. Остальные — по формуле "
                             "на предыдущей странице.", F, 10.2, 15, SOFT, TW, gap=18)

    # таблица
    col1 = TW * 0.30
    col2 = TW * 0.70
    rows = PRODUCTS

    # шапка
    c.setFillColor(WOOD)
    c.rect(MX, y - 20, TW, 20, stroke=0, fill=1)
    c.setFillColor(white)
    c.setFont(FSB, 8.4)
    c.drawString(MX + 8, y - 14, "ТОВАР")
    c.drawString(MX + col1 + 8, y - 14, "ЗАГОЛОВОК ДЛЯ ПОЛЯ TITLE")
    y -= 20

    for i, (name, ttl) in enumerate(rows):
        lines = wrap(ttl, FM, 8.6, col2 - 16)
        rh = max(len(lines) * 11.5 + 12, 24)
        if i % 2 == 1:
            c.setFillColor(SAND)
            c.rect(MX, y - rh, TW, rh, stroke=0, fill=1)
        c.setStrokeColor(LINE)
        c.setLineWidth(0.5)
        c.line(MX, y - rh, W - MX, y - rh)

        c.setFillColor(INK)
        c.setFont(FSB, 8.6)
        nm = wrap(name, FSB, 8.6, col1 - 16)
        ty = y - 15
        for line in nm:
            c.drawString(MX + 8, ty, line)
            ty -= 11.5

        c.setFillColor(INK)
        c.setFont(FM, 8.6)
        ty = y - 15
        for line in lines:
            c.drawString(MX + col1 + 8, ty, line)
            ty -= 11.5
        y -= rh

    c.setStrokeColor(LINE)
    c.setLineWidth(0.7)
    c.line(MX, y, W - MX, y)
    y -= 30

    c.setFillColor(INK)
    c.setFont(FSB, 11.5)
    c.drawString(MX, y, "Остальные 29 — по линейкам")
    y -= 20
    y = text_block(c, MX, y, "Откройте карточку и посмотрите первое предложение описания — "
                             "там обычно сразу понятно, что это за изделие.",
                   F, 9.6, 14, SOFT, TW, gap=14)

    groups = [
        ("ПУТОРАНО", "кухонный борд", "10"),
        ("МАЙГОТО", "придвижной столик", "1"),
        ("КУХТИНАБАТА", "шотница", "2"),
        ("САНТАЛА", "подставка для благовоний", "2"),
        ("ТИВДИЯ", "подсвечник", "1"),
        ("АМАЗОНИТА", "подсвечник", "1"),
        ("Журнальные столики", "столик", "1"),
        ("наборы", "подарочный набор", "4"),
        ("остальное", "уточнить по описанию", "15"),
    ]
    c.setFillColor(MUTED)
    c.setFont(FSB, 7.6)
    c.drawString(MX, y, "ЛИНЕЙКА")
    c.drawString(MX + 150, y, "ЧТО ЭТО")
    c.drawRightString(W - MX, y, "ШТ.")
    y -= 6
    rule(c, y)
    y -= 16
    for g, t, cnt in groups:
        c.setFillColor(INK)
        c.setFont(FSB, 9.2)
        c.drawString(MX, y, g)
        c.setFillColor(SOFT)
        c.setFont(F, 9.2)
        c.drawString(MX + 150, y, t)
        c.setFillColor(WOOD)
        c.setFont(FSB, 9.2)
        c.drawRightString(W - MX, y, cnt)
        y -= 18


def page_alts_1(c, n):
    page_no(c, n)
    y = H - 96
    c.setFillColor(WOOD)
    c.setFont(FB, 22)
    c.drawString(MX, y, "Альты для картинок")
    y -= 16
    rule(c, y, AMBER, 1.2)
    y -= 24

    y = text_block(c, MX, y, "Альт — это описание картинки для тех, кто её не видит: для "
                             "слабовидящих и для поисковика. В настройках страницы его нет.",
                   F, 10.6, 15.5, SOFT, TW, gap=16)

    # где находится
    c.setFillColor(SAND)
    c.roundRect(MX, y - 52, TW, 52, 5, stroke=0, fill=1)
    c.setFillColor(AMBER)
    c.rect(MX, y - 52, 2.6, 52, stroke=0, fill=1)
    c.setFillColor(INK)
    c.setFont(FSB, 9.8)
    c.drawString(MX + 14, y - 21, "Где: нажать на картинку → «Настройки» → поле «Alt текст»")
    c.setFillColor(SOFT)
    c.setFont(F, 9.4)
    c.drawString(MX + 14, y - 38, "В галерее — у каждого слайда отдельно, справа.")
    y -= 74

    c.setFillColor(INK)
    c.setFont(FSB, 11.5)
    c.drawString(MX, y, "Правило")
    y -= 20
    y = text_block(c, MX, y, "Альт отвечает на вопрос «что на этом фото». Не «что мы продаём», "
                             "а «что видно». 60–90 знаков, без слов «фото» и «картинка», без "
                             "перечисления запросов через запятую.",
                   F, 9.8, 14.5, SOFT, TW, gap=20)

    # хорошо / плохо
    c.setFillColor(HexColor("#1A7F37"))
    c.setFont(FSB, 9.4)
    c.drawString(MX, y, "Хорошо")
    c.setFillColor(HexColor("#B03A2E"))
    c.drawString(MX + TW / 2, y, "Плохо")
    y -= 16
    good = "кухонная борда из массива дерева с заливкой эпоксидной смолой"
    bad1 = "доска купить подарок дерево смола ручная работа москва"
    bad2 = "DSC_9849.JPG"
    c.setFillColor(SOFT)
    c.setFont(F, 9.2)
    gy = y
    for line in wrap(good, F, 9.2, TW / 2 - 16):
        c.drawString(MX, gy, line)
        gy -= 13
    by = y
    for line in wrap(bad1, F, 9.2, TW / 2 - 16):
        c.drawString(MX + TW / 2, by, line)
        by -= 13
    c.setFont(MONO, 8.4)
    c.drawString(MX + TW / 2, by, bad2)
    y = min(gy, by) - 26

    c.setFillColor(INK)
    c.setFont(FSB, 11.5)
    c.drawString(MX, y, "Чего не делать")
    y -= 20
    for t in ["Два одинаковых альта на одной странице",
              "Слова «фото», «картинка», «изображение»",
              "Альт длиннее 100 знаков",
              "Альты у декоративных линий и заглушек — там поле оставляем пустым"]:
        c.setFillColor(AMBER)
        c.setFont(F, 9.8)
        c.drawString(MX + 2, y, "—")
        c.setFillColor(SOFT)
        c.drawString(MX + 16, y, t)
        y -= 19

    y -= 10
    y = text_block(c, MX, y, "И ещё: при загрузке переименуйте файл. "
                             "podstavka-dlya-blagovonij.jpg вместо DSC_9554.jpg — "
                             "мелочь, но в поиске по картинкам помогает.",
                   F, 9.4, 13.5, MUTED, TW)


def page_alts_2(c, n):
    page_no(c, n)
    y = H - 96
    c.setFillColor(WOOD)
    c.setFont(FB, 22)
    c.drawString(MX, y, "Альты: готовые тексты")
    y -= 16
    rule(c, y, AMBER, 1.2)
    y -= 22

    y = text_block(c, MX, y, "Копировать в поле «Alt текст» у соответствующей картинки.",
                   F, 10.2, 15, SOFT, TW, gap=16)

    col1 = 108
    for group, place, alt in ALTS:
        if y < BOT + 60:
            break
        c.setFillColor(AMBER)
        c.setFont(FSB, 7.6)
        c.drawString(MX, y, group.upper())
        c.setFillColor(SOFT)
        c.setFont(F, 8.6)
        c.drawString(MX + col1 - 6, y, place)
        y -= 12
        c.setFillColor(INK)
        c.setFont(FM, 9.2)
        for line in wrap(alt, FM, 9.2, TW - col1 - 4):
            c.drawString(MX + col1, y, line)
            y -= 12
        y -= 7

    c.setFillColor(MUTED)
    c.setFont(F, 8.6)
    c.drawString(MX, BOT + 14, "В карточке товара — пять ракурсов, пять разных альтов: "
                               "главное фото, крупно, торец, в интерьере, упаковка.")


def page_check(c, n):
    page_no(c, n)
    y = H - 96
    c.setFillColor(WOOD)
    c.setFont(FB, 22)
    c.drawString(MX, y, "Чек-лист")
    y -= 16
    rule(c, y, AMBER, 1.2)
    y -= 22

    y = text_block(c, MX, y, "Отмечайте прямо в PDF или распечатайте. "
                             "Первые три строки — не про поиск, а про потерянные заказы: "
                             "с них и начните.", F, 10, 14.5, SOFT, TW, gap=16)

    for text, time, hot in CHECKLIST:
        if y < BOT + 24:
            break
        if hot:
            c.setFillColor(HexColor("#FBEFE4"))
            c.rect(MX - 4, y - 4.5, TW + 8, 16, stroke=0, fill=1)
        c.setFillColor(WOOD if hot else MUTED)
        c.setFont(SYM, 9.6)
        c.drawString(MX + 2, y - 1, "\u2610")
        c.setFillColor(INK if hot else SOFT)
        c.setFont(FSB if hot else F, 9)
        c.drawString(MX + 20, y, text)
        c.setFillColor(MUTED)
        c.setFont(F, 8.6)
        c.drawRightString(W - MX, y, time)
        y -= 17

    y -= 10
    if y > BOT + 46:
        c.setFillColor(SAND)
        c.roundRect(MX, y - 44, TW, 44, 5, stroke=0, fill=1)
        c.setFillColor(WOOD)
        c.rect(MX, y - 44, 2.6, 44, stroke=0, fill=1)
        c.setFillColor(INK)
        c.setFont(FSB, 9.4)
        c.drawString(MX + 14, y - 18, "Когда всё заполнено — проверка за минуту")
        c.setFillColor(SOFT)
        c.setFont(F, 9.2)
        c.drawString(MX + 14, y - 33,
                     "Откройте сайт, нажмите Ctrl+U и найдите в первых строках <title> и "
                     "<meta name=\"description\">.")


# ------------------------------------------------------------------ сборка
def build():
    prepare_fonts()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    c = canvas.Canvas(OUT, pagesize=A4)
    c.setTitle("BAK MASTERS: что вставить и в какое поле")
    c.setAuthor("SM Production")
    c.setSubject("SEO для Тильды пошагово: Title, Description, H1, альты")

    def mark(title, level=0):
        c.bookmarkPage(f"bm{title}-{c.getPageNumber()}")
        c.addOutlineEntry(title, f"bm{title}-{c.getPageNumber()}", level=level, closed=False)

    mark("Обложка")
    cover(c)
    c.showPage()

    mark("Что такое Title и Description")
    page_intro(c, 2)
    c.showPage()

    mark("Где эти поля в Тильде")
    page_where(c, 3)
    c.showPage()

    mark("Настройки сайта")
    page_site(c, 4)
    c.showPage()

    n = 5
    mark("Страницы сайта")
    for pg in PAGES:
        mark(f"{pg['n']}. {pg['name']}", 1)
        page_card(c, n, pg)
        c.showPage()
        n += 1

    mark("Товары")
    page_products_1(c, n)
    c.showPage()
    mark("Товары: готовые заголовки", 1)
    page_products_2(c, n + 1)
    c.showPage()

    mark("Альты")
    page_alts_1(c, n + 2)
    c.showPage()
    mark("Альты: готовые тексты", 1)
    page_alts_2(c, n + 3)
    c.showPage()

    mark("Чек-лист")
    page_check(c, n + 4)
    c.showPage()

    c.save()
    print(OUT, os.path.getsize(OUT) // 1024, "KB")


if __name__ == "__main__":
    sys.exit(build())
