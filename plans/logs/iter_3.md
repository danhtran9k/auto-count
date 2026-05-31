# Iteration 3 — Area-based: isolated singles set the unit

## Approach
Sidestep radius estimation. Find isolated single-pill CCs (where `area ≈ π * dist_max²`,
i.e. roughly a disk) and use their median area as the counting unit. For cluster CCs,
add `round(cluster_area / unit_area)` pills.

## Results
| Image  | Expected | Got  | Diff  | Status |
|--------|----------|------|-------|--------|
| test0  | 24       | 1    | -23   | UNDER  |
| test1  | 18       | 760  | +742  | OVER   |
| test2  | 28       | 595  | +567  | OVER   |
| test3  | 23       | 1    | -22   | UNDER  |
| test4  | 23       | 1    | -22   | UNDER  |
| test5  | 25       | 514  | +489  | OVER   |
| test6  | 21       | 205  | +184  | OVER   |
| test7  | 30       | 1    | -29   | UNDER  |
| test8  | 23       | 765  | +742  | OVER   |
| test9  | 6        | 971  | +965  | OVER   |
| test10 | 12       | 203  | +191  | OVER   |
| test11 | 7        | 10   | +3    | OVER   |
| test12 | 10       | 1371 | +1361 | OVER   |
| test14 | 8        | 3    | -5    | UNDER  |
| test15 | 50       | 482  | +432  | OVER   |

**Accuracy: 0/15** — bimodal failure: some images severely UNDER, others ridiculously OVER.

## Analysis
- **`min_area = 0.05% * img_area` is too coarse**: in test0/test3/test4/test7, individual pills are
  small enough to fall below the threshold → all CCs filtered out except one big blob → count = 1.
- **Noise speckles classify as "small singles"**: dust / glare blobs that pass `min_area` are circular
  by coincidence → they enter the `singles` list with tiny `area` → `unit_area` collapses to ~50–200 px
  → real cluster CCs get divided by this tiny unit → counts in the hundreds (test12=1371).
- The fundamental problem: **the classifier for "is this CC a single pill?" needs to distinguish
  pills from noise without knowing pill size in advance.** This is circular.
- **Distance transform of a binary cluster mask does NOT have per-pill peaks** in the deep interior
  of a tight cluster — the distance is to the nearest *background*, not to the nearest pill boundary.
  A pill buried inside a 4×5 grid of touching pills has `dist` ≈ distance to cluster edge, not to its
  neighbor's edge. This is why every distance-transform-based approach has struggled.
- To split touching pills we need either:
  - **Image gradients** at the inter-pill seam (faint dark crease), OR
  - **Morphological erosion** until the bridges between pills break.

## Next Steps (iter 4)
1. **Erosion sweep + max CC count.** For `n = 0..K`, compute `cv2.erode(mask, kernel, iter=n)`,
   then count valid CCs. Clusters split into individual CCs as bridges erode away. Take the
   maximum count over the sweep.
2. Filter CCs by an absolute minimum area (e.g. 20 px) — only to drop true speckle noise.
3. If `max` overcounts due to a single intermediate state, smooth: use the count at the *first plateau*
   above a threshold instead.
4. This is the textbook "ultimate erosion" approach for counting touching objects.
