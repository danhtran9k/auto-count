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
