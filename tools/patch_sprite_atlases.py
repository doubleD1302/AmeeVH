#!/usr/bin/env python3
"""Patch SpriteAtlas textures in ui_commonex.en.unity3d and ui_equipment.en.unity3d.

Inserts translated sprites directly into sactx-* atlas sheets:
- Battle Results:
    zs_battle_result_6 -> "CHIẾN THẮNG!"
    zs_battle_result_5 -> "THẤT BẠI!"
    zs_battle_result_4 -> "THĂNG HOA!"
    zs_avg_chapter_complete -> "HOÀN THÀNH CHƯƠNG"
    btn_video_skip -> "BỎ QUA"
- Feature Titles & Headers:
    zs_agent_title, zs_agent_title_1, zs_task_title, zs_favor_title,
    zs_dailycheckin_title_1, zs_gacha_new, zs_activity_02_title,
    zs_activity_logo_02, zs_unlock_title_2, zs_vestige_title_11..17,
    tab_activity_03, zs_startowerhandbook_fatecard_activity,
    zs_soldier_main_logo_lang
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import time

from PIL import Image
import UnityPy
from UnityPy.export import Texture2DConverter
from UnityPy.streams import EndianBinaryReader

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKUP_DIR = PROJECT_ROOT / "backups" / "steam_installresource_backup_20261023"
DIST_DIR = PROJECT_ROOT / "dist" / "AssetBundles"
STAGING_DIR = PROJECT_ROOT / "staging" / "bundles_patched_vi" / "Persistent_Store" / "AssetBundles"
MANIFEST_PATH = PROJECT_ROOT / "dist" / "patch_manifest.json"

STEAM_PS = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stella Sora\Persistent_Store\AssetBundles")
STEAM_IR = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stella Sora\StellaSora_Data\StreamingAssets\InstallResource")

# Gather all available VI textures (EXCLUDING btn_video_skip to preserve pristine English SKIP)
VI_SOURCES = [
    PROJECT_ROOT / "dist" / "StellaSora_Texture_AnhVeChu_EN" / "04_NutBam_HuyHieu_Results_VI",
    PROJECT_ROOT / "dist" / "StellaSora_Texture_VI" / "03_TieuDe_Logos_Headers_VI",
    PROJECT_ROOT / "dist" / "StellaSora_Texture_AnhVeChu_EN" / "05_SuKien_Banners_Tabs_VI",
]


def load_all_vi_sprites() -> dict[str, Image.Image]:
    sprites: dict[str, Image.Image] = {}
    for s_path in VI_SOURCES:
        if s_path.is_file():
            pass
        elif s_path.is_dir():
            for p in s_path.glob("*.png"):
                name = p.stem.split("__")[-1]
                if name == "btn_video_skip":
                    continue
                sprites[name] = Image.open(p).convert("RGBA")
    sprites.pop("btn_video_skip", None)
    return sprites


def patch_atlas_bundle(bundle_name: str, vi_sprites: dict[str, Image.Image]) -> bytes:
    print(f"\n-> Đang xử lý bundle: {bundle_name}...")
    b_path = BACKUP_DIR / bundle_name
    env = UnityPy.load(b_path.read_bytes())

    atlases = [o for o in env.objects if o.type.name == "SpriteAtlas"]
    if not atlases:
        raise ValueError(f"No SpriteAtlas found in {bundle_name}")

    atlas_obj = atlases[0].read()
    spr_map = {s.read().m_RenderDataKey: s.read().m_Name for s in env.objects if s.type.name == "Sprite"}
    tex_objs = {o.path_id: o for o in env.objects if o.type.name == "Texture2D"}

    # Find which sprites in this atlas have VI replacements
    atlas_patches: dict[int, list[tuple[str, Image.Image, any]]] = {}
    for key, val in atlas_obj.m_RenderDataMap:
        name = spr_map.get(key)
        if name in vi_sprites:
            tex_id = val.texture.m_PathID
            atlas_patches.setdefault(tex_id, []).append((name, vi_sprites[name], val))

    print(f"   Tìm thấy {sum(len(v) for v in atlas_patches.values())} sprites cần vá vào Atlas")

    # Get resource stream container
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
            im_upright.paste(vi_img, (x, y))
            print(f"     + Đã dán {spr_name} tại ({x}, {y}) [size: {vi_img.size}]")

        # Encode upright image with flip=True to GPU layout
        encoded, _ = Texture2DConverter.image_to_texture2d(
            im_upright, tex.m_TextureFormat, tex.object_reader.platform, tex.m_PlatformBlob, flip=True
        )

        start = int(tex.m_StreamData.offset)
        length = int(tex.m_StreamData.size)
        assert len(encoded) == length, f"Byte mismatch: {len(encoded)} != {length}"
        res_bytes[start : start + length] = encoded

    # Replace stream node
    reader = EndianBinaryReader(bytes(res_bytes))
    reader.flags = res_node.flags
    env.file.files[res_name] = reader

    patched_bytes = env.file.save(packer="original")
    print(f"   ✓ Đóng gói thành công {bundle_name} ({len(patched_bytes):,} bytes)")
    return patched_bytes


def main():
    print("=" * 70)
    print("VÁ TRIỆT ĐỂ MỤC RESULTS VÀ SPRITE ATLAS CHO GAME STELLA SORA")
    print("=" * 70)

    vi_sprites = load_all_vi_sprites()
    print(f"-> Tổng số sprite Việt Hóa thu thập được: {len(vi_sprites)}")

    results_check = ["zs_battle_result_4", "zs_battle_result_5", "zs_battle_result_6", "zs_avg_chapter_complete"]
    for r in results_check:
        print(f"   ✓ Sprite {r}: {'CÓ' if r in vi_sprites else 'THIẾU'}")

    bundles_to_patch = ["ui_commonex.en.unity3d", "ui_equipment.en.unity3d"]
    patched_bundles: dict[str, bytes] = {}

    for b_name in bundles_to_patch:
        patched_bytes = patch_atlas_bundle(b_name, vi_sprites)
        patched_bundles[b_name] = patched_bytes

        # Save to staging and dist
        (STAGING_DIR / b_name).write_bytes(patched_bytes)
        (DIST_DIR / b_name).write_bytes(patched_bytes)

    # Update manifest
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    for b_name, b_bytes in patched_bundles.items():
        manifest["bundles"][b_name] = {
            "patched_sha256": hashlib.sha256(b_bytes).hexdigest(),
            "size_bytes": len(b_bytes),
            "textures_patched": len(vi_sprites)
        }

    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print("\n-> Triển khai trực tiếp 2 bundle kết quả vào Steam...")
    for b_name, b_bytes in patched_bundles.items():
        # Persistent_Store
        p_ps = STEAM_PS / b_name
        p_ps.write_bytes(b_bytes)
        # InstallResource
        p_ir = STEAM_IR / b_name
        p_ir.write_bytes(b_bytes)
        print(f"   ✓ Đã ghi đè {b_name} vào cả Persistent_Store và InstallResource của Steam")

    print("\n" + "=" * 70)
    print("🎉 HOÀN TẤT VÁ MỤC RESULTS (CHIẾN THẮNG, THẤT BẠI, THĂNG HOA) VÀO STEAM!")
    print("=" * 70)


if __name__ == "__main__":
    main()
