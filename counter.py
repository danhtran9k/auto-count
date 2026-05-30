"""
Pill counter — iteration 0 (baseline).

Direct port of pill_counter.py logic, exposing the stable contract:
    count_pills(image_path: str) -> int

Strategy:
1. Estimate background from corners
2. Try multiple threshold offsets + Canny edge detection
3. Pick the result closest to the median of non-zero candidates
"""
import cv2
import numpy as np


def _get_bg(gray):
    h, w = gray.shape
    patch = min(20, h // 10, w // 10)
    corners = np.concatenate([
        gray[:patch, :patch].flatten(),
        gray[:patch, -patch:].flatten(),
        gray[-patch:, :patch].flatten(),
        gray[-patch:, -patch:].flatten(),
    ])
    return np.median(corners)


def _count_with_threshold(gray, bg_val, offset, img_area):
    if bg_val > 128:
        _, thresh = cv2.threshold(gray, int(bg_val - offset), 255, cv2.THRESH_BINARY_INV)
    else:
        _, thresh = cv2.threshold(gray, int(bg_val + offset), 255, cv2.THRESH_BINARY)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)
    opened = cv2.morphologyEx(closed, cv2.MORPH_OPEN, kernel, iterations=1)

    contours, _ = cv2.findContours(opened, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    min_area = img_area * 0.0005
    max_area = img_area * 0.15

    return sum(1 for c in contours if min_area <= cv2.contourArea(c) <= max_area)


def _count_with_canny(gray, img_area):
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 30, 100)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    dilated = cv2.dilate(edges, kernel, iterations=2)
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    min_area = img_area * 0.0005
    max_area = img_area * 0.15

    return sum(1 for c in contours if min_area <= cv2.contourArea(c) <= max_area)


def count_pills(image_path: str) -> int:
    """Return the number of pills in the image. -1 on read error."""
    img = cv2.imread(image_path)
    if img is None:
        return -1

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    img_area = h * w
    bg_val = _get_bg(gray)

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    candidates = []
    for offset in [15, 20, 25, 30, 35, 40, 50, 60]:
        candidates.append(_count_with_threshold(enhanced, bg_val, offset, img_area))
    for offset in [20, 30, 40, 50]:
        candidates.append(_count_with_threshold(gray, bg_val, offset, img_area))
    candidates.append(_count_with_canny(gray, img_area))
    candidates.append(_count_with_canny(enhanced, img_area))

    non_zero = [v for v in candidates if v > 0]
    if not non_zero:
        return 0

    median_val = float(np.median(non_zero))
    best = min(non_zero, key=lambda v: abs(v - median_val))
    return int(best)
