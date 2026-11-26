# Find highlighter-filled heading pills on the map image; write blobs.json and numbered tile overlays.
import fitz, io, sys, json, pathlib
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
Image.MAX_IMAGE_PIXELS = None

pdf, out = sys.argv[1], pathlib.Path(sys.argv[2]); out.mkdir(exist_ok=True)
d = fitz.open(pdf)
raw = d.extract_image(d[0].get_images()[0][0])["image"]
im = Image.open(io.BytesIO(raw)).convert("RGB")
W, H = im.size
F = 2
small = np.array(im.resize((W // F, H // F), Image.LANCZOS))
hsv = cv2.cvtColor(small, cv2.COLOR_RGB2HSV)
mask = ((hsv[..., 1] > 11) & (hsv[..., 2] > 165)).astype(np.uint8) * 255
mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (9, 7)))
mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9)))
n, lab, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
blobs = []
for i in range(1, n):
    x, y, w, h, a = stats[i]
    if w < 35 or h < 10 or h > 140 or w > 900: continue
    if a / (w * h) < 0.45: continue
    if w < 1.2 * h: continue
    col = small[y:y + h, x:x + w][lab[y:y + h, x:x + w] == i].mean(0)
    blobs.append({"x": int(x * F), "y": int(y * F), "w": int(w * F), "h": int(h * F), "rgb": [int(c) for c in col]})
blobs.sort(key=lambda b: (b["y"] // 300, b["x"]))
cols, rows = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (8, 6)
for i, b in enumerate(blobs):
    b["id"] = i
    b["tile"] = [min(rows - 1, (b["y"] + b["h"] // 2) * rows // H), min(cols - 1, (b["x"] + b["w"] // 2) * cols // W)]
json.dump({"W": W, "H": H, "blobs": blobs}, open(out / "blobs.json", "w"), indent=0)
print(len(blobs), "blobs")

# overlays per tile (same 8x6 grid, 90px overlap) with numbered red boxes
try: font = ImageFont.truetype("arialbd.ttf", 30)
except Exception: font = ImageFont.load_default()
ov = 90
for r in range(rows):
    for c in range(cols):
        x0, y0 = max(0, c * W // cols - ov), max(0, r * H // rows - ov)
        x1, y1 = min(W, (c + 1) * W // cols + ov), min(H, (r + 1) * H // rows + ov)
        t = im.crop((x0, y0, x1, y1)).copy(); dr = ImageDraw.Draw(t)
        for b in blobs:
            if b["tile"] != [r, c]: continue
            bx, by = b["x"] - x0, b["y"] - y0
            dr.rectangle([bx, by, bx + b["w"], by + b["h"]], outline=(220, 0, 0), width=4)
            lbl = str(b["id"]); tw = dr.textlength(lbl, font=font)
            dr.rectangle([bx - 2, by - 34, bx + tw + 6, by - 2], fill=(220, 0, 0))
            dr.text((bx + 2, by - 34), lbl, fill=(255, 255, 255), font=font)
        t.save(out / f"o_r{r}_c{c}.png")
