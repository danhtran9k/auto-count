# Pill Counter Pipeline Architecture

## Overview

Restructure the pill counting system into a clean pipeline with four files, each with a single responsibility. The core processing logic uses **SAM (Segment Anything Model)** as the primary approach, replacing the 13-iteration OpenCV trial-and-error approach.

## Why SAM?

After 13 iterations of classical CV (OpenCV), the best result was ~4-5/15 accuracy. The root cause: images contain interference (paper labels, container edges, glare) that classical thresholding cannot distinguish from pills.

SAM solves this directly:
- **Zero-shot segmentation** — no training needed, works out of the box
- **Instance segmentation** — separates touching objects natively
- **Understands "objects"** — trained on 11M images, 1.1B masks
- **Simple code** — ~50 lines vs hundreds of lines of heuristic tuning

## Architecture

```
run.py (orchestrator — zero logic)
│
│  get image paths from folder (non-recursive)
│  for each image:
│
├─► core.process(path)                    → result_json
├─► eval.evaluate(image_name, result_json) → eval_result
└─► report.add(eval_result)
    report.save("report.json")
```

## File Responsibilities

| File | Responsibility | Changes? |
|------|---------------|----------|
| `core.py` | Process one image using SAM, return count + diagnostics | Freely — experiment zone |
| `eval.py` | Compare result vs ground truth for one image | Almost never |
| `report.py` | Accumulate eval results, write report.json | Almost never |
| `run.py` | Get paths, call the three above in sequence | Almost never |

## Interfaces

### core.py

```python
def process(image_path: str) -> dict:
    """
    Process a single image using SAM and return results.

    Input: absolute or relative path to one image file
    Output: dict with at minimum:
      - "count": int          # -1 on error
      - "output_file": str    # path to annotated/debug output image

    May include additional diagnostics (mask count, confidence, timing, etc.)
    """
```

This is the only file that changes when experimenting with counting strategies.

### eval.py

```python
GROUND_TRUTH = {
    "test0": 24, "test1": 18, "test2": 28, "test3": 23,
    "test4": 23, "test5": 25, "test6": 21, "test7": 30,
    "test8": 23, "test9": 6, "test10": 12, "test11": 7,
    "test12": 10, "test14": 8, "test15": 50,
}

def evaluate(image_name: str, result: dict) -> dict:
    """
    Evaluate one image result against ground truth.

    Input:
      - image_name: e.g. "test0" (key into GROUND_TRUTH)
      - result: dict from core.process(), must have "count" key
    Output: dict with:
      - "image": str
      - "count": int
      - "expected": int
      - "diff": int
      - "match": bool
    """
```

### report.py

```python
def create() -> dict:
    """Create empty report structure."""

def add(report: dict, eval_result: dict) -> dict:
    """Append one eval result to the report. Returns updated report."""

def save(report: dict, path: str = "report.json"):
    """Write final report to JSON file."""

def summary(report: dict) -> dict:
    """Compute summary stats (matches, total, accuracy_pct)."""
```

### run.py

```python
def run_folder(folder_path: str, report_path: str = "report.json"):
    """
    Pure orchestrator. No business logic.

    1. Find all image files in folder (non-recursive, .jpg/.jpeg/.png/.bmp)
    2. For each image:
       a. result = core.process(img_path)
       b. eval_result = eval.evaluate(img_name, result)
       c. report.add(eval_result)
    3. report.save(report_path)
    """
```

`run.py` contains no conditionals, no data transformation, no decision-making. It is a dumb pipe.

## Output Format

### report.json

```json
{
  "results": {
    "test0": {
      "image": "test0",
      "count": 24,
      "expected": 24,
      "diff": 0,
      "match": true
    }
  },
  "summary": {
    "matches": 15,
    "total": 15,
    "accuracy_pct": 100.0
  }
}
```

## SAM Implementation Details

### Model
- Use `segment-anything` package (Meta AI)
- Model: `sam_vit_b` (smallest, ~375MB download)
- Use `SamAutomaticMaskGenerator` for zero-shot segmentation

### Core Logic
```python
from segment_anything import sam_model_registry, SamAutomaticMaskGenerator

sam = sam_model_registry["vit_b"](checkpoint="sam_vit_b.pth")
mask_generator = SamAutomaticMaskGenerator(sam)
masks = mask_generator.generate(image)

# Filter masks by expected pill size range
# Count remaining masks
```

### Filtering Strategy
SAM generates masks for ALL objects in the image. Filter by:
1. **Area** — pills are within a known size range relative to image
2. **Circularity/aspect ratio** — pills are roughly round or capsule-shaped
3. **Confidence** — SAM provides stability scores per mask

### Dependencies
```
segment-anything
torch
torchvision
opencv-python
numpy
```

## Iteration Plan

### Phase 1: Pipeline Scaffold
- Create the 4-file architecture with placeholder core.py
- Verify pipeline runs end-to-end

### Phase 2: SAM Integration
- Install SAM, download model checkpoint
- Implement core.py with SamAutomaticMaskGenerator
- Run eval, see baseline accuracy

### Phase 3: Filter Tuning
- Adjust area/circularity filters to eliminate non-pill masks
- Tune confidence threshold
- Target: 15/15

## Previous Approach (Archived)

The OpenCV-based approach is documented in `docs/approach_non_ml.md`. After 13 iterations:
- Best accuracy: ~4-5/15
- Root failure: cannot distinguish pills from interference in grayscale masks
- LAB chroma filtering was proposed but not yet tried
- Decision: pivot to SAM for higher probability of complete solution
