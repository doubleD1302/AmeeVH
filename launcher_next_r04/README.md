# Stella Sora Việt hoá — giao diện launcher r04

Bản r04 dựng lại tất cả màn hình bằng asset dự án và8asset trang trí bổ sung theo5ảnh mẫu người dùng. Đây là source + EXE build; theo yêu cầu người dùng, không chạy ứng dụng/EXE, không chạy tests và không tạo screenshot UI. Không khẳng định giao diện đã được xem khi chạy hoặc điểm giống mẫu.

## Chạy và build

EXE: `dist/launcher_ui_candidate_r04/StellaSora_Launcher.exe`.
Chạy source từ project root: `.venv/Scripts/python.exe -m launcher_next_r04.app`.
Build riêng: `.venv/Scripts/python.exe launcher_next_r04/build.py`. Script từ chối đè candidate và yêu cầu workdir mới. Xem requirements-build-lock.txt, BUILD_ENVIRONMENT.json và DEPENDENCY_PROVENANCE.json.

Giữ thư mục dữ liệu `%LOCALAPPDATA%/StellaSora_Launcher_Candidate_r02` để tiếp tục cấu hình/backup/journal của candidate cũ. Có thể chọn rõ bằng `--app-data-dir`.

## Asset và bố cục

- Giữ nguyên byte logo, nền, icon cờ được cung cấp; không cắt screenshot thành UI.
- Metadata gốc: resources/ui/asset_manifest.json. Giữ213SVG+426PNG1x/2x. Metadata bổ sung: resources/ui/supplemental/asset_manifest.json;8SVG+16PNG1x/2x.
- Runtime lấy PNG2x theo ID; panel/button dùng slice_insets/content_rect trong manifest. Header/footer có chữ và nút thật. Icon+text cùng được painter vẽ, dùng ink khi nút sáng.
- Tổng quan: logo lớn và3tab ở trái trên; hai card notification/install tách riêng, giữ khoảng trống rộng ở giữa cho tranh nền. Kích thước card tại1280px rộng khoảng466/403, cách giữa khoảng360px; chiều cao234/262, card thao tác tăng326 khi có tiến trình. Không có thanh công cụ dài chiếm toàn hàng dưới.
- Modal: panels/modal hoặc panels/dialog, sao/đuôi sáng lớn, lớp kính, dải lá hai góc và header từ asset bổ sung; dim/blur là ảnh chụp trong bộ nhớ của chính cửa sổ đang mở, không dùng mockup làm background.
- Thông báo: tìm kiếm,4tab lọc, card nội dung có badge/title/summary, chi tiết hai cột và phân trang thật.
- Hướng dẫn:5mục sidebar, bước nối, instruction cards, FAQ mở/đóng, nút quay về vùng cài.
- Ủng hộ: luôn có2cột/phương thức/QRplaceholder/bảng tìm kiếm. Thiếu người nhận/API nên tile bị vô hiệu, không QR thanh toán, không tên hay số tiền giả.
- Cài đặt/Công cụ/xác nhận/lỗi dùng cùng shell, input/checkbox/toggle/progress/spinner/scrollbar/table/alert theo asset.

ASSET_USAGE_MAP.json ghi221ID, nơi dùng và state condition, tách những biến thể chỉ được đóng gói. `wired_conditional` là liên kết trong source, không phải bằng chứng đã render. Không tuyên bố toàn213asset gốc đã cùng hiển thị.

## Chức năng giữ từ r03

Chọn/dò Steam/Yostar, mở game khi bấm; cài/update qua manifest có SHA256/size và game/resource version; gói ngoại tuyến explicit; root-bound backup/receipt/journal/recovery; kiểm tệp; rollback có preimage guard; thông báo theo kênh thật; cập nhật EXE chỉ khi có digest; ADB/chẩn đoán chỉ đọc. Manifest bundle-only không tự cho phép cài data/lua. Không sửa game live trong lượt dựng/build.

Giữ fix ICU r03: build subprocess có PATH allowlist, không thu Poppler/Conda DLL; ICU hệ thống không đóng gói và có đối chiếu export tĩnh. Không sửa shared.venv hoặc DLL hệ thống.

## Phạm vi chưa kiểm

Không mở EXE/app hoặc chạy tests theo yêu cầu. Typography, căn chỉnh thực tế, DPI/scroll/focus/blur, các nút và chức năng cài/khôi phục/update đều `not_run_user_requested`. Build và phân tích source/asset không thay bằng chứng runtime. Người dùng sẽ tự chạy thử candidate.
