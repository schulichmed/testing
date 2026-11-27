# Find the highlighter-filled heading pills on one map image; write blobs_<map>.json and numbered tile overlays.
# usage: python -I detect.py <map.png> <out dir> <map key> <cols> <rows>
import sys, json, pathlib
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
Image.MAX_IMAGE_PIXELS = None

src, out, key = sys.argv[1], pathlib.Path(sys.argv[2]), sys.argv[3]; out.mkdir(exist_ok=True)
cols, rows = int(sys.argv[4]), int(sys.argv[5])
im = Image.open(src).convert("RGB")
W, H = im.size
small = np.array(im)
hsv = cv2.cvtColor(small, cv2.COLOR_RGB2HSV)
mask = ((hsv[..., 1] > 14) & (hsv[..., 2] > 150)).astype(np.uint8) * 255
mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (9, 7)))
mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7)))
n, lab, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
blobs = []
for i in range(1, n):
    x, y, w, h, a = stats[i]
    if w < 40 or h < 14 or h > 160 or w > 900: continue
    if a / (w * h) < 0.45: continue
    if w < 1.2 * h: continue
    col = small[y:y + h, x:x + w][lab[y:y + h, x:x + w] == i].mean(0)
    blobs.append({"x": int(x), "y": int(y), "w": int(w), "h": int(h), "rgb": [int(c) for c in col]})
blobs.sort(key=lambda b: (b["y"] // 150, b["x"]))
for i, b in enumerate(blobs):
    b["id"] = i
    b["tile"] = [min(rows - 1, (b["y"] + b["h"] // 2) * rows // H), min(cols - 1, (b["x"] + b["w"] // 2) * cols // W)]
json.dump({"W": W, "H": H, "cols": cols, "rows": rows, "blobs": blobs}, open(out / f"blobs_{key}.json", "w"), indent=0)
print(key, len(blobs), "blobs")
try: font = ImageFont.truetype("arialbd.ttf", 22)
except Exception: font = ImageFont.load_default()
ov = 70
for r in range(rows):
    for c in range(cols):
        x0, y0 = max(0, c * W // cols - ov), max(0, r * H // rows - ov)
        x1, y1 = min(W, (c + 1) * W // cols + ov), min(H, (r + 1) * H // rows + ov)
        t = im.crop((x0, y0, x1, y1)).copy(); dr = ImageDraw.Draw(t)
        t.save(out / f"{key}_h_r{r}_c{c}.png")
        for b in blobs:
            if b["tile"] != [r, c]: continue
            bx, by = b["x"] - x0, b["y"] - y0
            dr.rectangle([bx, by, bx + b["w"], by + b["h"]], outline=(220, 0, 0), width=3)
            lbl = str(b["id"]); tw = dr.textlength(lbl, font=font)
            dr.rectangle([bx - 2, by - 25, bx + tw + 4, by - 1], fill=(220, 0, 0))
            dr.text((bx + 1, by - 25), lbl, fill=(255, 255, 255), font=font)
        t.save(out / f"{key}_o_r{r}_c{c}.png")
