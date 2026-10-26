#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Master Patch & Deployment Script for Gacha Banner Cover Textures (25 delivered items).
1. Standardizes delivered VI PNGs into dist/StellaSora_Texture_VI/08_Banner_GachaCover_VI/
2. Patches 25 Unity AssetBundles in Persistent_Store/AssetBundles/*.en.unity3d
3. Uses byte-exact stream data (.resS) replacement and original UnityPy packer
4. Verifies 100% readback on all 25 patched bundles
5. Dual-deploys to Yostar and Steam installations with .orig_en backups
6. Updates dist/AssetBundles/, staging/, and patch_manifest.json
"""

import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import time

from PIL import Image
import UnityPy
from UnityPy.export import Texture2DConverter
from UnityPy.streams import EndianBinaryReader

ROOT = Path(r"C:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
DELIV_DIR = ROOT / "dist/Xuat_Texture_Banner_Lon_Chua_Dich/01_Logo_TieuDe_Gacha_Cover/deliverables_20261027/StellaSora_Banner_VI_Completed_20261027"
STD_TEX_DIR = ROOT / "dist/StellaSora_Texture_VI/08_Banner_GachaCover_VI"
STAGING_DIR = ROOT / "staging/bundles_patched_vi/Persistent_Store/AssetBundles"
DIST_BUNDLES_DIR = ROOT / "dist/AssetBundles"
MANIFEST_PATH = ROOT / "dist/patch_manifest.json"

YOSTAR_BUNDLES_DIR = ROOT.parent / "Persistent_Store" / "AssetBundles"
STEAM_BUNDLES_DIR = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stella Sora\Persistent_Store\AssetBundles")

def step1_standardize_textures():
    print("=== BƯỚC 1: CHUẨN HÓA VÀ LƯU TRỮ TEXTURE VIỆT HÓA ===")
    STD_TEX_DIR.mkdir(parents=True, exist_ok=True)
    pngs = sorted(list(DELIV_DIR.glob("*.png")))
    print(f"-> Tìm thấy {len(pngs)} tệp PNG trong deliverables.")
    
    std_mapping = []
    for p in pngs:
        parts = p.name.replace(".png", "").split("__")
        cover_tag = parts[0] # e.g. Cover_10114
        tex_name = parts[1]  # e.g. cover_10114_lang
        cid = cover_tag.replace("Cover_", "").lower()
        bundle_name = f"ui_gachacover_cover_{cid}.en.unity3d"
        std_name = f"ui_gachacover_cover_{cid}__{tex_name}.png"
        std_path = STD_TEX_DIR / std_name
        shutil.copy2(p, std_path)
        std_mapping.append({
            "orig_file": p,
            "std_file": std_path,
            "bundle_name": bundle_name,
            "tex_name": tex_name
        })
    print(f"✓ Đã chuẩn hóa {len(std_mapping)} texture vào: {STD_TEX_DIR.relative_to(ROOT)}")
    return std_mapping

def step2_patch_bundles(std_mapping):
    print("\n=== BƯỚC 2: MÃ HÓA VÀ PATCH VÀO ASSETBUNDLES ===")
    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    DIST_BUNDLES_DIR.mkdir(parents=True, exist_ok=True)
    
    patched_bundles = []
    errors = []
    
    for item in std_mapping:
        b_name = item["bundle_name"]
        tex_target = item["tex_name"]
        png_path = item["std_file"]
        
        # Source bundle from Yostar live directory
        src_bundle_path = YOSTAR_BUNDLES_DIR / b_name
        if not src_bundle_path.exists():
            errors.append(f"Source bundle not found: {b_name}")
            continue
            
        # Ensure backup of original bundle (.orig_en)
        backup_path = YOSTAR_BUNDLES_DIR / f"{b_name}.orig_en"
        if not backup_path.exists():
            shutil.copy2(src_bundle_path, backup_path)
            
        raw_bytes = backup_path.read_bytes()
        env = UnityPy.load(raw_bytes)
        
        target_obj = None
        target_tex = None
        for obj in env.objects:
            if obj.type.name == "Texture2D":
                tex = obj.read()
                name = getattr(tex, "m_Name", "") or getattr(tex, "name", "")
                if name == tex_target:
                    target_obj = obj
                    target_tex = tex
                    break
                    
        if not target_obj or not target_tex:
            errors.append(f"Texture2D {tex_target} not found in {b_name}")
            continue
            
        target_size = (target_tex.m_Width, target_tex.m_Height)
        start = int(target_tex.m_StreamData.offset)
        length = int(target_tex.m_StreamData.size)
        
        res_name = target_tex.m_StreamData.path.replace("\\", "/").rsplit("/", 1)[-1]
        if res_name not in env.file.files:
            errors.append(f"Resource stream {res_name} not found in {b_name}")
            continue
            
        res_node = env.file.files[res_name]
        res_bytes = bytearray(bytes(res_node.reader.bytes if hasattr(res_node, "reader") else res_node.bytes))
        
        with Image.open(png_path) as img:
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
            canvas, target_tex.m_TextureFormat, target_tex.object_reader.platform, target_tex.m_PlatformBlob
        )
        
        if len(encoded) != length:
            errors.append(f"Byte mismatch {tex_target} in {b_name}: {len(encoded)} != {length}")
            continue
            
        res_bytes[start : start + length] = encoded
        
        for key, node in list(env.file.files.items()):
            raw_node = bytes(res_bytes) if key == res_name else (bytes(node.reader.bytes) if hasattr(node, "reader") else bytes(node.bytes))
            reader = EndianBinaryReader(raw_node)
            reader.flags = node.flags
            env.file.files[key] = reader
            
        patched_bytes = env.file.save(packer="original")
        
        # Verify readback
        try:
            v_env = UnityPy.load(patched_bytes)
            v_matched = False
            for o in v_env.objects:
                if o.type.name == "Texture2D":
                    t = o.read()
                    n = getattr(t, "m_Name", "") or getattr(t, "name", "")
                    if n == tex_target:
                        _ = t.image
                        v_matched = True
                        break
            if not v_matched:
                errors.append(f"{b_name} readback verification failed!")
                continue
        except Exception as e:
            errors.append(f"{b_name} readback error: {e}")
            continue
            
        # Write to staging and dist
        (STAGING_DIR / b_name).write_bytes(patched_bytes)
        (DIST_BUNDLES_DIR / b_name).write_bytes(patched_bytes)
        patched_bundles.append((b_name, tex_target, len(patched_bytes)))
        print(f"  ✓ Patched {b_name:<38} | {tex_target:<20} | {len(patched_bytes):,} bytes")
        
    print(f"\n✓ Hoàn tất patch {len(patched_bundles)}/25 AssetBundles. Lỗi: {len(errors)}")
    if errors:
        for err in errors:
            print(f"  ❌ {err}")
    assert len(patched_bundles) == 25 and len(errors) == 0
    return patched_bundles

def step3_dual_deploy(patched_bundles):
    print("\n=== BƯỚC 3: DUAL-DEPLOY SANG YOSTAR & STEAM LIVE CLIENTS ===")
    for b_name, _, _ in patched_bundles:
        src_patched = DIST_BUNDLES_DIR / b_name
        
        # 1. Yostar Client
        dst_yostar = YOSTAR_BUNDLES_DIR / b_name
        shutil.copy2(src_patched, dst_yostar)
        
        # 2. Steam Client
        if STEAM_BUNDLES_DIR.exists():
            dst_steam = STEAM_BUNDLES_DIR / b_name
            # backup steam original if exists
            steam_orig = STEAM_BUNDLES_DIR / f"{b_name}.orig_en"
            if dst_steam.exists() and not steam_orig.exists():
                shutil.copy2(dst_steam, steam_orig)
            shutil.copy2(src_patched, dst_steam)
            
    print(f"✓ Đã đồng bộ 25 AssetBundles vào Yostar: {YOSTAR_BUNDLES_DIR}")
    if STEAM_BUNDLES_DIR.exists():
        print(f"✓ Đã đồng bộ 25 AssetBundles vào Steam: {STEAM_BUNDLES_DIR}")

def step4_verify_live_deploy(patched_bundles):
    print("\n=== BƯỚC 4: XÁC MINH TRỰC TIẾP TRÊN TẬP TIN LIVE CLIENT ===")
    verified_count = 0
    for b_name, tex_target, _ in patched_bundles:
        live_bundle = YOSTAR_BUNDLES_DIR / b_name
        env = UnityPy.load(str(live_bundle))
        for obj in env.objects:
            if obj.type.name == "Texture2D":
                tex = obj.read()
                name = getattr(tex, "m_Name", "") or getattr(tex, "name", "")
                if name == tex_target:
                    im = tex.image
                    assert im.size == (tex.m_Width, tex.m_Height)
                    verified_count += 1
                    break
    print(f"✓ XÁC NHẬN: 100% {verified_count}/25 bundle live load thành công không lỗi!")

def step5_update_manifest(patched_bundles):
    print("\n=== BƯỚC 5: CẬP NHẬT PATCH_MANIFEST.JSON ===")
    if MANIFEST_PATH.exists():
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    else:
        manifest = {"version": "0.9.7", "bundles": {}}
        
    b_map = manifest.setdefault("bundles", {})
    for b_name, tex_target, size in patched_bundles:
        p = DIST_BUNDLES_DIR / b_name
        sha256 = hashlib.sha256(p.read_bytes()).hexdigest()
        b_map[b_name] = {
            "size": size,
            "sha256": sha256,
            "category": "08_Banner_GachaCover_VI",
            "texture": tex_target
        }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✓ Đã cập nhật manifest: {MANIFEST_PATH.name} (hiện có {len(b_map)} bundles theo dõi)")

if __name__ == "__main__":
    t0 = time.time()
    mapping = step1_standardize_textures()
    patched = step2_patch_bundles(mapping)
    step3_dual_deploy(patched)
    step4_verify_live_deploy(patched)
    step5_update_manifest(patched)
    elapsed = time.time() - t0
    print(f"\n=======================================================")
    print(f"HOÀN THÀNH TÍCH HỢP 25 BANNER GACHA TRONG {elapsed:.2f} GIÂY!")
    print(f"=======================================================")
