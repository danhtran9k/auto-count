# Plan: Improve SAM Pipeline — Speed + Over-segmentation + Filter Tuning

## Context

SAM pipeline đang có 3 vấn đề chính:
1. **Chậm** — `SamAutomaticMaskGenerator` default `points_per_side=32` (~1024 prompts)
2. **Over-segmentation** — Bicolor pill / pill có gân giữa → SAM detect ra 2 nửa riêng biệt
3. **Filter chain quá aggressive** — undercount một số trường hợp, IoU dedup drop mask thật

Mục tiêu: giữ 15/15 accuracy hiện tại, đồng thời fix các case mới (bicolor pill, undercount).

---

## Change 1: SAM Speed Optimization

**File:** `core.py` — `_get_mask_generator()`

**Problem:** Default `points_per_side=32` tạo ~1024 point prompts → chậm.

**Solution:** Tune params khi tạo `SamAutomaticMaskGenerator`:

```python
_mask_generator = SamAutomaticMaskGenerator(
    _sam_model,
    points_per_side=16,          # 32→16: ~4x nhanh hơn
    pred_iou_thresh=0.86,        # default 0.88, giảm nhẹ
    min_mask_region_area=100,    # bỏ mask quá nhỏ sớm
    crop_n_layers=0,             # tắt crop-based refinement
)
```

**Why these values:**
- `points_per_side=16` → 256 prompts (vs 1024). Pills là object lớn, không cần dense grid
- `crop_n_layers=0` → tắt multi-crop refinement, tiết kiệm nhiều thời gian nhất
- `pred_iou_thresh=0.86` → giữ mask quality tốt nhưng không quá strict
- `min_mask_region_area=100` → filter noise sớm trong SAM

**Risk:** Có thể miss pill rất nhỏ. Test lại 15/15 sau khi đổi.

---

## Change 2: Half-pill Merging (NEW step)

**File:** `core.py` — thêm function `_merge_half_pills()`, gọi TRƯỚC Step 1

**Problem:** Bicolor pill / pill có gân giữa → SAM tạo 2 mask cho 1 viên. 2 mask này:
- Gần nhau (touching hoặc gap nhỏ)
- Có area tương đương nhau
- Có thể khác màu (2 màu) nhưng cùng 1 viên

**Solution:** Merge adjacent mask pairs dựa trên 3 điều kiện:

```
Điều kiện merge:
1. Spatial proximity: dilate mask A (gap pixels), chạm mask B
2. Similar area: ratio trong khoảng [0.5, 2.0]
3. Similar color: Euclidean distance mean RGB < 40
```

**Algorithm:**
```
for each mask i (chưa merged):
    for each mask j > i (chưa merged):
        nếu đủ 3 điều kiện → merge i+j thành mask mới
        dùng union segmentation, sum area
```

**Thứ tự gọi:** Ngay sau `generator.generate()`, trước Step 1.

**Risk:** Merge nhầm 2 pill thật sự cạnh nhau. Mitigation: điều kiện color + area ratio đủ strict để tránh false merge. Với constraint "tất cả viên cùng 1 loại", 2 pill cạnh nhau sẽ có màu giống nhau → rely vào spatial proximity + area.

---

## Change 3: Relax Shape Outlier Filter (Step 4)

**File:** `core.py` — Step 4 trong `process()`

**Problem:** Thresholds quá strict → drop pill thật (pill hình oval, pill nén):

| Param | Hiện tại | Đề xuất | Lý do |
|-------|----------|---------|-------|
| `aspect` | > 3.0 | > 3.0 | Giữ nguyên — pill nén hiếm khi > 3x |
| `fill` | < 0.45 | < 0.35 | Pill oval có fill thấp hơn |
| `circ` | < 0.55 | < 0.40 | Pill nén có circularity thấp |
| `area_ratio` | < 0.80 | < 0.65 | Pill cùng loại có size variance |

**Risk:** Giảm strictness → có thể giữ lại mask rác. Bù bằng color filter (Step 3) đã rất tốt.

---

## Change 4: Relax Dedup (Step 5)

**File:** `core.py` — Step 5 trong `process()`

**Problem:** IoU > 0.5 → drop mask. Threshold này quá thấp, có thể drop mask thật khi 2 pill touching.

**Solution:** Tăng IoU threshold `0.5 → 0.7`

**Lý do:**
- 2 pill touching nhau có thể overlap 30-50% (do SAM mask boundary mềm)
- Chỉ merge khi IoU > 0.7 (thực sự là duplicate, không phải touching)
- Giữ lại mask có area lớn hơn khi drop

**Risk:** Có thể giữ lại duplicate mask thật. Bù bằng color + shape filter đã lọc.

---

## Implementation Order

```
1. Change 1: SAM speed params        → test 15/15
2. Change 3: Relax shape filter       → test 15/15
3. Change 4: Relax dedup              → test 15/15
4. Change 2: Half-pill merge          → test 15/15 + test bicolor cases
```

Làm từng bước, verify accuracy sau mỗi bước. Nếu step nào gây regression → revert riêng step đó.

---

## Files to Modify

| File | Thay đổi |
|------|----------|
| `core.py` | Tất cả 4 changes |

Không file nào khác cần sửa.

---

## Verification

- Chạy `main.py test-img` → kiểm tra report.json, phải 15/15
- Nếu có test-img bicolor riêng → verify count đúng
- So sánh thời gian chạy trước/sau (Change 1)
