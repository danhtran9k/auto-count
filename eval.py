"""
Evaluate a single image result against ground truth.

GROUND_TRUTH is hardcoded from user_specs.md.
This file is essentially fixed — do not modify.
"""

GROUND_TRUTH = {
    "test0": 24, "test1": 18, "test2": 28, "test3": 23,
    "test4": 23, "test5": 25, "test6": 21, "test7": 30,
    "test8": 23, "test9": 6, "test10": 12, "test11": 7,
    "test12": 10, "test14": 8, "test15": 50,
}


def evaluate(image_name: str, result: dict) -> dict:
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
