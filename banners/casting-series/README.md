# Серия баннеров «Кастинг» — SM Production

Комплект из трёх макетов: два информационных (кастинг на пробы в кино и на
модный показ) и один брендовый («Я звезда!»). Единая мадженто-золотая гамма,
общий стиль — баннеры работают как комплект.

## Структура

```
banners/casting-series/
├── print/                     печатные мастеры, JPEG, 300 dpi
│   ├── banner-kasting-proby-v-kino-4608x8256.jpg
│   ├── banner-kasting-modnyy-pokaz-5088x7584.jpg
│   └── banner-ya-zvezda-6144x6144.jpg
├── preview/                   итоговый вид серии (для согласования и клиента)
│   ├── casting-series-contact-sheet.jpg
│   └── casting-qr-proof.jpg
└── README.md
```

Производные версии лежат отдельно, чтобы их можно было отдавать в веб
и соцсети, не таская гигабайтные мастеры:

```
public/media/banners/           веб, ширина 1400 px (JPEG + WebP)
public/media/banners/social/    1080×1920, 1080×1350, 1080×1080, 1920×1080
```

## Ключевое

**QR-код в макете «Кастинг на пробы в кино» в исходнике был декоративным и
не сканировался** — сетка была правильной (29 × 29), но данных в коде не
было. Код заменён на рабочий, ведущий на `https://model.dvkino.ru` (тот же
адрес, что и во втором макете). Подробности проверки и правок — в
[спецификации серии](../../docs/konstruktsii/banners/01_seriya-kasting-prepress.md).

## Как пересобрать

```bash
pip install pillow numpy opencv-python-headless segno zxing-cpp
python3 scripts/banners/build_banners.py
python3 scripts/banners/jfif_density.py 300 banners/casting-series/print/*.jpg
python3 scripts/banners/make_preview.py     # контактный лист + проверка QR
```

## Требования к печати

- Разрешение: 300 dpi, 4:4:4, JPEG q95
- Вылеты: 0 (печать в размер)
- Цвет: sRGB, конвертация в CMYK — на стороне типографии
- Поверх: матовый ламинат (иначе блики от фотоаппаратов на пресс-волле)
