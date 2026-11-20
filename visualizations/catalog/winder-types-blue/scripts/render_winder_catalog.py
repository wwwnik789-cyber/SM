#!/usr/bin/env python3
"""Three researched winder forms on the locked SM catalog set.

Parus, Kaplya and rectangular Briz are based on the shape families in the
linked manufacturer catalogs, not on copied product photos. All are shown
at approximately 2.5 m overall height with an illustrative indoor cross base.
Reuse the approved blue print, original SM logo, photographic room, camera
and the exact 160/185 cm people layer. No prior export is overwritten.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import zipfile

import cv2
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT.parent
ASSETS = ROOT / "assets"
COMMON_RENDERER = CATALOG / "rollup-sizes/scripts/render_rollup_catalog.py"
spec = importlib.util.spec_from_file_location("sm_catalog_common", COMMON_RENDERER)
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
PATTERN = base.BASE / "assets/print-pattern-clean.png"
LOGO = base.BASE / "assets/branding-extracted.png"
CANVAS = base.CANVAS
SS = base.SS
PPM = 700
BOTTOM = .30
TOP = 2.49
HEIGHT = 2.50
BASE_SPAN = .63
LOGO_WIDTH = .44
LOGO_CENTER_Y = 1.70
COMPARISON = "sm-production-winder-types-comparison.jpg"
SOURCES = {
    "selection": "https://houstonprint.ru/msk/stendy/flagshtok-vinder/",
    "shapes_and_sizes": "https://zakaz-flagov.ru/flagi-vindery/",
    "construction_and_bases": "https://maxiflag.ru/servises/flag-parus-vinder-kaplya/",
}
MODELS = [
    {"id": "parus", "name": "Парус", "width_m": .63,
     "description": "straight lower mast, curved sail crown, mostly straight free edge",
     "reference": "https://www.nordwerk.ru/products/flagshtoki-vinder-parus"},
    {"id": "kaplya", "name": "Капля", "width_m": .90,
     "description": "half-rounded crown, diagonal taper to the lower mast attachment",
     "reference": "https://www.nordwerk.ru/products/flagshtoki-kaplya"},
    {"id": "briz", "name": "Бриз", "width_m": .71,
     "description": "rectangular hanging flag on a vertical mast and horizontal upper arm",
     "reference": "https://www.nordwerk.ru/products/flagshtoki-vinder-briz"},
]


def stem(model: dict) -> str:
    return f"sm-production-winder-{model['id']}-blue-people"


def bezier(a, b, c, d, n=70) -> np.ndarray:
    t = np.linspace(0, 1, n)[:, None]
    return (1-t)**3*np.array(a)+3*(1-t)**2*t*np.array(b)+3*(1-t)*t**2*np.array(c)+t**3*np.array(d)


def flag_paths(model: dict):
    """Paths in local meters: x runs from the mast toward the free fabric edge."""
    w = model["width_m"]
    if model["id"] == "parus":
        crown = bezier([0,1.84],[0,2.18],[w*.45,TOP],[w,TOP])
        sleeve = np.vstack([[0,BOTTOM],crown])
        free_y = np.linspace(TOP,BOTTOM+.01,110)
        free = np.column_stack([w-.006*np.sin(np.linspace(0,3*np.pi,len(free_y)))**2,free_y])
        hem = bezier([w,BOTTOM+.01],[w*.68,BOTTOM+.027],[w*.32,BOTTOM-.008],[0,BOTTOM],30)
        outline = np.vstack([sleeve,free,hem])
    elif model["id"] == "kaplya":
        first = bezier([0,1.96],[0,2.253],[w*.224,TOP],[w*.5,TOP])
        second = bezier([w*.5,TOP],[w*.776,TOP],[w,2.28],[w,2.02])
        sleeve = np.vstack([[0,BOTTOM],first,second])
        diagonal = bezier([w,2.02],[w*.79,1.52],[w*.19,.60],[0,BOTTOM],100)
        outline = np.vstack([sleeve,diagonal])
    else:
        sleeve = np.array([[0,BOTTOM],[0,TOP],[w,TOP]],float)
        yy = np.linspace(TOP,BOTTOM+.012,125)
        free = np.column_stack([w-.009*np.sin(np.linspace(0,3*np.pi,len(yy)))**2,yy])
        hem = bezier([w,BOTTOM+.012],[w*.68,BOTTOM-.003],[w*.30,BOTTOM+.020],[0,BOTTOM],40)
        outline = np.vstack([sleeve,free,hem])
    return outline, sleeve


def texture(model: dict):
    w = model["width_m"]
    h = TOP-BOTTOM
    tw, th = round(w*PPM), round(h*PPM)
    outline, _ = flag_paths(model)
    shape = np.column_stack([outline[:,0]/w*(tw-1),(TOP-outline[:,1])/h*(th-1)])
    mask = Image.new("L",(tw,th),0)
    ImageDraw.Draw(mask).polygon([tuple(v) for v in shape],fill=255)
    image = Image.open(PATTERN).convert("RGB").resize((tw,th),Image.Resampling.LANCZOS).convert("RGBA")
    logo = Image.open(LOGO).convert("RGBA")
    lw = round(LOGO_WIDTH*PPM)
    lh = round(lw*logo.height/logo.width)
    mark = logo.resize((lw,lh),Image.Resampling.LANCZOS)
    cx = .34 if model["id"] == "kaplya" else w/2
    x = round(cx/w*tw-lw/2)
    y = round((TOP-LOGO_CENTER_Y)/h*th-lh/2)
    logo_area = np.array(mask.crop((x,y,x+lw,y+lh)))
    assert logo_area.shape == (lh,lw)
    assert not np.any((np.array(mark.getchannel("A"))>12)&(logo_area==0)), "The original logo must not be clipped by the shaped flag"
    image.alpha_composite(mark,(x,y))
    array = np.array(image.convert("RGB")).astype(float)
    yy,xx = np.mgrid[:th,:tw]
    u=xx/max(tw-1,1)
    v=yy/max(th-1,1)
    # Quiet fabric folds and edge seams, without inventing wind in the indoor scene.
    illumination=1-.022*u-.018*v
    illumination*=1+.026*np.sin(2*np.pi*(2.8*u+.10*np.sin(v*8)))*np.power(u,.7)
    illumination*=1-.020*np.exp(-u*32)
    distance=cv2.distanceTransform(np.array(mask),cv2.DIST_L2,3)
    illumination*=1-.12*np.exp(-distance/2.6)
    array=np.rint(array*illumination[:,:,None]).clip(0,255).astype(np.uint8)
    return array,np.array(mask),{"logo_width_m":LOGO_WIDTH,
                                 "logo_center_local_xy_m":[cx,LOGO_CENTER_Y],
                                 "logo_uniform_scale":True,"logo_fully_inside_fabric":True}


def local_world(points,model,z=0.0):
    points=np.asarray(points,float)
    return np.column_stack([points[:,0]-model["width_m"]/2,points[:,1],np.full(len(points),z)])


def tube(image: Image.Image,points,diameter=.020,sleeve=False):
    pp=base.project(points)*SS
    midpoint=np.asarray(points)[len(points)//2]
    measure=base.project([midpoint+[-diameter/2,0,0],midpoint+[diameter/2,0,0]])
    width=max(1.8,np.linalg.norm(measure[1]-measure[0]))*SS
    draw=ImageDraw.Draw(image)
    path=[tuple(p) for p in pp]
    draw.line(path,fill=(30,34,37,255),width=round(width+SS*.45),joint="curve")
    if sleeve:
        draw.line(path,fill=(43,47,49,255),width=max(1,round(width*.72)),joint="curve")
        highlight=pp+np.array([-.23,-.16])*SS
        draw.line([tuple(p) for p in highlight],fill=(97,102,103,255),width=max(1,round(width*.15)),joint="curve")
    else:
        draw.line(path,fill=(158,166,169,255),width=max(1,round(width*.73)),joint="curve")
        highlight=pp+np.array([-.28,-.15])*SS
        draw.line([tuple(p) for p in highlight],fill=(226,229,225,255),width=max(1,round(width*.24)),joint="curve")


def cross_base(image: Image.Image,model: dict):
    x=-model["width_m"]/2
    metal=base.Hardware(image)
    r=BASE_SPAN/2
    arm=.022
    metal.box(x-r,x+r,.006,.016,-arm,arm,"cap")
    metal.box(x-arm,x+arm,.016,.026,-r,r,"cap")
    # Low spindle and a collar, rather than the cassette of a RollUp.
    metal.box(x-.030,x+.030,.026,.075,-.030,.030,"aluminum")
    metal.box(x-.017,x+.017,.075,.108,-.017,.017,"cap")
    for bx,bz in [(x-r,0),(x+r,0),(x,-r),(x,r)]:
        metal.box(bx-.016,bx+.016,0,.009,bz-.018,bz+.018,"rubber")
    tube(image,[[x,.070,0],[x,BOTTOM+.02,0]],.020)
    return [[x-r,0,0],[x+r,0,0],[x,0,-r],[x,0,r]]


def render_product(model: dict):
    size=(CANVAS[0]*SS,CANVAS[1]*SS)
    image=Image.new("RGBA",size,(0,0,0,0))
    feet=cross_base(image,model)
    outline,sleeve=flag_paths(model)
    mast=local_world(sleeve,model)
    # Structure behind the fabric, followed by the sewn pocket on its front edge.
    tube(image,np.vstack([[[mast[0,0],.10,0]],mast]),.020)
    if model["id"]=="briz":
        tube(image,local_world([[0,.10],[0,TOP+.008],[model["width_m"]+.024,TOP+.008]],model),.020)
    rgb,alpha,layout=texture(model)
    th,tw=alpha.shape
    w=model["width_m"]
    quad=base.project(local_world([[0,TOP],[w,TOP],[w,BOTTOM],[0,BOTTOM]],model,-.003))
    source=np.float32([[0,0],[tw-1,0],[tw-1,th-1],[0,th-1]])
    transform=cv2.getPerspectiveTransform(source,np.float32(quad*SS))
    color=cv2.warpPerspective(rgb,transform,size,flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_REPLICATE)
    a=cv2.warpPerspective(alpha,transform,size,flags=cv2.INTER_LINEAR)
    image.alpha_composite(Image.fromarray(np.dstack([color,a])))
    paper=cv2.resize(a,CANVAS,interpolation=cv2.INTER_AREA).astype(float)/255
    tube(image,local_world(sleeve,model,-.004),.025,sleeve=True)
    # A real lower attachment to the mast, not a perimeter frame.
    x=-w/2
    attach=base.project([[x,BOTTOM,-.004],[x,.255,0]])*SS
    ImageDraw.Draw(image).line([tuple(p) for p in attach],fill=(67,72,73,255),width=2*SS)
    metal=base.Hardware(image)
    for y in [1.15,1.78]:
        metal.box(x-.013,x+.013,y,y+.018,-.014,.014,"cap")
    rgba=np.array(image)
    ah=rgba[:,:,3].astype(np.float32)/255
    pm=cv2.resize(rgba[:,:,:3].astype(np.float32)*ah[:,:,None],CANVAS,interpolation=cv2.INTER_AREA)
    coverage=cv2.resize(ah,CANVAS,interpolation=cv2.INTER_AREA)
    geometry={"flag_outline_local_m":np.round(outline,6).tolist(),
              "flag_outline_px":np.round(base.project(local_world(outline,model,-.003)),6).tolist(),
              "mast_curve_px":np.round(base.project(mast),6).tolist(),
              "feet_endpoints_px":np.round(base.project(feet),6).tolist(),
              "cloth_bounding_quad_px":np.round(quad,6).tolist(),"print_layout":layout}
    return pm,coverage,paper,geometry


def floor_shadow(model: dict):
    outline,_=flag_paths(model)
    world=local_world(outline,model)
    cast=np.column_stack([world[:,0]+.50*world[:,1],np.zeros(len(world)),.67*world[:,1]])
    x=-model["width_m"]/2
    points=np.vstack([[[x,0,0]],cast])
    size=(CANVAS[0]*SS,CANVAS[1]*SS)
    mask=np.zeros((size[1],size[0]),np.uint8)
    hull=cv2.convexHull(np.rint(base.project(points)*SS).astype(np.int32))
    cv2.fillConvexPoly(mask,hull,255,cv2.LINE_AA)
    broad=cv2.GaussianBlur(mask,(0,0),6*SS).astype(float)/255*.085
    core=cv2.GaussianBlur(mask,(0,0),2.1*SS).astype(float)/255*.07
    contact=np.zeros_like(mask)
    r=BASE_SPAN/2
    for ends in [[[x-r,0,0],[x+r,0,0]],[[x,0,-r],[x,0,r]]]:
        q=np.rint(base.project(ends)*SS).astype(np.int32)
        cv2.line(contact,tuple(q[0]),tuple(q[1]),255,round(4*SS),cv2.LINE_AA)
    tight=cv2.GaussianBlur(contact,(0,0),1.3*SS).astype(float)/255*.28
    shadow=1-(1-broad)*(1-core)*(1-tight)
    return np.rint(cv2.resize(shadow,CANVAS,interpolation=cv2.INTER_AREA)*255).astype(np.uint8)


def overview(items):
    tw,th,gap,header,caption=632,424,24,144,64
    board=Image.new("RGB",(tw*3+gap*4,header+th+caption+gap*2),"#f3f4f6")
    draw=ImageDraw.Draw(board)
    draw.text((gap,20),"SM PRODUCTION / ВИНДЕРЫ",font=base.font(17,True),fill="#99752b")
    draw.text((gap,50),"Парус · Капля · Бриз — три распространённые формы",font=base.font(29,True),fill="#17283d")
    draw.text((gap,99),"Синий брендинг SM · высота около 2,5 м · девушка 160 см, мужчина 185 см · единый фон и масштаб",font=base.font(17),fill="#576579")
    for i,item in enumerate(items):
        x=gap+i*(tw+gap)
        y=header+gap
        tile=Image.open(ROOT/item["files"]["png"]).convert("RGB").resize((tw,th),Image.Resampling.LANCZOS)
        board.paste(tile,(x,y))
        draw.rectangle((x,y+th,x+tw-1,y+th+caption-1),fill="white")
        draw.text((x+18,y+th+16),f"{item['name']} · ≈2,5 м",font=base.font(24,True),fill="#17283d")
    base.save_image(board,ROOT/COMPARISON)


def verify():
    manifest=json.loads((ROOT/"manifest.json").read_text())
    assert manifest["camera_matrix"]==base.CALIBRATION["camera_matrix"]
    assert manifest["people"]==base.PEOPLE_METADATA
    assert [x["id"] for x in manifest["items"]]==[x["id"] for x in MODELS]
    assert base.sha(base.BACKGROUND)==manifest["background_sha256"]
    assert base.sha(base.PEOPLE)==manifest["people_layer_sha256"]
    assert base.sha(LOGO)==manifest["banner_design"]["logo_sha256"]
    assert base.sha(PATTERN)==manifest["banner_design"]["pattern_sha256"]
    assert base.sha(COMMON_RENDERER)==manifest["common_renderer_sha256"]
    bg=base.read_rgb(base.BACKGROUND)
    people=np.array(Image.open(base.PEOPLE).convert("RGBA"))
    opaque=people[:,:,3]==255
    common=np.array(Image.open(ASSETS/"common-background-check-mask.png").convert("L"))>0
    for item,model in zip(manifest["items"],MODELS):
        for f in item["files"].values():
            with Image.open(ROOT/f) as image:
                assert image.size==CANVAS
                image.verify()
        image=base.read_rgb(ROOT/item["files"]["png"])
        assert np.array_equal(image[common],bg[common]),"Room changed"
        assert np.array_equal(image[opaque],people[:,:,:3][opaque]),"People changed"
        outline,_=flag_paths(model)
        expected=base.project(local_world(outline,model,-.003))
        assert np.allclose(expected,item["flag_outline_px"],atol=.001)
        assert item["height_m_visualization"]==HEIGHT
        assert item["print_layout"]["logo_fully_inside_fabric"]
        for key in ["flag_outline_px","mast_curve_px","feet_endpoints_px"]:
            q=np.array(item[key])
            assert np.all((q[:,0]>0)&(q[:,0]<CANVAS[0]))
            assert np.all((q[:,1]>0)&(q[:,1]<CANVAS[1]))
    assert manifest["common_background_pixels"]==int(common.sum())
    print(f"Verified three shapes / nine exports, {int(common.sum()):,} locked room pixels and {int(opaque.sum()):,} unchanged opaque person pixels per PNG.")


def package(items):
    full=[ROOT/f for item in items for f in item["files"].values()]
    full += [ROOT/COMPARISON,ROOT/"manifest.json",ROOT/"DOWNLOAD-NOTES.txt"]
    for name,files in [("sm-production-winder-blue-catalog.zip",full),
                       ("sm-production-winder-blue-jpg.zip",[ROOT/x["files"]["jpg"] for x in items])]:
        with zipfile.ZipFile(ROOT/name,"w",zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for f in files:z.write(f,f.name)
        with zipfile.ZipFile(ROOT/name) as z:
            assert len(z.namelist())==len(files)
            assert z.testzip() is None
            assert all(z.read(f.name)==f.read_bytes() for f in files)
        print(f"ZIP CRC passed: {name}, {len(files)} entries, {(ROOT/name).stat().st_size:,} bytes.")


def render():
    ASSETS.mkdir(parents=True,exist_ok=True)
    bg=base.read_rgb(base.BACKGROUND)
    people=np.array(Image.open(base.PEOPLE).convert("RGBA"))
    pa=people[:,:,3].astype(float)/255
    ppm=people[:,:,:3].astype(float)*pa[:,:,None]
    pf=np.array(Image.open(base.HUMANS/"assets/people-floor-shadow.png").convert("L")).astype(float)/255
    pw=np.array(Image.open(base.HUMANS/"assets/people-wall-shadow.png").convert("L")).astype(float)/255
    union=pa>0
    items=[]
    for model in MODELS:
        pm,alpha,paper,geometry=render_product(model)
        ps=floor_shadow(model).astype(float)/255
        shade=1-(1-ps)*(1-pf*(1-alpha))
        shaded_bg=bg.astype(float)*(1-shade[:,:,None])
        subject=pm*(1-(pw*paper)[:,:,None])+shaded_bg*(1-alpha[:,:,None])
        final=np.rint(subject*(1-pa[:,:,None])+ppm).clip(0,255).astype(np.uint8)
        local=(alpha>0)|(ps>0)|((pf*(1-alpha))>.001)|(pa>0)
        assert np.array_equal(final[~local],bg[~local])
        union |= local
        files={}
        for ext in ["png","jpg","webp"]:
            name=f"{stem(model)}.{ext}"
            base.save_image(Image.fromarray(final),ROOT/name)
            files[ext]=name
        items.append({**model,"height_m_visualization":HEIGHT,
                      "nominal_fabric_max_size_cm_reference":[round(model["width_m"]*100),220],
                      "canvas_px":list(CANVAS),"files":files,**geometry})
        print(f"Rendered winder {model['name']}, approximately 2.5 m, original blue SM branding.")
    Image.fromarray((~union).astype(np.uint8)*255).save(ASSETS/"common-background-check-mask.png",compress_level=9)
    manifest={
        "title":"SM Production — Parus, Kaplya and Briz winders with blue branding",
        "canvas_px":list(CANVAS),"camera_matrix":base.P.tolist(),
        "camera_policy":"Approved fixed catalog room, camera, floor origin and people; no per-type zoom or crop.",
        "background":"../presswalls-sizes/assets/background-locked.png","background_sha256":base.sha(base.BACKGROUND),
        "people_layer":"../presswalls-with-people/assets/people-layer-160-185.png","people_layer_sha256":base.sha(base.PEOPLE),
        "people_heights_cm":[160,185],"people":base.PEOPLE_METADATA,
        "common_renderer":"../rollup-sizes/scripts/render_rollup_catalog.py","common_renderer_sha256":base.sha(COMMON_RENDERER),
        "selection":{"policy":"Three widely offered shape families, not a measured sales ranking. Do not treat supplier prices or stock as SM data.","sources":SOURCES},
        "construction":{"height_m_visualization":HEIGHT,"base_type":"illustrative indoor four-arm cross base",
                        "base_span_m_visual_assumption":BASE_SPAN,
                        "mast_diameter_m_visual_assumption":.020,
                        "note":"Generic visual models based on public shape/size references, not exact supplier products or fabrication templates. Confirm dimensions, material, printing, base, ballast and outdoor operating limits before sale/production."},
        "banner_design":{"style":"Previous SM blue geometric print with a white/gold cube, SM PRODUCTION wordmark and tagline",
                         "pattern":"../presswalls-sizes/assets/print-pattern-clean.png","pattern_sha256":base.sha(PATTERN),
                         "logo":"../presswalls-sizes/assets/branding-extracted.png","logo_sha256":base.sha(LOGO),
                         "logo_width_m":LOGO_WIDTH,"logo_policy":"Original logo, uniform scaling, never clipped by the shaped fabric."},
        "common_background_pixels":int((~union).sum()),"items":items
    }
    (ROOT/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")
    overview(items)
    verify()
    package(items)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check",action="store_true",help="Validate existing outputs without rerendering")
    args=parser.parse_args()
    verify() if args.check else render()
