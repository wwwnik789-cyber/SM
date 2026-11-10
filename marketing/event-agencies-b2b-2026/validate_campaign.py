#!/usr/bin/env python3
"""Validate the working Yandex Direct campaign package."""
from __future__ import annotations

import csv
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
DIRECT = ROOT / "yandex-direct"


def rows(name: str) -> list[dict[str, str]]:
    with (DIRECT / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def check_url(value: str) -> None:
    parsed = urlparse(value)
    assert parsed.scheme == "https" and parsed.netloc == "sm-production.ru", value


def main() -> None:
    required = [
        "campaign-structure.csv",
        "keywords.csv",
        "ads-combinatorial.csv",
        "negative-keywords.txt",
        "utm-map.csv",
        "setup-checklist.md",
    ]
    for name in required:
        assert (DIRECT / name).is_file(), name

    campaigns = rows("campaign-structure.csv")
    campaign_ids = {row["campaign_id"] for row in campaigns}
    assert campaign_ids == {"S1", "S2", "N1", "R1"}
    assert sum(int(row["monthly_budget_rub"]) for row in campaigns) == 120_000
    for row in campaigns:
        check_url(row["landing"])

    keywords = rows("keywords.csv")
    assert len(keywords) >= 55
    seen_keywords: set[str] = set()
    keyword_groups: set[tuple[str, str]] = set()
    for row in keywords:
        phrase = row["keyword"].strip().lower()
        assert phrase and phrase not in seen_keywords, phrase
        seen_keywords.add(phrase)
        assert row["campaign_id"] in {"S1", "S2"}
        assert row["intent"] in {"hot", "commercial"}
        check_url(row["landing"])
        keyword_groups.add((row["campaign_id"], row["group_id"]))

    ads = rows("ads-combinatorial.csv")
    ad_groups = {(row["campaign_id"], row["group_id"]) for row in ads}
    assert keyword_groups <= ad_groups, sorted(keyword_groups - ad_groups)
    for row in ads:
        for key in ("title_1", "title_2", "title_3", "title_4", "title_5"):
            value = row[key].strip()
            assert value and len(value) <= 56, (row["group_id"], key, len(value), value)
            assert max(map(len, value.replace("—", " ").split())) <= 22, (row["group_id"], key, value)
        for key in ("text_1", "text_2", "text_3"):
            value = row[key].strip()
            assert value and len(value) <= 81, (row["group_id"], key, len(value), value)
            assert max(map(len, value.replace("—", " ").split())) <= 23, (row["group_id"], key, value)
        assert len(row["display_link"]) <= 20, (row["group_id"], row["display_link"])
        check_url(row["url"])

    negatives = [
        line.strip().lower()
        for line in (DIRECT / "negative-keywords.txt").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(negatives) >= 40
    assert len(negatives) == len(set(negatives))

    utm_rows = rows("utm-map.csv")
    assert {row["campaign_id"] for row in utm_rows} == {"S1", "S2", "N1", "VK1", "VK2"}
    for row in utm_rows:
        final = row["final_url_template"]
        check_url(final)
        for marker in ("utm_source=", "utm_medium=", "utm_campaign=", "utm_content=", "utm_term="):
            assert marker in final, (row["campaign_id"], marker)

    print(f"Campaigns: {len(campaigns)}")
    print(f"Keyword seeds: {len(keywords)}")
    print(f"Ad groups: {len(ads)}")
    print(f"Negative phrases: {len(negatives)}")
    print("Budget: 120000 RUB")
    print("Validation: OK")


if __name__ == "__main__":
    main()
