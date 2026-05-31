# Iteration 2 — Local-max seeds with median-CC radius estimate

## Approach
Replaced iter 1's global `0.5 * dist.max()` seed cut with **per-pill local maxima**:
1. Otsu mask → morph clean → distance transform (same as iter 1).
2. Estimate `pill_r` = median of per-CC `dist.max()` over non-tiny CCs.
3. Local-max kernel: `cv2.dilate(dist, ones((win, win)))` with `win ≈ 1.5 * pill_r`.
4. Seed = pixel where `dist == dilated_dist AND dist >= 0.5 * pill_r`.
5. Count seed connected components.

## Results
| Image  | Expected | Got | Diff | Status |
|--------|----------|-----|------|--------|
| test0  | 24       | 24  | +0   | OK     |
| test1  | 18       | 300 | +282 | OVER   |
| test2  | 28       | 746 | +718 | OVER   |
| test3  | 23       | 3   | -20  | UNDER  |
| test4  | 23       | 199 | +176 | OVER   |
| test5  | 25       | 134 | +109 | OVER   |
| test6  | 21       | 32  | +11  | OVER   |
| test7  | 30       | 263 | +233 | OVER   |
| test8  | 23       | 272 | +249 | OVER   |
| test9  | 6        | 435 | +429 | OVER   |
| test10 | 12       | 299 | +287 | OVER   |
| test11 | 7        | 162 | +155 | OVER   |
| test12 | 10       | 460 | +450 | OVER   |
| test14 | 8        | 97  | +89  | OVER   |
| test15 | 50       | 181 | +131 | OVER   |

**Accuracy: 1/15 (6.7%)** — total |diff| = 3439, catastrophically OVER (vs iter 1's all-UNDER).

## Analysis
- The **per-CC median radius estimator is wildly unstable**:
  - Tiny / noisy CCs with `dist.max()` ≈ 1–2 px drag the median down → window tiny → every flat-top pixel in
    the distance map becomes a "local max" → 100s of false peaks (test1=300, test2=746, test9=435, test12=460).
  - test3 went the other way: window too large → only 3 peaks survive in the entire image.
- The CC distribution is bimodal/multimodal in clustered images:
  - Many tiny noise CCs (dust, edges)
  - A few large cluster CCs (touching-pill blobs)
  - Few or zero "isolated single pill" CCs to anchor the estimate.
- Median across this distribution gives a meaningless number.
- The local-max-of-distance-transform idea is still correct in principle. The blocker is reliably
  **estimating pill radius without already knowing the count**.

## Next Steps (iter 3)
1. **Skip radius estimation entirely. Use area-based counting from isolated single pills as the unit:**
   - Otsu → cleaned mask → CCs filtered by min area.
   - For each CC, compute circularity score: `score = area / (π * dist_max²)`.
     A score ≈ 1.0 indicates an isolated single pill (disk).
   - Use single-pill CCs to estimate `single_pill_area`.
   - For "cluster" CCs (score >> 1): `count += round(area / single_pill_area)`.
2. Fallback when no clean single pills exist: pick the smallest non-noise CC area as the unit.
3. This sidesteps the radius-estimation trap and uses the most reliable signal (a clearly-isolated pill).
