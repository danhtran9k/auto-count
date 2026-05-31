"""
Core image processing — counts pills using SAM (Segment Anything Model).

Uses SamAutomaticMaskGenerator for zero-shot instance segmentation.
Filters masks by area cluster (pills share similar size) and shape.
"""

import os
from datetime import datetime

import cv2
import numpy as np
from segment_anything import sam_model_registry, SamAutomaticMaskGenerator

RUN_TIMESTAMP = datetime.now().strftime("%y-%m-%d-%H-%M")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", RUN_TIMESTAMP)

# Lazy-load model (first call initializes, subsequent calls reuse)
_sam_model = None
_mask_generator = None

CHECKPOINT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sam_vit_b.pth")
MODEL_TYPE = "vit_b"


def _get_mask_generator():
    """Initialize SAM model and mask generator (lazy, cached)."""
    global _sam_model, _mask_generator
    if _mask_generator is None:
        if not os.path.exists(CHECKPOINT):
            raise FileNotFoundError(f"SAM checkpoint not found: {CHECKPOINT}")
        _sam_model = sam_model_registry[MODEL_TYPE](checkpoint=CHECKPOINT)
        _mask_generator = SamAutomaticMaskGenerator(_sam_model)
    return _mask_generator


def process(image_path: str) -> dict:
    """
    Process a single image using SAM and return pill count.

    Args:
        image_path: path to one image file

    Returns:
        dict with:
          - "count": int (-1 on error)
          - "output_file": str (path to annotated output image)
          - "num_masks": int (total masks from SAM before filtering)
    """
    if not os.path.exists(image_path):
        return {"count": -1, "output_file": "", "error": "file not found"}

    image = cv2.imread(image_path)
    if image is None:
        return {"count": -1, "output_file": "", "error": "failed to read image"}

    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    h, w = image.shape[:2]
    image_area = h * w

    # Generate masks
    generator = _get_mask_generator()
    masks = generator.generate(image_rgb)

    # Step 1: Loose area filter (remove tiny noise and huge background)
    min_area = image_area * 0.001   # 0.1%
    max_area = image_area * 0.10    # 10%

    candidates = []
    for m in masks:
        area = m["area"]
        if not (min_area <= area <= max_area):
            continue

        # Shape filter: circularity
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

        # Solidity
        hull = cv2.convexHull(cnt)
        hull_area = cv2.contourArea(hull)
        if hull_area == 0:
            continue
        solidity = area / hull_area
        if solidity < 0.6:
            continue

        candidates.append(m)

    # Step 2: Area cluster filter — pills share similar size
    if len(candidates) >= 3:
        areas = np.array([m["area"] for m in candidates])
        med_area = np.median(areas)
        lo, hi = med_area * 0.6, med_area * 1.4
        candidates = [m for m in candidates if lo <= m["area"] <= hi]

    # Step 3: Color cluster filter — pills share similar color
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
        # Keep masks within median color distance + 1.5x spread
        threshold = med_dist + 2.5 * np.std(color_dists) if np.std(color_dists) > 0 else med_dist + 30
        threshold = max(threshold, 40)  # minimum tolerance
        candidates = [m for m, d in zip(candidates, color_dists) if d <= threshold]

    # Step 4: Shape outlier filter — reject extreme aspect ratio or low fill
    if len(candidates) >= 3:
        shapes = []
        for m in candidates:
            seg = m["segmentation"].astype(np.uint8)
            x, y, bw, bh = cv2.boundingRect(seg)
            aspect = max(bw, bh) / max(min(bw, bh), 1)
            fill = m["area"] / (bw * bh) if bw * bh > 0 else 0
            shapes.append((aspect, fill))
        pill_masks = []
        for m, (aspect, fill) in zip(candidates, shapes):
            if aspect > 3.0:
                continue
            if fill < 0.4:
                continue
            pill_masks.append(m)
    else:
        pill_masks = candidates

    count = len(pill_masks)

    # Save annotated image to output/ directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    basename = os.path.splitext(os.path.basename(image_path))[0]
    output_path = os.path.join(OUTPUT_DIR, f"{basename}_out.jpg")
    annotated = image.copy()
    for i, m in enumerate(pill_masks):
        mask = m["segmentation"].astype(np.uint8)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(annotated, contours, -1, (0, 0, 255), 1)
        # Add number label
        ys, xs = np.where(mask > 0)
        if len(xs) > 0 and len(ys) > 0:
            cx, cy = int(xs.mean()), int(ys.mean())
            cv2.putText(annotated, str(i + 1), (cx - 8, cy + 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
    cv2.imwrite(output_path, annotated)

    return {
        "count": count,
        "output_file": output_path,
        "num_masks": len(masks),
    }
