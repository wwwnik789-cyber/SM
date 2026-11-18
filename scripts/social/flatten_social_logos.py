"""Делает «плоскую» версию листа логотипов соцсетей, которая открывается в любой программе.

Исходник (public/media/social-logos.svg из ветки arena/ccaea285-sm) собран на <symbol> + <use href="…">
(синтаксис SVG 2). Illustrator, CorelDRAW, старый Inkscape, просмотрщики Windows и многие
конвертеры такой <use> не понимают — подписи (обычные path) видны, а сами логотипы нет.

Здесь каждый <use> заменяется на копию содержимого символа с явным transform,
градиенты и clipPath переносятся в общий <defs>, символы удаляются.
Дополнительно в комплект добавляется MAX (мессенджер VK): знак-«облачко» с max.ru на градиентной
плашке приложения. Лист перестраивается в сетку 5 × 2 (1600 × 480), MAX стоит рядом с Telegram.
На выходе: social-logos_flat.svg, PNG всего листа и каждого логотипа отдельно (SVG + PNG).

Запуск: python3 scripts/social/flatten_social_logos.py <исходный.svg>
PNG рендерятся через node + @resvg/resvg-js (.cache/resvg/render.js), если он установлен.
"""
import copy
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "assets/social-logos"
SVG_NS = "http://www.w3.org/2000/svg"
XLINK = "http://www.w3.org/1999/xlink"
ET.register_namespace("", SVG_NS)
ET.register_namespace("xlink", XLINK)
q = lambda t: f"{{{SVG_NS}}}{t}"


def vb(sym):
    return [float(v) for v in re.split(r"[ ,]+", sym.get("viewBox").strip())]


def flatten(src):
    tree = add_max(src)
    root = tree.getroot()
    defs = root.find(q("defs"))
    symbols = {s.get("id"): s for s in defs.findall(q("symbol"))}
    new_defs = ET.Element(q("defs"))
    content = {}
    for sid, sym in symbols.items():
        kids = []
        for ch in list(sym):
            if ch.tag == q("defs"):
                for d in ch:
                    new_defs.append(copy.deepcopy(d))
            else:
                kids.append(ch)
        content[sid] = kids
    # заменить <use> на <g transform>
    parents = {c: p for p in root.iter() for c in p}
    singles = {}
    for use in list(root.iter(q("use"))):
        href = (use.get("href") or use.get(f"{{{XLINK}}}href"))[1:]
        x, y = float(use.get("x", 0)), float(use.get("y", 0))
        w, h = float(use.get("width")), float(use.get("height"))
        vx, vy, vw, vh = vb(symbols[href])
        s = min(w / vw, h / vh)
        tx = x + (w - vw * s) / 2 - vx * s
        ty = y + (h - vh * s) / 2 - vy * s
        g = ET.Element(q("g"), {"id": href, "transform": f"translate({tx:.3f} {ty:.3f}) scale({s:.5f})"})
        for ch in content[href]:
            g.append(copy.deepcopy(ch))
        p = parents[use]
        p.insert(list(p).index(use), g)
        p.remove(use)
        singles[href] = (vx, vy, vw, vh)
    root.remove(defs)
    if len(new_defs):
        root.insert(list(root).index(root.find(q("desc"))) + 1, new_defs)
    desc = root.find(q("desc"))
    if desc is not None:
        desc.text = re.sub(r"Каждый знак доступен отдельно через symbol[^.]*\.\s*", "", desc.text)
    return tree, symbols, content, new_defs, singles


def single_svg(sid, symbols, content, defs_all):
    vx, vy, vw, vh = vb(symbols[sid])
    root = ET.Element(q("svg"), {"width": "512", "height": f"{512 * vh / vw:.0f}", "viewBox": f"{vx} {vy} {vw} {vh}"})
    used = set(re.findall(r"url\(#([^)]+)\)", "".join(ET.tostring(c, encoding="unicode") for c in content[sid])))
    d = [x for x in defs_all if x.get("id") in used]
    if d:
        de = ET.SubElement(root, q("defs"))
        for x in d:
            de.append(copy.deepcopy(x))
    for ch in content[sid]:
        root.append(copy.deepcopy(ch))
    return ET.ElementTree(root)


# ---------------------------------------------------------------- MAX
# знак «облачко» — с сайта max.ru (тот же контур используют сторонние сборки иконок); плашка — градиент приложения
MAX_GLYPH = ("M21.47 41.88c-4.11 0-6.02-.6-9.34-3-2.1 2.7-8.75 4.81-9.04 1.2 0-2.71-.6-5-1.28-7.5C1 29.5.08 26.07"
             ".08 21.1.08 9.23 9.82.3 21.36.3c11.55 0 20.6 9.37 20.6 20.91a20.6 20.6 0 0 1-20.49 20.67Zm.17-31.32"
             "c-5.62-.29-10 3.6-10.97 9.7-.8 5.05.62 11.2 1.83 11.52.58.14 2.04-1.04 2.95-1.95a10.4 10.4 0 0 0 5.08 "
             "1.81 10.7 10.7 0 0 0 11.19-9.97 10.7 10.7 0 0 0-10.08-11.1Z")
MAX_GRAD = [("0", "#20C7FF"), ("0.55", "#3A58FF"), ("1", "#A23BFF")]
LABEL_FONT = "DejaVuSans.ttf"            # как у остальных подписей листа: DejaVu Sans 20 px, #20242D, в кривых
COLS, TILE_W, TILE_H = 5, 320, 240
ORDER = ["vkontakte", "pinterest", "telegram", "max", "dzen",
         "youtube", "rutube", "yandex-maps", "yandex-uslugi", "avito"]


def max_symbol():
    sym = ET.Element(q("symbol"), {"id": "logo-max", "viewBox": "0 0 48 48"})
    de = ET.SubElement(sym, q("defs"))
    lg = ET.SubElement(de, q("linearGradient"), {"id": "social-max-gradient", "x1": "4", "y1": "46", "x2": "44",
                                                 "y2": "2", "gradientUnits": "userSpaceOnUse"})
    for off, col in MAX_GRAD:
        ET.SubElement(lg, q("stop"), {"offset": off, "stop-color": col})
    ET.SubElement(sym, q("rect"), {"width": "48", "height": "48", "rx": "11.5", "fill": "url(#social-max-gradient)"})
    ET.SubElement(sym, q("path"), {"fill": "#FFFFFF", "fill-rule": "evenodd", "clip-rule": "evenodd",
                                   "transform": "translate(9.6 9.4) scale(0.69)", "d": MAX_GLYPH})
    return sym


def label_path(text, cx, baseline, size=20):
    import matplotlib
    from fontTools.pens.svgPathPen import SVGPathPen
    from fontTools.pens.transformPen import TransformPen
    from fontTools.ttLib import TTFont
    font = TTFont(str(Path(matplotlib.__file__).parent / "mpl-data/fonts/ttf" / LABEL_FONT))
    gs, cmap, hmtx = font.getGlyphSet(), font.getBestCmap(), font["hmtx"]
    k = size / font["head"].unitsPerEm
    width = sum(hmtx[cmap[ord(c)]][0] for c in text) * k
    pen = SVGPathPen(gs)
    x = cx - width / 2
    for c in text:
        g = cmap[ord(c)]
        gs[g].draw(TransformPen(pen, (k, 0, 0, -k, x, baseline)))
        x += hmtx[g][0] * k
    return pen.getCommands()


def add_max(src):
    """Исходник + символ MAX + плитка MAX → временное дерево (дальше обычное «уплощение»)."""
    tree = ET.parse(src)
    root = tree.getroot()
    root.find(q("defs")).append(max_symbol())
    grid = root.find(q("g"))
    tiles = {t.get("id").replace("tile-", ""): t for t in grid.findall(q("g"))}
    old = list(tiles)                                        # исходный порядок 3 × 3
    tile = ET.Element(q("g"), {"id": "tile-max"})
    ET.SubElement(tile, q("use"), {"href": "#logo-max", "x": "88", "y": "44", "width": "144", "height": "112"})
    ET.SubElement(tile, q("path"), {"id": "label-max", "data-label": "MAX", "fill": "#20242D",
                                    "d": label_path("MAX", 160, 192)})
    tiles["max"] = tile
    for t in list(grid):
        grid.remove(t)
    for i, name in enumerate(ORDER):
        ox, oy = (old.index(name) % 3, old.index(name) // 3) if name in old else (0, 0)
        nx, ny = i % COLS, i // COLS
        dx, dy = (nx - ox) * TILE_W, (ny - oy) * TILE_H
        wrap = ET.SubElement(grid, q("g"), {"transform": f"translate({dx} {dy})"} if (dx or dy) else {})
        wrap.append(tiles[name])
    W_, H_ = COLS * TILE_W, 2 * TILE_H
    root.set("width", str(W_)); root.set("height", str(H_)); root.set("viewBox", f"0 0 {W_} {H_}")
    root.find(q("title")).text = "Логотипы социальных сетей, мессенджеров и площадок"
    d = root.find(q("desc"))
    d.text = (d.text.replace("Telegram, Дзен", "Telegram, MAX, Дзен").replace("Девять", "Десять")
              .replace("сетка 3 на 3", "сетка 5 на 2"))
    return tree


def render(svg, png, width):
    js = ROOT / ".cache/resvg/render.js"
    if js.exists():
        subprocess.run(["node", str(js), str(svg), str(png), str(width)], check=True)


def main(src):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "single").mkdir(exist_ok=True)
    tree, symbols, content, defs_all, _ = flatten(src)
    flat = OUT / "social-logos_flat.svg"
    tree.write(flat, encoding="UTF-8", xml_declaration=True)
    render(flat, OUT / "social-logos.png", 3200)
    try:                                   # вариант на белом фоне (для просмотрщиков с тёмной темой)
        from PIL import Image
        im = Image.open(OUT / "social-logos.png").convert("RGBA")
        bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
        bg.alpha_composite(im)
        bg.convert("RGB").save(OUT / "social-logos_white.jpg", quality=95)
    except (ImportError, FileNotFoundError):
        pass
    for sid in symbols:
        name = sid.replace("logo-", "")
        p = OUT / "single" / f"{name}.svg"
        single_svg(sid, symbols, content, defs_all).write(p, encoding="UTF-8", xml_declaration=True)
        render(p, OUT / "single" / f"{name}.png", 512)
    print("✓", flat.relative_to(ROOT), "+ PNG,", len(symbols), "логотипов по отдельности")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ROOT / ".cache/soc/social-logos.svg")
