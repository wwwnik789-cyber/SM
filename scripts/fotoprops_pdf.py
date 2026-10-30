"""PDF-сборка пакета «Фотопропсы на заказ»: каталог визуализаций + статья + серия постов.

Использует шрифты и стили из md_to_pdf.py, добавляет вывод изображений с подписями.
Запуск: /tmp/venv/bin/python scripts/fotoprops_pdf.py
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import (BaseDocTemplate, Frame, Image, KeepTogether,
                                PageBreak, PageTemplate, Paragraph, Spacer,
                                Table, TableStyle)

from md_to_pdf import (ACCENT, INK, LINE, MUT, NAVY, SOFT, S, md_to_flowables)

ROOT = Path("/home/user/SM")
IMG = ROOT / "visualizations/fotoprops"
OUT = ROOT / "site_content/08_fotoprops-blog-i-smm.pdf"

# порядок: (файл, номер, название, размер/материал, цена)
ITEMS = [
    ("sm-fp-cover-set.jpg", "Комплект", "Набор реквизита «под ключ»",
     "6 баблов + гигантская рука + объёмный хештег, сумка для перевозки",
     "от 19 900 ₽ · с брендированием от 24 500 ₽"),
    ("sm-fp-bubbles.jpg", "Пропс 01", "Баблы на палочке",
     "450 × 300 мм, ПВХ 8 мм, шесть разных форм, меловое покрытие по запросу",
     "от 900 ₽ · набор 6 шт — от 4 900 ₽"),
    ("sm-fp-giant-hand.jpg", "Пропс 02", "Гигантская рука",
     "600 × 450 мм, ПВХ 10 мм, двусторонняя печать, деревянный держатель",
     "от 3 900 ₽"),
    ("sm-fp-hashtag.jpg", "Пропс 03", "Объёмный хештег",
     "1200 × 450 мм, фанера 12 мм + печать, стойка с утяжелённой плитой",
     "от 4 500 ₽ · со стойкой от 7 900 ₽"),
    ("sm-fp-tantamareska.jpg", "Пропс 04", "Тантамареска",
     "2000 × 1500 мм, два окна 320 мм, складная рама-тренога",
     "от 12 000 ₽"),
    ("sm-fp-instaframe.jpg", "Пропс 05", "Инстарамка",
     "1200 × 1200 мм, окно 1000 × 1000 мм, съёмная плашка под логотип",
     "от 14 500 ₽"),
    ("sm-fp-candy-cart.jpg", "Пропс 06", "Тележка для кенди-бара",
     "1200 × 600 × 900 мм, фанера 18 мм, съёмные брендированные борта",
     "от 38 000 ₽"),
    ("sm-fp-giant-cheque.jpg", "Пропс 07", "Гигантский чек и сертификат",
     "1000 × 600 мм, ПВХ 8 мм с жёсткой подложкой, ручки для переноски",
     "от 2 900 ₽"),
    ("sm-fp-microphone-cubes.jpg", "Пропс 08", "Кубики для микрофона",
     "80 × 80 × 80 мм, поролон 25 кг/м³, печать по четырём сторонам",
     "от 700 ₽ за штуку"),
]


# вторая серия: только ПВХ, без деревянных держателей
ITEMS_PVC = [
    ("sm-fp2-giant-hand-pvc.jpg", "Пропс 09", "Гигантская рука без держателя",
     "600 × 450 мм, ПВХ 10 мм, хват — сквозная прорезь в полотне", "от 3 900 ₽"),
    ("sm-fp2-bubbles-handheld.jpg", "Пропс 10", "Баблы, которые держат за край",
     "500 × 320 мм, ПВХ 8 мм, скруглённая кромка, без палочек", "от 1 100 ₽"),
    ("sm-fp2-face-props.jpg", "Пропс 11", "Набор «лица»: усы, губы, очки, корона",
     "ПВХ 6 мм, прорезь под пальцы, четыре предмета в наборе",
     "от 1 400 ₽ · набор от 4 200 ₽"),
    ("sm-fp2-giant-glasses.jpg", "Пропс 12", "Гигантские очки",
     "600 мм, ПВХ 8 мм, линзы — прозрачный ПЭТ, держат за дужки", "от 2 800 ₽"),
    ("sm-fp2-numbers-2027.jpg", "Пропс 13", "Ростовые цифры 2027",
     "Высота 1 300 мм, ПВХ 10 мм, пята-основание из того же листа",
     "от 2 400 ₽ за цифру"),
    ("sm-fp2-round-signs.jpg", "Пропс 14", "Круглые таблички",
     "Ø 300 мм, ПВХ 8 мм, цветной кант, хват-выемка на кромке", "от 800 ₽"),
    ("sm-fp2-hashtag-pvc.jpg", "Пропс 15", "Хештег на ПВХ-основании",
     "1200 × 450 мм, ПВХ 10 мм, основание вырезано из того же листа", "от 3 900 ₽"),
    ("sm-fp2-instaframe-pvc.jpg", "Пропс 16", "Инстарамка на ПВХ-ножках",
     "1200 × 1200 мм, ПВХ 12 мм, углы на скрытых винтах", "от 12 900 ₽"),
    ("sm-fp2-giant-cheque-pvc.jpg", "Пропс 17", "Чек с прорезями для рук",
     "1000 × 600 мм, ПВХ 8 мм, две прорези в полотне", "от 2 900 ₽"),
    ("sm-fp2-tantamareska-pvc.jpg", "Пропс 18", "Тантамареска на ПВХ-раме",
     "2000 × 1500 мм, полотно на трубе ПВХ, углы на фитингах", "от 11 500 ₽"),
]

FOOTER = "SM Production · фотопропсы на заказ · Москва"

EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F\u2B00-\u2BFF\u2190-\u21FF\u2700-\u27BF]")


def fences_to_quote(text):
    """Блоки ```…``` (тексты постов) превращаем в цитаты — моноширинный шрифт тут не нужен."""
    out, lines, inside = [], text.split("\n"), False
    for ln in lines:
        if ln.strip().startswith("```"):
            inside = not inside
            continue
        if inside:
            out.append("> " + ln if ln.strip() else ">")
        else:
            out.append(ln)
    return "\n".join(out)


def strip_emoji(text):
    return EMOJI_RE.sub("", text)


def meta_lines_to_bullets(text):
    """Строки вида **Формат:** … **Визуал:** … разводим по отдельным пунктам."""
    return re.sub(r"(?m)^\*\*(Формат|Визуал|Площадки|Заголовок|Текст|Аудитория|Длительность|Музыка):\*\*",
                  r"- **\1:**", text)



def cover():
    return [
        Spacer(1, 26 * mm),
        Paragraph("SM PRODUCTION · НОВОЕ НАПРАВЛЕНИЕ", S["kicker"]),
        Spacer(1, 6),
        Paragraph("Фотопропсы на заказ", S["title"]),
        Paragraph("Материалы для публикации: каталог визуализаций, статья в блог, серия постов в соцсети",
                  S["subtitle"]),
        Spacer(1, 12 * mm),
        Table(
            [[Paragraph("Услуга", S["cell"]),
              Paragraph("Изготовление фотопропсов и реквизита для фотосессий в Москве", S["cell"])],
             [Paragraph("Что внутри", S["cell"]),
              Paragraph("9 визуализаций с характеристиками · статья для блога с прайсом и FAQ · "
                        "8 публикаций, сценарий видео, план сторис, календарь на 2 недели", S["cell"])],
             [Paragraph("Сроки", S["cell"]),
              Paragraph("1–2 дня после согласования макета, срочные заказы — от 24 часов", S["cell"])],
             [Paragraph("Цены", S["cell"]),
              Paragraph("от 700 ₽ (кубик для микрофона) до 38 000 ₽ (тележка кенди-бара)", S["cell"])],
             [Paragraph("Дата", S["cell"]), Paragraph("30 октября 2026", S["cell"])]],
            colWidths=[30 * mm, 122 * mm], hAlign="LEFT",
            style=TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LINEBELOW", (0, 0), (-1, -1), 0.4, LINE),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ])),
        Spacer(1, 10 * mm),
        Paragraph(
            "Документ собран так, чтобы им можно было пользоваться без переписки: сначала визуальный ряд с "
            "характеристиками каждой позиции — по нему удобно согласовывать ассортимент; затем текст статьи, "
            "готовый к публикации в блоге; затем серия публикаций для ВКонтакте, Telegram и Instagram "
            "с привязкой к конкретным изображениям.", S["body"]),
        Spacer(1, 6 * mm),
        Paragraph("Важно: изображения сгенерированы как концепт реквизита. После первых заказов их стоит заменить "
                  "на съёмки реальных изделий — тексты и структура от этого не меняются.", S["quote"]),
    ]


def gallery(avail_w):
    flow = [Paragraph("Часть 1. Каталог визуализаций", S["h1"]),
            Paragraph("Две серии: классическая с деревянными держателями и полностью ПВХ — без дерева. "
                      "Под каждым кадром — размеры, материалы и ориентир по цене: этого набора "
                      "характеристик достаточно, чтобы ответить на первый запрос клиента.", S["body"]),
            Spacer(1, 2 * mm),
            Paragraph("Серия 1. Классические пропсы", S["h2"])]

    for name, num, title, spec, price in ITEMS:
        path = IMG / name
        img = Image(str(path))
        w = avail_w
        h = w * img.imageHeight / img.imageWidth
        max_h = 84 * mm
        if h > max_h:
            h = max_h
            w = h * img.imageWidth / img.imageHeight
        img.drawWidth, img.drawHeight = w, h

        cap = Paragraph(
            f'<font color="#ff4d1c" size="7.6"><b>{num.upper()}</b></font>　'
            f'<b>{title}</b><br/><font color="#5f6470" size="8.6">{spec}</font><br/>'
            f'<font color="#0f3460" size="8.8"><b>{price}</b></font>',
            S["body"])

        flow.append(KeepTogether([img, Spacer(1, 2.5 * mm), cap, Spacer(1, 6 * mm)]))

    flow.append(Spacer(1, 2 * mm))
    flow.append(PageBreak())
    flow.append(Paragraph("Серия 2. Только ПВХ — без деревянных держателей", S["h2"]))
    flow.append(Paragraph(
        "Держатель — не отдельная деталь, а сквозная прорезь в самом полотне: рука проходит внутрь, пропс "
        "лежит на пальцах и не проворачивается. Основания и пяты для напольных конструкций вырезаются из того "
        "же листа. Нечему ломаться, можно мыть, нет щепок и заусенцев, легче и дешевле в производстве.", S["body"]))
    flow.append(Spacer(1, 3 * mm))

    for name, num, title, spec, price in ITEMS_PVC:
        path = IMG / name
        img = Image(str(path))
        w = avail_w
        h = w * img.imageHeight / img.imageWidth
        max_h = 84 * mm
        if h > max_h:
            h = max_h
            w = h * img.imageWidth / img.imageHeight
        img.drawWidth, img.drawHeight = w, h

        cap = Paragraph(
            f'<font color="#ff4d1c" size="7.6"><b>{num.upper()}</b></font>　'
            f'<b>{title}</b><br/><font color="#5f6470" size="8.6">{spec}</font><br/>'
            f'<font color="#0f3460" size="8.8"><b>{price}</b></font>',
            S["body"])
        flow.append(KeepTogether([img, Spacer(1, 2.5 * mm), cap, Spacer(1, 6 * mm)]))

    flow.append(Spacer(1, 3 * mm))
    flow.append(Paragraph(
        "Все позиции делаются на собственном производстве: фрезеровка контура, печать 1440 dpi с матовой "
        "ламинацией, обработка торца, сборка держателей и стоек. Срок — 1–2 дня после согласования макета.",
        S["quote"]))
    return flow


def section_break(title, subtitle):
    return [PageBreak(),
            Spacer(1, 6 * mm),
            Paragraph(title, S["title"]),
            Spacer(1, 3),
            Paragraph(subtitle, S["subtitle"]),
            Spacer(1, 8 * mm)]


def main():
    blog_md = (ROOT / "site_content/08_blog-fotoprops.md").read_text(encoding="utf-8")
    smm_md = (ROOT / "smm/posts/fotoprops-launch.md").read_text(encoding="utf-8")

    # отрезаем служебный первый заголовок, чтобы не дублировать титул части
    blog_md = blog_md.split("\n", 1)[1] if blog_md.startswith("# ") else blog_md
    smm_md = smm_md.split("\n", 1)[1] if smm_md.startswith("# ") else smm_md

    # строки, целиком состоящие из жирного текста, выносим в подзаголовок:
    # иначе вопрос FAQ слипается с ответом в один абзац
    def bold_lines_to_h3(text):
        return re.sub(r"(?m)^\*\*([^*\n]+)\*\*$", r"### \1", text)

    def prepare(text):
        text = fences_to_quote(text)
        text = strip_emoji(text)
        text = meta_lines_to_bullets(text)
        return bold_lines_to_h3(text)

    blog_md = prepare(blog_md)
    smm_md = prepare(smm_md)

    doc = BaseDocTemplate(
        str(OUT), pagesize=A4,
        leftMargin=18 * mm, rightMargin=16 * mm,
        topMargin=16 * mm, bottomMargin=16 * mm,
        title="Фотопропсы на заказ — материалы для публикации · SM Production",
        author="SM Production", lang="ru")

    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")

    def deco(canv, d):
        canv.saveState()
        canv.setFont("DJ", 7.6)
        canv.setFillColor(MUT)
        canv.drawString(doc.leftMargin, 9 * mm, FOOTER)
        canv.drawRightString(A4[0] - doc.rightMargin, 9 * mm, f"{d.page}")
        canv.setStrokeColor(LINE)
        canv.setLineWidth(0.4)
        canv.line(doc.leftMargin, 12 * mm, A4[0] - doc.rightMargin, 12 * mm)
        canv.restoreState()

    doc.addPageTemplates([PageTemplate(id="page", frames=[frame], onPage=deco)])

    story = cover()
    story += [PageBreak()]
    story += gallery(doc.width)
    story += section_break("Часть 2. Статья для блога",
                           "Готова к публикации: /blog/fotoprops-na-zakaz")
    story += md_to_flowables(blog_md, doc.width)
    story += section_break("Часть 3. Серия публикаций в соцсети",
                           "ВКонтакте, Telegram, Instagram: 8 публикаций, видео, сторис, календарь")
    story += md_to_flowables(smm_md, doc.width)

    doc.build(story)
    print("PDF:", OUT)


if __name__ == "__main__":
    main()
