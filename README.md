# AmeeVH — Dự Án Việt Hóa Stella Sora (Đa Nền Tảng)

Bộ công cụ và dữ liệu Việt hóa game **Stella Sora (EN)** hỗ trợ đa nền tảng:
- 💻 **PC Windows**: Launcher cài đặt 1-chạm, khôi phục gốc (Rollback), tự động cập nhật từ GitHub, bảng thông báo và sao chép mã lỗi gửi Dev.
- 📱 **Android**: Ứng dụng APK tích hợp **Thông Báo Nổi (Floating Window Overlay)**, hỗ trợ nạp trực tiếp qua Local ADB, tự động cập nhật GitHub và sao chép mã lỗi gửi Dev.

---

## 🚀 Tính Năng Chính

1. **Bản dịch chất lượng cao**:
   - Dịch toàn bộ phụ đề mở đầu và ca từ (51 cue) chuẩn Unicode NFC.
   - Kiểm duyệt cấu trúc chặt chẽ (Static Audit 0 lỗi, bảo toàn token, tags, timestamps và ngắt dòng).
2. **PC Launcher 1-Chạm**:
   - Chạy trực tiếp qua `launcher/Start_Launcher.bat` hoặc `python launcher/launcher_pc.py`.
   - Sao lưu tự động nguyên bản gốc có kiểm tra mã băm SHA256 trước khi cài đặt.
   - Hỗ trợ rollback khôi phục nguyên bản bất cứ lúc nào.
3. **Android APK & Local ADB**:
   - Ứng dụng APK: `android/bin/StellaSora_VietHoa.apk` hiển thị widget thông báo nổi đè lên game.
   - Công cụ `tools/adb_patcher.py` tự động quét thiết bị và đẩy dữ liệu Việt hóa vào máy ảo/điện thoại qua ADB.
4. **Tự Động Cập Nhật GitHub**:
   - Cả PC Launcher và Android App đều tự động kiểm tra phiên bản mới từ repository `doubleD1302/AmeeVH`.
5. **Sao Chép Mã Lỗi Cho Dev (1-Chạm)**:
   - Thu thập cấu hình hệ thống, phiên bản game, log ngoại lệ và copy vào Clipboard chỉ với 1 cú click để người dùng dễ dàng gửi phản hồi cho đội ngũ phát triển.

---

## 📂 Cấu Trúc Thư Mục

- `launcher/`: Trình cài đặt PC giao diện trực quan 1-chạm (`launcher_pc.py`, `Start_Launcher.bat`).
- `android/`: Mã nguồn dự án Android app và gói cài đặt `StellaSora_VietHoa.apk`.
- `tools/`: Các công cụ cốt lõi (`localize.py`, `adb_patcher.py`).
- `work/batches/`: Các tập tin đề xuất bản dịch (proposals) đã dịch và audit.
- `docs/`: Tài liệu kỹ thuật, quy chuẩn dịch thuật (`STYLE_GUIDE_VI.md`), tiêu chuẩn an toàn (`PATCH_AND_ROLLBACK.md`).
- `STATUS.json` & `CHECKPOINT.json`: Nhật ký trạng thái và mốc tiến độ dự án.

---

## 📖 Bắt Đầu Nhanh

Xem chi tiết hướng dẫn tại [START_HERE.md](START_HERE.md) và hợp đồng vận hành tại [AGENTS.md](AGENTS.md).
