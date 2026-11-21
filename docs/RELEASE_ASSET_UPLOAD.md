# Cập nhật asset của GitHub Release

Launcher PC đọc bản dịch từ **asset của release mới nhất** (`releases/latest`), không đọc từ git.
`git push` không cập nhật `data_patched_vi.arcx`, `lua_patched_vi.arcx` hay manifest. Sau mỗi lần dựng lại:

1. Dựng lại, cài và kiểm chứng theo `docs/REBUILD_FOR_OFFICIAL_RELEASE.md`.
2. Cập nhật `dist/patch_manifest.json`, `dist/android_patch_manifest.json`, `dist/SHA256SUMS.txt` (sha + size).
3. Xin người dùng một token GitHub (fine-grained, chỉ repo `doubleD1302/AmeeVH`, **Contents: Read and write**).
4. Chạy `tools/upload_release_assets.ps1` với `GH_TOKEN` đặt trong phiên shell hiện tại.
5. Kiểm tra: `releases/latest` có size và digest SHA256 khớp `patch_manifest.json`.
   Upload đủ cả 5 file trong một lần, nếu không launcher báo `RELEASE_ASSET_MISMATCH`.

## Quy tắc về token

- Token chỉ nằm ở `.secrets/github_token.txt` trên máy local. Thư mục `.secrets/` bị git bỏ qua (có `.gitignore` riêng
  và dòng trong `.gitignore` gốc). **Repo là công khai: không bao giờ commit, copy vào `dist/`, zip, release hay tài liệu.**
- `tools/upload_release_assets.ps1` dùng `GH_TOKEN` nếu có, nếu không thì đọc file trên. Lỗi 401 nghĩa là token đã hết hạn
  hoặc bị thu hồi: hỏi người dùng token mới và ghi đè file.
- Không đọc token từ `git credential` hay kho thông tin đăng nhập của người dùng.
- Không in token ra log hay báo cáo; không đưa vào commit message, tài liệu hay chat.
- Trước mỗi `git add`/commit, chạy `git status` để chắc chắn không có gì trong `.secrets/`.
- Token có quyền ghi vào repo: chỉ dùng cho việc upload release được giao.
- Theo `docs/GITHUB_RELEASE_RULES.md`: tiêu đề release chỉ ghi số phiên bản; mô tả tối đa 100 từ.

## Phát hành tag mới (ví dụ v1.3.2, 2026-11-20)

Thứ tự đã dùng, tránh cửa sổ launcher thấy release nửa vời (`RELEASE_ASSET_MISMATCH`):

1. Bump `LAUNCHER_VERSION`, `version_info.txt`, dựng EXE (`tools/build_pc_launcher_v132.py`), cập nhật `patch_manifest.json` / `android_patch_manifest.json` (`version`, `release_tag`, URL zip/data/lua trỏ tag mới, sha/size data+lua cho cả Android `data_arcx`/`lua_arcx`/`files`), `android_localadb_launcher.json` (`apk_url` tag mới), rồi lập lại `SHA256SUMS.txt`. Chạy `tools/verify_seamless_update_readiness.py`.
2. Commit code (chưa kèm `launcher/notifications.json`, `web/index.html`) và push `main`.
3. Tạo release **nháp** (tiêu đề chỉ số phiên bản, mô tả ≤100 từ), tải đủ asset: EXE, APK, 2 zip, data, lua, 3 JSON, `SHA256SUMS.txt`. Chỉ một `.exe` trong release (launcher chọn `.exe` đầu tiên).
4. So digest SHA256 của từng asset với `SHA256SUMS.txt`, rồi mới công khai (`draft:false`, `make_latest`).
5. Mô phỏng người dùng cũ: `NetworkService.check_for_updates('1.3.1')` phải trả `has_update` + URL tải + sha; `sync_channel` phải báo bản Việt hóa mới.
6. Cuối cùng mới commit/push `launcher/notifications.json` và `web/index.html` (link tải).

## Bản chỉ đổi launcher (ví dụ v1.3.3, 2026-11-21)

Khi bản dịch không đổi, giữ nguyên `patch_manifest.json` và `android_patch_manifest.json` (không đổi `version`, `release_tag`, URL). Đổi `release_tag` làm đổi `manifest_sha256` và launcher sẽ hỏi mọi người cài lại cùng một bản dịch. Release mới vẫn phải mang đủ 10 asset vì launcher gắn gói ảnh `.zip` theo release mới nhất. Dùng `tools/release_v133.py draft | verify | publish` (token từ `.secrets/`, bản nháp trước, so digest rồi mới công khai).
