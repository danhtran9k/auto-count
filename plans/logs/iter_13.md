# Iteration 13 — Color cluster filter (median + 2.5σ)

## Approach
Added color-based filtering after area-cluster filter:
1. Loose area + shape filter → candidates
2. Area cluster: median ± 40% → tighter candidates
3. **Color cluster**: compute mean RGB per mask, find median color, reject masks whose color distance > median + 2.5σ (min tolerance 40 in RGB Euclidean)

## Results
| Image  | Expected | Got  | Diff  |
|--------|----------|------|-------|
| test0  | 24       | 26   | +2    |
| test1  | 18       | 18   | OK    |
| test2  | 28       | 31   | +3    |
| test3  | 23       | 26   | +3    |
| test4  | 23       | 23   | OK    |
| test5  | 25       | 26   | +1    |
| test6  | 21       | 22   | +1    |
| test7  | 30       | 30   | OK    |
| test8  | 23       | 23   | OK    |
| test9  | 6        | 8    | +2    |
| test10 | 12       | 13   | +1    |
| test11 | 7        | 9    | +2    |
| test12 | 10       | 13   | +3    |
| test14 | 8        | 8    | OK    |
| test15 | 50       | 53   | +3    |

**Accuracy: 5/15 (33.3%)** — up from 2/15.

## Analysis
- 5 exact: test1, test4, test7, test8, test14
- 3 within +1: test5, test6, test10
- Color filter helped most where non-pill objects had different color from pills
- Remaining over-counts: non-pill objects that happen to be similar color AND area to pills
- test5 regressed from exact (iter 12) to +1 — color filter too aggressive on that image

## Next Steps
1. For +1 cases: these are single outlier masks — can we use a more nuanced filter?
2. Try: combine area + color into a single "pill-likeness" score and use a tighter percentile cutoff
3. Or: use color in HSV space instead of RGB (more robust to lighting)
