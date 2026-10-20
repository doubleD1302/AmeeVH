# -*- coding: utf-8 -*-
"""
Update launcher_pc.py to v0.8.5:
- Adds dual-archive support: Tables/data.arcx (Core UI, tables) AND Scripts/lua.arcx (Dialogue, phone messages)
- Updates GitHubManager to download both archives when syncing online
- Bumps version to 0.8.5
"""

import re
from pathlib import Path

LAUNCHER_PATH = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\launcher\launcher_pc.py")
content = LAUNCHER_PATH.read_text(encoding="utf-8")

# 1. Bump version
content = content.replace('"version": "0.8.0"', '"version": "0.8.5"')

# 2. Add script_rel and patched_lua_arcx
old_targets = '''            table_rel = "Persistent_Store/Tables/data.arcx"

            # Source batch proposals
            batches_dir = BASE_DIR / "work" / "batches"
            batch_files = {
                "Persistent_Store/Videos/Prologue-Prologue_P4_JPVA_FP_EN.srt": batches_dir / "SRT001_JPVA.json",
                "Persistent_Store/Videos/Prologue-Prologue_P4_CNVA_FP_EN.srt": batches_dir / "SRT002_CNVA.json",
                "Persistent_Store/Videos/CH04ED-CH04ED_EN.srt": batches_dir / "SRT003_CH04ED.json",
                "Persistent_Store/Videos/CH06ED-CH06ED_EN.srt": batches_dir / "SRT004_CH06ED.json",
            }
            patched_arcx = BASE_DIR / "dist" / "data_patched_vi.arcx"
            if not patched_arcx.exists():
                patched_arcx = BASE_DIR / "work" / "research" / "data_patched_vi.arcx"'''

new_targets = '''            table_rel = "Persistent_Store/Tables/data.arcx"
            script_rel = "Persistent_Store/Scripts/lua.arcx"

            # Source batch proposals
            batches_dir = BASE_DIR / "work" / "batches"
            batch_files = {
                "Persistent_Store/Videos/Prologue-Prologue_P4_JPVA_FP_EN.srt": batches_dir / "SRT001_JPVA.json",
                "Persistent_Store/Videos/Prologue-Prologue_P4_CNVA_FP_EN.srt": batches_dir / "SRT002_CNVA.json",
                "Persistent_Store/Videos/CH04ED-CH04ED_EN.srt": batches_dir / "SRT003_CH04ED.json",
                "Persistent_Store/Videos/CH06ED-CH06ED_EN.srt": batches_dir / "SRT004_CH06ED.json",
            }
            patched_arcx = BASE_DIR / "dist" / "data_patched_vi.arcx"
            if not patched_arcx.exists():
                patched_arcx = BASE_DIR / "work" / "research" / "data_patched_vi.arcx"

            patched_lua_arcx = BASE_DIR / "dist" / "lua_patched_vi.arcx"
            if not patched_lua_arcx.exists():
                patched_lua_arcx = BASE_DIR / "work" / "research" / "lua_patched_vi.arcx"'''

assert old_targets in content, "Failed to match old_targets"
content = content.replace(old_targets, new_targets, 1)

# 3. Add backup of lua.arcx
old_backup = '''            # Backup table archive if game table and patched arcx exist
            orig_table = game_path / table_rel
            if patched_arcx.exists() and orig_table.exists():
                orig_hash = sha256_file(orig_table)
                bak_file = run_backup_dir / table_rel.replace("/", "_")
                shutil.copy2(orig_table, bak_file)
                backup_manifest["files"].append({
                    "relative_path": table_rel,
                    "backup_file": bak_file.name,
                    "original_sha256": orig_hash,
                    "size": orig_table.stat().st_size
                })
                log(f"   Đã sao lưu: {orig_table.name} (SHA: {orig_hash[:8]}...)")'''

new_backup = '''            # Backup table archive if game table and patched arcx exist
            orig_table = game_path / table_rel
            if patched_arcx.exists() and orig_table.exists():
                orig_hash = sha256_file(orig_table)
                bak_file = run_backup_dir / table_rel.replace("/", "_")
                shutil.copy2(orig_table, bak_file)
                backup_manifest["files"].append({
                    "relative_path": table_rel,
                    "backup_file": bak_file.name,
                    "original_sha256": orig_hash,
                    "size": orig_table.stat().st_size
                })
                log(f"   Đã sao lưu: {orig_table.name} (Giao diện Core UI ArcX)")

            # Backup lua archive if game script and patched lua arcx exist
            orig_script = game_path / script_rel
            if patched_lua_arcx.exists() and orig_script.exists():
                orig_hash = sha256_file(orig_script)
                bak_file = run_backup_dir / script_rel.replace("/", "_")
                shutil.copy2(orig_script, bak_file)
                backup_manifest["files"].append({
                    "relative_path": script_rel,
                    "backup_file": bak_file.name,
                    "original_sha256": orig_hash,
                    "size": orig_script.stat().st_size
                })
                log(f"   Đã sao lưu: {orig_script.name} (Kịch bản thoại & Tin nhắn ArcX)")'''

assert old_backup in content, "Failed to match old_backup"
content = content.replace(old_backup, new_backup, 1)

# 4. Add install of lua.arcx
old_install = '''            # Install Core UI table archive
            if patched_arcx.exists() and orig_table.exists():
                temp_table = orig_table.with_suffix(".tmp_patch")
                shutil.copy2(patched_arcx, temp_table)
                temp_table.replace(orig_table)
                installed_count += 1
                installed_files.append(table_rel)
                log(f"   ✓ Đã cài đặt thành công: {orig_table.name} (Giao diện Core UI ArcX)")'''

new_install = '''            # Install Core UI table archive
            if patched_arcx.exists() and orig_table.exists():
                temp_table = orig_table.with_suffix(".tmp_patch")
                shutil.copy2(patched_arcx, temp_table)
                temp_table.replace(orig_table)
                installed_count += 1
                installed_files.append(table_rel)
                log(f"   ✓ Đã cài đặt thành công: {orig_table.name} (Giao diện Core UI ArcX)")

            # Install Dialogue & Phone script archive
            if patched_lua_arcx.exists() and orig_script.exists():
                temp_script = orig_script.with_suffix(".tmp_patch")
                shutil.copy2(patched_lua_arcx, temp_script)
                temp_script.replace(orig_script)
                installed_count += 1
                installed_files.append(script_rel)
                log(f"   ✓ Đã cài đặt thành công: {orig_script.name} (Kịch bản thoại & Tin nhắn Lua ArcX)")'''

assert old_install in content, "Failed to match old_install"
content = content.replace(old_install, new_install, 1)

# 5. Add lua_arcx_asset to GitHubManager.check_updates
old_assets = '''        assets = rel_data.get("assets", [])
        launcher_asset = next((a for a in assets if "Launcher.exe" in a.get("name", "")), None)
        zip_asset = next((a for a in assets if a.get("name", "").endswith(".zip")), None)
        apk_asset = next((a for a in assets if a.get("name", "").endswith(".apk")), None)
        arcx_asset = next((a for a in assets if "data_patched_vi.arcx" in a.get("name", "")), None)'''

new_assets = '''        assets = rel_data.get("assets", [])
        launcher_asset = next((a for a in assets if "Launcher.exe" in a.get("name", "")), None)
        zip_asset = next((a for a in assets if a.get("name", "").endswith(".zip")), None)
        apk_asset = next((a for a in assets if a.get("name", "").endswith(".apk")), None)
        arcx_asset = next((a for a in assets if "data_patched_vi.arcx" in a.get("name", "")), None)
        lua_arcx_asset = next((a for a in assets if "lua_patched_vi.arcx" in a.get("name", "") or "lua.arcx" in a.get("name", "")), None)'''

assert old_assets in content, "Failed to match old_assets"
content = content.replace(old_assets, new_assets, 1)

old_return = '''            "apk_asset": apk_asset,
            "arcx_asset": arcx_asset,'''

new_return = '''            "apk_asset": apk_asset,
            "arcx_asset": arcx_asset,
            "lua_arcx_asset": lua_arcx_asset,'''

assert old_return in content, "Failed to match old_return"
content = content.replace(old_return, new_return, 1)

# 6. Add lua.arcx download in on_sync_game_patch_from_github
old_sync = '''            shutil.copy2(temp_dest, target_table)
            temp_dest.unlink(missing_ok=True)

            marker_file = self.game_path / "Persistent_Store" / "viethoa_installed.json"'''

new_sync = '''            shutil.copy2(temp_dest, target_table)
            temp_dest.unlink(missing_ok=True)
            self.log_ui("   ✓ Đã cập nhật xong Tables/data.arcx")

            # Check and sync lua_patched_vi.arcx if available
            lua_asset = res.get("lua_arcx_asset")
            if lua_asset and lua_asset.get("browser_download_url"):
                lua_url = lua_asset["browser_download_url"]
                lua_mb = lua_asset.get('size', 0) / (1024 * 1024)
                self.log_ui(f"Bắt đầu tải gói kịch bản thoại & tin nhắn ({lua_mb:.1f} MB)...")
                temp_lua = Path(os.environ.get("TEMP", str(EXE_DIR))) / "lua_patched_vi_download.arcx"
                if GitHubManager.download_file(lua_url, temp_lua):
                    target_script = self.game_path / "Persistent_Store" / "Scripts" / "lua.arcx"
                    target_script.parent.mkdir(parents=True, exist_ok=True)
                    orig_lua_bak = target_script.with_suffix(".arcx.orig_en")
                    if target_script.exists() and not orig_lua_bak.exists():
                        shutil.copy2(target_script, orig_lua_bak)
                    shutil.copy2(temp_lua, target_script)
                    temp_lua.unlink(missing_ok=True)
                    self.log_ui("   ✓ Đã cập nhật xong Scripts/lua.arcx (Thoại & Tin nhắn)")

            marker_file = self.game_path / "Persistent_Store" / "viethoa_installed.json"'''

assert old_sync in content, "Failed to match old_sync"
content = content.replace(old_sync, new_sync, 1)

LAUNCHER_PATH.write_text(content, encoding="utf-8")
print("Successfully upgraded launcher_pc.py to v0.8.5 with full lua.arcx support!")
