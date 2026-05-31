"""Check remaining images (test1, test4, test7, test8, test11, test15) with proposed filters."""
import cv2
import numpy as np
from core import _get_mask_generator
import os

test_dir = "test-img"
expected = {
    "test1": 18, "test4": 23, "test7": 30, "test8": 23, "test11": 7, "test15": 50,
}

for name in sorted(expected.keys()):
    path = os.path.join(test_dir, f"{name}.jpg")
    image = cv2.imread(path)
    if image is None:
        continue
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    h, w = image.shape[:2]
    image_area = h * w

    generator = _get_mask_generator()
    masks = generator.generate(image_rgb)

    min_area = image_area * 0.001
    max_area = image_area * 0.10

    candidates = []
    for m in masks:
        area = m["area"]
        if not (min_area <= area <= max_area):
            continue
        mask = m["segmentation"].astype(np.uint8)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            continue
        cnt = max(contours, key=cv2.contourArea)
        perimeter = cv2.arcLength(cnt, True)
        if perimeter == 0:
            continue
        circularity = 4 * np.pi * area / (perimeter * perimeter)
        if circularity < 0.3:
            continue
        hull = cv2.convexHull(cnt)
        hull_area = cv2.contourArea(hull)
        if hull_area == 0:
            continue
        solidity = area / hull_area
        if solidity < 0.6:
            continue
        candidates.append(m)

    if len(candidates) >= 3:
        areas = np.array([m["area"] for m in candidates])
        med_area = np.median(areas)
        lo, hi = med_area * 0.6, med_area * 1.4
        candidates = [m for m in candidates if lo <= m["area"] <= hi]

    if len(candidates) >= 3:
        mean_colors = []
        for m in candidates:
            seg = m["segmentation"]
            mean_rgb = image_rgb[seg].mean(axis=0)
            mean_colors.append(mean_rgb)
        mean_colors = np.array(mean_colors)
        med_color = np.median(mean_colors, axis=0)
        color_dists = np.sqrt(((mean_colors - med_color) ** 2).sum(axis=1))
        med_dist = np.median(color_dists)
        threshold = med_dist + 2.5 * np.std(color_dists) if np.std(color_dists) > 0 else med_dist + 30
        threshold = max(threshold, 40)
        candidates = [m for m, d in zip(candidates, color_dists) if d <= threshold]

    data = []
    for m in candidates:
        seg = m["segmentation"].astype(np.uint8)
        x, y, bw, bh = cv2.boundingRect(seg)
        aspect = max(bw, bh) / max(min(bw, bh), 1)
        fill = m["area"] / (bw * bh) if bw * bh > 0 else 0
        contours, _ = cv2.findContours(seg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnt = max(contours, key=cv2.contourArea)
        perimeter = cv2.arcLength(cnt, True)
        circ = 4 * np.pi * m["area"] / (perimeter * perimeter) if perimeter > 0 else 0
        data.append({"area": m["area"], "aspect": aspect, "fill": fill, "circ": circ})

    if not data:
        continue

    med_area_c = np.median([d["area"] for d in data])

    survived = []
    rejected = []
    for d in data:
        area_ratio = d["area"] / med_area_c
        reasons = []
        if d["aspect"] > 3.0:
            reasons.append(f"aspect={d['aspect']:.2f}")
        if d["fill"] < 0.45:
            reasons.append(f"fill={d['fill']:.2f}")
        if d["circ"] < 0.55:
            reasons.append(f"circ={d['circ']:.2f}")
        if area_ratio < 0.80:
            reasons.append(f"area_ratio={area_ratio:.2f}")
        if reasons:
            rejected.append((d, reasons))
        else:
            survived.append(d)

    count = len(survived)
    exp = expected[name]
    status = "OK" if count == exp else f"diff={count-exp:+d}"

    # Show area ratios to verify no false rejects
    area_ratios = sorted([d["area"]/med_area_c for d in data])
    print(f"{name}: count={count} expected={exp} {status}  area_ratios=[{area_ratios[0]:.2f}..{area_ratios[-1]:.2f}]")
    if rejected:
        for d, reasons in rejected:
            ar = d["area"]/med_area_c
            print(f"  REJ: area={d['area']:.0f} ar={ar:.2f} aspect={d['aspect']:.2f} fill={d['fill']:.2f} circ={d['circ']:.2f} -> {','.join(reasons)}")
