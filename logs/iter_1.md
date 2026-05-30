# Iteration 1 — Otsu + Distance Transform + Global Seed Threshold

## Approach
Replaced the iter 0 candidate-generation/selection scheme with a single principled pipeline:
1. Grayscale + Gaussian blur (5x5).
2. Auto bg/fg detection via corner-vs-image median, then Otsu threshold (inverted if bg is bright).
3. Morphological open(2) + close(2) with 3x3 ellipse kernel.
4. Distance transform (L2, mask 5).
5. Threshold distance map at `0.5 * dist.max()` to get seeds.
6. Count connected components (filter tiny ones < 0.005% img area).

## Results
| Image  | Expected | Got | Diff | Status |
|--------|----------|-----|------|--------|
| test0  | 24       | 24  | +0   | OK     |
| test1  | 18       | 4   | -14  | UNDER  |
| test2  | 28       | 2   | -26  | UNDER  |
| test3  | 23       | 3   | -20  | UNDER  |
| test4  | 23       | 1   | -22  | UNDER  |
| test5  | 25       | 1   | -24  | UNDER  |
| test6  | 21       | 1   | -20  | UNDER  |
| test7  | 30       | 2   | -28  | UNDER  |
| test8  | 23       | 3   | -20  | UNDER  |
| test9  | 6        | 3   | -3   | UNDER  |
| test10 | 12       | 3   | -9   | UNDER  |
| test11 | 7        | 1   | -6   | UNDER  |
| test12 | 10       | 3   | -7   | UNDER  |
| test14 | 8        | 2   | -6   | UNDER  |
| test15 | 50       | 3   | -47  | UNDER  |

**Accuracy: 1/15 (6.7%)** — total |diff| = 252 (worse than iter 0's 235, but for a different reason)

## Analysis
- **test0 (24/24)**: 24 well-separated, similarly-sized objects → the global-threshold seed scheme worked.
- **The global-threshold failure mode**: when the foreground includes any region whose distance-from-bg is much larger
  than a typical pill radius (e.g. a tightly-packed cluster forms a big "blob" whose deepest interior point is
  far from any background), `dist.max()` is dominated by that one peak. `0.5 * dist.max()` then exceeds the
  distance-peak of every individual pill, killing all but a couple of seeds. This explains the catastrophic UNDER
  on test4 (1), test5 (1), test6 (1), test11 (1), test15 (3, 50 pills).
- **Touching pills not actually split** by the seed step in most cases, because the seed threshold is calibrated
  to the wrong scale. The distance transform itself is correct; selection is wrong.
- Compared to iter 0, total |diff| got slightly worse (252 vs 235) but iter 1 actually has 1 OK vs iter 0's 0,
  and the failure pattern is now diagnostic (1 pipeline, 1 cause) rather than a black-box selection heuristic.

## Next Steps (iter 2)
1. **Replace global seed threshold with local-maxima detection**: a pixel is a seed iff it equals
   `cv2.dilate(dist, square_kernel)` within a window sized to the expected pill radius. This naturally
   places one seed per pill regardless of cluster geometry.
2. **Auto-estimate pill radius**: e.g., median of per-CC `dist.max()` values across the cleaned mask,
   or mode of bounding-box short sides of small isolated CCs.
3. Add a minimum dist-peak threshold (e.g. `> 0.3 * estimated_radius`) to reject spurious noise peaks.
4. If still struggling, fall back to `cv2.HoughCircles` as an independent signal — pills are roughly circular.
