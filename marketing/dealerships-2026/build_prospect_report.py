#!/usr/bin/env python3
"""Build the verified Moscow dealership prospect/contact PDF.

Requires ReportLab. The document reads the CRM prospect CSV and the public
employee-contact CSV from this directory, so the PDF can be regenerated after
an explicit source re-check.
"""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from typing import Iterable

from reportlab.lib.colors import Color, HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PROSPECTS_CSV = HERE / "prospects-moscow-inside-mkad.csv"
EMPLOYEES_CSV = HERE / "public-employee-contacts.csv"
OUT = HERE / "SM-Production-dealership-prospects-Moscow-2026.pdf"

W, H = A4
M = 44
CONTENT_W = W - 2 * M

BG = HexColor("#0B0D10")
BG2 = HexColor("#11151A")
CARD = HexColor("#171C22")
CARD2 = HexColor("#20262D")
IVORY = HexColor("#F5F2EA")
PAPER = HexColor("#FBFAF6")
INK = HexColor("#171A1F")
MUTED = HexColor("#6B7078")
LIGHT_MUTED = HexColor("#A5ABB3")
ACCENT = HexColor("#FF4D1C")
ACCENT_DARK = HexColor("#B63D1C")
ACID = HexColor("#D8FF3E")
BLUE = HexColor("#5FC8FF")
PURPLE = HexColor("#B39DFF")
GREEN = HexColor("#65D69A")
LINE = HexColor("#D8D6D0")
DARK_LINE = Color(1, 1, 1, alpha=0.13)

# The bundled Montserrat variable font resolves to its Thin instance in ReportLab.
# DejaVu Sans is used for the readable edition so body text remains dark and legible.
FONT_REG_PATH = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
FONT_ITALIC_PATH = FONT_REG_PATH
FONT_BOLD_PATH = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")

pdfmetrics.registerFont(TTFont("Mont", str(FONT_REG_PATH)))
pdfmetrics.registerFont(TTFont("MontI", str(FONT_ITALIC_PATH)))
pdfmetrics.registerFont(TTFont("Head", str(FONT_BOLD_PATH)))


ACCOUNT_ORDER = [
    "ACC-01", "ACC-02", "ACC-03", "ACC-04", "ACC-05", "ACC-06",
    "ACC-07", "ACC-08", "ACC-09", "ACC-10", "ACC-11",
]

ACCOUNT_NAMES = {
    "ACC-01": "AVILON",
    "ACC-02": "БорисХоф",
    "ACC-03": "АВТОМИР",
    "ACC-04": "Major",
    "ACC-05": "РОЛЬФ",
    "ACC-06": "АвтоСпецЦентр",
    "ACC-07": "FAVORIT MOTORS",
    "ACC-08": "АВТОДОМ",
    "ACC-09": "ГК «СИМ»",
    "ACC-10": "БИЗНЕС КАР",
    "ACC-11": "АвтоГЕРМЕС",
}

FIRST_WAVE = [
    ("AVILON", "№ 1", "Премиальный кластер", "Пилот одной зоны с образцами материалов и монтажом вне клиентского потока."),
    ("БорисХоф", "№ 2", "Много брендов и строений", "Один стандарт производства, отдельная маркировка комплектов по брендам и зданиям."),
    ("АВТОМИР", "№ 3 + 8", "Два плотных кластера", "Выбрать Крылатское или Дмитровку для пилота, затем тиражировать по соседним шоурумам."),
    ("Major", "№ 4 + 6", "Строгино и Тушино", "Модульный набор для запуска модели с повторным использованием конструктивной базы."),
    ("РОЛЬФ", "№ 5 + 11", "Центр и Сити", "Начать с маршрута клиента и формы «Написать директору» в РОЛЬФ Центр."),
]

STAFF_SOURCE_NOTES = {
    "https://landrover-avilon.ru/": "AVILON · команда Land Rover Волгоградский и рабочий телефон центра",
    "https://borishof.ru/dealers/borishof-hyundai/": "БорисХоф · Евгений Королёв, директор HYUNDAI Центр",
    "https://borishof.ru/dealers/borishof-genesis/": "БорисХоф · Евгений Королёв, директор GENESIS Центр и рабочий канал",
    "https://borishof.ru/dealers/borishof-volvo-tsentr/": "БорисХоф · Дмитрий Урюпин, директор VOLVO Car Центр",
    "https://ascgroup.ru/contacts/chery/chery-kashirka/advisers/": "АвтоСпецЦентр · Михаил Масенин и рабочий добавочный",
    "https://ascgroup.ru/about/": "АвтоСпецЦентр · пресс-служба, Анна Уткина и Анастасия Моисеева",
    "https://avtodom.ru/about/": "АВТОДОМ · пресс-служба, Анна Уткина и Анастасия Моисеева",
    "https://avtomir.ru/about/": "АВТОМИР · Владимир Григорьев, генеральный директор с 01.01.2026",
    "https://www.rolf.ru/news/svetlana-vinogradova-diler-kak-integrator/": "РОЛЬФ · Светлана Виноградова, генеральный директор",
    "https://favorit-motors.ru/about/book/": "FAVORIT MOTORS · Владимир Попов, основатель и президент",
    "https://business-car.ru/about/team/": "БИЗНЕС КАР · Алексей Исупов, генеральный директор",
    "https://www.avtogermes.ru/contacts/ryabinovaya/kia/": "АвтоГЕРМЕС Рябиновая · публично названные сотрудники площадки",
}


def read_semicolon_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh, delimiter=";"))


def split_long_token(token: str, font: str, size: float, width: float) -> list[str]:
    if pdfmetrics.stringWidth(token, font, size) <= width:
        return [token]
    parts: list[str] = []
    current = ""
    for char in token:
        test = current + char
        if current and pdfmetrics.stringWidth(test, font, size) > width:
            parts.append(current)
            current = char
        else:
            current = test
    if current:
        parts.append(current)
    return parts


def wrap_lines(value: str, font: str, size: float, width: float) -> list[str]:
    result: list[str] = []
    for paragraph in str(value).split("\n"):
        if not paragraph:
            result.append("")
            continue
        tokens: list[str] = []
        for raw in paragraph.split():
            tokens.extend(split_long_token(raw, font, size, width))
        current = ""
        for token in tokens:
            test = f"{current} {token}".strip()
            if not current or pdfmetrics.stringWidth(test, font, size) <= width:
                current = test
            else:
                result.append(current)
                current = token
        if current:
            result.append(current)
    return result


def clipped_lines(lines: list[str], font: str, size: float, width: float, max_lines: int | None) -> list[str]:
    if max_lines is None or len(lines) <= max_lines:
        return lines
    visible = lines[:max_lines]
    suffix = "…"
    last = visible[-1]
    while last and pdfmetrics.stringWidth(last + suffix, font, size) > width:
        last = last[:-1]
    visible[-1] = last.rstrip(" ,;:") + suffix
    return visible


def draw_text(c: canvas.Canvas, value: str, x: float, y: float, size: float = 9,
              color=INK, font: str = "Mont", align: str = "left") -> None:
    c.setFillColor(color)
    c.setFont(font, size)
    if align == "right":
        c.drawRightString(x, y, value)
    elif align == "center":
        c.drawCentredString(x, y, value)
    else:
        c.drawString(x, y, value)


def draw_wrapped(c: canvas.Canvas, value: str, x: float, y: float, width: float,
                 size: float = 9, leading: float | None = None, color=INK,
                 font: str = "Mont", max_lines: int | None = None,
                 url: str | None = None) -> float:
    leading = leading or size * 1.35
    lines = clipped_lines(wrap_lines(value, font, size, width), font, size, width, max_lines)
    c.setFillColor(color)
    c.setFont(font, size)
    for line in lines:
        c.drawString(x, y, line)
        if url and line:
            c.linkURL(url, (x, y - 2, x + min(width, pdfmetrics.stringWidth(line, font, size)), y + size + 1), relative=0)
        y -= leading
    return y


def pill(c: canvas.Canvas, label: str, x: float, y: float, fill, text_color=white,
         font: str = "Head", size: float = 6.5, pad_x: float = 9, height: float = 20) -> float:
    width = pdfmetrics.stringWidth(label, font, size) + 2 * pad_x
    c.setFillColor(fill)
    c.roundRect(x, y, width, height, height / 2, fill=1, stroke=0)
    draw_text(c, label, x + width / 2, y + (height - size) / 2 + 1.5, size, text_color, font, "center")
    return width


def card(c: canvas.Canvas, x: float, y: float, w: float, h: float, fill=PAPER,
         stroke=LINE, radius: float = 12, line_width: float = 0.7) -> None:
    c.setFillColor(fill)
    c.setStrokeColor(stroke)
    c.setLineWidth(line_width)
    c.roundRect(x, y, w, h, radius, fill=1, stroke=1)


def label(c: canvas.Canvas, value: str, x: float, y: float, color=ACCENT_DARK) -> None:
    """Small section label; deliberately no smaller than 7.2 pt."""
    draw_text(c, value.upper(), x, y, 7.2, color, "Head")


class Report:
    def __init__(self, output: Path):
        self.c = canvas.Canvas(str(output), pagesize=A4, pageCompression=1)
        self.page = 0
        self.output = output
        self.c.setTitle("Дилерские центры Москвы: проспекты и публичные контакты — читаемая версия")
        self.c.setAuthor("SM Production")
        self.c.setSubject("15 площадок внутри МКАД, 11 корпоративных аккаунтов, публичные профессиональные контакты")
        self.c.setKeywords("дилерские центры, Москва, SM Production, оформление интерьеров, контакты")

    def base(self, dark: bool = False, section: str = "") -> None:
        self.page += 1
        self.dark = dark
        self.c.setFillColor(BG if dark else IVORY)
        self.c.rect(0, 0, W, H, fill=1, stroke=0)
        if section:
            draw_text(self.c, section.upper(), M, H - 29, 7.4, ACCENT if dark else ACCENT_DARK, "Head")
        self.c.bookmarkPage(f"page-{self.page}")

    def footer(self) -> None:
        color = Color(1, 1, 1, alpha=0.52) if self.dark else HexColor("#696D73")
        self.c.setStrokeColor(DARK_LINE if self.dark else LINE)
        self.c.setLineWidth(0.7)
        self.c.line(M, 34, W - M, 34)
        draw_text(self.c, "SM PRODUCTION · ПРОВЕРЕНО 06.11.2026 · ПЕРЕД ОБРАЩЕНИЕМ ПЕРЕПРОВЕРИТЬ", M, 18, 6.2, color, "Head")
        draw_text(self.c, f"{self.page:02}", W - M, 18, 7.2, color, "Head", "right")

    def end(self, footer: bool = True) -> None:
        if footer:
            self.footer()
        self.c.showPage()

    def page_title(self, kicker: str, title: str, subtitle: str | None = None,
                   dark: bool = False) -> float:
        accent = ACCENT if dark else ACCENT_DARK
        title_color = white if dark else INK
        body_color = HexColor("#C3C8CF") if dark else MUTED
        c = self.c
        c.setStrokeColor(accent)
        c.setLineWidth(2.5)
        c.line(M, H - 68, M + 30, H - 68)
        draw_text(c, kicker.upper(), M + 42, H - 72, 7.2, accent, "Head")
        y = draw_wrapped(c, title, M, H - 108, CONTENT_W, 23.5, 28.5, title_color, "Head", 2)
        if subtitle:
            y = draw_wrapped(c, subtitle, M, y - 3, CONTENT_W, 10.2, 15.0, body_color, "Mont", 4)
        return y


def classify_color(contact_type: str):
    lower = contact_type.lower()
    if "первичный" in lower:
        return GREEN, BG
    if "локальный руководитель" in lower:
        return ACCENT, white
    if "операционный" in lower:
        return BLUE, BG
    if "коммуникации" in lower:
        return PURPLE, BG
    if "маршрутизация" in lower:
        return HexColor("#E3B866"), BG
    return HexColor("#D7D9DC"), INK


def collapse_staff(rows: list[dict[str, str]]) -> list[dict]:
    grouped_names = {"Анна Уткина", "Анастасия Моисеева"}
    result: list[dict] = []
    used: set[tuple[str, str]] = set()
    for row in rows:
        key = (row["person"], row["role"])
        if row["person"] not in grouped_names:
            item = dict(row)
            item["sources"] = [row["source_url"]]
            item["display_group"] = row["group"]
            item["display_contact"] = f'{row["public_phone"]} · {row["public_email_or_form"]}'
            result.append(item)
            continue
        if key in used:
            continue
        same = [r for r in rows if (r["person"], r["role"]) == key]
        used.add(key)
        item = dict(same[0])
        item["sources"] = [r["source_url"] for r in same]
        item["display_group"] = "АвтоСпецЦентр + АВТОДОМ"
        item["scope"] = "Пресс-службы двух групп"
        item["display_contact"] = "\n".join(
            f'{r["group"]}: {r["public_phone"]} · {r["public_email_or_form"]}' for r in same
        )
        item["recommended_use"] = (
            "Только запросить правильного владельца задачи в маркетинге; публикация в пресс-службе "
            "не означает полномочий по закупкам."
        )
        result.append(item)
    return result


def draw_metric(c: canvas.Canvas, x: float, y: float, w: float, value: str,
                caption: str, accent=ACCENT) -> None:
    card(c, x, y, w, 74, white, LINE, 11)
    draw_text(c, value, x + 16, y + 30, 24, INK, "Head")
    c.setFillColor(accent)
    c.rect(x + 16, y + 17, 28, 3, fill=1, stroke=0)
    draw_wrapped(c, caption, x + 68, y + 43, w - 84, 9.1, 12.2, MUTED, "Mont", 3)


def cover(report: Report, staff_count: int) -> None:
    report.base(dark=True)
    c = report.c
    c.setStrokeColor(Color(1, 1, 1, alpha=0.055))
    c.setLineWidth(0.5)
    for x in range(26, int(W), 34):
        c.line(x, 0, x, H)
    for y in range(34, int(H), 34):
        c.line(0, y, W, y)
    c.setStrokeColor(Color(1, 0.30, 0.11, alpha=0.5))
    c.setLineWidth(1.2)
    c.circle(W - 86, H - 164, 118, fill=0, stroke=1)
    c.circle(W - 86, H - 164, 88, fill=0, stroke=1)
    c.setFillColor(ACCENT)
    c.circle(W - 86, H - 164, 8, fill=1, stroke=0)
    c.setFillColor(Color(1, 0.30, 0.11, alpha=0.12))
    c.circle(W - 86, H - 164, 54, fill=1, stroke=0)

    draw_text(c, "SM PRODUCTION / SALES RESEARCH", M, H - 54, 8.3, ACCENT, "Head")
    draw_text(c, "ОФОРМЛЕНИЕ КОММЕРЧЕСКИХ ИНТЕРЬЕРОВ", M, H - 81, 7.4, Color(1, 1, 1, alpha=0.72), "Head")
    y = draw_wrapped(c, "Дилерские центры\nМосквы", M, H - 164, 430, 39, 47, white, "Head")
    y = draw_wrapped(c, "Проверенный список площадок и публичных профессиональных контактов", M, y - 8, 410, 14.5, 20, ACCENT, "Head", 3)
    draw_wrapped(c, "Строго внутри МКАД · приоритизация для POS, запусков моделей, зон выдачи, навигации, фасадов и монтажа вне клиентского потока.", M, y - 30, 430, 10.8, 16.2, Color(1, 1, 1, alpha=0.80), "Mont", 5)

    stats = [("15", "площадок"), ("11", "аккаунтов"), ("5", "в первой волне"), (str(staff_count), "публичных записей")]
    sx = M
    widths = [112, 112, 128, 135]
    for (value, caption), width in zip(stats, widths):
        c.setFillColor(CARD)
        c.setStrokeColor(DARK_LINE)
        c.roundRect(sx, 156, width, 74, 10, fill=1, stroke=1)
        draw_text(c, value, sx + 14, 190, 19, white, "Head")
        draw_wrapped(c, caption, sx + 14, 172, width - 28, 7.8, 10.3, HexColor("#C5CAD1"), "Mont", 2)
        sx += width + 8

    c.setFillColor(ACID)
    c.roundRect(M, 88, 304, 38, 8, fill=1, stroke=0)
    draw_text(c, "ВЕРСИЯ С УВЕЛИЧЕННЫМ ШРИФТОМ · 06.11.2026", M + 16, 102, 8.0, BG, "Head")
    draw_wrapped(c, "Только официальные публичные источники. Частные телефоны и предполагаемые адреса не использовались.", M, 61, 480, 8.5, 11.8, Color(1, 1, 1, alpha=0.66), "Mont", 2)
    report.end(footer=False)


def executive_summary(report: Report, prospects: list[dict], staff_rows: list[dict]) -> None:
    report.base(section="Краткий вывод")
    c = report.c
    report.page_title(
        "Рабочая база, а не каталог",
        "15 площадок — 11 корпоративных аккаунтов",
        "Не дублировать обращения к разным адресам одной группы. Сначала найти владельца задачи, затем согласовать одну площадку для пилота.",
    )
    gap = 12
    mw = (CONTENT_W - gap) / 2
    draw_metric(c, M, 572, mw, "15", "физических адресов строго внутри МКАД")
    draw_metric(c, M + mw + gap, 572, mw, "11", "дедуплицированных корпоративных аккаунтов", BLUE)
    draw_metric(c, M, 486, mw, "8 / 7", "площадок в волнах A / B", PURPLE)
    draw_metric(c, M + mw + gap, 486, mw, str(len(staff_rows)), "публичных записей о сотрудниках", GREEN)

    col_w = (CONTENT_W - 14) / 2
    card(c, M, 164, col_w, 292, white, LINE, 12)
    card(c, M + col_w + 14, 164, col_w, 292, white, LINE, 12)
    label(c, "Что подтверждено", M + 18, 426)
    items = [
        "официальный адрес и нахождение внутри МКАД;",
        "корпоративный телефон, e-mail или форма;",
        "коммерческий повод: POS, запуск, навигация, фасад;",
        "роль для первого запроса и персональный угол;",
        "правило дедупликации по группе.",
    ]
    yy = 397
    for item in items:
        c.setFillColor(ACCENT)
        c.circle(M + 22, yy + 4, 2.5, fill=1, stroke=0)
        yy = draw_wrapped(c, item, M + 34, yy, col_w - 54, 9.2, 13.2, INK, "Mont", 3) - 13

    x2 = M + col_w + 14
    label(c, "Первый звонок", x2 + 18, 426)
    draw_wrapped(c, "Не продавать «всё оформление» сразу. Предложить один измеримый пилот: конкретная зона, дата, состав носителей и монтаж под режим салона.", x2 + 18, 394, col_w - 36, 11.0, 16.2, INK, "Head", 7)
    c.setFillColor(IVORY)
    c.roundRect(x2 + 18, 188, col_w - 36, 105, 9, fill=1, stroke=0)
    label(c, "Формула", x2 + 32, 266)
    draw_wrapped(c, "Площадка → повод → пилот одной зоны → ответственный → смета и срок → тираж по группе.", x2 + 32, 239, col_w - 64, 9.2, 13.2, MUTED, "Mont", 5)

    c.setFillColor(BG2)
    c.roundRect(M, 68, CONTENT_W, 74, 12, fill=1, stroke=0)
    draw_text(c, "ВАЖНО", M + 18, 118, 7.2, ACID, "Head")
    draw_wrapped(c, "Названный сотрудник не автоматически отвечает за закупки. PR/коммуникации — только для корректной маршрутизации.", M + 18, 96, CONTENT_W - 36, 9.7, 13.7, white, "Mont", 3)
    report.end()


def draw_priority_card(c: canvas.Canvas, item: tuple[str, str, str, str], number: int,
                       top: float, h: float = 150) -> None:
    name, ranks, why, ask = item
    y = top - h
    card(c, M, y, CONTENT_W, h, CARD, DARK_LINE, 13)
    c.setFillColor(ACCENT)
    c.roundRect(M + 16, y + 28, 58, h - 56, 10, fill=1, stroke=0)
    draw_text(c, f"{number:02}", M + 45, y + h / 2 - 5, 17, white, "Head", "center")
    draw_text(c, name, M + 92, top - 36, 15, white, "Head")
    draw_text(c, ranks, W - M - 18, top - 34, 8.8, ACCENT, "Head", "right")
    draw_text(c, why, M + 92, top - 61, 9.4, ACID, "Head")
    draw_wrapped(c, ask, M + 92, top - 88, CONTENT_W - 126, 10.1, 14.5, HexColor("#D0D4DA"), "Mont", 4)


def priority_pages(report: Report) -> None:
    chunks = [FIRST_WAVE[:3], FIRST_WAVE[3:]]
    number = 1
    for page_idx, chunk in enumerate(chunks, start=1):
        report.base(dark=True, section="Приоритеты")
        c = report.c
        report.page_title(
            f"Первая волна · {page_idx}/2",
            "Пять аккаунтов — восемь площадок",
            "Начать с аккаунта, а не с адреса. Цель — разрешение отправить короткую презентацию и выбор площадки для пилота.",
            dark=True,
        )
        top = 630
        for item in chunk:
            draw_priority_card(c, item, number, top)
            number += 1
            top -= 166
        if page_idx == 2:
            c.setFillColor(ACID)
            c.roundRect(M, 180, CONTENT_W, 102, 12, fill=1, stroke=0)
            draw_text(c, "РЕЗУЛЬТАТ ПЕРВОГО КОНТАКТА", M + 18, 250, 7.5, BG, "Head")
            draw_wrapped(c, "Имя владельца задачи · разрешённый канал · выбранный адрес пилота · дата следующего шага.", M + 18, 220, CONTENT_W - 36, 11.0, 15.5, BG, "Head", 4)
        report.end()


def account_map_pages(report: Report, prospects: list[dict], employee_rows: list[dict]) -> None:
    by_account: dict[str, list[dict]] = defaultdict(list)
    for p in prospects:
        by_account[p["account_id"]].append(p)
    employee_by_account: dict[str, list[dict]] = defaultdict(list)
    for e in employee_rows:
        employee_by_account[e["account_id"]].append(e)
    chunks = [ACCOUNT_ORDER[:6], ACCOUNT_ORDER[6:]]
    for page_idx, chunk in enumerate(chunks, start=1):
        report.base(section="Дедупликация")
        c = report.c
        report.page_title(
            f"Аккаунты {page_idx}/2",
            "Один вход в группу — затем локальный пилот",
            "Площадки одной группы не получают два одинаковых холодных письма. Карточки показывают единицу работы CRM.",
        )
        top = 650
        for account_id in chunk:
            rows = by_account[account_id]
            names = employee_by_account.get(account_id, [])
            ranks = ", ".join(p["rank"] for p in rows)
            wave = rows[0]["wave"]
            role = rows[0]["recommended_role"].split("/")[0].strip()
            name_text = ", ".join(dict.fromkeys(e["person"] for e in names)) if names else "Профильное имя не подтверждено"
            y = top - 92
            card(c, M, y, CONTENT_W, 92, white, LINE, 10)
            draw_text(c, ACCOUNT_NAMES[account_id], M + 16, top - 28, 12.4, INK, "Head")
            draw_text(c, f"ПЛОЩАДКИ № {ranks}", M + 16, top - 53, 7.4, MUTED, "Head")
            wave_color = ACCENT if wave == "A" else BLUE
            pill(c, f"ВОЛНА {wave}", M + 16, y + 13, wave_color, white if wave == "A" else BG, size=7.0, pad_x=10, height=22)
            right_x = M + 190
            label(c, "Первый вход", right_x, top - 23)
            draw_wrapped(c, role, right_x, top - 40, CONTENT_W - 206, 8.8, 11.5, MUTED, "Mont", 2)
            label(c, "Публичные имена", right_x, top - 68)
            draw_wrapped(c, name_text, right_x, top - 83, CONTENT_W - 206, 8.4, 10.6, INK if names else MUTED, "Mont", 1)
            top -= 101
        if page_idx == 2:
            draw_wrapped(c, "Имя, опубликованное на официальном сайте, не равно закупочному контакту. Для Major и ГК «СИМ» профильное имя на текущих официальных страницах не подтверждено.", M, 92, CONTENT_W, 9.2, 13.2, MUTED, "Mont", 4)
        report.end()


def staff_guide(report: Report) -> None:
    report.base(dark=True, section="Сотрудники")
    c = report.c
    report.page_title(
        "Как использовать публичные имена",
        "Персонализация без домыслов",
        "ФИО помогает пройти ресепшн. Оно не подтверждает бюджет, закупочную функцию или согласие на рассылку.",
        dark=True,
    )
    types = [
        (GREEN, "Профильный", "Маркетинг площадки", "Попросить соединить по имени; предложить пилот и получить разрешение на материалы."),
        (ACCENT, "Локальный", "Директор / операционный руководитель", "Подтвердить актуальность, ограничения объекта и правильного владельца бюджета."),
        (PURPLE, "Маршрутизация", "PR / коммуникации / другой отдел", "Только спросить, кому адресовать предложение. Не отправлять КП как в закупки."),
    ]
    top = 650
    for color, head, sub, body in types:
        y = top - 105
        card(c, M, y, CONTENT_W, 105, CARD, DARK_LINE, 12)
        c.setFillColor(color)
        c.circle(M + 28, y + 53, 8, fill=1, stroke=0)
        draw_text(c, head, M + 52, top - 34, 12.5, white, "Head")
        draw_text(c, sub, M + 52, top - 58, 8.8, color, "Head")
        draw_wrapped(c, body, M + 230, top - 36, CONTENT_W - 248, 9.5, 13.5, HexColor("#D0D4DA"), "Mont", 4)
        top -= 118

    card(c, M, 96, CONTENT_W, 185, CARD, DARK_LINE, 13)
    draw_text(c, "ПЯТЬ ПРАВИЛ", M + 18, 252, 7.5, ACID, "Head")
    rules = [
        "Называть официальный источник.",
        "Не угадывать e-mail по домену.",
        "У PR-контакта просить только маршрут.",
        "У директора уточнять владельца бюджета.",
        "Перед звонком заново открыть источник.",
    ]
    yy = 221
    for idx, rule in enumerate(rules, start=1):
        c.setFillColor(ACCENT)
        c.circle(M + 28, yy + 4, 10, fill=1, stroke=0)
        draw_text(c, str(idx), M + 28, yy + 1, 7.0, white, "Head", "center")
        draw_text(c, rule, M + 50, yy, 9.5, white, "Mont")
        yy -= 29
    report.end()


def draw_staff_card(c: canvas.Canvas, item: dict, top: float, h: float = 255) -> None:
    y = top - h
    card(c, M, y, CONTENT_W, h, white, LINE, 12)
    fill, text_color = classify_color(item["contact_type"])
    pill(c, item["contact_type"], M + 18, top - 37, fill, text_color, size=7.2, pad_x=10, height=22)
    draw_text(c, item["display_group"], W - M - 18, top - 28, 7.4, ACCENT_DARK, "Head", "right")
    source_text = "ИСТОЧНИК ↗" if len(item["sources"]) == 1 else "2 ИСТОЧНИКА ↗"
    draw_text(c, source_text, W - M - 18, top - 49, 7.0, ACCENT_DARK, "Head", "right")
    for url in item["sources"]:
        c.linkURL(url, (W - M - 130, top - 57, W - M - 12, top - 37), relative=0)

    draw_text(c, item["person"], M + 18, top - 77, 16.0, INK, "Head")
    draw_wrapped(c, f'{item["role"]} · {item["scope"]}', M + 18, top - 100, CONTENT_W - 36, 9.5, 13.0, MUTED, "Mont", 2)
    label(c, "Публичный рабочий канал", M + 18, top - 145)
    draw_wrapped(c, item["display_contact"], M + 18, top - 166, CONTENT_W - 36, 9.3, 13.0, INK, "Mont", 4)
    label(c, "Рекомендованное использование", M + 18, top - 214)
    draw_wrapped(c, item["recommended_use"], M + 18, top - 235, CONTENT_W - 36, 9.0, 12.8, MUTED, "Mont", 3)


def staff_pages(report: Report, staff: list[dict]) -> None:
    per_page = 2
    total_pages = (len(staff) + per_page - 1) // per_page
    for page_index in range(total_pages):
        report.base(section="Публичные сотрудники")
        c = report.c
        chunk = staff[page_index * per_page:(page_index + 1) * per_page]
        report.page_title(
            f"Карточки {page_index + 1}/{total_pages}",
            "Публичные профессиональные контакты",
            "Канал указан ровно в опубликованном виде: персональный, общий центр, корпоративная почта или форма.",
        )
        top = 620
        for item in chunk:
            draw_staff_card(c, item, top)
            top -= 273
        report.end()


def account_staff_line(account_id: str, employees: list[dict]) -> str:
    rows = [e for e in employees if e["account_id"] == account_id]
    if not rows:
        return "Профильное имя не подтверждено — просить роль через официальный канал."
    relevant = [e for e in rows if "Контекст" not in e["contact_type"]]
    selected = relevant or rows
    names = []
    for row in selected:
        short_role = row["role"].replace("Генеральный директор ГК «БИЗНЕС КАР»", "генеральный директор")
        names.append(f'{row["person"]} — {short_role.lower()}')
    return "; ".join(names[:4]) + "."


def location_pages(report: Report, prospects: list[dict], employees: list[dict]) -> None:
    for p in prospects:
        report.base(section="Площадки")
        c = report.c
        report.page_title(
            f'Площадка № {p["rank"]} · волна {p["wave"]}',
            f'{p["group"]} · {p["location"]}',
            p["address"],
        )
        wave_color = ACCENT if p["wave"] == "A" else BLUE
        pill(c, f'ВОЛНА {p["wave"]}', M, 630, wave_color, white if p["wave"] == "A" else BG, size=7.4, pad_x=11, height=24)
        pill(c, "СТРОГО ВНУТРИ МКАД", M + 94, 630, BG2, white, size=7.2, pad_x=11, height=24)

        card(c, M, 510, CONTENT_W, 102, white, LINE, 12)
        label(c, "Коммерческий повод", M + 18, 582)
        draw_wrapped(c, p["opportunity"], M + 18, 555, CONTENT_W - 36, 10.4, 14.6, INK, "Mont", 5)

        col_w = (CONTENT_W - 14) / 2
        card(c, M, 326, col_w, 166, white, LINE, 12)
        card(c, M + col_w + 14, 326, col_w, 166, white, LINE, 12)
        label(c, "Публичный вход", M + 18, 464)
        draw_wrapped(c, p["public_phone"] + "\n" + p["public_email_or_form"], M + 18, 439, col_w - 36, 9.3, 13.0, INK, "Mont", 5)
        label(c, "Кого просить", M + 18, 378)
        draw_wrapped(c, p["recommended_role"], M + 18, 354, col_w - 36, 9.1, 12.7, MUTED, "Mont", 4)

        rx = M + col_w + 14
        label(c, "Публичные имена", rx + 18, 464)
        draw_wrapped(c, account_staff_line(p["account_id"], employees), rx + 18, 439, col_w - 36, 9.2, 13.0, INK, "Mont", 6)
        label(c, "Не дублировать", rx + 18, 378)
        draw_wrapped(c, p["duplicate_rule"], rx + 18, 354, col_w - 36, 9.0, 12.6, MUTED, "Mont", 4)

        c.setFillColor(BG2)
        c.roundRect(M, 121, CONTENT_W, 185, 13, fill=1, stroke=0)
        draw_text(c, "ПЕРСОНАЛЬНЫЙ УГОЛ", M + 20, 274, 7.5, ACID, "Head")
        draw_wrapped(c, p["first_message_angle"], M + 20, 244, CONTENT_W - 40, 11.5, 16.8, white, "Head", 8)

        draw_text(c, "ОФИЦИАЛЬНЫЙ ИСТОЧНИК ↗", M, 91, 7.2, ACCENT_DARK, "Head")
        draw_wrapped(c, p["official_url"], M, 72, CONTENT_W, 8.2, 10.8, MUTED, "Mont", 2, url=p["official_url"])
        report.end()


def draw_day_card(c: canvas.Canvas, number: str, head: str, body: str, top: float, h: float = 148) -> None:
    y = top - h
    card(c, M, y, CONTENT_W, h, CARD, DARK_LINE, 12)
    draw_text(c, number, M + 24, y + h / 2 - 6, 19, ACCENT, "Head")
    draw_text(c, head, M + 78, top - 40, 13.2, white, "Head")
    draw_wrapped(c, body, M + 78, top - 70, CONTENT_W - 102, 10.0, 14.5, HexColor("#D0D4DA"), "Mont", 5)


def action_plan_pages(report: Report) -> None:
    days = [
        ("01", "AVILON · БорисХоф · АВТОМИР", "Три групповых входа. У АВТОМИР назвать Крылатское и Дмитровку, но попросить выбрать один пилот."),
        ("02", "Major · РОЛЬФ · АвтоСпецЦентр", "Major — один звонок на два кластера. РОЛЬФ — Центр и «Написать директору». ASC — Каширка + Дубровка."),
        ("03", "FAVORIT · АВТОДОМ · СИМ", "Для АВТОДОМ PR-контакт использовать только для маршрута; не как закупки."),
        ("04", "БИЗНЕС КАР · АвтоГЕРМЕС", "Сервисные кампании и клиентская навигация; повторные звонки по обещанным срокам."),
        ("05", "Согласованные материалы", "Отправить только запрошенные презентации; зафиксировать ФИО, роль, повод, адрес пилота и дату следующего шага."),
    ]
    report.base(dark=True, section="Запуск")
    c = report.c
    report.page_title("Первые пять дней · 1/2", "Контакт → разрешение → пилот", "Нужный результат — владелец задачи, согласованный канал и следующий шаг.", dark=True)
    top = 650
    for item in days[:3]:
        draw_day_card(c, *item, top)
        top -= 166
    report.end()

    report.base(dark=True, section="Запуск")
    c = report.c
    report.page_title("Первые пять дней · 2/2", "Закрепить следующий шаг", "Не измерять успех количеством отправленных писем. Отправлять материалы только после согласия.", dark=True)
    top = 650
    for item in days[3:]:
        draw_day_card(c, *item, top, h=132)
        top -= 148
    c.setFillColor(ACCENT)
    c.roundRect(M, 105, CONTENT_W, 232, 13, fill=1, stroke=0)
    draw_text(c, "ФОРМУЛИРОВКА ДЛЯ РЕСЕПШН", M + 20, 305, 7.6, Color(1, 1, 1, alpha=0.78), "Head")
    script = (
        "Добрый день! Подскажите, пожалуйста, кто у вас отвечает за оформление дилерского центра, сезонные POS-материалы и презентации моделей? "
        "Мы — московское производство SM Production. Хотим предложить пилот для одной зоны: предварительный состав и расчёт по фотографиям, затем изготовление и монтаж под режим салона. "
        "С кем можно согласовать отправку короткой презентации?"
    )
    draw_wrapped(c, script, M + 20, 271, CONTENT_W - 40, 10.6, 15.8, white, "Mont", 10)
    report.end()


def draw_source_row(c: canvas.Canvas, idx: int, note: str, url: str, top: float, h: float = 88) -> None:
    y = top - h
    card(c, M, y, CONTENT_W, h, white, LINE, 10)
    c.setFillColor(ACCENT)
    c.circle(M + 26, y + h / 2, 14, fill=1, stroke=0)
    draw_text(c, str(idx), M + 26, y + h / 2 - 3, 7.4, white, "Head", "center")
    draw_wrapped(c, note, M + 50, top - 25, CONTENT_W - 68, 9.2, 12.2, INK, "Head", 3)
    draw_wrapped(c, url, M + 50, y + 27, CONTENT_W - 68, 8.2, 10.5, ACCENT_DARK, "Mont", 3, url=url)


def staff_sources_pages(report: Report) -> None:
    sources = list(STAFF_SOURCE_NOTES.items())
    chunks = [sources[:6], sources[6:]]
    number = 1
    for page_idx, chunk in enumerate(chunks, start=1):
        report.base(section="Источники")
        c = report.c
        report.page_title(
            f"Сотрудники {page_idx}/2",
            "Официальные страницы для ФИО и ролей",
            "Ссылки кликабельны. Если карточка исчезла или роль изменилась, запись требует повторного подтверждения.",
        )
        top = 630
        for url, note in chunk:
            draw_source_row(c, number, note, url, top)
            number += 1
            top -= 99
        report.end()


def location_sources_pages(report: Report, prospects: list[dict]) -> None:
    chunks = [prospects[:5], prospects[5:10], prospects[10:]]
    for page_idx, chunk in enumerate(chunks, start=1):
        report.base(section="Источники")
        c = report.c
        report.page_title(
            f"Площадки {page_idx}/3",
            "Официальные страницы 15 адресов",
            "В PDF указан основной URL; в Markdown-шорт-листе сохранены дополнительные страницы подтверждения.",
        )
        top = 662
        for p in chunk:
            note = f'№ {p["rank"]} · {p["group"]} · {p["location"]} · {p["address"]}'
            draw_source_row(c, int(p["rank"]), note, p["official_url"], top, h=100)
            top -= 112
        report.end()


def final_page(report: Report) -> None:
    report.base(dark=True, section="Правила использования")
    c = report.c
    report.page_title(
        "Перед каждым обращением",
        "Проверить, спросить, зафиксировать",
        "База предназначена для ручной B2B-работы. Она не заменяет актуализацию в день контакта.",
        dark=True,
    )
    cols = [
        ("ПЕРЕПРОВЕРИТЬ", ["ФИО и должность", "телефон и добавочный", "бренд и адрес", "режим работы", "актуальный повод"]),
        ("СПРОСИТЬ", ["кто владелец задачи", "можно ли прислать материалы", "какой канал разрешён", "где провести пилот", "когда вернуться"]),
        ("ЗАФИКСИРОВАТЬ", ["ФИО и роль", "группа или площадка", "следующий шаг", "дата follow-up", "отказ / запрет дубля"]),
    ]
    x = M
    y = 425
    w = (CONTENT_W - 20) / 3
    for head, items in cols:
        card(c, x, y, w, 230, CARD, DARK_LINE, 13)
        draw_text(c, head, x + 16, y + 198, 8.0, ACCENT, "Head")
        yy = y + 164
        for item in items:
            c.setFillColor(ACID)
            c.circle(x + 19, yy + 4, 2.7, fill=1, stroke=0)
            yy = draw_wrapped(c, item, x + 31, yy, w - 47, 9.0, 12.5, white, "Mont", 2) - 13
        x += w + 10

    card(c, M, 177, CONTENT_W, 210, CARD, DARK_LINE, 13)
    draw_text(c, "ЧЕГО В БАЗЕ НЕТ", M + 18, 353, 7.8, PURPLE, "Head")
    exclusions = [
        "предполагаемых e-mail по шаблону имени и домена;",
        "частных мобильных телефонов и закрытых профилей;",
        "утверждения, что PR или директор контролирует закупку;",
        "площадок на МКАД, за МКАД и в Московской области;",
        "гарантии актуальности без повторной проверки источника.",
    ]
    yy = 319
    for item in exclusions:
        draw_text(c, "—", M + 20, yy, 9.0, ACCENT, "Head")
        yy = draw_wrapped(c, item, M + 42, yy, CONTENT_W - 60, 9.2, 12.8, HexColor("#D0D4DA"), "Mont", 2) - 9

    c.setFillColor(ACID)
    c.roundRect(M, 77, CONTENT_W, 70, 11, fill=1, stroke=0)
    draw_text(c, "РАБОЧИЙ ПРИНЦИП", M + 18, 122, 7.2, BG, "Head")
    draw_wrapped(c, "Лучше 11 персонализированных контактов с разрешением на следующий шаг, чем 15 одинаковых писем без владельца задачи.", M + 18, 100, CONTENT_W - 36, 10.0, 13.7, BG, "Head", 3)
    report.end()


def build() -> Path:
    prospects = read_semicolon_csv(PROSPECTS_CSV)
    employees = read_semicolon_csv(EMPLOYEES_CSV)
    staff = collapse_staff(employees)

    report = Report(OUT)
    cover(report, len(employees))
    executive_summary(report, prospects, employees)
    priority_pages(report)
    account_map_pages(report, prospects, employees)
    staff_guide(report)
    staff_pages(report, staff)
    location_pages(report, prospects, employees)
    action_plan_pages(report)
    staff_sources_pages(report)
    location_sources_pages(report, prospects)
    final_page(report)
    report.c.save()
    return OUT


if __name__ == "__main__":
    print(build())
