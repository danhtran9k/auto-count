import numpy as np
from PIL import Image
import os, glob

IMG_DIR = "test-img/pilleye"
files = sorted(glob.glob(os.path.join(IMG_DIR, "raw_test*.jpg")))

def find_content_bounds(path, white_thresh=245):
    img = Image.open(path).convert("RGB")
    arr = np.array(img)
    h, w, _ = arr.shape

    # Row-wise: check if entire row is "white" (all pixels above threshold)
    row_brightness = arr.mean(axis=(1, 2))  # average brightness per row
    row_is_white = np.all(arr.mean(axis=2) >= white_thresh, axis=1)

    # Find content start (first non-white row from top)
    content_top = 0
    for i in range(h):
        if not row_is_white[i]:
            content_top = i
            break

    # Find content end (first non-white row from bottom)
    content_bottom = h
    for i in range(h - 1, -1, -1):
        if not row_is_white[i]:
            content_bottom = i + 1
            break

    # Within the content region, find horizontal bounds
    content_slice = arr[content_top:content_bottom, :, :]
    col_is_white = np.all(content_slice.mean(axis=2) >= white_thresh, axis=0)

    content_left = 0
    for i in range(w):
        if not col_is_white[i]:
            content_left = i
            break

    content_right = w
    for i in range(w - 1, -1, -1):
        if not col_is_white[i]:
            content_right = i + 1
            break

    return {
        "path": path,
        "size": (w, h),
        "content_top": content_top,
        "content_bottom": content_bottom,
        "content_left": content_left,
        "content_right": content_right,
        "content_height": content_bottom - content_top,
        "content_width": content_right - content_left,
        "header_white": content_top,
        "footer_white": h - content_bottom,
    }


print("=" * 70)
print("CONFIRMING PATTERN: All raw images have same structure")
print("=" * 70)
print()

results = []
for f in files:
    r = find_content_bounds(f)
    results.append(r)
    fname = os.path.basename(f)
    print(f"{fname}:")
    print(f"  Image size:        {r['size'][0]}x{r['size'][1]}")
    print(f"  White header:      rows 0-{r['content_top']-1} ({r['header_white']}px)")
    print(f"  Content region:    rows {r['content_top']}-{r['content_bottom']-1} ({r['content_height']}px)")
    print(f"  Content horiz:     cols {r['content_left']}-{r['content_right']-1} ({r['content_width']}px)")
    print(f"  White footer:      rows {r['content_bottom']}-{r['size'][1]-1} ({r['footer_white']}px)")
    print()

# Check consistency
print("=" * 70)
print("CONSISTENCY CHECK")
print("=" * 70)
tops = [r['content_top'] for r in results]
bottoms = [r['content_bottom'] for r in results]
lefts = [r['content_left'] for r in results]
rights = [r['content_right'] for r in results]
heights = [r['content_height'] for r in results]
widths = [r['content_width'] for r in results]

print(f"  Content top:    {min(tops)}-{max(tops)} (variance={max(tops)-min(tops)}px)")
print(f"  Content bottom: {min(bottoms)}-{max(bottoms)} (variance={max(bottoms)-min(bottoms)}px)")
print(f"  Content left:   {min(lefts)}-{max(lefts)} (variance={max(lefts)-min(lefts)}px)")
print(f"  Content right:  {min(rights)}-{max(rights)} (variance={max(rights)-min(rights)}px)")
print(f"  Content height: {min(heights)}-{max(heights)} (variance={max(heights)-min(heights)}px)")
print(f"  Content width:  {min(widths)}-{max(widths)} (variance={max(widths)-min(widths)}px)")

if max(tops) - min(tops) <= 5 and max(bottoms) - min(bottoms) <= 5:
    print("\n  PASS: Content vertical bounds are consistent across all images!")
else:
    print("\n  NOTE: Some variance detected in vertical bounds.")

if max(heights) - min(heights) <= 10:
    print(f"  PASS: All content regions have similar height (~{max(heights)}px)")

print(f"\n  RECOMMENDED CROP: top={max(tops)}, bottom={min(bottoms)}, left={max(lefts)}, right={min(rights)}")
print(f"  CROP SIZE: {min(rights)-max(lefts)}x{min(bottoms)-max(tops)}")
