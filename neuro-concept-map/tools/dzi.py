# Write the map image as a Deep Zoom (DZI) pyramid for OpenSeadragon, with the legend's person name blanked.
import fitz, io, sys, math, pathlib
from PIL import Image, ImageDraw
Image.MAX_IMAGE_PIXELS = None
pdf, out = sys.argv[1], pathlib.Path(sys.argv[2])
d = fitz.open(pdf)
im = Image.open(io.BytesIO(d.extract_image(d[0].get_images()[0][0])["image"])).convert("RGB")
# blank the name in the legend line "<name> Summative Exam Hints" (top-left), keep the star and the words after it
x0, y0, x1, y1 = [int(v) for v in sys.argv[3].split(",")]
ImageDraw.Draw(im).rectangle([x0, y0, x1, y1], fill=(255, 255, 255))
if len(sys.argv) > 4:
    im.crop((x0 - 60, y0 - 40, x1 + 260, y1 + 40)).save(sys.argv[4]);
W, H = im.size
TS, OV, Q = 510, 1, 82
name = "map"
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
    im_small = li
(out / f"{name}.dzi").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<Image xmlns="http://schemas.microsoft.com/deepzoom/2008" Format="jpg" Overlap="{OV}" TileSize="{TS}"><Size Width="{W}" Height="{H}"/></Image>\n', encoding="utf-8")
im.resize((1600, int(1600 * H / W)), Image.LANCZOS).save(out / "preview.jpg", quality=85)
print(W, H, maxlvl, n, "tiles")
