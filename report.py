"""
Accumulate evaluation results and write report.json.
"""

import json


def create() -> dict:
    """Create empty report structure."""
    return {"results": {}, "summary": {}}


def add(report: dict, eval_result: dict) -> dict:
    """Append one eval result to the report. Returns updated report."""
    image_name = eval_result["image"]
    report["results"][image_name] = eval_result
    return report


def summary(report: dict) -> dict:
    """Compute summary stats from all results."""
    results = report["results"]
    total = len(results)
    matches = sum(1 for r in results.values() if r.get("match"))
    accuracy_pct = round(matches / total * 100, 1) if total > 0 else 0.0
    return {
        "matches": matches,
        "total": total,
        "accuracy_pct": accuracy_pct,
    }


def save(report: dict, path: str = "report.json"):
    """Write final report to JSON file."""
    report["summary"] = summary(report)
    with open(path, "w") as f:
        json.dump(report, f, indent=2)
