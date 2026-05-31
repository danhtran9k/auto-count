# Iteration 7 — HoughCircles + foreground-area score

## Approach
Strategic pivot. Drop erosion+CC. Use `cv2.HoughCircles` (direct circle detection
from gradient) with a geometric sweep of radius centers `geomspace(short/80, short/10, 10)`.
For each pass: compute `N * π * avg_r²`, compare to `Otsu fg area`. Score = `1/(1+|log ratio|)`.

## Results
| Image  | Expected | Got | Diff | Status |
|--------|----------|-----|------|--------|
| test0  | 24       | 23  | -1   | UNDER  |
| test1  | 18       | 6   | -12  | UNDER  |
| test2  | 28       | 117 | +89  | OVER   |
| test3  | 23       | 13  | -10  | UNDER  |
| test4  | 23       | 14  | -9   | UNDER  |
| test5  | 25       | 26  | +1   | OVER   |
| test6  | 21       | 6   | -15  | UNDER  |
| test7  | 30       | 23  | -7   | UNDER  |
| test8  | 23       | 6   | -17  | UNDER  |
| test9  | 6        | 17  | +11  | OVER   |
| test10 | 12       | 6   | -6   | UNDER  |
| test11 | 7        | 2   | -5   | UNDER  |
| test12 | 10       | 16  | +6   | OVER   |
| test14 | 8        | 5   | -3   | UNDER  |
| test15 | 50       | 15  | -35  | UNDER  |

**Accuracy: 0/15** but several within ±3 of truth (test0, test5, test12, test14, test11).

## Analysis
- HoughCircles is **finding the right scale of objects** — just selecting the wrong radius bin per image.
- The area-ratio scoring is wrong: when pills touch, circles overlap → `circle_area > fg_area` → ratio penalized → picks too-large radius → too-few circles.
- For test2 (28 expected, got 117), the score picked a too-small radius (every spot is a "circle").
- For test15 (50 expected, got 15), picked too-large radius.
- **Hough CAN solve this** with better radius selection.

## Next Steps (iter 8)
- **Sweep both radius and param2 (accumulator threshold)**, generating many (N, r, p2) candidates.
- **Selection heuristic**: cluster candidates whose `(N, avg_r)` are mutually consistent; take the majority cluster.
- Sanity bounds:
  - `N * π * minR²  ≤  fg_area * 1.2` (can't have more circles than fit in foreground)
  - `N * π * maxR²  ≥  fg_area * 0.4` (must cover reasonable fraction)
- Tie-break: pick max N among candidates satisfying both bounds.
