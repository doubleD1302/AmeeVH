# Dựng lại gói Việt hóa trên bản game chính thức mới (2.1.0 / resource 2611141949)

Mỗi khi game ra hotfix, bản `data.arcx`/`lua.arcx` Việt hóa phải được dựng lại trên **file chính thức mới**, không được vá chồng lên bản cũ
(v1.3.0 vá chữ lên bảng 2.0.x nên thiếu Gacha 10161 và kẹt màn hình Chiêu Mộ).

```powershell
# 1) tải data/lua chính thức (ghi ra ngoài thư mục game)
cd C:\YostarGames\StellaResourceTool
python stella_resource_fetch.py EN --profile text

# 2) dựng lại (chạy trong StellaSora_VietHoa, dùng .venv)
$O = 'C:\YostarGames\StellaResourceDownloads\EN\<snapshot>\files'
python tools/rebuild_data_arcx_from_official_210.py --official "$O\Tables\data.arcx" --vi <data_patched_vi.arcx cũ> `
  --overlay translations/2.1.0/Van_ban_EN_VI.jsonl --overlay translations/hotfix_2611141949/data_extra.jsonl --out dist/data_patched_vi.arcx
python tools/rebuild_lua_arcx_from_official_210.py --official "$O\Scripts\lua.arcx" --old-vi <lua_patched_vi.arcx cũ> `
  --en-orig dist/vanilla/lua_original_en.arcx --overlay translations/2.1.0/Van_ban_EN_VI.jsonl `
  --overlay translations/hotfix_2611141949/pending_vi.jsonl --overlay translations/hotfix_2611141949/lua_extra.jsonl --out dist/lua_patched_vi.arcx

# 3) kiểm chứng sau khi cài
python tools/verify_deployed_game_data.py
```

Ghi chú:
- `dist/vanilla/data_original_en.arcx` đã chứa chữ Việt, không dùng làm gốc tiếng Anh.
- Bản dịch 2.1.0 (`translations/2.1.0/Van_ban_EN_VI.jsonl` và `translations/hotfix_2611141949/*.jsonl`): các dòng khớp release v1.3.0 trên GitHub đã được chủ dự án duyệt ngày 2026-11-16 (trạng thái `Đã duyệt`, gồm chương 6.5 và 9.5). Đây là duyệt của chủ dự án, **không phải QA ngữ nghĩa độc lập**. Căn cứ và danh sách ID chưa duyệt: `translations/2.1.0/APPROVAL_v1.3.0.json`.
- 53 dòng bảng dữ liệu (Item, Skill, MallPackage, Potential...) từng khác cách dịch với release v1.3.0 đã được đồng bộ `text_vi` theo release rồi duyệt (2026-11-16). 23 dòng `Chờ dịch` còn lại (21 `Item.*.1` + 2 mã màn `ActivityStory.*.4` `BT01`/`BT02`) đã được hoàn tất và qua `LOCALIZATION_QA_REVIEWER` độc lập (`work/subagents/pending_23_20261116_r01/qa_23/REVIEW_23.json`), đồng thời dựng lại `dist/data_patched_vi.arcx` với `--force-overlay translations/hotfix_2611141949/data_extra.jsonl` để đồng bộ `Item.115018.1..115030.1` (`Quán Quân Sinh Tồn Mùa 18..30`). `Van_ban_EN_VI.jsonl`: 5.799 `Đã duyệt`, 33 `Giữ EN`, 0 `Chờ dịch`, 0 `Bản nháp`.
- Các dòng thoại dịch tay (chương 16–19) nằm trong `translations/hotfix_2611141949/` (`story_*.py`, `assemble_pending.py`).
- Một vài script Lua mà bản cũ từng sửa mã tay (dorm/guide) không được mang sang; chỉ chữ được áp lại lên script chính thức.

## Bundle ảnh (texture) cũng phải dựng lại trên bản chính thức

Bundle ảnh Việt hóa ghi đè bundle chính thức cùng tên. Nếu dựng từ bản cũ thì mọi ảnh mà bản mới thêm vào đều mất, và game hiện **banner/tab trắng**
(log game: `load resource failed: Assets/AssetBundles/Icon/Banner/...`). Sự cố thực tế: hotfix 2611141949 thêm 34 ảnh vào 13 bundle (`icon-*`, `ui_big_sprites`).

```powershell
# 1) bundle chính thức của đúng resource version nằm trong game sau khi updater chạy (sao lưu trước khi cài đè), hoặc tải bằng plan.json của StellaResourceTool
# 2) dựng lại: bản chính thức + ảnh Việt hóa (chỉ ghi vào staging/)
.venv\Scripts\python tools\rebuild_texture_bundles_on_official.py --source <thư mục .en.unity3d chính thức> --out staging\bundles_rebuilt_<tag>
# 3) so asset: bundle mới không được thiếu asset nào của bản chính thức, ảnh chưa dịch phải trùng byte với bản chính thức
# 4) cài vào dist + game, cập nhật manifest, zip, SHA256SUMS (không upload)
python tools\apply_rebuilt_texture_bundles.py --staged <thư mục bundle cần thay> --backup backups\pre_texture_fix_<tag> --game-dir <Persistent_Store\AssetBundles>
# 5) upload StellaSora_AssetBundles_VI.zip + patch_manifest.json + SHA256SUMS.txt: docs/RELEASE_ASSET_UPLOAD.md
```

Để trích ảnh của bundle chính thức ra PNG (kèm trạng thái đã dịch/chưa): `tools/export_official_bundle_textures.py`.
Android có bundle riêng (ASTC) và chưa được dựng lại theo hotfix này.
