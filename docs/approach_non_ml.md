# Non-ML Approaches for Pill Counting

## Problem Analysis

### Image Characteristics
- Photos include the entire medicine container with bright highlights
- Medicine placed in bags with paper labels (labels cause interference)
- Container edges, rims, glare/reflection on surfaces
- The main plane containing pills is simple, but surrounding interference is significant
- Pills are the dominant object type (100% guaranteed same type per image)

### Pill Forms
- Round pills
- Capsule-shaped (elongated)
- Oval pills
- Two-tone capsules (e.g., red/blue, red/yellow)
- Single-color pills

### Core Challenge
The problem is **not** finding foreground vs background. Otsu works fine for that.
The problem is **distinguishing pills from interference** (labels, glare, container edges, text) in the segmentation mask.

---

## Approach: LAB Color-Space Chroma Filtering

### Why LAB?

LAB separates lightness from color:
- **L channel** = brightness (like grayscale)
- **a channel** = green ↔ red
- **b channel** = blue ↔ yellow

### Key Insight

Pills have **saturated color**. Background elements (paper, containers, glare) are **achromatic** (gray/white).

| Element | Chroma (|a|+|b|) | Hue |
|---------|------------------|-----|
| Red/blue capsule | High | Red or blue |
| White pill | Low | — |
| Paper label | Very low | — |
| Gray container | Very low | — |
| Glare/reflection | Very low | — |

### How It Works

```python
lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB).astype(np.float32)
a = lab[:,:,1] - 128  # center around 0
b = lab[:,:,2] - 128
chroma = np.sqrt(a**2 + b**2)  # how "colorful" each pixel is
mask = (chroma > threshold).astype(np.uint8) * 255
```

- Catches red, blue, yellow, green pills — **any chromatic color**
- Rejects white paper, gray containers, glare (all achromatic)
- Works for two-tone capsules (both halves are chromatic)
- Single threshold to tune (chroma cutoff)

### Limitation
White/achromatic pills would be rejected. For those, fall back to brightness-based detection.

---

## Alternative Approaches Considered

### 1. Distance Transform + Watershed (current pipeline)
- Best at splitting touching pills
- Issue: noise peaks from textured foreground (labels, glare) dominate
- Could work if fed a **cleaner mask** from LAB chroma filtering

### 2. HoughCircles
- Directly detects circles — ignores labels, glare, texture
- Only works for round pills, fails on capsules/ovals
- Needs per-image tuning

### 3. Contour + Area Filtering
- Simple, fast
- Struggles with touching pills

### 4. scikit-image SLIC Superpixels
- Segment into uniform regions, then cluster pill regions
- More powerful segmentation primitives than raw OpenCV
- Still offline, no ML model

### 5. Template Matching
- Works if pills are very uniform
- Slow, sensitive to scale/rotation

---

## Recommended Strategy

**Primary: LAB chroma filter → existing distance transform pipeline**

1. Use LAB chroma to create a clean pill mask (rejects labels, glare, containers)
2. Feed clean mask into distance transform + watershed for splitting touching pills
3. Contour detection on the result for final count

**Fallback for white pills:** brightness-based thresholding on L channel

This directly attacks the root cause (interference in the mask) while keeping the proven cluster-splitting approach.
