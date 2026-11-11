#!/usr/bin/env python3
"""Шпаргалка на первый звонок в автосалон: 6 страниц A4.

Собирает first-call-shpargalka.pdf:
  1. шпаргалка на звонок (гейты и фразы)
  2. возражения и ответы на 20 секунд
  3–5. карточки трёх первых звонков
  6. оценочный лист для разбора

Запуск из корня репозитория:
    .venv/bin/python marketing/dealerships-2026/first-call/build_first_call_pdf.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Frame, KeepTogether, PageBreak, PageTemplate,
    Paragraph, Spacer, Table, TableStyle,
)

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "first-call-shpargalka.pdf"

PAGE_W, PAGE_H = A4
MARGIN_X = 18 * mm
MARGIN_TOP = 26 * mm
MARGIN_BOTTOM = 17 * mm

PURPLE = colors.HexColor("#7550B5")
PURPLE_DARK = colors.HexColor("#4B2B78")
GOLD = colors.HexColor("#D5A600")
INK = colors.HexColor("#18191F")
MUTED = colors.HexColor("#61636A")
LINE = colors.HexColor("#DDD9D1")
SOFT = colors.HexColor("#F7F5F1")
SOFT_PURPLE = colors.HexColor("#F0EAF8")
WHITE = colors.white

TOTAL_PAGES = 0

FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
pdfmetrics.registerFont(TTFont("Body", str(FONT_DIR / "DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("Body-Bold", str(FONT_DIR / "DejaVuSans-Bold.ttf")))
pdfmetrics.registerFontFamily(
    "Body", normal="Body", bold="Body-Bold", italic="Body", boldItalic="Body-Bold"
)

S = {
    "h1": ParagraphStyle("h1", fontName="Body-Bold", fontSize=21, leading=25, textColor=INK),
    "lead": ParagraphStyle("lead", fontName="Body", fontSize=9.4, leading=13.4, textColor=MUTED),
    "h2": ParagraphStyle("h2", fontName="Body-Bold", fontSize=11.4, leading=14.5, textColor=PURPLE_DARK,
                         spaceBefore=9, spaceAfter=4),
    "h3": ParagraphStyle("h3", fontName="Body-Bold", fontSize=9.8, leading=13, textColor=INK,
                         spaceBefore=6, spaceAfter=2),
    "body": ParagraphStyle("body", fontName="Body", fontSize=9.0, leading=13.2, textColor=INK, spaceAfter=3),
    "small": ParagraphStyle("small", fontName="Body", fontSize=7.8, leading=11, textColor=MUTED),
    "quote": ParagraphStyle("quote", fontName="Body", fontSize=8.9, leading=12.8, textColor=INK),
    "cell": ParagraphStyle("cell", fontName="Body", fontSize=8.4, leading=12, textColor=INK),
    "cellb": ParagraphStyle("cellb", fontName="Body-Bold", fontSize=8.4, leading=12, textColor=INK),
    "cellhead": ParagraphStyle("cellhead", fontName="Body-Bold", fontSize=7.6, leading=10, textColor=WHITE),
    "num": ParagraphStyle("num", fontName="Body-Bold", fontSize=9.6, leading=13, textColor=PURPLE),
}


def esc(text: str) -> str:
    return escape(text)


def quote_block(lines: list[str], bg=SOFT_PURPLE, accent=PURPLE) -> Table:
    """Речевой блок: цветная полоса слева и цитаты внутри."""
    paras = [Paragraph(esc(line), S["quote"]) for line in lines]
    cell = Table([[p] for p in paras], colWidths=[PAGE_W - MARGIN_X * 2 - 5 * mm])
    cell.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 1.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
    ]))
    box = Table([["", cell]], colWidths=[2.6 * mm, PAGE_W - MARGIN_X * 2])
    box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), accent),
        ("BACKGROUND", (1, 0), (1, 0), bg),
        ("LEFTPADDING", (0, 0), (0, 0), 0),
        ("RIGHTPADDING", (0, 0), (0, 0), 0),
        ("LEFTPADDING", (1, 0), (1, 0), 7),
        ("RIGHTPADDING", (1, 0), (1, 0), 7),
        ("TOPPADDING", (1, 0), (1, 0), 7),
        ("BOTTOMPADDING", (1, 0), (1, 0), 7),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return box


def gate(number: str, title: str, subtitle: str, lines: list[str]) -> list:
    head = Table([[Paragraph(number, S["num"]),
                   Paragraph(f"<b>{esc(title)}</b>", S["body"]),
                   Paragraph(esc(subtitle), S["small"])]],
                 colWidths=[9 * mm, (PAGE_W - MARGIN_X * 2) * 0.46, (PAGE_W - MARGIN_X * 2) * 0.52])
    head.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return [head, quote_block(lines), Spacer(1, 7)]


def bullets(items: list[str], style="body") -> list:
    return [Paragraph(f"•&nbsp;&nbsp;{esc(i)}", S[style]) for i in items]


def table(data, widths, header=True, sizes=None, align="LEFT") -> Table:
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    cmds = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, LINE),
        ("BOX", (0, 0), (-1, -1), 0.4, LINE),
    ]
    if header:
        cmds += [("BACKGROUND", (0, 0), (-1, 0), PURPLE_DARK)]
    else:
        cmds += [("BACKGROUND", (0, 0), (-1, -1), SOFT)]
    for row in range(1 if header else 0, len(data)):
        if (row % 2) == (0 if header else 1):
            cmds.append(("BACKGROUND", (0, row), (-1, row), SOFT))
    t.setStyle(TableStyle(cmds))
    return t


# ─── страницы ────────────────────────────────────────────────────────────────


def page_cheatsheet() -> list:
    flow = [
        Paragraph("Первый звонок в автосалон", S["h1"]),
        Spacer(1, 3),
        Paragraph("Шпаргалка на один разговор. Цель — не продать, а получить фотографию зоны и дату.",
                  S["lead"]),
        Spacer(1, 12),
        Paragraph("10 минут до звонка", S["h2"]),
        *bullets([
            "Открыть сайт центра: акции, новые модели, контакты.",
            "Записать три факта о центре — они пригодятся в разговоре.",
            "Сформулировать строку: «звоню про [зона] к [дата]».",
            "Рядом — карточка звонка, ручка, таймер на 7 минут.",
        ]),
        Spacer(1, 8),
        Paragraph("Три двери", S["h2"]),
        *gate("01", "Ресепшн", "30–60 секунд · цель — имя и должность", [
            "Добрый день! Подскажите, пожалуйста, кто у вас отвечает за оформление салона — сезонные материалы, презентации моделей?",
            "Если «пришлите на почту»: Обязательно пришлю. На чьё имя адресовать, чтобы письмо не попало в общую папку?",
            "Если не соединяют: Подскажите имя и должность того, кто решает по оформлению. Напишу письмо и сошлюсь на вас.",
        ]),
        *gate("02", "Ответственный", "2–3 минуты · сначала вопрос, потом рассказ", [
            "[Имя], добрый день! Меня зовут [имя], SM Production. Мы производим оформление для дилерских центров: сезонные материалы, навигацию, зоны выдачи, конструкции под запуск модели. Производство своё, в Москве.",
            "Звоню не с предложением купить — хочу понять, есть ли задача на ближайшие два-три месяца.",
            "Что у вас сейчас вероятнее: сезонное обновление, запуск модели или переделка зон?",
            "Какая зона? Когда должно стоять? Кто ещё участвует? Что не устроило в прошлый раз?",
        ]),
    ]

    kill = [
        [Paragraph("Не говорить", S["cellhead"]), Paragraph("Почему", S["cellhead"])],
        [Paragraph("«Хотел бы предложить сотрудничество»", S["cell"]),
         Paragraph("ноль информации, мгновенный отказ", S["cell"])],
        [Paragraph("«Полный комплекс услуг под ключ»", S["cell"]),
         Paragraph("так говорят все, слушать нечего", S["cell"])],
        [Paragraph("«Есть минутка?»", S["cell"]),
         Paragraph("даёт право сказать «нет» до объяснения", S["cell"])],
        [Paragraph("«Давайте я приеду и всё расскажу»", S["cell"]),
         Paragraph("встреча без повода — отказ", S["cell"])],
    ]
    flow += [Spacer(1, 2), Paragraph("Чего не обещать", S["h2"]),
             Paragraph("Цену без размеров · концепцию «за день» · срок без подтверждения производства · "
                       "монтаж без проверки доступа · точный цвет без пробы · кейсы, которых не было.", S["body"]),
             Spacer(1, 6),
             table(kill, [PAGE_W - MARGIN_X * 2 - 62 * mm, 62 * mm])]
    return flow


def page_cheatsheet_2() -> list:
    """Продолжение шпаргалки: третий гейт и пять вопросов после звонка."""
    return [
        Paragraph("Три двери (продолжение)", S["h2"]),
        *gate("03", "Следующий шаг", "20–30 секунд · одна договорённость", [
            "Тогда так: вы присылаете фото зоны и примерные размеры, я в течение рабочего дня возвращаюсь с составом и предварительным расчётом. Дизайн и точную смету подтвердим после брифа.",
            "Когда удобнее прислать фото — сегодня или завтра? И на какой канал?",
        ]),
        Spacer(1, 4),
        Paragraph("Если после звонка нет ответов на эти вопросы — звонка не было", S["h2"]),
        table([
            [Paragraph("№", S["cellhead"]), Paragraph("Что должно быть записано", S["cellhead"])],
            [Paragraph("1", S["cellb"]), Paragraph("Как зовут человека и какова его роль", S["cell"])],
            [Paragraph("2", S["cellb"]), Paragraph("Какая задача прозвучала — его словами, в кавычках", S["cell"])],
            [Paragraph("3", S["cellb"]), Paragraph("Какая дата: месяц или конкретный день", S["cell"])],
            [Paragraph("4", S["cellb"]), Paragraph("Кто ещё участвует в решении", S["cell"])],
            [Paragraph("5", S["cellb"]), Paragraph("Что я обещал прислать и когда", S["cell"])],
        ], [11 * mm, PAGE_W - MARGIN_X * 2 - 11 * mm]),
        Spacer(1, 12),
        Paragraph("Если три звонка из трёх упираются в ресепшн", S["h2"]),
        Paragraph("Проблема в первой фразе, а не в рынке. Меняем фразу и звоним ещё три. "
                  "Если наоборот — доходят до человека, но никто не даёт фото — проблема в шаге "
                  "«следующий шаг»: мы просим слишком много или слишком неопределённо.", S["body"]),
        Spacer(1, 12),
        Paragraph("Порядок дня", S["h2"]),
        table([
            [Paragraph("Когда", S["cellhead"]), Paragraph("Что", S["cellhead"])],
            [Paragraph("10:30–12:00", S["cell"]), Paragraph("Звонок 1 — АвтоГЕРМЕС, разминка", S["cell"])],
            [Paragraph("12:00–12:30", S["cell"]), Paragraph("Карточка, письмо, пауза", S["cell"])],
            [Paragraph("15:00–15:40", S["cell"]), Paragraph("Звонок 2 — БИЗНЕС КАР, его записываем", S["cell"])],
            [Paragraph("15:40–16:10", S["cell"]), Paragraph("Карточка, письмо", S["cell"])],
            [Paragraph("16:10–16:40", S["cell"]), Paragraph("Звонок 3 — AVILON, вход через имя", S["cell"])],
            [Paragraph("17:00", S["cell"]), Paragraph("Три карточки, две правки в скрипт", S["cell"])],
        ], [34 * mm, PAGE_W - MARGIN_X * 2 - 34 * mm]),
    ]


def page_objections() -> list:
    rows = [[Paragraph("Возражение", S["cellhead"]), Paragraph("Ответ на 20 секунд", S["cellhead"])]]
    data = [
        ("У нас есть подрядчик",
         "Менять никого не предлагаю. Что вы делаете, когда подрядчик не успевает к дате? Если было — можем быть вторым производством. Прислать материалы, чтобы были под рукой?"),
        ("Пришлите прайс",
         "Прайса как таблицы нет: цена зависит от размера, материала и монтажа. Пришлите фото зоны и размер — вернусь с расчётом в течение рабочего дня."),
        ("Нет бюджета",
         "Понял. Бюджет закончился на этот год или не выделен под задачу? И есть ли задача, где деньги уже есть — запуск модели, сезонная кампания?"),
        ("Сейчас не до этого",
         "Хорошо, не буду занимать. В каком месяце у вас начинается подготовка — чтобы вернуться вовремя?"),
        ("Нужен тендер",
         "Готовы участвовать. Какие документы нужны для допуска и в каком формате смета? Если ТЗ формируется — поможем уточнить производственные параметры."),
        ("Слишком дорого",
         "Разделим смету на обязательное и опции. Часто можно сохранить задачу, изменив материал или конструкцию. Что из позиций критично?"),
        ("Нет макета",
         "Макет на первом шаге и не нужен. Нужны фотография зоны, примерный размер и дата. Состав предложим мы, дизайн — после брифа."),
        ("Отправьте на общую почту",
         "Отправлю. На чьё имя адресовать, чтобы письмо не потерялось? И кто обычно смотрит такие письма — позвоню ему через пару дней."),
        ("Только проверенные поставщики",
         "Логично. Предложу маленький шаг: одна зона, один комплект, расчёт по фото. Сработает — добавите нас в список, нет — вы ничего не потеряли."),
        ("Откуда у вас мой номер",
         "Звоню на официальный номер центра, взял с сайта. Меня зовут [имя], SM Production, Москва. Если удобнее письмом — скажите адрес."),
    ]
    for q, a in data:
        rows.append([Paragraph(esc(q), S["cellb"]), Paragraph(esc(a), S["cell"])])

    return [
        Paragraph("Возражения", S["h1"]),
        Spacer(1, 3),
        Paragraph("Не спорить. Длинный ответ после возражения не слушают.", S["lead"]),
        Spacer(1, 12),
        table(rows, [52 * mm, PAGE_W - MARGIN_X * 2 - 52 * mm]),
        Spacer(1, 10),
        Paragraph("Одно нарушенное обещание стоит дороже десяти пропущенных звонков: "
                  "салон — тесный рынок, здесь всё рассказывают друг другу.", S["small"]),
    ]


def page_card(index: str, title: str, rows: list[tuple[str, str]], why: str, angle: str, goal: str) -> list:
    info = [[Paragraph(esc(k), S["cellb"]), Paragraph(esc(v), S["cell"])] for k, v in rows]
    info_table = Table(info, colWidths=[42 * mm, PAGE_W - MARGIN_X * 2 - 42 * mm])
    info_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 0), (0, -1), SOFT),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, LINE),
        ("BOX", (0, 0), (-1, -1), 0.4, LINE),
    ]))

    notes = Table([[""] for _ in range(6)], colWidths=[PAGE_W - MARGIN_X * 2], rowHeights=[9 * mm] * 6)
    notes.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
    ]))

    return [
        Paragraph(f"Карточка звонка {index}", S["h1"]),
        Spacer(1, 3),
        Paragraph(esc(title), S["lead"]),
        Spacer(1, 12),
        info_table,
        Spacer(1, 10),
        Paragraph("Почему этот звонок", S["h2"]),
        Paragraph(esc(why), S["body"]),
        Paragraph("Угол разговора", S["h2"]),
        quote_block([angle]),
        Spacer(1, 8),
        Paragraph("Задача звонка", S["h2"]),
        Paragraph(esc(goal), S["body"]),
        Spacer(1, 8),
        Paragraph("Что записать после разговора", S["h2"]),
        notes,
    ]


def page_score() -> list:
    rows = [[Paragraph("№", S["cellhead"]), Paragraph("Критерий", S["cellhead"]),
             Paragraph("0", S["cellhead"]), Paragraph("1", S["cellhead"]), Paragraph("2", S["cellhead"])]]
    criteria = [
        ("Назвал себя и компанию в первые 10 секунд", "нет", "с запинкой", "чётко"),
        ("Сказал, что производит, а не «предлагает услуги»", "нет", "общо", "конкретно"),
        ("Задал вопрос о задаче раньше, чем рассказал о себе", "нет", "после", "первым"),
        ("Выслушал до конца, не перебил", "перебил", "почти", "полностью"),
        ("Уточнил зону", "нет", "в общем", "конкретно"),
        ("Уточнил дату", "нет", "«когда-нибудь»", "месяц или день"),
        ("Уточнил, кто участвует в решении", "нет", "намёком", "имя и роль"),
        ("Предложил один следующий шаг", "нет", "несколько", "один"),
        ("Договорился о дате и канале", "нет", "«пришлите»", "день и канал"),
        ("Не обещал цену и срок без данных", "обещал", "почти", "чисто"),
        ("Записал формулировки клиента дословно", "нет", "пересказ", "цитаты"),
        ("Отправил письмо в течение 30 минут", "нет", "в тот же день", "в течение часа"),
    ]
    for i, (name, a, b, c) in enumerate(criteria, 1):
        is_footer = i == len(criteria)

    data_rows = []
    for i, (name, a, b, c) in enumerate(criteria, 1):
        data_rows.append([Paragraph(f"{i:02d}", S["cellb"]), Paragraph(esc(name), S["cell"]),
                          Paragraph(esc(a), S["small"]), Paragraph(esc(b), S["small"]), Paragraph(esc(c), S["small"])])
    rows += data_rows

    legend = [
        [Paragraph("<b>16–24</b>", S["cell"]), Paragraph("можно звонить по базе самостоятельно", S["cell"])],
        [Paragraph("<b>10–15</b>", S["cell"]), Paragraph("ещё три круга в ролевой игре, потом на живых", S["cell"])],
        [Paragraph("<b>меньше 10</b>", S["cell"]), Paragraph("проблема в структуре звонка, а не в человеке", S["cell"])],
    ]
    legend_t = Table(legend, colWidths=[28 * mm, PAGE_W - MARGIN_X * 2 - 28 * mm])
    legend_t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 0), (-1, -1), SOFT),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, LINE),
    ]))

    return [
        Paragraph("Оценочный лист", S["h1"]),
        Spacer(1, 3),
        Paragraph("Заполняется наставником во время звонка. Максимум 24 балла, проходной — 16.", S["lead"]),
        Spacer(1, 12),
        table(rows, [11 * mm, 86 * mm, 24 * mm, 26 * mm, PAGE_W - MARGIN_X * 2 - 147 * mm]),
        Spacer(1, 10),
        Paragraph("Итог: _______ из 24", ParagraphStyle("score", fontName="Body-Bold", fontSize=12,
                                                        leading=16, textColor=INK)),
        Spacer(1, 6),
        legend_t,
        Spacer(1, 10),
        Paragraph("Три фразы для разбора: что сработало · где просели · какую фразу заменим. "
                  "Одна правка за раз, иначе статистики не будет.", S["small"]),
    ]


# ─── каркас документа ────────────────────────────────────────────────────────


def header_footer(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(PURPLE_DARK)
    canvas.rect(0, PAGE_H - 18 * mm, PAGE_W, 18 * mm, fill=1, stroke=0)
    canvas.setFillColor(GOLD)
    canvas.rect(0, PAGE_H - 19.2 * mm, PAGE_W, 1.2 * mm, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont("Body-Bold", 7.6)
    canvas.drawString(MARGIN_X, PAGE_H - 12 * mm, "SM PRODUCTION · ПЕРВЫЙ ЗВОНОК В АВТОСАЛОН")
    canvas.setFont("Body", 7.2)
    canvas.setFillColor(colors.HexColor("#C9B8E0"))
    canvas.drawRightString(PAGE_W - MARGIN_X, PAGE_H - 12 * mm, "декабрь 2026 / сезон 2027")
    canvas.setFillColor(MUTED)
    canvas.setFont("Body", 7.2)
    canvas.drawString(MARGIN_X, 10 * mm, "Внутренний документ. Цены по телефону не называем.")
    canvas.drawRightString(PAGE_W - MARGIN_X, 10 * mm, f"{doc.page} / {TOTAL_PAGES or doc.page}")
    canvas.restoreState()


def build_once() -> int:
    doc = BaseDocTemplate(
        str(OUT), pagesize=A4,
        leftMargin=MARGIN_X, rightMargin=MARGIN_X,
        topMargin=MARGIN_TOP, bottomMargin=MARGIN_BOTTOM,
        title="Первый звонок в автосалон — шпаргалка",
        author="SM Production",
    )
    frame = Frame(MARGIN_X, MARGIN_BOTTOM, PAGE_W - MARGIN_X * 2, PAGE_H - MARGIN_TOP - MARGIN_BOTTOM,
                  id="main", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate(id="page", frames=[frame], onPage=header_footer)])

    story = []
    story += page_cheatsheet()
    story.append(PageBreak())
    story += page_cheatsheet_2()
    story.append(PageBreak())
    story += page_objections()
    story.append(PageBreak())
    story += page_card(
        "1", "АвтоГЕРМЕС, Рябиновая · разминка",
        [("Телефон", "+7 (495) 236-00-56"),
         ("Адрес", "Москва, ул. Рябиновая, 43Б"),
         ("Кому", "руководитель маркетинга площадки или директор комплекса"),
         ("Почта", "info@avtogermes.ru — только если попросят"),
         ("account_id", "ACC-11")],
        "Массовые бренды и частая смена ценовых и сезонных предложений: то, что висит в зале, "
        "меняется постоянно. Ресепшн спокойнее, разговор короче — хорошо для первого раза.",
        "Не «оформление салона», а «комплект, который меняется за одну смену»: ценники, сезонные "
        "предложения, акции. Это их ежедневная задача, а не наш интересный проект.",
        "Пройти ресепшн и понять, есть ли отдельный маркетолог площадки. Если нет — узнать, кто согласует.",
    )
    story.append(PageBreak())
    story += page_card(
        "2", "БИЗНЕС КАР, Битца · основной, его и записываем",
        [("Телефон", "+7 (495) 172-22-83"),
         ("Адрес", "Москва, Балаклавский пр-т, 26"),
         ("Кому", "маркетинг центра или маркетинг сервиса"),
         ("Канал", "телефон; на сайте есть форма обратного звонка"),
         ("account_id", "ACC-10")],
        "Несколько сегментов — новые автомобили, сервис, машины с пробегом — и текущие сезонные "
        "кампании. Здесь видно, как один вопрос превращается в маршрут: въезд, приёмка, ожидание, выдача.",
        "«Комплект кампании по маршруту клиента». Не «напечатаем баннеры», а «акция идёт по всему "
        "маршруту, а материалы, скорее всего, только на входе».",
        "Получить фотографии зоны и дату ближайшей кампании. Это уже бриф, а не «интересно».",
    )
    story.append(PageBreak())
    story += page_card(
        "3", "AVILON, Волгоградский · сложный, вход через имя",
        [("Телефон", "+7 (495) 730-44-08"),
         ("Через центр", "+7 (495) 730-44-46"),
         ("Адрес", "Москва, Волгоградский проспект, 41–43"),
         ("Кому", "Алина Косикова, руководитель отдела маркетинга Land Rover АВИЛОН"),
         ("Почта", "info@avilon.ru"),
         ("account_id", "ACC-01")],
        "Есть публично названное имя — отдельный навык: не «соедините с маркетингом», а «соедините "
        "с Алиной Косиковой». Такой вход выглядит профессионально, но и отказать по нему проще.",
        "Кластер: несколько брендов и корпусов, запуски моделей, ночной монтаж. Предложение — пилот "
        "на одной зоне с образцами материалов и монтажом вне клиентского потока.",
        "Не встреча, а разрешение прислать материалы на конкретную зону с фотографией. "
        "Имя публичное: не заявлять, что человек отвечает за закупку.",
    )
    story.append(PageBreak())
    story += page_score()

    doc.build(story)
    return doc.page


def build() -> int:
    """Две сборки: первая узнаёт число страниц, вторая печатает его в колонтитул."""
    global TOTAL_PAGES
    TOTAL_PAGES = 0
    pages = build_once()
    TOTAL_PAGES = pages
    build_once()

    size = OUT.stat().st_size // 1024
    print(f"{OUT.name}: {size} КБ, {pages} страниц")
    return 0


if __name__ == "__main__":
    sys.exit(build())
