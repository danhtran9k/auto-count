# Iteration 12 — Area-cluster filter (median ± 40%)

## Approach
Replace fixed area bounds with adaptive cluster filtering:
1. Loose area filter (0.1%–10% of image) to get candidates
2. Shape filter: circularity ≥ 0.3, solidity ≥ 0.6
3. **Area cluster**: compute median area of candidates, keep only masks within ±40% of median

Key insight: all pills in an image are same type, so they share similar area. Non-pill objects (tray edges, reflections) have very different area and get rejected by the cluster filter.

## Results
| Image  | Expected | Got  | Diff  |
|--------|----------|------|-------|
| test0  | 24       | 26   | +2    |
| test1  | 18       | 19   | +1    |
| test2  | 28       | 32   | +4    |
| test3  | 23       | 29   | +6    |
| test4  | 23       | 25   | +2    |
| test5  | 25       | 26   | +1    |
| test6  | 21       | 24   | +3    |
| test7  | 30       | 30   | OK    |
| test8  | 23       | 24   | +1    |
| test9  | 6        | 9    | +3    |
| test10 | 12       | 15   | +3    |
| test11 | 7        | 9    | +2    |
| test12 | 10       | 14   | +4    |
| test14 | 8        | 8    | OK    |
| test15 | 50       | 55   | +5    |

**Accuracy: 2/15 (13.3%)** — up from 0/15.

## Analysis
- test7, test14: exact match — area cluster perfectly isolates pills
- Close images (±1): test1, test5, test8 — just one extra non-pill mask
- Worst: test3 (+6), test15 (+5), test2/test12 (+4)
- All still OVER — remaining non-pill objects have similar area to pills (e.g., reflections, tray features)
- No half-pill problem detected — user's area analysis confirmed masks cluster at full-pill size

## Next Steps
1. Tighten cluster range: ±30% instead of ±40% — reject more outliers
2. Try color-based filtering: since pills share color, reject masks with outlier mean color
3. Consider: for the +1 cases, the extra mask is likely one non-pill object — can we use color to reject it?
