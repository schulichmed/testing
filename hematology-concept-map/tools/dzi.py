# Write one map image as a Deep Zoom (DZI) pyramid for OpenSeadragon, optionally blanking person names first.
# usage: python -I dzi.py <map.png> <out dir> <name: w9|w10|w11> [x0,y0,x1,y1[;x0,y0,x1,y1...] | -] [check.png]
import sys, math, pathlib
from PIL import Image, ImageDraw
Image.MAX_IMAGE_PIXELS = None
src, out, name = sys.argv[1], pathlib.Path(sys.argv[2]), sys.argv[3]
im = Image.open(src).convert("RGB")
if len(sys.argv) > 4 and sys.argv[4] != "-":
    rects = [[int(v) for v in r.split(",")] for r in sys.argv[4].split(";")]
    for x0, y0, x1, y1 in rects:
        ImageDraw.Draw(im).rectangle([x0, y0, x1, y1], fill=(255, 255, 255))
    if len(sys.argv) > 5:
        x0, y0, x1, y1 = rects[0]
        im.crop((max(0, x0 - 200), max(0, y0 - 120), x1 + 200, y1 + 120)).save(sys.argv[5])
W, H = im.size
TS, OV, Q = 510, 1, 84
files = out / f"{name}_files"
maxlvl = math.ceil(math.log2(max(W, H)))
n = 0
for lvl in range(maxlvl, -1, -1):
    s = 2 ** (maxlvl - lvl)
    w, h = max(1, math.ceil(W / s)), max(1, math.ceil(H / s))
    li = im if s == 1 else im.resize((w, h), Image.LANCZOS)
    dd = files / str(lvl); dd.mkdir(parents=True, exist_ok=True)
    for ty in range(math.ceil(h / TS)):
        for tx in range(math.ceil(w / TS)):
            bx0 = max(0, tx * TS - OV); by0 = max(0, ty * TS - OV)
            bx1 = min(w, (tx + 1) * TS + OV); by1 = min(h, (ty + 1) * TS + OV)
            li.crop((bx0, by0, bx1, by1)).save(dd / f"{tx}_{ty}.jpg", quality=Q, optimize=True, progressive=True); n += 1
(out / f"{name}.dzi").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<Image xmlns="http://schemas.microsoft.com/deepzoom/2008" Format="jpg" Overlap="{OV}" TileSize="{TS}"><Size Width="{W}" Height="{H}"/></Image>\n', encoding="utf-8")
print(name, W, H, maxlvl, n, "tiles")
