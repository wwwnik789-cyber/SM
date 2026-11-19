#!/usr/bin/env python3
"""Build the self-contained Russian prices-page handbook from approved content."""
from pathlib import Path
from html import escape
import csv
import textwrap
from urllib.parse import urljoin

from markdown_it import MarkdownIt
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, PageBreak,
    Image, Table, LongTable, TableStyle, KeepTogether, Preformatted, CondPageBreak,
)
from reportlab.platypus.tableofcontents import TableOfContents

FOLDER = Path(__file__).resolve().parents[1]
ROOT = FOLDER.parents[1]
OUTPUT = FOLDER / 'sm-production-nashi-tseny-instruction.pdf'
FONTROOT = Path('/usr/share/fonts/truetype/dejavu')
for name, fn in [('Body','DejaVuSans.ttf'), ('BodyBold','DejaVuSans-Bold.ttf'), ('Mono','DejaVuSansMono.ttf')]:
    pdfmetrics.registerFont(TTFont(name, str(FONTROOT/fn)))
pdfmetrics.registerFontFamily('Body', normal='Body', bold='BodyBold', italic='Body', boldItalic='BodyBold')
pdfmetrics.registerFontFamily('Mono', normal='Mono', bold='Mono', italic='Mono', boldItalic='Mono')

NAVY = colors.HexColor('#192d43')
GOLD = colors.HexColor('#a47a29')
INK = colors.HexColor('#23313f')
MUTED = colors.HexColor('#64717f')
LINK = colors.HexColor('#236c8d')
PALE = colors.HexColor('#f2f5f7')
LINE = colors.HexColor('#dce3e9')
WHITE = colors.white
PAGE_W, PAGE_H = A4
MARGIN = 48
CONTENT_W = PAGE_W - MARGIN*2
CONTENT_H = PAGE_H - 104
BASE_URL = 'https://github.com/wwwnik789-cyber/SM/blob/arena/48344a20-sm/site_content/05_nashi-tseny-st340c/'
GH = 'https://github.com/wwwnik789-cyber/SM/blob/arena/48344a20-sm/'

styles = {}
def sty(name, **kw):
    base=dict(fontName='Body',fontSize=9.3,leading=14.1,textColor=INK,
              spaceAfter=7.5,allowWidows=0,allowOrphans=0,splitLongWords=1)
    base.update(kw)
    styles[name] = ParagraphStyle(name, **base)
    return styles[name]

sty('Body')
sty('Small',fontSize=8.1,leading=12,textColor=MUTED)
sty('Lead',fontSize=12,leading=18.5,textColor=MUTED,spaceAfter=16)
sty('Brand',fontName='BodyBold',fontSize=15,leading=20,textColor=NAVY,spaceAfter=12)
sty('Kicker',fontName='BodyBold',fontSize=8.6,leading=13,textColor=GOLD,spaceAfter=14)
sty('CoverTitle',fontName='BodyBold',fontSize=35,leading=43,textColor=NAVY,spaceAfter=20)
sty('H1',fontName='BodyBold',fontSize=20,leading=27,textColor=NAVY,spaceAfter=17,keepWithNext=1)
sty('H2',fontName='BodyBold',fontSize=12.1,leading=17,textColor=NAVY,spaceBefore=14,spaceAfter=8,keepWithNext=1)
sty('H3',fontName='BodyBold',fontSize=10.3,leading=15,textColor=NAVY,spaceBefore=10,spaceAfter=6,keepWithNext=1)
sty('Quote',fontSize=10,leading=15.5,leftIndent=13,rightIndent=9,borderColor=GOLD,borderWidth=0,borderPadding=9,backColor=PALE,spaceBefore=3,spaceAfter=12)
sty('Bullet',leftIndent=15,firstLineIndent=0,bulletIndent=1,spaceAfter=6)
sty('NestedBullet',leftIndent=28,bulletIndent=14,spaceAfter=5)
sty('Cell',fontSize=8,leading=11.5,spaceAfter=0,allowWidows=1,allowOrphans=1)
sty('CellSmall',fontSize=7.2,leading=10.5,spaceAfter=0,allowWidows=1,allowOrphans=1)
sty('CellHead',fontName='BodyBold',fontSize=8,leading=11.5,textColor=WHITE,spaceAfter=0,allowWidows=1,allowOrphans=1)
sty('CellNum',fontName='BodyBold',fontSize=8.5,leading=11.5,alignment=TA_CENTER,spaceAfter=0,allowWidows=1,allowOrphans=1)
sty('CellHeadNum',fontName='BodyBold',fontSize=8,leading=11.5,alignment=TA_CENTER,textColor=WHITE,spaceAfter=0,allowWidows=1,allowOrphans=1)
sty('Code',fontName='Mono',fontSize=7.8,leading=11.2,spaceAfter=0,allowWidows=1,allowOrphans=1)
sty('Caption',fontSize=8.2,leading=12.2,textColor=MUTED,spaceBefore=6,spaceAfter=10)
sty('Toc',fontSize=9.3,leading=14.5,textColor=NAVY,leftIndent=0,firstLineIndent=0,rightIndent=24,spaceBefore=5,spaceAfter=5)


def p(txt, s='Body'):
    return Paragraph(txt, styles[s])

def resolve_link(href):
    if href == 'assortiment-plan.csv':
        return '#worksheet'
    if href == 'furniture-selection.csv':
        return '#furniture'
    if href.startswith(('https://','http://','mailto:','tel:','#')):
        return href
    return urljoin(BASE_URL, href)


def inline(children):
    out=[]
    for t in children or []:
        typ=t.type
        if typ=='text':
            out.append(escape(t.content.replace('[ ]','☐')))
        elif typ=='code_inline':
            out.append('<font name="Mono" size="7.8">'+escape(t.content)+'</font>')
        elif typ=='strong_open': out.append('<b>')
        elif typ=='strong_close': out.append('</b>')
        elif typ=='em_open': out.append('<i>')
        elif typ=='em_close': out.append('</i>')
        elif typ=='link_open':
            href=resolve_link(t.attrGet('href'))
            out.append('<link href="'+escape(href,quote=True)+'" color="#236c8d">')
        elif typ=='link_close': out.append('</link>')
        elif typ=='softbreak': out.append(' ')
        elif typ=='hardbreak': out.append('<br/>')
        elif typ=='image': out.append(escape(t.content))
        elif typ=='html_inline': out.append(escape(t.content))
    return ''.join(out)


def table_block(rows, widths=None, header=True, fs='Cell'):
    if widths is None:
        n=len(rows[0])
        if n==2:
            widths=[CONTENT_W*.30,CONTENT_W*.70]
        elif n==3 and rows[0][0].replace('<b>','').startswith('№'):
            widths=[28,219,CONTENT_W-247]
        elif n==3:
            widths=[68,159,CONTENT_W-227]
        elif n==4 and 'Порядок' in rows[0][0]:
            widths=[39,143,183,CONTENT_W-365]
        elif n==4:
            widths=[28,138,220,CONTENT_W-386]
        elif n==5:
            widths=[205]+[(CONTENT_W-205)/4]*4
        else:
            widths=[CONTENT_W/n]*n
    cell_rows=[]
    for ri,row in enumerate(rows):
        cell_rows.append([p(c, ('CellHeadNum' if ci else 'CellHead') if header and ri==0 and len(row)==5 else ('CellNum' if ci else fs) if len(row)==5 else 'CellHead' if header and ri==0 else fs) for ci,c in enumerate(row)])
    tb=LongTable(cell_rows,colWidths=widths,repeatRows=1 if header else 0,hAlign='LEFT')
    commands=[('VALIGN',(0,0),(-1,-1),'TOP'),
              ('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),
              ('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),
              ('LINEBELOW',(0,0),(-1,-1),.45,LINE),
              ('ROWBACKGROUNDS',(0,1 if header else 0),(-1,-1),[WHITE,PALE])]
    if header: commands += [('BACKGROUND',(0,0),(-1,0),NAVY)]
    tb.setStyle(TableStyle(commands))
    return tb


class GuideDoc(BaseDocTemplate):
    def __init__(self,*a,**kw):
        super().__init__(*a,**kw)
        frame=Frame(MARGIN,48,CONTENT_W,CONTENT_H,id='main',leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)
        self.addPageTemplates(PageTemplate(id='guide',frames=frame,onPage=self.decorate))
    def decorate(self,c,doc):
        c.saveState()
        if doc.page > 1:
            c.setFillColor(MUTED);c.setFont('Body',7.4)
            c.drawString(MARGIN,PAGE_H-28,'SM PRODUCTION  /  НАШИ ЦЕНЫ  /  TILDA ST340C')
            c.setStrokeColor(LINE);c.setLineWidth(.6)
            c.line(MARGIN,PAGE_H-37,PAGE_W-MARGIN,PAGE_H-37)
        c.setFillColor(MUTED);c.setFont('Body',7.3)
        c.drawString(MARGIN,27,'Инструкция по оформлению • 19.11.2026')
        c.drawRightString(PAGE_W-MARGIN,27,str(doc.page))
        c.restoreState()
    def afterFlowable(self,flow):
        if isinstance(flow,Paragraph) and getattr(flow,'_key',None):
            name=flow.getPlainText()
            self.canv.bookmarkPage(flow._key)
            self.canv.addOutlineEntry(name,flow._key,level=0,closed=False)
            self.notify('TOCEntry',(0,name,self.page,flow._key))


def heading(text,key):
    flow=p(escape(text),'H1')
    flow._key=key
    return flow


def cover_image(path,w):
    with PILImage.open(path) as im:
        iw,ih=im.size
    return Image(str(path),width=w,height=w*ih/iw,hAlign='CENTER')

story=[]
story += [Spacer(1,20),p('SM PRODUCTION','Brand'),p('ЕДИНЫЙ РАБОЧИЙ ДОКУМЕНТ','Kicker'),
          p('Наши цены<br/>Инструкция<br/>по оформлению','CoverTitle'),
          p('Страница sm-production.ru/tseny<br/>Tilda · Интернет-магазин ST340C','Lead')]

thumbw=(CONTENT_W-14)/2
brus=ROOT/'visualizations/catalog/presswalls-with-people/sm-production-presswall-3x2p5-people.jpg'
joker=ROOT/'visualizations/catalog/joker-sizes/sm-production-joker-3x2p5-people.jpg'
thumbs=Table([[cover_image(brus,thumbw),cover_image(joker,thumbw)],
              [p('Брус-баннеры · 8 размеров','Caption'),p('«Джокер» · 4 размера','Caption')]],
             colWidths=[CONTENT_W/2,CONTENT_W/2],hAlign='LEFT')
thumbs.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0)]))
story += [thumbs,Spacer(1,12),p('<b>Внутри:</b> структура страницы, настройка каталога, готовые тексты, оформление карточек, 10 стульев и 10 кресел со ссылками, цены и заявки, проверка перед запуском и рабочая ведомость на 42 позиции.'),
          p('Всё собрано в этом PDF. Открывать Markdown или отдельные таблицы для чтения инструкции не требуется.','Small'),
          p('<b>ОБНОВЛЕНО:</b> фрезеровка — 13 строк материалов, 4 объёмных тарифа и минимальный заказ 10 000. Полная таблица в разделе 13.','Small'),
          Spacer(1,5),p('Это руководство по сборке страницы, не опубликованный прайс. Коммерческие условия и наличие необходимо утвердить. Действующий сайт не изменён.','Small'),PageBreak()]

story += [heading('Как работать с этим PDF','how-to'),
          p('<b>Откройте редактор Tilda рядом с документом и выполняйте шаги раздела 6 по порядку.</b> Готовые тексты можно выделять и копировать прямо из PDF.'),
          p('1. Согласуйте цены, комплектацию и реальный ассортимент. Для отметок используйте рабочую ведомость в приложении А.'),
          p('2. Начните с 8 фотозон и 4 «Джокеров»: изображения для них уже подготовлены. Ссылки на оригиналы указаны в разделах 2–3.'),
          p('3. Создайте разделы каталога, настройте первый ST340C и повторите его оформление для остальных групп. Затем подключите заявку.'),
          p('4. Добавьте подтверждённые рекламные конструкции и мебель. Перед публикацией пройдите проверку из раздела 11.'),
          p('5. Новые тарифы фрезеровки находятся в разделе 13. Таблица добавляется после аренды отдельно от шести сеток ST340C; остальные товарные цены из неё не выводятся.'),
          p('Все ссылки в документе кликабельны. Оглавление ниже и закладки PDF ведут к нужному разделу. Мебель — внешняя подборка, а не подтверждённое наличие SM.','Small'),Spacer(1,8),p('Содержание','H2')]
toc=TableOfContents()
toc.levelStyles=[styles['Toc']]
toc.dotsMinLevel=0
story += [toc,PageBreak()]

source=(FOLDER/'README.md').read_text()
source=source[source.index('## Главное решение'):]
start=source.index('**Подготовленные таблицы:**')
end=source.index('\n---',start)
source=source[:start]+'''**Всё находится в этом PDF:** полная инструкция, подборка 10 стульев и 10 кресел в разделе 5, рабочая ведомость на 42 позиции в приложении А, наглядное сравнение согласованных конструкций в приложении Б и полученные тарифы фрезеровки в разделе 13.

Ведомость нужна для согласования цен и ассортимента. Это не готовый импорт Tilda. Цены товарных карточек намеренно не выдуманы; их нужно утвердить отдельно. Тарифы фрезеровки добавлены из новых вводных без наценок и пересчёта.
'''+source[end:]
source=source.replace('Артикулы из приложенного CSV — **предлагаемые новые коды**, не ID существующих товаров.','Для новых карточек задайте уникальные артикулы, например SM-BRUS-200-200 для фотозоны 2 × 2 м. Артикул не заменяет PRODUCT ID.')
source=source.replace('Ссылки на фото в CSV — для выбора и согласования, не для автоматического копирования на сайт.','Ссылки на страницы моделей в этом PDF — для выбора и согласования, не для автоматического копирования фотографий на сайт.')
source=source.replace('Все значения в приложенных CSV пустые до согласования.','Цены в рабочей ведомости этого PDF оставлены пустыми до согласования.')
source=source.replace('Прямые страницы всех 20 моделей мебели приведены в таблицах и в `furniture-selection.csv`.','Прямые кликабельные ссылки на все 20 моделей мебели приведены в разделе 5 этого PDF.')

md=MarkdownIt('commonmark').enable('table')
tokens=md.parse(source)
i=0
section_idx=0
list_stack=[]
blockquote=0
while i<len(tokens):
    t=tokens[i]
    if t.type=='heading_open':
        content=tokens[i+1]
        label=content.content
        if t.tag=='h2':
            if label.startswith('13.'):
                story.append(PageBreak())
            elif section_idx:
                story.extend([CondPageBreak(230), Spacer(1, 17)])
            section_idx += 1
            key='furniture' if label.startswith('5.') else 'milling' if label.startswith('13.') else 'chapter-'+str(section_idx)
            story.append(heading(label,key))
        else:
            story.append(p(inline(content.children),'H2' if t.tag=='h3' else 'H3'))
        i+=3
        continue
    if t.type in ('bullet_list_open','ordered_list_open'):
        list_stack.append({'ordered':t.type=='ordered_list_open','num':int(t.attrGet('start') or 1),'pending':False})
    elif t.type=='list_item_open':
        list_stack[-1]['pending']=True
    elif t.type in ('bullet_list_close','ordered_list_close'):
        list_stack.pop()
    elif t.type=='blockquote_open':
        blockquote+=1
    elif t.type=='blockquote_close':
        blockquote-=1
    elif t.type=='paragraph_open':
        it=tokens[i+1]
        text=inline(it.children)
        if list_stack:
            state=list_stack[-1]
            marker=None
            if state['pending']:
                marker=str(state['num'])+'.' if state['ordered'] else '•'
                state['pending']=False
                state['num']+=1
            story.append(Paragraph(text,styles['Bullet' if len(list_stack)==1 else 'NestedBullet'],bulletText=marker))
        else:
            story.append(p(text,'Quote' if blockquote else 'Body'))
        i+=3
        continue
    elif t.type=='fence':
        lines=[]
        for ln in t.content.rstrip('\n').splitlines():
            if len(ln)>93:
                lines.extend(textwrap.wrap(ln,93,replace_whitespace=False,drop_whitespace=False,subsequent_indent='  ',break_long_words=True))
            else:
                lines.append(ln)
        pre=Preformatted('\n'.join(lines),styles['Code'])
        tb=Table([[pre]],colWidths=[CONTENT_W],hAlign='LEFT')
        tb.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),PALE),('BOX',(0,0),(-1,-1),.5,LINE),('LEFTPADDING',(0,0),(-1,-1),11),('RIGHTPADDING',(0,0),(-1,-1),11),('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),10)]))
        story.extend([tb,Spacer(1,9)])
    elif t.type=='table_open':
        rows=[];row=[];j=i+1
        while tokens[j].type!='table_close':
            tt=tokens[j]
            if tt.type=='tr_open': row=[]
            elif tt.type in ('th_open','td_open'):
                row.append(inline(tokens[j+1].children))
            elif tt.type=='tr_close': rows.append(row)
            j+=1
        story.extend([table_block(rows),Spacer(1,12)])
        i=j
    i+=1

# Include the planning sheet itself, not a link to a separate CSV.
story += [PageBreak(),heading('Приложение А. Рабочая ведомость ассортимента','worksheet'),
          p('42 планируемые товарные позиции. Заполните утверждённые цены SM, а в последней колонке отметьте готовность. Пустое поле — это не нулевая цена и не разрешение на публикацию. Фрезеровка сюда не включена: полученные ставки приведены отдельно в разделе 13.'),
          p('Для аренды базовая единица — 1 шт. за первые сутки; последующие сутки и логистика согласуются отдельно. «Джокер»: сначала определить, продаётся каркас или предоставляется на срок мероприятия.','Small')]
with (FOLDER/'assortiment-plan.csv').open(encoding='utf-8-sig',newline='') as f:
    plan=list(csv.DictReader(f,delimiter=';'))
assert len(plan)==42
works=[['Товар / размер','Единица цены','Цена SM, ₽','ОК']]
groups=[]
prev=None
for r in plan:
    if r['Раздел_страницы']!=prev:
        groups.append(len(works))
        works.append([r['Раздел_страницы'],'','',''])
        prev=r['Раздел_страницы']
    unit=r['Единица_цены'].replace('; условия предоставления уточнить','')
    works.append([r['Предлагаемое_название'],unit,'____________','☐'])
wrows=[]
for idx,row in enumerate(works):
    s='CellHead' if idx==0 or idx in groups else 'Cell'
    wrows.append([p(escape(c),s) for c in row])
wt=LongTable(wrows,colWidths=[CONTENT_W-229,108,76,45],repeatRows=1,hAlign='LEFT')
cmd=[('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),('LINEBELOW',(0,0),(-1,-1),.45,LINE),('BACKGROUND',(0,0),(-1,0),NAVY)]
for gr in groups:
    cmd.extend([('SPAN',(0,gr),(-1,gr)),('BACKGROUND',(0,gr),(-1,gr),NAVY),('NOSPLIT',(0,gr),(-1,min(gr+1,len(wrows)-1)))])
wt.setStyle(TableStyle(cmd))
story += [wt,Spacer(1,12),p('Перед публикацией для каждой позиции подтвердить: модель и исполнение; комплектацию; фото и права; цену и налоговую формулировку; наличие или срок изготовления; логистику. Для рекламных конструкций размеры пока предложены, для мебели наличие SM не подтверждено.','Small')]

# Embed already-approved comparison images so the instruction remains readable offline.
story += [PageBreak(),heading('Приложение Б. Согласованные визуализации','visuals'),
          p('Восемь размеров фотозон на каркасе из бруса. Полный кадр и общий масштаб необходимо сохранить в карточках сайта. Размеры — ширина × высота.','Small')]
imgpath=ROOT/'visualizations/catalog/presswalls-with-people/sm-production-people-size-comparison.jpg'
with PILImage.open(imgpath) as im: iw,ih=im.size
hh=596
story += [Image(str(imgpath),width=hh*iw/ih,height=hh,hAlign='CENTER')]
story += [PageBreak(),p('Четыре размера «Джокера»','H1'),
          p('Открытый металлический каркас, баннер на люверсах и опорные ножки. Фон и люди те же, что у брус-баннеров.','Small')]
imgpath=ROOT/'visualizations/catalog/joker-sizes/sm-production-joker-size-comparison.jpg'
with PILImage.open(imgpath) as im: iw,ih=im.size
story += [Image(str(imgpath),width=CONTENT_W,height=CONTENT_W*ih/iw,hAlign='CENTER'),Spacer(1,13),
          p('<b>Как перенести изображения на сайт:</b> скачать исходный WebP/JPEG из утверждённой серии, загрузить его в Tilda и выбрать показ целиком. Не делать скриншот страницы этого PDF: он предназначен для инструкции, а не вместо оригинального файла.'),
          p('<link href="'+GH+'visualizations/catalog/presswalls-with-people/README.md" color="#236c8d">Открыть оригиналы восьми брус-баннеров</link>'),
          p('<link href="'+GH+'visualizations/catalog/joker-sizes/README.md" color="#236c8d">Открыть оригиналы четырёх «Джокеров»</link>')]

OUTPUT.parent.mkdir(parents=True,exist_ok=True)
doc=GuideDoc(str(OUTPUT),pagesize=A4,leftMargin=MARGIN,rightMargin=MARGIN,topMargin=56,bottomMargin=48,
             title='Наши цены — единая инструкция по оформлению страницы Tilda ST340C',author='SM Production',
             subject='Структура страницы, каталог, 20 моделей мебели, тарифы фрезеровки, цены и заявки',
             creator='SM Production · Руководство по оформлению',pageCompression=1)
doc.multiBuild(story)
print(OUTPUT)
print(f'{OUTPUT.stat().st_size:,} bytes')
