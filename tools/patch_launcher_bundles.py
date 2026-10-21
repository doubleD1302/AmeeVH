import sys
from pathlib import Path

lp = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\launcher\launcher_pc.py")
content = lp.read_text(encoding="utf-8")

anchor = 'log(f"   ✓ Đã cài đặt thành công: {orig_script.name} (Kịch bản thoại & Tin nhắn Lua ArcX)")'

addition = '''

            # Install Vietnamese AssetBundles (Textures: Comics, Titles, Logos)
            bundles_src_dirs = [
                BASE_DIR / "dist" / "AssetBundles",
                BASE_DIR / "staging" / "bundles_patched_vi" / "Persistent_Store" / "AssetBundles",
            ]
            bundles_src = next((d for d in bundles_src_dirs if d.exists()), None)
            if bundles_src:
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
                    log(f"   ✓ Đã cài đặt thành công: {b_count} tệp AssetBundles ảnh chữ Việt hóa (Truyện tranh, Danh hiệu, Tiêu đề)")'''

if anchor in content:
    content = content.replace(anchor, anchor + addition, 1)
    lp.write_text(content, encoding="utf-8")
    print("SUCCESS: Updated launcher_pc.py")
else:
    print("ERROR: Anchor not found")
