# Cơ Chế Ưu Tiên Tải `InstallResource` vs `Persistent_Store` & Quy Chuẩn Định Tuyến Texture

Tài liệu này ghi lại bài học kỹ thuật về hiện tượng texture đã Việt hóa nằm trong `Persistent_Store/AssetBundles/` nhưng trong game Yostar PC vẫn hiển thị bản EN gốc từ `StellaSora_Data/StreamingAssets/InstallResource/`, cùng quy trình xử lý an toàn và quy chuẩn giữ sạch GitHub.

---

## 1. Hiện Tượng & Nguyên Nhân Gốc Rễ

Trên client Yostar PC (đã xác minh ở phiên bản game `2.1.0`, `RES_VER:2611141949`):
1. Toàn bộ `105/105` bundle `.en.unity3d` đã Việt hóa được triển khai đúng SHA256 vào `Persistent_Store/AssetBundles/`.
2. Tuy nhiên, khi một bundle **không thay đổi MD5** giữa bản cài gốc trong `StellaSora_Data/StreamingAssets/InstallResource/install_resource_manifest.mani` (`RES_VER:0`, `GAME_VER:2.0.0`) và manifest cập nhật `Persistent_Store/ss_win.mani` (`RES_VER:2611141949`, `GAME_VER:2.1.0`), client có thể đọc bản EN gốc trong `InstallResource/` hoặc bỏ qua file đã sửa trong `Persistent_Store/` nếu `file_versions.dat` / `ss_win.mani` không khớp.
3. Kết quả kiểm kê ngày `2026-11-24` trên `2.1.0` ghi nhận đúng **3 bundle** (tổng cộng **96 texture đã Việt hóa**) rơi vào trạng thái bị che (`shadowed`):

| Bundle | Số texture VI bị che | MD5 trong `ss_win.mani` & `install_resource_manifest.mani` | MD5 trong `file_versions.dat` trước khi sửa |
| --- | ---: | --- | --- |
| `ui_commonex.en.unity3d` | **80** (`4` standalone + `76` atlas UI cốt lõi: `btn_video_skip`, `zs_result_win_1..7`, `zs_battle_result_4..6`, `zs_level_levelup_text`, `zs_avg_chapter_complete`…) | `62aff84f3ab5ba88927eadc302aa5b5f` | `e88529c33776d52510fd11acb993d872` *(lệch)* |
| `icon-5.en.unity3d` | **15** (`CharSkin_ArtText_11603_lang`, banner, comic, tab…) | `0ff78c4c073b15f76b1af1fdfe3d2c29` | `bb9ad589f4a43858c9ab08845fb309d3` *(lệch)* |
| `ui_activity__102005.en.unity3d` | **1** (`zs_towerdef_title_lang`) | `874a7c961eac1770a72cdaf76b9b4630` | `874a7c961eac1770a72cdaf76b9b4630` *(trùng IR)* |

---

## 2. Ranh Giới Vùng Cấm Tuyệt Đối

**TUYỆT ĐỐI KHÔNG** sửa, ghi đè hay xóa bất kỳ tệp nào trong:
- `StellaSora_Data/` và toàn bộ `StellaSora_Data/StreamingAssets/InstallResource/` (bao gồm các file `.en.unity3d` gốc và `install_resource_manifest.mani`).
- `StellaSora.exe`, `GameAssembly.dll`, `UnityPlayer.dll`, `StellaSoraBase.dll`, `AntiCheatExpert/`.
- `dist/data_patched_vi.arcx`, `dist/lua_patched_vi.arcx`, `Persistent_Store/Tables/data.arcx`, `Persistent_Store/Scripts/lua.arcx` khi chỉ xử lý texture (`AssetBundles`).

**Lý do:** Sửa `InstallResource/` phá vỡ nguồn gốc để launcher/game tự phục hồi (`official_restore` / `vanilla_restore`) và vi phạm nguyên tắc bảo toàn nhị phân cài sẵn; sửa nhầm `.arcx` có thể gây thoái lui dữ liệu dịch bảng/kịch bản.

---

## 3. Quy Trình Định Tuyến An Toàn 2 Mức (`tools/sync_persistent_texture_routing.py`)

Công cụ [sync_persistent_texture_routing.py](../tools/sync_persistent_texture_routing.py) chỉ đọc `InstallResource/` để đối chiếu và có chốt bảo vệ từ chối mọi thao tác ghi vào `StellaSora_Data/`. Sao lưu gốc của `file_versions.dat` và `Persistent_Store/ss_win.mani` được tạo một lần (bất biến) tại `backups/pre_routing_sync_20261124/`.

### Kiểm tra trạng thái (chỉ đọc)
```powershell
& 'StellaSora_VietHoa\.venv\Scripts\python.exe' StellaSora_VietHoa\tools\sync_persistent_texture_routing.py --status
```

### Mức 1 (`--mode file-versions-only` — An toàn tối đa, thử trước)
- Không đụng tới `Persistent_Store/ss_win.mani`.
- Đồng bộ MD5 của mọi bundle Việt hóa trong `file_versions.dat` về đúng MD5 chính thức trong `ss_win.mani`.
```powershell
& 'StellaSora_VietHoa\.venv\Scripts\python.exe' StellaSora_VietHoa\tools\sync_persistent_texture_routing.py --mode file-versions-only
```

### Mức 2 (`--mode persistent-override` — Dự phòng nếu Mức 1 chưa đủ)
- Dùng khi đã test thực tế trong game ở Mức 1 mà engine vẫn ưu tiên `InstallResource` cho các bundle có `ss_win.mani MD5 == install_resource_manifest.mani MD5`.
- Chỉ cập nhật đúng cột `md5` và `size` của các bundle bị che trong `Persistent_Store/ss_win.mani` và `file_versions.dat` sang MD5/size thật của file Việt hóa trong `Persistent_Store/AssetBundles/` (giữ nguyên cột 4 và toàn bộ dòng khác).
- **Bắt buộc hoàn nguyên trước khi cập nhật game từ nhà phát hành** để tránh `BinDiffPatchError` khi game tải patch chính thức.
```powershell
& 'StellaSora_VietHoa\.venv\Scripts\python.exe' StellaSora_VietHoa\tools\sync_persistent_texture_routing.py --mode persistent-override
```

### Hoàn nguyên (`--restore`)
- Khôi phục byte-identical cả `file_versions.dat` và `Persistent_Store/ss_win.mani` từ `backups/pre_routing_sync_20261124/` kèm kiểm tra SHA256 readback.
```powershell
& 'StellaSora_VietHoa\.venv\Scripts\python.exe' StellaSora_VietHoa\tools\sync_persistent_texture_routing.py --restore
```

Sau mọi thao tác, luôn chạy cổng kiểm chứng bắt buộc:
```powershell
& 'StellaSora_VietHoa\.venv\Scripts\python.exe' StellaSora_VietHoa\tools\verify_deployed_game_data.py
```

---

## 4. Quy Chuẩn Giữ Sạch GitHub Push (Không Lỗi, Không Rác)

1. **Không dùng `git add -A` bừa bãi** khi workspace có tệp tạm, dữ liệu run lớn hoặc sản phẩm build ngoài phạm vi: chỉ `git add` đích danh các file code/docs thuộc task.
2. **Không commit file rác / nhị phân nặng / thư mục bị ignore**: kiểm tra `git status --short`, dọn file 0-byte lạc (ví dụ lỗi gõ lệnh tạo file `i)`), không commit `dist/`, `work/`, `backups/`, `staging/`, `*.unity3d`, `*.arcx`, `*.exe`, `*.apk`, `*.zip`, `.secrets/`.
3. **Kiểm tra trước khi commit & push**:
   - Chạy `git fetch origin` để đảm bảo không lệch `origin/main`.
   - Chạy `git diff --cached --stat` (xác nhận không có file > 50 MB hoặc file ngoài scope).
   - Chạy `git diff --cached --check` (đảm bảo không có lỗi whitespace/conflict marker).
   - Chỉ `git push origin main` sau khi các kiểm tra cục bộ đều `PASS`.
