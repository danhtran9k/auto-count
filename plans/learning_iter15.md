---
name: learning-iter15
description: Gap-based color filter achieves 15/15 (100%) accuracy
metadata:
  type: project
---

## Iter 15: Gap-Based Color Filter — 14/15 → 15/15

**Key insight:** The previous color cluster filter used `median + 2.5*std` as threshold. This gets inflated when outliers themselves contribute to high std, letting color outliers through (e.g., test12 idx=12 with color_dist=112.3, threshold=125.8).

**Solution: Gap-based threshold detection.**
- Sort all color distances
- Find the biggest ratio gap between consecutive sorted values: `gap / dist[i]`
- If the max ratio > 2.0 and the distance > 15, use the gap midpoint as threshold
- Otherwise fall back to the original `median + 2.5*std` method

**Why this works:**
- Pills form a tight color cluster (distances 0-17), outliers jump to 100+
- The ratio-based gap detection is self-calibrating — no fixed multiplier to tune
- test12: sorted dists = [...17.5, 112.3, 162.2], gap ratio at 17.5→112.3 is huge → threshold ~65, catches idx=12
- All other images: no significant gap → falls back to original method unchanged

**Why:** The std-based threshold is sensitive to outlier contamination. Gap detection finds the natural cluster boundary.

**How to apply:** Any future color filter change must preserve 15/15. The gap method is strictly better than fixed-multiplier std.
