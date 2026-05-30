# Iteration 0 — Baseline (port of pill_counter.py)

## Approach
Direct port of existing `pill_counter.py` to `counter.py` with the stable contract `count_pills(path) -> int`. Strategy:
- Estimate background gray value from 4 corner patches.
- Generate count candidates via multi-offset thresholding (on CLAHE-enhanced and raw gray) + Canny edge dilation.
- Pick the non-zero candidate closest to the median of all non-zero candidates.

No algorithm changes from `pill_counter.py` — this just establishes the baseline.

## Results
| Image  | Expected | Got | Diff | Status |
|--------|----------|-----|------|--------|
| test0  | 24       | 1   | -23  | UNDER  |
| test1  | 18       | 2   | -16  | UNDER  |
| test2  | 28       | 2   | -26  | UNDER  |
| test3  | 23       | 2   | -21  | UNDER  |
| test4  | 23       | 1   | -22  | UNDER  |
| test5  | 25       | 3   | -22  | UNDER  |
| test6  | 21       | 5   | -16  | UNDER  |
| test7  | 30       | 21  | -9   | UNDER  |
| test8  | 23       | 4   | -19  | UNDER  |
| test9  | 6        | 2   | -4   | UNDER  |
| test10 | 12       | 8   | -4   | UNDER  |
| test11 | 7        | 6   | -1   | UNDER  |
| test12 | 10       | 9   | -1   | UNDER  |
| test14 | 8        | 2   | -6   | UNDER  |
| test15 | 50       | 5   | -45  | UNDER  |

**Accuracy: 0/15 (0.0%)**

## Analysis
- Every prediction is UNDER. The "pick candidate closest to median of non-zero candidates" heuristic is broken:
  the candidate set is dominated by low-threshold runs that merge most pills into 1–5 giant blobs.
  Median ends up being a tiny number, and the heuristic then selects exactly those merged-blob counts.
- The closest-to-real results (test7=21/30, test10=8/12, test11=6/7, test12=9/10) hint that *some* threshold/Canny pass
  did produce reasonable per-pill segmentation, but it was discarded by the selection heuristic.
- Touching pills are merged into single contours (classic single-threshold failure mode).
- test15 (50 pills) is catastrophic — small pills + lots of touching → only 5 blobs.

## Next Steps
1. Drop the "closest to median" selector — it systematically rewards undersegmentation.
   Better: pick **max non-zero candidate** within a sanity band (between 50% and 200% of mode), or use
   a per-image self-consistency metric (e.g., the count that maximizes circularity of resulting blobs).
2. Add watershed / distance-transform splitting to break touching-pill clusters.
3. Reconsider area bounds — `min_area = 0.05%` of image may be too small (lets noise speckles in) while
   `max_area = 15%` lets huge merged blobs through (a merged blob covering 15% of the image is counted as 1 pill).
4. Try `cv2.HoughCircles` as an independent signal — pills are roughly circular.
