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
