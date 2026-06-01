import numpy as np
from PIL import Image
import os, glob

IMG_DIR = "test-img/pilleye"
files = sorted(glob.glob(os.path.join(IMG_DIR, "raw_test*.jpg")))

# Check horizontal bounds of the content region (rows 212-1040)
img = Image.open(files[0]).convert("RGB")
arr = np.array(img)

content = arr[212:1040, :, :]  # The main content region

# Check each row's horizontal extent of non-white pixels
print("HORIZONTAL SCAN of content region (rows 212-1040):")
print("Checking if content extends full width or has margins...\n")

for row_offset in [0, 100, 200, 300, 400, 500, 600, 700, 800]:
    row = content[row_offset, :, :].mean(axis=1)  # brightness per column
    non_white = np.where(row < 250)[0]
    if len(non_white) > 0:
        print(f"  Row 212+{row_offset:3d} (abs {212+row_offset}): non-white cols {non_white[0]} to {non_white[-1]} (width={non_white[-1]-non_white[0]+1})")
    else:
        print(f"  Row 212+{row_offset:3d} (abs {212+row_offset}): all white")

# More detailed: find the tightest bounding box of the entire content
print("\n\nBOUNDING BOX of content (rows 212-1040):")
# For each row, find leftmost and rightmost non-white pixel
lefts = []
rights = []
for r in range(212, 1040):
    row = arr[r, :, :].mean(axis=1)
    non_white = np.where(row < 250)[0]
    if len(non_white) > 0:
        lefts.append(non_white[0])
        rights.append(non_white[-1])

if lefts:
    print(f"  Left bound:  min={min(lefts)}, max={max(lefts)}, most common={max(set(lefts), key=lefts.count)}")
    print(f"  Right bound: min={min(rights)}, max={max(rights)}, most common={max(set(rights), key=rights.count)}")
    print(f"  Content width range: {min(rights)-max(lefts)+1} to {max(rights)-min(lefts)+1}")

# Check brightness threshold - what's "white" in these images?
print("\n\nBRIGHTNESS DISTRIBUTION in content region:")
all_brightness = content.mean(axis=2).flatten()
for thresh in [240, 245, 248, 250, 252, 254, 255]:
    pct = (all_brightness >= thresh).sum() / len(all_brightness) * 100
    print(f"  >= {thresh}: {pct:.1f}%")

# Try different thresholds for content boundary
print("\n\nCONTENT BOUNDARY at different thresholds:")
for thresh in [200, 210, 220, 230, 240]:
    top_white = np.all(content.mean(axis=2) >= thresh, axis=1)
    # Find first non-all-white row from top
    content_start = 0
    for i in range(len(top_white)):
        if not top_white[i]:
            content_start = i
            break
    # Find last non-all-white row from bottom
    content_end = len(top_white)
    for i in range(len(top_white)-1, -1, -1):
        if not top_white[i]:
            content_end = i
            break

    # Horizontal bounds for that content
    lefts2 = []
    rights2 = []
    for r in range(content_start, content_end):
        row = content[r, :, :].mean(axis=1)
        nw = np.where(row < thresh)[0]
        if len(nw) > 0:
            lefts2.append(nw[0])
            rights2.append(nw[-1])

    left_bound = max(lefts2) if lefts2 else 0
    right_bound = min(rights2) if rights2 else 828

    print(f"  Threshold {thresh}: rows {212+content_start} to {212+content_end} (height={content_end-content_start}), cols {left_bound} to {right_bound} (width={right_bound-left_bound})")
