# PDF для Кристины

Два файла — для отправки в мессенджер. Исходники — markdown в родительской папке.

| Файл | Страниц | Кому | Что внутри |
|---|---|---|---|
| `BAK-MASTERS-SEO.pdf` | 16 | Кристине | SEO 9 страниц + 37 товаров, альты, инструкция по Тильде, чек-лист |
| `BAK-MASTERS-audit.pdf` | 5 | Никите и Кристине | Аудит: домен `.su`, битые ссылки, дубли, порядок исправления |

## Пересобрать

```bash
python -m venv .venv
.venv/bin/pip install reportlab fonttools pymupdf
.venv/bin/python bakmasters/build_pdf.py
```

Шрифт Montserrat нарезается из переменного TTF в
`banners/anikom-arena-3000x2500-concepts/source/` во временную папку `/tmp` —
в git бинарники шрифтов не попадают.

## Правки

Текст правится в `01-seo-stranic.md` … `04-kriticheskie-oshibki.md`, потом
пересборка. Стили и вёрстка — в `build_pdf.py`.
