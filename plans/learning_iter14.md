---
name: learning-iter14
description: Shape outlier filter breakthrough — aspect ratio + fill ratio strategy
metadata:
  type: project
---

## Iter 14: Shape Outlier Filter — 5/15 → 10/15

**Key insight:** After area cluster and color cluster filters, remaining overcount comes from non-pill objects that passed shape tests (circularity, solidity) but have abnormal bounding-box geometry.

**Two complementary metrics:**
1. **Aspect ratio** (`max(w,h) / min(w,h)`): Reject > 3.0 — catches elongated strips/rods (e.g. test6 idx 21 with aspect 4.53)
2. **Fill ratio** (`area / bbox_area`): Reject < 0.4 — catches oddly-shaped objects with low bbox occupancy (e.g. test9 idx 7 with fill 0.26)

**Why this works for rotated pills:**
- Diagonal pills typically have aspect ~1.5-2.5, fill ~0.6-0.8
- Thresholds are conservative enough to preserve them

**Why:** Absolute bbox dimensions (width/height) failed because pills rotate diagonally, creating varied bbox sizes. Aspect ratio and fill ratio are rotation-invariant.

**How to apply:** Any future filter refinement must NOT touch the 10 already-correct images. Test against all 15 after every change.

**Remaining failures (5/15 overcount):**
- test9: +1, test10: +1, test2: +1, test12: +2, test15: +2
