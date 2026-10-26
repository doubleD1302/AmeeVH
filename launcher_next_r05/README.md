# Stella Sora Việt hoá — độ nét và skin r05

r05 sửa theo ảnh chạy thật của người dùng: ảnh mềm do scale ở độ phân giải logic, font nhỏ/không hợp, status bị bó thành3dòng, path chỉ hiện đuôi, nút vô hiệu khó đọc và hoa văn đè footer. Lượt này chỉ sửa source/asset và build; không chạy app/EXE/tests hoặc tạo screenshot UI theo yêu cầu người dùng.

## Chạy và build

Candidate: dist/launcher_ui_candidate_r05/StellaSora_Launcher.exe.
Build từ project root: `.venv/Scripts/python.exe launcher_next_r05/build.py`.
Chạy source khi người dùng tự thử: `.venv/Scripts/python.exe -m launcher_next_r05.app`.
Giữ AppData `%LOCALAPPDATA%/StellaSora_Launcher_Candidate_r02` để không bỏ cấu hình/backup/journal. Có thể chỉ định `--app-data-dir`.

## Thay đổi độ nét và chữ

- Nền master2048×1451 được giữ nguyên byte, vẽ trực tiếp bằng QPainter với crop cover nguồn; không tạo pixmap chỉ bằng kích thước logic rồi phóng tiếp theo DPR. Screen/DPR change yêu cầu repaint.
- Logo2152×856 là bản4xLanczos đã có trong dự án, dẫn xuất từ538×214; không phải chi tiết2Knative mới. Không AI vẽ lại. MasterLogo vẽ thẳng master, không thu300px trước.
- Bốn font Be Vietnam Pro Regular/Medium/SemiBold/Bold được đóng gói cùngOFL, đăng ký trước widget. Body15DIP, caption13, card title20semibold, modal29bold, CTA16semibold. Không ép font-size15 cho toàn QWidget, để hierarchy widget không bị QSS ghi đè. Alias style từng weight không làm startup thất bại nếu font đã nạp.
- Tiêu đề ghim riêng qua QMainWindow.menuWidget, không nằm chung height constraint với vùng cuộn; vị trí được clamp sau layout và khi đổi màn hình. Chưa quan sát khi chạy nên không gọi là đã xác nhận titlebar thực tế.
- Status112DIP không wrap. Path readonly vẽ elide giữa và luôn giữ full tooltip/copy, không có con trỏ QLineEdit kéo về đuôi.
- Nút kiểm/khôi phục vẫn bị vô hiệu khi thiếu điều kiện, nhưng chữ#b2cde3 và iconmuted đọc được; tooltip nêu lý do. Folder vuông mở chọn thư mục đúng nghĩa; Mở game ở menu bánh răng, có điều kiện thật.

## Skin và giới hạn

resources/ui/skin_r05 có183SVG,544PNG1x/2x/4x,4TTF+OFL và branding/provenance. Cùng logical ID override bản cũ. Icon outline đồng nhất24px, tab nghiêng vẽ uniform/contain với contentrect tương ứng, nút/frame mép mảnh theo skin. Frame đã có hoa văn nên không phủ crest/sweeps r04 lên nữa; footer được đẩy lên vùng an toàn. Chỉ hiển thị focus ring khi bàn phím; tab không chọn không bị mousefocus làm sáng như đã chọn.

Nguồn backend/core và guard ICU được giữ từ r04: manifest/hash/version, backup/rollback/journal/recovery, network, chỉ update khi có digest, ADB/chẩn đoán. Ủng hộ vẫn unavailable khi chưa có người nhận/API; không có dữ liệu giả.

ASSET_USAGE_MAP.json ghi rõ layer override, trạng thái wired/unused và provenance. Không khẳng định tất cả asset đã render hoặc UI đã đạt điểm giống mẫu. Font/DPI/layout/các nút và runtime đều not_run_user_requested; người dùng sẽ tự chạy candidate.
