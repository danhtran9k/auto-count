# Iteration 4 — Erosion sweep + max CC count

## Approach
Otsu → light morph clean → iteratively erode the mask, counting valid CCs
(area >= 20 px) at each step. Return `max(counts)` across the sweep.

Rationale: as erosion progresses, thin bridges between touching pills break first,
splitting clusters into individual CCs. At some erosion depth every cluster is
split before any pill has fully disappeared, and CC count peaks at the true count.

## Results
| Image  | Expected | Got | Diff  | Status |
|--------|----------|-----|-------|--------|
| test0  | 24       | 1   | -23   | UNDER  |
| test1  | 18       | 16  | -2    | UNDER  |
| test2  | 28       | 279 | +251  | OVER   |
| test3  | 23       | 9   | -14   | UNDER  |
| test4  | 23       | 7   | -16   | UNDER  |
| test5  | 25       | 25  | +0    | OK     |
| test6  | 21       | 38  | +17   | OVER   |
| test7  | 30       | 19  | -11   | UNDER  |
| test8  | 23       | 18  | -5    | UNDER  |
| test9  | 6        | 28  | +22   | OVER   |
| test10 | 12       | 40  | +28   | OVER   |
| test11 | 7        | 105 | +98   | OVER   |
| test12 | 10       | 77  | +67   | OVER   |
| test14 | 8        | 8   | +0    | OK     |
| test15 | 50       | 62  | +12   | OVER   |

**Accuracy: 2/15 (13.3%)** — best so far. test5 and test14 exact; test1=16/18 and test8=18/23 close.

## Analysis
- **Erosion-sweep concept works**: where it scores or comes close (test1, test5, test8, test14, test15),
  the peak count tracks the true count reasonably well — confirming that clusters do get split.
- **`max(counts)` is too greedy**: as erosion deepens, individual pills shrink and eventually shatter
  into 2+ tiny fragments before fully disappearing. The "shatter" phase produces a count spike well
  above the true count. This is the main OVER failure (test2=279, test11=105, test12=77).
- **test0 = 1** is a different failure: the 24 small objects on test0 are so small that after even 1
  erosion they all collapse below the 20-px area floor. The `max(counts)` includes step 0 (pre-erosion),
  which apparently is 1 CC — meaning Otsu followed by morph open+close merged all 24 objects into one
  blob (probably small + close to each other → close operation bridged them).
- The selection problem is the same as iter 1's: a global statistic (`max`) over the sweep is
  poisoned by the shatter spike.

## Next Steps (iter 5)
1. **Use the mode (most frequent value) of `counts`** during the sweep instead of `max`. The mode is
   the count value that persists across the largest number of erosion steps — i.e., the value held
   during the "all clusters split, no pills shattered yet" plateau.
2. Drop the initial `cv2.MORPH_CLOSE` to avoid bridging close-but-separate small objects (test0 fix).
3. Lower `min_blob_area` to absolute 5 px so tiny remnants of small pills aren't lost during the sweep.
4. Sweep range needs to cover enough erosion depth for the biggest cluster — keep `max_iter` adaptive.
