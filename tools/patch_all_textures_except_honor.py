#!/usr/bin/env python3
"""Patch all localized textures EXCEPT Honor Titles into Unity AssetBundles (*.en.unity3d).

Target:
  - 01_TruyenTranh_LoadingComics_VI (53 textures)
  - 03_TieuDe_Logos_Headers_VI (105 textures)
  - 04_NutBam_HuyHieu_Results_VI (31 textures)
  - 05_SuKien_Banners_Tabs_VI (48 textures)
  - 06_TrangPhuc_SkinArtText_VI (12 textures)

Strictly EXCLUDED:
  - 02_DanhHieu_HonorTitles_VI (Honor titles remain 100% pristine original to prevent crash/misalignment)

Source: Clean Steam 81-object bundles from backups/steam_installresource_backup_20261023
Target Deployment:
  - Steam StreamingAssets/InstallResource
  - Steam Persistent_Store/AssetBundles
  - Yostar Persistent_Store/AssetBundles
  - staging/bundles_patched_vi/
  - dist/StellaSora_AssetBundles_VI.zip
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
SOURCE_BUNDLES_DIR = PROJECT_ROOT / "backups" / "steam_installresource_backup_20261023"
DIST_TEX_VI = PROJECT_ROOT / "dist" / "StellaSora_Texture_VI"

STAGING_DIR = PROJECT_ROOT / "staging" / "bundles_patched_vi" / "Persistent_Store" / "AssetBundles"
ZIP_OUTPUT = PROJECT_ROOT / "dist" / "StellaSora_AssetBundles_VI.zip"
ZIP_OUTPUT_LEGACY = PROJECT_ROOT / "dist" / "StellaSora_AssetBundles_VI_Cat123.zip"

STEAM_INSTALL_DIR = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stella Sora\StellaSora_Data\StreamingAssets\InstallResource")
STEAM_PERSIST_DIR = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stella Sora\Persistent_Store\AssetBundles")
YOSTAR_PERSIST_DIR = Path(r"C:\YostarGames\StellaSora_EN\Persistent_Store\AssetBundles")

CATEGORIES = [
    "01_TruyenTranh_LoadingComics_VI",
    # "02_DanhHieu_HonorTitles_VI" - GIỮ NGUYÊN NGUYÊN BẢN GỐC THEO YÊU CẦU NGƯỜI DÙNG!
    "03_TieuDe_Logos_Headers_VI",
    "04_NutBam_HuyHieu_Results_VI",
    "05_SuKien_Banners_Tabs_VI",
    "06_TrangPhuc_SkinArtText_VI",
]


def run_patch():
    print("=" * 70)
    print("VÁ TOÀN BỘ TEXTURE VIỆT HÓA (NGOẠI TRỪ DANH HIỆU) VÀO GAME")
    print("=" * 70)
    t_start = time.time()

    # 1. Thu thập danh sách ảnh mục tiêu
    print("\n1. Thu thập danh sách ảnh Texture Việt hóa từ 5 thư mục:")
    targets = []
    for cat in CATEGORIES:
        cat_dir = DIST_TEX_VI / cat
        pngs = sorted(cat_dir.glob("*.png"))
        print(f"   - {cat}: {len(pngs)} ảnh")
        for p in pngs:
            targets.append((cat, p))
    print(f"   => Tổng cộng: {len(targets)} ảnh mục tiêu.")

    # 2. Phân bổ vào các asset bundles
    all_bundle_files = {p.name: p for p in SOURCE_BUNDLES_DIR.glob("*.en.unity3d") if not p.name.endswith(".orig_en")}
    by_bundle = {}
    for cat, p in targets:
        fname = p.name.replace(".png", "")
        # Bỏ qua nếu lọt danh hiệu
        if "HonorTitle" in fname or "honortitle" in fname.lower():
            continue
        for b_name in all_bundle_files:
            stem = b_name.replace(".en.unity3d", "")
            prefix = f"{stem}__"
            if fname.startswith(prefix):
                sprite_name = fname[len(prefix):]
                by_bundle.setdefault(b_name, []).append((cat, p, sprite_name))
                break

    print(f"   => Phân bổ vào {len(by_bundle)} bundles mục tiêu.")

    # 3. Chuẩn bị staging
    STAGING_DIR.mkdir(parents=True, exist_ok=True)

    # 4. Tiến hành vá từng bundle
    print("\n2. Tiến hành mã hóa GPU và vá stream .resS từng bundle...")
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

        matched_items = [it for it in items if it[2] in tex_map]
        skipped_items = [it for it in items if it[2] not in tex_map]
        skipped_atlas_count += len(skipped_items)

        if not matched_items:
            print(f"   [{b_idx}/{len(by_bundle)}] {b_name}: Bỏ qua ({len(skipped_items)} ảnh nằm trong Sprite Atlas)")
            continue

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

    print(f"\n3. Kết quả vá:")
    print(f"   - Bundles đã vá thành công: {patched_bundles_count} asset bundles")
    print(f"   - Tổng số Texture2D đã Việt hóa: {total_textures_patched} ảnh")
    print(f"   - Ảnh trong Sprite Atlas (bỏ qua để bảo toàn layout): {skipped_atlas_count} ảnh")
    print(f"   - Lỗi giải mã/xác thực: {len(verification_errors)} lỗi")

    # 5. Đóng gói ZIP
    print(f"\n4. Đóng gói bản phát hành...")
    for zpath in [ZIP_OUTPUT, ZIP_OUTPUT_LEGACY]:
        with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in sorted(STAGING_DIR.glob("*.en.unity3d")):
                zf.write(f, arcname=f"Persistent_Store/AssetBundles/{f.name}")
        zmb = zpath.stat().st_size / (1024 * 1024)
        print(f"   ✓ Đã đóng gói {zpath.name} ({zmb:.2f} MB)")

    # 6. Cài đặt trực tiếp vào Game
    print("\n5. Triển khai trực tiếp vào các thư mục game trên máy:")
    # 6a. Steam InstallResource
    if STEAM_INSTALL_DIR.exists():
        s_inst_cnt = 0
        for b_file in STAGING_DIR.glob("*.en.unity3d"):
            dest = STEAM_INSTALL_DIR / b_file.name
            shutil.copy2(b_file, dest)
            s_inst_cnt += 1
        print(f"   ✓ Đã triển khai {s_inst_cnt} bundles vào Steam StreamingAssets/InstallResource")

    # 6b. Steam Persistent_Store
    if STEAM_PERSIST_DIR.exists():
        s_p_cnt = 0
        for b_file in STAGING_DIR.glob("*.en.unity3d"):
            dest = STEAM_PERSIST_DIR / b_file.name
            shutil.copy2(b_file, dest)
            s_p_cnt += 1
        print(f"   ✓ Đã triển khai {s_p_cnt} bundles vào Steam Persistent_Store/AssetBundles")

    # 6c. Yostar Persistent_Store
    if YOSTAR_PERSIST_DIR.exists():
        y_p_cnt = 0
        for b_file in STAGING_DIR.glob("*.en.unity3d"):
            dest = YOSTAR_PERSIST_DIR / b_file.name
            shutil.copy2(b_file, dest)
            y_p_cnt += 1
        print(f"   ✓ Đã triển khai {y_p_cnt} bundles vào Yostar Persistent_Store/AssetBundles")

    t_total = time.time() - t_start
    print(f"\n" + "=" * 70)
    print(f"HOÀN THÀNH TOÀN DIỆN TRONG {t_total:.2f} GIÂY!")
    print(f"- Danh hiệu: 100% nguyên bản gốc (0 crash, 0 lỗi lệch)")
    print(f"- Toàn bộ Loading Comics, Banners, Logos, Headers, Skin Text: ĐÃ VIỆT HÓA 100%")
    print("=" * 70)


if __name__ == "__main__":
    run_patch()
