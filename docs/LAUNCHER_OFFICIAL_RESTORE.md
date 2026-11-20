# Launcher: Khôi phục gốc từ máy chủ chính thức + nhắc trước khi game update

Cập nhật 2026-11-20. Chưa phát hành, chưa bump version (launcher vẫn `1.3.1` trong `launcher/core/config.py`). Mã: `launcher/core/official_resources.py`, `official_restore.py`, `bsdiff40.py`; giao diện: `launcher/ui/main_window.py`, `overview_view.py`, `settings_modal.py`; test: `launcher/tests/test_official_restore.py`.

## 1. Vì sao đổi

Nút "Khôi phục" cũ copy lại `data.arcx.orig_en` / `lua.arcx.orig_en` hoặc bản sao lưu trong `%LOCALAPPDATA%\StellaSora_Launcher_Candidate_r02\backups`. Các bản này có thể là phiên bản game cũ (trong game của người dùng `lua.arcx.orig_en` là bản 2.0.x, 65 386 664 byte, ngày 21/10) hoặc chính là bản đã Việt hóa. Bản mới **không đọc** các nguồn đó nữa.

## 2. Nút "Khôi phục" làm gì

1. Hỏi máy chủ chính thức (`https://nova-static.stellasora.global`, khu vực EN): `/meta/serverlist.html` + `/meta/win.html` (AES-128-CBC; giải mã bằng Windows CNG qua ctypes, không thêm thư viện) → manifest `ss_win.mani` + `ss_win_add.mani` + `p_N_m.ss_win.mani`, kiểm MD5 từng manifest, kiểm serverlist không đổi trong lúc đọc. Cùng giao thức với `tools/stella_hot_update.py` / StellaResourceTool.
2. Chọn tập tệp cần khôi phục: `data.arcx`, `lua.arcx` và mọi tệp trong `.vietnamese_patch_receipt.json` (bundle `.en.unity3d`, `.srt`), chỉ trong allow-list của installer. Không có biên bản thì quét thêm `AssetBundles/*.en.unity3d` khác bản chính thức.
3. Chọn **phiên bản đích** (xem mục 4): mặc định đúng phiên bản mà `Persistent_Store/ss_win.mani` của game đang ghi nhận.
4. Mỗi tệp: nếu MD5 hiện tại đã bằng bản chính thức → giữ; nếu `StreamingAssets/InstallResource/<tên>` khớp MD5 → dùng bản đó; còn lại tải từ CDN (tệp đầy đủ hoặc base + chuỗi delta BSDIFF40, kiểm MD5/kích thước từng bước, tải tiếp bằng HTTP Range, thử lại 3 lần). Tệp chỉ có trong gói Việt hóa (không có trong manifest) bị gỡ.
5. **Chưa động vào game cho đến khi mọi thứ đã tải xong và đúng MD5.** Sau đó: kiểm dung lượng → chép bản đã xác minh cạnh đích (`.official_*`) và đọc lại MD5 → chuyển tệp hiện tại sang `backups/game_*/official_restore_*` → `os.replace` → đọc lại MD5. Lỗi ở bước nào cũng hoàn tác các tệp đã đổi; nếu tiến trình chết giữa chừng, lần chạy sau tự trả tệp gốc từ journal (`official_restore_*/journal.json`). Thành công thì xoá bản sao lưu Việt hóa (cài lại được từ GitHub) và xoá bộ nhớ đệm tải.
6. Trạng thái: xoá `.vietnamese_patch_receipt.json`; ghi `Persistent_Store/viethoa_installed.json` = `{"status":"official_restored","vietnamese_installed":false,"official_resource_version":…,"manifest_sha256":…,"files":{rel:{md5}},…}`; đánh dấu các journal installer cũ là `restored`. Launcher đọc file này (`GameInfo.official_restore`) và hiện "Đang ở dữ liệu gốc nhà phát hành (…)". Biên bản cài Việt hóa mới luôn thắng nếu cài lại.

Không động tới: `ss_win.mani`, `Hotfix.dll`, `hotfix.arch`, bundle không có trong biên bản, `*.orig_en`, thư mục Steam khác (mỗi lần chỉ làm trên thư mục game đang chọn; Yostar và Steam là hai bản cài riêng, không copy chéo).

## 3. Nhắc / tự khôi phục trước khi game update

Phương án chọn: **phát hiện + nhắc + nút khôi phục nhanh; tự khôi phục là tuỳ chọn, mặc định TẮT.**

- Mỗi lần mở launcher (sau khi quét game), và mỗi 30 phút, launcher gọi `check_official_update`: chỉ tải `serverlist.html` (432 byte); chỉ khi `server_data_version` đổi mới đọc lại catalog đầy đủ (kết quả nhớ trong `%LOCALAPPDATA%\…\official_check.json`). So `RES_VER`/`GAME_VER` của máy chủ với `ss_win.mani` của game. Offline hoặc lỗi → im lặng, không làm phiền.
- Cần khôi phục = có bản cập nhật **và** game đang mang bản Việt hóa (biên bản cài hợp lệ). Khi đó: badge "⚠ Game có bản cập nhật — Khôi phục gốc", hộp thoại hỏi 1 lần/phiên cho mỗi phiên bản mới, và nút **Mở game** của launcher chặn lại hỏi "Khôi phục rồi mở game" (bấm Hủy → không mở; bấm Mở game lần nữa → mở không khôi phục, vì người chơi đã chọn).
- Cài đặt (Cài đặt launcher): "Kiểm tra bản cập nhật game của nhà phát hành lúc mở" (`check_official_on_start`, mặc định bật) và "Tự khôi phục dữ liệu gốc khi game có bản cập nhật" (`auto_restore_before_game_update`, mặc định tắt). Khi bật tự khôi phục: tải ngay khi phát hiện (nếu game không chạy) và tự khôi phục trước khi Mở game.
- Luồng "Cài Việt hóa" khi phát hiện game mới hơn gói dịch hoặc log lỗi vá cũng dùng engine mới.

Vì sao không bật tự khôi phục mặc định: nó ghi vào game của người chơi không cần họ bấm và tải vài trăm MB; người chơi mất bản Việt hóa cho đến khi cài lại. Nhắc + hỏi an toàn hơn. Hạn chế đã biết: nếu người chơi mở game bằng Yostar Launcher/Steam mà không qua launcher này thì launcher không chặn được — khi đó chỉ dựa vào banner lần mở sau và `notifications.json` (đăng thông báo type `release`/`notice` khi game update để người chơi biết; chưa thay file này vì thuộc phát hành).

## 4. Phiên bản đích: `prefer="game"` (mặc định) và `"latest"`

- `game`: dùng MD5 ghi trong `Persistent_Store/ss_win.mani` của game → đúng thứ mà bộ cập nhật của chính game mong đợi, nên game vá delta bình thường sau đó. Khi game đã mới nhất (hiện tại: 2.1.0 / 2611141949, server data v149) thì **bằng** bản mới nhất của server. Khi server đã có bản mới hơn thì khôi phục về phiên bản game đang ghi nhận rồi để game tự lên bản mới (launcher nhắc "hãy mở game để cập nhật").
- `latest`: dùng bản cuối của server; chỉ dùng khi game chưa có/không đọc được `ss_win.mani`. Không dùng khi mani đã có vì nếu mani cũ mà tệp là bản mới thì delta của game có thể báo lỗi xác minh (chưa thử được vì hiện chưa có bản cập nhật nào mới hơn 2611141949).
- Nếu MD5 mà game ghi nhận không có trên máy chủ EN (ví dụ bản Steam khác) → dừng với lỗi `NOT_FOUND`, không đoán bản khác; dùng "Kiểm tra/Sửa tệp" của Yostar Launcher hoặc Steam.

## 5. Kiểm chứng

- `python -m unittest launcher.tests.test_official_restore` (máy chủ giả, 3 phiên bản, delta thật): khôi phục khi game mới nhất; game cũ hơn server; thiếu mani → latest; dry-run không ghi gì; tái dùng InstallResource; mất mạng/cắt tải → game nguyên vẹn, chạy lại thì tiếp tục; Range resume; lỗi `os.replace` giữa chừng → hoàn tác; hồi phục sau crash; MD5 lạ → từ chối; URL ngoài máy chủ chính thức bị từ chối; vector AES NIST; phát hiện update.
- Thực tế (2026-11-20): dry-run với máy chủ thật và e2e trên **bản sao** 95 tệp Việt hóa của game (game thật không bị ghi): 94/95 tệp được thay (1 bundle vốn đã đúng), tải 308 MB trong 145 giây; `data.arcx` (d2ee38a8…) và `lua.arcx` (55950277…) khớp MD5 với snapshot `StellaResourceDownloads\EN\2.1.0_2611141949_text_…` do StellaResourceTool tải độc lập; 0 bundle lệch manifest của game; biên bản Việt hóa đã gỡ; không còn tệp tạm; chạy lại thì không phải tải gì.
- Chưa kiểm chứng: chạy game thật sau khi khôi phục; trường hợp server có phiên bản mới hơn 2611141949 (chưa có); bản Steam; giao diện trên máy có font thật (chỉ chạy offscreen); chưa dựng lại `StellaSora_Launcher.exe` (cần chạy `tools/build_pc_launcher_v130.py` hoặc bản mới khi được phép phát hành).
