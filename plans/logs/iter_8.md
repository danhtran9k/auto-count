# Iteration 8 — Hough dual-sweep (radius × param2) with area-budget cap

## Approach
For each `(r_center, param2)`, accept Hough circles if `circle_area <= 1.3 * fg_area`.
Track the last accepted N per radius; return the max across radii.

## Results
**Accuracy: 0/15** — every image OVER by 50–600. The "max across radii" picks the smallest
radius (3–4 px), which fits hundreds of tiny circles into 1.3× fg budget.

## Analysis
- Smallest radius wins because `N ∝ 1/r²` at fixed area budget.
- Area-budget alone cannot determine the correct radius.
- The right signal: **stability** — at the true radius, the count is stable across param2
  values; at wrong radii, count is erratic.

## Next Steps (iter 9)
Pivot back to iter 4's erosion sweep (best so far: 2/15) and try a **multi-method ensemble**:
1. Otsu CC count at no erosion.
2. Erosion sweep first-peak count.
3. Erosion sweep at peak / 2 fraction.
4. Hough with a smarter "stability" radius pick.

Take the **median** of the candidate counts as the final answer.
Median is robust to one outlier method.
