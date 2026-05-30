"""
Evaluation harness for pill counter.

FIXED CONTRACT — DO NOT MODIFY.

- Imports `count_pills(image_path: str) -> int` from counter.py
- Runs against hardcoded GROUND_TRUTH (from user_specs.md)
- Prints per-image results to stderr (human-readable)
- Prints JSON summary to stdout
- Exit code 0 iff 100% accuracy, 1 otherwise
"""
import json
import os
import sys
import traceback

from counter import count_pills

GROUND_TRUTH = {
    "test0": 24,
    "test1": 18,
    "test2": 28,
    "test3": 23,
    "test4": 23,
    "test5": 25,
    "test6": 21,
    "test7": 30,
    "test8": 23,
    "test9": 6,
    "test10": 12,
    "test11": 7,
    "test12": 10,
    "test14": 8,
    "test15": 50,
}


def main() -> int:
    img_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test-img")
    results = {}

    for name in sorted(GROUND_TRUTH.keys(), key=lambda k: int(k.replace("test", ""))):
        expected = GROUND_TRUTH[name]
        path = os.path.join(img_dir, f"{name}.jpg")
        if not os.path.exists(path):
            results[name] = {
                "count": -1,
                "expected": expected,
                "diff": 0,
                "match": False,
                "error": "file not found",
            }
            continue

        try:
            count = int(count_pills(path))
        except Exception as e:
            results[name] = {
                "count": -1,
                "expected": expected,
                "diff": 0,
                "match": False,
                "error": f"{type(e).__name__}: {e}",
                "traceback": traceback.format_exc(),
            }
            continue

        diff = count - expected
        results[name] = {
            "count": count,
            "expected": expected,
            "diff": diff,
            "match": count == expected,
        }

    total = len(GROUND_TRUTH)
    matches = sum(1 for r in results.values() if r.get("match"))
    accuracy_pct = round(matches / total * 100, 1)
    total_abs_diff = sum(abs(r.get("diff", 0)) for r in results.values())

    for name in sorted(results.keys(), key=lambda k: int(k.replace("test", ""))):
        r = results[name]
        if "error" in r:
            print(f"  {name}: ERROR expected={r['expected']} ({r['error']})", file=sys.stderr)
            continue
        if r["match"]:
            status = "OK"
        elif r["diff"] > 0:
            status = "OVER"
        else:
            status = "UNDER"
        print(
            f"  {name}: got={r['count']} expected={r['expected']} diff={r['diff']:+d} {status}",
            file=sys.stderr,
        )
    print(f"Accuracy: {matches}/{total} ({accuracy_pct}%)", file=sys.stderr)

    output = {
        "results": results,
        "summary": {
            "matches": matches,
            "total": total,
            "accuracy_pct": accuracy_pct,
            "total_abs_diff": total_abs_diff,
        },
    }
    print(json.dumps(output, indent=2))

    return 0 if matches == total else 1


if __name__ == "__main__":
    sys.exit(main())
