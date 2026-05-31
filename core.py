"""
Core image processing — counts pills in a single image.

This is the experiment zone. Swap implementations freely.
All other files consume output through the dict interface.
"""

import os


def process(image_path: str) -> dict:
    """
    Process a single image and return results.

    Args:
        image_path: path to one image file

    Returns:
        dict with:
          - "count": int (-1 on error)
          - "output_file": str (path to annotated output image)
    """
    if not os.path.exists(image_path):
        return {"count": -1, "output_file": "", "error": "file not found"}

    # Placeholder — returns 0 until SAM is integrated
    return {"count": 0, "output_file": ""}
