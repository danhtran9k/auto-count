# Pill Counter Autoresearch Design

## Overview

Apply the autoresearch iterative improvement pattern to the pill counting problem using pure OpenCV. The agent modifies the counting algorithm between iterations, evaluates against ground truth, logs learnings, and repeats until 100% accuracy.

## File Structure

```
gs-count/
├── counter.py          # COUNTING LOGIC — agent rewrites freely
├── eval.py             # EVALUATION HARNESS — fixed, never modified
├── test-img/           # test images (existing)
├── logs/
│   ├── iter_1.md       # iteration log
│   ├── iter_N.md
│   └── learning.md     # cumulative cross-iteration insights
└── user_specs.md       # ground truth (existing)
```

## Interfaces

### counter.py

```python
def count_pills(image_path: str) -> int:
    """Returns the count of pills in the image. -1 on error."""
```

This is the stable contract. Internals can change completely between iterations.

### eval.py (fixed, never modified)

Behavior:
1. Reads hardcoded GROUND_TRUTH dict from user_specs.md (15 images)
2. Calls `count_pills(path)` for each test image
3. Outputs per-image results to stderr (human-readable table)
4. Outputs JSON to stdout: `{results, summary: {matches, total, accuracy_pct}}`
5. Exit code 0 if 100% accuracy, 1 otherwise

## Iteration Log Format

### logs/iter_N.md

```markdown
# Iteration N — <short title>

## Approach
What changed from previous iteration.

## Results
| Image | Expected | Got | Diff | Status |
|-------|----------|-----|------|--------|

**Accuracy: X/15 (Y%)**

## Analysis
Which images failed, hypothesized reasons, what worked.

## Next Steps
What to try next.
```

### logs/learning.md (cumulative)

```markdown
# Learning Log

## Iteration 1 — <title>
- [insight]

## Iteration 2 — <title>
- [new insight, referencing/comparing with previous iterations]

## Cross-cutting Patterns
- [patterns observed across multiple iterations]
```

Each new iteration section explicitly references and compares with previous findings.

## Autoresearch Loop

```
1. Read current counter.py + eval output
2. Analyze failures (which images, why)
3. Rewrite counter.py with new approach
4. Run: python eval.py
5. Write logs/iter_N.md
6. Update logs/learning.md
7. Git commit: "iter N: <summary>"
8. If accuracy < 100% → go to 1
   If accuracy == 100% → DONE
```

### Constraints

- Agent does NOT read images directly — all image info comes from eval.py output
- Each iteration is a single commit with log files
- Agent has full rewrite freedom on counter.py
- eval.py is written once and never modified
- Target: 15/15 exact matches on ground truth

### Strategy Progression (adaptive)

1. Baseline: existing multi-threshold + Canny consensus
2. Analyze failures per image
3. Targeted fixes: preprocessing, segmentation, morphological ops
4. If stuck: fundamentally different approaches (watershed, distance transform, blob detection)
5. Image-specific logic if needed

## Ground Truth (from user_specs.md)

| Image  | Expected |
|--------|----------|
| test0  | 24       |
| test1  | 18       |
| test2  | 28       |
| test3  | 23       |
| test4  | 23       |
| test5  | 25       |
| test6  | 21       |
| test7  | 30       |
| test8  | 23       |
| test9  | 6        |
| test10 | 12       |
| test11 | 7        |
| test12 | 10       |
| test14 | 8        |
| test15 | 50       |
