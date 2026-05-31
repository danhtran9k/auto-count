# Iteration 9 — Median CC area as single-pill unit

## Approach
Otsu → CCs with abs_floor=30. Use **median CC area** as unit; each CC contributes
`max(1, round(area/unit))` pills.

## Results
**Accuracy: 0/15** — test0=1, everyone else MASSIVELY over (1000–7000).

## Analysis — CRITICAL DIAGNOSTIC
Ran a diagnostic and discovered:

| Image  | Shape       | nCC | CC≥30 | top-areas (first few)                             |
|--------|-------------|-----|-------|---------------------------------------------------|
| test0  | 312x252     | 1   | 1     | [44421]                                           |
| test1  | 897x1000    | 22  | 15    | [423810, 14562, 802, 597, ...]                    |
| test2  | 1065x1300   | 1038| 216   | [301998, 12578, 11635, 10727, 6323, 5883, ...]    |
| test3  | 792x1000    | 12  | 4     | [422095, 191, 51, 47]                             |
| test5  | 1280x960    | 55  | 25    | [456050, 2629, 1175, ...]                         |
| test9  | 1280x960    | 55  | 26    | [321554, 155588, 75474, 26441, 20846, ...]        |
| test10 | 1280x960    | 69  | 35    | [245993, 154249, 21810, 15351, ...]               |
| test11 | 1280x960    | 314 | 69    | [330992, 10483, 10326, 10050, 9902, ...]          |
| test12 | 1280x960    | 111 | 70    | [813378, 17798, 2197, ...]                        |
| test15 | 1280x960    | 205 | 56    | [403553, 15939, 6032, 5775, 5774, 5716, ...]      |

**Every image has one MASSIVE merged CC** containing most/all pills. The median CC area is
either tiny (lots of noise speckles → median collapses) or huge (few CCs all huge → median useless).
Either way, the area-divide approach fails catastrophically.

The good news: in some images (test2, test11, test15) the smaller CCs that survive the 30-px floor
are actually pill-sized (5000–12000 px) and could anchor a unit estimate — but the giant CC poisons
the median.

## Key Reframe
The problem is NOT "count separated CCs". The problem is:
1. There's one huge merged-foreground CC containing N pills.
2. Possibly a few isolated pill CCs.
3. Need to **count pills within the merged CC**.

Distance-transform local-maxima detection inside the merged CC is the right tool — but window-size
selection has been the recurring blocker.

## Next Steps (iter 10) — back to distance transform, but smarter
1. Otsu + morph open. Don't worry about CCs being merged.
2. Compute global distance transform.
3. Sweep local-max **window size** from small to large.
4. For each window, count local-max peaks (with `dist > some_floor`).
5. The count curve will: start very high (every plateau pixel is a peak) → drop rapidly → **plateau
   at true count when window ≈ pill diameter** → drop to ~ #CCs as window grows past pill diameter.
6. Return the count from the longest plateau in this curve.
