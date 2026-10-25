#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Apply Vietnamese Mall Part 16 Textures:
- Sourced from: dist/StellaSora_Textures_Chua_Viet_Hoa_Dang_Hoat_Dong/03_CuaHang_TheThang_TrangPhuc_Mall_VI_Phan16
  Contains 16 translated textures:
  * 1 UI activity texture: ui_activity__302001__icon_mallcheckinact_tabel_lang.png (164x71)
  * 15 Mall Shop skin/pass banner textures: ui_big_sprites__mallAdv.*.png (1066x570 / 1068x570)
- Copies to distribution folders:
  * dist/StellaSora_Texture_VI/07_GiaoDienKhac_OtherUI_VI/
  * dist/StellaSora_Texture_AnhVeChu_EN/07_GiaoDienKhac_OtherUI_VI/
- Patches Texture2D assets in:
  * ui_activity__302001.en.unity3d
  * ui_big_sprites.en.unity3d
- Performs readback decode verification for all 16 textures.
- Dual-syncs to Standalone Yostar and Steam installations (both PS and IR).
- Updates patch_manifest.json and repacks dist/StellaSora_AssetBundles_VI.zip.
- Executes verify_deployed_game_data.py to assert data integrity.
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
sys.path.insert(0, str(PROJECT_ROOT))

USER_SRC = PROJECT_ROOT / "dist" / "StellaSora_Textures_Chua_Viet_Hoa_Dang_Hoat_Dong" / "03_CuaHang_TheThang_TrangPhuc_Mall_VI_Phan16"

DIST_BUNDLES_DIR = PROJECT_ROOT / "dist" / "AssetBundles"
STAGING_DIR = PROJECT_ROOT / "staging" / "bundles_patched_vi" / "Persistent_Store" / "AssetBundles"
MANIFEST_PATH = PROJECT_ROOT / "dist" / "patch_manifest.json"
ZIP_OUTPUT = PROJECT_ROOT / "dist" / "StellaSora_AssetBundles_VI.zip"

STANDALONE_PS = Path(r"c:\YostarGames\StellaSora_EN\Persistent_Store\AssetBundles")
STEAM_PS = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stella Sora\Persistent_Store\AssetBundles")
STEAM_IR = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stella Sora\StellaSora_Data\StreamingAssets\InstallResource")

TARGET_PNGS = [
    "ui_activity__302001__icon_mallcheckinact_tabel_lang.png",
    "ui_big_sprites__mallAdv.month_01.png",
    "ui_big_sprites__mallAdv.skin_10704_lang.png",
    "ui_big_sprites__mallAdv.skin_11003_lang.png",
    "ui_big_sprites__mallAdv.skin_11203_lang.png",
    "ui_big_sprites__mallAdv.skin_11903_lang.png",
    "ui_big_sprites__mallAdv.skin_12503_lang.png",
    "ui_big_sprites__mallAdv.skin_12603_lang.png",
    "ui_big_sprites__mallAdv.skin_13204_lang.png",
    "ui_big_sprites__mallAdv.skin_13303_lang.png",
    "ui_big_sprites__mallAdv.skin_13403_lang.png",
    "ui_big_sprites__mallAdv.skin_13503_lang.png",
    "ui_big_sprites__mallAdv.skin_14103_lang.png",
    "ui_big_sprites__mallAdv.skin_14403_lang.png",
    "ui_big_sprites__mallAdv.skin_14903_lang.png",
    "ui_big_sprites__mallAdv.skin_15603_lang.png",
]

def step1_copy_distribution_files():
    print("=== BƯỚC 1: LƯU TRỮ VÀO THƯ MỤC PHÂN PHỐI TEXTURE_VI ===")
    assert USER_SRC.exists(), f"Không tìm thấy thư mục nguồn: {USER_SRC}"

    dst_dirs = [
        PROJECT_ROOT / "dist" / "StellaSora_Texture_VI" / "07_GiaoDienKhac_OtherUI_VI",
        PROJECT_ROOT / "dist" / "StellaSora_Texture_AnhVeChu_EN" / "07_GiaoDienKhac_OtherUI_VI",
    ]

    for d in dst_dirs:
        d.mkdir(parents=True, exist_ok=True)
        for fname in TARGET_PNGS:
            src_f = USER_SRC / fname
            assert src_f.exists(), f"Thiếu file nguồn: {fname}"
            shutil.copy2(src_f, d / fname)
        print(f"  ✓ Đã sao chép 16 ảnh vào {d.relative_to(PROJECT_ROOT)}")

def patch_bundle_textures(b_name: str, items: list[tuple[str, Path]]) -> bytes:
    print(f"\n-> Đang vá bundle: {b_name} ({len(items)} textures)...")
    
    # Load from dist or fallback to staging or backup
    src_path = DIST_BUNDLES_DIR / b_name
    if not src_path.exists():
        src_path = STAGING_DIR / b_name
    if not src_path.exists():
        src_path = PROJECT_ROOT / "backups" / "steam_installresource_backup_20261023" / b_name
    assert src_path.exists(), f"Không tìm thấy file nguồn bundle: {b_name}"

    raw_b = src_path.read_bytes()
    env = UnityPy.load(raw_b)

    tex_map = {obj.read().m_Name: (obj, obj.read()) for obj in env.objects if obj.type.name == "Texture2D"}
    spr_map = {obj.read().m_Name: obj.read() for obj in env.objects if obj.type.name == "Sprite"}

    sample_tex = list(tex_map.values())[0][1]
    res_name = sample_tex.m_StreamData.path.replace("\\", "/").rsplit("/", 1)[-1]
    res_node = env.file.files[res_name]
    res_bytes = bytearray(bytes(res_node.reader.bytes if hasattr(res_node, "reader") else res_node.bytes))

    for spr_name, f_png in items:
        assert spr_name in tex_map, f"Texture2D {spr_name} không tìm thấy trong {b_name}"
        obj, tex = tex_map[spr_name]
        spr = spr_map.get(spr_name)
        
        target_size = (tex.m_Width, tex.m_Height)
        start = int(tex.m_StreamData.offset)
        length = int(tex.m_StreamData.size)

        with Image.open(f_png) as img:
            vi_img = img.convert("RGBA")

        # Determine exact coordinate offset using Sprite textureRect if available
        if spr and hasattr(spr, "m_RD") and hasattr(spr.m_RD, "textureRect"):
            r = spr.m_RD.textureRect
            off_x = round(r.x)
            off_y = tex.m_Height - round(r.y + r.height)
        else:
            off_x = (target_size[0] - vi_img.width) // 2
            off_y = (target_size[1] - vi_img.height) // 2

        # Use original upright texture as background canvas for seamless border blending
        canvas = tex.image.copy()
        canvas.paste(vi_img, (off_x, off_y), vi_img)

        encoded, _ = Texture2DConverter.image_to_texture2d(
            canvas, tex.m_TextureFormat, tex.object_reader.platform, tex.m_PlatformBlob
        )
        assert len(encoded) == length, f"Byte mismatch cho {spr_name}: {len(encoded)} != {length}"
        res_bytes[start : start + length] = encoded
        print(f"   + Đã thay thế Texture2D: {spr_name} ({target_size[0]}x{target_size[1]}) tại offset ({off_x}, {off_y})")

    reader = EndianBinaryReader(bytes(res_bytes))
    reader.flags = res_node.flags
    env.file.files[res_name] = reader
    patched_bytes = env.file.save(packer="original")

    # Readback verification
    print(f"   -> Đang xác thực giải mã readback cho {b_name}...")
    v_env = UnityPy.load(patched_bytes)
    v_texs = {o.read().m_Name: o.read() for o in v_env.objects if o.type.name == "Texture2D"}
    for spr_name, _ in items:
        assert spr_name in v_texs, f"Readback: thiếu {spr_name}"
        v_img = v_texs[spr_name].image
        assert v_img is not None, f"Readback: không giải mã được {spr_name}"
    print(f"   ✓ Đóng gói & xác thực readback thành công {b_name} ({len(patched_bytes):,} bytes)")

    return patched_bytes

def main():
    t0 = time.time()
    step1_copy_distribution_files()

    print("\n=== BƯỚC 2: PHÂN LOẠI & VÁ 16 TEXTURES VÀO ASSETBUNDLES ===")
    
    # 1. Activity Bundle: ui_activity__302001
    activity_items = [
        ("icon_mallcheckinact_tabel_lang", USER_SRC / "ui_activity__302001__icon_mallcheckinact_tabel_lang.png")
    ]
    
    # 2. Big Sprites Bundle: ui_big_sprites
    big_sprites_items = []
    for fname in TARGET_PNGS:
        if fname.startswith("ui_big_sprites__"):
            spr_name = fname.replace("ui_big_sprites__", "").replace(".png", "")
            big_sprites_items.append((spr_name, USER_SRC / fname))

    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    DIST_BUNDLES_DIR.mkdir(parents=True, exist_ok=True)

    patched_bundles: dict[str, bytes] = {}

    # Patch ui_activity__302001.en.unity3d
    b_act_name = "ui_activity__302001.en.unity3d"
    b_act_bytes = patch_bundle_textures(b_act_name, activity_items)
    patched_bundles[b_act_name] = b_act_bytes
    (STAGING_DIR / b_act_name).write_bytes(b_act_bytes)
    (DIST_BUNDLES_DIR / b_act_name).write_bytes(b_act_bytes)

    # Patch ui_big_sprites.en.unity3d
    b_big_name = "ui_big_sprites.en.unity3d"
    b_big_bytes = patch_bundle_textures(b_big_name, big_sprites_items)
    patched_bundles[b_big_name] = b_big_bytes
    (STAGING_DIR / b_big_name).write_bytes(b_big_bytes)
    (DIST_BUNDLES_DIR / b_big_name).write_bytes(b_big_bytes)

    print("\n=== BƯỚC 3: ĐỒNG BỘ TRỰC TIẾP VÀO GAME (YOSTAR STANDALONE + STEAM) ===")
    for b_name, b_bytes in patched_bundles.items():
        # Standalone PS
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

    print("\n=== BƯỚC 4: CẬP NHẬT PATCH MANIFEST & TẠO FILE NÉN BUNDLE ===")
    if MANIFEST_PATH.exists():
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    else:
        manifest = {"version": "0.9.7", "bundles": {}}

    manifest.setdefault("bundles", {})
    
    # Update bundle entries
    # ui_activity__302001: previously 1, now +1 = 2
    act_prev_count = manifest["bundles"].get(b_act_name, {}).get("textures_patched_count", 1)
    manifest["bundles"][b_act_name] = {
        "patched_sha256": hashlib.sha256(b_act_bytes).hexdigest(),
        "size_bytes": len(b_act_bytes),
        "textures_patched": act_prev_count + len(activity_items),
        "textures_patched_count": act_prev_count + len(activity_items),
        "relative_path": f"Persistent_Store/AssetBundles/{b_act_name}"
    }

    # ui_big_sprites: previously 10, now +15 = 25
    big_prev_count = manifest["bundles"].get(b_big_name, {}).get("textures_patched", 10)
    manifest["bundles"][b_big_name] = {
        "patched_sha256": hashlib.sha256(b_big_bytes).hexdigest(),
        "size_bytes": len(b_big_bytes),
        "textures_patched": big_prev_count + len(big_sprites_items),
        "textures_patched_count": big_prev_count + len(big_sprites_items),
        "relative_path": f"Persistent_Store/AssetBundles/{b_big_name}"
    }

    manifest["total_textures_patched"] = manifest.get("total_textures_patched", 401) + len(TARGET_PNGS)
    manifest["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")

    # Repack ZIP output
    with zipfile.ZipFile(ZIP_OUTPUT, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(DIST_BUNDLES_DIR.glob("*.en.unity3d")):
            zf.write(f, arcname=f"Persistent_Store/AssetBundles/{f.name}")
        zf.writestr("patch_manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))

    zip_bytes = ZIP_OUTPUT.read_bytes()
    manifest["package_zip"] = {
        "filename": ZIP_OUTPUT.name,
        "size_bytes": len(zip_bytes),
        "sha256": hashlib.sha256(zip_bytes).hexdigest(),
        "total_bundles": len(manifest["bundles"])
    }
    manifest["asset_bundles_package_sha256"] = manifest["package_zip"]["sha256"]
    manifest["asset_bundles_package_size"] = manifest["package_zip"]["size_bytes"]

    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"  ✓ Đã cập nhật dist/patch_manifest.json")
    print(f"  ✓ Đã đóng gói {ZIP_OUTPUT.name}: {ZIP_OUTPUT.stat().st_size:,} bytes")

    print("\n=== BƯỚC 5: CHẠY KIỂM CHỨNG TỔNG THỂ DỮ LIỆU GAME ===")
    from tools.verify_deployed_game_data import main as run_verify
    run_verify()

    elapsed = time.time() - t0
    print(f"\n🎉 HOÀN TẤT ÁP DỤNG THÀNH CÔNG 16 TEXTURE CỬA HÀNG VÀ TRANG PHỤC MALL TRONG {elapsed:.2f} GIÂY!")

if __name__ == "__main__":
    main()
