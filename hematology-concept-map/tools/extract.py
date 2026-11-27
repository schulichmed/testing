# Pull each FoM hematology concept map's page image out of its PDF, unchanged (the drawing itself, never redrawn).
# usage: python -I extract.py <out dir> <w9.pdf> <w10.pdf> <w11.pdf>   (writes w9.png, w10.png, w11.png)
import fitz, io, sys, pathlib
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
out = pathlib.Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
for key, pdf in zip(("w9", "w10", "w11"), sys.argv[2:5]):
    d = fitz.open(pdf)
    im = Image.open(io.BytesIO(d.extract_image(d[0].get_images()[0][0])["image"])).convert("RGB")
    im.save(out / f"{key}.png"); print(key, im.size)
