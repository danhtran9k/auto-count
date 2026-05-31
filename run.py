"""
Orchestrator — finds images, pipes through core → eval → report.
Zero business logic.
"""

import os
import sys

from core import process
from utils.annotated import save_annotated, OUTPUT_DIR
from utils.eval import evaluate
from utils.report import create, add, save

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
    report = create()
    image_paths = get_image_paths(folder_path)

    if not image_paths:
        print(f"No images found in {folder_path}", file=sys.stderr)
        return

    for img_path in image_paths:
        name = image_name_from_path(img_path)
        result = process(img_path)
        result["output_file"] = save_annotated(
            result["image"], result["pill_masks"], result["image_path"], OUTPUT_DIR
        )
        
        # Evaluated
        eval_result = evaluate(name, result)

        # Report
        add(report, eval_result)

        if "error" in eval_result:
            status = f"ERROR: {eval_result['error']}"
        elif eval_result["match"]:
            status = "OK"
        else:
            status = f"diff={eval_result['diff']:+d}"
        print(f"  {name}: got={eval_result['count']} expected={eval_result['expected']} {status}", file=sys.stderr)

    report_path = os.path.join(OUTPUT_DIR, "report.json")
    save(report, report_path)

    s = report["summary"]
    print(f"\nAccuracy: {s['matches']}/{s['total']} ({s['accuracy_pct']}%)", file=sys.stderr)
    print(f"Report saved to {report_path}", file=sys.stderr)


if __name__ == "__main__":
    folder = sys.argv[1] if len(sys.argv) > 1 else "test-img"
    run_folder(folder)
