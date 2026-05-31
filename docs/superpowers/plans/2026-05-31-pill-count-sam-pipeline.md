# Pill Counter SAM Pipeline — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a clean 4-file pipeline that counts pills in images using SAM (Segment Anything Model), replacing 13 iterations of unsuccessful OpenCV heuristics.

**Architecture:** Four files with single responsibilities — core.py (SAM-based counting), eval.py (ground truth comparison), report.py (JSON accumulation), run.py (orchestrator). Only core.py changes when experimenting with strategies.

**Tech Stack:** Python 3, segment-anything, torch, torchvision, opencv-python, numpy

**Spec:** `docs/superpowers/specs/2026-05-31-pill-count-pipeline-design.md`

---

## File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `eval.py` | Rewrite | Single-image evaluation against ground truth |
| `report.py` | Create | Accumulate eval results, write report.json |
| `core.py` | Create | Process one image with SAM, return count |
| `run.py` | Create | Orchestrator — zero logic, just plumbing |
| `requirements.txt` | Create | Python dependencies |

---

## Phase 1: Pipeline Scaffold

### Task 1: Create eval.py

**Files:**
- Rewrite: `eval.py`

- [ ] **Step 1: Write eval.py**

```python
"""
Evaluate a single image result against ground truth.

GROUND_TRUTH is hardcoded from user_specs.md.
This file is essentially fixed — do not modify.
"""

GROUND_TRUTH = {
    "test0": 24, "test1": 18, "test2": 28, "test3": 23,
    "test4": 23, "test5": 25, "test6": 21, "test7": 30,
    "test8": 23, "test9": 6, "test10": 12, "test11": 7,
    "test12": 10, "test14": 8, "test15": 50,
}


def evaluate(image_name: str, result: dict) -> dict:
    """
    Evaluate one image result against ground truth.

    Args:
        image_name: e.g. "test0" (key into GROUND_TRUTH)
        result: dict from core.process(), must have "count" key

    Returns:
        dict with: image, count, expected, diff, match
    """
    expected = GROUND_TRUTH.get(image_name)
    if expected is None:
        return {
            "image": image_name,
            "count": result.get("count", -1),
            "expected": None,
            "diff": None,
            "match": False,
            "error": f"unknown image: {image_name}",
        }

    count = result.get("count", -1)
    diff = count - expected
    return {
        "image": image_name,
        "count": count,
        "expected": expected,
        "diff": diff,
        "match": count == expected,
    }
```

- [ ] **Step 2: Verify it works**

Run: `python3 -c "from eval import evaluate; print(evaluate('test0', {'count': 24}))"`
Expected: `{'image': 'test0', 'count': 24, 'expected': 24, 'diff': 0, 'match': True}`

- [ ] **Step 3: Commit**

```bash
git add eval.py
git commit -m "refactor: rewrite eval.py as single-image evaluation function"
```

---

### Task 2: Create report.py

**Files:**
- Create: `report.py`

- [ ] **Step 1: Write report.py**

```python
"""
Accumulate evaluation results and write report.json.
"""

import json


def create() -> dict:
    """Create empty report structure."""
    return {"results": {}, "summary": {}}


def add(report: dict, eval_result: dict) -> dict:
    """Append one eval result to the report. Returns updated report."""
    image_name = eval_result["image"]
    report["results"][image_name] = eval_result
    return report


def summary(report: dict) -> dict:
    """Compute summary stats from all results."""
    results = report["results"]
    total = len(results)
    matches = sum(1 for r in results.values() if r.get("match"))
    accuracy_pct = round(matches / total * 100, 1) if total > 0 else 0.0
    return {
        "matches": matches,
        "total": total,
        "accuracy_pct": accuracy_pct,
    }


def save(report: dict, path: str = "report.json"):
    """Write final report to JSON file."""
    report["summary"] = summary(report)
    with open(path, "w") as f:
        json.dump(report, f, indent=2)
```

- [ ] **Step 2: Verify it works**

Run: `python3 -c "from report import create, add, summary; r = create(); r = add(r, {'image': 'test0', 'count': 24, 'expected': 24, 'diff': 0, 'match': True}); print(summary(r))"`
Expected: `{'matches': 1, 'total': 1, 'accuracy_pct': 100.0}`

- [ ] **Step 3: Commit**

```bash
git add report.py
git commit -m "feat: add report.py for result accumulation and JSON export"
```

---

### Task 3: Create core.py (placeholder)

**Files:**
- Create: `core.py`

- [ ] **Step 1: Write core.py with placeholder**

```python
"""
Core image processing — counts pills in a single image.

This is the experiment zone. Swap implementations freely.
All other files consume output through the dict interface.
"""

import os


def process(image_path: str) -> dict:
    """
    Process a single image and return results.

    Args:
        image_path: path to one image file

    Returns:
        dict with:
          - "count": int (-1 on error)
          - "output_file": str (path to annotated output image)
    """
    if not os.path.exists(image_path):
        return {"count": -1, "output_file": "", "error": "file not found"}

    # Placeholder — returns 0 until SAM is integrated
    return {"count": 0, "output_file": ""}
```

- [ ] **Step 2: Verify it works**

Run: `python3 -c "from core import process; print(process('test-img/test0.jpg'))"`
Expected: `{'count': 0, 'output_file': ''}`

- [ ] **Step 3: Commit**

```bash
git add core.py
git commit -m "feat: add core.py with placeholder implementation"
```

---

### Task 4: Create run.py

**Files:**
- Create: `run.py`

- [ ] **Step 1: Write run.py**

```python
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
```

- [ ] **Step 2: Verify pipeline runs end-to-end**

Run: `python3 run.py test-img/`
Expected: All images show `got=0`, accuracy 0/15, report.json created

- [ ] **Step 3: Check report.json was created**

Run: `cat report.json`
Expected: JSON with all 15 images, count=0, summary shows 0/15

- [ ] **Step 4: Commit**

```bash
git add run.py report.json
git commit -m "feat: add run.py orchestrator and verify pipeline works end-to-end"
```

---

## Phase 2: SAM Integration

### Task 5: Install SAM dependencies

**Files:**
- Create: `requirements.txt`

- [ ] **Step 1: Create requirements.txt**

```
segment-anything
torch
torchvision
opencv-python
numpy
```

- [ ] **Step 2: Install dependencies**

Run: `pip install -r requirements.txt`
Expected: Successful installation

- [ ] **Step 3: Download SAM checkpoint**

Run: `python3 -c "from segment_anything import sam_model_registry; print('SAM import OK')" `
Expected: `SAM import OK`

Download the vit_b checkpoint:
```bash
wget https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth -O sam_vit_b.pth
```
Or use curl:
```bash
curl -L -o sam_vit_b.pth https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth
```

- [ ] **Step 4: Verify checkpoint exists**

Run: `ls -lh sam_vit_b.pth`
Expected: File ~375MB

- [ ] **Step 5: Commit**

```bash
git add requirements.txt
git commit -m "deps: add SAM and torch dependencies"
```

Note: Do NOT commit sam_vit_b.pth (add to .gitignore if needed).

---

### Task 6: Implement core.py with SAM

**Files:**
- Modify: `core.py`

- [ ] **Step 1: Rewrite core.py with SAM**

```python
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
```

- [ ] **Step 2: Test on one image**

Run: `python3 -c "from core import process; r = process('test-img/test0.jpg'); print(r)"`
Expected: dict with count > 0, output_file path, num_masks

- [ ] **Step 3: Verify annotated image exists**

Run: `ls test-img/test0_out.jpg`
Expected: File exists

- [ ] **Step 4: Commit**

```bash
git add core.py
git commit -m "feat: implement core.py with SAM automatic mask generation"
```

---

### Task 7: Run full evaluation

**Files:**
- None (just running existing code)

- [ ] **Step 1: Run pipeline on all test images**

Run: `python3 run.py test-img/`
Expected: Per-image results printed to stderr, report.json written

- [ ] **Step 2: Review report.json**

Run: `cat report.json`
Expected: JSON with all 15 images, varying accuracy

- [ ] **Step 3: Note baseline accuracy**

Record the accuracy from stderr output. This is the SAM baseline before any filtering tuning.

- [ ] **Step 4: Commit**

```bash
git add report.json
git commit -m "eval: SAM baseline results"
```

---

## Phase 3: Filter Tuning

### Task 8: Tune area filters

**Files:**
- Modify: `core.py`

- [ ] **Step 1: Analyze results**

Look at report.json. For each image:
- If OVER: too many masks passing the filter → tighten max_area or add shape filters
- If UNDER: pills being filtered out → loosen min_area

- [ ] **Step 2: Adjust area thresholds if needed**

In `core.py`, modify the area filter bounds:
```python
min_area = image_area * 0.0005  # adjust based on results
max_area = image_area * 0.15    # adjust based on results
```

- [ ] **Step 3: Run eval again**

Run: `python3 run.py test-img/`
Expected: Improved accuracy

- [ ] **Step 4: Commit**

```bash
git add core.py report.json
git commit -m "tune: adjust SAM mask area filters"
```

---

### Task 9: Add shape filtering

**Files:**
- Modify: `core.py`

- [ ] **Step 1: Add circularity/aspect ratio filter**

After the area filter, add shape-based filtering:

```python
    pill_masks = []
    for m in masks:
        area = m["area"]
        if not (min_area <= area <= max_area):
            continue

        # Shape filter: check if mask is roughly compact (not elongated noise)
        mask = m["segmentation"].astype(np.uint8)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            continue
        cnt = max(contours, key=cv2.contourArea)
        perimeter = cv2.arcLength(cnt, True)
        if perimeter == 0:
            continue
        circularity = 4 * np.pi * area / (perimeter * perimeter)
        if circularity < 0.3:  # too elongated/irregular — likely noise
            continue

        pill_masks.append(m)
```

- [ ] **Step 2: Run eval**

Run: `python3 run.py test-img/`
Expected: Improved accuracy from removing non-pill masks

- [ ] **Step 3: Commit**

```bash
git add core.py report.json
git commit -m "tune: add circularity filter to remove irregular masks"
```

---

### Task 10: Iterate until 15/15

**Files:**
- Modify: `core.py`

- [ ] **Step 1: Review remaining failures**

Look at report.json. For each failing image, check the annotated output (`*_out.jpg`) to see:
- Are pills being missed? (UNDER)
- Are non-pill objects being counted? (OVER)

- [ ] **Step 2: Adjust filters based on findings**

Possible adjustments:
- Tighten/loosen area bounds
- Adjust circularity threshold
- Add aspect ratio filter (width/height of bounding box)
- Adjust SAM parameters (points_per_side, pred_iou_thresh, stability_score_thresh)

- [ ] **Step 3: Run eval after each adjustment**

Run: `python3 run.py test-img/`

- [ ] **Step 4: Repeat until 15/15**

Keep iterating steps 1-3 until accuracy is 100%.

- [ ] **Step 5: Final commit**

```bash
git add core.py report.json
git commit -m "feat: achieve 15/15 accuracy with SAM + tuned filters"
```

---

## Verification

After all tasks, run:
```bash
python3 run.py test-img/
```

Expected output:
```
  test0: got=24 expected=24 diff=+0 OK
  test1: got=18 expected=18 diff=+0 OK
  ...
Accuracy: 15/15 (100.0%)
Report saved to report.json
```

Exit code: 0
