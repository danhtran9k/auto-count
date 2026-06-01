import numpy as np
from PIL import Image
import os, glob

SRC_DIR = "test-img/pilleye"
OUT_DIR = "test-img/crop"
os.makedirs(OUT_DIR, exist_ok=True)

# Content bounds from scan analysis (consistent across all images)
CONTENT_TOP = 212
CONTENT_BOTTOM = 1040

files = sorted(glob.glob(os.path.join(SRC_DIR, "raw_test*.jpg")))

for f in files:
    fname = os.path.basename(f)
    out_name = fname.replace("raw_", "")

    img = Image.open(f)
    cropped = img.crop((0, CONTENT_TOP, img.width, CONTENT_BOTTOM))

    out_path = os.path.join(OUT_DIR, out_name)
    cropped.save(out_path, quality=95)
    print(f"{fname} -> {out_name}  ({cropped.width}x{cropped.height})")

print(f"\nDone! {len(files)} images saved to {OUT_DIR}/")
