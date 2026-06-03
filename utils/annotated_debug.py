"""Debug annotated image: pill contours + raw SAM masks + count overlay."""

from pathlib import Path

import cv2
import numpy as np

from utils.annotated import _compute_centroids


def save_debug(
    image: np.ndarray,
    pill_masks: list,
    raw_masks: list,
    image_path: str,
    output_dir: str,
    expected: int | None = None,
) -> str:
    """
    Draw pill contours (filtered) + all raw SAM masks + count text at top-left.

    Args:
        image: original BGR image
        pill_masks: filtered pill mask dicts (each has "segmentation")
        raw_masks: all raw SAM mask dicts before filtering
        image_path: original image path (used for naming)
        output_dir: directory to write the debug image
        expected: ground truth count (from eval), shown if not None

    Returns:
        path to the saved debug image
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    basename = Path(image_path).stem
    output_path = str(Path(output_dir) / f"{basename}_debug.jpg")

    annotated = image.copy()

    # Build a single binary mask of all filtered pills
    filtered_union = np.zeros(image.shape[:2], dtype=bool)
    for m in pill_masks:
        filtered_union |= m["segmentation"].astype(bool)

    # Draw raw masks (semi-transparent green) — skip those overlapping >50% with filtered
    overlay = annotated.copy()
    for m in raw_masks:
        seg = m["segmentation"].astype(bool)
        seg_area = seg.sum()
        if seg_area == 0:
            continue
        overlap = (seg & filtered_union).sum()
        if overlap / seg_area > 0.5:
            continue
        overlay[seg] = (0, 180, 0)
    cv2.addWeighted(overlay, 0.3, annotated, 0.7, 0, annotated)

    # Draw filtered pill contours + labels (red, thin)
    centroids = _compute_centroids(pill_masks)
    for i, m in enumerate(pill_masks):
        mask = m["segmentation"].astype(np.uint8)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(annotated, contours, -1, (0, 0, 255), 1)
        cx, cy = centroids[i]
        if cx >= 0:
            cv2.putText(annotated, str(i + 1), (cx - 6, cy + 3),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 0, 255), 1)

    # Top-left count overlay (white text, thin, gray semi-transparent bg)
    count = len(pill_masks)
    raw = len(raw_masks)

    lines = [f"count: {count}", f"raw: {raw}"]
    if expected is not None:
        diff = count - expected
        lines.append(f"eval: expected={expected} diff={diff:+d}")

    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.4
    thickness = 1
    line_height = 18
    padding = 5
    max_w = max(cv2.getTextSize(l, font, font_scale, thickness)[0][0] for l in lines)
    box_h = line_height * len(lines) + padding * 2
    box_w = max_w + padding * 2

    # Semi-transparent gray overlay
    roi = annotated[0:box_h, 0:box_w]
    gray = np.full_like(roi, 80, dtype=np.uint8)
    cv2.addWeighted(gray, 0.45, roi, 0.55, 0, roi)
    annotated[0:box_h, 0:box_w] = roi

    for i, line in enumerate(lines):
        y = padding + (i + 1) * line_height
        color = (255, 255, 255)
        if expected is not None and i == 2:
            diff_val = count - expected
            color = (0, 255, 0) if diff_val == 0 else (0, 0, 255)
        cv2.putText(annotated, line, (padding, y), font, font_scale, color, thickness)

    cv2.imwrite(output_path, annotated)
    return output_path
