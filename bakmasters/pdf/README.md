# PDF для Кристины

| Файл | Страниц | Что это |
|---|---|---|
| `BAK-MASTERS-SEO.pdf` | 18 | Инструкция «что вставить и в какое поле»: Title, Description, H1, альты |
| `BAK-MASTERS-audit.pdf` | 5 | Аудит: домен `.su`, битые ссылки, дубли, порядок исправления |

## Как устроен SEO-документ

Расчёт на человека, который не работал с SEO. Одна страница сайта — один экран:

1. Заголовок страницы (Title) + путь в Тильде + текст для копирования
2. Описание (Description) + путь + текст
3. Заголовок H1 + пометка «не в настройках»

Внизу страницы — предпросмотр: как эта страница будет выглядеть в поиске.
Плюс страницы «что такое Title и Description» и «где эти поля в Тильде» со
схемой панели.

## Пересобрать

```bash
python -m venv .venv
.venv/bin/pip install reportlab fonttools pymupdf
.venv/bin/python bakmasters/build_seo_guide.py     # SEO-гайд
.venv/bin/python bakmasters/build_pdf.py           # аудит
```

`build_seo_guide.py` — отдельный скрипт, вёрстка страниц задана кодом (canvas).
Текст и данные — в списках `PAGES`, `PRODUCTS`, `ALTS`, `CHECKLIST` в начале файла.

Шрифт Montserrat нарезается из переменного TTF в `/tmp/bakmasters-fonts`,
в git бинарники шрифтов не попадают.
