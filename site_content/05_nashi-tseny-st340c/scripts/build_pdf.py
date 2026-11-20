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
sty('CoverTitle',fontName='BodyBold',fontSize=32,leading=39,textColor=NAVY,spaceAfter=20)
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
sty('Toc',fontSize=9.1,leading=13.8,textColor=NAVY,leftIndent=0,firstLineIndent=0,rightIndent=24,spaceBefore=0,spaceAfter=0)


def p(txt, s='Body'):
    return Paragraph(txt, styles[s])

def resolve_link(href):
    if href == 'assortiment-plan.csv':
        return '#worksheet'
    if href == 'furniture-selection.csv':
        return '#furniture'
    if href == 'image-alt-register.csv':
        return '#alt'
    if href == 'seo-setup.md':
        return '#seo'
    if href == 'cl46-table.md':
        return '#cl46'
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
    if len(rows[0])==5:
        # Keep the unchanged 13×4 milling table and its caveats on one A4 page.
        commands += [('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]
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
            c.drawString(MARGIN,PAGE_H-28,'SM PRODUCTION  /  НАШИ ЦЕНЫ  /  ST340C · CL46 · SEO / ALT')
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
        elif isinstance(flow,Paragraph) and getattr(flow,'_child_key',None):
            self.canv.bookmarkPage(flow._child_key)
            self.canv.addOutlineEntry(flow.getPlainText(),flow._child_key,level=1,closed=False)


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
          p('Наши цены<br/>Настройка страницы<br/>SEO и alt','CoverTitle'),
          p('sm-production.ru/tseny<br/>ST340C · таблица CL46 · SEO · изображения','Lead')]

thumbw=(CONTENT_W-14)/2
brus=ROOT/'visualizations/catalog/presswalls-with-people/sm-production-presswall-3x2p5-people.jpg'
joker=ROOT/'visualizations/catalog/joker-sizes/sm-production-joker-3x2p5-people.jpg'
thumbs=Table([[cover_image(brus,thumbw),cover_image(joker,thumbw)],
              [p('Брус-баннеры · 8 размеров','Caption'),p('«Джокер» · 4 размера','Caption')]],
             colWidths=[CONTENT_W/2,CONTENT_W/2],hAlign='LEFT')
thumbs.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0)]))
story += [thumbs,Spacer(1,12),p('<b>Внутри:</b> сборка страницы и каталога, CL46, готовые SEO-тексты, 19 готовых alt и 24 условных текста для будущих фото; 10 стульев и 10 кресел, заявки, фрезеровка и ведомость на 42 позиции.'),
          p('Всё собрано в этом PDF. Открывать Markdown или отдельные таблицы для чтения инструкции не требуется.','Small'),
          p('<b>СОХРАНЕНО:</b> 13 строк / 52 ставки фрезеровки и минимум 10 000. <b>ДОБАВЛЕНО:</b> SEO, alt по файлам и настройки таблицы брус-баннеров — всё в одном PDF.','Small'),
          Spacer(1,5),p('Это руководство по сборке страницы, не опубликованный прайс. Коммерческие условия и наличие необходимо утвердить. Действующий сайт не изменён.','Small'),PageBreak()]

story += [heading('Как работать с этим PDF','how-to'),
          p('<b>Откройте редактор Тильды рядом с документом.</b> Тексты, строки CL46 и alt можно выделять и копировать. Оглавление и закладки ведут к разделам; готовые значения не нужно искать в отдельных файлах.'),
          table_block([
              ['Этап','Что делать / куда перейти'],
              ['1. Утвердить', '<link href="#worksheet" color="#236c8d">Приложение А: 42 позиции, цены и комплектность</link>. Цены не выдуманы; мебель пока внешние кандидаты.'],
              ['2. Собрать', '<link href="#setup" color="#236c8d">Раздел 6: Каталог, шесть ST340C, заявка</link>. Сначала восемь брус-баннеров и четыре «Джокера».'],
              ['3. Таблица', '<link href="#cl46" color="#236c8d">Раздел 14: CL46, 8 строк и ширина 60/40</link>. Сверить цены с карточками.'],
              ['4. SEO', '<link href="#seo" color="#236c8d">Раздел 10: Title, Description, H1/H2/H3, соцсети, индексация</link>. Готовые значения и примеры для товаров.'],
              ['5. Изображения', '<link href="#alt" color="#236c8d">Приложение В: файл → alt</link>. 19 готовых текстов, 24 условных; ограничение Каталога описано в 10.5.'],
              ['6. Проверить', '<link href="#launch" color="#236c8d">Раздел 11: контроль публикации</link>. Цены, права, мобильная версия и получение тестовой заявки.'],
          ],widths=[92,CONTENT_W-92]),
          Spacer(1,13),
          p('Что можно копировать сразу','H2'),
          p('SEO основной страницы — для целевой сборки после согласования разделов. Alt подготовленных визуализаций — для точно соответствующего файла. Строки CL46 — в черновик; метки «УТОЧНИТЬ» заменить до публикации.'),
          p('Что требует подтверждения','H2'),
          p('Цены, состав комплектов, НДС, география и сроки; собственный/партнёрский парк мебели; фото и права; реальная модель рекламной конструкции и основания; фактический вывод alt в вашей версии ST340C.'),
          p('Не потеряйте фрезеровку','H2'),
          p('<link href="#milling" color="#236c8d">Раздел 13</link>: все 52 полученные ставки и минимальный заказ 10 000 сохранены без изменений. Минимум не относится к фотозонам или аренде.'),
          p('«Бриз» есть среди подготовленных визуализаций, но остаётся дополнительным кандидатом вне старой ведомости 42 позиций. Это не автоматическое расширение подтверждённого ассортимента.','Small'),
          PageBreak(),p('Содержание','H1')]
toc=TableOfContents()
toc.levelStyles=[styles['Toc']]
toc.dotsMinLevel=0
# Avoid a second contents page for one entry: no extra padded spacer rows.
toc.tableStyle=TableStyle([('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),7)])
story += [toc,PageBreak()]

source=(FOLDER/'README.md').read_text()
source=source[source.index('## Главное решение'):]
# Inline the complete SEO and table instructions: the deliverable is one PDF.
start=source.index('## 10. ')
end=source.index('\n## 11.',start)
source=source[:start]+(FOLDER/'seo-setup.md').read_text().rstrip()+'\n\n---\n'+source[end:]
start=source.index('## 14. ')
end=source.index('\n## Технические источники',start)
source=source[:start]+(FOLDER/'cl46-table.md').read_text().rstrip()+'\n'+source[end:]

start=source.index('**Подготовленные таблицы:**')
end=source.index('\n---',start)
source=source[:start]+'''**Всё находится в этом PDF:** полная инструкция, подборка 10 стульев и 10 кресел в разделе 5, рабочая ведомость на 42 позиции в приложении А, наглядное сравнение согласованных конструкций в приложении Б, реестр alt в приложении В, полный SEO-пакет в разделе 10, тарифы фрезеровки в разделе 13 и CL46 в разделе 14.

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
            if label.startswith(('10.','13.','14.')):
                story.append(PageBreak())
            elif section_idx:
                story.extend([CondPageBreak(230), Spacer(1, 17)])
            section_idx += 1
            key=next((key for prefix,key in [('5.','furniture'),('6.','setup'),('10.','seo'),('11.','launch'),('13.','milling'),('14.','cl46')] if label.startswith(prefix)),'chapter-'+str(section_idx))
            story.append(heading(label,key))
        else:
            subheading=p(inline(content.children),'H2' if t.tag=='h3' else 'H3')
            if t.tag=='h3' and label.startswith('10.'):
                # Detailed SEO navigation in the PDF sidebar, without bloating contents.
                subheading._child_key='seo-sub-'+label.split()[0].rstrip('.')
            story.append(subheading)
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

# The two newer advertising series remain separate assets, embedded here only as previews.
story += [PageBreak(),heading('Синие RollUp и три формы виндеров','advertising-visuals'),
          p('Типовые визуализации для выбора и оформления, не подтверждение складской модели. В карточку сайта загружать оригинал, не скриншот PDF.','Small')]
rollup=ROOT/'visualizations/catalog/rollup-sizes-blue/sm-production-rollup-blue-size-comparison.jpg'
winder=ROOT/'visualizations/catalog/winder-types-blue/sm-production-winder-types-comparison.jpg'
story += [cover_image(rollup,445),Spacer(1,8),cover_image(winder,CONTENT_W),Spacer(1,8),
          p('<link href="'+GH+'visualizations/catalog/rollup-sizes-blue/README.md" color="#236c8d">Оригиналы четырёх синих RollUp</link> · <link href="'+GH+'visualizations/catalog/winder-types-blue/README.md" color="#236c8d">Оригиналы трёх виндеров</link>','Small')]

# All alt data is visible inside the PDF; CSV is an optional editable source.
with (FOLDER/'image-alt-register.csv').open(encoding='utf-8-sig',newline='') as f:
    alt_rows=list(csv.DictReader(f,delimiter=';'))
assert len(alt_rows)==43
assert sum(bool(r['Файл']) for r in alt_rows)==19
assert len({r['Артикул_плана'] for r in alt_rows})==43
for r in alt_rows:
    if r['Файл']:
        assert (FOLDER/r['Файл']).is_file(),r['Файл']


def alt_table(group,ready):
    selected=[r for r in alt_rows if r['Группа']==group]
    rows=[['Файл / карточка' if ready else 'Кандидат / код плана','Готовый alt' if ready else 'Черновик — сверить с фото']]
    for r in selected:
        first='<b>'+escape(r['Карточка'])+'</b>'
        detail=Path(r['Файл']).name if r['Файл'] else r['Артикул_плана']
        first+='<br/><font size="7.1" color="#64717f">'+escape(detail)+'</font>'
        rows.append([first,escape(r['Alt'])])
    return table_block(rows,widths=[CONTENT_W*.46,CONTENT_W*.54])


story += [PageBreak(),heading('Приложение В. Alt по файлам: брус-баннеры','alt'),
          p('43 строки реестра: 19 подготовленных обложек и 24 условных текста для будущих фото. В этом приложении — все фразы; скачивать CSV не требуется. Копируйте только фразу из правой колонки.','Small'),
          p('<b>Готово для восьми основных обложек.</b> Размер — ширина × высота; синее оформление, люди для масштаба. Кадры без людей или другие принты требуют соответствующего изменения alt.','Small'),
          alt_table('Брус-баннеры',True),
          p('Имя файла под названием карточки нужно только для сопоставления. Alt не заменяет название, цену и описание товара. Путь заполнения и ограничение Каталога/ST340C — в разделе 10.5.','Small')]

story += [PageBreak(),heading('В.2. Alt для четырёх «Джокеров»','alt-joker'),
          p('Для обновлённой серии со светлым баннером и сеткой логотипов SM. Не описывайте эти файлы как синий принт или деревянный короб.','Small'),
          alt_table('Джокер',True),
          p('Дополнительные кадры и детали','H2'),
          p('Для действительно отдельного кадра крепления опишите видимое крепление; для изображения без людей не упоминайте людей. Если фото просто повторяет то же изделие без новой информации, не заполняйте alt рекламными ключами ради разнообразия.'),
          p('При использовании файла другого размера меняются и название, и alt. Для одной картинки в плитке и в карточке допустим один и тот же корректный текст; не меняйте в нём размер без замены файла.','Small')]

story += [PageBreak(),heading('В.3. Alt для RollUp и виндеров','alt-advertising'),
          p('Основной выбор для этой сборки — синие RollUp. Если публикуете светлую альтернативу, замените слова «с синим баннером» на описание светлого баннера с сеткой логотипов и сопоставьте другой файл.','Small'),
          alt_table('RollUp',True),
          p('Три формы виндеров','H2'),
          alt_table('Виндеры',True),
          p('«Бриз» — дополнительный кандидат вне ведомости 42 позиций; фраза alt не утверждает его наличие. Высота около 2,5 м — визуальный ориентир, поэтому точная высота поставляемой модели в alt не обещана.','Small')]

story += [PageBreak(),heading('В.4. Стулья: условные alt','alt-chairs'),
          p('<b>Это не готовые подписи к уже загруженным фото.</b> Фотографии в собственном каталоге ещё не выбраны. Для каждой строки сначала подтвердите модель, исполнение, цвет, наличие и права на снимок. Если реальное фото отличается, перепишите alt.','Small'),
          alt_table('Стулья',False),
          p('Коды — предлагаемые артикулы из ведомости, не реальные PRODUCT ID. Ссылки на страницы внешних моделей находятся в разделе 5. Цены и право на публикацию их фотографий не подтверждены.','Small')]

story += [PageBreak(),heading('В.5. Кресла: условные alt','alt-armchairs'),
          p('Та же проверка: выбранное разрешённое фото должно действительно показывать указанную модель и цвет. Не приписывайте предмету авторство, материал или конструктивные детали, которых не видно и которые не подтверждены.','Small'),
          alt_table('Кресла',False),
          p('После замены внешнего референса собственным снимком проверьте видимые детали и обновите alt. Простая ссылка на поставщика не даёт права копировать его изображения.','Small')]

story += [PageBreak(),heading('В.6. Шаблоны и особые случаи','alt-pending'),
          p('Для двух X-баннеров, LED-бара и мольберта подготовлены только шаблоны. <b>Квадратные скобки заполнить после выбора фото; публиковать эти строки как есть нельзя.</b>','Small'),
          alt_table('Требуются фото',False),
          p('Логотип, фон и декоративные элементы','H2'),
          p('Логотип-ссылка: «SM Production — на главную» либо эквивалентное доступное имя ссылки. Декоративному узору и дублирующему значку обычно нужен пустой alt, а не перечисление услуг. У CSS-фона alt отсутствует: важный предмет должен быть доступен также как изображение с описанием или в содержательном тексте.'),
          p('Финальная проверка','H2'),
          p('Сверьте файл → предмет → размер → оформление → alt в опубликованном выводе. Проверьте плитку, подробную карточку и мобильную версию. Не переносите черновые alt мебели на случайную фотографию и не считайте переименование файла заменой настройки alt.'),
          p('Если отдельного поля alt в Каталоге нет, действуйте по разделу 10.5: проверка фактического доступного имени и отдельная задача по шаблону при необходимости. В этом руководстве никаких скриптов на сайт не добавлено.','Small')]

OUTPUT.parent.mkdir(parents=True,exist_ok=True)
doc=GuideDoc(str(OUTPUT),pagesize=A4,leftMargin=MARGIN,rightMargin=MARGIN,topMargin=56,bottomMargin=48,
             title='Наши цены — настройка страницы Tilda, SEO и alt изображений',author='SM Production',
             subject='ST340C и CL46, готовые SEO-тексты, 43 alt, 20 моделей мебели, тарифы фрезеровки и заявки',
             creator='SM Production · Руководство по оформлению',pageCompression=1)
doc.multiBuild(story)
print(OUTPUT)
print(f'{OUTPUT.stat().st_size:,} bytes')
