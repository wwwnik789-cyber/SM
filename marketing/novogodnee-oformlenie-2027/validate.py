#!/usr/bin/env python3
"""Validate the New Year 2027 campaign package before launch."""

from __future__ import annotations

import csv
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent

LIMITS = {
    "title1": 56,
    "title2": 30,
    "text": 81,
    "display_path": 20,
    "sitelink_title": 30,
    "sitelink_description": 60,
    "callout": 25,
}

# Words that must never become a standalone negative keyword: they kill good traffic.
DANGEROUS_NEGATIVES = {"купить", "фото", "заказ", "услуги", "цена", "стоимость"}

errors: list[str] = []
warnings: list[str] = []


def fail(message: str) -> None:
    errors.append(message)


def warn(message: str) -> None:
    warnings.append(message)


def read_csv(name: str) -> list[dict[str, str]]:
    path = ROOT / name
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def check_ads() -> None:
    rows = read_csv("ads.csv")
    seen: set[str] = set()
    groups: dict[str, int] = defaultdict(int)

    for row in rows:
        ad_id = row["ad_id"]
        part = row["part"]
        if ad_id in seen:
            fail(f"{ad_id}: повторяющийся id")
        seen.add(ad_id)

        if part == "объявление":
            groups[row["group_code"]] += 1
            for field in ("title1", "title2", "text"):
                value = (row.get(field) or "").strip()
                if not value:
                    fail(f"{ad_id}: пустое поле {field}")
                    continue
                if len(value) > LIMITS[field]:
                    fail(f"{ad_id}: {field} {len(value)} символов, лимит {LIMITS[field]} — «{value}»")
            for field in ("display_path_1", "display_path_2"):
                value = (row.get(field) or "").strip()
                if not value:
                    continue
                if len(value) > LIMITS["display_path"]:
                    fail(f"{ad_id}: {field} {len(value)} символов, лимит {LIMITS['display_path']}")
                if not re.fullmatch(r"[a-z0-9-]+", value):
                    fail(f"{ad_id}: {field} должен быть латиницей без пробелов — «{value}»")
        elif part == "заголовок":
            value = (row.get("title1") or "").strip()
            if len(value) > LIMITS["title1"]:
                fail(f"{ad_id}: заголовок {len(value)} символов, лимит {LIMITS['title1']}")
        elif part == "текст":
            value = (row.get("text") or "").strip()
            if len(value) > LIMITS["text"]:
                fail(f"{ad_id}: текст {len(value)} символов, лимит {LIMITS['text']}")

    for group, count in sorted(groups.items()):
        if count < 2:
            warn(f"{group}: только {count} объявление, нужно минимум 2 для теста")

    forbidden = ("лучш", "№1", "номер 1", "гарантир", "100%", "самый")
    for row in rows:
        blob = " ".join((row.get(f) or "") for f in ("title1", "title2", "text")).lower()
        for word in forbidden:
            if word in blob:
                warn(f"{row['ad_id']}: рискованный оборот «{word}» — проверьте модерацию")


def check_extensions() -> None:
    rows = read_csv("extensions.csv")
    sitelinks = [r for r in rows if r["type"] == "быстрая ссылка"]
    callouts = [r for r in rows if r["type"] == "уточнение"]

    if len(sitelinks) > 8:
        fail(f"быстрых ссылок {len(sitelinks)}, максимум 8")
    for row in sitelinks:
        if len(row["title"]) > LIMITS["sitelink_title"]:
            fail(f"{row['id']}: заголовок ссылки длиннее {LIMITS['sitelink_title']}")
        if len(row["description"]) > LIMITS["sitelink_description"]:
            fail(f"{row['id']}: описание ссылки длиннее {LIMITS['sitelink_description']}")
    for row in callouts:
        if len(row["title"]) > LIMITS["callout"]:
            fail(f"{row['id']}: уточнение длиннее {LIMITS['callout']}")


def check_keywords() -> None:
    rows = read_csv("keywords.csv")
    phrases = [r["phrase"].strip().lower() for r in rows]

    duplicates = [p for p, n in Counter(phrases).items() if n > 1]
    if duplicates:
        fail(f"дубли фраз: {duplicates}")

    by_group = Counter(r["group_code"] for r in rows)
    for group, count in sorted(by_group.items()):
        if count < 3:
            warn(f"{group}: всего {count} фразы — группа слишком узкая")

    for row in rows:
        if not row["landing"].startswith("/"):
            fail(f"{row['phrase']}: адрес должен начинаться с /")
        if row["type"] == "поиск" and len(row["phrase"].split()) > 6:
            warn(f"{row['phrase']}: длинная фраза, проверьте частотность перед добавлением")


def check_negatives() -> None:
    path = ROOT / "negative-keywords.txt"
    words = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        words.append(line.lower())

    dangerous = sorted(set(words) & DANGEROUS_NEGATIVES)
    if dangerous:
        fail(f"опасные минус-слова, отсекают целевой трафик: {dangerous}")

    duplicates = [w for w, n in Counter(words).items() if n > 1]
    if duplicates:
        warn(f"дубли в минус-словах: {duplicates}")

    print(f"Минус-слов: {len(words)}")


def check_page_copy() -> None:
    text = (ROOT / "page-copy.md").read_text(encoding="utf-8")
    title = re.search(r"\*\*Title \((\d+) символ(?:ов|а)?\):\*\*\n`([^`]+)`", text)
    description = re.search(r"\*\*Description \((\d+) символ(?:ов|а)?\):\*\*\n`([^`]+)`", text)

    if not title or not description:
        fail("не найдены Title и Description в page-copy.md")
        return

    title_len = len(title.group(2))
    description_len = len(description.group(2))
    if title_len > 90:
        fail(f"Title {title_len} символов — длиннее 90")
    if not 140 <= description_len <= 170:
        warn(f"Description {description_len} символов — комфортный диапазон 140–170")

    if "`[нужны данные" not in text and "нужны данные" not in text:
        warn("в тексте нет пометок о недостающих данных — проверьте кейсы")

    print(f"Title: {title_len} символов")
    print(f"Description: {description_len} символов")


def check_creatives() -> None:
    folder = ROOT / "creatives"
    if not folder.exists():
        warn("папка creatives отсутствует")
        return
    files = sorted(folder.glob("[0-9][0-9]-*.jpg"))
    print(f"Креативов: {len(files)}")
    for path in files:
        if path.stat().st_size < 40_000:
            warn(f"{path.name}: подозрительно маленький файл")


def main() -> int:
    check_ads()
    check_extensions()
    check_keywords()
    check_negatives()
    check_page_copy()
    check_creatives()

    print()
    for message in warnings:
        print(f"ПРЕДУПРЕЖДЕНИЕ: {message}")
    for message in errors:
        print(f"ОШИБКА: {message}")

    if errors:
        print(f"\nПроверка не пройдена: {len(errors)} ошибок, {len(warnings)} предупреждений")
        return 1
    print(f"\nПроверка пройдена: {len(warnings)} предупреждений")
    return 0


if __name__ == "__main__":
    sys.exit(main())
