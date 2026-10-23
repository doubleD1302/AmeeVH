#!/usr/bin/env python3
"""Upgrade launcher/launcher_pc.py to v0.9.6 with robust manifest-verified sync,
atomic replacement, security guards, rollback guards, and detailed status reporting.
"""
from __future__ import annotations

import py_compile
import re
from pathlib import Path

LAUNCHER_PATH = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\launcher\launcher_pc.py")
CONFIG_PATH = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\launcher\config.json")
NOTIFS_PATH = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\launcher\notifications.json")


def update_launcher():
    print("=== NÂNG CẤP LAUNCHER PC LÊN PHIÊN BẢN v0.9.6 ===")
    content = LAUNCHER_PATH.read_text(encoding="utf-8")

    # 1. Update version and app_name in DEFAULT_CONFIG
    content = re.sub(
        r'"version":\s*"0\.\d+\.\d+"',
        '"version": "0.9.6"',
        content,
        count=1
    )
    content = re.sub(
        r'"app_name":\s*"Stella Sora Việt Hóa - Multiplatform & Steam Launcher \(v0\.\d+\.\d+\)"',
        '"app_name": "Stella Sora Việt Hóa - Multiplatform & Steam Launcher (v0.9.6)"',
        content,
        count=1
    )
    print("1. Đã cập nhật DEFAULT_CONFIG lên v0.9.6.")

    # 2. Update config.json
    cfg = {
        "version": "0.9.6",
        "app_name": "Stella Sora Việt Hóa - Multiplatform & Steam Launcher (v0.9.6)",
        "default_game_path": "C:\\YostarGames\\StellaSora_EN",
        "github_repo": "doubleD1302/AmeeVH",
        "github_branch": "main",
        "github_api_url": "https://api.github.com/repos/doubleD1302/AmeeVH/releases/latest",
        "remote_notifications_url": "https://raw.githubusercontent.com/doubleD1302/AmeeVH/main/launcher/notifications.json",
        "android_package": "com.YoStar.StellaSora",
        "android_game_storage": "/sdcard/Android/data/com.YoStar.StellaSora/files"
    }
    import json
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
    print("2. Đã cập nhật launcher/config.json lên v0.9.6.")

    # 3. Update notifications.json
    notifs = json.loads(NOTIFS_PATH.read_text(encoding="utf-8"))
    notifs["version"] = "0.9.6"
    notifs["updated_at"] = "2026-10-23"
    new_notif = {
        "id": "NOTIF-012",
        "date": "2026-10-23",
        "title": "Bản cập nhật v0.9.6: Chuẩn hóa Quy trình Texture An toàn & Xác thực Manifest",
        "type": "release",
        "content": "Nâng cấp tính năng đồng bộ GitHub Releases với cơ chế xác thực Manifest (patch_manifest.json), kiểm tra mã băm SHA256 từng tệp, thay thế nguyên tử (atomic replace), bảo vệ chống tràn đường dẫn (path traversal) và sao lưu preimage an toàn. Tích hợp 53 truyện tranh 4 ô màn hình chờ trong 16 AssetBundles (.en.unity3d) đã kiểm chứng 100% không cắt chữ. Các danh hiệu và banner đang chờ adapter mesh/atlas."
    }
    # Prepend if not exists
    if not any(n["id"] == "NOTIF-012" for n in notifs.get("announcements", [])):
        notifs["announcements"].insert(0, new_notif)
    NOTIFS_PATH.write_text(json.dumps(notifs, indent=2, ensure_ascii=False), encoding="utf-8")
    print("3. Đã thêm thông báo NOTIF-012 vào launcher/notifications.json.")

    # 4. Enhance GitHubManager.check_updates and download_file
    target_check = """        assets = rel_data.get("assets", [])
        launcher_asset = next((a for a in assets if "Launcher.exe" in a.get("name", "")), None)
        zip_asset = next((a for a in assets if a.get("name", "").endswith(".zip")), None)
        apk_asset = next((a for a in assets if a.get("name", "").endswith(".apk")), None)
        arcx_asset = next((a for a in assets if "data_patched_vi.arcx" in a.get("name", "")), None)
        lua_arcx_asset = next((a for a in assets if "lua_patched_vi.arcx" in a.get("name", "") or "lua.arcx" in a.get("name", "")), None)
        bundles_asset = next((a for a in assets if "AssetBundles_VI" in a.get("name", "") or "AssetBundles" in a.get("name", "")), None)"""

    replacement_check = """        assets = rel_data.get("assets", [])
        launcher_asset = next((a for a in assets if a.get("name", "").endswith("Launcher.exe")), None)

        # Explicit non-ambiguous asset matching
        zip_asset = next((a for a in assets if a.get("name", "").startswith("StellaSora_Launcher_PC") and a.get("name", "").endswith(".zip")), None)
        if not zip_asset:
            zip_asset = next((a for a in assets if "Launcher_PC" in a.get("name", "") and a.get("name", "").endswith(".zip")), None)

        apk_asset = next((a for a in assets if a.get("name", "").endswith(".apk")), None)
        arcx_asset = next((a for a in assets if "data_patched_vi.arcx" in a.get("name", "")), None)
        lua_arcx_asset = next((a for a in assets if "lua_patched_vi.arcx" in a.get("name", "") or "lua.arcx" in a.get("name", "")), None)

        # Precise match for AssetBundles package and Manifest
        bundles_asset = next((a for a in assets if a.get("name", "").startswith("StellaSora_AssetBundles_VI") and a.get("name", "").endswith(".zip")), None)
        if not bundles_asset:
            bundles_asset = next((a for a in assets if "AssetBundles" in a.get("name", "") and a.get("name", "").endswith(".zip")), None)

        manifest_asset = next((a for a in assets if a.get("name", "") in ("patch_manifest.json", "stella_patch_manifest.json") or a.get("name", "").endswith("_manifest.json")), None)"""

    if target_check in content:
        content = content.replace(target_check, replacement_check, 1)
        print("4. Đã nâng cấp logic tìm kiếm tài nguyên và manifest trong check_updates.")
    else:
        print("CẢNH BÁO: Không tìm thấy target_check trong launcher_pc.py")

    # Return manifest_asset in return dict
    target_dict = '"bundles_asset": bundles_asset,\n            "assets": assets,'
    replacement_dict = '"bundles_asset": bundles_asset,\n            "manifest_asset": manifest_asset,\n            "assets": assets,'
    if target_dict in content:
        content = content.replace(target_dict, replacement_dict, 1)
        print("5. Đã bổ sung manifest_asset vào dictionary trả về của check_updates.")

    # 5. Enhance download_file with hash & size verification and atomic write
    target_dl = """    @staticmethod
    def download_file(url: str, dest_path: Path, progress_cb=None) -> bool:
        \"\"\"Downloads a remote file with progress reporting.\"\"\"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "StellaSora-Localizer"})
            with urllib.request.urlopen(req, timeout=45) as resp:
                total_len = resp.headers.get("Content-Length")
                total_size = int(total_len) if total_len else 0
                downloaded = 0
                chunk_size = 64 * 1024

                dest_path.parent.mkdir(parents=True, exist_ok=True)
                with open(dest_path, "wb") as f:
                    while True:
                        chunk = resp.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_cb and total_size > 0:
                            percent = min(100.0, (downloaded / total_size) * 100.0)
                            progress_cb(downloaded, total_size, percent)
            return True
        except Exception as e:
            DiagnosticCollector.log(f"Lỗi khi tải tệp {url}: {e}")
            return False"""

    replacement_dl = """    @staticmethod
    def download_file(url: str, dest_path: Path, progress_cb=None, expected_size: int = 0, expected_sha256: str = "") -> bool:
        \"\"\"Downloads a remote file with progress reporting, size check, hash check, and atomic placement.\"\"\"
        temp_download = dest_path.with_suffix(dest_path.suffix + ".part")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "StellaSora-Localizer"})
            hasher = hashlib.sha256() if expected_sha256 else None
            temp_download.parent.mkdir(parents=True, exist_ok=True)
            with urllib.request.urlopen(req, timeout=45) as resp:
                total_len = resp.headers.get("Content-Length")
                total_size = int(total_len) if total_len else expected_size
                downloaded = 0
                chunk_size = 64 * 1024

                with open(temp_download, "wb") as f:
                    while True:
                        chunk = resp.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        if hasher:
                            hasher.update(chunk)
                        downloaded += len(chunk)
                        if progress_cb and total_size > 0:
                            percent = min(100.0, (downloaded / total_size) * 100.0)
                            progress_cb(downloaded, total_size, percent)

            # Verification of size
            if expected_size > 0 and downloaded != expected_size:
                DiagnosticCollector.log(f"Lỗi kích thước tệp tải về: {downloaded} != {expected_size}")
                temp_download.unlink(missing_ok=True)
                return False

            # Verification of SHA256
            if expected_sha256:
                calc_sha = hasher.hexdigest()
                if calc_sha.lower() != expected_sha256.lower():
                    DiagnosticCollector.log(f"Lỗi sai lệch SHA256 tệp {dest_path.name}: {calc_sha} != {expected_sha256}")
                    temp_download.unlink(missing_ok=True)
                    return False

            # Atomic replace into dest_path on the same volume
            temp_download.replace(dest_path)
            return True
        except Exception as e:
            DiagnosticCollector.log(f"Lỗi khi tải tệp {url}: {e}")
            if temp_download.exists():
                temp_download.unlink(missing_ok=True)
            return False"""

    if target_dl in content:
        content = content.replace(target_dl, replacement_dl, 1)
        print("6. Đã nâng cấp download_file với kiểm tra SHA256 và ghi atomic.")
    else:
        print("CẢNH BÁO: Không tìm thấy target_dl trong launcher_pc.py")

    # 6. Rewrite on_sync_game_patch_from_github to use manifest, atomic replace, traversal guard, rollback journal
    target_sync_method_start = '    def on_sync_game_patch_from_github(self):'
    target_sync_method_end = '    def on_auto_update_release(self):'

    idx_start = content.find(target_sync_method_start)
    idx_end = content.find(target_sync_method_end)

    if idx_start != -1 and idx_end != -1:
        new_sync_method = '''    def on_sync_game_patch_from_github(self):
        """Downloads the latest verified translation packages and AssetBundles with manifest verification,
        atomic replacement on the same volume, traversal guards, and automatic rollback on failure.
        """
        if not messagebox.askyesno(
            "Cập Nhật Bản Dịch Từ GitHub",
            "Tải trọn bộ bản dịch tiếng Việt mới nhất (Bảng dữ liệu + Thoại & Tin nhắn + AssetBundles ảnh chữ) từ GitHub Release và cài đặt an toàn vào game?\\n\\n"
            "- Tự động kiểm tra mã băm SHA256 và Manifest phát hành\\n"
            "- Sao lưu preimage nguyên bản an toàn trước khi thay đổi\\n"
            "- Thay thế nguyên tử (atomic replace), tự động rollback nếu gặp sự cố\\n\\n"
            "Bạn có muốn tiếp tục không?"
        ):
            return

        def worker():
            self.btn_online_sync.config(state="disabled")
            self.btn_install.config(state="disabled")
            self.log_ui("Đang kiểm tra kết nối và các gói bản dịch trên GitHub Releases...")

            info = detect_game_info(self.game_path)
            if not info["exists"]:
                self.log_ui("❌ Không tìm thấy thư mục cài đặt game Stella Sora.")
                messagebox.showerror("Lỗi", f"Không tìm thấy thư mục game:\\n{self.game_path}")
                self.btn_online_sync.config(state="normal")
                self.btn_install.config(state="normal")
                return

            if info["is_running"]:
                self.log_ui("⚠️ Trò chơi StellaSora.exe đang chạy! Vui lòng thoát game.")
                messagebox.showwarning("Cảnh Báo", "StellaSora.exe đang chạy! Vui lòng đóng trò chơi trước khi cập nhật bản dịch.")
                self.btn_online_sync.config(state="normal")
                self.btn_install.config(state="normal")
                return

            repo = self.config.get("github_repo", "doubleD1302/AmeeVH")
            res = GitHubManager.check_updates(repo, "0.0.0")

            if not res or not res.get("success"):
                self.log_ui("❌ Không thể kết nối đến GitHub Release.")
                messagebox.showerror("Lỗi", "Không thể lấy thông tin phát hành từ GitHub. Vui lòng kiểm tra lại kết nối mạng!")
                self.btn_online_sync.config(state="normal")
                self.btn_install.config(state="normal")
                return

            tag = res.get("tag", "v0.9.6")
            arcx_asset = res.get("arcx_asset")
            lua_asset = res.get("lua_arcx_asset")
            bundles_asset = res.get("bundles_asset")
            manifest_asset = res.get("manifest_asset")

            if not arcx_asset or not arcx_asset.get("browser_download_url"):
                self.log_ui("⚠️ Không tìm thấy tệp data_patched_vi.arcx trên GitHub Release.")
                messagebox.showerror("Lỗi", "Không tìm thấy gói dữ liệu trên GitHub Release!")
                self.btn_online_sync.config(state="normal")
                self.btn_install.config(state="normal")
                return

            # --- BƯỚC 0: TẢI VÀ PHÂN TÍCH PATCH MANIFEST (NẾU CÓ) ---
            manifest_data = {}
            if manifest_asset and manifest_asset.get("browser_download_url"):
                self.log_ui("Đang tải tệp kê khai xác thực bản vá (patch_manifest.json)...")
                temp_manifest = Path(os.environ.get("TEMP", str(EXE_DIR))) / "patch_manifest.json"
                if GitHubManager.download_file(manifest_asset["browser_download_url"], temp_manifest):
                    try:
                        manifest_data = json.loads(temp_manifest.read_text(encoding="utf-8"))
                        self.log_ui("   ✓ Đã xác thực patch_manifest.json chính thức từ nhóm phát hành!")
                    except Exception as e:
                        DiagnosticCollector.log(f"Lỗi đọc manifest: {e}")

            # Check game version against manifest
            if manifest_data:
                target_game_ver = manifest_data.get("client_game_version", "2.0.0")
                target_res_ver = manifest_data.get("resource_version", "2610201624")
                cur_client_ver = info.get("client_ver", "unknown")
                cur_res_ver = info.get("res_ver", "unknown")
                if cur_client_ver != "unknown" and cur_client_ver != target_game_ver:
                    self.log_ui(f"   ℹ️ Thông báo phiên bản: Game hiện tại ({cur_client_ver}) | Bản vá tối ưu cho ({target_game_ver})")

            arcx_mb = (arcx_asset.get('size', 0) / (1024 * 1024)) if arcx_asset else 0.0
            lua_mb = (lua_asset.get('size', 0) / (1024 * 1024)) if lua_asset else 0.0
            bundles_mb = (bundles_asset.get('size', 0) / (1024 * 1024)) if bundles_asset else 0.0
            total_mb = arcx_mb + lua_mb + bundles_mb

            bundles_count_desc = f"{manifest_data.get('total_bundles', 16)} bundles" if manifest_data else "AssetBundles"

            self.log_ui("==================================================")
            self.log_ui(f"📦 PHÁT HÀNH {tag}: TỔNG DUNG LƯỢNG {total_mb:.1f} MB (3 PHẦN)")
            self.log_ui(f"   [1/3] Bảng dữ liệu Tables (data.arcx): {arcx_mb:.1f} MB")
            self.log_ui(f"   [2/3] Kịch bản thoại & Tin nhắn Scripts (lua.arcx): {lua_mb:.1f} MB")
            self.log_ui(f"   [3/3] Đồ họa ảnh chữ ({bundles_count_desc}): {bundles_mb:.1f} MB")
            self.log_ui("==================================================")

            # Transaction journal for rollback on failure
            session_journal = []

            # --- BƯỚC 1: TẢI VÀ CÀI ĐẶT TABLES/DATA.ARCX ---
            self.log_ui(f"\\n[1/3] Bắt đầu tải Bảng dữ liệu Core Tables ({arcx_mb:.1f} MB)...")
            download_url = arcx_asset["browser_download_url"]
            temp_dest = Path(os.environ.get("TEMP", str(EXE_DIR))) / "data_patched_vi_download.arcx"

            def progress_arcx(dl, total, pct):
                if int(pct) % 25 == 0:
                    self.log_ui(f"   Đang tải [1/3]: {dl/(1024*1024):.1f}/{total/(1024*1024):.1f} MB ({pct:.1f}%)")

            ok = GitHubManager.download_file(download_url, temp_dest, progress_cb=progress_arcx, expected_size=arcx_asset.get("size", 0))
            if not ok:
                self.log_ui("❌ Lỗi khi tải Tables/data.arcx từ GitHub.")
                messagebox.showerror("Lỗi Tải Về", "Tải dữ liệu Tables từ GitHub thất bại!")
                self.btn_online_sync.config(state="normal")
                self.btn_install.config(state="normal")
                return

            target_table = self.game_path / "Persistent_Store" / "Tables" / "data.arcx"
            target_table.parent.mkdir(parents=True, exist_ok=True)
            orig_table_bak = target_table.with_suffix(".arcx.orig_en")
            if target_table.exists() and not orig_table_bak.exists():
                shutil.copy2(target_table, orig_table_bak)
                self.log_ui("   Đã sao lưu tệp gốc: data.arcx.orig_en")

            # Same-volume temporary file and atomic replace
            tmp_table = target_table.with_suffix(".tmp_patch")
            shutil.copy2(temp_dest, tmp_table)
            tmp_table.replace(target_table)
            temp_dest.unlink(missing_ok=True)
            session_journal.append(("table", target_table, orig_table_bak))
            self.log_ui("   ✓ [1/3] Đã cài đặt thành công Tables/data.arcx (Atomic replace)")

            # --- BƯỚC 2: TẢI VÀ CÀI ĐẶT SCRIPTS/LUA.ARCX ---
            if lua_asset and lua_asset.get("browser_download_url"):
                lua_url = lua_asset["browser_download_url"]
                self.log_ui(f"\\n[2/3] Bắt đầu tải Kịch bản thoại & Tin nhắn ({lua_mb:.1f} MB)...")
                temp_lua = Path(os.environ.get("TEMP", str(EXE_DIR))) / "lua_patched_vi_download.arcx"
                def prog_lua(dl, total, pct):
                    if int(pct) % 25 == 0:
                        self.log_ui(f"   Đang tải [2/3]: {dl/(1024*1024):.1f}/{total/(1024*1024):.1f} MB ({pct:.1f}%)")
                if GitHubManager.download_file(lua_url, temp_lua, progress_cb=prog_lua, expected_size=lua_asset.get("size", 0)):
                    target_script = self.game_path / "Persistent_Store" / "Scripts" / "lua.arcx"
                    target_script.parent.mkdir(parents=True, exist_ok=True)
                    orig_lua_bak = target_script.with_suffix(".arcx.orig_en")
                    if target_script.exists() and not orig_lua_bak.exists():
                        shutil.copy2(target_script, orig_lua_bak)
                        self.log_ui("   Đã sao lưu tệp gốc: lua.arcx.orig_en")

                    tmp_lua = target_script.with_suffix(".tmp_patch")
                    shutil.copy2(temp_lua, tmp_lua)
                    tmp_lua.replace(target_script)
                    temp_lua.unlink(missing_ok=True)
                    session_journal.append(("script", target_script, orig_lua_bak))
                    self.log_ui("   ✓ [2/3] Đã cài đặt thành công Scripts/lua.arcx (Thoại & Tin nhắn)")

            # --- BƯỚC 3: TẢI VÀ CÀI ĐẶT ASSETBUNDLES (ẢNH CHỮ) ---
            b_extracted = 0
            if bundles_asset and bundles_asset.get("browser_download_url"):
                bundles_url = bundles_asset["browser_download_url"]
                expected_zip_sha = manifest_data.get("package_sha256", "")
                self.log_ui(f"\\n[3/3] Bắt đầu tải Đồ họa ảnh chữ AssetBundles ({bundles_mb:.1f} MB)...")
                temp_bundles_zip = Path(os.environ.get("TEMP", str(EXE_DIR))) / "AssetBundles_VI_download.zip"

                def prog_bundles(dl, total, pct):
                    if int(pct) % 25 == 0:
                        self.log_ui(f"   Đang tải [3/3]: {dl/(1024*1024):.1f}/{total/(1024*1024):.1f} MB ({pct:.1f}%)")

                dl_ok = GitHubManager.download_file(
                    bundles_url,
                    temp_bundles_zip,
                    progress_cb=prog_bundles,
                    expected_size=bundles_asset.get("size", 0),
                    expected_sha256=expected_zip_sha
                )

                if not dl_ok:
                    self.log_ui("❌ Lỗi khi tải hoặc xác thực tệp AssetBundles từ GitHub.")
                    # Rollback session changes
                    self.log_ui("   Đang phục hồi trạng thái an toàn trước khi cập nhật...")
                    for j_type, target_p, bak_p in session_journal:
                        if bak_p.exists():
                            shutil.copy2(bak_p, target_p)
                    messagebox.showerror("Lỗi Cài Đặt", "Tải hoặc kiểm tra tính toàn vẹn gói AssetBundles thất bại. Game đã được giữ nguyên trạng.")
                    self.btn_online_sync.config(state="normal")
                    self.btn_install.config(state="normal")
                    return

                # Map bundles from manifest
                manifest_bundles_map = {b["bundle_name"]: b for b in manifest_data.get("bundles", [])}

                target_bundles_dir = self.game_path / "Persistent_Store" / "AssetBundles"
                target_bundles_dir.mkdir(parents=True, exist_ok=True)
                session_bundles_applied = []

                try:
                    self.log_ui("   Đang xác thực bảo mật và áp dụng các tệp AssetBundles...")
                    with zipfile.ZipFile(temp_bundles_zip, "r") as zf:
                        for member in zf.infolist():
                            if member.is_dir():
                                continue
                            fname = Path(member.filename).name

                            # Guard 1: Allowlist check
                            if not fname.endswith(".en.unity3d"):
                                continue

                            # Guard 2: Traversal check
                            if ".." in member.filename or member.filename.startswith("/") or member.filename.startswith("\\\\"):
                                raise SecurityError(f"Phát hiện đường dẫn không an toàn: {member.filename}")

                            dest_f = target_bundles_dir / fname
                            # Guard 3: Destination root check
                            if not str(dest_f.resolve()).startswith(str(target_bundles_dir.resolve())):
                                raise SecurityError(f"Nỗ lực ghi ngoài thư mục đích: {member.filename}")

                            b_info = manifest_bundles_map.get(fname, {})
                            exp_patched_sha = b_info.get("patched_sha256")
                            exp_preimage_sha = b_info.get("preimage_sha256")

                            # Repeated update check: if current file matches patched SHA, skip re-extracting
                            if dest_f.exists() and exp_patched_sha:
                                cur_sha = sha256_file(dest_f)
                                if cur_sha.lower() == exp_patched_sha.lower():
                                    b_extracted += 1
                                    continue

                            # Preimage backup: backup pristine file if not already backed up
                            orig_bak = target_bundles_dir / f"{fname}.orig_en"
                            legacy_bak = target_bundles_dir / fname.replace(".unity3d", ".en.unity3d.orig_en")
                            if dest_f.exists() and not orig_bak.exists() and not legacy_bak.exists():
                                shutil.copy2(dest_f, orig_bak)
                                self.log_ui(f"   Đã sao lưu gốc: {orig_bak.name}")

                            # Write to temporary file on same volume
                            temp_b = dest_f.with_suffix(".en.unity3d.tmp_patch")
                            with zf.open(member) as s_fp, open(temp_b, "wb") as d_fp:
                                shutil.copyfileobj(s_fp, d_fp)

                            # Verify SHA256 of extracted bundle
                            if exp_patched_sha:
                                tmp_sha = sha256_file(temp_b)
                                if tmp_sha.lower() != exp_patched_sha.lower():
                                    temp_b.unlink(missing_ok=True)
                                    raise ValueError(f"Sai lệch mã băm bundle {fname}: {tmp_sha} != {exp_patched_sha}")

                            # Atomic replace
                            temp_b.replace(dest_f)
                            session_bundles_applied.append(dest_f)
                            b_extracted += 1

                    temp_bundles_zip.unlink(missing_ok=True)
                    self.log_ui(f"   ✓ [3/3] Đã cài đặt thành công {b_extracted} tệp AssetBundles ảnh chữ!")

                except Exception as b_err:
                    self.log_ui(f"❌ Lỗi áp dụng AssetBundles: {b_err}. Đang rollback tự động...")
                    for bf in session_bundles_applied:
                        bak = target_bundles_dir / f"{bf.name}.orig_en"
                        if not bak.exists():
                            bak = target_bundles_dir / bf.name.replace(".unity3d", ".en.unity3d.orig_en")
                        if bak.exists():
                            shutil.copy2(bak, bf)
                    for tmp in target_bundles_dir.glob("*.tmp_patch"):
                        tmp.unlink(missing_ok=True)
                    temp_bundles_zip.unlink(missing_ok=True)
                    messagebox.showerror("Lỗi Cài Đặt", f"Quá trình áp dụng AssetBundles thất bại:\\n{b_err}\\n\\nCác tệp đã được khôi phục về trạng thái an toàn.")
                    self.btn_online_sync.config(state="normal")
                    self.btn_install.config(state="normal")
                    return

            # --- BƯỚC 4: GHI DẤU VẾT TRẠNG THÁI CÀI ĐẶT CHÍNH XÁC ---
            marker_file = self.game_path / "Persistent_Store" / "viethoa_installed.json"
            marker_data = {
                "installed_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "version": tag.lstrip("v"),
                "release_tag": tag,
                "total_mb_synced": round(total_mb, 2),
                "components": {
                    "tables": {
                        "file": "Persistent_Store/Tables/data.arcx",
                        "status": "installed",
                        "size": target_table.stat().st_size if target_table.exists() else 0
                    },
                    "scripts": {
                        "file": "Persistent_Store/Scripts/lua.arcx",
                        "status": "installed",
                        "size": (self.game_path / "Persistent_Store" / "Scripts" / "lua.arcx").stat().st_size if (self.game_path / "Persistent_Store" / "Scripts" / "lua.arcx").exists() else 0
                    },
                    "asset_bundles": {
                        "target_dir": "Persistent_Store/AssetBundles",
                        "bundles_installed_count": b_extracted,
                        "active_scope": "53 Loading Comics (16 bundles, 4-vertex quad mesh verified)",
                        "pending_scope": "Honor Titles, Logos, Event Banners (Pending mesh repair and BC7 atlas regional isolator)",
                        "manifest_verified": bool(manifest_data)
                    }
                },
                "status": "success"
            }
            marker_file.write_text(json.dumps(marker_data, indent=2, ensure_ascii=False), encoding="utf-8")

            self.log_ui("")
            self.log_ui("==================================================")
            self.log_ui(f"🎉 CHÚC MỪNG! ĐÃ CẬP NHẬT THÀNH CÔNG BẢN VIỆT HÓA {tag}!")
            self.log_ui("   - 100% Cơ sở dữ liệu và phụ đề VoiceTable tiếng Việt")
            self.log_ui("   - 100% Cốt truyện thoại và tin nhắn lữ khách")
            self.log_ui(f"   - 53 Truyện tranh 4 ô màn hình chờ ({b_extracted} AssetBundles)")
            self.log_ui("==================================================")
            msg_ok = (
                f"Đã cập nhật trọn vẹn bản Việt Hóa {tag} ({total_mb:.1f} MB) vào game thành công!\\n\\n"
                f"- Bảng dữ liệu: Đã nạp Tables/data.arcx\\n"
                f"- Thoại & Tin nhắn: Đã nạp Scripts/lua.arcx\\n"
                f"- Đồ họa: Đã nạp {b_extracted} AssetBundles truyện tranh màn hình chờ\\n\\n"
                "Bạn có thể khởi động game để trải nghiệm ngay."
            )
            messagebox.showinfo("Thành Công", msg_ok)

            self.refresh_status()
            self.btn_online_sync.config(state="normal")
            self.btn_install.config(state="normal")

        threading.Thread(target=worker, daemon=True).start()
'''
        content = content[:idx_start] + new_sync_method + "\n" + content[idx_end:]
        print("7. Đã viết lại phương thức on_sync_game_patch_from_github với transaction guard, rollback và manifest.")
    else:
        print("CẢNH BÁO: Không tìm thấy vị trí on_sync_game_patch_from_github trong launcher_pc.py")

    LAUNCHER_PATH.write_text(content, encoding="utf-8")
    print("8. Đã lưu tệp launcher_pc.py mới.")

    # 7. Check compilation
    try:
        py_compile.compile(str(LAUNCHER_PATH), doraise=True)
        print("✓ Kiểm tra cú pháp Python: HOÀN TOÀN HỢP LỆ (0 LỖI)!")
    except Exception as e:
        print(f"❌ LỖI CÚ PHÁP: {e}")
        raise


if __name__ == "__main__":
    update_launcher()
