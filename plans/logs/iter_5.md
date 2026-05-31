# Iteration 5 — Erosion sweep + mode of counts

## Approach
Same erosion sweep as iter 4 but: dropped `MORPH_CLOSE`, lowered `min_blob_area` to 5,
and returned the **mode** of the per-step CC counts (filtered to values ≥ peak/2)
instead of the max.

## Results
**Accuracy: 1/15 (6.7%)** — test0 only. All other images severely OVER (test2=1035, test11=312).

## Analysis
- test0=24 OK: dropping close + tiny min_area fixed the iter 4 test0 collapse.
- Everything else exploded: with `min_blob_area=5` and long sweep, the **shatter phase**
  produces hundreds of tiny fragments that persist for many erosion steps. The mode
  ends up picking a value from the shatter regime, not the true plateau.
- Mode is not robust here because shatter lasts *longer* than the true plateau when
  pill sizes vary.

## Next Steps (iter 6)
- Use iter 4's settings (min_blob_area=20, light open+close) but **select the first
  plateau** in the count curve instead of `max`. First plateau (≥K consecutive equal
  values) marks "all clusters split, no shatter yet".
- For test0 (24 separate objects), use `counts[0]` if it's > 0 — the pre-erosion CC count
  is already correct when objects are pre-separated.
