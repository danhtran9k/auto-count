---
name: no-direct-image-read
description: Never read images directly with Read tool — use a Python script instead. Use when working with image files (PNG, JPG, etc.) to extract information programmatically.
---

# No Direct Image Read

**CRITICAL RULE**: Never use the Read tool to directly view/read image files (PNG, JPG, etc.).

## Why
Direct image reading causes the CLI to crash. A Python script provides a safe, programmatic way to access image data.

## How to Apply
Whenever you need information from an image:
1. Write a `read_info.py` script that loads the image using OpenCV/PIL
2. Return the needed information (dimensions, pixel data, metadata, etc.)
3. Run the script via Bash to get the output

## Example Script Template
```python
import cv2
import sys

def get_image_info(image_path):
    img = cv2.imread(image_path)
    if img is None:
        return f"Error: Could not read image at {image_path}"
    
    height, width, channels = img.shape
    return {
        "path": image_path,
        "width": width,
        "height": height,
        "channels": channels,
        "size_bytes": img.nbytes
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python read_info.py <image_path>")
        sys.exit(1)
    
    result = get_image_info(sys.argv[1])
    print(result)
```

## When to Use
- When you need to check if an image exists
- When you need image dimensions or metadata
- When you need to analyze pixel data
- When you need to process images for any reason

**Always write a script instead of using the Read tool on image files.**