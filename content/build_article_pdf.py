#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PDF статьи для блога SM Production: «Оформление сцен в помещениях»."""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, HRFlowable)
from reportlab.lib.styles import ParagraphStyle

FD = "/usr/share/fonts/truetype/dejavu"
pdfmetrics.registerFont(TTFont("DV", f"{FD}/DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DVB", f"{FD}/DejaVuSans-Bold.ttf"))

GRAPHITE = HexColor("#17181C")
ORANGE = HexColor("#FF7A1A")
LIME = HexColor("#B7E048")
GREY = HexColor("#5A5E66")
LIGHT = HexColor("#F4F5F7")

TITLE = "Сцена в помещении: экраны, каше и раусы — из чего собирается образ площадки"
SLUG = "oformlenie-scen-v-pomeshcheniyah"
TAG = "Сцены"
DATE = "17.11.2026"
READ = "3 мин"
EXCERPT = ("Какие LED-экраны ставят на сцену, как собирают каше и оформляют "
           "раусы — короткий разбор вариантов оформления сцен в закрытых залах.")

BODY = [
    ("p", "В закрытом зале сцена держит внимание аудитории и работает в кадре. "
          "Рассказываем, из чего собирается её образ."),
    ("h", "Экраны"),
    ("p", "Основа медиасцены — LED-экран с шагом пикселя 2,6–3,9 мм: картинка "
          "остаётся гладкой даже для первых рядов. Центральный экран дополняют "
          "боковыми «ушами» или вертикальными колоннами, чтобы контент читался "
          "и в трансляции."),
    ("h", "Каше"),
    ("p", "Так называют декоративное обрамление экрана. Мы собираем его из "
          "каркаса с брендированной печатью или световыми линиями — и "
          "«телевизор на стойках» превращается в единую сценическую стену."),
    ("h", "Раусы"),
    ("p", "Порталы по бокам сцены задают архитектуру и прячут технические зоны: "
          "фрезерованные фигуры, баннерная печать, контурная подсветка в цвет "
          "графики экрана."),
    ("h", "Дополнительное оборудование"),
    ("p", "Подиум с брендированным торцом, лестницы, пультовые тумбы и "
          "кабель-каналы — детали, которые отвечают за безопасность и чистый "
          "общий план."),
    ("p", "Пришлите план площадки — предложим варианты сцены под ваш бюджет."),
]

body_plain = " ".join(t for _, t in BODY)
N_CHARS = len(body_plain)

st_title = ParagraphStyle("t", fontName="DVB", fontSize=17, leading=22,
                          textColor=GRAPHITE, spaceAfter=4)
st_h = ParagraphStyle("h", fontName="DVB", fontSize=12.5, leading=16,
                      textColor=GRAPHITE, spaceBefore=10, spaceAfter=3)
st_p = ParagraphStyle("p", fontName="DV", fontSize=10.5, leading=15.5,
                      textColor=HexColor("#26282E"), spaceAfter=4)
st_meta_k = ParagraphStyle("mk", fontName="DVB", fontSize=9, leading=12,
                           textColor=GREY)
st_meta_v = ParagraphStyle("mv", fontName="DV", fontSize=9.5, leading=13,
                           textColor=GRAPHITE)
st_note = ParagraphStyle("n", fontName="DV", fontSize=8.5, leading=12,
                         textColor=GREY)


def header(canvas, doc):
    canvas.saveState()
    w, h = A4
    canvas.setFillColor(GRAPHITE)
    canvas.rect(0, h - 24 * mm, w, 24 * mm, stroke=0, fill=1)
    canvas.setFillColor(ORANGE)
    canvas.rect(0, h - 25.2 * mm, w, 1.2 * mm, stroke=0, fill=1)
    canvas.setFont("DVB", 13)
    canvas.setFillColor(white)
    canvas.drawString(18 * mm, h - 15 * mm, "SM PRODUCTION")
    canvas.setFont("DV", 9)
    canvas.setFillColor(HexColor("#C9CCD4"))
    canvas.drawString(18 * mm, h - 20.5 * mm,
                      "Статья для блога · оформление сцен в помещениях")
    canvas.setFillColor(LIME)
    canvas.circle(w - 22 * mm, h - 13 * mm, 2.2 * mm, stroke=0, fill=1)
    canvas.setFont("DV", 8.5)
    canvas.setFillColor(GREY)
    canvas.drawString(18 * mm, 12 * mm,
                      f"Текст статьи: {N_CHARS} знаков с пробелами (лимит 1000)")
    canvas.drawRightString(w - 18 * mm, 12 * mm, "sm-production.ru · блог")
    canvas.restoreState()


doc = SimpleDocTemplate("content/blog-oformlenie-scen.pdf", pagesize=A4,
                        leftMargin=18 * mm, rightMargin=18 * mm,
                        topMargin=34 * mm, bottomMargin=20 * mm,
                        title=TITLE, author="SM Production")

story = [Paragraph(TITLE, st_title), Spacer(1, 3 * mm)]

meta = [
    [Paragraph("Slug", st_meta_k), Paragraph(SLUG, st_meta_v)],
    [Paragraph("Рубрика", st_meta_k), Paragraph(TAG, st_meta_v)],
    [Paragraph("Дата", st_meta_k), Paragraph(DATE, st_meta_v)],
    [Paragraph("Время чтения", st_meta_k), Paragraph(READ, st_meta_v)],
    [Paragraph("Лид (excerpt)", st_meta_k), Paragraph(EXCERPT, st_meta_v)],
]
t = Table(meta, colWidths=[32 * mm, 142 * mm])
t.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
    ("ROWBACKGROUNDS", (0, 0), (-1, -1), [LIGHT, white]),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("TOPPADDING", (0, 0), (-1, -1), 3.5),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
    ("LEFTPADDING", (0, 0), (-1, -1), 7),
    ("LINEBELOW", (0, 0), (-1, -2), 0.4, HexColor("#E2E4E9")),
]))
story += [t, Spacer(1, 2 * mm),
          HRFlowable(width="100%", thickness=1.6, color=ORANGE),
          Spacer(1, 3 * mm)]

for kind, text in BODY:
    story.append(Paragraph(text, st_h if kind == "h" else st_p))

story += [Spacer(1, 4 * mm),
          HRFlowable(width="100%", thickness=0.6, color=HexColor("#E2E4E9")),
          Spacer(1, 2 * mm),
          Paragraph("Поля meta выше совпадают со структурой src/data/blog.js — "
                    "можно переносить в карточку новости без правок. "
                    "Обложку для поста выберите из visualizations/home-covers/.",
                    st_note)]

doc.build(story, onFirstPage=header, onLaterPages=header)
print("PDF собран:", N_CHARS, "знаков в тексте статьи")
