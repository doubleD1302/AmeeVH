#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Apply 86 Vietnamese Textures (Category 4 Buttons/Results + Category 7 OtherUI):
- Sources:
  * work/textures/otherui_20261025_r01/candidate_part02_r02 (13 files)
  * dist/StellaSora_Textures_VI_ButtonsResults_20261025 (73 files)
- Targets:
  * Standalone Texture2D bundles (9 bundles, 23 textures):
    ui_activity_20103, ui_activity_30103, ui_activity_30104,
    ui_activity__1110701, ui_activity__400018, ui_activity__500001,
    ui_activity__510001, ui_big_sprites, ui_play_towerdefence
  * SpriteAtlas bundles (2 bundles, 63 textures):
    ui_commonex, ui_equipment
- Dual-sync to Standalone and Steam installations.
- Update patch_manifest.json and package dist/StellaSora_AssetBundles_VI.zip.
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
SRC_OTHERUI = PROJECT_ROOT / "work" / "textures" / "otherui_20261025_r01" / "candidate_part02_r02"
SRC_BUTTONS = PROJECT_ROOT / "dist" / "StellaSora_Textures_VI_ButtonsResults_20261025"

DIST_BUNDLES_DIR = PROJECT_ROOT / "dist" / "AssetBundles"
STAGING_DIR = PROJECT_ROOT / "staging" / "bundles_patched_vi" / "Persistent_Store" / "AssetBundles"
MANIFEST_PATH = PROJECT_ROOT / "dist" / "patch_manifest.json"
ZIP_OUTPUT = PROJECT_ROOT / "dist" / "StellaSora_AssetBundles_VI.zip"

STANDALONE_PS = Path(r"c:\YostarGames\StellaSora_EN\Persistent_Store\AssetBundles")
STEAM_PS = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stella Sora\Persistent_Store\AssetBundles")
STEAM_IR = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stella Sora\StellaSora_Data\StreamingAssets\InstallResource")

def get_bundle_and_sprite(fname: str) -> tuple[str, str]:
    stem = Path(fname).stem
    if stem.startswith("ui_activity__"):
        parts = stem.split("__")
        b_name = f"{parts[0]}__{parts[1]}.en.unity3d"
        spr_name = "__".join(parts[2:])
        return b_name, spr_name
    parts = stem.split("__")
    b_name = f"{parts[0]}.en.unity3d"
    spr_name = parts[1] if len(parts) > 1 else stem
    return b_name, spr_name

def step1_copy_distribution_files():
    print("=== BƯỚC 1: LƯU TRỮ VÀO CÁC THƯ MỤC PHÂN PHỐI TEXTURE_VI ===")
    
    # 1. Category 4: Buttons & Results (73 files)
    dst_c4_1 = PROJECT_ROOT / "dist" / "StellaSora_Texture_VI" / "04_NutBam_HuyHieu_Results_VI"
    dst_c4_2 = PROJECT_ROOT / "dist" / "StellaSora_Texture_AnhVeChu_EN" / "04_NutBam_HuyHieu_Results_VI"
    dst_c4_1.mkdir(parents=True, exist_ok=True)
    dst_c4_2.mkdir(parents=True, exist_ok=True)
    
    c4_count = 0
    for f in SRC_BUTTONS.glob("*.png"):
        shutil.copy2(f, dst_c4_1 / f.name)
        shutil.copy2(f, dst_c4_2 / f.name)
        c4_count += 1
    print(f"  ✓ Đã sao chép {c4_count} ảnh mục 04 vào 04_NutBam_HuyHieu_Results_VI")

    # 2. Category 7: Other UI (13 files)
    dst_c7_1 = PROJECT_ROOT / "dist" / "StellaSora_Texture_VI" / "07_GiaoDienKhac_OtherUI_VI"
    dst_c7_2 = PROJECT_ROOT / "dist" / "StellaSora_Texture_AnhVeChu_EN" / "07_GiaoDienKhac_OtherUI_VI"
    dst_c7_1.mkdir(parents=True, exist_ok=True)
    dst_c7_2.mkdir(parents=True, exist_ok=True)
    
    c7_count = 0
    for f in SRC_OTHERUI.glob("*.png"):
        shutil.copy2(f, dst_c7_1 / f.name)
        shutil.copy2(f, dst_c7_2 / f.name)
        c7_count += 1
    print(f"  ✓ Đã sao chép {c7_count} ảnh mục 07 vào 07_GiaoDienKhac_OtherUI_VI")

def patch_standalone_textures(b_name: str, items: list[tuple[str, Path]]) -> bytes:
    print(f"\n-> Đang vá Texture2D độc lập cho: {b_name} ({len(items)} textures)...")
    b_path = STANDALONE_PS / b_name
    raw_b = b_path.read_bytes()
    env = UnityPy.load(raw_b)

    tex_map = {obj.read().m_Name: (obj, obj.read()) for obj in env.objects if obj.type.name == "Texture2D"}
    sample_tex = list(tex_map.values())[0][1]
    res_name = sample_tex.m_StreamData.path.replace("\\", "/").rsplit("/", 1)[-1]
    res_node = env.file.files[res_name]
    res_bytes = bytearray(bytes(res_node.reader.bytes if hasattr(res_node, "reader") else res_node.bytes))

    for spr_name, f_png in items:
        obj, tex = tex_map[spr_name]
        target_size = (tex.m_Width, tex.m_Height)
        start = int(tex.m_StreamData.offset)
        length = int(tex.m_StreamData.size)

        with Image.open(f_png) as img:
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
        assert len(encoded) == length, f"Byte mismatch for {spr_name}: {len(encoded)} != {length}"
        res_bytes[start : start + length] = encoded
        print(f"   + Đã thay thế Texture2D: {spr_name} ({target_size[0]}x{target_size[1]})")

    reader = EndianBinaryReader(bytes(res_bytes))
    reader.flags = res_node.flags
    env.file.files[res_name] = reader
    patched_bytes = env.file.save(packer="original")
    print(f"   ✓ Đóng gói thành công {b_name} ({len(patched_bytes):,} bytes)")
    return patched_bytes

def patch_atlas_bundle(b_name: str, items: list[tuple[str, Path]]) -> bytes:
    print(f"\n-> Đang vá SpriteAtlas cho: {b_name} ({len(items)} sprites)...")
    b_path = STANDALONE_PS / b_name
    env = UnityPy.load(b_path.read_bytes())

    atlases = [o for o in env.objects if o.type.name == "SpriteAtlas"]
    if not atlases:
        raise ValueError(f"No SpriteAtlas in {b_name}")

    atlas_obj = atlases[0].read()
    spr_map = {s.read().m_RenderDataKey: s.read().m_Name for s in env.objects if s.type.name == "Sprite"}
    tex_objs = {o.path_id: o for o in env.objects if o.type.name == "Texture2D"}

    items_dict = {spr_name: f_path for spr_name, f_path in items}

    atlas_patches: dict[int, list[tuple[str, Path, any]]] = {}
    for key, val in atlas_obj.m_RenderDataMap:
        name = spr_map.get(key)
        if name in items_dict:
            tex_id = val.texture.m_PathID
            atlas_patches.setdefault(tex_id, []).append((name, items_dict[name], val))

    print(f"   Tìm thấy {sum(len(v) for v in atlas_patches.values())} sprites trong SpriteAtlas")

    sample_tex = tex_objs[list(atlas_patches.keys())[0]].read()
    res_name = sample_tex.m_StreamData.path.replace("\\", "/").rsplit("/", 1)[-1]
    res_node = env.file.files[res_name]
    res_bytes = bytearray(bytes(res_node.reader.bytes if hasattr(res_node, "reader") else res_node.bytes))

    for tex_id, patches in atlas_patches.items():
        tex = tex_objs[tex_id].read()
        print(f"   * Vá Texture Atlas: {tex.m_Name} ({len(patches)} sprites)...")
        im_upright = Texture2DConverter.get_image_from_texture2d(tex, True)

        for spr_name, f_png, val in patches:
            r = val.textureRect
            x = round(r.x)
            y = tex.m_Height - round(r.y + r.height)
            target_w = round(r.width)
            target_h = round(r.height)

            with Image.open(f_png) as img:
                vi_img = img.convert("RGBA")

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
    print(f"   ✓ Đóng gói thành công {b_name} ({len(patched_bytes):,} bytes)")
    return patched_bytes

def main():
    t0 = time.time()
    step1_copy_distribution_files()

    all_files = [(SRC_OTHERUI, f) for f in SRC_OTHERUI.glob("*.png")] + \
                [(SRC_BUTTONS, f) for f in SRC_BUTTONS.glob("*.png")]
    print(f"\n=== BƯỚC 2: PHÂN LOẠI {len(all_files)} TEXTURES VÀO ASSETBUNDLES ===")

    bundle_groups = {}
    for src_dir, f in all_files:
        b_name, spr_name = get_bundle_and_sprite(f.name)
        bundle_groups.setdefault(b_name, []).append((spr_name, f))

    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    DIST_BUNDLES_DIR.mkdir(parents=True, exist_ok=True)

    patched_bundles: dict[str, bytes] = {}

    for b_name, items in sorted(bundle_groups.items()):
        if b_name in ["ui_commonex.en.unity3d", "ui_equipment.en.unity3d"]:
            patched_bytes = patch_atlas_bundle(b_name, items)
        else:
            patched_bytes = patch_standalone_textures(b_name, items)
        
        patched_bundles[b_name] = patched_bytes
        (STAGING_DIR / b_name).write_bytes(patched_bytes)
        (DIST_BUNDLES_DIR / b_name).write_bytes(patched_bytes)

    # Step 3: Dual-sync to games
    print("\n=== BƯỚC 3: ĐỒNG BỘ TRỰC TIẾP VÀO GAME (STANDALONE + STEAM) ===")
    for b_name, b_bytes in patched_bundles.items():
        # Standalone
        if STANDALONE_PS.exists():
            (STANDALONE_PS / b_name).write_bytes(b_bytes)
            print(f"  ✓ Standalone PS: {b_name} ({len(b_bytes):,} bytes)")
        # Steam PS
        if STEAM_PS.exists():
            (STEAM_PS / b_name).write_bytes(b_bytes)
            print(f"  ✓ Steam PS:      {b_name} ({len(b_bytes):,} bytes)")
        # Steam IR
        if (STEAM_IR / b_name).exists():
            (STEAM_IR / b_name).write_bytes(b_bytes)
            print(f"  ✓ Steam IR:      {b_name} ({len(b_bytes):,} bytes)")

    # Step 4: Manifest
    print("\n=== BƯỚC 4: CẬP NHẬT PATCH MANIFEST ===")
    if MANIFEST_PATH.exists():
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    else:
        manifest = {"version": "0.9.7", "bundles": {}}

    for b_name, b_bytes in patched_bundles.items():
        manifest["bundles"][b_name] = {
            "patched_sha256": hashlib.sha256(b_bytes).hexdigest(),
            "size_bytes": len(b_bytes),
            "textures_patched": len(bundle_groups[b_name])
        }

    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print("  ✓ Đã cập nhật dist/patch_manifest.json")

    # Step 5: Repack ZIP
    print("\n=== BƯỚC 5: TẠO FILE NÉN BUNDLE PHÁT HÀNH ===")
    with zipfile.ZipFile(ZIP_OUTPUT, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in DIST_BUNDLES_DIR.glob("*.en.unity3d"):
            zf.write(f, arcname=f"AssetBundles/{f.name}")
        if MANIFEST_PATH.exists():
            zf.write(MANIFEST_PATH, arcname="patch_manifest.json")
    print(f"  ✓ Đã đóng gói {ZIP_OUTPUT.name}: {ZIP_OUTPUT.stat().st_size:,} bytes")

    print(f"\n🎉 HOÀN TẤT VÁ TOÀN BỘ 86 TEXTURES TRONG {time.time() - t0:.2f} GIÂY!")

if __name__ == "__main__":
    main()
