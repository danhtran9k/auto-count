"""
Orchestrator — finds images, pipes through core → eval → report.
Zero business logic.
"""

import os
import sys

from core import process
from utils.annotated import save_annotated, save_annotated_zone, OUTPUT_DIR
from utils.annotated_debug import save_debug
from utils.eval import evaluate
from utils.report import create_empty_report, add_image_result, save_and_log, timed_image

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp"}


def get_image_paths(folder: str) -> list[str]:
    """Get all image file paths in folder (non-recursive)."""
    paths = []
    for f in sorted(os.listdir(folder)):
        ext = os.path.splitext(f)[1].lower()
        if ext in IMAGE_EXTENSIONS and "_out" not in f:
            paths.append(os.path.join(folder, f))
    return paths


def image_name_from_path(path: str) -> str:
    """Extract image name without extension, e.g. 'test0'."""
    return os.path.splitext(os.path.basename(path))[0]


def run_folder(folder_path: str):
    """
    Pure orchestrator. No business logic.

    1. Find all image files in folder (non-recursive)
    2. For each image: core → eval → report
    3. Save report to the same timestamped output folder as images
    """
    report = create_empty_report()
    image_paths = get_image_paths(folder_path)

    if not image_paths:
        print(f"No images found in {folder_path}", file=sys.stderr)
        return

    for img_path in image_paths:
        name = image_name_from_path(img_path)
        with timed_image(report, name):
            result = process(img_path)
            add_image_result(report, name, result["count"])

            eval_result = evaluate(name, result)
            expected = eval_result.get("expected") if eval_result else None
            if eval_result:
                report["results"][name].update(eval_result)

            result["debug_file"] = save_debug(
                result["image"], result["pill_masks"], result["raw_masks"],
                result["image_path"], OUTPUT_DIR, expected,
            )
            
            # result["output_file"] = save_annotated(
            #     result["image"], result["pill_masks"], result["image_path"], OUTPUT_DIR
            # )
            # result["zone_file"] = save_annotated_zone(
            #     result["image"], result["pill_masks"], result["image_path"], OUTPUT_DIR
            # )


    report_path = os.path.join(OUTPUT_DIR, "report.json")
    save_and_log(report, report_path)


if __name__ == "__main__":
    folder = sys.argv[1] if len(sys.argv) > 1 else "test-img"
    run_folder(folder)
