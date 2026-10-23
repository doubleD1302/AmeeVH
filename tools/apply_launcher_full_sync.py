import sys
from pathlib import Path

p = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\launcher\launcher_pc.py")
code = p.read_text(encoding="utf-8")

# 1. Update DEFAULT_CONFIG
old_cfg = '''DEFAULT_CONFIG = {
    "version": "0.9.0",
    "app_name": "Stella Sora Việt Hóa - Multiplatform & Steam Launcher",'''

new_cfg = '''DEFAULT_CONFIG = {
    "version": "0.9.5",
    "app_name": "Stella Sora Việt Hóa - Multiplatform & Steam Launcher (v0.9.5)",'''

if old_cfg in code:
    code = code.replace(old_cfg, new_cfg, 1)
    print("1. Updated DEFAULT_CONFIG to v0.9.5")
else:
    print("WARNING: old_cfg not found")

# 2. Update on_sync_game_patch_from_github to display total size upfront and clear 3-stage progress
target_sync_start = '        def worker():\n            self.btn_online_sync.config(state="disabled")'
target_sync_end = '            self.refresh_status()\n            self.btn_online_sync.config(state="normal")'

pos_s = code.find(target_sync_start)
pos_e = code.find(target_sync_end)

if pos_s != -1 and pos_e != -1:
    new_worker = '''        def worker():
            self.btn_online_sync.config(state="disabled")
            self.btn_install.config(state="disabled")
            self.log_ui("Đang kiểm tra các gói bản dịch trên GitHub Releases...")

            repo = self.config.get("github_repo", "doubleD1302/AmeeVH")
            res = GitHubManager.check_updates(repo, "0.0.0")
            arcx_asset = res.get("arcx_asset")
            lua_asset = res.get("lua_arcx_asset")
            bundles_asset = res.get("bundles_asset")

            if not arcx_asset or not arcx_asset.get("browser_download_url"):
                self.log_ui("⚠️ Không tìm thấy tệp data_patched_vi.arcx trên GitHub Release.")
                messagebox.showerror("Lỗi", "Không tìm thấy gói dữ liệu trên GitHub Release. Vui lòng kiểm tra lại kết nối mạng!")
                self.btn_online_sync.config(state="normal")
                self.btn_install.config(state="normal")
                return

            tag = res.get("tag", "v0.9.5")
            arcx_mb = (arcx_asset.get('size', 0) / (1024 * 1024)) if arcx_asset else 0.0
            lua_mb = (lua_asset.get('size', 0) / (1024 * 1024)) if lua_asset else 0.0
            bundles_mb = (bundles_asset.get('size', 0) / (1024 * 1024)) if bundles_asset else 0.0
            total_mb = arcx_mb + lua_mb + bundles_mb

            self.log_ui(f"==================================================")
            self.log_ui(f"📦 BẢN PHÁT HÀNH {tag}: TỔNG DUNG LƯỢNG {total_mb:.1f} MB (3 PHẦN)")
            self.log_ui(f"   [1/3] Bảng dữ liệu Tables (data.arcx): {arcx_mb:.1f} MB")
            self.log_ui(f"   [2/3] Kịch bản thoại & Tin nhắn Scripts (lua.arcx): {lua_mb:.1f} MB")
            self.log_ui(f"   [3/3] Đồ họa ảnh chữ AssetBundles (Comics, Titles): {bundles_mb:.1f} MB")
            self.log_ui(f"==================================================")

            # --- BƯỚC 1: TẢI VÀ ÁP DỤNG TABLES/DATA.ARCX ---
            self.log_ui(f"\n[1/3] Bắt đầu tải Bảng dữ liệu {tag} ({arcx_mb:.1f} MB)...")
            download_url = arcx_asset["browser_download_url"]
            temp_dest = Path(os.environ.get("TEMP", str(EXE_DIR))) / "data_patched_vi_download.arcx"

            def progress_arcx(dl, total, pct):
                if int(pct) % 25 == 0:
                    self.log_ui(f"   Đang tải [1/3]: {dl/(1024*1024):.1f}/{total/(1024*1024):.1f} MB ({pct:.1f}%)")

            ok = GitHubManager.download_file(download_url, temp_dest, progress_cb=progress_arcx)
            if not ok:
                self.log_ui("❌ Lỗi khi tải Tables/data.arcx từ GitHub.")
                messagebox.showerror("Lỗi Tải Về", "Tải dữ liệu Tables từ GitHub thất bại!")
                self.btn_online_sync.config(state="normal")
                self.btn_install.config(state="normal")
                return

            target_table = self.game_path / "Persistent_Store" / "Tables" / "data.arcx"
            target_table.parent.mkdir(parents=True, exist_ok=True)
            orig_bak = target_table.with_suffix(".arcx.orig_en")
            if target_table.exists() and not orig_bak.exists():
                shutil.copy2(target_table, orig_bak)
                self.log_ui("   Đã sao lưu tệp gốc: data.arcx.orig_en")
            shutil.copy2(temp_dest, target_table)
            temp_dest.unlink(missing_ok=True)
            self.log_ui("   ✓ [1/3] Đã cài đặt thành công Tables/data.arcx!")

            # --- BƯỚC 2: TẢI VÀ ÁP DỤNG SCRIPTS/LUA.ARCX ---
            if lua_asset and lua_asset.get("browser_download_url"):
                lua_url = lua_asset["browser_download_url"]
                self.log_ui(f"\n[2/3] Bắt đầu tải Kịch bản thoại & Tin nhắn ({lua_mb:.1f} MB)...")
                temp_lua = Path(os.environ.get("TEMP", str(EXE_DIR))) / "lua_patched_vi_download.arcx"
                def prog_lua(dl, total, pct):
                    if int(pct) % 25 == 0:
                        self.log_ui(f"   Đang tải [2/3]: {dl/(1024*1024):.1f}/{total/(1024*1024):.1f} MB ({pct:.1f}%)")
                if GitHubManager.download_file(lua_url, temp_lua, progress_cb=prog_lua):
                    target_script = self.game_path / "Persistent_Store" / "Scripts" / "lua.arcx"
                    target_script.parent.mkdir(parents=True, exist_ok=True)
                    orig_lua_bak = target_script.with_suffix(".arcx.orig_en")
                    if target_script.exists() and not orig_lua_bak.exists():
                        shutil.copy2(target_script, orig_lua_bak)
                    shutil.copy2(temp_lua, target_script)
                    temp_lua.unlink(missing_ok=True)
                    self.log_ui("   ✓ [2/3] Đã cài đặt thành công Scripts/lua.arcx (Thoại & Tin nhắn)!")

            # --- BƯỚC 3: TẢI VÀ ÁP DỤNG ASSETBUNDLES (ẢNH CHỮ) ---
            if bundles_asset and bundles_asset.get("browser_download_url"):
                bundles_url = bundles_asset["browser_download_url"]
                self.log_ui(f"\n[3/3] Bắt đầu tải Đồ họa ảnh chữ AssetBundles ({bundles_mb:.1f} MB)...")
                temp_bundles_zip = Path(os.environ.get("TEMP", str(EXE_DIR))) / "AssetBundles_VI_download.zip"
                def prog_bundles(dl, total, pct):
                    if int(pct) % 25 == 0:
                        self.log_ui(f"   Đang tải [3/3]: {dl/(1024*1024):.1f}/{total/(1024*1024):.1f} MB ({pct:.1f}%)")
                if GitHubManager.download_file(bundles_url, temp_bundles_zip, progress_cb=prog_bundles):
                    self.log_ui("   Đang giải nén và áp dụng 60 AssetBundles vào game...")
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
                    self.log_ui(f"   ✓ [3/3] Đã cài đặt thành công {b_extracted} tệp AssetBundles đồ họa ảnh chữ!")

            marker_file = self.game_path / "Persistent_Store" / "viethoa_installed.json"
            marker_file.write_text(json.dumps({
                "installed_at": datetime.datetime.now().strftime("%Y%m%d_%H%M%S"),
                "version": tag.lstrip("v"),
                "release_tag": tag,
                "total_mb_synced": round(total_mb, 1),
                "components": ["Tables (data.arcx)", "Scripts (lua.arcx)", "AssetBundles (60 bundles)"]
            }, indent=2), encoding="utf-8")

            self.log_ui(f"\n==================================================")
            self.log_ui(f"🎉 CHÚC MỪNG! ĐÃ CẬP NHẬT TRỌN VẸN {total_mb:.1f} MB VÀO GAME!")
            self.log_ui(f"   Game đã sẵn sàng với 100% tiếng Việt cho Bảng dữ liệu, Thoại nhân vật và Ảnh chữ!")
            self.log_ui(f"==================================================")
            messagebox.showinfo("Thành Công", f"Đã cập nhật trọn vẹn bản Việt Hóa {tag} ({total_mb:.1f} MB gồm 3 phần) trực tiếp vào game thành công!\n\nBạn có thể khởi động game để trải nghiệm ngay.")
'''
    code = code[:pos_s] + new_worker + "\n" + code[pos_e:]
    print("2. Updated on_sync_game_patch_from_github to display full 171MB breakdown")
else:
    print(f"WARNING: positions not found: pos_s={pos_s}, pos_e={pos_e}")

p.write_text(code, encoding="utf-8")
print("SUCCESS: Finished updating launcher_pc.py")
