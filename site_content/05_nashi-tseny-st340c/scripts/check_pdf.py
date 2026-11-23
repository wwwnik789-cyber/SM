#!/usr/bin/env python3
"""Check the alt-first guide, new page structure, calculator, SEO and milling."""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
from pathlib import Path
import re

import pymupdf
from pypdf import PdfReader

FOLDER = Path(__file__).resolve().parents[1]
PDF = FOLDER / 'sm-production-nashi-tseny-instruction.pdf'
CALCULATOR = 'https://sm-production.ru/uslugi/standartnye-reklamnye-konstruktsii'
TITLE = 'Баннеры на каркасе — цены и калькулятор | SM Production'
DESCRIPTION = 'Баннеры на деревянном каркасе: варианты, стандартные цены и расчёт своих размеров. PressWall «Джокер», RollUp, виндеры, аренда мебели и оборудования, фрезеровка.'
SIZES = ['2 × 2','2 × 2,5','3 × 2','3 × 2,5','4 × 2,5','4 × 3','5 × 2,5','5 × 3']
MILLING = [
    ('Вспененный ПВХ 2–4 мм',[38,36,34,31]),
    ('Вспененный ПВХ 5–6 мм',[44,39,38,36]),
    ('Вспененный ПВХ 8–10 мм',[49,44,42,38]),
    ('Оргстекло 1–2 мм',[49,43,41,39]),
    ('Оргстекло 3–4 мм',[52,49,44,41]),
    ('Оргстекло 5–6 мм',[88,77,66,61]),
    ('Оргстекло 8–12 мм',[122,110,99,88]),
    ('Полистирол 1–3 мм',[44,41,39,37]),
    ('Полистирол 4–6 мм',[55,49,47,41]),
    ('Фанера / МДФ / ЛДСП до 10 мм',[111,99,83,71]),
    ('Фанера / МДФ / ЛДСП до 15 мм',[133,122,111,99]),
    ('Фанера / МДФ / ЛДСП до 21 мм',[199,166,144,122]),
    ('Фанера / МДФ / ЛДСП до 30 мм',[234,211,189,166]),
]


def compact(text):
    return re.sub(r'\s+','',text)


def outlines(items):
    for item in items:
        if isinstance(item,list):
            yield from outlines(item)
        else:
            yield item


def records(name):
    with (FOLDER/name).open(encoding='utf-8-sig',newline='') as f:
        return list(csv.DictReader(f,delimiter=';'))


def verify(render_dir: Path | None = None):
    reader=PdfReader(PDF)
    assert not reader.is_encrypted
    assert len(reader.pages)==42
    bookmarks=list(outlines(reader.outline))
    assert len(bookmarks)==35
    assert sum(d.title.startswith('10.') for d in bookmarks)==9
    dest_pages=[reader.get_destination_page_number(d) for d in bookmarks]
    assert dest_pages==sorted(dest_pages) and all(0<=p<len(reader.pages) for p in dest_pages)
    texts=[page.extract_text() for page in reader.pages]
    all_text='\n'.join(texts)
    whole=compact(all_text)
    assert '\ufffd' not in all_text
    toc_pages=[i for i,t in enumerate(texts) if '\nСодержание\n' in t]
    assert toc_pages==[9]  # One contents page after the seven actual alt pages and quick route.
    assert 'Alt по файлам — рабочий реестр' in texts[9]
    assert 'Приложение Б.' in texts[9]
    assert compact(TITLE) in whole and len(TITLE)==55
    assert compact(DESCRIPTION) in whole and len(DESCRIPTION)==161
    for phrase in ['canonical','https://sm-production.ru/tseny','Image alt for SEO','ST340C','CL46',
                   'H1/H2/H3','не гарантирует отдельное поле alt','46 записей',
                   'Автоматическая синхронизация здесь не настраивается.',
                   'Действующий сайт не изменён.','пять ST340C',
                   'Названия и фотографии трёх вариантов ещё не предоставлены.',
                   'калькулятора — сантиметры','передачи параметров здесь не выполняется.']:
        assert compact(phrase).casefold() in whole.casefold(),phrase
    for obsolete in ['шесть ST340C','шестью одинаково','ST340C №6','Приложение В.',
                     'Под восемью карточками','Создать восемь отдельных товаров',
                     'вне ведомости 42 позиций']:
        assert compact(obsolete).casefold() not in whole.casefold(),obsolete

    # The handbook chapters follow the new site order as well as the diagram.
    def chapter(prefix):
        return next(d for d in bookmarks if d.title.startswith(prefix))

    chapter_pages=[reader.get_destination_page_number(chapter(prefix)) for prefix in ['2. Баннеры','3. Таблица','4. Один блок','5. Раздел']]
    assert chapter_pages==sorted(set(chapter_pages)),chapter_pages
    structure_page=reader.get_destination_page_number(chapter('1. Структура'))
    structure=compact(texts[structure_page])
    sequence=['H2 «Баннеры на деревянном каркасе»','CL46 — 8 стандартных размеров',
              'H2 «Рассчитать по своим размерам»','ST340C №2: 4 «Джокера» → 4 RollUp → 3 виндера',
              'H2 «Аренда оборудования и мебели»','H2 «Фрезеровка»']
    positions=[structure.index(compact(label)) for label in sequence]
    assert positions==sorted(positions),positions
    calculator_chapter=compact(texts[chapter_pages[1]])
    assert compact(CALCULATOR) in calculator_chapter
    assert compact('Не подменять кнопку якорем #raschet') in calculator_chapter
    assert compact('не проверены') in calculator_chapter

    # No arbitrary three sizes: the three new slots must remain unassigned.
    plan=records('assortiment-plan.csv')
    assert len(plan)==36
    assert len({r['Предлагаемый_артикул'] for r in plan})==36
    for r in plan:
        assert not r['Цена_SM_руб'] and not r['Старая_цена_руб'] and r['Публиковать']=='Нет'
        assert compact(r['Предлагаемое_название']) in whole,r['Предлагаемое_название']
    wood=[r for r in plan if r['Предлагаемый_артикул'].startswith('SM-BRUS-')]
    assert [r['Предлагаемый_артикул'] for r in wood]==[f'SM-BRUS-VAR-{i:02}' for i in range(1,4)]
    assert all(not r['Ширина_м'] and not r['Высота_м'] and not r['Файл_согласованной_обложки'] for r in wood)
    combined=[r for r in plan if r['Раздел_страницы']=='PressWall «Джокер», RollUp и виндеры']
    expected_skus=['SM-JOKER-200-200','SM-JOKER-300-250','SM-JOKER-300-300','SM-JOKER-400-300',
                   'SM-ADV-RU-085-200','SM-ADV-RU-100-200','SM-ADV-RU-120-200','SM-ADV-RU-150-200',
                   'SM-ADV-WINDER-SAIL','SM-ADV-WINDER-DROP','SM-ADV-WINDER-BRIZ']
    assert [r['Предлагаемый_артикул'] for r in combined]==expected_skus
    assert len({r['Раздел_каталога'] for r in combined})==1
    assert [r['Порядок_в_разделе'] for r in combined]==list(map(str,range(1,12)))
    assert not any(r['Предлагаемый_артикул'].startswith('SM-ADV-X-') for r in plan)
    assert sum(r['Предлагаемый_артикул'].startswith('SM-RENT-CHAIR-') for r in plan)==10
    assert sum(r['Предлагаемый_артикул'].startswith('SM-RENT-ARMCHAIR-') for r in plan)==10

    # All actual alt phrases are before the quick route, contents and handbook.
    alts=records('image-alt-register.csv')
    assert len(alts)==46
    assert len({r['Артикул_плана'] for r in alts})==46
    active=[r for r in alts if r['Использование']=='Активная позиция']
    reserve=[r for r in alts if r['Использование']=='Резерв']
    assert len(active)==36 and len(reserve)==10
    assert {r['Артикул_плана'] for r in active}=={r['Предлагаемый_артикул'] for r in plan}
    ready=[r for r in alts if r['Файл']]
    draft=[r for r in alts if not r['Файл']]
    assert len(ready)==19 and len(draft)==27
    assert sum(bool(r['Файл']) for r in active)==11
    assert Counter(r['Группа'] for r in reserve)=={'Резерв обложек дерева':8,'Резерв X-баннеров':2}
    alt_start=reader.get_destination_page_number(chapter('Alt по файлам'))
    howto=reader.get_destination_page_number(chapter('Как работать'))
    assert (alt_start,howto)==(1,8)
    front=compact('\n'.join(texts[alt_start:howto]))
    assert len(bookmarks[1:7])==6 and all(1<=p<8 for p in dest_pages[:7])
    for r in alts:
        assert compact(r['Alt']) in front,r['Alt']
        if r['Файл']:
            assert (FOLDER/r['Файл']).is_file()
            assert compact(Path(r['Файл']).name) in front,r['Файл']
            assert '[' not in r['Alt'] and r['Статус'].startswith('ГОТОВО')
        else:
            assert compact(r['Артикул_плана']) in front
            assert r['Статус'].startswith(('ЧЕРНОВИК','ШАБЛОН'))
    assert sum(r['Группа']=='Стулья' for r in draft)==10
    assert sum(r['Группа']=='Кресла' for r in draft)==10
    assert sum('[' in r['Alt'] for r in draft)==7

    md=(FOLDER/'README.md').read_text()
    start=md.index('| Материал / толщина |')
    end=md.index('\n\n',start)
    lines=md[start:end].splitlines()
    assert len(lines)==15
    for line,(name,rates) in zip(lines[2:],MILLING):
        cols=[c.strip() for c in line.strip('|').split('|')]
        assert cols==[name]+list(map(str,rates))
    milling_page=reader.get_destination_page_number(chapter('13.'))
    milling=compact(texts[milling_page])
    assert compact('Минимальный заказ на фрезеровку — 10 000.') in milling
    for name,rates in MILLING:
        assert compact(name+''.join(map(str,rates))) in milling,(name,rates)
    assert compact('Другие цены каталога из этой таблицы не пересчитывать.') in milling
    assert re.findall(r'(?m)^([2345] × [23](?:,5)?);УТОЧНИТЬ\s*$',all_text)==SIZES
    assert 'Размер (Ш × В), м;Стоимость, ₽' in all_text
    assert '60%;40%' in all_text

    uris=[];internal=0
    refs={p.indirect_reference.idnum for p in reader.pages}
    for page in reader.pages:
        for ref in page.get('/Annots',[]):
            a=ref.get_object()
            if a.get('/Subtype')!='/Link':continue
            if a.get('/A') and a['/A'].get('/URI'):
                uri=str(a['/A']['/URI']);uris.append(uri)
                assert uri.startswith(('https://','http://','mailto:','tel:')),uri
            if a.get('/Dest'):
                assert a['/Dest'][0].idnum in refs
                internal+=1
    for item in records('furniture-selection.csv'):
        assert item['Страница_модели'] in uris
    for url in ['https://help-ru.tilda.cc/search-engine','https://help-ru.tilda.cc/accessibility',
                'https://help-ru.tilda.cc/online-store/seo-and-microdata-for-products',
                'https://help-ru.tilda.cc/tables',CALCULATOR]:
        assert url in uris,url
    assert uris.count(CALCULATOR)==4
    assert not any(CALCULATOR+'#' in uri for uri in uris)
    assert internal==51  # 21 contents entries × 2 links + 9 front-matter links.
    assert len(uris)==58
    document=pymupdf.open(PDF)
    for i,page in enumerate(document,1):
        assert abs(page.rect.width-595.276)<.1 and abs(page.rect.height-841.890)<.1
        assert len(page.get_text())>200,f'Empty/sparse page {i}'
        for block in page.get_text('dict')['blocks']:
            for line in block.get('lines',[]):
                for span in line['spans']:
                    x0,y0,x1,y1=span['bbox']
                    assert 45<=x0<=x1<=page.rect.width-45,(i,span)
                    assert 14<=y0<=y1<=page.rect.height-17,(i,span)
        if render_dir:
            render_dir.mkdir(parents=True,exist_ok=True)
            page.get_pixmap(matrix=pymupdf.Matrix(1.25,1.25),alpha=False).save(render_dir/f'page-{i:02}.png')
    print(f'PASS: {len(reader.pages)} A4 pages, {len(bookmarks)} bookmarks, {internal} internal links, {len(uris)} external links.')
    print('PASS: new structure; three unassigned wood variants; table/calculator before one 4/4/3 block; 36 blank-price plan rows.')
    print('PASS: all 46 alt texts on pp. 2–8 / 19 real files; 36 active + 10 reserve; SEO; all 52 milling rates; 8 CL46 rows.')
    print('PASS: readable Cyrillic, one-page contents/milling table, calculator URL, valid links and text within page bounds.')
    print(f'Size: {PDF.stat().st_size:,} bytes')
    print(f'SHA256: {hashlib.sha256(PDF.read_bytes()).hexdigest()}')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--render-dir',type=Path,help='Optional scratch output for all page previews')
    args=parser.parse_args()
    verify(args.render_dir)
