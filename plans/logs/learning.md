# Learning Log

## Iteration 0 — Baseline (port of pill_counter.py)
- The "pick candidate closest to median of non-zero counts" selector is **biased toward undersegmentation**:
  low thresholds merge most pills into a handful of giant blobs, dragging the median down and causing the
  selector to pick exactly those merged counts. Result: 0/15, all UNDER.
- Single global thresholding cannot separate touching pills — segmentation alone is insufficient; need
  watershed / distance-transform / Hough-circle style splitting.
- Area filter bounds inherited from baseline (`0.05%` to `15%` of image) are too permissive:
  a single merged blob covering 15% of the frame is accepted as "one pill".
- Only test7, test10, test11, test12 produced near-correct candidates somewhere in the candidate set
  — meaning the *generation* step partially worked even when the *selection* step failed.

## Iteration 1 — Otsu + Distance Transform + Global Seed Threshold
- A **single principled pipeline** is easier to debug than a candidate-generation/selection ensemble (iter 0).
  Iter 1 went from 0/15 to 1/15 but every failure now has one identifiable cause.
- **Global thresholds calibrated to `dist.max()` are fragile**: one anomalously deep pill-cluster interior
  drives `dist.max()` high, and `0.5 * dist.max()` then exceeds the distance peak of every individual pill,
  collapsing the count. This is the *same class of bug* as iter 0's median-selector: any global statistic
  computed across the whole frame can be hijacked by one outlier region.
- **Touching pills require per-pill seeds, not a global cut**. Distance transform is the right tool; the
  selection step must be **local** (local maxima within a window ≈ pill radius), not global.
- Otsu + invert-if-bg-bright correctly separated fg/bg on every image (no Otsu failures observed).
  The bottleneck is *splitting clusters*, not *finding foreground*.

## Iteration 12 — SAM + Area-Cluster Filter
- **SAM over-segments but the right masks are there.** After area+shape filtering, the median mask
  area corresponds to pill size. Non-pill objects (tray edges, reflections) have very different areas.
- **Area-cluster filtering (median ± 40%) is a simple, effective filter.** Rejects outlier-area
  objects without any tuning. Went from 0/15 → 2/15 in one step.
- **No half-pill problem.** Diagnostic showed all mask areas cluster at full-pill size — the
  over-counting comes from non-pill objects with similar area, not from split pills.
- **Remaining over-counts (all +1 to +6) are non-pill objects with pill-like area.** These need
  a second discriminator — likely color, since all pills in an image share the same color.

## Iteration 13 — Color Cluster Filter
- **Color filtering adds 3 more exact matches** (test1, test4, test5 → but test5 regressed later).
  Combined area+color gets 5/15.
- **Adaptive threshold (median + 2.5σ, min 40) works better than fixed.** Too tight (1.5σ, min 25)
  over-filtered and lost test14. Too loose and it doesn't help.
- **Non-pill objects that pass both filters are color+area-similar to pills.** These are the hard
  cases — reflections, tray features that mimic pill appearance.
- **HSV might be better than RGB** for color comparison — more robust to brightness variation.
- **Loosened shape thresholds (circularity ≥ 0.3, solidity ≥ 0.6) vs prior (0.45, 0.7).** SAM
  masks are cleaner than OpenCV contours, so tighter thresholds would reject valid pills.

## Cross-cutting Patterns
- **Global statistics over the whole image are the recurring failure mode.** Both iter 0 (median of all
  candidate counts) and iter 1 (50% of global `dist.max()`) failed because a small anomalous region
  poisoned the global statistic. Future iterations should prefer **local / per-component** decisions.
- **Test0 is a "trivial" image** (24 well-separated similar objects on simple bg): any reasonable pipeline
  solves it. It's a smoke test, not a discriminator.
- **The hard images cluster around touching pills + size variation** (test2, test3, test4, test5, test6,
  test15). These will not be solved without an explicit cluster-splitting step.
