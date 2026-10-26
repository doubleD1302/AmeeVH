# r03 — sửa dependency Qt khi đóng gói

Bản r02 người dùng mở báo lỗi QtWidgets. r03 sửa dependency ICU bị lấy nhầm từ Poppler trong PATH; xem PACKAGING_FIX_R03.md. Bản r03 chỉ được build và phân tích tĩnh, chưa mở EXE hay kiểm thử theo yêu cầu người dùng. Giữ nguyên thư mục AppData candidate r02 để tiếp tục cấu hình/backup.

# Stella Sora Việt Hóa — launcher candidate r03

Đây là bản candidate mới, giữ nguyên launcher_next r01 và launcher đang dùng. Theo yêu cầu người dùng, phiên này chỉ sửa source và build; không chạy unit/fixture tests, không mở EXE, không chụp UI. Tất cả các gate đó là `untested_user_requested`. Build thành công không chứng minh cài đặt hoặc giao diện đã hoạt động.

## Chạy

Nhấp đúp `dist/launcher_ui_candidate_r03/StellaSora_Launcher.exe` sau khi nhận bàn giao. Cấu hình/backup/journal/cache nằm tại `%LOCALAPPDATA%/StellaSora_Launcher_Candidate_r02`. Có thể chỉ định `--app-data-dir "D:/Thư mục có dấu/Launcher Data"`.

Chạy source từ project root: `.venv/Scripts/python.exe -m launcher_next_r03.app`.

## Build

Từ project root: `.venv/Scripts/python.exe launcher_next_r03/build.py`. Script chỉ build, ghi hash/receipt và từ chối đè candidate đã tồn tại. Thư viện khóa ở requirements-lock.txt. Không chạy script build cũ r01.

## Chức năng và dữ liệu

- Chọn/dò Steam hoặc Yostar, đọc GAME_VER/RES_VER trong `Persistent_Store/ss_win.mani`, mở game chỉ khi nhấn. Steam dùng AppID 4813850 từ source legacy.
- Kênh mặc định kế thừa `doubleD1302/AmeeVH`; thông báo dùng schema `announcements` của source thật, có nhãn trực tuyến/bản lưu/bundled/lỗi/rỗng. Không bịa trạng thái mới nhất khi mạng lỗi.
- Cài bằng manifest `files` có SHA256/size hoặc `bundles` có patched_sha256/size_bytes; bắt buộc client_game_version/resource_version khớp. Manifest bundles-only chỉ cho phép cài texture, không tự thêm data/lua thiếu hash. Gói không có metadata nguồn đầy đủ sẽ báo unavailable.
- Gói ngoại tuyến: Cài đặt → chọn thư mục chứa patch_manifest.json và tệp tương ứng trường source. Để trống để lấy manifest/payload từ release cấu hình. Không lấy payload tự động từ đường dẫn máy dev hoặc cwd.
- Đích allowlist: Persistent_Store Scripts/lua.arcx, Tables/data.arcx, AssetBundles/*.en.unity3d, Videos/*.srt. Không ghi executable/DLL/anti-cheat/manifest game.
- Trước thay tệp: kiểm hash/kích thước, đủ đĩa, backup đọc lại, preimage guard, journal ý định trước replace. Receipt chỉ sau toàn bộ readback. Lỗi phục hồi giữ journal và báo RECOVERY_REQUIRED.
- Khôi phục dùng đúng journal/backup của receipt và canonical root. Tệp hiện tại phải khớp hash bản đã cài; game cập nhật gây conflict. Tệp tạo mới được loại khi restore. Backup lịch sử giữ nguyên. Có thể phục hồi qua nhiều lần cài ngược từng bước; không khẳng định một lần restore luôn về game gốc ban đầu.
- Công cụ nâng cao: chẩn đoán/copy log, quét ADB chỉ đọc (người dùng nhấn), phục hồi journal bị ngắt, kiểm update EXE. Không có ADB push/install.
- Cập nhật EXE chỉ khi release asset có digest SHA256. Helper dùng argument list Unicode, deadline, preimage/backup/readback, giữ nguồn khi lỗi. Endpoint thiếu digest thì unavailable; không tự bỏ hash để cập nhật.
- Ủng hộ chưa có người nhận/API xác minh nên hiển thị chưa khả dụng, không có QR hay danh sách giả.

## Giới hạn chưa kiểm

Chưa chạy code ứng dụng hoặc candidate theo yêu cầu người dùng. DPI 100/125/150/200%, 1366×768, nút/bàn phím/FAQ, worker responsiveness, fault injection, network/cache, installer/recovery/rollback/self-update và môi trường Windows sạch đều chưa kiểm. Source có các biện pháp bảo vệ nhưng chưa được xác nhận bằng chạy thử. Hãy giữ launcher cũ và backup hiện có khi tự thử.

`tests/` được giữ từ bản r01 với namespace đã chuyển; nhiều kỳ vọng của bộ test cũ không còn tương thích contract strict r02. Chúng không được chạy hay dùng làm bằng chứng cho r02.
