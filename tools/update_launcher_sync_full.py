import sys
from pathlib import Path

lp = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\launcher\launcher_pc.py")
content = lp.read_text(encoding="utf-8")

# 1. Update check_updates to detect bundles_asset
target_check = 'lua_arcx_asset = next((a for a in assets if "lua_patched_vi.arcx" in a.get("name", "") or "lua.arcx" in a.get("name", "")), None)'
replacement_check = '''lua_arcx_asset = next((a for a in assets if "lua_patched_vi.arcx" in a.get("name", "") or "lua.arcx" in a.get("name", "")), None)
        bundles_asset = next((a for a in assets if "AssetBundles_VI" in a.get("name", "") or "AssetBundles" in a.get("name", "")), None)'''

if target_check in content:
    content = content.replace(target_check, replacement_check, 1)
    print("1. Added bundles_asset detection in check_updates")
else:
    print("ERROR: target_check not found")

# Add "bundles_asset": bundles_asset to return dict
target_dict = '"lua_arcx_asset": lua_arcx_asset,'
replacement_dict = '''"lua_arcx_asset": lua_arcx_asset,
            "bundles_asset": bundles_asset,'''

if target_dict in content:
    content = content.replace(target_dict, replacement_dict, 1)
    print("2. Added bundles_asset to return dict")
else:
    print("ERROR: target_dict not found")

# 2. Update on_sync_game_patch_from_github to download lua and bundles with progress
target_sync_start = '            # Check and sync lua_patched_vi.arcx if available'
target_sync_end = '            marker_file = self.game_path / "Persistent_Store" / "viethoa_installed.json"'

pos_start = content.find(target_sync_start)
pos_end = content.find(target_sync_end)

if pos_start != -1 and pos_end != -1:
    new_sync_code = '''            # 2. Check and sync lua_patched_vi.arcx if available
            lua_asset = res.get("lua_arcx_asset")
            if lua_asset and lua_asset.get("browser_download_url"):
                lua_url = lua_asset["browser_download_url"]
                lua_mb = lua_asset.get('size', 0) / (1024 * 1024)
                self.log_ui(f"Bắt đầu tải gói kịch bản thoại & tin nhắn ({lua_mb:.1f} MB)...")
                temp_lua = Path(os.environ.get("TEMP", str(EXE_DIR))) / "lua_patched_vi_download.arcx"
                def prog_lua(dl, total, pct):
                    if int(pct) % 20 == 0:
                        self.log_ui(f"Đang tải Thoại & Tin nhắn: {dl/(1024*1024):.1f}/{total/(1024*1024):.1f} MB ({pct:.1f}%)")
                if GitHubManager.download_file(lua_url, temp_lua, progress_cb=prog_lua):
                    target_script = self.game_path / "Persistent_Store" / "Scripts" / "lua.arcx"
                    target_script.parent.mkdir(parents=True, exist_ok=True)
                    orig_lua_bak = target_script.with_suffix(".arcx.orig_en")
                    if target_script.exists() and not orig_lua_bak.exists():
                        shutil.copy2(target_script, orig_lua_bak)
                    shutil.copy2(temp_lua, target_script)
                    temp_lua.unlink(missing_ok=True)
                    self.log_ui("   ✓ Đã cập nhật xong Scripts/lua.arcx (Thoại & Tin nhắn)")

            # 3. Check and sync AssetBundles (Textures: Comics, Titles, Logos)
            bundles_asset = res.get("bundles_asset")
            if bundles_asset and bundles_asset.get("browser_download_url"):
                bundles_url = bundles_asset["browser_download_url"]
                bundles_mb = bundles_asset.get('size', 0) / (1024 * 1024)
                self.log_ui(f"Bắt đầu tải gói đồ họa AssetBundles ảnh chữ ({bundles_mb:.1f} MB)...")
                temp_bundles_zip = Path(os.environ.get("TEMP", str(EXE_DIR))) / "AssetBundles_VI_download.zip"
                def prog_bundles(dl, total, pct):
                    if int(pct) % 20 == 0:
                        self.log_ui(f"Đang tải AssetBundles: {dl/(1024*1024):.1f}/{total/(1024*1024):.1f} MB ({pct:.1f}%)")
                if GitHubManager.download_file(bundles_url, temp_bundles_zip, progress_cb=prog_bundles):
                    self.log_ui("✓ Đã tải xong gói AssetBundles. Đang giải nén và cài đặt vào game...")
                    target_bundles_dir = self.game_path / "Persistent_Store" / "AssetBundles"
                    target_bundles_dir.mkdir(parents=True, exist_ok=True)
                    b_extracted = 0
                    with zipfile.ZipFile(temp_bundles_zip, "r") as zf:
                        for member in zf.infolist():
                            if member.filename.endswith(".en.unity3d"):
                                fname = Path(member.filename).name
                                dest_f = target_bundles_dir / fname
                                orig_bak = dest_f.with_suffix(".en.unity3d.orig_en")
                                if dest_f.exists() and not orig_bak.exists():
                                    shutil.copy2(dest_f, orig_bak)
                                with zf.open(member) as s_fp, open(dest_f, "wb") as d_fp:
                                    shutil.copyfileobj(s_fp, d_fp)
                                b_extracted += 1
                    temp_bundles_zip.unlink(missing_ok=True)
                    self.log_ui(f"   ✓ Đã cập nhật xong {b_extracted} tệp AssetBundles đồ họa ảnh chữ (Truyện tranh, Danh hiệu, Tiêu đề)")

'''
    content = content[:pos_start] + new_sync_code + content[pos_end:]
    print("3. Replaced on_sync_game_patch_from_github sync block")
else:
    print(f"ERROR: pos_start={pos_start}, pos_end={pos_end}")

lp.write_text(content, encoding="utf-8")
print("SUCCESS: Updated launcher_pc.py")
