"""
Pill Counter v6 — multi-approach with auto threshold selection.

Strategy:
1. Estimate background from corners
2. Try multiple threshold offsets and pick the one giving the most "reasonable" count
3. Use Canny edge-based detection as backup
4. Combine results
"""
import cv2
import numpy as np
import json
import sys
import os

GROUND_TRUTH = {
    "test0": 24, "test1": 18, "test2": 28, "test3": 23,
    "test4": 23, "test5": 25, "test6": 21, "test7": 30,
    "test8": 23, "test9": 6, "test10": 12, "test11": 7,
    "test12": 10, "test14": 8, "test15": 50,
}


def get_bg(gray):
    """Estimate background from corners."""
    h, w = gray.shape
    patch = min(20, h // 10, w // 10)
    corners = np.concatenate([
        gray[:patch, :patch].flatten(),
        gray[:patch, -patch:].flatten(),
        gray[-patch:, :patch].flatten(),
        gray[-patch:, -patch:].flatten(),
    ])
    return np.median(corners)


def count_with_threshold(gray, bg_val, offset, img_area):
    """Count objects using threshold at bg +/- offset."""
    h, w = gray.shape

    if bg_val > 128:
        _, thresh = cv2.threshold(gray, int(bg_val - offset), 255, cv2.THRESH_BINARY_INV)
    else:
        _, thresh = cv2.threshold(gray, int(bg_val + offset), 255, cv2.THRESH_BINARY)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)
    opened = cv2.morphologyEx(closed, cv2.MORPH_OPEN, kernel, iterations=1)

    contours, _ = cv2.findContours(opened, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    min_area = img_area * 0.0005
    max_area = img_area * 0.15

    valid = []
    for c in contours:
        area = cv2.contourArea(c)
        if min_area <= area <= max_area:
            valid.append(c)

    return len(valid)


def count_with_canny(gray, img_area):
    """Count objects using Canny edge detection + contour filling."""
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 30, 100)

    # Dilate edges to close gaps
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    dilated = cv2.dilate(edges, kernel, iterations=2)

    # Fill enclosed regions
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    min_area = img_area * 0.0005
    max_area = img_area * 0.15

    valid = []
    for c in contours:
        area = cv2.contourArea(c)
        if min_area <= area <= max_area:
            valid.append(c)

    return len(valid)


def count_pills(image_path: str) -> tuple:
    """Multi-approach counting. Returns (count, diagnostics)."""
    img = cv2.imread(image_path)
    if img is None:
        return -1, {}

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    img_area = h * w
    bg_val = get_bg(gray)

    # CLAHE for contrast
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    # Try multiple threshold offsets
    results = {}
    for offset in [15, 20, 25, 30, 35, 40, 50, 60]:
        cnt = count_with_threshold(enhanced, bg_val, offset, img_area)
        results[f"thresh_{offset}"] = cnt

    # Also try on raw gray
    for offset in [20, 30, 40, 50]:
        cnt = count_with_threshold(gray, bg_val, offset, img_area)
        results[f"raw_{offset}"] = cnt

    # Canny approach
    results["canny"] = count_with_canny(gray, img_area)
    results["canny_enhanced"] = count_with_canny(enhanced, img_area)

    # Pick the best: use median of non-zero results as heuristic
    non_zero = [v for v in results.values() if v > 0]
    if non_zero:
        # Use the result closest to the median (most "reasonable" count)
        median_val = np.median(non_zero)
        best_key = min(results.keys(), key=lambda k: abs(results[k] - median_val) if results[k] > 0 else 9999)
        best_count = results[best_key]
    else:
        best_count = 0
        best_key = "none"

    diag = {
        "bg": round(float(bg_val), 1),
        "approaches": results,
        "best_approach": best_key,
        "shape": [h, w],
    }

    return best_count, diag


def main():
    results = {}
    img_dir = os.path.join(os.path.dirname(__file__), "test-img")

    for name in sorted(GROUND_TRUTH.keys()):
        path = os.path.join(img_dir, f"{name}.jpg")
        if not os.path.exists(path):
            results[name] = {"count": -1, "expected": GROUND_TRUTH[name], "error": "file not found"}
            continue

        count, diag = count_pills(path)
        expected = GROUND_TRUTH[name]
        diff = count - expected
        results[name] = {
            "count": count, "expected": expected, "diff": diff, "match": count == expected,
            "diag": diag,
        }

    total_tests = len(GROUND_TRUTH)
    matches = sum(1 for r in results.values() if r.get("match"))
    total_diff = sum(abs(r.get("diff", 0)) for r in results.values())

    for name in sorted(results.keys()):
        r = results[name]
        status = "OK" if r["match"] else ("OVER" if r["diff"] > 0 else "UNDER")
        d = r["diag"]
        print(f"  {name}: got={r['count']} expected={r['expected']} diff={r['diff']:+d} bg={d.get('bg',0)} best={d.get('best_approach','')} {status}", file=sys.stderr)

    output = {
        "results": results,
        "summary": {
            "total_tests": total_tests, "matches": matches,
            "accuracy_pct": round(matches / total_tests * 100, 1),
            "total_abs_diff": total_diff,
        }
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
