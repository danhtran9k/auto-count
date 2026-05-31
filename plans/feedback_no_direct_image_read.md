---
name: no-direct-image-read
description: Never read images directly with Read tool — write a read_info.py script to extract and return information instead
metadata:
  type: feedback
---

Never use the Read tool to directly view/read image files (PNG, JPG, etc.).

**Why:** Direct image reading is unreliable for this project's needs. A Python script provides consistent, programmatic access to image data.

**How to apply:** Whenever you need information from an image, write a `read_info.py` script that loads the image using OpenCV/PIL and returns the needed information (dimensions, pixel data, metadata, etc.). Run the script via Bash to get the output.
