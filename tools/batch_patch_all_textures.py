#!/usr/bin/env python3
"""Batch patch ALL translated Vietnamese textures into Unity AssetBundles (*.en.unity3d).

Includes:
- Category 1: Loading Comics (53 files)
- Category 3: Logos, Titles & Headers (105 files)
- Category 4: Buttons & Results (31 files)
- Category 5: Event & Gacha Banners / Tabs (280 files!)
- Category 6: Costume Art Text (12 files)

Sourced from:
- backups/steam_installresource_backup_20261023/
Outputs to:
- staging/bundles_patched_vi/Persistent_Store/AssetBundles/
- dist/AssetBundles/
Updates dist/patch_manifest.json and dist/StellaSora_AssetBundles_VI.zip
"""
from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import sys
import time
import zipfile

from PIL import Image
import UnityPy
from UnityPy.export import Texture2DConverter
from UnityPy.streams import EndianBinaryReader

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_BUNDLES_DIR = PROJECT_ROOT / "backups" / "steam_installresource_backup_20261023"
DIST_BUNDLES_DIR = PROJECT_ROOT / "dist" / "AssetBundles"
STAGING_DIR = PROJECT_ROOT / "staging" / "bundles_patched_vi" / "Persistent_Store" / "AssetBundles"
MANIFEST_PATH = PROJECT_ROOT / "dist" / "patch_manifest.json"
ZIP_OUTPUT = PROJECT_ROOT / "dist" / "StellaSora_AssetBundles_VI.zip"

TEXTURE_SOURCES = [
    PROJECT_ROOT / "dist" / "StellaSora_Texture_VI" / "01_TruyenTranh_LoadingComics_VI",
    PROJECT_ROOT / "dist" / "StellaSora_Texture_VI" / "03_TieuDe_Logos_Headers_VI",
    PROJECT_ROOT / "dist" / "StellaSora_Texture_AnhVeChu_EN" / "04_NutBam_HuyHieu_Results_VI",
    PROJECT_ROOT / "dist" / "StellaSora_Texture_AnhVeChu_EN" / "05_SuKien_Banners_Tabs_VI",
    PROJECT_ROOT / "dist" / "StellaSora_Texture_VI" / "06_TrangPhuc_SkinArtText_VI",
]


def run():
    print("=" * 75)
    print("BẮT ĐẦU ĐÓNG GÓI TOÀN BỘ 100% TEXTURE VIỆT HÓA (BAO GỒM 280 BANNER SỰ KIỆN & GACHA)")
    print("=" * 75)
    t0 = time.time()

    # 1. Collect all target PNGs
    targets = {}  # fname -> path
    for s_dir in TEXTURE_SOURCES:
        if not s_dir.exists():
            print(f"⚠️ Cảnh báo: Thư mục nguồn không tồn tại: {s_dir.name}")
            continue
        count = 0
        for p in s_dir.glob("*.png"):
            targets[p.name] = p
            count += 1
        print(f"-> Nạp từ {s_dir.name}: {count} ảnh PNG")

    print(f"-> Tổng số ảnh Việt hóa thu thập được: {len(targets)} ảnh")

    # 2. Map targets to bundle names
    all_bundle_files = {p.name: p for p in SOURCE_BUNDLES_DIR.glob("*.en.unity3d")}
    by_bundle = {}
    for fname, p in sorted(targets.items()):
        # parse bundle name: icon-1__banner_beginner.png -> icon-1.en.unity3d
        parts = fname.split("__", 1)
        if len(parts) != 2:
            continue
        stem, spr_name = parts[0], parts[1].replace(".png", "")
        b_name = f"{stem}.en.unity3d"
        if b_name in all_bundle_files:
            by_bundle.setdefault(b_name, []).append((spr_name, p))

    print(f"-> Phân bổ mục tiêu vào {len(by_bundle)} AssetBundles")

    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    DIST_BUNDLES_DIR.mkdir(parents=True, exist_ok=True)

    # Load existing manifest if present
    if MANIFEST_PATH.exists():
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
    else:
        manifest_data = {"version": "0.9.7", "bundles": {}}

    manifest_bundles = manifest_data.setdefault("bundles", {})

    total_patched_textures = 0
    total_patched_bundles = 0
    errors = []

    for b_idx, (b_name, items) in enumerate(sorted(by_bundle.items()), 1):
        b_path = all_bundle_files[b_name]
        raw_bundle = b_path.read_bytes()
        env = UnityPy.load(raw_bundle)

        tex_map = {}
        for obj in env.objects:
            if obj.type.name == "Texture2D":
                tex = obj.read()
                tex_map[tex.m_Name] = (obj, tex)

        matched_items = [it for it in items if it[0] in tex_map]
        if not matched_items:
            continue

        sample_tex = tex_map[matched_items[0][0]][1]
        if not sample_tex.m_StreamData or not sample_tex.m_StreamData.path:
            continue

        res_name = sample_tex.m_StreamData.path.replace("\\", "/").rsplit("/", 1)[-1]
        if res_name not in env.file.files:
            continue

        res_node = env.file.files[res_name]
        res_bytes = bytearray(bytes(res_node.reader.bytes if hasattr(res_node, "reader") else res_node.bytes))

        bundle_patched_count = 0
        for spr_name, p in matched_items:
            obj, tex = tex_map[spr_name]
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
                if spr_name == "zs_activity_trial_logo":
                    off_x, off_y = 57, 8
                else:
                    off_x = (target_size[0] - vi_img.width) // 2
                    off_y = (target_size[1] - vi_img.height) // 2
                canvas.paste(vi_img, (off_x, off_y), vi_img)

            encoded, _ = Texture2DConverter.image_to_texture2d(
                canvas, tex.m_TextureFormat, tex.object_reader.platform, tex.m_PlatformBlob
            )

            if len(encoded) != length:
                print(f"⚠️ Sai lệch kích thước {spr_name} trong {b_name}: {len(encoded)} != {length}")
                continue

            res_bytes[start : start + length] = encoded
            bundle_patched_count += 1
            total_patched_textures += 1

        # Re-save bundle
        for key, node in list(env.file.files.items()):
            raw_node = bytes(res_bytes) if key == res_name else (bytes(node.reader.bytes) if hasattr(node, "reader") else bytes(node.bytes))
            reader = EndianBinaryReader(raw_node)
            reader.flags = node.flags
            env.file.files[key] = reader

        patched_bytes = env.file.save(packer="original")
        
        # Verify readback
        try:
            v_env = UnityPy.load(patched_bytes)
            v_tex = {o.read().m_Name: o.read() for o in v_env.objects if o.type.name == "Texture2D"}
            for spr_name, _ in matched_items:
                if spr_name in v_tex:
                    _ = v_tex[spr_name].image
        except Exception as e:
            errors.append(f"{b_name} readback failed: {e}")
            continue

        # Write to staging and dist
        (STAGING_DIR / b_name).write_bytes(patched_bytes)
        (DIST_BUNDLES_DIR / b_name).write_bytes(patched_bytes)

        new_sha = hashlib.sha256(patched_bytes).hexdigest()
        manifest_bundles[b_name] = {
            "patched_sha256": new_sha,
            "size_bytes": len(patched_bytes),
            "textures_patched": bundle_patched_count
        }

        total_patched_bundles += 1
        print(f"[{total_patched_bundles:02d}] ✓ Đã vá {b_name}: {bundle_patched_count} textures (Size: {len(patched_bytes):,} bytes)")

    # Save manifest
    manifest_data["total_textures_patched"] = total_patched_textures
    manifest_data["total_bundles"] = len(manifest_bundles)
    manifest_data["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2, ensure_ascii=False)

    print("\n-> Cập nhật tệp nén phân phối:", ZIP_OUTPUT.name)
    with zipfile.ZipFile(ZIP_OUTPUT, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(DIST_BUNDLES_DIR.glob("*.en.unity3d")):
            zf.write(p, arcname=p.name)

    elapsed = time.time() - t0
    print("=" * 75)
    print(f"🎉 HOÀN THÀNH ĐÓNG GÓI TOÀN BỘ TEXTURE TRONG {elapsed:.1f} GIÂY!")
    print(f"📦 Đã xử lý và vá thành công: {total_patched_bundles} AssetBundles")
    print(f"🖼️ Tổng số Texture Việt hóa thực tế được nhúng: {total_patched_textures} textures")
    if errors:
        print(f"⚠️ Có {len(errors)} lỗi phát sinh:")
        for e in errors:
            print("  ", e)
    else:
        print("✓ Không có bất kỳ lỗi xác thực nào!")
    print("=" * 75)
    return 0


if __name__ == "__main__":
    sys.exit(run())
