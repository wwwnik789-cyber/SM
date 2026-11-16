#!/usr/bin/env python3
"""Собирает PDF-инструкцию по правке страницы «Контакты».

PDF нужен, чтобы инструкцию можно было читать, печатать и передавать дальше
без интернета и без GitHub: весь код страницы лежит внутри.

    .venv/bin/python docs/kontakty-pravka/build_pdf.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "marketing"))

from pdfkit import (  # noqa: E402
    CORAL, MUTED, NAVY, NAVY_D, PAGE_H, PAGE_W, PAPER, TINT, WHITE, LINE, INK,
    CONTENT_W, ML, MR, Doc, register_fonts, wrap,
)
from reportlab.lib.colors import HexColor  # noqa: E402
from reportlab.pdfbase import pdfmetrics  # noqa: E402
from reportlab.pdfbase.ttfonts import TTFont  # noqa: E402

OUT = Path(__file__).resolve().parent / "kontakty-pravka.pdf"
MONO_SRC = Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf")

CODE_BG = HexColor("#F2F4F6")
CODE_INK = HexColor("#1E2A36")
CODE_NUM = HexColor("#A7B4C0")
ADD_BG = HexColor("#EAF6E4")
DEL_BG = HexColor("#FBEBE9")
ADD_INK = HexColor("#2F6B2A")
DEL_INK = HexColor("#8C2E26")


def register_mono() -> str:
    pdfmetrics.registerFont(TTFont("Mono", str(MONO_SRC)))
    return "Mono"


def mono_w(text: str, size: float) -> float:
    return pdfmetrics.stringWidth(text, "Mono", size)


def wrap_mono(text: str, size: float, width: float,
              numbers: bool = False) -> list:
    """Перенос по символам: код нельзя рвать по словам.

    При numbers=True возвращает пары (номер строки файла | None, текст): номер
    стоит только у первой визуальной строки, продолжения идут без него. Иначе
    счётчик врал бы и по нему нельзя было найти место в редакторе.
    """
    per_line = max(10, int(width / mono_w("M", size)))
    out: list = []
    for no, raw in enumerate(text.split("\n"), 1):
        if not raw:
            out.append((no, "") if numbers else "")
            continue
        first = True
        while len(raw) > per_line:
            out.append((no if first else None, raw[:per_line]) if numbers else raw[:per_line])
            first = False
            raw = "  " + raw[per_line:]
        out.append((no if first else None, raw) if numbers else raw)
    return out


class Pdf(Doc):
    """Тот же визуальный язык, что у остальных PDF, плюс блоки кода."""

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)

    # ── код ────────────────────────────────────────────────────────────────
    def code(self, text: str, size: float = 7.4, label: str | None = None,
             numbered: bool = False, max_lines: int | None = None,
             offset: int = 0) -> None:
        """offset — сдвиг номеров: для куска файла номера нужны настоящие, файла."""
        mono = "Mono"
        pad = 9
        inner = CONTENT_W - pad * 2 - (28 if numbered else 0)
        lines = wrap_mono(text, size, inner, numbers=numbered)
        if max_lines:
            lines = lines[:max_lines]
        leading = size * 1.52

        if label:
            # ярлык держим вместе с началом блока: минимум восемь строк кода
            self.need(26 + leading * 8)
            self.c.setFillColor(MUTED)
            self.c.setFont("Mono", 6.4)
            self.c.drawString(ML, self.y, label.upper())
            self.y -= 11

        # блок может занимать несколько страниц: рисуем полосами
        i = 0
        while i < len(lines):
            avail = self.y - MB_LOCAL
            per_page = int((avail - pad * 2) / leading)
            remaining = len(lines) - i
            if per_page < min(remaining, 8):
                self.new_page()
                continue
            chunk = lines[i:i + per_page]
            h = len(chunk) * leading + pad * 2
            top = self.y
            self.c.setFillColor(CODE_BG)
            self.c.rect(ML, top - h, CONTENT_W, h, stroke=0, fill=1)
            self.c.setFillColor(NAVY)
            self.c.rect(ML, top - h, 2.4, h, stroke=0, fill=1)

            yy = top - pad - size
            x_text = ML + pad + (28 if numbered else 0)
            for line in chunk:
                if numbered:
                    no, line = line
                    if no is not None:
                        self.c.setFillColor(CODE_NUM)
                        self.c.setFont(mono, size - 0.6)
                        self.c.drawRightString(ML + pad + 17, yy, str(no + offset))
                self.c.setFillColor(CODE_INK)
                self.c.setFont(mono, size)
                self.c.drawString(x_text, yy, line)
                yy -= leading
            self.y = top - h - 10
            i += len(chunk)
            if i < len(lines):
                self.new_page()

    def diff(self, removed: str, added: str, label: str) -> None:
        """Пара «было → стало» двумя цветными плашками."""
        mono = "Mono"
        size = 7.4
        pad = 7
        inner = CONTENT_W - pad * 2 - 12 - mono_w("− ", size)

        def block(text, bg, ink, mark):
            lines = wrap_mono(text, size, inner)
            h = len(lines) * size * 1.5 + pad * 2
            self.need(h + 8)
            top = self.y
            self.c.setFillColor(bg)
            self.c.rect(ML, top - h, CONTENT_W, h, stroke=0, fill=1)
            self.c.setFillColor(ink)
            self.c.setFont(mono, size)
            yy = top - pad - size
            for line in lines:
                self.c.drawString(ML + pad, yy, f"{mark} {line}")
                yy -= size * 1.5
            self.y = top - h - 3

        def height(text: str) -> float:
            return len(wrap_mono(text, size, inner)) * size * 1.5 + pad * 2

        total = height(removed) + height(added) + 14 if removed else height(added) + 14
        self.need(total + 10)
        self.c.setFillColor(MUTED)
        self.c.setFont(FONTS_S(), 7.4)
        self.c.drawString(ML, self.y, label.upper())
        self.y -= 13
        if removed:
            block(removed, DEL_BG, DEL_INK, "−")
        if added:
            block(added, ADD_BG, ADD_INK, "+")
        self.y -= 8

    def steps(self, items: list[str]) -> None:
        for n, text in enumerate(items, 1):
            body = wrap(text, "R", 10.3, CONTENT_W - 34)
            h = max(len(body) * 14.4, 20)
            self.need(h + 8)
            top = self.y
            self.c.setFillColor(CORAL)
            self.c.circle(ML + 9, top - 1, 9, stroke=0, fill=1)
            self.c.setFillColor(WHITE)
            self.c.setFont(FONTS_S(), 8.6)
            self.c.drawCentredString(ML + 9, top - 4, str(n))
            yy = top
            self.c.setFillColor(INK)
            self.c.setFont(FONTS_R(), 10.3)
            for line in body:
                self.c.drawString(ML + 28, yy, line)
                yy -= 14.4
            self.y = yy - 6

    def checkbox(self, text: str) -> None:
        body = wrap(text, "R", 10.3, CONTENT_W - 30)
        h = max(len(body) * 14.4, 18)
        self.need(h + 26)
        top = self.y
        self.c.setStrokeColor(HexColor("#9AA7B2"))
        self.c.setLineWidth(0.8)
        self.c.rect(ML + 1, top - 7, 8.5, 8.5, stroke=1, fill=0)
        yy = top
        self.c.setFillColor(INK)
        self.c.setFont(FONTS_R(), 10.3)
        for line in body:
            self.c.drawString(ML + 18, yy, line)
            yy -= 14.4
        self.c.setStrokeColor(LINE)
        self.c.setLineWidth(0.4)
        self.c.line(ML, yy + 8, ML + CONTENT_W, yy + 8)
        self.y = yy - 3


MB_LOCAL = 58


def FONTS_S():
    return "MS"


def FONTS_R():
    return "MR"


def main() -> int:
    register_fonts()
    register_mono()

    contacts = (ROOT / "src/pages/Contacts.jsx").read_text(encoding="utf-8")
    footer = (ROOT / "src/components/layout/Footer.jsx").read_text(encoding="utf-8")
    overlays = (ROOT / "src/components/layout/overlays.jsx").read_text(encoding="utf-8")

    d = Pdf(
        OUT,
        kicker="Инструкция по правке · контакты",
        title="Страница «Контакты»: убрать Санкт-Петербург и добавить блок производства",
        subtitle="Один адрес вместо двух, отдельный блок про цех, режим работы и запись на визит. "
                 "В этом PDF лежит весь код — его можно копировать прямо отсюда или набрать руками.",
        meta=[
            ("Проект", "sm-production.ru · новый сайт на React + Vite"),
            ("Файлов меняем", "3: страница, футер, форма заявки"),
            ("Коммит", "817b219, ветка arena/57df9bb4-sm"),
            ("Объём правки", "+315 строк, −34 строки"),
        ],
        note="Концепт-документ для внутренней работы: описывает правку кода, а не содержание сайта. "
             "Все адреса, телефоны и ссылки взяты из действующего сайта и карточки организации.",
        footer="SM-Production · правка страницы «Контакты» · внутренний документ",
    )

    # ── 1. что меняется ───────────────────────────────────────────────────
    d.h1("Что меняется")
    d.p("Страница контактов сейчас показывает два офиса — Москву и Санкт-Петербург. "
        "Остаётся один адрес: производство и офис на Остаповском проезде. "
        "Вместо второй карточки появляется полноценный блок про производство, "
        "в который можно приехать.")
    d.bullet("Уходят: адрес «Швецова, 41», телефон +7 812 985-50-21 и вторая карта.")
    d.bullet("Добавляются: карточки трёх каналов связи, адрес производства отдельным блоком, "
             "галерея цеха, шесть участков, чек-лист визита, три шага «как попасть» и FAQ.")
    d.bullet("В футере вместо петербургского адреса — режим производства.")
    d.bullet("В форме заявки тема «Визит на производство» больше не теряется.")

    d.gap(6)
    d.callout("Перед правкой сохраните копию трёх файлов: Contacts.jsx, Footer.jsx, overlays.jsx. "
              "Если что-то пойдёт не так, вернётесь к ним одной командой.")

    # ── 2. как вообще открыть код ─────────────────────────────────────────
    d.gap(10)
    d.h1("Если код в руках впервые")
    d.p("Сайт — это папка с файлами. Один файл отвечает за одну страницу: "
        "Contacts.jsx — за страницу контактов, Footer.jsx — за подвал, который виден везде. "
        "Собирать и компилировать вручную ничего не нужно: всё делает одна команда.")
    d.p("Понадобятся две бесплатные программы: Node.js — движок, который запускает сайт у вас "
        "на компьютере, и VS Code — редактор, где удобно открывать файлы.")

    d.steps([
        "Поставьте Node.js с сайта nodejs.org: версию LTS, она помечена словом «Recommended». "
        "Установка обычная — далее, далее, готово. Затем VS Code с code.visualstudio.com.",
        "Скачайте проект: на странице репозитория на GitHub зелёная кнопка «Code» → «Download ZIP». "
        "Распакуйте архив в простую папку вроде C:\\sm. Путь без русских букв избавит от половины ошибок.",
        "Откройте папку в VS Code: меню File → Open Folder. Слева появится дерево файлов. "
        "Страница контактов лежит по пути src → pages → Contacts.jsx.",
        "Включите терминал: меню Terminal → New Terminal, внизу откроется строка ввода. "
        "Наберите npm install и нажмите Enter. Это один раз, скачиваются библиотеки.",
        "Затем npm run dev. Появится адрес http://localhost:5173 — откройте его в браузере. "
        "Сайт работает у вас на компьютере, пока идёт эта команда.",
    ])

    d.callout("Пока npm run dev работает, терминал не закрывайте: остановится команда — пропадёт сайт. "
              "Останавливают сочетанием Ctrl+C. Файлы сохраняются Ctrl+S, и браузер сам показывает "
              "изменение — перезапускать ничего не нужно.")

    d.gap(4)
    d.h2("Что делаем в каждом файле")
    d.table([
        ["Файл", "Действие"],
        ["pages/Contacts.jsx", "Шаг 1: заменить содержимое целиком — Ctrl+A, затем вставить код из PDF."],
        ["layout/Footer.jsx", "Шаг 2: две точечные правки. Искать по строкам из плашек «было → стало»."],
        ["layout/overlays.jsx", "Шаг 3: вставить четыре строки в форму заявки."],
    ], widths=[1.05, 2.6])

    d.gap(2)
    d.h2("Три вещи, на которых спотыкаются")
    d.bullet("Имя файла. Contacts.jsx — с большой буквы C и с расширением .jsx. "
             "Если переименовать, соседний файл его не найдёт и сайт перестанет открываться.")
    d.bullet("Кавычки. Код различает прямые кавычки \" и «ёлочки»: не заменяйте их на красивые, "
             "даже если так аккуратнее выглядит в тексте.")
    d.bullet("Красная ошибка в браузере. Это не смертельно: в терминале будет номер строки. "
             "Ctrl+Z в редакторе отменяет последнюю правку, и страница возвращается.")

    d.gap(4)
    d.p("Можно и совсем без установки: на GitHub открыть файл, нажать карандаш, вставить текст "
        "и «Commit changes». Так удобно править текст, но посмотреть результат до публикации "
        "не получится — проверять всё равно лучше локально.", size=9.8)

    # ── 3. шаг 1 ──────────────────────────────────────────────────────────
    # шаг начинается с новой страницы: код занимает семь страниц подряд
    d.new_page()
    d.h1("Шаг 1. Заменить страницу целиком")
    d.p("Файл src/pages/Contacts.jsx — 20 049 символов, 356 строк. "
        "Проще заменить содержимое полностью, чем выискивать отдельные строки: "
        "откройте файл, выделите всё (Ctrl+A), удалите и вставьте код с ниже.")
    d.gap(4)
    d.code(contacts, size=7.2, label="src/pages/Contacts.jsx — полный текст", numbered=True)

    # ── 3. шаг 2 ──────────────────────────────────────────────────────────
    d.gap(10)
    d.h1("Шаг 2. Футер: убрать питерский адрес")
    d.p("Файл src/components/layout/Footer.jsx. Две точечные правки.")

    d.h2("2.1 · Импорт иконок — строка 4")
    d.diff(
        'import { Logo, Mail, MapPin, Phone, Send } from "../ui/Icons";',
        'import { Clock, Logo, Mail, MapPin, Phone, Send } from "../ui/Icons";',
        "Было → стало",
    )

    d.h2("2.2 · Нижняя строка с адресами")
    d.p("Ближе к концу файла три строки подряд: адрес Москвы, адрес СПб и телефон. "
        "Первые две меняются так:", size=10.2)
    d.diff(
        '<p className="flex items-center gap-2"><MapPin size={14} /> Москва, Остаповский проезд, 9 с13</p>\n'
        '<p className="flex items-center gap-2 md:justify-center"><MapPin size={14} /> СПб, ул. Швецова, 41 лит. А</p>',
        '<Link to="/kontakty" className="flex items-center gap-2 hover:text-ink"><MapPin size={14} /> Москва, Остаповский проезд, 9 с13</Link>\n'
        '<p className="flex items-center gap-2 md:justify-center"><Clock size={14} /> Производство ежедневно 9:00–22:00</p>',
        "Было → стало",
    )
    d.p("Третья строка с телефоном остаётся без изменений.", size=10.2)

    # ── 4. шаг 3 ──────────────────────────────────────────────────────────
    d.new_page()
    d.h1("Шаг 3. Форма заявки: показать тему визита")
    d.p("Файл src/components/layout/overlays.jsx. Без этой правки кнопка «Записаться на визит» "
        "откроет форму, но тема не подсветится: в списке типовых тем «Визит на производство» нет.")
    d.p("Найдите блок step === 0 и добавьте четыре строки перед перебором тем:", size=10.2)
    d.diff(
        "",
        "{topic && !TOPICS.includes(topic) && (\n"
        "  <button className=\"rounded-xl border border-accent bg-accent px-4 py-2.5 text-sm font-semibold text-white\">\n"
        "    {topic}\n"
        "  </button>\n"
        ")}",
        "Вставить внутрь <div className=\"flex flex-wrap gap-2\">, до {TOPICS.map(...)}",
    )

    # ── 5. проверка ───────────────────────────────────────────────────────
    d.new_page()
    d.h1("Шаг 4. Проверить")
    d.p("Запустите проект и откройте страницу /kontakty.")
    d.code("npm install\nnpm run dev\n# затем в браузере: http://localhost:5173/kontakty", size=8.4)
    d.gap(6)
    d.p("Чек-лист. Если все пункты совпали — страница собрана правильно.", size=10.2)
    for item in [
        "В тексте нет «Санкт-Петербург», «СПб», «Швецова» и телефона +7 812.",
        "Вверху три кнопки: телефон, почта, Telegram — все кликаются.",
        "Блок «Наш адрес в Москве»: Остаповский проезд, 24/7, производство 9:00–22:00.",
        "«Построить маршрут» открывает Яндекс Карты, «Карточка в Яндекс Картах» — карточку организации.",
        "«Записаться на визит» открывает форму с уже выбранной темой.",
        "Блок «Цех, в который можно приехать»: три фото и четыре счётчика — 6, 3 ч, 24/7, 300+.",
        "Шесть карточек участков и три шага «Как попасть в цех» на месте.",
        "Аккордеон с четырьмя вопросами раскрывается.",
        "В футере вместо адреса СПб — «Производство ежедневно 9:00–22:00».",
        "Сборка проходит без ошибок: npm run build.",
    ]:
        d.checkbox(item)

    # ── 6. где остался Питер ──────────────────────────────────────────────
    # раздел с таблицей не рвём между страницами: места нужно ~300 pt
    d.need(330)
    d.gap(10)
    d.h1("Что осталось про Питер в других местах")
    d.p("На странице контактов Санкт-Петербурга больше нет, но он встречается ещё в шести местах. "
        "Их я не трогал: непонятно, цех закрылся или переехал, а формулировка зависит от этого.")
    d.table([
        ["Где", "Что написано"],
        ["index.html", "Заголовок сайта: «…в Москве и СПб». Перебивает заголовок страницы для поиска и соцсетей."],
        ["Footer.jsx", "Описание компании: «Москва и Санкт-Петербург»."],
        ["About.jsx", "«750 м² в Москве и Санкт-Петербурге»."],
        ["Production.jsx", "«Москва и Санкт-Петербург, 750 м²»."],
        ["data/faq.js, data/team.js", "Визит в СПб и «открытие цеха в Санкт-Петербурге» в истории компании."],
        ["data/blog.js", "Два упоминания в статьях."],
    ], widths=[1, 2.6])

    d.gap(2)
    d.callout("Почему «750 м²» заменено на «6 участков»: 750 м² — сумма по двум городам. "
              "Для страницы про московский цех такая цифра вводила бы в заблуждение. "
              "Как только будет площадь московского цеха, поставлю точную.")

    d.save()
    print(f"  размер: {OUT.stat().st_size:,} байт".replace(",", " "))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
