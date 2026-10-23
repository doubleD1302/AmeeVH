from pathlib import Path

p = Path(r"StellaSora_VietHoa/launcher/launcher_pc.py")
text = p.read_text(encoding="utf-8")

old_code_1 = """            if bundles_src:
                target_bundles_dir = game_path / "Persistent_Store" / "AssetBundles"
                target_bundles_dir.mkdir(parents=True, exist_ok=True)
                b_count = 0
                for b_file in bundles_src.glob("*.en.unity3d"):
                    dest_b = target_bundles_dir / b_file.name
                    if dest_b.exists():
                        bak_b = run_backup_dir / b_file.name
                        shutil.copy2(dest_b, bak_b)
                        backup_manifest["files"].append({
                            "relative_path": f"Persistent_Store/AssetBundles/{b_file.name}",
                            "backup_file": b_file.name,
                            "original_sha256": sha256_file(dest_b),
                            "size": dest_b.stat().st_size
                        })
                    temp_b = dest_b.with_suffix(".en.unity3d.tmp_patch")
                    shutil.copy2(b_file, temp_b)
                    temp_b.replace(dest_b)
                    b_count += 1
                if b_count > 0:
                    installed_count += b_count
                    installed_files.append(f"Persistent_Store/AssetBundles/ ({b_count} bundles)")
                    log(f"   ✓ Đã cài đặt thành công: {b_count} tệp AssetBundles ảnh chữ Việt hóa (Truyện tranh, Danh hiệu, Tiêu đề)")"""

new_code_1 = """            if bundles_src:
                target_bundles_dir = game_path / "Persistent_Store" / "AssetBundles"
                target_bundles_dir.mkdir(parents=True, exist_ok=True)
                steam_install_dir = game_path / "StellaSora_Data" / "StreamingAssets" / "InstallResource"
                has_steam_install = steam_install_dir.exists() and any(steam_install_dir.iterdir())
                b_count = 0
                for b_file in bundles_src.glob("*.en.unity3d"):
                    dest_b = target_bundles_dir / b_file.name
                    if dest_b.exists():
                        bak_b = run_backup_dir / b_file.name
                        shutil.copy2(dest_b, bak_b)
                        backup_manifest["files"].append({
                            "relative_path": f"Persistent_Store/AssetBundles/{b_file.name}",
                            "backup_file": b_file.name,
                            "original_sha256": sha256_file(dest_b),
                            "size": dest_b.stat().st_size
                        })
                    temp_b = dest_b.with_suffix(".en.unity3d.tmp_patch")
                    shutil.copy2(b_file, temp_b)
                    temp_b.replace(dest_b)
                    b_count += 1

                    if has_steam_install:
                        dest_steam = steam_install_dir / b_file.name
                        if dest_steam.exists():
                            bak_steam = run_backup_dir / f"steam_{b_file.name}"
                            if not bak_steam.exists():
                                shutil.copy2(dest_steam, bak_steam)
                                backup_manifest["files"].append({
                                    "relative_path": f"StellaSora_Data/StreamingAssets/InstallResource/{b_file.name}",
                                    "backup_file": f"steam_{b_file.name}",
                                    "original_sha256": sha256_file(dest_steam),
                                    "size": dest_steam.stat().st_size
                                })
                            temp_s = dest_steam.with_suffix(".en.unity3d.tmp_steam_patch")
                            shutil.copy2(b_file, temp_s)
                            temp_s.replace(dest_steam)

                if b_count > 0:
                    installed_count += b_count
                    installed_files.append(f"AssetBundles ({b_count} bundles)")
                    log(f"   ✓ Đã cài đặt thành công: {b_count} tệp AssetBundles ảnh chữ Việt hóa (Truyện tranh, Danh hiệu, Tiêu đề)")"""

old_code_2 = """                            # Atomic replace
                            temp_b.replace(dest_f)
                            session_bundles_applied.append(dest_f)
                            b_extracted += 1"""

new_code_2 = """                            # Atomic replace
                            temp_b.replace(dest_f)
                            session_bundles_applied.append(dest_f)
                            b_extracted += 1

                            # Also sync to Steam InstallResource if present (critical for Steam client)
                            steam_install_dir = self.game_path / "StellaSora_Data" / "StreamingAssets" / "InstallResource"
                            if steam_install_dir.exists():
                                steam_f = steam_install_dir / fname
                                if steam_f.exists():
                                    bak_s = steam_install_dir / f"{fname}.orig_en"
                                    if not bak_s.exists():
                                        shutil.copy2(steam_f, bak_s)
                                    tmp_s = steam_f.with_suffix(".en.unity3d.tmp_steam_patch")
                                    shutil.copy2(dest_f, tmp_s)
                                    tmp_s.replace(steam_f)"""

text_lf = text.replace("\r\n", "\n")
old_1_lf = old_code_1.replace("\r\n", "\n")
new_1_lf = new_code_1.replace("\r\n", "\n")
old_2_lf = old_code_2.replace("\r\n", "\n")
new_2_lf = new_code_2.replace("\r\n", "\n")

ok1 = old_1_lf in text_lf
ok2 = old_2_lf in text_lf
print(f"Match 1: {ok1}, Match 2: {ok2}")

if ok1 and ok2:
    text_lf = text_lf.replace(old_1_lf, new_1_lf).replace(old_2_lf, new_2_lf)
    p.write_text(text_lf.replace("\n", "\r\n"), encoding="utf-8")
    print("SUCCESS: launcher_pc.py updated with Steam InstallResource support!")
