"""
Evaluate a single image result against ground truth.
Also handles printing eval results.

GROUND_TRUTH is hardcoded from user_specs.md.
This file is essentially fixed — do not modify.
"""

import sys

GROUND_TRUTH = {
    "test0": 24, "test1": 18, "test2": 28, "test3": 23,
    "test4": 23, "test5": 25, "test6": 21, "test7": 30,
    "test8": 23, "test9": 6, "test10": 12, "test11": 7,
    "test12": 10, "test13": 100, "test14": 8, "test15": 50,

    "test24": 75, "test25": 70, "test26": 259, "test27": 219,
    "test28": 179, "test29": 59, "test30": 102, "test31": 124,
    "test32": 125, "test33": 100,
}


def compare(image_name: str, result: dict) -> dict:
    """
    Evaluate one image result against ground truth.

    Args:
        image_name: e.g. "test0" (key into GROUND_TRUTH)
        result: dict from core.process(), must have "count" key

    Returns:
        dict with: image, count, expected, diff, match
    """
    expected = GROUND_TRUTH.get(image_name)
    if expected is None:
        return {
            "image": image_name,
            "count": result.get("count", -1),
            "expected": None,
            "diff": None,
            "match": False,
            "error": f"unknown image: {image_name}",
        }

    count = result.get("count", -1)
    diff = count - expected
    return {
        "image": image_name,
        "count": count,
        "expected": expected,
        "diff": diff,
        "match": count == expected,
    }


def evaluate(image_name: str, result: dict) -> dict:
    """
    Evaluate and print result. Returns data for report.
    
    Returns:
        dict with eval data to merge into report, or empty dict if no ground truth.
    """
    eval_result = compare(image_name, result)
    
    if "error" in eval_result:
        print(f"  {image_name}: got={result['count']}", file=sys.stderr)
        return {}
    
    status = "OK" if eval_result["match"] else f"diff={eval_result['diff']:+d}"
    print(f"  {image_name}: got={eval_result['count']} expected={eval_result['expected']} {status}", file=sys.stderr)
    
    return {
        "expected": eval_result["expected"],
        "diff": eval_result["diff"],
        "match": eval_result["match"],
    }
