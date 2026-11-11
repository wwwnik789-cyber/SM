#!/usr/bin/env python3
"""Собирает src/data/blog-ng2027.js из markdown-статей этого каталога.

Markdown — единственный источник текста. Правьте статьи в blog/*.md и
перезапускайте скрипт: JS-модуль сайта пересоберётся, расхождений не будет.

Запуск из корня репозитория:
    python3 marketing/novogodnee-oformlenie-2027/content/build_blog_data.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
BLOG_DIR = HERE / "blog"
OUT = REPO / "src/data/blog-ng2027.js"

WORDS_PER_MINUTE = 165
META_RE = re.compile(r"^- \*\*(?P<key>[^*]+?)\*\*:?\s*(?P<value>.*)$")


def parse_meta(lines: list[str]) -> dict[str, str]:
    meta: dict[str, str] = {}
    for line in lines:
        m = META_RE.match(line.strip())
        if not m:
            continue
        key = m.group("key").strip().rstrip(":").strip()
        value = m.group("value").strip()
        # Убираем счётчик длины в скобках: "SEO title (62)" -> "SEO title"
        key = re.sub(r"\s*\(\d+\)$", "", key).strip()
        meta[key.lower()] = value
    return meta


def split_article(text: str) -> tuple[list[str], list[str]]:
    lines = text.splitlines()
    try:
        sep = lines.index("---")
    except ValueError:
        raise SystemExit("Нет разделителя --- между метаданными и текстом")
    return lines[:sep], lines[sep + 1 :]


def blocks_from_body(lines: list[str]) -> list[dict]:
    blocks: list[dict] = []
    para: list[str] = []
    bullets: list[str] = []

    def flush_para() -> None:
        nonlocal para
        if para:
            blocks.append({"p": " ".join(para).strip()})
            para = []

    def flush_list() -> None:
        nonlocal bullets
        if bullets:
            blocks.append({"list": list(bullets)})
            bullets = []

    for raw in lines:
        line = raw.strip()
        if not line:
            flush_para()
            flush_list()
            continue
        if line.startswith("## "):
            flush_para()
            flush_list()
            blocks.append({"h": line[3:].strip()})
            continue
        if line.startswith("- "):
            flush_para()
            bullets.append(line[2:].strip())
            continue
        flush_list()
        para.append(line)

    flush_para()
    flush_list()
    return blocks


def clean(value: str) -> str:
    value = value.replace("`", "")
    return value.strip()


def read_minutes(blocks: list[dict]) -> int:
    words = 0
    for b in blocks:
        if "p" in b:
            words += len(b["p"].split())
        if "h" in b:
            words += len(b["h"].split())
        if "list" in b:
            words += sum(len(x.split()) for x in b["list"])
    return max(4, round(words / WORDS_PER_MINUTE))


def js_str(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def build_post(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    meta_lines, body_lines = split_article(text)
    meta = parse_meta(meta_lines)
    blocks = blocks_from_body(body_lines)

    title = next((l[2:].strip() for l in meta_lines if l.startswith("# ")), path.stem)
    slug = clean(meta.get("slug", ""))
    date = clean(meta.get("дата", ""))
    tag = clean(meta.get("тег", ""))
    cover = clean(meta.get("обложка", ""))
    excerpt = clean(meta.get("seo description", ""))

    missing = [k for k, v in {"slug": slug, "дата": date, "тег": tag, "обложка": cover, "seo description": excerpt}.items() if not v]
    if missing:
        raise SystemExit(f"{path.name}: не хватает полей {', '.join(missing)}")

    return {
        "slug": slug,
        "title": title,
        "date": date,
        "tag": tag,
        "read": read_minutes(blocks),
        "cover": cover,
        "excerpt": excerpt,
        "content": blocks,
    }


def render(posts: list[dict]) -> str:
    out = [
        "// Сгенерировано build_blog_data.py — не правьте руками.",
        "// Источник: marketing/novogodnee-oformlenie-2027/content/blog/*.md",
        "export const ng2027Posts = [",
    ]
    for p in posts:
        out.append("  {")
        for key in ("slug", "title", "date", "tag", "read", "cover", "excerpt"):
            out.append(f"    {key}: {js_str(p[key]) if isinstance(p[key], str) else p[key]},")
        out.append("    content: [")
        for b in p["content"]:
            if "h" in b:
                out.append(f"      {{ h: {js_str(b['h'])} }},")
            if "p" in b:
                out.append(f"      {{ p: {js_str(b['p']) } }},")
            if "list" in b:
                out.append("      { list: [")
                for item in b["list"]:
                    out.append(f"        {js_str(item)},")
                out.append("      ] },")
        out.append("    ],")
        out.append("  },")
    out.append("];")
    out.append("")
    return "\n".join(out)


def main() -> None:
    files = sorted(BLOG_DIR.glob("*.md"))
    if not files:
        raise SystemExit("В blog/ нет статей")
    posts = [build_post(f) for f in files]
    posts.sort(key=lambda p: p["date"])
    OUT.write_text(render(posts), encoding="utf-8")
    total = sum(len(b.get("p", "").split()) + sum(len(x.split()) for x in b.get("list", [])) for p in posts for b in p["content"])
    print(f"{OUT.relative_to(REPO)}: {len(posts)} статей, ~{total} слов")
    for p in posts:
        print(f"  {p['date']}  {p['read']:>2} мин  {p['slug']}")


if __name__ == "__main__":
    main()
