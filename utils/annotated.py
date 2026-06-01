"""Save annotated images with pill contours and labels."""

from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

RUN_TIMESTAMP = datetime.now().strftime("%y-%m-%d-%H-%M")
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output" / RUN_TIMESTAMP


def save_annotated(image: np.ndarray, pill_masks: list, image_path: str, output_dir: str) -> str:
    """
    Draw pill contours and number labels on the image, save to output_dir.

    Args:
        image: original BGR image
        pill_masks: list of SAM mask dicts (each has "segmentation")
        image_path: original image path (used for naming the output file)
        output_dir: directory to write the annotated image

    Returns:
        path to the saved annotated image
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    basename = Path(image_path).stem
    output_path = str(Path(output_dir) / f"{basename}_out.jpg")

    annotated = image.copy()
    for i, m in enumerate(pill_masks):
        mask = m["segmentation"].astype(np.uint8)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(annotated, contours, -1, (0, 0, 255), 1)
        ys, xs = np.where(mask > 0)
        if len(xs) > 0 and len(ys) > 0:
            cx, cy = int(xs.mean()), int(ys.mean())
            cv2.putText(annotated, str(i + 1), (cx - 10, cy + 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

    cv2.imwrite(output_path, annotated)
    return output_path


def _compute_centroids(pill_masks: list) -> list[tuple[int, int]]:
    """Compute (cx, cy) for each mask. Cached — called once."""
    centroids = []
    for m in pill_masks:
        seg = m["segmentation"].astype(np.uint8)
        ys, xs = np.where(seg > 0)
        if len(xs) == 0:
            centroids.append((-1, -1))
        else:
            centroids.append((int(xs.mean()), int(ys.mean())))
    return centroids


def _build_zone_tree(
    indices: list[int],
    centroids: list[tuple[int, int]],
    row_off: int,
    col_off: int,
    grid_r: int,
    grid_c: int,
    img_h: int,
    img_w: int,
    max_per_zone: int = 10,
) -> tuple[dict[tuple[int, int], list[int]], list[tuple[int, int, int, int]]]:
    """
    Recursively assign masks to zones. Subdivide if zone > max_per_zone.

    Returns:
        - dict of (row, col) -> list of mask indices
        - list of subdivided parent zones as (row, col, sub_rows, sub_cols) in base grid coords
    """
    zone_h = img_h // grid_r
    zone_w = img_w // grid_c
    buckets: dict[tuple[int, int], list[int]] = {}

    for idx in indices:
        cx, cy = centroids[idx]
        if cx < 0:
            continue
        c = min(cx // zone_w, grid_c - 1)
        r = min(cy // zone_h, grid_r - 1)
        buckets.setdefault((r, c), []).append(idx)

    result: dict[tuple[int, int], list[int]] = {}
    subdivisions: list[tuple[int, int, int, int]] = []

    for (r, c), idxs in buckets.items():
        abs_r = row_off + r
        abs_c = col_off + c
        if len(idxs) > max_per_zone:
            # Record subdivided zone at CURRENT grid level
            subdivisions.append((abs_r, abs_c, grid_r, grid_c))
            # Subdivide: split this cell into 2x2
            sub, sub_divs = _build_zone_tree(
                idxs, centroids,
                row_off=abs_r * 2,
                col_off=abs_c * 2,
                grid_r=grid_r * 2,
                grid_c=grid_c * 2,
                img_h=img_h,
                img_w=img_w,
                max_per_zone=max_per_zone,
            )
            result.update(sub)
            subdivisions.extend(sub_divs)
        else:
            result[(abs_r, abs_c)] = idxs

    return result, subdivisions


def save_annotated_zone(
    image: np.ndarray,
    pill_masks: list,
    image_path: str,
    output_dir: str,
    grid_rows: int = 3,
    grid_cols: int = 3,
    max_per_zone: int = 10,
) -> str:
    """
    Draw pill contours grouped by grid zone with per-zone numbering and subtotals.
    Zones with > max_per_zone pills get an internal 2x2 sub-grid drawn only inside them.

    Args:
        image: original BGR image
        pill_masks: list of SAM mask dicts
        image_path: original image path
        output_dir: directory to write the annotated image
        grid_rows: number of zone rows (base grid)
        grid_cols: number of zone columns (base grid)
        max_per_zone: subdivide zone if pill count exceeds this

    Returns:
        path to the saved zone-annotated image
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    basename = Path(image_path).stem
    output_path = str(Path(output_dir) / f"{basename}_zone.jpg")

    h, w = image.shape[:2]
    all_indices = list(range(len(pill_masks)))

    # Cache centroids once
    centroids = _compute_centroids(pill_masks)

    # Build zone tree (recursive subdivision)
    zones, subdivisions = _build_zone_tree(
        all_indices, centroids, 0, 0, grid_rows, grid_cols, h, w, max_per_zone
    )

    # Color palette (BGR)
    zone_colors = [
        (0, 200, 0), (255, 150, 0), (0, 150, 255), (200, 0, 200),
        (0, 255, 255), (255, 100, 100), (100, 255, 100), (100, 100, 255),
        (200, 200, 0),
    ]

    annotated = image.copy()

    # Step 1: Draw base 3x3 grid (always)
    base_h = h // grid_rows
    base_w = w // grid_cols
    for r in range(1, grid_rows):
        cv2.line(annotated, (0, r * base_h), (w, r * base_h), (200, 200, 200), 2)
    for c in range(1, grid_cols):
        cv2.line(annotated, (c * base_w, 0), (c * base_w, h), (200, 200, 200), 2)

    # Step 2: Draw sub-grid lines only inside subdivided zones
    drawn_subs = set()
    for (zr, zc, zgr, zgc) in subdivisions:
        key = (zr, zc, zgr, zgc)
        if key in drawn_subs:
            continue
        drawn_subs.add(key)

        # Pixel rect of this zone at its grid level
        zh = h // zgr
        zw = w // zgc
        y1 = zr * zh
        x1 = zc * zw
        y2 = y1 + zh
        x2 = x1 + zw

        # Draw 2x2 sub-grid inside
        mid_y = y1 + zh // 2
        mid_x = x1 + zw // 2
        cv2.line(annotated, (x1, mid_y), (x2, mid_y), (180, 180, 180), 1)
        cv2.line(annotated, (mid_x, y1), (mid_x, y2), (180, 180, 180), 1)

    # Step 3: Draw pills per zone
    for (row, col), idxs in sorted(zones.items()):
        color = zone_colors[(row * 17 + col * 13) % len(zone_colors)]

        # Determine pixel position for label
        # Find which base zone this belongs to
        if row >= grid_rows or col >= grid_cols:
            # Sub-zone: find the base zone parent
            # row/col are at 2x the base grid level
            base_r = row // 2
            base_c = col // 2
            # Pixel offset within base zone
            sub_in_base_r = row % 2
            sub_in_base_c = col % 2
            by = base_r * base_h
            bx = base_c * base_w
            zone_x1 = bx + sub_in_base_c * (base_w // 2)
            zone_y1 = by + sub_in_base_r * (base_h // 2)
        else:
            zone_x1 = col * base_w
            zone_y1 = row * base_h

        for local_i, mask_i in enumerate(idxs):
            m = pill_masks[mask_i]
            seg = m["segmentation"].astype(np.uint8)
            contours, _ = cv2.findContours(seg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cv2.drawContours(annotated, contours, -1, color, 2)
            cx, cy = centroids[mask_i]
            cv2.putText(annotated, str(local_i + 1), (cx - 10, cy + 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        # Zone label
        label = f"R{row+1}C{col+1}: {len(idxs)}"
        cv2.putText(annotated, label, (zone_x1 + 4, zone_y1 + 18),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)

    # Overall count
    cv2.putText(annotated, f"Total: {len(pill_masks)}", (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

    cv2.imwrite(output_path, annotated)
    return output_path
