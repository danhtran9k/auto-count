# Pill Counter

Count pills in images using SAM (Segment Anything Model).

## Setup

### Download SAM checkpoint (~375MB)

```bash
curl -L -o sam_vit_b.pth https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth
```

### Install dependencies

Requires [uv](https://docs.astral.sh/uv/) (preferred) or Python 3.8+ with pip.

**uv (preferred)**

```bash
uv sync
```

**pip (fallback)**

```bash
python -m venv .venv

# Linux / macOS
source .venv/bin/activate

# Windows (cmd)
.venv\Scripts\activate.bat

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

pip install .
```

## Usage

```bash
# Run on a folder of images (defaults to test-img/)
uv run run.py test-img/

# Using pip
python run.py test-img/
```

Results are printed per-image. All outputs (annotated images + `report.json`) are saved to `output/<timestamp>/`, where `<timestamp>` is `YY-MM-DD-HH-MM` (e.g. `output/26-05-31-14-30/`).

## Project Structure

| File | Role |
|------|------|
| `core.py` | SAM-based image processing and pill counting |
| `eval.py` | Ground truth comparison (hardcoded expected counts) |
| `report.py` | Accumulate results, write JSON report |
| `run.py` | Orchestrator — pipes images through the pipeline |
