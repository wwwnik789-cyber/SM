# Сборка единого PDF

`build_pdf.py` собирает `../sm-production-nashi-tseny-instruction.pdf` из основной инструкции `../README.md`, ведомости ассортимента и согласованных визуализаций. Тарифы фрезеровки находятся в разделе 13 основной инструкции и переносятся в PDF без вычислений.

```bash
python -m pip install --target .arena/pdf-libs -r site_content/05_nashi-tseny-st340c/scripts/requirements.txt
PYTHONPATH=.arena/pdf-libs python site_content/05_nashi-tseny-st340c/scripts/build_pdf.py
```

Нужны шрифты DejaVu Sans, DejaVu Sans Bold и DejaVu Sans Mono в `/usr/share/fonts/truetype/dejavu/`. В PDF встраиваются кириллические шрифты; оглавление, закладки, ссылки на мебель и оригиналы визуализаций остаются кликабельными.

Генератор не публикует страницу Tilda, не рассчитывает наценки и не меняет утверждённые изображения. `.arena/` — только локальные зависимости и проверочные рендеры, в Git не добавлять.
