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

FONT_REG_PATH = ROOT / "presentations" / "dealerships-2026" / "fonts" / "Montserrat-Variable.ttf"
FONT_ITALIC_PATH = ROOT / "presentations" / "dealerships-2026" / "fonts" / "Montserrat-Italic-Variable.ttf"
FONT_BOLD_PATH = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
if not FONT_BOLD_PATH.exists():
    FONT_BOLD_PATH = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")

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
    draw_text(c, value.upper(), x, y, 6.1, color, "Head")


class Report:
    def __init__(self, output: Path):
        self.c = canvas.Canvas(str(output), pagesize=A4, pageCompression=1)
        self.page = 0
        self.output = output
        self.c.setTitle("Дилерские центры Москвы: проспекты и публичные контакты сотрудников")
        self.c.setAuthor("SM Production")
        self.c.setSubject("15 площадок внутри МКАД, 11 корпоративных аккаунтов, публичные профессиональные контакты")
        self.c.setKeywords("дилерские центры, Москва, SM Production, оформление интерьеров, контакты")

    def base(self, dark: bool = False, section: str = "") -> None:
        self.page += 1
        self.dark = dark
        self.c.setFillColor(BG if dark else IVORY)
        self.c.rect(0, 0, W, H, fill=1, stroke=0)
        if section:
            draw_text(self.c, section.upper(), M, H - 29, 6.5, ACCENT if dark else ACCENT_DARK, "Head")
        self.c.bookmarkPage(f"page-{self.page}")

    def footer(self) -> None:
        color = Color(1, 1, 1, alpha=0.45) if self.dark else HexColor("#777B81")
        self.c.setStrokeColor(DARK_LINE if self.dark else LINE)
        self.c.setLineWidth(0.6)
        self.c.line(M, 31, W - M, 31)
        draw_text(self.c, "SM PRODUCTION · ПРОВЕРЕНО 06.11.2026 · ПЕРЕД ОБРАЩЕНИЕМ ПЕРЕПРОВЕРИТЬ", M, 17, 5.5, color, "Head")
        draw_text(self.c, f"{self.page:02}", W - M, 17, 6.5, color, "Head", "right")

    def end(self, footer: bool = True) -> None:
        if footer:
            self.footer()
        self.c.showPage()

    def page_title(self, kicker: str, title: str, subtitle: str | None = None,
                   dark: bool = False) -> float:
        accent = ACCENT if dark else ACCENT_DARK
        title_color = white if dark else INK
        body_color = LIGHT_MUTED if dark else MUTED
        c = self.c
        c.setStrokeColor(accent)
        c.setLineWidth(2.4)
        c.line(M, H - 68, M + 28, H - 68)
        draw_text(c, kicker.upper(), M + 40, H - 72, 6.5, accent, "Head")
        y = draw_wrapped(c, title, M, H - 108, CONTENT_W, 22, 27, title_color, "Head", 2)
        if subtitle:
            y = draw_wrapped(c, subtitle, M, y - 2, CONTENT_W, 8.6, 12.5, body_color, "Mont", 3)
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
    card(c, x, y, w, 82, white, LINE, 11)
    draw_text(c, value, x + 14, y + 42, 24, INK, "Head")
    c.setFillColor(accent)
    c.rect(x + 14, y + 20, 24, 3, fill=1, stroke=0)
    draw_wrapped(c, caption, x + 48, y + 27, w - 60, 7.1, 9.3, MUTED, "Mont", 3)


def cover(report: Report, staff_count: int) -> None:
    report.base(dark=True)
    c = report.c
    # Architectural grid and focus marks.
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

    draw_text(c, "SM PRODUCTION / SALES RESEARCH", M, H - 54, 7.2, ACCENT, "Head")
    draw_text(c, "ОФОРМЛЕНИЕ КОММЕРЧЕСКИХ ИНТЕРЬЕРОВ", M, H - 79, 6.3, Color(1, 1, 1, alpha=0.62), "Head")
    y = draw_wrapped(c, "Дилерские центры\nМосквы", M, H - 160, 430, 38, 45, white, "Head")
    y = draw_wrapped(c, "Проверенный список площадок и публичных профессиональных контактов", M, y - 8, 390, 14, 19, ACCENT, "Head", 3)
    draw_wrapped(c, "Строго внутри МКАД · приоритизация для POS, запусков моделей, зон выдачи, навигации, фасадов и монтажа вне клиентского потока.", M, y - 28, 420, 9.5, 14.5, Color(1, 1, 1, alpha=0.72), "Mont", 5)

    stats = [("15", "площадок"), ("11", "аккаунтов"), ("5", "в первой волне"), (str(staff_count), "публичных записей о сотрудниках")]
    sx = M
    for i, (value, caption) in enumerate(stats):
        width = 112 if i < 3 else 156
        c.setFillColor(CARD)
        c.setStrokeColor(DARK_LINE)
        c.roundRect(sx, 151, width, 70, 10, fill=1, stroke=1)
        draw_text(c, value, sx + 13, 184, 18, white, "Head")
        draw_wrapped(c, caption, sx + 13, 166, width - 24, 6.5, 8.5, LIGHT_MUTED, "Mont", 2)
        sx += width + 9

    c.setFillColor(ACID)
    c.roundRect(M, 79, 272, 34, 7, fill=1, stroke=0)
    draw_text(c, "ВЕРИФИКАЦИЯ: 6 НОЯБРЯ 2026", M + 16, 91, 7.2, BG, "Head")
    draw_wrapped(c, "Только официальные публичные источники. Частные телефоны и предполагаемые адреса не использовались.", M, 55, 470, 6.8, 9.5, Color(1, 1, 1, alpha=0.55), "Mont", 2)
    report.end(footer=False)


def executive_summary(report: Report, prospects: list[dict], staff_rows: list[dict]) -> None:
    report.base(section="Краткий вывод")
    c = report.c
    y = report.page_title(
        "Рабочая база, а не каталог",
        "15 площадок объединены в 11 корпоративных аккаунтов",
        "Главное правило — не дублировать обращения к разным адресам одной группы и сначала найти владельца задачи в маркетинге или управлении площадкой.",
    )
    gap = 8
    mw = (CONTENT_W - 3 * gap) / 4
    metrics_y = y - 92
    draw_metric(c, M, metrics_y, mw, "15", "физических адресов внутри МКАД")
    draw_metric(c, M + (mw + gap), metrics_y, mw, "11", "дедуплицированных корпоративных аккаунтов", BLUE)
    draw_metric(c, M + 2 * (mw + gap), metrics_y, mw, "8 / 7", "площадок в волнах A / B", PURPLE)
    draw_metric(c, M + 3 * (mw + gap), metrics_y, mw, str(len(staff_rows)), "публичных записей о сотрудниках", GREEN)

    box_top = metrics_y - 24
    box_h = 245
    col_w = (CONTENT_W - 14) / 2
    for x in (M, M + col_w + 14):
        card(c, x, box_top - box_h, col_w, box_h, white, LINE, 12)
    label(c, "Что уже подтверждено", M + 18, box_top - 28)
    items = [
        "точный официальный адрес и нахождение строго внутри МКАД;",
        "публичный корпоративный телефон, e-mail или форма;",
        "коммерческий повод: POS, запуск, зона выдачи, навигация, фасад, тираж;",
        "роль для первого запроса и персонализированный угол обращения;",
        "правило дедупликации для групп с несколькими площадками.",
    ]
    yy = box_top - 55
    for item in items:
        c.setFillColor(ACCENT)
        c.circle(M + 22, yy + 3, 2.2, fill=1, stroke=0)
        yy = draw_wrapped(c, item, M + 32, yy, col_w - 51, 7.8, 11.6, INK, "Mont", 3) - 9

    x2 = M + col_w + 14
    label(c, "Рекомендация на первый звонок", x2 + 18, box_top - 28)
    draw_wrapped(c, "Не продавать «всё оформление» сразу. Предложить один измеримый пилот: конкретная зона, дата, состав носителей и монтаж под режим салона.", x2 + 18, box_top - 57, col_w - 36, 10.2, 15, INK, "Head", 6)
    c.setFillColor(IVORY)
    c.roundRect(x2 + 18, box_top - 204, col_w - 36, 84, 9, fill=1, stroke=0)
    label(c, "Формула", x2 + 32, box_top - 143)
    draw_wrapped(c, "Площадка → ближайший повод → пилот одной зоны → ответственный → смета и срок → тираж по группе.", x2 + 32, box_top - 165, col_w - 64, 8.2, 11.8, MUTED, "Mont", 5)

    c.setFillColor(BG2)
    c.roundRect(M, 62, CONTENT_W, 86, 12, fill=1, stroke=0)
    draw_text(c, "КЛЮЧЕВОЕ ОГРАНИЧЕНИЕ", M + 18, 120, 6.3, ACID, "Head")
    draw_wrapped(c, "Названный сотрудник не автоматически отвечает за закупки. PR/коммуникации используются только для корректной маршрутизации; персональные адреса не выводились по шаблону.", M + 18, 98, CONTENT_W - 36, 9.2, 13.2, white, "Mont", 4)
    report.end()


def priority_page(report: Report) -> None:
    report.base(dark=True, section="Приоритеты")
    c = report.c
    report.page_title(
        "Первая волна",
        "Пять аккаунтов — восемь площадок",
        "Начать с аккаунта, а не с адреса. Цель первого контакта — разрешение отправить короткую презентацию и выбор площадки для пилота.",
        dark=True,
    )
    top = 657
    for i, (name, ranks, why, ask) in enumerate(FIRST_WAVE, start=1):
        h = 104
        y = top - h
        c.setFillColor(CARD)
        c.setStrokeColor(DARK_LINE)
        c.roundRect(M, y, CONTENT_W, h, 13, fill=1, stroke=1)
        c.setFillColor(ACCENT)
        c.roundRect(M + 14, y + 20, 52, 64, 9, fill=1, stroke=0)
        draw_text(c, f"{i:02}", M + 40, y + 48, 15, white, "Head", "center")
        draw_text(c, name, M + 82, y + 70, 13, white, "Head")
        draw_text(c, ranks, W - M - 18, y + 72, 7, ACCENT, "Head", "right")
        draw_text(c, why, M + 82, y + 50, 7.4, ACID, "Head")
        draw_wrapped(c, ask, M + 82, y + 27, CONTENT_W - 116, 7.8, 11.3, LIGHT_MUTED, "Mont", 3)
        top = y - 10
    report.end()


def account_map(report: Report, prospects: list[dict], employee_rows: list[dict]) -> None:
    report.base(section="Дедупликация")
    c = report.c
    report.page_title(
        "11 корпоративных аккаунтов",
        "Один вход в группу — затем локальный пилот",
        "Площадки одной группы не получают два одинаковых холодных письма. Таблица показывает правильную единицу работы CRM.",
    )
    by_account: dict[str, list[dict]] = defaultdict(list)
    for p in prospects:
        by_account[p["account_id"]].append(p)
    employee_by_account: dict[str, list[dict]] = defaultdict(list)
    for e in employee_rows:
        employee_by_account[e["account_id"]].append(e)

    x = M
    top = 652
    row_h = 46
    cols = [0, 112, 170, 206, 346, CONTENT_W]
    c.setFillColor(BG2)
    c.roundRect(x, top, CONTENT_W, 30, 7, fill=1, stroke=0)
    headers = ["АККАУНТ", "№", "ВОЛНА", "ПЕРВЫЙ ВХОД", "ИМЕНА"]
    for idx, head in enumerate(headers):
        draw_text(c, head, x + cols[idx] + 8, top + 11, 5.7, white, "Head")

    for index, account_id in enumerate(ACCOUNT_ORDER):
        rows = by_account[account_id]
        y = top - (index + 1) * row_h
        fill = white if index % 2 == 0 else PAPER
        c.setFillColor(fill)
        c.setStrokeColor(LINE)
        c.rect(x, y, CONTENT_W, row_h, fill=1, stroke=1)
        ranks = ", ".join(p["rank"] for p in rows)
        wave = rows[0]["wave"]
        role = rows[0]["recommended_role"].split("/")[0].strip()
        names = employee_by_account.get(account_id, [])
        name_text = ", ".join(dict.fromkeys(e["person"] for e in names)) if names else "не подтверждены"
        draw_wrapped(c, ACCOUNT_NAMES[account_id], x + 8, y + 27, 98, 7.2, 9.2, INK, "Head", 2)
        draw_text(c, ranks, x + cols[1] + 8, y + 24, 7.2, MUTED, "Head")
        wave_color = ACCENT if wave == "A" else BLUE
        pill(c, wave, x + cols[2] + 7, y + 13, wave_color, white if wave == "A" else BG, size=6.4, pad_x=8, height=20)
        draw_wrapped(c, role, x + cols[3] + 7, y + 29, cols[4] - cols[3] - 14, 6.4, 8.3, MUTED, "Mont", 3)
        draw_wrapped(c, name_text, x + cols[4] + 7, y + 29, CONTENT_W - cols[4] - 14, 6.3, 8.2, INK if names else MUTED, "Mont", 3)

    draw_wrapped(c, "Имена в правом столбце опубликованы официально, но статус «имя найдено» не равен статусу «закупочный контакт». Для Major и ГК «СИМ» профильное имя на текущих официальных страницах не подтверждено.", M, 92, CONTENT_W, 7.3, 10.5, MUTED, "Mont", 4)
    report.end()


def staff_guide(report: Report) -> None:
    report.base(dark=True, section="Сотрудники")
    c = report.c
    report.page_title(
        "Как использовать публичные имена",
        "Персонализация без домыслов",
        "ФИО помогает пройти ресепшн и сформулировать релевантный запрос. Оно не подтверждает бюджет, закупочную функцию или согласие на рассылку.",
        dark=True,
    )
    types = [
        (GREEN, "Профильный", "Маркетинг площадки", "Попросить соединить по имени; предложить короткий пилот и получить разрешение на материалы."),
        (ACCENT, "Локальный", "Директор / операционный руководитель", "Подтвердить актуальность, ограничения объекта и правильного владельца бюджета."),
        (PURPLE, "Маршрутизация", "PR / коммуникации / другой отдел", "Только спросить, кому адресовать предложение. Не отправлять КП как в закупки."),
    ]
    x = M
    y = 490
    w = (CONTENT_W - 20) / 3
    for color, head, sub, body in types:
        card(c, x, y, w, 172, CARD, DARK_LINE, 13)
        c.setFillColor(color)
        c.circle(x + 25, y + 140, 7, fill=1, stroke=0)
        draw_text(c, head, x + 42, y + 136, 11, white, "Head")
        draw_wrapped(c, sub, x + 18, y + 109, w - 36, 7.2, 10, color, "Head", 2)
        draw_wrapped(c, body, x + 18, y + 77, w - 36, 7.5, 11, LIGHT_MUTED, "Mont", 5)
        x += w + 10

    c.setFillColor(CARD)
    c.setStrokeColor(DARK_LINE)
    c.roundRect(M, 124, CONTENT_W, 310, 14, fill=1, stroke=1)
    draw_text(c, "ПЯТЬ ПРАВИЛ", M + 20, 398, 6.5, ACID, "Head")
    rules = [
        "Называть источник: «Увидели на официальной странице, что вы отвечаете за…».",
        "Не угадывать e-mail по домену и не переносить частный телефон из неофициального профиля.",
        "У PR-контакта просить маршрут, а не утверждать, что он отвечает за закупку.",
        "У директора центра уточнять владельца задачи и бренд-правила до расчёта.",
        "Перед звонком открыть источник заново: команды дилеров меняются быстро.",
    ]
    yy = 360
    for idx, rule in enumerate(rules, start=1):
        c.setFillColor(ACCENT)
        c.circle(M + 30, yy + 4, 11, fill=1, stroke=0)
        draw_text(c, str(idx), M + 30, yy + 1, 6.5, white, "Head", "center")
        yy = draw_wrapped(c, rule, M + 54, yy, CONTENT_W - 78, 8.4, 12.2, white, "Mont", 3) - 15
    report.end()


def draw_staff_card(c: canvas.Canvas, item: dict, x: float, top: float, w: float, h: float) -> None:
    y = top - h
    card(c, x, y, w, h, white, LINE, 11)
    fill, text_color = classify_color(item["contact_type"])
    pill(c, item["contact_type"], x + 14, top - 30, fill, text_color, size=5.8, pad_x=8, height=18)
    draw_text(c, item["display_group"], x + w - 14, top - 23, 6.3, ACCENT_DARK, "Head", "right")
    source_text = "источник ↗" if len(item["sources"]) == 1 else "2 источника ↗"
    draw_text(c, source_text, x + w - 14, top - 41, 5.8, ACCENT_DARK, "Head", "right")
    for url in item["sources"]:
        c.linkURL(url, (x + w - 104, top - 48, x + w - 10, top - 31), relative=0)

    draw_text(c, item["person"], x + 14, top - 61, 12.4, INK, "Head")
    draw_wrapped(c, f'{item["role"]} · {item["scope"]}', x + 14, top - 79, w - 28, 7.0, 9.4, MUTED, "Mont", 2)
    label(c, "Публичный рабочий канал", x + 14, top - 108)
    draw_wrapped(c, item["display_contact"], x + 14, top - 122, w - 28, 7.0, 9.1, INK, "Mont", 3)
    label(c, "Рекомендованное использование", x + 14, top - 151)
    draw_wrapped(c, item["recommended_use"], x + 14, top - 165, w - 28, 6.9, 9.0, MUTED, "Mont", 2)


def staff_pages(report: Report, staff: list[dict]) -> None:
    per_page = 3
    total_pages = (len(staff) + per_page - 1) // per_page
    for page_index in range(total_pages):
        report.base(section="Публичные сотрудники")
        c = report.c
        chunk = staff[page_index * per_page:(page_index + 1) * per_page]
        report.page_title(
            f"Карточки {page_index + 1}/{total_pages}",
            "Публичные профессиональные контакты",
            "Канал указан ровно в том виде, в котором он опубликован: персональный, общий центр, корпоративная почта или форма.",
        )
        top = 680
        for item in chunk:
            draw_staff_card(c, item, M, top, CONTENT_W, 180)
            top -= 192
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
    return "; ".join(names[:4]) + ("." if names else "")


def draw_location_card(c: canvas.Canvas, p: dict, employee_rows: list[dict],
                       x: float, top: float, w: float, h: float) -> None:
    y = top - h
    card(c, x, y, w, h, white, LINE, 12)
    wave_color = ACCENT if p["wave"] == "A" else BLUE
    c.setFillColor(wave_color)
    c.roundRect(x + 14, top - 62, 48, 42, 8, fill=1, stroke=0)
    draw_text(c, f'№ {p["rank"]}', x + 38, top - 47, 10, white if p["wave"] == "A" else BG, "Head", "center")
    pill(c, f'ВОЛНА {p["wave"]}', x + w - 76, top - 34, wave_color, white if p["wave"] == "A" else BG, size=5.6, pad_x=8, height=18)
    draw_wrapped(c, f'{p["group"]} · {p["location"]}', x + 76, top - 29, w - 168, 11.2, 13, INK, "Head", 2)
    draw_wrapped(c, p["address"], x + 76, top - 56, w - 100, 6.8, 9, MUTED, "Mont", 2)
    c.setStrokeColor(LINE)
    c.line(x + 14, top - 78, x + w - 14, top - 78)

    left_x = x + 16
    left_w = 296
    right_x = x + 328
    right_w = w - 344
    label(c, "Коммерческий повод", left_x, top - 99)
    draw_wrapped(c, p["opportunity"], left_x, top - 116, left_w, 7.3, 10.3, INK, "Mont", 3)

    box_y = y + 39
    box_h = 120
    c.setFillColor(IVORY)
    c.roundRect(left_x, box_y, left_w, box_h, 9, fill=1, stroke=0)
    label(c, "Персональный угол", left_x + 12, box_y + box_h - 21)
    draw_wrapped(c, p["first_message_angle"], left_x + 12, box_y + box_h - 40, left_w - 24, 7.7, 10.8, INK, "Head", 6)

    label(c, "Публичный вход", right_x, top - 99)
    channel = p["public_phone"] + "\n" + p["public_email_or_form"]
    draw_wrapped(c, channel, right_x, top - 116, right_w, 6.6, 8.7, INK, "Mont", 4)
    label(c, "Кого просить", right_x, top - 164)
    draw_wrapped(c, p["recommended_role"], right_x, top - 181, right_w, 6.5, 8.5, MUTED, "Mont", 3)
    label(c, "Публичные имена", right_x, top - 220)
    draw_wrapped(c, account_staff_line(p["account_id"], employee_rows), right_x, top - 237, right_w, 6.3, 8.2, INK, "Mont", 3)
    label(c, "Не дублировать", right_x, top - 266)
    draw_wrapped(c, p["duplicate_rule"], right_x, top - 282, right_w, 6.2, 8.1, MUTED, "Mont", 2)

    draw_text(c, "ОФИЦИАЛЬНЫЙ ИСТОЧНИК ↗", left_x, y + 17, 5.7, ACCENT_DARK, "Head")
    c.linkURL(p["official_url"], (left_x, y + 8, left_x + 135, y + 28), relative=0)
    draw_text(c, "СТРОГО ВНУТРИ МКАД", x + w - 16, y + 17, 5.7, MUTED, "Head", "right")


def location_pages(report: Report, prospects: list[dict], employees: list[dict]) -> None:
    for page_index in range(0, len(prospects), 2):
        report.base(section="Площадки")
        c = report.c
        chunk = prospects[page_index:page_index + 2]
        start = int(chunk[0]["rank"])
        end = int(chunk[-1]["rank"])
        title = f"Площадки № {start}–{end}" if start != end else f"Площадка № {start}"
        report.page_title(
            "Карточки первого контакта",
            title,
            "Каждая карточка соединяет официальный вход, нужную роль, коммерческий повод и персонализированный первый угол.",
        )
        top = 678
        for p in chunk:
            draw_location_card(c, p, employees, M, top, CONTENT_W, 292)
            top -= 306
        report.end()


def action_plan(report: Report) -> None:
    report.base(dark=True, section="Запуск")
    c = report.c
    report.page_title(
        "Первые пять дней",
        "Контакт → разрешение → пилот",
        "Не измерять успех количеством отправленных писем. Нужный результат — имя владельца задачи, согласованный канал и следующий шаг.",
        dark=True,
    )
    days = [
        ("01", "AVILON · БорисХоф · АВТОМИР", "Три групповых входа. У АВТОМИР сразу назвать Крылатское и Дмитровку, но попросить выбрать один пилот."),
        ("02", "Major · РОЛЬФ · АвтоСпецЦентр", "Major — один звонок на два кластера. РОЛЬФ — Центр и «Написать директору». ASC — Каширка + Дубровка."),
        ("03", "FAVORIT · АВТОДОМ · СИМ", "Для АВТОДОМ PR-контакт использовать только для маршрута; не как закупки."),
        ("04", "БИЗНЕС КАР · АвтоГЕРМЕС", "Сервисные кампании и клиентская навигация; повторные звонки по обещанным срокам."),
        ("05", "Согласованные материалы", "Отправить только запрошенные презентации; зафиксировать ФИО, роль, повод, адрес пилота и дату следующего шага."),
    ]
    top = 650
    for number, head, body in days:
        y = top - 78
        c.setFillColor(CARD)
        c.setStrokeColor(DARK_LINE)
        c.roundRect(M, y, CONTENT_W, 70, 10, fill=1, stroke=1)
        draw_text(c, number, M + 22, y + 28, 15, ACCENT, "Head")
        draw_text(c, head, M + 67, y + 42, 9.3, white, "Head")
        draw_wrapped(c, body, M + 67, y + 23, CONTENT_W - 86, 6.7, 9, LIGHT_MUTED, "Mont", 3)
        top -= 82

    c.setFillColor(ACCENT)
    c.roundRect(M, 70, CONTENT_W, 152, 13, fill=1, stroke=0)
    draw_text(c, "ФОРМУЛИРОВКА ДЛЯ РЕСЕПШН", M + 18, 192, 6.3, Color(1, 1, 1, alpha=0.72), "Head")
    script = (
        "Добрый день! Подскажите, пожалуйста, кто у вас отвечает за оформление дилерского центра, сезонные POS-материалы и презентации моделей? "
        "Мы — московское производство SM Production. Хотим предложить пилот для одной зоны: предварительный состав и расчёт по фотографиям, затем изготовление и монтаж под режим салона. "
        "С кем можно согласовать отправку короткой презентации?"
    )
    draw_wrapped(c, script, M + 18, 169, CONTENT_W - 36, 8.6, 12.8, white, "Mont", 8)
    report.end()


def draw_source_row(c: canvas.Canvas, idx: int, note: str, url: str, x: float,
                    top: float, w: float, h: float = 55) -> None:
    y = top - h
    c.setFillColor(white)
    c.setStrokeColor(LINE)
    c.roundRect(x, y, w, h, 8, fill=1, stroke=1)
    c.setFillColor(ACCENT)
    c.circle(x + 22, y + h / 2, 12, fill=1, stroke=0)
    draw_text(c, str(idx), x + 22, y + h / 2 - 2.5, 6.5, white, "Head", "center")
    draw_wrapped(c, note, x + 43, y + h - 17, w - 56, 6.9, 9, INK, "Head", 2)
    draw_wrapped(c, url, x + 43, y + 16, w - 56, 5.8, 7.3, ACCENT_DARK, "Mont", 2, url=url)


def staff_sources_page(report: Report) -> None:
    report.base(section="Источники")
    c = report.c
    report.page_title(
        "Публичные сотрудники",
        "Официальные страницы, использованные для ФИО и ролей",
        "Ссылки кликабельны. Если карточка сотрудника исчезла или роль изменилась — запись нельзя использовать без повторного подтверждения.",
    )
    top = 668
    for idx, (url, note) in enumerate(STAFF_SOURCE_NOTES.items(), start=1):
        draw_source_row(c, idx, note, url, M, top, CONTENT_W, 43)
        top -= 49
    report.end()


def location_sources_pages(report: Report, prospects: list[dict]) -> None:
    chunks = [prospects[:8], prospects[8:]]
    for page_index, chunk in enumerate(chunks, start=1):
        report.base(section="Источники")
        c = report.c
        report.page_title(
            f"Площадки {page_index}/2",
            "Официальные страницы 15 адресов",
            "В PDF указан один основной официальный URL на площадку; в полном Markdown-шорт-листе сохранены дополнительные страницы подтверждения.",
        )
        top = 668
        for p in chunk:
            note = f'№ {p["rank"]} · {p["group"]} · {p["location"]} · {p["address"]}'
            draw_source_row(c, int(p["rank"]), note, p["official_url"], M, top, CONTENT_W, 60)
            top -= 68
        report.end()


def final_page(report: Report) -> None:
    report.base(dark=True, section="Правила использования")
    c = report.c
    report.page_title(
        "Перед каждым обращением",
        "Проверить, спросить, зафиксировать",
        "Эта база — стартовая карта для ручной B2B-работы. Она не предназначена для массовой рассылки и не заменяет актуализацию в день контакта.",
        dark=True,
    )
    cols = [
        ("ПЕРЕПРОВЕРИТЬ", ["ФИО и должность", "телефон и добавочный", "бренд и адрес", "режим работы", "актуальный повод"]),
        ("СПРОСИТЬ", ["кто владелец задачи", "можно ли прислать материалы", "какой канал разрешён", "где провести пилот", "когда вернуться"]),
        ("ЗАФИКСИРОВАТЬ", ["ФИО и роль", "группа или площадка", "следующий шаг", "дата follow-up", "отказ / запрет дубля"]),
    ]
    x = M
    y = 430
    w = (CONTENT_W - 20) / 3
    for head, items in cols:
        card(c, x, y, w, 230, CARD, DARK_LINE, 13)
        draw_text(c, head, x + 16, y + 198, 7, ACCENT, "Head")
        yy = y + 166
        for item in items:
            c.setFillColor(ACID)
            c.circle(x + 20, yy + 3, 2.2, fill=1, stroke=0)
            yy = draw_wrapped(c, item, x + 31, yy, w - 48, 7.8, 10.5, white, "Mont", 2) - 14
        x += w + 10

    c.setFillColor(CARD)
    c.setStrokeColor(DARK_LINE)
    c.roundRect(M, 178, CONTENT_W, 206, 13, fill=1, stroke=1)
    draw_text(c, "ЧЕГО В БАЗЕ НЕТ", M + 18, 350, 6.5, PURPLE, "Head")
    exclusions = [
        "предполагаемых e-mail по шаблону имени и домена;",
        "частных мобильных телефонов и данных из закрытых профилей;",
        "утверждения, что PR, директор или продавец контролирует закупку;",
        "площадок на МКАД, за МКАД и в Московской области;",
        "гарантии актуальности после даты проверки без повторного открытия источника.",
    ]
    yy = 320
    for item in exclusions:
        draw_text(c, "—", M + 20, yy, 8, ACCENT, "Head")
        yy = draw_wrapped(c, item, M + 40, yy, CONTENT_W - 58, 7.6, 10.8, LIGHT_MUTED, "Mont", 2) - 9

    c.setFillColor(ACID)
    c.roundRect(M, 76, CONTENT_W, 70, 11, fill=1, stroke=0)
    draw_text(c, "РАБОЧИЙ ПРИНЦИП", M + 18, 121, 6.2, BG, "Head")
    draw_wrapped(c, "Лучше 11 аккуратных персонализированных контактов с разрешением на следующий шаг, чем 15 одинаковых писем без владельца задачи.", M + 18, 100, CONTENT_W - 36, 9, 12.5, BG, "Head", 3)
    report.end()


def build() -> Path:
    prospects = read_semicolon_csv(PROSPECTS_CSV)
    employees = read_semicolon_csv(EMPLOYEES_CSV)
    staff = collapse_staff(employees)

    report = Report(OUT)
    cover(report, len(employees))
    executive_summary(report, prospects, employees)
    priority_page(report)
    account_map(report, prospects, employees)
    staff_guide(report)
    staff_pages(report, staff)
    location_pages(report, prospects, employees)
    action_plan(report)
    staff_sources_page(report)
    location_sources_pages(report, prospects)
    final_page(report)
    report.c.save()
    return OUT


if __name__ == "__main__":
    print(build())
