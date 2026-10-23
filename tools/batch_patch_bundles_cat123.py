#!/usr/bin/env python3
"""Batch patch translated Vietnamese textures (Categories 1, 2, 3) into Unity AssetBundles (*.en.unity3d).

1. Reads all translated PNG textures from:
   - 01_TruyenTranh_LoadingComics_VI (53 files)
   - 02_DanhHieu_HonorTitles_VI (361 files)
   - 03_TieuDe_Logos_Headers_VI (105 files)
2. Targets 59 unique AssetBundles in Persistent_Store/AssetBundles/*.en.unity3d.
3. Automatically maps textures to Texture2D objects, composites onto exact canvas, and encodes GPU mips (BC7/RGBA32).
4. Replaces stream segments in .resS preserving bundle structure, nodes, and serialized objects.
5. Verifies 100% of patched bundles with UnityPy readback.
6. Deploys to staging/bundles_patched_vi/ and packages dist/StellaSora_AssetBundles_VI_Cat123.zip.
7. Deploys patched bundles to local Yostar and Steam game installations with .orig_en backups.
"""
from __future__ import annotations

import io
import json
import os
from pathlib import Path
import shutil
import time
import zipfile

from PIL import Image
import UnityPy
from UnityPy.export import Texture2DConverter
from UnityPy.streams import EndianBinaryReader

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PROJECT_ROOT.parent
SOURCE_BUNDLES_DIR = PROJECT_ROOT / "backups" / "steam_installresource_backup_20261023"
STEAM_BUNDLES_DIR = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stella Sora\Persistent_Store\AssetBundles")

DIST_TEX_VI = PROJECT_ROOT / "dist" / "StellaSora_Texture_VI"
STAGING_DIR = PROJECT_ROOT / "staging" / "bundles_patched_vi" / "Persistent_Store" / "AssetBundles"
ZIP_OUTPUT = PROJECT_ROOT / "dist" / "StellaSora_AssetBundles_VI_Cat123.zip"

CATEGORIES = [
    "01_TruyenTranh_LoadingComics_VI",
    # "02_DanhHieu_HonorTitles_VI" - Giữ nguyên tài nguyên gốc theo yêu cầu người dùng
    "03_TieuDe_Logos_Headers_VI"
]


def run_batch_patch():
    print("=== BẮT ĐẦU ĐÓNG GÓI BẢN VIỆT HÓA MỤC 1-2-3 VÀO ASSET BUNDLES (.en.unity3d) ===")
    t_start = time.time()

    # 1. Gather all targets
    print("\n1. Thu thập danh sách ảnh Việt hóa Mục 1-2-3...")
    targets = []
    for cat in CATEGORIES:
        cat_dir = DIST_TEX_VI / cat
        for p in sorted(cat_dir.glob("*.png")):
            targets.append((cat, p))
    print(f"   Tổng số ảnh mục tiêu: {len(targets)} ảnh.")

    # 2. Map targets to bundle files
    all_bundle_files = {p.name: p for p in SOURCE_BUNDLES_DIR.glob("*.en.unity3d")}
    by_bundle = {}
    for cat, p in targets:
        fname = p.name.replace(".png", "")
        for b_name in all_bundle_files:
            stem = b_name.replace(".en.unity3d", "")
            prefix = f"{stem}__"
            if fname.startswith(prefix):
                sprite_name = fname[len(prefix):]
                by_bundle.setdefault(b_name, []).append((cat, p, sprite_name))
                break

    print(f"   Phân bổ vào {len(by_bundle)} asset bundles.")

    # 3. Create staging directory
    STAGING_DIR.mkdir(parents=True, exist_ok=True)

    # 4. Process each bundle
    print("\n2. Tiến hành mã hóa GPU và vá từng bundle...")
    patched_bundles_count = 0
    total_textures_patched = 0
    skipped_atlas_count = 0
    verification_errors = []
    patch_manifest = {}

    for b_idx, (b_name, items) in enumerate(sorted(by_bundle.items()), 1):
        b_path = all_bundle_files[b_name]
        raw_bundle = b_path.read_bytes()
        env = UnityPy.load(raw_bundle)

        # Map Texture2D objects
        tex_map = {}
        for obj in env.objects:
            if obj.type.name == "Texture2D":
                tex = obj.read()
                tex_map[tex.m_Name] = (obj, tex)

        # Filter items that have matching Texture2D
        matched_items = [it for it in items if it[2] in tex_map]
        skipped_items = [it for it in items if it[2] not in tex_map]
        skipped_atlas_count += len(skipped_items)

        if not matched_items:
            print(f"   [{b_idx}/{len(by_bundle)}] {b_name}: Bỏ qua (chỉ chứa Sprite Atlas)")
            continue

        # Get resource stream file name
        sample_tex = tex_map[matched_items[0][2]][1]
        if not sample_tex.m_StreamData or not sample_tex.m_StreamData.path:
            print(f"   [{b_idx}/{len(by_bundle)}] {b_name}: Không có stream data bên ngoài, bỏ qua")
            continue

        res_name = sample_tex.m_StreamData.path.replace("\\", "/").rsplit("/", 1)[-1]
        if res_name not in env.file.files:
            print(f"   [{b_idx}/{len(by_bundle)}] {b_name}: Resource node {res_name} không tìm thấy")
            continue

        res_node = env.file.files[res_name]
        res_bytes = bytearray(bytes(res_node.reader.bytes if hasattr(res_node, "reader") else res_node.bytes))

        # Encode and patch each texture
        b_patched_count = 0
        for cat, p, name in matched_items:
            obj, tex = tex_map[name]
            target_size = (tex.m_Width, tex.m_Height)
            start = int(tex.m_StreamData.offset)
            length = int(tex.m_StreamData.size)

            with Image.open(p) as img:
                img.load()
                vi_img = img.convert("RGBA")

            if vi_img.size == target_size:
                canvas = vi_img
            else:
                canvas = Image.new("RGBA", target_size, (0, 0, 0, 0))
                off_x = (target_size[0] - vi_img.width) // 2
                off_y = (target_size[1] - vi_img.height) // 2
                canvas.paste(vi_img, (off_x, off_y), vi_img)

            encoded, _ = Texture2DConverter.image_to_texture2d(
                canvas, tex.m_TextureFormat, tex.object_reader.platform, tex.m_PlatformBlob
            )

            if len(encoded) != length:
                print(f"   ⚠️ Lỗi kích thước byte {name}: {len(encoded)} != {length}")
                continue

            res_bytes[start : start + length] = encoded
            b_patched_count += 1
            total_textures_patched += 1

        # Re-save bundle preserving original node structure
        for key, node in list(env.file.files.items()):
            raw_node = bytes(res_bytes) if key == res_name else (bytes(node.reader.bytes) if hasattr(node, "reader") else bytes(node.bytes))
            reader = EndianBinaryReader(raw_node)
            reader.flags = node.flags
            env.file.files[key] = reader

        patched_bundle_bytes = env.file.save(packer="original")
        staging_bundle_path = STAGING_DIR / b_name
        staging_bundle_path.write_bytes(patched_bundle_bytes)

        # Verification by reopening
        try:
            v_env = UnityPy.load(patched_bundle_bytes)
            v_tex = {o.read().m_Name: o.read() for o in v_env.objects if o.type.name == "Texture2D"}
            for _, _, name in matched_items:
                if name not in v_tex:
                    verification_errors.append(f"{b_name} missing {name}")
                else:
                    _ = v_tex[name].image  # verify decode
        except Exception as e:
            verification_errors.append(f"{b_name} readback error: {e}")

        patched_bundles_count += 1
        patch_manifest[b_name] = {
            "textures_patched": b_patched_count,
            "bundle_size": len(patched_bundle_bytes),
            "original_size": len(raw_bundle)
        }
        print(f"   [{b_idx}/{len(by_bundle)}] ✓ {b_name}: Đã vá {b_patched_count} textures ({len(patched_bundle_bytes):,} bytes)")

    print(f"\n3. Kết quả vá Staging:")
    print(f"   - Đã xử lý thành công: {patched_bundles_count} asset bundles.")
    print(f"   - Đã vá tổng cộng: {total_textures_patched} ảnh Texture2D độc lập.")
    print(f"   - Lỗi xác thực: {len(verification_errors)} lỗi.")

    # 5. Package into distribution ZIP
    print(f"\n4. Đóng gói {ZIP_OUTPUT.name}...")
    with zipfile.ZipFile(ZIP_OUTPUT, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in STAGING_DIR.glob("*.en.unity3d"):
            zf.write(f, arcname=f"Persistent_Store/AssetBundles/{f.name}")
    zip_mb = ZIP_OUTPUT.stat().st_size / (1024 * 1024)
    print(f"   ✓ Đã đóng gói thành công {ZIP_OUTPUT.name} ({zip_mb:.2f} MB)!")

    # 6. Deploy to local game installations (Yostar & Steam)
    print("\n5. Triển khai trực tiếp vào game trên máy tính...")
    # 6a. Yostar Game
    yostar_updated = 0
    for b_file in STAGING_DIR.glob("*.en.unity3d"):
        dest = SOURCE_BUNDLES_DIR / b_file.name
        bak = dest.with_suffix(".en.unity3d.orig_en")
        if dest.exists() and not bak.exists():
            shutil.copy2(dest, bak)  # Backup original
        shutil.copy2(b_file, dest)
        yostar_updated += 1
    print(f"   ✓ Đã cài đặt {yostar_updated} bundles vào Yostar Client (đã sao lưu *.orig_en)")

    # 6b. Steam Game
    steam_updated = 0
    steam_install_dir = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stella Sora\StellaSora_Data\StreamingAssets\InstallResource")
    if STEAM_BUNDLES_DIR.exists():
        for b_file in STAGING_DIR.glob("*.en.unity3d"):
            dest = STEAM_BUNDLES_DIR / b_file.name
            bak = dest.with_suffix(".en.unity3d.orig_en")
            if dest.exists() and not bak.exists():
                shutil.copy2(dest, bak)  # Backup original
            shutil.copy2(b_file, dest)
            steam_updated += 1
        print(f"   ✓ Đã cài đặt {steam_updated} bundles vào Steam Persistent_Store (đã sao lưu *.orig_en)")

    if steam_install_dir.exists():
        s_inst_count = 0
        for b_file in STAGING_DIR.glob("*.en.unity3d"):
            dest = steam_install_dir / b_file.name
            shutil.copy2(b_file, dest)
            s_inst_count += 1
        print(f"   ✓ Đã cài đặt {s_inst_count} bundles vào Steam StreamingAssets/InstallResource")

    t_total = time.time() - t_start
    print(f"\n=== HOÀN TẤT TOÀN DIỆN TRONG {t_total:.2f} GIÂY ===")
    return patched_bundles_count, total_textures_patched


if __name__ == "__main__":
    run_batch_patch()
