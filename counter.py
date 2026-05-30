"""
Pill counter — iteration 1.

Approach: Otsu threshold + distance transform peak seeds.

Rationale (vs iter 0):
- iter 0 picked the count "closest to median of candidates", which systematically
  selected merged-blob (undersegmented) results -> 0/15, all UNDER.
- iter 1 uses a single principled pipeline:
    1. Grayscale + Gaussian blur.
    2. Otsu threshold (auto bg/fg). Invert if background is bright.
    3. Morphological open + close to clean speckle and fill interior gaps.
    4. Distance transform: each FG pixel -> distance to nearest BG.
    5. Threshold the distance map at a fraction of its max -> one seed per pill,
       even when pills touch.
    6. Connected-components on the seeds = pill count.

Public contract:
    count_pills(image_path: str) -> int
"""
import cv2
import numpy as np


def _bg_is_bright(gray: np.ndarray) -> bool:
    h, w = gray.shape
    patch = max(5, min(30, h // 10, w // 10))
    corners = np.concatenate([
        gray[:patch, :patch].flatten(),
        gray[:patch, -patch:].flatten(),
        gray[-patch:, :patch].flatten(),
        gray[-patch:, -patch:].flatten(),
    ])
    return float(np.median(corners)) > float(np.median(gray))


def count_pills(image_path: str) -> int:
    img = cv2.imread(image_path)
    if img is None:
        return -1

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    img_area = h * w

    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    if _bg_is_bright(gray):
        thresh_type = cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU
    else:
        thresh_type = cv2.THRESH_BINARY | cv2.THRESH_OTSU
    _, binary = cv2.threshold(blurred, 0, 255, thresh_type)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    cleaned = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=2)
    cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, kernel, iterations=2)

    dist = cv2.distanceTransform(cleaned, cv2.DIST_L2, 5)
    if dist.max() <= 0:
        return 0

    seed_thresh = 0.5 * float(dist.max())
    _, seeds = cv2.threshold(dist, seed_thresh, 255, cv2.THRESH_BINARY)
    seeds = seeds.astype(np.uint8)

    num_labels, _, stats, _ = cv2.connectedComponentsWithStats(seeds, connectivity=8)

    min_seed_area = max(2, int(img_area * 0.00005))
    count = 0
    for i in range(1, num_labels):
        if stats[i, cv2.CC_STAT_AREA] >= min_seed_area:
            count += 1

    return int(count)
