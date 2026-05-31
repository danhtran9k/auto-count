"""
Orchestrator — finds images, pipes through core → eval → report.
Zero business logic.
"""

import os
import sys

from core import process
from eval import evaluate
from report import create, add, save

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp"}


def get_image_paths(folder: str) -> list[str]:
    """Get all image file paths in folder (non-recursive)."""
    paths = []
    for f in sorted(os.listdir(folder)):
        ext = os.path.splitext(f)[1].lower()
        if ext in IMAGE_EXTENSIONS:
            paths.append(os.path.join(folder, f))
    return paths


def image_name_from_path(path: str) -> str:
    """Extract image name without extension, e.g. 'test0'."""
    return os.path.splitext(os.path.basename(path))[0]


def run_folder(folder_path: str, report_path: str = "report.json"):
    """
    Pure orchestrator. No business logic.

    1. Find all image files in folder (non-recursive)
    2. For each image: core → eval → report
    3. Save report
    """
    report = create()
    image_paths = get_image_paths(folder_path)

    if not image_paths:
        print(f"No images found in {folder_path}", file=sys.stderr)
        return

    for img_path in image_paths:
        name = image_name_from_path(img_path)
        result = process(img_path)
        eval_result = evaluate(name, result)
        add(report, eval_result)

        status = "OK" if eval_result["match"] else f"diff={eval_result['diff']:+d}"
        print(f"  {name}: got={eval_result['count']} expected={eval_result['expected']} {status}", file=sys.stderr)

    save(report, report_path)

    s = report["summary"]
    print(f"\nAccuracy: {s['matches']}/{s['total']} ({s['accuracy_pct']}%)", file=sys.stderr)
    print(f"Report saved to {report_path}", file=sys.stderr)


if __name__ == "__main__":
    folder = sys.argv[1] if len(sys.argv) > 1 else "test-img"
    report = sys.argv[2] if len(sys.argv) > 2 else "report.json"
    run_folder(folder, report)
