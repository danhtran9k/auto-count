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

## Cross-cutting Patterns
- **Global statistics over the whole image are the recurring failure mode.** Both iter 0 (median of all
  candidate counts) and iter 1 (50% of global `dist.max()`) failed because a small anomalous region
  poisoned the global statistic. Future iterations should prefer **local / per-component** decisions.
- **Test0 is a "trivial" image** (24 well-separated similar objects on simple bg): any reasonable pipeline
  solves it. It's a smoke test, not a discriminator.
- **The hard images cluster around touching pills + size variation** (test2, test3, test4, test5, test6,
  test15). These will not be solved without an explicit cluster-splitting step.
