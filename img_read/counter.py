"""
Pill counter — iteration 13.

Iter 12 over-merged with close iter=2. Iter 13: lighter close (iter=1)
and middle window cap. Keep area sanity + plateau pick.
"""
import math

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
    short = min(h, w)

    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    if _bg_is_bright(gray):
        ttype = cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU
    else:
        ttype = cv2.THRESH_BINARY | cv2.THRESH_OTSU
    _, binary = cv2.threshold(blurred, 0, 255, ttype)

    k3 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    k5 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.morphologyEx(binary, cv2.MORPH_OPEN, k3, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k5, iterations=1)

    fg_area = float(cv2.countNonZero(mask))
    if fg_area < 100:
        return 0

    dist = cv2.distanceTransform(mask, cv2.DIST_L2, 5)
    if dist.max() < 1:
        return 0

    max_win = max(7, min(int(short / 3), 301))
    if max_win % 2 == 0:
        max_win -= 1

    w_steps = sorted(set([
        max(3, int(round(v))) | 1
        for v in np.geomspace(3, max_win, num=28)
    ]))

    LO_RATIO = 0.40
    HI_RATIO = 1.5

    entries = []
    for win in w_steps:
        kernel = np.ones((win, win), np.uint8)
        dilated = cv2.dilate(dist, kernel)
        peaks = (dist == dilated) & (mask > 0) & (dist > 1.0)
        peaks_u8 = peaks.astype(np.uint8) * 255
        n, _, _, _ = cv2.connectedComponentsWithStats(peaks_u8, connectivity=8)
        c = int(n - 1)
        r = win / 2.0
        ratio = c * math.pi * r * r / fg_area
        ok = (c >= 1) and (LO_RATIO <= ratio <= HI_RATIO)
        entries.append((win, c, ratio, ok))

    best_len = 0
    best_val = 0
    cur_len = 0
    cur_val = -1
    for _, c, _, ok in entries:
        if not ok:
            cur_len = 0
            cur_val = -1
            continue
        if c == cur_val:
            cur_len += 1
        else:
            cur_val = c
            cur_len = 1
        if cur_len > best_len:
            best_len = cur_len
            best_val = c

    if best_len >= 2 and best_val > 0:
        return int(best_val)

    valid = [(c, ratio) for _, c, ratio, ok in entries if ok]
    if valid:
        valid.sort(key=lambda t: abs(math.log(max(t[1], 1e-6))))
        return int(valid[0][0])

    best_diff = float("inf")
    best_c = 0
    for _, c, ratio, _ in entries:
        if c < 1:
            continue
        d = abs(math.log(max(ratio, 1e-6)))
        if d < best_diff:
            best_diff = d
            best_c = c
    return int(best_c)
