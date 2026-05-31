# Iteration 6 — Adaptive shatter filter (per-step median CC area)

## Approach
At each erosion step, drop CCs whose area is < 30% of the step's median CC area,
then take `max(filtered_counts)` over the sweep.

## Results
**Accuracy: 1/15 (6.7%)** — test0 OK; all others severely OVER (test2=1035, test11=312, test15=205).

## Analysis
- The adaptive median filter **doesn't help** because when shatter dominates, the shatter
  fragments ARE the median. The filter keeps them all.
- test1=17, test3=12, test4=15 — close-ish but undercount.
- The fundamental issue with binary-mask + erosion: it can't use any image information
  beyond "is this pixel foreground". Touching pills with a wide bridge between them
  cannot be split by erosion before pills shrink to nothing.
- Need an algorithm that uses **edge / gradient information** to detect inter-pill seams,
  OR detects pills directly by shape.

## Next Steps (iter 7) — strategic pivot
- Switch to **HoughCircles**: pills are circular by construction. Hough directly detects
  circle centers regardless of touching, using gradient image, not binary mask.
- Auto-tune radius range by sweeping `r_center ∈ geomspace(short/80, short/10, ~10 values)`.
- Score each pass by how well `N * π * avg_r²` matches the Otsu foreground area (ratio ≈ 1).
- This is the textbook fix for "count touching circles" problems.
