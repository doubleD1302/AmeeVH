#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build Android Vietnamese AssetBundles (*.en.unity3d)
- Uses ASTC texture format matching Android native GPU requirements.
- Uses ThreadPoolExecutor to patch and verify all bundles concurrently.
- Generates verified bundles in dist/android_AssetBundles/
- Packages dist/StellaSora_Android_AssetBundles_VI.zip
"""

import hashlib
import os
import sys
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from PIL import Image
import UnityPy
from UnityPy.export import Texture2DConverter
from UnityPy.streams import EndianBinaryReader
import astc_encoder

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORK_DIR = PROJECT_ROOT / "work" / "android_pipeline"
SRC_DIR = WORK_DIR / "source_bundles"
OUT_DIR = PROJECT_ROOT / "dist" / "android_AssetBundles"
ZIP_OUTPUT = PROJECT_ROOT / "dist" / "StellaSora_Android_AssetBundles_VI.zip"
TEXTURE_ROOT = PROJECT_ROOT / "dist" / "StellaSora_Texture_VI"

# Fast ASTC encoding
def fast_get_astc_context(ident: int, block_size: tuple, hdr: bool = False):
    cfg = astc_encoder.ASTCConfig(
        astc_encoder.ASTCProfile.LDR,
        *block_size,
        block_z=1,
        quality=60,
        flags=astc_encoder.ASTCConfigFlags.USE_DECODE_UNORM8,
    )
    return astc_encoder.ASTCContext(cfg)

Texture2DConverter._get_astc_context = fast_get_astc_context


def collect_texture_map():
    all_pngs = list(TEXTURE_ROOT.rglob("*.png"))
    print(f"Total Vietnamese PNGs found: {len(all_pngs)}")
    
    # Map bundle_stem -> {asset_name: Path}
    mapping = {}
    for p in all_pngs:
        stem = p.name[:-4]
        if "__" not in stem:
            continue
        # Split on the last double underscore or first double underscore?
        # Standard convention: {bundle_stem}__{asset_name}
        # In case bundle has __ in stem (like ui_activity__101002), we match against known source bundles
        pass
    
    # Accurate matching by checking against available bundle filenames in SRC_DIR
    src_bundles = {b.name: b for b in SRC_DIR.glob("*.en.unity3d")}
    by_bundle = {}
    for p in all_pngs:
        stem = p.name[:-4]
        for b_name in sorted(src_bundles.keys(), key=len, reverse=True):
            b_stem = b_name.replace(".en.unity3d", "")
            prefix = f"{b_stem}__"
            if stem.startswith(prefix):
                asset_name = stem[len(prefix):]
                by_bundle.setdefault(b_name, {})[asset_name] = p
                break
                
    return by_bundle


def patch_single_bundle(b_name, asset_to_path):
    src_path = SRC_DIR / b_name
    out_path = OUT_DIR / b_name
    
    t0 = time.time()
    raw_data = src_path.read_bytes()
    env = UnityPy.load(raw_data)
    
    tex_map = {}
    for obj in env.objects:
        if obj.type.name == "Texture2D":
            t = obj.read()
            tex_map[t.m_Name] = (obj, t)
            
    res_names = [k for k in env.file.files.keys() if k.endswith(".resS")]
    if not res_names:
        return b_name, 0, 0, f"No .resS stream data found in {b_name}"
    res_name = res_names[0]
    res_node = env.file.files[res_name]
    res_bytes = bytearray(bytes(res_node.bytes))
    
    patched = 0
    mismatches = 0
    patched_names = []
    
    # 1. Handle SpriteAtlas textures if present
    atlases = [o for o in env.objects if o.type.name == "SpriteAtlas"]
    if atlases:
        atlas_obj = atlases[0].read()
        spr_map = {s.read().m_RenderDataKey: s.read().m_Name for s in env.objects if s.type.name == "Sprite"}
        atlas_patches = {}
        for key, val in atlas_obj.m_RenderDataMap:
            s_name = spr_map.get(key)
            if s_name in asset_to_path:
                tex_id = val.texture.m_PathID
                atlas_patches.setdefault(tex_id, []).append((s_name, asset_to_path[s_name], val))
                
        tex_by_id = {o.path_id: o.read() for o in env.objects if o.type.name == "Texture2D"}
        for tex_id, items in atlas_patches.items():
            tex = tex_by_id[tex_id]
            if not tex.m_StreamData or tex.m_StreamData.size == 0:
                continue
            im_upright = Texture2DConverter.get_image_from_texture2d(tex, True)
            for spr_name, p, val in items:
                r = val.textureRect
                rw, rh = round(r.width), round(r.height)
                with Image.open(p) as im:
                    im.load()
                    vi_img = im.convert("RGBA")
                if vi_img.size != (rw, rh):
                    vi_img = vi_img.resize((rw, rh), Image.Resampling.LANCZOS)
                x = round(r.x)
                y = tex.m_Height - round(r.y + r.height)
                im_upright.paste(vi_img, (x, y))
                patched += 1
                patched_names.append(spr_name)
                
            encoded, _ = Texture2DConverter.image_to_texture2d(
                im_upright, tex.m_TextureFormat, tex.object_reader.platform, tex.m_PlatformBlob, flip=True
            )
            start = int(tex.m_StreamData.offset)
            length = int(tex.m_StreamData.size)
            if len(encoded) != length:
                mismatches += 1
                print(f"  [WARN] Atlas size mismatch for {tex.m_Name} in {b_name}: {len(encoded)} != {length}")
                continue
            res_bytes[start : start + length] = encoded

    # 2. Handle standalone Texture2D
    for asset_name, p in asset_to_path.items():
        if asset_name not in tex_map:
            continue
        obj, tex = tex_map[asset_name]
        if not tex.m_StreamData or not tex.m_StreamData.path or tex.m_StreamData.size == 0:
            continue
            
        target_size = (tex.m_Width, tex.m_Height)
        start = int(tex.m_StreamData.offset)
        length = int(tex.m_StreamData.size)
        
        with Image.open(p) as im:
            im.load()
            vi_img = im.convert("RGBA")
            
        if vi_img.size != target_size:
            if b_name == "ui_activity_trial.en.unity3d" and asset_name == "zs_activity_trial_logo":
                canvas = Image.new("RGBA", target_size, (0, 0, 0, 0))
                canvas.paste(vi_img, (57, 8), vi_img)
            else:
                canvas = vi_img.resize(target_size, Image.Resampling.LANCZOS)
        else:
            canvas = vi_img
            
        encoded, _ = Texture2DConverter.image_to_texture2d(
            canvas, tex.m_TextureFormat, tex.object_reader.platform, tex.m_PlatformBlob
        )
        
        if len(encoded) != length:
            mismatches += 1
            print(f"  [WARN] Size mismatch for {asset_name} in {b_name}: {len(encoded)} != {length}")
            continue
            
        res_bytes[start : start + length] = encoded
        patched += 1
        patched_names.append(asset_name)
        
    if patched == 0:
        return b_name, 0, mismatches, "No matching textures inside bundle"
        
    # Replace resS reader
    new_reader = EndianBinaryReader(bytes(res_bytes), res_node.endian)
    new_reader.flags = res_node.flags
    env.file.files[res_name] = new_reader
    
    # Save bundle with lz4 compression
    out_path.parent.mkdir(parents=True, exist_ok=True)
    saved_bytes = env.file.save(packer="lz4")
    out_path.write_bytes(saved_bytes)
    
    # Readback verification: reload saved bundle and verify all patched textures decode
    env_verify = UnityPy.load(saved_bytes)
    verify_count = 0
    for obj in env_verify.objects:
        if obj.type.name == "Texture2D":
            t = obj.read()
            if t.m_Name in patched_names or (atlases and t.m_Name.startswith("sactx-")):
                _ = t.image # trigger decode
                verify_count += 1
                
    dt = time.time() - t0
    return b_name, patched, mismatches, f"Patched & verified {patched} textures ({verify_count} decoded) in {dt:.2f}s ({len(saved_bytes):,} bytes)"


def main():
    print("=== BẮT ĐẦU XÂY DỰNG ASSETBUNDLES VIỆT HÓA CHO ANDROID ===")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    
    by_bundle = collect_texture_map()
    print(f"Tổng số bundles có texture Việt hóa: {len(by_bundle)}")
    
    total_textures_to_patch = sum(len(v) for v in by_bundle.values())
    print(f"Tổng số textures ứng viên: {total_textures_to_patch}")
    
    t_start = time.time()
    results = []
    
    # Run with ThreadPoolExecutor
    workers = min(12, os.cpu_count() or 4)
    print(f"Chạy tiến trình với {workers} luồng xử lý...")
    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_map = {
            executor.submit(patch_single_bundle, b_name, items): b_name
            for b_name, items in by_bundle.items()
        }
        for future in as_completed(future_map):
            b_name = future_map[future]
            try:
                res = future.result()
                results.append(res)
                print(f"[{len(results)}/{len(by_bundle)}] {res[0]}: {res[3]}")
            except Exception as e:
                print(f"[ERROR] Bundle {b_name} failed: {e}")
                
    total_patched = sum(r[1] for r in results)
    total_mismatches = sum(r[2] for r in results)
    total_time = time.time() - t_start
    print(f"\n=== HOÀN TẤT BUILD ASSETBUNDLES ANDROID ===")
    print(f"Thời gian: {total_time:.2f}s")
    print(f"Tổng textures đã vá thành công: {total_patched}")
    print(f"Số lỗi kích thước: {total_mismatches}")
    
    # Package ZIP
    print(f"\nĐang đóng gói ZIP: {ZIP_OUTPUT}...")
    with zipfile.ZipFile(ZIP_OUTPUT, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(OUT_DIR.glob("*.unity3d")):
            zf.write(p, arcname=f"Persistent_Store/AssetBundles/{p.name}")
            
    zip_size_mb = ZIP_OUTPUT.stat().st_size / (1024 * 1024)
    print(f"Đã tạo ZIP thành công: {ZIP_OUTPUT} ({zip_size_mb:.2f} MB)")


if __name__ == "__main__":
    main()
