# Iteration 10 — Distance transform + local-max window sweep + plateau

## Approach
Global Otsu mask → distance transform → for each window `w ∈ geomspace(3, min(short/4, 201), 24)`,
compute local maxima (`dist == cv2.dilate(dist, w×w)` on FG, `dist > 1`) and count peak CCs.
Return the count from the longest plateau in the curve.

## Results
| Image  | Expected | Got  | Status |
|--------|----------|------|--------|
| test0  | 24       | 24   | OK     |
| test1  | 18       | 19   | +1     |
| test2  | 28       | 6404 | OVER   |
| test3  | 23       | 17   | -6     |
| test4  | 23       | 8    | -15    |
| test5  | 25       | 843  | OVER   |
| test6  | 21       | 721  | OVER   |
| test7  | 30       | 1286 | OVER   |
| test8  | 23       | 8    | -15    |
| test9  | 6        | 1915 | OVER   |
| test10 | 12       | 1203 | OVER   |
| test11 | 7        | 1901 | OVER   |
| test12 | 10       | 1657 | OVER   |
| test14 | 8        | 6    | -2     |
| test15 | 50       | 1662 | OVER   |

**Accuracy: 1/15 (6.7%)** but **test1, test3, test14 within ±6** — signal is real.

## Analysis
- The correct plateau exists in many images (test0 hit perfectly; test1=19 is essentially right).
- The OVER cases pick a plateau at **small windows** where the count is dominated by noise peaks
  in textured foreground regions (glare, reflections, paper grain). These plateaus are LONG (count
  stays high & roughly stable across many small windows) and beat the real peak plateau.
- The UNDER cases (test4, test8) have plateaus picked at too-large windows.

## Next Steps (iter 11)
- Add an **area-sanity filter** before plateau selection:
  for each `(window w, count c)`, require `c * π * (w/2)² ∈ [0.3, 1.6] * fg_area`.
  This drops the small-window/many-noise-peaks regime (where `c * π * (w/2)²` is tiny relative
  to fg_area) and the large-window regime (count too small for fg).
- Among surviving plateaus, pick the longest.
- This combines the distance-transform window sweep with the foreground-area sanity check that
  iter 7 introduced (but applied at plateau level, not single-pass).
