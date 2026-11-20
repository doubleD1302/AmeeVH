#!/usr/bin/env python3
"""Export all gacha-related videos and images from Stella Sora EN into a single folder.

Strictly read-only on game installation directories. Outputs to:
    StellaSora_VietHoa/dist/StellaSora_Gacha_Assets/
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import shutil
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import UnityPy

GAME_ROOT = Path(r"c:\YostarGames\StellaSora_EN")
PERSISTENT_BUNDLES = GAME_ROOT / "Persistent_Store" / "AssetBundles"
INSTALL_RESOURCE = GAME_ROOT / "StellaSora_Data" / "StreamingAssets" / "InstallResource"
PERSISTENT_VIDEOS = GAME_ROOT / "Persistent_Store" / "Videos"
OUTPUT_DIR = GAME_ROOT / "StellaSora_VietHoa" / "dist" / "StellaSora_Gacha_Assets"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_name(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', "_", name).strip() or "unnamed"


def pil_to_png_bytes(img) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def resolve_bundle_variants(bundle_stem: str) -> Dict[str, Optional[Path]]:
    """Return {'base': Path|None, 'en': Path|None, 'vi': Path|None} for a bundle stem."""
    base_name = f"{bundle_stem}.unity3d"
    en_name = f"{bundle_stem}.en.unity3d"

    base_path = PERSISTENT_BUNDLES / base_name
    if not base_path.exists():
        base_path = INSTALL_RESOURCE / base_name
    if not base_path.exists():
        base_path = None

    # Original EN priority: .en.en.unity3d.orig_en -> .en.unity3d.orig_en -> InstallResource -> Persistent_Store
    en_candidates = [
        PERSISTENT_BUNDLES / f"{bundle_stem}.en.en.unity3d.orig_en",
        PERSISTENT_BUNDLES / f"{bundle_stem}.en.unity3d.orig_en",
        INSTALL_RESOURCE / en_name,
        PERSISTENT_BUNDLES / en_name,
    ]
    en_path = next((p for p in en_candidates if p.exists()), None)

    vi_candidate = PERSISTENT_BUNDLES / en_name
    vi_path = None
    if vi_candidate.exists() and en_path is not None and vi_candidate != en_path:
        if sha256_file(vi_candidate) != sha256_file(en_path):
            vi_path = vi_candidate

    return {"base": base_path, "en": en_path, "vi": vi_path}


def extract_full_bundle_images(
    bundle_path: Path,
    out_dir: Path,
    known_hashes: Optional[Dict[str, str]] = None,
    manifest_rows: Optional[List[Dict]] = None,
    category: str = "",
) -> Dict[str, str]:
    """Extract all Texture2D images (plus sliced sprites for multi-sprite sheets) from a bundle."""
    env = UnityPy.load(str(bundle_path))
    tex_by_pid: Dict[int, Tuple[str, int, int, bytes]] = {}
    sprites_by_tex: Dict[int, List[Tuple[str, object]]] = {}

    for obj in env.objects:
        if obj.type.name == "Texture2D":
            tex = obj.read()
            try:
                img = tex.image
                png_bytes = pil_to_png_bytes(img)
                tex_by_pid[obj.path_id] = (tex.m_Name, img.width, img.height, png_bytes)
            except Exception as exc:
                print(f"  [WARN] Texture2D {getattr(tex, 'm_Name', '?')} in {bundle_path.name}: {exc}")
        elif obj.type.name == "Sprite":
            sp = obj.read()
            tid = sp.m_RD.texture.path_id
            sprites_by_tex.setdefault(tid, []).append((sp.m_Name, sp))

    exported: Dict[str, str] = {}
    used_names: Dict[str, int] = {}

    def save_png(target_dir: Path, name: str, w: int, h: int, png_bytes: bytes, asset_type: str):
        digest = sha256_bytes(png_bytes)
        if known_hashes is not None and known_hashes.get(name) == digest:
            return
        idx = used_names.get(name, 0)
        used_names[name] = idx + 1
        fname = f"{safe_name(name)}.png" if idx == 0 else f"{safe_name(name)}_{idx}.png"
        target_dir.mkdir(parents=True, exist_ok=True)
        dest = target_dir / fname
        dest.write_bytes(png_bytes)
        exported[name] = digest
        if manifest_rows is not None:
            manifest_rows.append(
                {
                    "category": category,
                    "file": str(dest.relative_to(OUTPUT_DIR)).replace("\\", "/"),
                    "source_bundle": bundle_path.name,
                    "asset_name": name,
                    "asset_type": asset_type,
                    "width": w,
                    "height": h,
                    "sha256": digest,
                }
            )

    for pid, (tname, w, h, png_bytes) in sorted(tex_by_pid.items(), key=lambda x: x[1][0]):
        save_png(out_dir, tname, w, h, png_bytes, "Texture2D")
        sps = sprites_by_tex.get(pid, [])
        if len(sps) > 1:
            for sp_name, sp in sorted(sps, key=lambda x: x[0]):
                try:
                    sp_img = sp.image
                    save_png(
                        out_dir / "sprites",
                        sp_name,
                        sp_img.width,
                        sp_img.height,
                        pil_to_png_bytes(sp_img),
                        "Sprite",
                    )
                except Exception as exc:
                    print(f"  [WARN] Sprite {sp_name} in {bundle_path.name}: {exc}")

    return exported


def extract_filtered_sprites(
    bundle_path: Path,
    pattern: re.Pattern,
    exclude_pattern: Optional[re.Pattern],
    out_dir_fn,
    known_hashes: Optional[Dict[str, str]] = None,
    manifest_rows: Optional[List[Dict]] = None,
    category: str = "",
) -> Dict[str, str]:
    """Extract matching Sprite objects (or standalone Texture2D if no Sprite exists) from shared atlas bundles."""
    env = UnityPy.load(str(bundle_path))
    exported: Dict[str, str] = {}
    seen_names: set[str] = set()

    def matches(nm: str) -> bool:
        if not pattern.search(nm):
            return False
        if exclude_pattern and exclude_pattern.search(nm):
            return False
        return True

    # Prefer Sprite objects so atlases are cleanly cropped
    for obj in env.objects:
        if obj.type.name == "Sprite":
            sp = obj.read()
            nm = getattr(sp, "m_Name", "")
            if not matches(nm):
                continue
            try:
                img = sp.image
            except Exception as exc:
                print(f"  [WARN] Sprite {nm} in {bundle_path.name}: {exc}")
                continue
            png_bytes = pil_to_png_bytes(img)
            digest = sha256_bytes(png_bytes)
            seen_names.add(nm)
            if known_hashes is not None and known_hashes.get(nm) == digest:
                continue
            dest_dir = out_dir_fn(nm)
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest = dest_dir / f"{safe_name(nm)}.png"
            dest.write_bytes(png_bytes)
            exported[nm] = digest
            if manifest_rows is not None:
                manifest_rows.append(
                    {
                        "category": category,
                        "file": str(dest.relative_to(OUTPUT_DIR)).replace("\\", "/"),
                        "source_bundle": bundle_path.name,
                        "asset_name": nm,
                        "asset_type": "Sprite",
                        "width": img.width,
                        "height": img.height,
                        "sha256": digest,
                    }
                )

    # Also capture any matching standalone Texture2D not already exported as a Sprite
    for obj in env.objects:
        if obj.type.name == "Texture2D":
            tex = obj.read()
            nm = getattr(tex, "m_Name", "")
            if nm in seen_names or not matches(nm):
                continue
            try:
                img = tex.image
            except Exception as exc:
                print(f"  [WARN] Texture2D {nm} in {bundle_path.name}: {exc}")
                continue
            png_bytes = pil_to_png_bytes(img)
            digest = sha256_bytes(png_bytes)
            if known_hashes is not None and known_hashes.get(nm) == digest:
                continue
            dest_dir = out_dir_fn(nm)
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest = dest_dir / f"{safe_name(nm)}.png"
            dest.write_bytes(png_bytes)
            exported[nm] = digest
            if manifest_rows is not None:
                manifest_rows.append(
                    {
                        "category": category,
                        "file": str(dest.relative_to(OUTPUT_DIR)).replace("\\", "/"),
                        "source_bundle": bundle_path.name,
                        "asset_name": nm,
                        "asset_type": "Texture2D",
                        "width": img.width,
                        "height": img.height,
                        "sha256": digest,
                    }
                )

    return exported


def main() -> None:
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    manifest_rows: List[Dict] = []

    # 1. Videos
    videos_dir = OUTPUT_DIR / "01_Videos"
    videos_dir.mkdir(parents=True, exist_ok=True)
    video_files = sorted(
        [p for p in PERSISTENT_VIDEOS.glob("*.mp4") if "gacha" in p.name.lower()]
    )
    print(f"[1/4] Copying {len(video_files)} gacha videos...")
    for vp in video_files:
        dest = videos_dir / vp.name
        shutil.copy2(vp, dest)
        manifest_rows.append(
            {
                "category": "01_Videos",
                "file": str(dest.relative_to(OUTPUT_DIR)).replace("\\", "/"),
                "source_bundle": str(vp.relative_to(GAME_ROOT)).replace("\\", "/"),
                "asset_name": vp.stem,
                "asset_type": "VideoMP4",
                "width": "",
                "height": "",
                "sha256": sha256_file(dest),
            }
        )

    # 2. Gacha Covers (ui_gachacover_cover_*)
    cover_stems = sorted(
        {
            re.sub(r"(\.en)?\.unity3d(\.orig_en)?$", "", p.name)
            for d in (PERSISTENT_BUNDLES, INSTALL_RESOURCE)
            for p in d.glob("ui_gachacover_cover_*.unity3d")
        }
    )
    print(f"[2/4] Extracting {len(cover_stems)} gacha cover bundles...")
    covers_dir = OUTPUT_DIR / "02_Gacha_Covers"
    for stem in cover_stems:
        short_id = stem.replace("ui_gachacover_", "")
        target = covers_dir / short_id
        variants = resolve_bundle_variants(stem)
        known: Dict[str, str] = {}
        if variants["base"]:
            known.update(
                extract_full_bundle_images(
                    variants["base"], target, None, manifest_rows, "02_Gacha_Covers"
                )
            )
        if variants["en"]:
            en_exported = extract_full_bundle_images(
                variants["en"], target / "EN", known, manifest_rows, "02_Gacha_Covers_EN"
            )
            known.update(en_exported)
        if variants["vi"]:
            extract_full_bundle_images(
                variants["vi"], target / "VI", known, manifest_rows, "02_Gacha_Covers_VI"
            )

    # 3. Gacha UI & FX bundles
    print("[3/4] Extracting Gacha UI & FX bundles...")
    ui_dir = OUTPUT_DIR / "03_Gacha_UI_And_FX"
    for stem in ("ui_gachaex", "ui_gachacover_commonfx"):
        target = ui_dir / stem
        variants = resolve_bundle_variants(stem)
        known = {}
        if variants["base"]:
            known.update(
                extract_full_bundle_images(
                    variants["base"], target, None, manifest_rows, "03_Gacha_UI_And_FX"
                )
            )
        if variants["en"]:
            en_exported = extract_full_bundle_images(
                variants["en"], target / "EN", known, manifest_rows, "03_Gacha_UI_And_FX_EN"
            )
            known.update(en_exported)
        if variants["vi"]:
            extract_full_bundle_images(
                variants["vi"], target / "VI", known, manifest_rows, "03_Gacha_UI_And_FX_VI"
            )

    shared_ui_specs = [
        ("ui_commonex", re.compile(r"gacha|recruit", re.I), None),
        ("ui_big_sprites", re.compile(r"gacha", re.I), None),
        ("ui_equipment", re.compile(r"gacha", re.I), None),
        ("ui_charconsumablepanel", re.compile(r"gacha", re.I), None),
        ("ui_activity__211002", re.compile(r"gacha", re.I), None),
        ("ui_mainviewex", re.compile(r"^MainView_Recruit_", re.I), None),
    ]
    for stem, pat, excl in shared_ui_specs:
        target = ui_dir / stem
        variants = resolve_bundle_variants(stem)
        known = {}
        if variants["base"]:
            known.update(
                extract_filtered_sprites(
                    variants["base"], pat, excl, lambda _nm, t=target: t, None, manifest_rows, "03_Gacha_UI_And_FX"
                )
            )
        if variants["en"]:
            en_exp = extract_filtered_sprites(
                variants["en"], pat, excl, lambda _nm, t=target / "EN": t, known, manifest_rows, "03_Gacha_UI_And_FX_EN"
            )
            known.update(en_exp)
        if variants["vi"]:
            extract_filtered_sprites(
                variants["vi"], pat, excl, lambda _nm, t=target / "VI": t, known, manifest_rows, "03_Gacha_UI_And_FX_VI"
            )

    # 4. Banners, Tabs & Outfit Gacha Cards from icon-0..f
    print("[4/4] Extracting gacha banners, tabs, and outfit cards from icon-0..f...")
    icons_dir = OUTPUT_DIR / "04_Banners_Tabs_And_Outfit_Cards"
    icon_pat = re.compile(r"gacha", re.I)
    icon_excl = re.compile(r"CommonBuff_Summon", re.I)

    def route_icon(nm: str, variant: Optional[str] = None) -> Path:
        low = nm.lower()
        if low.startswith("banner_gacha_"):
            sub = "banners"
        elif low.startswith("tab_gacha_"):
            sub = "tabs"
        elif "outfit_" in low:
            sub = "outfit_gacha"
        else:
            sub = "other"
        return icons_dir / sub / variant if variant else icons_dir / sub

    for hex_c in "0123456789abcdef":
        stem = f"icon-{hex_c}"
        variants = resolve_bundle_variants(stem)
        known = {}
        if variants["base"]:
            known.update(
                extract_filtered_sprites(
                    variants["base"],
                    icon_pat,
                    icon_excl,
                    lambda nm: route_icon(nm),
                    None,
                    manifest_rows,
                    "04_Banners_Tabs_And_Outfit_Cards",
                )
            )
        if variants["en"]:
            en_exp = extract_filtered_sprites(
                variants["en"],
                icon_pat,
                icon_excl,
                lambda nm: route_icon(nm, "EN"),
                known,
                manifest_rows,
                "04_Banners_Tabs_And_Outfit_Cards_EN",
            )
            known.update(en_exp)
        if variants["vi"]:
            extract_filtered_sprites(
                variants["vi"],
                icon_pat,
                icon_excl,
                lambda nm: route_icon(nm, "VI"),
                known,
                manifest_rows,
                "04_Banners_Tabs_And_Outfit_Cards_VI",
            )

    # Write MANIFEST.json and INDEX.csv
    summary = {
        "output_dir": str(OUTPUT_DIR),
        "total_files": len(manifest_rows),
        "videos_count": sum(1 for r in manifest_rows if r["asset_type"] == "VideoMP4"),
        "images_count": sum(1 for r in manifest_rows if r["asset_type"] != "VideoMP4"),
        "by_category": {},
    }
    for r in manifest_rows:
        summary["by_category"][r["category"]] = summary["by_category"].get(r["category"], 0) + 1

    (OUTPUT_DIR / "MANIFEST.json").write_text(
        json.dumps({"summary": summary, "files": manifest_rows}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    with (OUTPUT_DIR / "INDEX.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["category", "file", "source_bundle", "asset_name", "asset_type", "width", "height", "sha256"],
        )
        writer.writeheader()
        writer.writerows(manifest_rows)

    print("DONE:", json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
