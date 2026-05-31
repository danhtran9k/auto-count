# Iteration 11 — Distance-transform sweep + area-sanity gating

## Approach
Same as iter 10 but filter `(window, count)` tallies by
`c * π * (w/2)² ∈ [0.35, 1.6] * fg_area` before plateau detection.
Fallback: pick the valid entry whose coverage ratio is closest to 1.0.

## Results
| Image  | Expected | Got  | Diff  | Note            |
|--------|----------|------|-------|-----------------|
| test0  | 24       | 24   | +0    | OK              |
| test1  | 18       | 19   | +1    | close           |
| test2  | 28       | 3048 | +3020 | noise peaks pass sanity |
| test3  | 23       | 17   | -6    | close-ish       |
| test4  | 23       | 8    | -15   |                 |
| test5  | 25       | 50   | +25   | ~2x             |
| test6  | 21       | 25   | +4    | close           |
| test7  | 30       | 21   | -9    |                 |
| test8  | 23       | 0    | -23   | window cap blocked |
| test9  | 6        | 10   | +4    | close           |
| test10 | 12       | 100  | +88   |                 |
| test11 | 7        | 159  | +152  |                 |
| test12 | 10       | 20   | +10   | ~2x             |
| test14 | 8        | 0    | -8    | window cap blocked |
| test15 | 50       | 165  | +115  |                 |

**Accuracy: 1/15** but **many within ±10**: test0, test1, test3, test6, test9, test12.

## Analysis
- test8 / test14 returned 0: window cap `min(short/4, 201)` = 201, but expected pill diameter
  for these images (`fg/N` math) is ~300px → no window covers the right scale.
- test2 = 3048: dist transform of a noisy / textured Otsu mask has thousands of micro-peaks
  that survive the area sanity for some `(w, c)` combos.
- Several images are 2x expected (test5=50/25, test12=20/10) — suggests Otsu mask is fragmenting
  pills into two parts each, OR each pill has two local-max plateaus (e.g., glare splits into
  bright crescent).

## Next Steps (iter 12)
1. **Relax window cap to `min(short/2, 401)`** — fixes test8 / test14.
2. **Stronger pre-smoothing**: morph close after open (kernel 5×5, 2 iter) to fill internal
   pill holes and merge near-touching glare blobs. Reduces noise peaks.
3. Tighten area sanity: `[0.45, 1.4]` to reduce noise-peak admission.
4. Robust fallback when no plateau survives: pick valid entry whose count×r² is **median across
   valid entries**, not just closest to 1.0.
