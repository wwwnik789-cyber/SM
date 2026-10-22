# ICC-профили для CMYK-версий мастеров

| Файл | Что это | Лицензия |
|------|---------|----------|
| `craft-coated-fogra39.icc` | Coated FOGRA39, подогнан под данные Fogra | CC0-1.0 (public domain) — свободное использование |
| `Coated_Fogra39L_VIGC_300.icc` | Coated FOGRA39 (L), 300 % TAC — профиль X-Rite / ECI | Copyright X-Rite, Inc. — лежит в рабочей папке, **в git не коммитится** (см. `.gitignore`) |

Выпущенные CMYK-мастера конвертированы профилем X-Rite
`Coated_Fogra39L_VIGC_300.icc` (Coated FOGRA39 (L) VIGC 300) — этот профиль
встроен в сами TIFF-файлы, типографии отдельный `.icc` не нужен.

Если типография работает на другом профиле FOGRA39 (например, `CoaFOGRA39.icc`
из набора ECI или `PSOcoated_v3`) — скажите, пересоберём CMYK в нём:

```bash
python3 scripts/banners/to_cmyk.py --profile <путь-к-профилю>.icc
```

Собрать заново с нуля (профили ECI/X-Rite скачиваются с eci.org — бесплатно,
для печати):

```bash
python3 scripts/banners/to_cmyk.py \
  --profile scripts/banners/icc/Coated_Fogra39L_VIGC_300.icc \
  --out /home/user/print-cmyk
```
