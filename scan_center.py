import numpy as np
from PIL import Image
import os
import glob

IMG_DIR = "test-img/pilleye"
files = sorted(glob.glob(os.path.join(IMG_DIR, "raw_test*.jpg")))

def scan_vertical_center(path):
    img = Image.open(path).convert("RGB")
    arr = np.array(img)
    h, w, _ = arr.shape
    cx = w // 2

    # Get the center column (average of a few columns for stability)
    col_range = slice(cx - 2, cx + 3)
    center_col = arr[:, col_range, :].mean(axis=1)  # shape (H, 3)

    # Convert to brightness (0-255)
    brightness = center_col.mean(axis=1)

    # Print header
    print(f"\n{'='*60}")
    print(f"FILE: {path}")
    print(f"Size: {w}x{h}, Center column: x={cx}")
    print(f"{'='*60}")

    # Sample every 10px and show brightness as bar
    print(f"\nRow | Brightness | Visual")
    print(f"-"*50)
    for row in range(0, h, max(1, h // 60)):
        b = int(brightness[row])
        bar = "#" * (b // 5)
        # Mark transition zones
        marker = ""
        if row > 0:
            diff = abs(brightness[row] - brightness[max(0, row-10)])
            if diff > 15:
                marker = " <-- TRANSITION"
        print(f"{row:4d} | {b:3d}        | {bar}{marker}")

    # Find the white region (top) and the content region (bottom)
    # Threshold: white = brightness > 240
    white_mask = brightness > 240

    # Find transitions
    transitions = []
    prev_white = white_mask[0]
    for i in range(1, h):
        curr_white = white_mask[i]
        if curr_white != prev_white:
            transitions.append((i, "white->content" if prev_white else "content->white"))
            prev_white = curr_white

    print(f"\nTransitions found:")
    for t_row, t_type in transitions:
        print(f"  Row {t_row}: {t_type} (brightness={int(brightness[t_row])})")

    # Find the main content region (non-white continuous block)
    non_white_regions = []
    in_region = False
    start = 0
    for i in range(h):
        if not white_mask[i] and not in_region:
            start = i
            in_region = True
        elif white_mask[i] and in_region:
            non_white_regions.append((start, i, i - start))
            in_region = False
    if in_region:
        non_white_regions.append((start, h, h - start))

    print(f"\nNon-white regions (>10px):")
    for s, e, length in non_white_regions:
        if length > 10:
            avg_b = int(brightness[s:e].mean())
            print(f"  Row {s} to {e} (height={length}, avg_brightness={avg_b})")

    return h, w, brightness, non_white_regions


# Scan all images and compare patterns
print("=" * 60)
print("VERTICAL CENTER SCAN - ALL RAW IMAGES")
print("=" * 60)

results = []
for f in files:
    h, w, brightness, regions = scan_vertical_center(f)
    results.append((f, h, w, brightness, regions))

# Summary comparison
print("\n\n" + "=" * 60)
print("PATTERN COMPARISON SUMMARY")
print("=" * 60)
print(f"\n{'File':<30} {'Size':>10} {'Top White':>10} {'Content Start':>15} {'Content Height':>15}")
print("-" * 85)

for f, h, w, brightness, regions in results:
    fname = os.path.basename(f)
    white_mask = brightness > 240

    # Find first non-white row (content start)
    content_start = 0
    for i in range(h):
        if not white_mask[i]:
            content_start = i
            break

    # Find the largest non-white region
    largest = max(regions, key=lambda x: x[2]) if regions else (0, 0, 0)

    print(f"{fname:<30} {w}x{h:>5} {content_start:>10} {largest[0]:>15} {largest[2]:>15}")

# Check if pattern is consistent
print("\n\nCONSISTENCY CHECK:")
content_starts = []
for f, h, w, brightness, regions in results:
    white_mask = brightness > 240
    for i in range(h):
        if not white_mask[i]:
            content_starts.append(i)
            break

if len(set(content_starts)) <= 2:
    print(f"  PASS: All images have similar white header region (content starts around row {max(set(content_starts), key=content_starts.count)})")
else:
    print(f"  NOTE: Content start varies: {sorted(set(content_starts))}")

# Also check bottom white region
print("\nBOTTOM REGION CHECK:")
for f, h, w, brightness, regions in results:
    fname = os.path.basename(f)
    white_mask = brightness > 240
    # Find last non-white row
    content_end = h
    for i in range(h - 1, -1, -1):
        if not white_mask[i]:
            content_end = i
            break
    bottom_white = h - content_end
    print(f"  {fname}: content ends at row {content_end}, bottom white = {bottom_white}px")
