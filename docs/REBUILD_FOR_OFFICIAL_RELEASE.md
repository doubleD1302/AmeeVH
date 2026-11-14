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
- Bản nháp 2.1.0 (`translations/2.1.0/Van_ban_EN_VI.jsonl`) chưa được QA ngữ nghĩa độc lập.
- Các dòng thoại dịch tay (chương 16–19) nằm trong `translations/hotfix_2611141949/` (`story_*.py`, `assemble_pending.py`).
- Một vài script Lua mà bản cũ từng sửa mã tay (dorm/guide) không được mang sang; chỉ chữ được áp lại lên script chính thức.
