# Project Memory

## Core Rules

### Prefer `uv` over `python3`
- Always try `uv` first when running Python scripts or commands
- Only fall back to `python3` if `uv` is unavailable or fails

### No Direct Image Read
- **File**: `plans/feedback_no_direct_image_read.md`
- **Skill**: `.opencode/skills/no-direct-image-read/SKILL.md`
- **Rule**: Never use the Read tool to directly view/read image files (PNG, JPG, etc.)
- **Why**: Direct image reading causes the CLI to crash
- **How**: Write a `read_info.py` script that loads the image using OpenCV/PIL and returns needed information (dimensions, pixel data, metadata, etc.). Run the script via Bash to get the output.