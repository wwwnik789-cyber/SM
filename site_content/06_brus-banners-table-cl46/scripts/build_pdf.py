#!/usr/bin/env python3
"""Build the standalone, six-page Russian CL46 timber-banner table guide."""
from __future__ import annotations

from html import escape
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Frame, KeepTogether, PageBreak, PageTemplate,
    Paragraph, Preformatted, Spacer, Table, TableStyle,
)

FOLDER = Path(__file__).resolve().parents[1]
OUTPUT = FOLDER / "sm-production-brus-banners-table-tilda-cl46.pdf"
DATE = "19.11.2026"
PAGE_COUNT = 6
FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
for name, filename in [
    ("Body", "DejaVuSans.ttf"),
    ("BodyBold", "DejaVuSans-Bold.ttf"),
    ("Mono", "DejaVuSansMono.ttf"),
]:
    pdfmetrics.registerFont(TTFont(name, str(FONT_DIR / filename)))
pdfmetrics.registerFontFamily("Body", normal="Body", bold="BodyBold", italic="Body", boldItalic="BodyBold")

PW, PH = A4
MARGIN = 44
CW = PW - 2 * MARGIN
NAVY = colors.HexColor("#223347")
GOLD = colors.HexColor("#a47a29")
INK = colors.HexColor("#253548")
MUTED = colors.HexColor("#647181")
LINE = colors.HexColor("#dce3e9")
PALE = colors.HexColor("#f2f5f8")
BLUE = colors.HexColor("#266887")

SIZES = ["2 × 2", "2 × 2,5", "3 × 2", "3 × 2,5", "4 × 2,5", "4 × 3", "5 × 2,5", "5 × 3"]
TABLE_HEADER = "Размер (Ш × В), м;Стоимость, ₽"
TABLE_BODY = "\n".join(f"{size};УТОЧНИТЬ" for size in SIZES)
COLUMN_WIDTHS = "60%;40%"

STYLES = {}
def style(name, **kwargs):
    options = dict(fontName="Body", fontSize=9.4, leading=14,
                   textColor=INK, spaceAfter=7, allowWidows=0, allowOrphans=0)
    options.update(kwargs)
    STYLES[name] = ParagraphStyle(name, **options)

style("Body")
style("Small", fontSize=8.2, leading=12, textColor=MUTED, spaceAfter=6)
style("Kicker", fontName="BodyBold", fontSize=8.2, leading=12, textColor=GOLD, spaceAfter=9)
style("Title", fontName="BodyBold", fontSize=25, leading=31, textColor=NAVY, spaceAfter=13)
style("H1", fontName="BodyBold", fontSize=20, leading=25, textColor=NAVY, spaceAfter=14, keepWithNext=1)
style("H2", fontName="BodyBold", fontSize=11.1, leading=16, textColor=NAVY, spaceBefore=9, spaceAfter=6, keepWithNext=1)
style("Lead", fontSize=10.7, leading=16, textColor=MUTED, spaceAfter=13)
style("Cell", fontSize=8.6, leading=12.3, spaceAfter=0, allowWidows=1, allowOrphans=1)
style("CellSmall", fontSize=8.1, leading=11.5, spaceAfter=0, allowWidows=1, allowOrphans=1)
style("HeadCell", fontName="BodyBold", fontSize=8.7, leading=12.5, textColor=colors.white, spaceAfter=0, allowWidows=1, allowOrphans=1)
style("Code", fontName="Mono", fontSize=9, leading=14, spaceAfter=0, allowWidows=1, allowOrphans=1)
style("Check", leftIndent=16, firstLineIndent=0, bulletIndent=0, bulletFontName="Body", bulletFontSize=9, spaceAfter=5, fontSize=9, leading=13.3)
style("Notice", fontSize=8.8, leading=13.1, spaceAfter=0)


def p(text, kind="Body"):
    return Paragraph(text, STYLES[kind])


def heading(text, key, first=False):
    flow = p(escape(text).replace("&lt;br/&gt;", "<br/>"), "Title" if first else "H1")
    flow.section_key = key
    return flow


def table(rows, ratios=None, small=False, padding=7):
    if ratios is None:
        ratios = [1 / len(rows[0])] * len(rows[0])
    data = [[p(str(cell), "HeadCell" if i == 0 else "CellSmall" if small else "Cell")
             for cell in row] for i, row in enumerate(rows)]
    result = Table(data, colWidths=[CW * r for r in ratios], hAlign="LEFT", repeatRows=1)
    result.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PALE]),
        ("LINEBELOW", (0, 0), (-1, -1), .45, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), padding),
        ("RIGHTPADDING", (0, 0), (-1, -1), padding),
        ("TOPPADDING", (0, 0), (-1, -1), padding),
        ("BOTTOMPADDING", (0, 0), (-1, -1), padding),
    ]))
    return result


def notice(text):
    item = Table([[p(text, "Notice")]], colWidths=[CW], hAlign="LEFT")
    item.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PALE),
        ("LINEBEFORE", (0, 0), (0, 0), 2.4, GOLD),
        ("LEFTPADDING", (0, 0), (-1, -1), 11),
        ("RIGHTPADDING", (0, 0), (-1, -1), 11),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
    ]))
    return item


def code_field(title, text):
    block = Table([[Preformatted(text, STYLES["Code"])]], colWidths=[CW], hAlign="LEFT")
    block.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PALE),
        ("BOX", (0, 0), (-1, -1), .5, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 11),
        ("RIGHTPADDING", (0, 0), (-1, -1), 11),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    return KeepTogether([p(title, "H2"), block, Spacer(1, 3)])


def check(text):
    return Paragraph(text, STYLES["Check"], bulletText="☐")


def link(url, label):
    return f'<link href="{escape(url, quote=True)}" color="#266887">{escape(label)}</link>'


class GuideDoc(BaseDocTemplate):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        frame = Frame(MARGIN, 49, CW, PH - 111, id="main",
                      leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        self.addPageTemplates(PageTemplate(id="guide", frames=[frame], onPage=self.decorate))

    def decorate(self, canvas, doc):
        canvas.saveState()
        canvas.setFillColor(NAVY)
        canvas.setFont("BodyBold", 7.9)
        canvas.drawString(MARGIN, PH - 30, "SM PRODUCTION / ТАБЛИЦА СТОИМОСТИ / TILDA CL46")
        canvas.setStrokeColor(LINE)
        canvas.setLineWidth(.6)
        canvas.line(MARGIN, PH - 40, PW - MARGIN, PH - 40)
        canvas.setFillColor(MUTED)
        canvas.setFont("Body", 7.4)
        canvas.drawString(MARGIN, 27, f"Практическая инструкция · {DATE}")
        canvas.drawRightString(PW - MARGIN, 27, f"{doc.page} / {PAGE_COUNT}")
        canvas.restoreState()

    def afterFlowable(self, flow):
        if isinstance(flow, Paragraph) and getattr(flow, "section_key", None):
            key = flow.section_key
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(flow.getPlainText().replace("\n", " "), key, level=0)


def build():
    story = []

    # 1 — A usable visual target, not a page consisting only of a title.
    story += [p("ОТДЕЛЬНАЯ ИНСТРУКЦИЯ · БЕЗ КОДА И БЕЗ ZERO BLOCK", "Kicker"),
              heading("Таблица стоимости<br/>стандартных<br/>брус-баннеров на Тильде", "overview", first=True),
              p("Готовая схема для блока CL46: восемь размеров, две колонки, читаемая мобильная версия и кнопка заявки.", "Lead"),
              notice("<b>Цены пока не утверждены.</b> В этом документе нет выдуманных сумм. «УТОЧНИТЬ» — рабочая метка, а не готовая публичная цена. Сайт не изменён и не опубликован."),
              p("Как должна выглядеть таблица", "H2"),
              table([["Размер (Ш × В), м", "Стоимость, ₽"]] + [[s, "УТОЧНИТЬ"] for s in SIZES], [.60, .40], padding=6),
              Spacer(1, 8),
              p("Все размеры — <b>ширина × высота</b>. Таблица относится только к стандартным конструкциям на каркасе из бруса: не добавляйте сюда «Джокеры», RollUp или виндеры.", "Small"),
              p("Маршрут по документу", "H2"),
              p('<link href="#content" color="#266887">2 · Блок и готовые строки</link>  /  '
                '<link href="#appearance" color="#266887">3 · Оформление и мобильная версия</link><br/>'
                '<link href="#prices" color="#266887">4 · Цены и комплектация</link>  /  '
                '<link href="#request" color="#266887">5 · Заявка и карточки</link>  /  '
                '<link href="#publish" color="#266887">6 · Проверка и запуск</link>', "Small"),
              PageBreak()]

    # 2 — All pasteable data is in the actual PDF, not in a separate download.
    story += [p("ШАГ 1 / КОНТЕНТ", "Kicker"),
              heading("Добавьте блок и вставьте данные", "content"),
              p("<b>1.</b> Откройте нужный проект Tilda и страницу прайса. Начните с копии страницы или сохранённого черновика. Старые суммы с /tseny не считайте автоматически согласованными."),
              p("<b>2.</b> Нажмите «Добавить блок» → «Все блоки» → <b>«Колонки» → CL46 «Таблица»</b>. Это блок таблицы, а не ST340C с товарными карточками."),
              p("<b>3.</b> Разместите его в разделе брус-баннеров: <b>заголовок → пояснение комплектации → таблица → кнопка заявки</b>. Заголовок рядом с таблицей: «Стоимость стандартных брус-баннеров»."),
              p("<b>4.</b> Откройте «Контент» CL46. Замените демонстрационные данные блоками ниже. Копируйте только строки внутри серых полей, без их названий."),
              code_field("Поле «Шапка таблицы» — одна строка", TABLE_HEADER),
              code_field("Поле «Содержимое таблицы» / «Текст» — восемь строк", TABLE_BODY),
              code_field("Поле «Ширина колонок»", COLUMN_WIDTHS),
              p("<b>Как работает разметка:</b> точка с запятой <b>;</b> разделяет две ячейки; <b>Enter</b> создаёт следующую строку. В каждой строке должен быть ровно один разделитель. Заголовок в основной текст не дублируйте."),
              notice("После вставки нажмите «Сохранить и закрыть». В предпросмотре должно быть <b>2 колонки, 8 строк данных и отдельная шапка</b>. Восемь меток «УТОЧНИТЬ» замените утверждёнными ценами перед публикацией."),
              PageBreak()]

    # 3 — Distinguish documented CL46 controls from suggested visual values.
    story += [p("ШАГ 2 / ДИЗАЙН И АДАПТИВНОСТЬ", "Kicker"),
              heading("Настройте оформление<br/>и мобильную версию", "appearance"),
              p("Сначала настройте штатные параметры CL46. Значения цветов и размеров ниже — <b>рекомендация для оформления SM</b>, а не обязательные настройки самой Тильды."),
              table([
                  ["Что настроить", "Значение / действие"],
                  ["Ширина колонок", "В «Контенте»: <b>60%;40%</b>. Сумма — 100%. Если оставить поле пустым, колонки будут равной ширины."],
                  ["Общая ширина", "В «Настройках» задайте ширину и отступ слева. В стандартной 12-колоночной сетке ориентир: 10 колонок и отступ 1. Сохраните центрирование относительно заголовка."],
                  ["Шапка", "Тёмно-синий фон <b>#223347</b>, белый текст <b>#FFFFFF</b>. Используйте читаемый полужирный шрифт."],
                  ["Строки", "Нечётные — <b>#FFFFFF</b>, чётные — <b>#F2F5F8</b>. Разделители — <b>#DCE3E9</b>; основной текст — <b>#253548</b>."],
                  ["Текст и плотность", "Ориентир: 16 px на компьютере, не меньше 14 px на телефоне. Если доступен только общий масштаб, начните с 1 и проверьте читаемость. Не пытайтесь уместить текст уменьшением до 10–11 px."],
                  ["Мобильная версия", "Включите <b>«Разрешить изменение ширины таблицы на мобильных устройствах»</b>. Для двух коротких колонок это подходящий режим сжатия по ширине экрана."],
              ], [.29, .71], small=True),
              p("Проверка в предпросмотре", "H2"),
              check("Откройте версии примерно <b>320, 375, 768 px</b> и широкий экран. Таблица не должна заставлять прокручивать всю страницу по горизонтали."),
              check("Шапка и цена читаются; цифры не обрезаются; размер остаётся в левой колонке, а стоимость — в правой."),
              check("У всех строк одинаковые отступы. Заголовок и пояснение не прижаты к таблице; кнопка ниже доступна пальцем."),
              notice("Если отдельного параметра шрифта или отступа нет в вашей версии блока, оставьте ближайшее штатное значение. В этой инструкции <b>не требуются CSS, HTML или Zero Block</b>."),
              PageBreak()]

    # 4 — No price, kit, VAT or hire assumptions silently become approved data.
    story += [p("ШАГ 3 / КОММЕРЧЕСКИЕ ДАННЫЕ", "Kicker"),
              heading("Впишите цены<br/>и поясните комплектацию", "prices"),
              p("Перед заполнением согласуйте <b>единую основу цены</b>: изготовление, продажа или аренда; за что именно платит клиент; одинаков ли комплект для всех восьми размеров. Изображения конструкций этого не определяют."),
              table([["Размер (Ш × В), м", "Утверждённая цена, ₽", "Проверено"]] +
                    [[s, "________________", "☐"] for s in SIZES], [.42, .40, .18], padding=6),
              p("Что обязательно уточнить", "H2"),
              check("Цена за одну конструкцию, комплект или иной объём? Для аренды отдельно укажите срок, но не переносите условия аренды на изготовление."),
              check("Входят ли деревянный каркас, опоры, баннер и печать? Утвердите материал, сторону печати и обработку края, если они влияют на цену."),
              check("Входят ли макет, доставка, монтаж и демонтаж? Как отражается НДС — по реально согласованным условиям."),
              code_field("Шаблон пояснения под заголовком — заполнить скобки",
                         "Размеры: ширина × высота.\nЦена указана за [ЕДИНИЦА ЦЕНЫ].\nВ стоимость входит: [СОСТАВ].\nДоставка и монтаж: [УСЛОВИЯ].\nНДС: [УСЛОВИЯ]."),
              p("Числовой формат держите единым: разделяйте тысячи пробелом, валюту оставьте в шапке. Не заменяйте неизвестную цену нулём и не добавляйте «от», если минимальная комплектация не определена.", "Small"),
              notice("Если суммы ещё не готовы, <b>не публикуйте рабочие метки</b>. Либо дождитесь утверждения цен, либо согласуйте отдельный публичный вариант «По запросу» с работающей кнопкой — это уже не числовой прайс."),
              PageBreak()]

    # 5 — A functioning destination is created, never an invented live ID.
    story += [p("ШАГ 4 / ЗАЯВКА И ОБНОВЛЕНИЯ", "Kicker"),
              heading("Подключите кнопку заявки<br/>и проверьте карточки", "request"),
              p("Под таблицей поставьте отдельную кнопку <b>«Рассчитать брус-баннер»</b>. Две колонки останутся компактными; добавлять третью колонку с кнопками для этой схемы не требуется."),
              p("Вариант без программирования", "H2"),
              p("<b>1.</b> Найдите уже работающую форму заявки. Если её нет — добавьте блок из категории «Форма» и настройте поля. Минимум: имя, телефон или email, размер; можно добавить комментарий и место установки."),
              p("<b>2.</b> Непосредственно перед формой добавьте <b>T173 «Якорная ссылка»</b> из категории «Другое». В «Контенте» задайте имя без решётки:"),
              code_field("Имя якоря T173", "raschet-brus"),
              p("<b>3.</b> В поле ссылки кнопки под таблицей укажите тот же якорь с решёткой:"),
              code_field("Ссылка кнопки на этой же странице", "#raschet-brus"),
              p("Это <b>новое предлагаемое имя</b>, не существующий ID вашего сайта. Сначала создайте якорь и убедитесь, что имя не занято. Не используйте системные имена #price и #order. Переход к форме через T173 описан в справке Тильды. " + link("https://help-ru.tilda.cc/anchor", "[Справка о якорях]"), "Small"),
              p("<b>4.</b> В «Настройках сайта → Формы» подключите получателя, затем выберите его в самом блоке формы. Используйте утверждённые на сайте тексты согласий и политики обработки данных."),
              p("<b>5.</b> Проверьте отправку на опубликованной тестовой странице или в согласованное окно запуска. Должны появиться сообщение об успехе, запись в «Заявках» Tilda и, если сервис подключён, уведомление у выбранного получателя."),
              notice("Общая кнопка только переводит к форме: <b>размер и цена из строки CL46 автоматически в неё не подставляются</b> в описанной схеме. Клиент выбирает размер в форме или указывает его в комментарии."),
              p("Если рядом остаются карточки ST340C", "H2"),
              p("В этом решении CL46 заполняется вручную. Для каждого размера сверяйте <b>цену и комплектацию</b> с соответствующей карточкой. Одно изменение цены — обновить таблицу и карточку, затем заново опубликовать затронутые страницы. Автоматическая синхронизация здесь не настраивается."),
              PageBreak()]

    # 6 — A bounded, practical launch checklist and clickable official sources.
    story += [p("ШАГ 5 / КОНТРОЛЬ И ПУБЛИКАЦИЯ", "Kicker"),
              heading("Проверьте перед запуском", "publish"),
              check("Выбран <b>CL46</b>; таблица содержит 2 колонки и ровно 8 размеров в согласованном порядке. Ширина всегда указана первой."),
              check("Все цены утверждены; нет «УТОЧНИТЬ», нулевых заглушек и незаполненных квадратных скобок в публичном тексте."),
              check("Единица цены, состав, доставка, монтаж и налоговые условия понятны. При наличии ST340C значения и условия совпадают."),
              check("На телефоне включено сжатие таблицы. Текст и стоимость читаются, страница не уезжает за экран."),
              check("Кнопка ведёт к существующей форме, заголовок формы не закрывается шапкой сайта. Получатель выбран и тестовая заявка дошла."),
              check("Ответственный за прайс подтвердил версию и дату. Только после этого опубликуйте рабочую страницу."),
              p("Порядок запуска", "H2"),
              p("<b>Сохранить блок → проверить предпросмотр → утвердить цены → проверить заявку на опубликованном тесте → опубликовать рабочую страницу → открыть публичный адрес и повторить проверку.</b> Публикацию тестовой страницы и реальные тестовые заявки согласуйте с владельцем."),
              p("Если что-то отображается неправильно", "H2"),
              table([
                  ["Проблема", "Что исправить"],
                  ["Всё попало в одну колонку", "В каждой строке поставьте именно <b>;</b>, а не запятую. Новая строка — Enter. Удалите лишние пустые строки."],
                  ["Появились лишние ячейки", "Оставьте ровно один <b>;</b> на строку. Не вставляйте внутрь названий дополнительные разделители."],
                  ["Таблица шире телефона", "Включите изменение ширины на мобильных, сократите длинные пояснения в ячейках и вынесите их под таблицу."],
                  ["В таблице и карточке разные цены", "Сверьте один размер и один состав. Исправьте оба источника, сохраните и повторно опубликуйте страницу."],
              ], [.33, .67], small=True, padding=6),
              p("Официальные инструкции Тильды", "H2"),
              p(link("https://help-ru.tilda.cc/tables", "CL46: разметка, ширина колонок и мобильная версия") + "<br/>" +
                link("https://help-ru.tilda.cc/anchor", "T173: якоря и переход к форме") + "<br/>" +
                link("https://help-ru.tilda.cc/forms", "Формы: получатели данных и проверка отправки"), "Small"),
              p("Проверено по справке на 19.11.2026. Названия отдельных полей интерфейса могут меняться. Документ — инструкция по ручной настройке: никаких изменений или публикации в вашем проекте не выполнено.", "Small")]

    doc = GuideDoc(str(OUTPUT), pagesize=A4, title="Таблица стоимости стандартных брус-баннеров на Тильде — CL46",
                   author="SM Production", subject="Пошаговая настройка CL46: 8 размеров, цены, мобильная версия и заявка",
                   creator="SM Production guide builder", pageCompression=1,
                   leftMargin=MARGIN, rightMargin=MARGIN, topMargin=62, bottomMargin=49)
    doc.build(story)
    print(f"Built {OUTPUT.relative_to(FOLDER)} ({OUTPUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    build()
