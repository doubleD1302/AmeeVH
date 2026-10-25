# Quy chuẩn Bất biến khi Build, Đồng bộ và Triển khai (Deployment & Sync Invariants)

Tài liệu này là quy chuẩn bắt buộc cho mọi Agent, Subagent và Script trong dự án Việt hóa Stella Sora nhằm ngăn chặn triệt để sự cố thoái lui dữ liệu (data regression).

---

## 1. Bài học Sự cố ngày 25/10/2026 (Post-Mortem)

### Mô tả hiện tượng
Trong quá trình hoàn thiện và trau chuốt kịch bản cốt truyện (`lua.arcx`), người dùng phát hiện toàn bộ các bản dịch giao diện (`UIText`), tên kỹ năng nhân vật (`Skill`, `MainSkill`, `SecondarySkill`, `Potential`) và tên đĩa nhạc (`DiscIP`, `Item`) vốn đã hoàn thiện 100% trước đó đột ngột bị thụt lùi về phiên bản cũ (tiếng Anh hoặc bản dịch thô).

### Nguyên nhân gốc rễ (Root Cause)
1. **Sao chép dây chuyền sai nguồn**: Trong script đóng gói kịch bản `tools/build_lua_arcx_v097.py`, có logic tự động đồng bộ sang thư mục Steam:
   ```python
   standalone_data = Path(r"c:\YostarGames\StellaSora_EN") / "Persistent_Store" / "Tables" / "data.arcx"
   steam_data = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stella Sora") / "Persistent_Store" / "Tables" / "data.arcx"
   shutil.copy2(standalone_data, steam_data)
   ```
2. **File nguồn bị lỗi thời**: Thư mục cục bộ `c:\YostarGames\StellaSora_EN` lúc đó đang chứa file `data.arcx` cũ (25.77 MB) chưa được cập nhật 95 bảng dịch đĩa nhạc/kỹ năng mới nhất, thay vì bản chuẩn vàng `dist/data_patched_vi.arcx` (25.79 MB).
3. **Hiệu ứng lan truyền lỗi**: Khi script build kịch bản thoại chạy, nó đã vô tình lấy file cũ từ Yostar ghi đè sang Steam, làm mất toàn bộ thành quả dịch bảng thuật ngữ và giao diện đã được duyệt.

---

## 2. Các nguyên tắc Bất biến (Core Invariants)

### Invariant 1: Tách biệt tuyệt đối giữa Kịch bản và Bảng dữ liệu (Domain Separation)
* `lua.arcx` (kịch bản, hội thoại, tương tác, story) và `data.arcx` (bảng dữ liệu hệ thống, kỹ năng, đĩa nhạc, UI text) là hai thực thể dữ liệu hoàn toàn độc lập.
* Khi build hoặc chỉnh sửa kịch bản (`lua.arcx`), **NGHIÊM CẤM** tự ý can thiệp, sao chép hoặc ghi đè file bảng dữ liệu `data.arcx`, trừ khi task được giao có phạm vi rõ ràng về cập nhật bảng dữ liệu.

### Invariant 2: Nguồn Chuẩn Độc lập Duy nhất (Single Golden Source of Truth)
Mọi hành động triển khai (deploy) vào game (dù là bản Yostar Standalone hay Steam) **CHỈ ĐƯỢC PHÉP** lấy trực tiếp từ thư mục `StellaSora_VietHoa/dist/`:
* **Bảng dữ liệu (Tables)**: `StellaSora_VietHoa/dist/data_patched_vi.arcx`
  - Đã tích hợp đầy đủ 95 bảng dịch, 38 đĩa nhạc, 92 kỹ năng, toàn bộ giao diện UI.
  - Kích thước chuẩn: ~25.799.809 bytes.
* **Kịch bản (Scripts)**: `StellaSora_VietHoa/dist/lua_patched_vi.arcx`
  - Đã đóng gói toàn bộ kịch bản, hội thoại mượt mà, văn phong thuần Việt.
  - Kích thước chuẩn: ~67.946.295 bytes.

### Invariant 3: Nghiêm cấm Sao chép Dây chuyền giữa các Client (No Cross-Client Copying)
* **TUYỆT ĐỐI KHÔNG** sao chép dữ liệu từ client này sang client khác (ví dụ: copy từ Yostar sang Steam, hoặc từ Steam sang Yostar).
* Cả hai thư mục game chỉ đóng vai trò là đích nạp (Sink/Consumer) nhận bản sao độc lập trực tiếp từ `dist/`.

### Invariant 4: Chốt chặn Kiểm chứng Hồi quy Bắt buộc (Mandatory Regression Gate)
Sau bất kỳ thao tác build hoặc triển khai nào, Agent/Script **BẮT BUỘC** phải chạy script kiểm tra tính toàn vẹn:
```powershell
python tools/verify_deployed_game_data.py
```
Tiêu chí nghiệm thu của Gate:
1. Giải mã trực tiếp (Decrypted inspection) và xác nhận sự tồn tại của các đĩa nhạc mẫu:
   - `211001`: *Sớm Mai Trong Lành*
   - `213013`: *Thì Thầm Mùa Thu*
   - `214058`: *Hành Khúc Mùa Hè*
   - `214066`: *Khải Minh Dẫn Lối*
   - `214067`: *Rực Rỡ Vĩnh Hằng*
2. Xác nhận sự tồn tại của các kỹ năng mẫu:
   - `101000103.1`: *Ném Chuột Chù*
   - `101001502.1`: *Bom Bùm Bụp*
   - `100011102.1`: *Hàn Băng Lộ*
   - `14040000.1`: *Bão Đạn Thỏ Con*
   - `14740000.1`: *Giai Điệu Seraphim*
3. Xác nhận chuỗi giao diện (`Bỏ qua đoạn cốt truyện này?`, `Nhận tất cả`...).
4. Kiểm tra mã băm SHA256 giữa file nguồn trong `dist/` và file đích trong tất cả thư mục game thực tế phải trùng khớp 100%. Nếu có sai lệch, tiến trình build phải bị hủy ngay lập tức.
