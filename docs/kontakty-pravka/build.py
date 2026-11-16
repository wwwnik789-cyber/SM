#!/usr/bin/env python3
"""Собирает автономную инструкцию по правке страницы контактов.

Один HTML-файл без внешних зависимостей: открывается двойным щелчком, код
внутри можно копировать кнопкой, шрифты и стили встроены. Нужен, чтобы правку
можно было внести руками, не открывая GitHub.

    python3 docs/kontakty-pravka/build.py
"""
from __future__ import annotations

import html
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "kontakty-pravka.html"

FILES = {
    "contacts": ROOT / "src/pages/Contacts.jsx",
    "footer": ROOT / "src/components/layout/Footer.jsx",
    "overlays": ROOT / "src/components/layout/overlays.jsx",
}

TEMPLATE = """<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Правка страницы «Контакты» — SM Production</title>
<style>
  :root {
    --ink: #14141a; --mut: #5f6068; --line: #e2ded4; --bg: #faf8f3;
    --card: #fff; --accent: #e8441a; --code-bg: #14141a; --code-ink: #e9e6dd;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; background: var(--bg); color: var(--ink);
    font: 16px/1.62 -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    -webkit-font-smoothing: antialiased;
  }
  .wrap { max-width: 980px; margin: 0 auto; padding: 0 22px 96px; }
  header.top {
    border-bottom: 1px solid var(--line); background: #fff; margin-bottom: 34px;
  }
  header.top .wrap { padding-top: 40px; padding-bottom: 34px; }
  .kicker {
    font-size: 12px; letter-spacing: .22em; text-transform: uppercase;
    color: var(--mut); margin: 0 0 14px; display: flex; align-items: center; gap: 10px;
  }
  .kicker::before {
    content: ""; width: 8px; height: 8px; background: var(--accent); transform: rotate(45deg);
  }
  h1 { font-size: 34px; line-height: 1.14; margin: 0 0 16px; letter-spacing: -.01em; }
  .lead { font-size: 17px; color: var(--mut); margin: 0; max-width: 74ch; }
  .meta {
    margin-top: 22px; display: flex; flex-wrap: wrap; gap: 8px;
  }
  .tag {
    font-size: 12.5px; border: 1px solid var(--line); border-radius: 999px;
    padding: 5px 12px; color: var(--mut); background: #fff;
  }
  h2 {
    font-size: 23px; margin: 46px 0 6px; letter-spacing: -.01em;
    display: flex; align-items: baseline; gap: 12px;
  }
  h2 .num {
    font-size: 13px; font-weight: 700; color: #fff; background: var(--accent);
    border-radius: 8px; padding: 3px 9px; letter-spacing: .04em; flex: none;
  }
  h3 { font-size: 16.5px; margin: 26px 0 8px; }
  p { margin: 10px 0; }
  .muted { color: var(--mut); }
  .card {
    background: var(--card); border: 1px solid var(--line); border-radius: 16px;
    padding: 20px 22px; margin: 16px 0;
  }
  .card.note { border-left: 3px solid var(--accent); }
  .card.warn { border-left: 3px solid #b58900; background: #fffdf3; }
  ul, ol { margin: 10px 0; padding-left: 22px; }
  li { margin: 6px 0; }
  code.inline {
    background: #efece4; border-radius: 5px; padding: 1px 6px;
    font: 13.5px/1.5 ui-monospace, "SF Mono", Menlo, Consolas, monospace;
  }
  .filepath {
    display: inline-flex; align-items: center; gap: 8px; background: #14141a; color: #f4f2ec;
    border-radius: 8px; padding: 6px 12px; margin: 8px 0 12px;
    font: 13.5px/1.4 ui-monospace, "SF Mono", Menlo, Consolas, monospace;
  }
  .codebox { position: relative; margin: 12px 0 4px; }
  pre {
    margin: 0; background: var(--code-bg); color: var(--code-ink);
    border-radius: 14px; padding: 18px 18px 20px; overflow-x: auto;
    font: 12.7px/1.55 ui-monospace, "SF Mono", Menlo, Consolas, monospace;
    tab-size: 2;
  }
  pre.small { max-height: 420px; overflow-y: auto; }
  .copy {
    position: absolute; top: 10px; right: 10px; z-index: 2;
    background: rgba(255,255,255,.1); color: #f4f2ec; border: 1px solid rgba(255,255,255,.25);
    border-radius: 8px; padding: 6px 12px; font-size: 12px; cursor: pointer;
    font-family: inherit; transition: background .2s, border-color .2s;
  }
  .copy:hover { background: rgba(255,255,255,.18); }
  .copy.done { background: #d8ff3e; color: #14141a; border-color: #d8ff3e; }
  .del { color: #ff8f7a; }
  .add { color: #b6f36a; }
  .dim { color: #8a8781; }
  table { width: 100%; border-collapse: collapse; margin: 14px 0; font-size: 15px; }
  th, td { text-align: left; padding: 10px 12px; border-bottom: 1px solid var(--line); vertical-align: top; }
  th { font-size: 12px; letter-spacing: .14em; text-transform: uppercase; color: var(--mut); }
  td:first-child { white-space: nowrap; font-weight: 600; }
  .checklist { list-style: none; padding: 0; }
  .checklist li { display: flex; gap: 10px; align-items: flex-start; padding: 7px 0; border-bottom: 1px dashed var(--line); }
  .checklist li::before {
    content: "☐"; color: var(--accent); font-size: 17px; line-height: 1.35; flex: none;
  }
  footer {
    margin-top: 60px; padding-top: 22px; border-top: 1px solid var(--line);
    color: var(--mut); font-size: 13.5px;
  }
  a { color: var(--accent); }
  @media print {
    body { background: #fff; font-size: 12pt; }
    .copy { display: none; }
    pre { background: #f4f2ec; color: #14141a; border: 1px solid #ddd; }
    header.top { border: none; }
    h2 { page-break-after: avoid; }
    .card, pre { page-break-inside: avoid; }
  }
</style>
</head>
<body>

<header class="top">
  <div class="wrap">
    <p class="kicker">Инструкция по правке</p>
    <h1>Страница «Контакты»: убрать Санкт-Петербург и добавить блок производства</h1>
    <p class="lead">
      Один файл, три небольших правки. Код можно копировать прямо отсюда кнопкой
      «Скопировать» — интернет, GitHub и доступы не нужны.
    </p>
    <div class="meta">
      <span class="tag">Ветка arena/57df9bb4-sm</span>
      <span class="tag">Коммит 817b219</span>
      <span class="tag">3 файла</span>
      <span class="tag">React + Vite + Tailwind</span>
    </div>
  </div>
</header>

<div class="wrap">

  <div class="card note">
    <strong>Коротко, что меняется.</strong>
    <ul>
      <li>Страница контактов остаётся с одним адресом — Москва, Остаповский проезд, 9&nbsp;с13. Питерский адрес, телефон <code class="inline">+7 812</code> и вторая карта уходят.</li>
      <li>Добавляется отдельный блок про производство: галерея цеха, шесть участков, чек-лист «что увидите на визите» и три шага, как попасть в цех.</li>
      <li>В футере вместо петербургского адреса — режим производства.</li>
      <li>В форме заявки тема «Визит на производство» больше не теряется.</li>
    </ul>
  </div>

  <div class="card warn">
    <strong>Перед началом — сделайте копию.</strong>
    Сохраните исходные три файла рядом с проектом или переименуйте в
    <code class="inline">Contacts.jsx.bak</code>. Если что-то пойдёт не так, вернётесь к ним одной командой.
  </div>

  <h2><span class="num">1</span> Заменить страницу целиком</h2>
  <p class="muted">
    Это самый простой путь: файл небольшой, и в нём проще заменить всё содержимое,
    чем выискивать отдельные строки.
  </p>
  <div class="filepath">src/pages/Contacts.jsx</div>
  <p>
    Откройте файл, выделите всё (<code class="inline">Ctrl+A</code>), удалите и вставьте код ниже
    (<code class="inline">Ctrl+V</code>). Сохраните.
  </p>
  <div class="codebox">
    <button class="copy" data-target="code-contacts">Скопировать</button>
    <pre id="code-contacts" class="small">{contacts}</pre>
  </div>
  <p class="muted">
    Файл целиком — {contacts_size} байт, {contacts_lines} строк. Если правите в редакторе,
    следите, чтобы не сломались кавычки: в JSX текст пишется в двойных кавычках,
    а фигурные скобки — это код.
  </p>

  <h2><span class="num">2</span> Футер: убрать питерский адрес</h2>
  <div class="filepath">src/components/layout/Footer.jsx</div>

  <h3>Правка 2.1 — добавить иконку часов в импорт</h3>
  <p class="muted">Найдите строку 4 (самое начало файла) и замените:</p>
  <div class="codebox">
    <button class="copy" data-target="code-f1-before">Скопировать</button>
    <pre id="code-f1-before"><span class="del">− import { Logo, Mail, MapPin, Phone, Send } from "../ui/Icons";</span>
<span class="add">+ import { Clock, Logo, Mail, MapPin, Phone, Send } from "../ui/Icons";</span></pre>
  </div>

  <h3>Правка 2.2 — нижняя строка с адресами</h3>
  <p class="muted">
    Ближе к концу файла есть блок с тремя строками адресов. Две первые строки меняются так:
  </p>
  <div class="codebox">
    <button class="copy" data-target="code-f2-before">Скопировать</button>
    <pre id="code-f2-before"><span class="del">− &lt;p className="flex items-center gap-2"&gt;&lt;MapPin size={14} /&gt; Москва, Остаповский проезд, 9 с13&lt;/p&gt;
− &lt;p className="flex items-center gap-2 md:justify-center"&gt;&lt;MapPin size={14} /&gt; СПб, ул. Швецова, 41 лит. А&lt;/p&gt;</span>
<span class="add">+ &lt;Link to="/kontakty" className="flex items-center gap-2 hover:text-ink"&gt;&lt;MapPin size={14} /&gt; Москва, Остаповский проезд, 9 с13&lt;/Link&gt;
+ &lt;p className="flex items-center gap-2 md:justify-center"&gt;&lt;Clock size={14} /&gt; Производство ежедневно 9:00–22:00&lt;/p&gt;</span></pre>
  </div>

  <h2><span class="num">3</span> Форма заявки: показать тему визита</h2>
  <div class="filepath">src/components/layout/overlays.jsx</div>
  <p class="muted">
    Без этой правки кнопка «Записаться на визит» откроет форму, но тема
    «Визит на производство» не подсветится — человеку придётся выбирать её вручную,
    а нужного варианта в списке нет.
  </p>
  <p>Найдите блок <code class="inline">step === 0</code> и добавьте четыре строки перед списком тем:</p>
  <div class="codebox">
    <button class="copy" data-target="code-o1">Скопировать</button>
    <pre id="code-o1"><span class="dim">  {step === 0 &amp;&amp; (
    &lt;div className="flex flex-wrap gap-2"&gt;</span>
<span class="add">+     {topic &amp;&amp; !TOPICS.includes(topic) &amp;&amp; (
+       &lt;button className="rounded-xl border border-accent bg-accent px-4 py-2.5 text-sm font-semibold text-white"&gt;
+         {topic}
+       &lt;/button&gt;
+     )}</span>
<span class="dim">      {TOPICS.map((t) =&gt; (</span></pre>
  </div>
  <p class="muted">
    Здесь <code class="inline">+</code> — вставка, серым показано то, что уже есть в файле и остаётся на месте.
  </p>

  <h2><span class="num">4</span> Проверить</h2>
  <p>Запустите проект и откройте страницу <code class="inline">/kontakty</code>:</p>
  <div class="codebox">
    <button class="copy" data-target="code-run">Скопировать</button>
    <pre id="code-run">npm install
npm run dev
<span class="dim"># затем в браузере: http://localhost:5173/kontakty</span></pre>
  </div>
  <p>Ниже — чек-лист. Если все пункты совпали, страница собрана правильно.</p>
  <ul class="checklist">
    <li>В тексте страницы нет «Санкт-Петербург», «СПб», «Швецова» и телефона <code class="inline">+7 812</code>.</li>
    <li>Вверху три кнопки: телефон, почта, Telegram — все кликаются и открывают звонок, почту и чат.</li>
    <li>Блок «Наш адрес в Москве» показывает Остаповский проезд, режим 24/7 и производство 9:00–22:00.</li>
    <li>Кнопка «Построить маршрут» открывает Яндекс Карты, «Карточка в Яндекс Картах» — карточку организации.</li>
    <li>Кнопка «Записаться на визит» открывает форму с уже выбранной темой «Визит на производство».</li>
    <li>Блок «Цех, в который можно приехать»: три фото (цех, УФ-принтер, студия) и четыре счётчика — 6 участков, 3 ч, 24/7, 300+.</li>
    <li>Шесть карточек участков и три шага «Как попасть в цех» на месте, аккордеон с четырьмя вопросами раскрывается.</li>
    <li>В футере внизу вместо адреса СПб — «Производство ежедневно 9:00–22:00».</li>
    <li>Сборка проходит без ошибок: <code class="inline">npm run build</code>.</li>
  </ul>

  <h2><span class="num">5</span> Что осталось про Питер в других местах</h2>
  <p class="muted">
    На странице контактов Питера больше нет, но он встречается ещё в шести местах.
    Их я не трогал: непонятно, цех закрылся или просто переехал, а формулировка зависит от этого.
  </p>
  <table>
    <tr><th>Где</th><th>Что написано</th></tr>
    <tr><td>index.html</td><td>Заголовок страницы: «…в Москве и СПб» — перебивает заголовок самой страницы для поиска и соцсетей</td></tr>
    <tr><td>Footer.jsx</td><td>Описание компании: «Москва и Санкт-Петербург»</td></tr>
    <tr><td>About.jsx</td><td>«750 м² в Москве и Санкт-Петербурге»</td></tr>
    <tr><td>Production.jsx</td><td>«Москва и Санкт-Петербург, 750 м²»</td></tr>
    <tr><td>data/faq.js, data/team.js</td><td>Визит в СПб и «открытие цеха в Санкт-Петербурге» в истории компании</td></tr>
    <tr><td>data/blog.js</td><td>Два упоминания в статьях</td></tr>
  </table>
  <div class="card">
    <strong>Почему «750 м²» я заменил на «6 участков».</strong>
    750 м² — это сумма по двум городам. Если страница теперь про московский цех,
    такая цифра вводила бы в заблуждение. Как только скажете площадь московского цеха,
    поставлю точную.
  </div>

  <footer>
    Файл собран из репозитория SM (ветка arena/57df9bb4-sm, коммит 817b219) —
    код в нём совпадает с тем, что лежит в проекте. Если что-то не сойдётся
    с вашей версией файла, скажите: пришлю конкретный файл целиком.
  </footer>
</div>

<script>
document.querySelectorAll(".copy").forEach((btn) => {
  btn.addEventListener("click", async () => {
    const block = document.getElementById(btn.dataset.target);
    const text = block.innerText;
    try {
      await navigator.clipboard.writeText(text);
    } catch (e) {
      const ta = document.createElement("textarea");
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      ta.remove();
    }
    const old = btn.textContent;
    btn.textContent = "Скопировано";
    btn.classList.add("done");
    setTimeout(() => { btn.textContent = old; btn.classList.remove("done"); }, 1600);
  });
});
</script>
</body>
</html>
"""


def main() -> int:
    contacts = FILES["contacts"].read_text(encoding="utf-8")
    html_out = (TEMPLATE
                .replace("{contacts}", html.escape(contacts))
                .replace("{contacts_size}", f"{len(contacts.encode('utf-8')):,}".replace(",", " "))
                .replace("{contacts_lines}", str(contacts.count("\n") + 1)))
    OUT.write_text(html_out, encoding="utf-8")
    size = OUT.stat().st_size
    print(f"✓ {OUT.relative_to(ROOT)} — {size:,} байт".replace(",", " "))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
