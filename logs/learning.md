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

## Cross-cutting Patterns
- (none yet — only one iteration)
