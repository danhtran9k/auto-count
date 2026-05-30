"""
Pill counter — iteration 2.

Approach: Otsu mask + distance transform + LOCAL-MAX peak seeds with auto-estimated pill radius.

Vs iter 1: replaced global `0.5 * dist.max()` (which collapsed when a single deep cluster
peak dominated) with local-maxima detection in a window sized to the estimated pill radius.

Pipeline:
1. Grayscale + Gaussian blur.
2. Otsu threshold (inverted if bg is bright).
3. Morph open + close to clean speckle/holes.
4. Distance transform (L2).
5. Estimate pill radius `r`: median of per-connected-component `dist.max()` (one peak per blob).
6. Find local maxima: a pixel is a seed iff `dist == cv2.dilate(dist, (k,k))` with k ~ pill diameter
   AND `dist > 0.3 * r` (reject low/edge noise).
7. Count seed connected components.
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


def _estimate_radius(dist: np.ndarray, mask: np.ndarray) -> float:
    """Median of per-CC max distance — robust pill-radius estimate."""
    n, labels, _, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    peaks = []
    for i in range(1, n):
        region = dist[labels == i]
        if region.size > 0:
            peaks.append(float(region.max()))
    if not peaks:
        return 0.0
    return float(np.median(peaks))


def count_pills(image_path: str) -> int:
    img = cv2.imread(image_path)
    if img is None:
        return -1

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    thresh_type = (cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU) if _bg_is_bright(gray) else (cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    _, binary = cv2.threshold(blurred, 0, 255, thresh_type)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    cleaned = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=2)
    cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, kernel, iterations=2)

    dist = cv2.distanceTransform(cleaned, cv2.DIST_L2, 5)
    if dist.max() <= 0:
        return 0

    r = _estimate_radius(dist, cleaned)
    if r <= 0:
        return 0

    # Local-max window ~ pill diameter (≈ 2r). Odd size, min 3.
    k = max(3, int(round(2 * r)) | 1)
    dilated = cv2.dilate(dist, np.ones((k, k), np.uint8))
    is_peak = (dist == dilated) & (dist > 0.3 * r)
    seeds = is_peak.astype(np.uint8) * 255

    num_labels, _, _, _ = cv2.connectedComponentsWithStats(seeds, connectivity=8)
    return int(num_labels - 1)  # exclude background label
