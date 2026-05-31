"""
Core image processing — counts pills using SAM (Segment Anything Model).

Uses SamAutomaticMaskGenerator for zero-shot instance segmentation.
Filters masks by area to keep only pill-sized objects.
"""

import os
import cv2
import numpy as np
from segment_anything import sam_model_registry, SamAutomaticMaskGenerator

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

    # Filter masks by area — pills are within a size range
    # Min: 0.05% of image (tiny noise)
    # Max: 15% of image (one pill can't be bigger than this)
    min_area = image_area * 0.0005
    max_area = image_area * 0.15

    pill_masks = []
    for m in masks:
        area = m["area"]
        if min_area <= area <= max_area:
            pill_masks.append(m)

    count = len(pill_masks)

    # Save annotated image
    output_path = image_path.replace(".jpg", "_out.jpg").replace(".jpeg", "_out.jpg").replace(".png", "_out.png")
    annotated = image.copy()
    for i, m in enumerate(pill_masks):
        mask = m["segmentation"].astype(np.uint8)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(annotated, contours, -1, (0, 0, 255), 2)
        # Add number label
        ys, xs = np.where(mask > 0)
        if len(xs) > 0 and len(ys) > 0:
            cx, cy = int(xs.mean()), int(ys.mean())
            cv2.putText(annotated, str(i + 1), (cx - 10, cy + 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    cv2.imwrite(output_path, annotated)

    return {
        "count": count,
        "output_file": output_path,
        "num_masks": len(masks),
    }
