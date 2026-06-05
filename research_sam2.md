# Nghiên cứu về SAM 2 & SAM 2.1 (Segment Anything Model 2)

Tài liệu này tổng hợp thông tin về yêu cầu phần cứng, tài nguyên chính thức, kích thước các phiên bản mô hình của **SAM 2 / SAM 2.1**, đồng thời đánh giá khả năng chạy thực tế trên cấu hình máy Mac M1 của bạn.

---

## 1. Link Repo & Model Checkpoints chính thức

*   **GitHub Repository chính thức:** [facebookresearch/sam2](https://github.com/facebookresearch/sam2)
    *   *Đây là nơi chứa toàn bộ mã nguồn cài đặt, cấu hình model (YAML) và hướng dẫn sử dụng.*
*   **Bài báo nghiên cứu (Research Paper):** [SAM 2: Segment Anything in Images and Videos](https://arxiv.org/abs/2408.00714)
*   **Hugging Face Hub:** [facebook/sam2](https://huggingface.co/facebook/sam2) hoặc [facebook/sam2.1](https://huggingface.co/facebook/sam2.1)

---

## 2. Danh sách các phiên bản Model (Model Weights)

Meta cung cấp 4 kích thước khác nhau dựa trên kiến trúc bộ mã hóa ảnh **Hiera**, giúp giảm đáng kể số lượng tham số so với SAM 1 nhưng vẫn đạt độ chính xác vượt trội:

| Phiên bản Model | Số lượng tham số (Parameters) | Kích thước file (.pt) | File cấu hình (Config YAML) | Phù hợp với thiết bị |
| :--- | :--- | :--- | :--- | :--- |
| **SAM 2 Tiny (t)** | ~38.9 Triệu (38.9M) | ~149 MB (Ultralytics: ~78 MB) | `sam2_hiera_t.yaml` | Thiết bị cấu hình yếu, Mac Air M1 8GB |
| **SAM 2 Small (s)** | ~46.0 Triệu (46.0M) | ~176 MB (Ultralytics: ~92 MB) | `sam2_hiera_s.yaml` | Cân bằng tốt giữa tốc độ và độ chính xác |
| **SAM 2 Base Plus (b+)**| ~80.8 Triệu (80.8M) | ~309 MB (Ultralytics: ~162 MB)| `sam2_hiera_b+.yaml` | Máy Mac 16GB RAM, GPU tầm trung |
| **SAM 2 Large (l)** | ~224.4 Triệu (224.4M)| ~856 MB (Ultralytics: ~449 MB)| `sam2_hiera_l.yaml` | Server GPU chuyên dụng, Máy Mac >= 32GB |

> [!NOTE]
> Phiên bản **SAM 2.1** (cập nhật cuối năm 2024) giữ nguyên số lượng tham số và kiến trúc, nhưng được tinh chỉnh trên tập dữ liệu tối ưu hơn để xử lý tốt hơn các vật thể bị che khuất (occlusions) hoặc tương đồng nhau.

---

## 3. Cấu hình yêu cầu (Hardware Requirements)

*   **Hệ điều hành:** Linux, Windows, macOS 14+ (đối với Apple Silicon cần PyTorch hỗ trợ MPS).
*   **Python:** Khuyến nghị Python 3.10 - 3.12.
*   **PyTorch:** Yêu cầu PyTorch 2.3.1+ (Khuyến nghị 2.5.1+ để có hỗ trợ MPS cho Apple Silicon tốt nhất).
*   **GPU NVIDIA (Khuyến nghị cho server/training):** Chạy mượt trên GPU có VRAM từ 6GB trở lên. Với video dài hoặc xử lý số lượng lớn cần 16GB VRAM trở lên (A100/H100 cho khối lượng công việc cấp doanh nghiệp).
*   **CPU:** Có thể chạy được nhưng cực kỳ chậm (chậm hơn GPU khoảng 30x - 60x), không thích hợp cho các ứng dụng thời gian thực.

---

## 4. Đánh giá hiệu năng trên cấu hình Mac của bạn

Kiến trúc Unified Memory (Bộ nhớ dùng chung) của Apple Silicon giúp GPU tích hợp truy cập trực tiếp vào RAM hệ thống một cách nhanh chóng, rất phù hợp để chạy các mô hình AI vừa và nhỏ.

### Kịch bản 1: Mac M1 Pro (16GB RAM) của bạn
*   **Khả năng đáp ứng:** **Rất tốt.**
*   **Model phù hợp:** **Tiny, Small, và Base Plus.**
*   **Đánh giá thực tế:**
    *   Khi chạy inference trên ảnh đơn (để đếm thuốc), bản **Tiny** và **Small** sẽ chỉ mất khoảng **15ms - 40ms** cho mỗi lượt xử lý nếu sử dụng GPU qua cơ chế MPS (`device="mps"`).
    *   Lượng RAM tiêu thụ tĩnh khi load model rất thấp (< 1GB). Bộ nhớ phát sinh khi chạy (activation memory) chỉ khoảng 1-2GB, hoàn toàn nằm trong mức an toàn của 16GB RAM (kể cả khi bạn đang mở VS Code và trình duyệt Chrome).
    *   Bạn cũng có thể chạy được bản **Base Plus** mượt mà. Bản **Large** có thể chạy được nhưng tốc độ sẽ chậm đi đáng kể và bắt đầu gây áp lực lên dung lượng RAM còn trống của máy.

### Kịch bản 2: Macbook Air M1 (Không quạt)
Khả năng hoạt động phụ thuộc vào phiên bản RAM của chiếc Mac Air M1 đó:

*   **Nếu là Mac Air M1 bản 16GB RAM:**
    *   Chạy rất tốt các bản **Tiny** và **Small**. 
    *   Tốc độ xử lý sẽ chậm hơn M1 Pro khoảng 30% - 50% do M1 thường có ít nhân GPU hơn (7-8 nhân so với 14-16 nhân của M1 Pro) và băng thông bộ nhớ thấp hơn, nhưng hoàn toàn chấp nhận được cho nhu cầu đếm thuốc offline.
*   **Nếu là Mac Air M1 bản 8GB RAM:**
    *   **Giới hạn phần cứng:** 8GB RAM phải chia sẻ cho cả hệ điều hành macOS (đã ăn khoảng 3-4GB), các ứng dụng chạy ngầm và GPU. Lượng RAM trống thực tế cho mô hình chỉ còn khoảng 2-3GB.
    *   **Khả năng chạy:** Bạn **chỉ nên dùng bản Tiny (sam2_hiera_t)**. Bản Tiny tiêu tốn rất ít RAM và VRAM.
    *   **Rủi ro:** Nếu bạn cố chạy bản Base hoặc Large, hệ thống sẽ bị tràn RAM và phải chuyển sang sử dụng bộ nhớ ảo trên SSD (Swap). Điều này làm tốc độ chạy chậm đi hàng chục lần, máy bị giật lag nghiêm trọng, và có thể dẫn đến crash ứng dụng (lỗi OOM). Ngoài ra, do Macbook Air không có quạt tản nhiệt, nếu chạy tác vụ nặng liên tục thì máy sẽ bị nóng và tự động giảm hiệu năng (thermal throttling).

---

## 5. Lưu ý quan trọng khi cài đặt SAM 2 trên macOS (Apple Silicon)

Khi cài đặt thư viện `sam2` chính thức từ Meta trên macOS, bạn cần lưu ý:

1.  **Bỏ qua CUDA Compilation:** Do thư viện mặc định cố gắng biên dịch các extension CUDA (chỉ dành cho card NVIDIA), bạn cần đặt biến môi trường để bỏ qua bước này khi cài đặt:
    ```bash
    SAM2_BUILD_CUDA=0 pip install -e .
    ```
2.  **Khởi tạo thiết bị MPS (Metal Performance Shaders):** Thay vì dùng `cuda`, hãy cấu hình mã nguồn trỏ sang `mps`:
    ```python
    import torch
    device = torch.device("mps") if torch.backends.mps.is_available() else torch.device("cpu")
    ```
3.  **Sử dụng Ultralytics (Giải pháp thay thế đơn giản nhất):**
    Nếu không muốn cài đặt phức tạp từ repo gốc của Meta, bạn có thể sử dụng thư viện `ultralytics` (đã tích hợp sẵn SAM 2 rất tối ưu cho macOS):
    ```bash
    pip install ultralytics
    ```
    Code gọi model cực kỳ ngắn gọn và tự động tối ưu thiết bị chạy:
    ```python
    from ultralytics import SAM
    model = SAM("sam2_t.pt") # Tự động tải checkpoint dạng tối ưu của Ultralytics
    results = model("path/to/image.jpg")
    ```
