#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Apply Vietnamese Category 5 Textures:
- Copies 2 translated files from dist/StellaSora_Textures_VI_2Anh_20261025/05_SuKien_Banners_Tabs
  (ui_equipment__tab_activity_03.png and ui_equipment__zs_startowerhandbook_fatecard_activity.png)
  into distribution folders.
- Patches both ui_equipment.en.unity3d and ui_commonex.en.unity3d sprite atlases.
- Dual-syncs to Standalone and Steam installations live.
- Updates dist/patch_manifest.json and dist/StellaSora_AssetBundles_VI.zip.
- Re-exports dist/StellaSora_Textures_Chua_Viet_Hoa.
"""

from __future__ import annotations
import hashlib
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

PROJECT_ROOT = Path(r"C:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
USER_SRC = PROJECT_ROOT / "dist" / "StellaSora_Textures_VI_2Anh_20261025" / "05_SuKien_Banners_Tabs"

BACKUP_DIR = PROJECT_ROOT / "backups" / "steam_installresource_backup_20261023"
DIST_BUNDLES_DIR = PROJECT_ROOT / "dist" / "AssetBundles"
STAGING_DIR = PROJECT_ROOT / "staging" / "bundles_patched_vi" / "Persistent_Store" / "AssetBundles"
MANIFEST_PATH = PROJECT_ROOT / "dist" / "patch_manifest.json"
ZIP_OUTPUT = PROJECT_ROOT / "dist" / "StellaSora_AssetBundles_VI.zip"

STANDALONE_PS = Path(r"c:\YostarGames\StellaSora_EN\Persistent_Store\AssetBundles")
STEAM_PS = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stella Sora\Persistent_Store\AssetBundles")
STEAM_IR = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stella Sora\StellaSora_Data\StreamingAssets\InstallResource")

VI_SOURCES = [
    PROJECT_ROOT / "dist" / "StellaSora_Texture_AnhVeChu_EN" / "04_NutBam_HuyHieu_Results_VI",
    PROJECT_ROOT / "dist" / "StellaSora_Texture_VI" / "03_TieuDe_Logos_Headers_VI",
    PROJECT_ROOT / "dist" / "StellaSora_Texture_AnhVeChu_EN" / "05_SuKien_Banners_Tabs_VI",
    PROJECT_ROOT / "dist" / "btn_video_skip_viet_hoa.png",
]

def step1_copy_user_textures():
    print("=== BƯỚC 1: TIẾP NHẬN 2 ẢNH VIỆT HÓA MỤC 05 ===")
    assert USER_SRC.exists(), f"Không tìm thấy thư mục nguồn: {USER_SRC}"

    src_tab = USER_SRC / "ui_equipment__tab_activity_03.png"
    src_act = USER_SRC / "ui_equipment__zs_startowerhandbook_fatecard_activity.png"
    assert src_tab.exists(), f"Thiếu {src_tab.name}"
    assert src_act.exists(), f"Thiếu {src_act.name}"

    dst_folders = [
        PROJECT_ROOT / "dist" / "StellaSora_Texture_AnhVeChu_EN" / "05_SuKien_Banners_Tabs_VI",
        PROJECT_ROOT / "dist" / "StellaSora_Texture_VI" / "05_SuKien_Banners_Tabs_VI"
    ]

    for d in dst_folders:
        d.mkdir(parents=True, exist_ok=True)
        # Copy to equipment target
        shutil.copy2(src_tab, d / "ui_equipment__tab_activity_03.png")
        shutil.copy2(src_act, d / "ui_equipment__zs_startowerhandbook_fatecard_activity.png")
        # Also sync tab_activity_03 to ui_commonex (same exact 259x108 dimension)
        shutil.copy2(src_tab, d / "ui_commonex__tab_activity_03.png")
        print(f"  ✓ Đã cập nhật vào {d.relative_to(PROJECT_ROOT)}")

def load_all_sprites():
    sprites = {}
    bundle_specific = {}
    for s_path in VI_SOURCES:
        if s_path.is_file():
            sprites["btn_video_skip"] = Image.open(s_path).convert("RGBA")
        elif s_path.is_dir():
            for p in s_path.glob("*.png"):
                parts = p.stem.split("__")
                img = Image.open(p).convert("RGBA")
                if len(parts) == 2:
                    bundle_stem, spr_name = parts[0], parts[1]
                    bundle_specific[(bundle_stem, spr_name)] = img
                    sprites[spr_name] = img
                else:
                    sprites[parts[-1]] = img
    return sprites, bundle_specific

def patch_atlas_bundle(bundle_name: str, sprites: dict, bundle_specific: dict) -> bytes:
    print(f"\n-> Đang đóng gói SpriteAtlas cho: {bundle_name}...")
    b_path = BACKUP_DIR / bundle_name
    b_stem = bundle_name.replace(".en.unity3d", "")
    env = UnityPy.load(b_path.read_bytes())

    atlases = [o for o in env.objects if o.type.name == "SpriteAtlas"]
    if not atlases:
        raise ValueError(f"No SpriteAtlas found in {bundle_name}")

    atlas_obj = atlases[0].read()
    spr_map = {s.read().m_RenderDataKey: s.read().m_Name for s in env.objects if s.type.name == "Sprite"}
    tex_objs = {o.path_id: o for o in env.objects if o.type.name == "Texture2D"}

    atlas_patches: dict[int, list[tuple[str, Image.Image, any]]] = {}
    for key, val in atlas_obj.m_RenderDataMap:
        name = spr_map.get(key)
        img = bundle_specific.get((b_stem, name), sprites.get(name))
        if img:
            tex_id = val.texture.m_PathID
            atlas_patches.setdefault(tex_id, []).append((name, img, val))

    print(f"   Tìm thấy {sum(len(v) for v in atlas_patches.values())} sprites cần vá vào Atlas")

    sample_tex = tex_objs[list(atlas_patches.keys())[0]].read()
    res_name = sample_tex.m_StreamData.path.replace("\\", "/").rsplit("/", 1)[-1]
    res_node = env.file.files[res_name]
    res_bytes = bytearray(bytes(res_node.reader.bytes if hasattr(res_node, "reader") else res_node.bytes))

    for tex_id, items in atlas_patches.items():
        tex = tex_objs[tex_id].read()
        print(f"   * Vá Texture Atlas: {tex.m_Name} ({len(items)} sprites)...")
        im_upright = Texture2DConverter.get_image_from_texture2d(tex, True)

        for spr_name, vi_img, val in items:
            r = val.textureRect
            x = round(r.x)
            y = tex.m_Height - round(r.y + r.height)
            target_w = round(r.width)
            target_h = round(r.height)

            if vi_img.size == (target_w, target_h):
                canvas = vi_img
            else:
                canvas = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
                off_x = (target_w - vi_img.width) // 2
                off_y = (target_h - vi_img.height) // 2
                canvas.paste(vi_img, (off_x, off_y), vi_img)

            im_upright.paste(canvas, (x, y))
            print(f"     + Đã dán {spr_name} tại ({x}, {y}) [size: {canvas.size}]")

        encoded, _ = Texture2DConverter.image_to_texture2d(
            im_upright, tex.m_TextureFormat, tex.object_reader.platform, tex.m_PlatformBlob, flip=True
        )

        start = int(tex.m_StreamData.offset)
        length = int(tex.m_StreamData.size)
        assert len(encoded) == length, f"Byte mismatch: {len(encoded)} != {length}"
        res_bytes[start : start + length] = encoded

    reader = EndianBinaryReader(bytes(res_bytes))
    reader.flags = res_node.flags
    env.file.files[res_name] = reader

    patched_bytes = env.file.save(packer="original")
    print(f"   ✓ Đóng gói thành công {bundle_name} ({len(patched_bytes):,} bytes)")
    return patched_bytes

def main():
    t0 = time.time()
    step1_copy_user_textures()

    print("\n=== BƯỚC 2: NẠP SPRITES VÀ ĐÓNG GÓI BUNDLE ===")
    sprites, bundle_specific = load_all_sprites()
    print(f"-> Tổng số sprite nạp được: {len(sprites)} chung, {len(bundle_specific)} riêng theo bundle")

    bundles_to_patch = ["ui_equipment.en.unity3d", "ui_commonex.en.unity3d"]
    patched_bundles: dict[str, bytes] = {}

    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    DIST_BUNDLES_DIR.mkdir(parents=True, exist_ok=True)

    for b_name in bundles_to_patch:
        patched_bytes = patch_atlas_bundle(b_name, sprites, bundle_specific)
        patched_bundles[b_name] = patched_bytes
        (STAGING_DIR / b_name).write_bytes(patched_bytes)
        (DIST_BUNDLES_DIR / b_name).write_bytes(patched_bytes)

    # Update manifest
    print("\n=== BƯỚC 3: CẬP NHẬT PATCH MANIFEST ===")
    if MANIFEST_PATH.exists():
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    else:
        manifest = {"version": "0.9.7", "bundles": {}}

    for b_name, b_bytes in patched_bundles.items():
        manifest["bundles"][b_name] = {
            "patched_sha256": hashlib.sha256(b_bytes).hexdigest(),
            "size_bytes": len(b_bytes),
            "textures_patched": len(sprites)
        }

    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print("  ✓ Đã cập nhật dist/patch_manifest.json")

    # Sync live games
    print("\n=== BƯỚC 4: ĐỒNG BỘ TRỰC TIẾP VÀO GAME (STANDALONE + STEAM) ===")
    for b_name, b_bytes in patched_bundles.items():
        # 1. Standalone
        if STANDALONE_PS.exists():
            (STANDALONE_PS / b_name).write_bytes(b_bytes)
            print(f"  ✓ Standalone Persistent_Store: {b_name} ({len(b_bytes):,} bytes)")

        # 2. Steam Persistent_Store
        if STEAM_PS.exists():
            (STEAM_PS / b_name).write_bytes(b_bytes)
            print(f"  ✓ Steam Persistent_Store: {b_name} ({len(b_bytes):,} bytes)")

        # 3. Steam InstallResource
        if STEAM_IR.exists():
            (STEAM_IR / b_name).write_bytes(b_bytes)
            print(f"  ✓ Steam InstallResource: {b_name} ({len(b_bytes):,} bytes)")

    # Repack dist ZIP
    print("\n=== BƯỚC 5: TẠO FILE NÉN BUNDLE PHÁT HÀNH ===")
    with zipfile.ZipFile(ZIP_OUTPUT, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in DIST_BUNDLES_DIR.glob("*.en.unity3d"):
            zf.write(f, arcname=f"AssetBundles/{f.name}")
        if MANIFEST_PATH.exists():
            zf.write(MANIFEST_PATH, arcname="patch_manifest.json")
    print(f"  ✓ Đã đóng gói {ZIP_OUTPUT.name}: {ZIP_OUTPUT.stat().st_size:,} bytes")

    print(f"\n🎉 HOÀN TẤT VÁ 2 TEXTURE MỤC 05 TRONG {time.time() - t0:.2f} GIÂY!")

if __name__ == "__main__":
    main()
