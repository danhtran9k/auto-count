"""
Accumulate results and write report.json.
Generic reporting — no eval knowledge.
"""

import json
import sys


def create_empty_report() -> dict:
    """Create empty report structure."""
    return {"results": {}, "summary": {}}


def add_image_result(report: dict, image_name: str, count: int) -> dict:
    """Append one result to the report. Returns updated report."""
    report["results"][image_name] = {"image": image_name, "count": count}
    return report


def summary(report: dict) -> dict:
    """Compute summary stats from all results."""
    results = report["results"]
    total = len(results)
    # Accuracy only available when eval data (expected/match) is present
    eval_results = [r for r in results.values() if "expected" in r]
    if eval_results:
        matches = sum(1 for r in eval_results if r.get("match"))
        accuracy_pct = round(matches / len(eval_results) * 100, 1)
    else:
        matches = 0
        accuracy_pct = 0.0
    return {
        "total": total,
        "matches": matches,
        "accuracy_pct": accuracy_pct,
    }


def save_and_log(report: dict, path: str = "report.json"):
    """Write final report to JSON file and print summary."""
    report["summary"] = summary(report)
    with open(path, "w") as f:
        json.dump(report, f, indent=2)

    s = report["summary"]
    if s["accuracy_pct"] > 0:
        print(f"\nAccuracy: {s['matches']}/{s['total']} ({s['accuracy_pct']}%)", file=sys.stderr)
    print(f"Total {s['total']} annotations saved to {path}", file=sys.stderr)
