#!/usr/bin/env python3
"""Audit all available Vietnamese textures against original AssetBundles.

Maps each PNG to bundle, Texture2D/CAB/path_id, checks dimensions, format,
mips, alpha, stream data, sprite consumers, and classifies patchability.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from PIL import Image
import UnityPy

PROJECT_ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
GAME_ROOT = Path(r"c:\YostarGames\StellaSora_EN")
ORIG_BUNDLES_DIR = GAME_ROOT / "Persistent_Store" / "AssetBundles"

DIST_EN = PROJECT_ROOT / "dist" / "StellaSora_Texture_AnhVeChu_EN"
DIST_VI = PROJECT_ROOT / "dist" / "StellaSora_Texture_VI"

# Collect all potential PNG VI source directories
SOURCES = {
    "cat1_comics": DIST_VI / "01_TruyenTranh_LoadingComics_VI",
    "cat2_titles": DIST_VI / "02_DanhHieu_HonorTitles_VI",
    "cat3_logos": DIST_VI / "03_TieuDe_Logos_Headers_VI",
    "cat4_buttons_en_sub": DIST_EN / "04_NutBam_HuyHieu_Results_VI",
    "cat4_buttons_vi": DIST_VI / "04_NutBam_HuyHieu_Results_VI",
    "cat5_banners_en_sub": DIST_EN / "05_SuKien_Banners_Tabs_VI",
    "cat5_banners_vi": DIST_VI / "05_SuKien_Banners_Tabs_VI",
    "cat6_skin_art": DIST_VI / "06_TrangPhuc_SkinArtText_VI",
}

def get_bundle_bytes(b_name: str) -> bytes:
    """Reads pristine unpatched bundle bytes."""
    # Check .orig_en first, else .en.unity3d
    orig_file = ORIG_BUNDLES_DIR / (b_name.replace(".unity3d", ".en.unity3d.orig_en"))
    if not orig_file.exists():
        orig_file = ORIG_BUNDLES_DIR / (b_name + ".orig_en")
    if orig_file.exists():
        return orig_file.read_bytes()
    cur_file = ORIG_BUNDLES_DIR / b_name
    if cur_file.exists():
        return cur_file.read_bytes()
    raise FileNotFoundError(f"Bundle {b_name} not found")

def main():
    print("=== BẮT ĐẦU KIỂM KÊ TOÀN DIỆN TEXTURE VIỆT HÓA ===")

    # 1. Index all available PNG VI files
    all_pngs = {}  # fname -> {cat, path, sha256, width, height, has_alpha}
    for cat_name, cat_dir in SOURCES.items():
        if not cat_dir.exists():
            continue
        for p in cat_dir.glob("*.png"):
            # Prefer larger/newer or distinct
            if p.name not in all_pngs or "en_sub" in cat_name:
                with open(p, "rb") as f:
                    data = f.read()
                sha = hashlib.sha256(data).hexdigest()
                with Image.open(p) as img:
                    w, h = img.size
                    mode = img.mode
                all_pngs[p.name] = {
                    "filename": p.name,
                    "cat": cat_name,
                    "path": str(p),
                    "sha256": sha,
                    "width": w,
                    "height": h,
                    "mode": mode,
                }

    print(f"Tổng số tệp PNG VI độc nhất thu thập được: {len(all_pngs)}")

    # 2. Map PNGs to bundle names
    # Naming convention: {bundle_stem}__{asset_name}.png
    bundle_to_pngs = {}
    unmapped_pngs = []

    all_bundle_names = set(p.name for p in ORIG_BUNDLES_DIR.glob("*.en.unity3d"))

    for fname, info in all_pngs.items():
        stem = fname[:-4]  # strip .png
        matched_b = None
        for b_name in sorted(all_bundle_names, key=len, reverse=True):
            b_stem = b_name.replace(".en.unity3d", "")
            prefix = f"{b_stem}__"
            if stem.startswith(prefix):
                matched_b = b_name
                asset_name = stem[len(prefix):]
                break

        if matched_b:
            info["bundle_name"] = matched_b
            info["asset_name"] = asset_name
            bundle_to_pngs.setdefault(matched_b, []).append(info)
        else:
            unmapped_pngs.append(fname)

    print(f"Số PNG ánh xạ được vào bundle: {len(all_pngs) - len(unmapped_pngs)}")
    print(f"Số PNG không ánh xạ được: {len(unmapped_pngs)}")
    if unmapped_pngs:
        print("   Mẫu không ánh xạ được:", unmapped_pngs[:5])

    print(f"Số bundle liên quan: {len(bundle_to_pngs)}")

    # 3. Analyze each bundle with UnityPy
    bundle_analysis = {}
    safe_patchable_count = 0
    pending_atlas_count = 0
    pending_other_count = 0

    for b_idx, (b_name, png_list) in enumerate(sorted(bundle_to_pngs.items()), 1):
        try:
            raw_b = get_bundle_bytes(b_name)
        except Exception as e:
            print(f"[{b_idx}] Error loading bundle {b_name}: {e}")
            continue

        env = UnityPy.load(raw_b)

        # Collect Texture2D and Sprite metadata
        tex_objects = {}  # m_Name -> {obj, tex}
        sprite_objects = {}  # m_Name -> {obj, sprite}

        for obj in env.objects:
            if obj.type.name == "Texture2D":
                tex = obj.read()
                tex_objects[tex.m_Name] = (obj, tex)
            elif obj.type.name == "Sprite":
                spr = obj.read()
                sprite_objects[spr.m_Name] = (obj, spr)

        b_results = []
        for p_info in png_list:
            aname = p_info["asset_name"]
            status = "unknown"
            reason = ""
            meta = {}

            if aname in tex_objects:
                obj, tex = tex_objects[aname]
                meta["type"] = "Texture2D"
                meta["path_id"] = obj.path_id
                meta["cab"] = getattr(obj.assets_file, "name", "unknown")
                meta["format"] = str(tex.m_TextureFormat)
                meta["width"] = tex.m_Width
                meta["height"] = tex.m_Height
                meta["mips"] = tex.m_MipCount
                meta["has_stream"] = bool(tex.m_StreamData and tex.m_StreamData.path)
                if meta["has_stream"]:
                    meta["stream_path"] = tex.m_StreamData.path
                    meta["stream_offset"] = int(tex.m_StreamData.offset)
                    meta["stream_size"] = int(tex.m_StreamData.size)

                # Find sprite consumers
                consumers = [s_name for s_name, (_, s) in sprite_objects.items()
                             if hasattr(s, "m_RD") and hasattr(s.m_RD, "texture") and s.m_RD.texture.path_id == obj.path_id]
                meta["sprite_consumers"] = consumers

                # Check dimensions match
                dim_match = (p_info["width"] == tex.m_Width and p_info["height"] == tex.m_Height)
                meta["dim_match"] = dim_match

                # Check if stream exists in bundle files
                res_fname = tex.m_StreamData.path.replace("\\", "/").rsplit("/", 1)[-1] if meta["has_stream"] else None
                res_exists = res_fname in env.file.files if res_fname else False
                meta["res_exists"] = res_exists

                if not meta["has_stream"] or not res_exists:
                    status = "pending_no_external_stream"
                    reason = f"Texture has no external .resS node ({res_fname})"
                    pending_other_count += 1
                elif not dim_match:
                    status = "pending_dimension_mismatch"
                    reason = f"PNG size ({p_info['width']}x{p_info['height']}) != texture ({tex.m_Width}x{tex.m_Height})"
                    pending_other_count += 1
                else:
                    status = "safe_standalone_texture"
                    reason = "Standalone Texture2D with exact size and valid .resS slice"
                    safe_patchable_count += 1

            elif aname in sprite_objects:
                obj, spr = sprite_objects[aname]
                meta["type"] = "Sprite"
                meta["path_id"] = obj.path_id
                meta["cab"] = getattr(obj.assets_file, "name", "unknown")
                # Find parent texture
                tex_pid = spr.m_RD.texture.path_id if hasattr(spr, "m_RD") and hasattr(spr.m_RD, "texture") else None
                parent_tex_name = None
                for t_name, (t_obj, t) in tex_objects.items():
                    if t_obj.path_id == tex_pid:
                        parent_tex_name = t_name
                        break
                meta["parent_texture"] = parent_tex_name
                meta["sprite_rect"] = [spr.m_Rect.x, spr.m_Rect.y, spr.m_Rect.width, spr.m_Rect.height]
                status = "pending_atlas_sprite"
                reason = f"Sprite is part of Atlas Texture2D '{parent_tex_name}' (BC7 atlas region patch blocked by policy)"
                pending_atlas_count += 1
            else:
                status = "pending_asset_not_found"
                reason = "Asset name not found in Texture2D or Sprite table of bundle"
                pending_other_count += 1

            p_info["status"] = status
            p_info["reason"] = reason
            p_info["metadata"] = meta
            b_results.append(p_info)

        bundle_analysis[b_name] = {
            "bundle_name": b_name,
            "bundle_size": len(raw_b),
            "bundle_sha256": hashlib.sha256(raw_b).hexdigest(),
            "png_count": len(png_list),
            "safe_count": sum(1 for r in b_results if r["status"] == "safe_standalone_texture"),
            "pending_atlas_count": sum(1 for r in b_results if r["status"] == "pending_atlas_sprite"),
            "pending_other_count": sum(1 for r in b_results if r["status"] not in ["safe_standalone_texture", "pending_atlas_sprite"]),
            "items": b_results
        }

    print("\n=== KẾT QUẢ PHÂN LOẠI TOÀN BỘ TEXTURE ===")
    print(f"Tổng số texture PNG được khảo sát: {len(all_pngs)}")
    print(f"1. Safe Standalone Texture2D (Có thể vá an toàn): {safe_patchable_count}")
    print(f"2. Pending Atlas Sprite (Bị chặn do Sprite thuộc Atlas BC7): {pending_atlas_count}")
    print(f"3. Pending Other (Không tìm thấy / Kích thước lệch / Không có resS): {pending_other_count}")

    # Summary by bundle
    safe_bundles = [b for b, data in bundle_analysis.items() if data["safe_count"] > 0]
    pure_atlas_bundles = [b for b, data in bundle_analysis.items() if data["safe_count"] == 0 and data["pending_atlas_count"] > 0]
    print(f"\nTổng số bundles có chứa Texture an toàn để vá: {len(safe_bundles)} bundles")
    print(f"Tổng số bundles thuần Atlas Sprite (phải pending): {len(pure_atlas_bundles)} bundles")

    out_file = PROJECT_ROOT / "work" / "textures" / "texture_mapping_audit.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps({
        "total_pngs": len(all_pngs),
        "safe_patchable_count": safe_patchable_count,
        "pending_atlas_count": pending_atlas_count,
        "pending_other_count": pending_other_count,
        "safe_bundles_count": len(safe_bundles),
        "pure_atlas_bundles_count": len(pure_atlas_bundles),
        "bundles": bundle_analysis
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nĐã lưu kết quả kiểm kê chi tiết vào: {out_file.name}")

if __name__ == "__main__":
    main()
