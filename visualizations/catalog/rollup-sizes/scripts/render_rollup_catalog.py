#!/usr/bin/env python3
"""RollUp catalog: four widths on the locked SM room/camera/people set.

Sizes describe the visible 200 cm print, not a particular manufacturer's
cassette or print bleed. Generic hardware is constructed in meters: a low
retractable aluminum cassette, two swivel feet, a rear mast and a top clamp.
The approved navy/gold SM mark is repeated on the same light vinyl style as
the Joker PressWall series. No room or person is regenerated or resized.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import zipfile

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT.parent
BASE = CATALOG / "presswalls-sizes"
HUMANS = CATALOG / "presswalls-with-people"
JOKER = CATALOG / "joker-sizes"
ASSETS = ROOT / "assets"
BACKGROUND = BASE / "assets/background-locked.png"
PEOPLE = HUMANS / "assets/people-layer-160-185.png"
PRINT_LOGO = JOKER / "assets/sm-logo-presswall-navy-gold.png"
CALIBRATION = json.loads((BASE / "manifest.json").read_text())
PEOPLE_METADATA = json.loads((HUMANS / "manifest.json").read_text())["people"]
P = np.array(CALIBRATION["camera_matrix"], float)
_, _, _vt = np.linalg.svd(P)
CAMERA_CENTER = _vt[-1, :3] / _vt[-1, 3]
CANVAS = (1264, 848)
SS = 3
PPM = 600
SIZES_CM = [(85, 200), (100, 200), (120, 200), (150, 200)]
PRINT_BOTTOM = 0.085
PRINT_Z = -0.012
CASSETTE_CENTER_Y = 0.048
CASSETTE_RADIUS_Y = 0.041
CASSETTE_RADIUS_Z = 0.066
CASSETTE_EXTRA_WIDTH = 0.075
FOOT_LENGTH = 0.34
FOOT_WIDTH = 0.035
FOOT_HEIGHT = 0.008
LOGO_WIDTH = 0.30
LOGO_PITCH_X = 0.36
LOGO_PITCH_Y = 0.36
LOGO_MARGIN = 0.04
LIGHT = np.array([-0.65, 1.15, -1.0], float)
LIGHT /= np.linalg.norm(LIGHT)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_rgb(path: Path) -> np.ndarray:
    return np.array(Image.open(path).convert("RGB"))


def project(points) -> np.ndarray:
    points = np.asarray(points, float)
    q = (P @ np.column_stack([points, np.ones(len(points))]).T).T
    return q[:, :2] / q[:, 2:]


def stem(w_cm: int, h_cm: int) -> str:
    return f"sm-production-rollup-{w_cm}x{h_cm}-people"


def label(w_cm: int, h_cm: int) -> str:
    return f"{w_cm} × {h_cm} см"


def save_image(image: Image.Image, path: Path) -> None:
    if path.suffix == ".png":
        image.save(path, compress_level=9)
    elif path.suffix == ".jpg":
        image.save(path, quality=95, subsampling=0, optimize=True, progressive=True)
    elif path.suffix == ".webp":
        image.save(path, quality=92, method=6)
    else:
        raise ValueError(path.suffix)


def grid_layout(w: float, h: float) -> dict:
    with Image.open(PRINT_LOGO) as logo:
        mark_height = LOGO_WIDTH * logo.height / logo.width
    columns = max(1, math.floor((w-LOGO_WIDTH-2*LOGO_MARGIN) / LOGO_PITCH_X + 1e-8) + 1)
    rows = max(1, math.floor((h-mark_height-2*LOGO_MARGIN) / LOGO_PITCH_Y + 1e-8) + 1)
    return {"columns": columns, "rows": rows, "logo_count": columns*rows,
            "logo_width_m": LOGO_WIDTH, "logo_height_m": round(mark_height, 6),
            "pitch_x_m": LOGO_PITCH_X, "pitch_y_m": LOGO_PITCH_Y,
            "alignment": "centered regular grid, fixed physical mark size in all four widths"}


def banner_texture(w: float, h: float) -> np.ndarray:
    tw, th = round(w*PPM), round(h*PPM)
    image = Image.new("RGBA", (tw, th), (244, 243, 238, 255))
    logo = Image.open(PRINT_LOGO).convert("RGBA")
    lw = round(LOGO_WIDTH*PPM)
    lh = round(lw*logo.height/logo.width)
    mark = logo.resize((lw, lh), Image.Resampling.LANCZOS)
    grid = grid_layout(w, h)
    for row in range(grid["rows"]):
        cy = th/2 + (row-(grid["rows"]-1)/2)*LOGO_PITCH_Y*PPM
        for col in range(grid["columns"]):
            cx = tw/2 + (col-(grid["columns"]-1)/2)*LOGO_PITCH_X*PPM
            image.alpha_composite(mark, (round(cx-lw/2), round(cy-lh/2)))
    rgb = np.array(image.convert("RGB")).astype(float)
    yy, xx = np.mgrid[:th, :tw]
    # The same quiet daylight falloff as the light Joker banner, without grommets.
    illumination = 1 - .022*xx/max(tw-1, 1) - .018*yy/max(th-1, 1)
    # Very small edge and lower-roller tension shading: no thick box or sidewalls.
    edge = np.exp(-xx/9) + np.exp(-(tw-1-xx)/9)
    lower = np.exp(-(th-1-yy)/20)
    illumination *= 1 - .020*edge - .016*lower
    rgb *= illumination[:, :, None]
    return np.rint(rgb).clip(0, 255).astype(np.uint8)


class Hardware:
    """Supersampled opaque metal, with physical camera culling and broad highlights."""
    def __init__(self, image: Image.Image):
        self.image = image
        self.draw = ImageDraw.Draw(image)

    def polygon(self, vertices, fill) -> None:
        xy = project(vertices)*SS
        self.draw.polygon([tuple(p) for p in xy], fill=tuple(fill)+(255,))

    def line(self, points, fill, width_px: float = 1.0) -> None:
        xy = project(points)*SS
        self.draw.line([tuple(p) for p in xy], fill=tuple(fill)+(255,), width=max(1, round(width_px*SS)))

    def color(self, normal, center, material="aluminum", band=0.0):
        normal = np.asarray(normal, float)
        normal /= max(np.linalg.norm(normal), 1e-12)
        view = CAMERA_CENTER - np.asarray(center, float)
        view /= np.linalg.norm(view)
        half = LIGHT+view
        half /= np.linalg.norm(half)
        diffuse = max(0.0, float(normal@LIGHT))
        specular = max(0.0, float(normal@half))**50
        if material == "rubber":
            value = 29 + 20*diffuse + 8*specular
        elif material == "cap":
            value = 58 + 47*diffuse + 36*specular
        else:
            # Soft room reflection bands keep the housing from reading as flat gray.
            reflection = 1 - .16*math.exp(-((band+.20)/.10)**2) + .08*math.exp(-((band-.20)/.12)**2)
            value = (128 + 86*diffuse + 45*specular)*reflection
        return tuple(np.rint(np.clip([value*.98, value*.995, value*1.015], 0, 250)).astype(int))

    def cylinder_x(self, left, right, cy, cz, ry, rz, material="aluminum", caps=(True, True)) -> None:
        """Extruded ellipse, including endcaps; visible front/top are depth sorted."""
        angles = np.linspace(-math.pi, math.pi, 121)
        faces = []
        for a, b in zip(angles, angles[1:]):
            middle = (a+b)/2
            normal = np.array([0, math.cos(middle)/ry, math.sin(middle)/rz])
            center = np.array([(left+right)/2, cy+ry*math.cos(middle), cz+rz*math.sin(middle)])
            if normal@(CAMERA_CENTER-center) <= 0:
                continue
            vertices = [[left, cy+ry*math.cos(a), cz+rz*math.sin(a)],
                        [right, cy+ry*math.cos(a), cz+rz*math.sin(a)],
                        [right, cy+ry*math.cos(b), cz+rz*math.sin(b)],
                        [left, cy+ry*math.cos(b), cz+rz*math.sin(b)]]
            distance = np.linalg.norm(center-CAMERA_CENTER)
            faces.append((distance, vertices, self.color(normal, center, material, math.sin(middle))))
        for x, normal, enabled in [(left, [-1,0,0], caps[0]), (right, [1,0,0], caps[1])]:
            center = np.array([x, cy, cz])
            if not enabled or np.dot(normal, CAMERA_CENTER-center) <= 0:
                continue
            vertices = [[x,cy+ry*math.cos(a),cz+rz*math.sin(a)] for a in angles]
            faces.append((np.linalg.norm(center-CAMERA_CENTER), vertices, self.color(normal, center, material)))
        for _, vertices, color in sorted(faces, key=lambda f:f[0], reverse=True):
            self.polygon(vertices, color)

    def box(self, x0, x1, y0, y1, z0, z1, material="aluminum") -> None:
        faces = [
            ([[x0,y0,z0],[x1,y0,z0],[x1,y1,z0],[x0,y1,z0]], [0,0,-1]),
            ([[x0,y0,z1],[x1,y0,z1],[x1,y1,z1],[x0,y1,z1]], [0,0,1]),
            ([[x0,y1,z0],[x1,y1,z0],[x1,y1,z1],[x0,y1,z1]], [0,1,0]),
            ([[x0,y0,z0],[x1,y0,z0],[x1,y0,z1],[x0,y0,z1]], [0,-1,0]),
            ([[x0,y0,z0],[x0,y1,z0],[x0,y1,z1],[x0,y0,z1]], [-1,0,0]),
            ([[x1,y0,z0],[x1,y1,z0],[x1,y1,z1],[x1,y0,z1]], [1,0,0]),
        ]
        visible=[]
        for vertices, normal in faces:
            center=np.mean(vertices,axis=0)
            if np.dot(normal,CAMERA_CENTER-center)>0:
                visible.append((np.linalg.norm(center-CAMERA_CENTER),vertices,self.color(normal,center,material)))
        for _,vertices,color in sorted(visible,key=lambda f:f[0],reverse=True):
            self.polygon(vertices,color)

    def vertical_mast(self, x, low, high, z) -> None:
        # Rear support, never a side frame around the graphic.
        segments=21
        for i in range(segments):
            a=-.007+i*.014/segments
            b=-.007+(i+1)*.014/segments
            value=round(83+145*math.exp(-((i/segments-.35)/.29)**2))
            self.polygon([[x+a,low,z],[x+b,low,z],[x+b,high,z],[x+a,high,z]],(value,value,min(255,value+3)))
        self.box(x-.011,x+.011,1.03,1.055,z-.005,z+.005,"cap")

    def foot(self, x) -> list[list[float]]:
        half=FOOT_WIDTH/2
        end=FOOT_LENGTH/2-half
        outline=[]
        for t in np.linspace(0,math.pi,17):
            outline.append([x+half*math.cos(t),FOOT_HEIGHT,end+half*math.sin(t)])
        for t in np.linspace(math.pi,2*math.pi,17):
            outline.append([x+half*math.cos(t),FOOT_HEIGHT,-end+half*math.sin(t)])
        # The thin near side is visible; top plate is satin aluminum, not a tube.
        for a,b in zip(outline,outline[1:]+outline[:1]):
            normal=np.cross(np.array(b)-a,[0,-FOOT_HEIGHT,0])
            if normal@(CAMERA_CENTER-np.mean([a,b],axis=0))>0:
                self.polygon([a,b,[b[0],0,b[2]],[a[0],0,a[2]]],(98,104,106))
        self.polygon(outline,(193,197,197))
        self.line([[x,FOOT_HEIGHT+.0005,-end],[x,FOOT_HEIGHT+.0005,end]],(223,225,221),.48)
        for z in [-FOOT_LENGTH/2+.012,FOOT_LENGTH/2-.012]:
            self.box(x-half*.8,x+half*.8,0,.003,z-.008,z+.008,"rubber")
        return [[x,0,-FOOT_LENGTH/2],[x,0,FOOT_LENGTH/2]]


def render_product(w: float, h: float):
    high_size=(CANVAS[0]*SS,CANVAS[1]*SS)
    image=Image.new("RGBA",high_size,(0,0,0,0))
    hardware=Hardware(image)
    feet=[]
    for x in [-w*.30,w*.30]:
        feet.extend(hardware.foot(x))
    hardware.vertical_mast(0,.055,PRINT_BOTTOM+h+.002,.038)

    # A plain frameless print rising out of the cassette. No eyelets or Joker rails.
    paper_quad=project([[-w/2,PRINT_BOTTOM+h,PRINT_Z],[w/2,PRINT_BOTTOM+h,PRINT_Z],
                        [w/2,PRINT_BOTTOM,PRINT_Z],[-w/2,PRINT_BOTTOM,PRINT_Z]])
    texture=banner_texture(w,h)
    th,tw=texture.shape[:2]
    source=np.float32([[0,0],[tw-1,0],[tw-1,th-1],[0,th-1]])
    transform=cv2.getPerspectiveTransform(source,np.float32(paper_quad*SS))
    color=cv2.warpPerspective(texture,transform,high_size,flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_REPLICATE)
    paper_alpha=cv2.warpPerspective(np.full((th,tw),255,np.uint8),transform,high_size,flags=cv2.INTER_LINEAR)
    image.alpha_composite(Image.fromarray(np.dstack([color,paper_alpha])))
    paper=cv2.resize(paper_alpha,CANVAS,interpolation=cv2.INTER_AREA).astype(float)/255
    hardware=Hardware(image)
    top=PRINT_BOTTOM+h
    hardware.box(-w/2-.005,w/2+.005,top-.009,top+.006,PRINT_Z-.009,.006)
    for x in [-w/2-.006,w/2+.006]:
        hardware.box(x-.003,x+.003,top-.010,top+.006,PRINT_Z-.010,.007,"cap")
    # Slight bevel highlight on the upper edge, not a large enclosing border.
    hardware.line([[-w/2,top+.004,PRINT_Z-.009],[w/2,top+.004,PRINT_Z-.009]],(232,234,227),.48)

    outside=(w+CASSETTE_EXTRA_WIDTH)/2
    cap=.016
    # Do not expose buried inner endcaps as floating dark disks over the housing.
    hardware.cylinder_x(-outside,-outside+cap,CASSETTE_CENTER_Y,0,CASSETTE_RADIUS_Y+.001,CASSETTE_RADIUS_Z+.001,"cap",caps=(True,False))
    hardware.cylinder_x(-outside+cap,outside-cap,CASSETTE_CENTER_Y,0,CASSETTE_RADIUS_Y,CASSETTE_RADIUS_Z,caps=(False,False))
    hardware.cylinder_x(outside-cap,outside,CASSETTE_CENTER_Y,0,CASSETTE_RADIUS_Y+.001,CASSETTE_RADIUS_Z+.001,"cap",caps=(False,True))
    hardware.line([[-w/2,.084,PRINT_Z-.006],[w/2,.084,PRINT_Z-.006]],(86,93,95),.55)
    hardware.line([[-w/2,.080,PRINT_Z-.013],[w/2,.080,PRINT_Z-.013]],(225,228,224),.45)

    rgba=np.array(image)
    alpha_high=rgba[:,:,3].astype(np.float32)/255
    pm_high=rgba[:,:,:3].astype(np.float32)*alpha_high[:,:,None]
    pm=cv2.resize(pm_high,CANVAS,interpolation=cv2.INTER_AREA)
    alpha=cv2.resize(alpha_high,CANVAS,interpolation=cv2.INTER_AREA)
    cassette_points=project([[-outside,0,-CASSETTE_RADIUS_Z],[outside,0,-CASSETTE_RADIUS_Z],
                             [outside,.09,CASSETTE_RADIUS_Z],[-outside,.09,CASSETTE_RADIUS_Z]])
    geometry={"banner_quad_px":np.round(paper_quad,6).tolist(),
              "cassette_extent_px":np.round(cassette_points,6).tolist(),
              "feet_endpoints_px":np.round(project(feet),6).tolist(),
              "print_bottom_above_floor_m_visual_assumption":PRINT_BOTTOM,
              "top_of_assembly_m_visual_assumption":round(top+.006,6),
              "print_layout":grid_layout(w,h)}
    return pm,alpha,paper,geometry


def floor_shadow(w: float,h: float) -> np.ndarray:
    high_size=(CANVAS[0]*SS,CANVAS[1]*SS)
    wide=(w+CASSETTE_EXTRA_WIDTH)/2
    ground=[[-wide,0,-.05],[wide,0,-.05],[wide,0,.05],[-wide,0,.05]]
    cast=[[x+.50*h,0,z+.67*h] for x,_,z in ground]
    mask=np.zeros((high_size[1],high_size[0]),np.uint8)
    polygon=cv2.convexHull(np.rint(project(ground+cast)*SS).astype(np.int32))
    cv2.fillConvexPoly(mask,polygon,255,cv2.LINE_AA)
    broad=cv2.GaussianBlur(mask,(0,0),6*SS).astype(float)/255*.095
    core=cv2.GaussianBlur(mask,(0,0),2.2*SS).astype(float)/255*.075
    contact=np.zeros_like(mask)
    for x in [-w*.30,w*.30]:
        ends=np.rint(project([[x,0,-FOOT_LENGTH/2],[x,0,FOOT_LENGTH/2]])*SS).astype(np.int32)
        cv2.line(contact,tuple(ends[0]),tuple(ends[1]),255,round(2.5*SS),cv2.LINE_AA)
    ends=np.rint(project([[-wide,0,0],[wide,0,0]])*SS).astype(np.int32)
    cv2.line(contact,tuple(ends[0]),tuple(ends[1]),255,round(2.5*SS),cv2.LINE_AA)
    local=cv2.GaussianBlur(contact,(0,0),1.2*SS).astype(float)/255*.28
    shadow=1-(1-broad)*(1-core)*(1-local)
    return np.rint(cv2.resize(shadow,CANVAS,interpolation=cv2.INTER_AREA)*255).astype(np.uint8)


def font(size:int,bold:bool=False):
    name="DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{name}",size)


def overview(items:list[dict]) -> None:
    tw,th,caption,gap,header=632,424,56,24,144
    board=Image.new("RGB",(tw*2+gap*3,header+(th+caption)*2+gap*3),"#f3f4f6")
    draw=ImageDraw.Draw(board)
    draw.text((gap,20),"SM PRODUCTION / ROLLUP",font=font(17,True),fill="#99752b")
    draw.text((gap,50),"Четыре ширины — сетка логотипов SM",font=font(29,True),fill="#17283d")
    draw.text((gap,99),"Один фон и масштаб · девушка 160 см, мужчина 185 см · размер полотна",font=font(17),fill="#576579")
    for i,item in enumerate(items):
        row,col=divmod(i,2)
        x=gap+col*(tw+gap)
        y=header+gap+row*(th+caption+gap)
        tile=Image.open(ROOT/item["files"]["png"]).convert("RGB").resize((tw,th),Image.Resampling.LANCZOS)
        board.paste(tile,(x,y))
        draw.rectangle((x,y+th,x+tw-1,y+th+caption-1),fill="white")
        draw.text((x+18,y+th+14),item["label"],font=font(24,True),fill="#17283d")
    save_image(board,ROOT/"sm-production-rollup-size-comparison.jpg")


def verify() -> None:
    manifest=json.loads((ROOT/"manifest.json").read_text())
    assert manifest["canvas_px"]==list(CANVAS)
    assert manifest["camera_matrix"]==CALIBRATION["camera_matrix"]
    assert manifest["people"]==PEOPLE_METADATA
    assert [(i["width_cm"],i["height_cm"]) for i in manifest["items"]]==SIZES_CM
    assert sha(BACKGROUND)==manifest["background_sha256"]
    assert sha(PEOPLE)==manifest["people_layer_sha256"]
    assert sha(PRINT_LOGO)==manifest["banner_design"]["logo_sha256"]
    bg=read_rgb(BACKGROUND)
    common=np.array(Image.open(ASSETS/"common-background-check-mask.png").convert("L"))>0
    people=np.array(Image.open(PEOPLE).convert("RGBA"))
    opaque=people[:,:,3]==255
    widths=[]
    for item in manifest["items"]:
        for filename in item["files"].values():
            with Image.open(ROOT/filename) as image:
                assert image.size==CANVAS
                image.verify()
        image=read_rgb(ROOT/item["files"]["png"])
        assert np.array_equal(image[common],bg[common]),"Room changed"
        assert np.array_equal(image[opaque],people[:,:,:3][opaque]),"People changed"
        w,h=item["width_cm"]/100,item["height_cm"]/100
        expected=project([[-w/2,PRINT_BOTTOM+h,PRINT_Z],[w/2,PRINT_BOTTOM+h,PRINT_Z],
                          [w/2,PRINT_BOTTOM,PRINT_Z],[-w/2,PRINT_BOTTOM,PRINT_Z]])
        assert np.allclose(expected,item["banner_quad_px"],atol=.001)
        assert item["print_layout"]==grid_layout(w,h)
        for field in ["banner_quad_px","cassette_extent_px","feet_endpoints_px"]:
            q=np.array(item[field])
            assert np.all((q[:,0]>0)&(q[:,0]<CANVAS[0]))
            assert np.all((q[:,1]>0)&(q[:,1]<CANVAS[1]))
        widths.append(float(np.linalg.norm(expected[1]-expected[0])))
    assert np.all(np.diff(widths)>0),"Per-item zoom or scale inconsistency"
    assert int(common.sum())==manifest["common_background_pixels"]
    print(f"Verified four sizes / 12 exports: {int(common.sum()):,} locked background pixels and {int(opaque.sum()):,} identical opaque person pixels per PNG.")


def package(items:list[dict]) -> None:
    files=[ROOT/f for item in items for f in item["files"].values()]
    files += [ROOT/"sm-production-rollup-size-comparison.jpg",ROOT/"manifest.json",ROOT/"DOWNLOAD-NOTES.txt"]
    for filename,members in [("sm-production-rollup-catalog.zip",files),
                              ("sm-production-rollup-jpg.zip",[ROOT/i["files"]["jpg"] for i in items])]:
        with zipfile.ZipFile(ROOT/filename,"w",zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for path in members:
                z.write(path,path.name)
        with zipfile.ZipFile(ROOT/filename) as z:
            assert len(z.namelist())==len(members)
            assert z.testzip() is None
            assert all(z.read(path.name)==path.read_bytes() for path in members)
        print(f"ZIP CRC passed: {filename}, {len(members)} entries, {(ROOT/filename).stat().st_size:,} bytes.")


def render() -> None:
    ASSETS.mkdir(parents=True,exist_ok=True)
    bg=read_rgb(BACKGROUND)
    people=np.array(Image.open(PEOPLE).convert("RGBA"))
    pa=people[:,:,3].astype(float)/255
    ppm=people[:,:,:3].astype(float)*pa[:,:,None]
    pf=np.array(Image.open(HUMANS/"assets/people-floor-shadow.png").convert("L")).astype(float)/255
    pw=np.array(Image.open(HUMANS/"assets/people-wall-shadow.png").convert("L")).astype(float)/255
    union=pa>0
    items=[]
    for wc,hc in SIZES_CM:
        w,h=wc/100,hc/100
        pm,alpha,paper,geometry=render_product(w,h)
        ps=floor_shadow(w,PRINT_BOTTOM+h).astype(float)/255
        shade=1-(1-ps)*(1-pf*(1-alpha))
        shaded_bg=bg.astype(float)*(1-shade[:,:,None])
        subject=pm*(1-(pw*paper)[:,:,None])+shaded_bg*(1-alpha[:,:,None])
        final=np.rint(subject*(1-pa[:,:,None])+ppm).clip(0,255).astype(np.uint8)
        local=(alpha>0)|(ps>0)|((pf*(1-alpha))>.001)|(pa>0)
        assert np.array_equal(final[~local],bg[~local])
        union |= local
        files={}
        for ext in ["png","jpg","webp"]:
            name=f"{stem(wc,hc)}.{ext}"
            save_image(Image.fromarray(final),ROOT/name)
            files[ext]=name
        items.append({"id":f"{wc}x{hc}","label":label(wc,hc),"width_cm":wc,"height_cm":hc,
                      "width_m":w,"height_m":h,"canvas_px":list(CANVAS),"files":files,**geometry})
        print(f"Rendered RollUp {label(wc,hc)}; grid {geometry['print_layout']['columns']} × {geometry['print_layout']['rows']}.")
    Image.fromarray((~union).astype(np.uint8)*255).save(ASSETS/"common-background-check-mask.png",compress_level=9)
    manifest={
        "title":"SM Production — four RollUp sizes, light vinyl with repeated SM logos",
        "dimension_order":"visible banner width x height, centimeters; not cassette or print bleed",
        "size_source":"Four RollUp formats proposed in site_content/05_nashi-tseny-st340c/README.md, visualized at the user's request",
        "canvas_px":list(CANVAS),"camera_matrix":P.tolist(),
        "camera_policy":"Same photographic room, projective camera, ground origin and people as approved Joker and wooden-frame series. No independent zoom or crop.",
        "background":"../presswalls-sizes/assets/background-locked.png","background_sha256":sha(BACKGROUND),
        "people_layer":"../presswalls-with-people/assets/people-layer-160-185.png","people_layer_sha256":sha(PEOPLE),
        "people_heights_cm":[160,185],"people":PEOPLE_METADATA,
        "construction":{
            "type":"Generic retractable RollUp with aluminum cassette, two flat swivel feet, rear support mast and top clamp; no perimeter frame or eyelets",
            "cassette_height_m_visual_assumption":2*CASSETTE_RADIUS_Y,
            "cassette_depth_m_visual_assumption":2*CASSETTE_RADIUS_Z,
            "cassette_extra_width_m_visual_assumption":CASSETTE_EXTRA_WIDTH,
            "foot_length_m_visual_assumption":FOOT_LENGTH,
            "note":"Illustrative generic hardware, not an approved supplier model, stock claim or manufacturing drawing. Confirm cassette, full print length, bleed and usable dimensions before production."
        },
        "banner_design":{
            "style":"Light vinyl, regular navy/gold SM cube + wordmark grid, matching Joker PressWall branding",
            "logo":"../joker-sizes/assets/sm-logo-presswall-navy-gold.png","logo_sha256":sha(PRINT_LOGO),
            "logo_policy":"Exact previously approved transparent mark; uniform scaling only. Same physical size/pitch for all RollUp widths.",
            "logo_width_m":LOGO_WIDTH,"pitch_m":[LOGO_PITCH_X,LOGO_PITCH_Y],
            "paper_rgb":[244,243,238],"note":"Repeated-mark scale adapted to the narrower RollUp media; source logo unchanged."
        },
        "common_background_pixels":int((~union).sum()),"items":items
    }
    (ROOT/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")
    overview(items)
    verify()
    package(items)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check",action="store_true",help="Check existing exports without rendering")
    args=parser.parse_args()
    verify() if args.check else render()
