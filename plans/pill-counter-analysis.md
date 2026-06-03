# Pill Counter App - Analysis

## Problem Statement

Đếm chính xác số lượng viên thuốc trong hình ảnh (counting maximum overlapping objects). App độc lập, không liên quan project hiện tại.

## Constraints

| Yếu tố | Chi tiết |
|---------|----------|
| **Loại thuốc** | Unknown trước - bất kỳ shape/color nào (normal pill shapes, không exotic như ngôi sao) |
| **1 loại thuốc/ảnh** | **TẤT CẢ viên trong 1 ảnh LUÔN cùng 1 loại** (kể cả 100-500 viên) |
| **Loại thuốc thay đổi** | Mỗi lần chụp có thể là LOẠI KHÁC, mỗi user quan tâm các loại RIÊNG BIỆT |
| **1 or 2 color pill** | Có thể |
| **Background** | Đơn giản (user control), có thể trong bịch đựng thuốc |
| **Lighting** | Amateur camera - shadow, hand shadow, reflection nhẹ ở biên khay |
| **Góc chụp** | Nghiêng, không lab-standard |
| **Overlap** | **100% KHÔNG overlap đè lớp** - chỉ touching, luôn trên cùng mặt phẳng |
| **Số lượng** | 100-500 viên |
| **Bag label** | Có thể có label giấy dán trên bịch → ignore, không phải dominant object |

## Accuracy & Performance Requirements

- Accuracy: **rất cao**, lệch ±1 đã là xấu
- Sẵn sàng tune thêm image processing nhưng không nên tăng thời gian quá nhiều
- Target: **<5s/ảnh** (ideal), **<60s/ảnh** (worst case)
- User **không muốn annotate data**
- User **không prefer few-shot** (xem như last resort, chỉ khi primary fail hoàn toàn)

## Approach Evaluation

### ❌ Loại bỏ

| Approach | Lý do loại bỏ |
|----------|--------------|
| **OpenCV thuần (contour only)** | Không generalize được với unknown pill types across images, nhưng CÓ THỂ work tốt trong 1 ảnh (cùng loại) nhờ size consistency |
| **Color-based segmentation** | Thuốc 1/2 màu không predict được |
| **Multimodal LLM (GPT-4V, Gemini Vision)** | Không chính xác cho counting task, tốn API, chậm |
| **HoughCircles** | Chỉ work với hình tròn, thuốc có thể oval/viên nén |

### ✅ Khả thi

| Approach | Ưu điểm | Nhược điểm |
|----------|---------|------------|
| **SAM2 + Watershed** | Zero-shot, không cần train, robust với lighting | Cần GPU, model lớn |
| **YOLOv8 Instance Segmentation** | Chính xác cao, handle tốt | Cần annotated data |
| **OpenCV Advanced (CLAHE + Watershed + contour refinement)** | Nhẹ, nhanh, offline. Với "1 loại/ảnh" → dùng size consistency làm prior → CÓ THỂ là primary nếu tune tốt | Cần tune kỹ, nhạy lighting hơn SAM2 |

**Với constraint "1 loại/ảnh" + "loại thuốc thay đổi":**
- OpenCV approach **trở nên khả thi hơn** vì dùng size/shape consistency làm strong prior trong 1 ảnh
- SAM2 + Watershed **vẫn là primary** vì robust hơn với lighting/shadow và generalize across unknown pill types
- YOLO **vẫn không cần** vì không có occlusion phức tạp

## Recommended Pipeline

### Phase 1 - POC (Python, local PC)

```
Ảnh input
  ↓
Preprocessing (CLAHE, denoise, edge enhance)
  ↓
SAM2 zero-shot segmentation → mask tổng tất cả viên thuốc
  ↓
Watershed algorithm → tách các viên touching
  ↓
Contour counting + filtering → đếm chính xác
  ↓
Output: số lượng viên
```

**Lý do chọn SAM2 + Watershed:**
- SAM2 zero-shot → không cần annotate data
- Watershed chuyên tách object touching nhau (perfect fit vì thuốc chỉ touching, không stacking)
- Không cần YOLO (vì không có occlusion phức tạp)
- Processing time ước tính: ~2-4s trên PC có GPU

### Phase 2 - Mobile Deployment

| Option | Mô tả | Khi nào dùng |
|--------|-------|---------------|
| **A** | Convert SAM2 → ONNX → mobile | Nếu cần giữ accuracy cao nhất |
| **B** | Dùng OpenCV pipeline thuần (nhẹ) | Nếu POC confirm accuracy OK với OpenCV alone |
| **C** | Fine-tune YOLOv8-nano | Nếu cần balance accuracy + speed |

**Lưu ý POC vs Mobile:**
- Model chạy trên mobile đều chạy được trên PC, ngược lại không phải
- POC nên dùng model tốt nhất trước, rồi optimize cho mobile sau
- Mobile cần convert sang TFLite/Core ML/ONNX, giảm model size
- Mobile GPU hạn chế, latency target <5s khó hơn PC nhiều

## Tác động của constraint "1 loại thuốc/ảnh" + "loại thuốc thay đổi"

### Trong 1 ảnh (cùng loại)
- **Watershed separation dễ hơn**: Biết trước kích thước viên → tách touching chính xác hơn
- **Validation**: Detected pills phải có kích thước tương đồng → filter false positive
- **Template matching khả thi hơn**: Chỉ cần 1 reference image (không phải per type)
- **OpenCV approach có thể work tốt hơn**: Dùng size/shape consistency làm strong prior

### Across images/users (khác loại)
- Phải handle **unknown pill types** → zero-shot vẫn cần
- Mỗi user có bộ thuốc riêng → không thể dùng chung model trained trên fixed dataset

### Ảnh hưởng đến pipeline
```
SAM2 segmentation → mask tổng
  ↓
Watershed tách touching (dùng expected size từ detected pills lớn nhất)
  ↓
Validate: tất cả detected pill phải có kích thước ±20% của median
  ↓
Filter outlier → đếm chính xác
```

## Few-shot Analysis

### Few-shot là gì?
User chụp riêng lẻ 1 viên mẫu của MỖI loại thuốc họ quan tâm → app dùng làm reference template để matching.

### Few-shot trong context này:
- Mỗi user chỉ cần capture reference cho **RIÊNG loại thuốc của họ** (1 ảnh/loại)
- App matching viên mẫu với ảnh thực tế
- **Không phải annotate data** → chỉ cần chụp 1 viên mẫu

### Đánh giá

| Aspect | Đánh giá |
|--------|----------|
| **Đơn giản hóa** | Chỉ cần 1 ảnh reference/loại → dễ cho user |
| **Accuracy cải thiện** | Có, vì reference chính xác cho loại thuốc cụ thể |
| **Giải quyết bài toán gốc?** | ❌ KHÔNG - vẫn cần pipeline tách touching |
| **Giảm dev effort?** | ❌ KHÔNG -反而 tăng (thêm reference management + matching logic) |
| **Khi nào xem xét** | Chỉ khi primary approach (SAM2 + Watershed) fail hoàn toàn |

### Kết luận
- Few-shot **đáng xem xét hơn** so với trước (chỉ cần 1 ảnh/loại, không phải annotate)
- Nhưng vẫn **không phải silver bullet** - core problem (tách touching) vẫn cần giải quyết
- **Primary approach**: Zero-shot (SAM2 + Watershed) → work với bất kỳ loại thuốc nào ngay
- **Few-shot**: Có thể làm **enhancement** (không phải requirement), xem như "option dev đã bế tắc" - cần user hint, đổi lại rất lớn mới xem xét

## Technical Notes

- Platform preference: Cross-platform, nhưng POC trên local PC trước
- POC dùng Python + OpenCV + SAM2
- Cần NVIDIA GPU cho SAM2 (hoặc fallback sang approach khác)
