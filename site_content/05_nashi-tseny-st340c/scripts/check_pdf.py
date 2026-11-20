#!/usr/bin/env python3
"""Check the unified guide: SEO, all alt records, CL46, old prices and navigation."""
from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path
import re

import pymupdf
from pypdf import PdfReader

FOLDER = Path(__file__).resolve().parents[1]
PDF = FOLDER / 'sm-production-nashi-tseny-instruction.pdf'
TITLE = 'Цены на фотозоны, рекламные конструкции и аренду | SM Production'
DESCRIPTION = 'Цены на брус-баннеры и пресс-воллы «Джокер», роллапы и виндеры. Аренда оборудования и мебели, фрезеровка. Выберите размер или модель и запросите расчёт.'
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
    assert len(reader.pages)==41
    bookmarks=list(outlines(reader.outline))
    assert len(bookmarks)==34
    assert sum(d.title.startswith('10.') for d in bookmarks)==9
    pages=[reader.get_destination_page_number(d) for d in bookmarks]
    assert pages==sorted(pages) and all(0<=p<41 for p in pages)
    assert 'Содержание' in reader.pages[2].extract_text()
    assert 'В.6. Шаблоны и особые случаи' in reader.pages[2].extract_text()
    texts=[page.extract_text() for page in reader.pages]
    all_text='\n'.join(texts)
    whole=compact(all_text)
    assert '\ufffd' not in all_text
    assert compact(TITLE) in whole and len(TITLE)==64
    assert compact(DESCRIPTION) in whole and len(DESCRIPTION)==152
    for phrase in ['canonical','https://sm-production.ru/tseny','Image alt for SEO','ST340C','CL46',
                   'H1/H2/H3','не гарантирует отдельное поле alt','43 строки реестра',
                   'Автоматическая синхронизация здесь не настраивается.',
                   'Действующий сайт не изменён.']:
        assert compact(phrase).casefold() in whole.casefold(),phrase
    plan=records('assortiment-plan.csv')
    assert len(plan)==42
    for r in plan:
        assert not r['Цена_SM_руб'] and not r['Старая_цена_руб'] and r['Публиковать']=='Нет'
        assert compact(r['Предлагаемое_название']) in whole,r['Предлагаемое_название']
    alts=records('image-alt-register.csv')
    assert len(alts)==43
    assert len({r['Артикул_плана'] for r in alts})==43
    assert {r['Артикул_плана'] for r in alts}=={r['Предлагаемый_артикул'] for r in plan}|{'SM-ADV-WINDER-BRIZ'}
    ready=[r for r in alts if r['Файл']]
    draft=[r for r in alts if not r['Файл']]
    assert len(ready)==19 and len(draft)==24
    for r in alts:
        assert compact(r['Alt']) in whole,r['Alt']
        if r['Файл']:
            assert (FOLDER/r['Файл']).is_file()
            assert compact(Path(r['Файл']).name) in whole,r['Файл']
            assert '[' not in r['Alt'] and r['Статус'].startswith('ГОТОВО')
        else:
            assert compact(r['Артикул_плана']) in whole
            assert r['Статус'].startswith('ЧЕРНОВИК')
    assert sum(r['Группа']=='Стулья' for r in draft)==10
    assert sum(r['Группа']=='Кресла' for r in draft)==10
    assert sum('[' in r['Alt'] for r in draft)==4
    md=(FOLDER/'README.md').read_text()
    start=md.index('| Материал / толщина |')
    end=md.index('\n\n',start)
    lines=md[start:end].splitlines()
    assert len(lines)==15
    for line,(name,rates) in zip(lines[2:],MILLING):
        cols=[c.strip() for c in line.strip('|').split('|')]
        assert cols==[name]+list(map(str,rates))
    milling_page=next(reader.get_destination_page_number(d) for d in bookmarks if d.title.startswith('13.'))
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
                'https://help-ru.tilda.cc/tables']:
        assert url in uris,url
    assert internal==59  # 26 contents entries × 2 links + 7 quick-route links.
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
    print(f'PASS: 41 A4 pages, 34 bookmarks, {internal} internal links, {len(uris)} external links.')
    print('PASS: SEO fields; all 43 alt texts / 19 real files; 42 unchanged blank-price plan rows; all 52 milling rates; 8 CL46 rows.')
    print('PASS: readable Cyrillic, one-page contents/milling table, valid links and text within page bounds.')
    print(f'Size: {PDF.stat().st_size:,} bytes')
    print(f'SHA256: {hashlib.sha256(PDF.read_bytes()).hexdigest()}')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--render-dir',type=Path,help='Optional scratch output for all 41 page previews')
    args=parser.parse_args()
    verify(args.render_dir)
