import fitz, io, sys
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
d = fitz.open(sys.argv[1])
xref = d[0].get_images()[0][0]
im = Image.open(io.BytesIO(d.extract_image(xref)["image"])).convert("RGB")
W, H = im.size
cols, rows, ov = int(sys.argv[3]) if len(sys.argv) > 3 else 8, int(sys.argv[4]) if len(sys.argv) > 4 else 6, 90
out = sys.argv[2]
for r in range(rows):
    for c in range(cols):
        x0, y0 = max(0, c * W // cols - ov), max(0, r * H // rows - ov)
        x1, y1 = min(W, (c + 1) * W // cols + ov), min(H, (r + 1) * H // rows + ov)
        im.crop((x0, y0, x1, y1)).save(f"{out}/h_r{r}_c{c}.png")
print(W, H)
