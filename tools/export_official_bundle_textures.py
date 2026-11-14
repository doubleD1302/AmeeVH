#!/usr/bin/env python3
"""Export every Texture2D of given official *.en.unity3d bundles to PNG + a status CSV.

Files are named <bundle stem>__<texture name>.png (same naming the texture patch pipeline uses).
CSV columns: file, bundle, texture, size, format, lang_text (name ends with _lang => language-specific text),
has_vi (a Vietnamese PNG with this name exists in the dist texture sources),
in_old_vn_bundle (texture already existed in the VN bundle built from the older base => NEW in this resource version if false).

  .venv\\Scripts\\python tools\\export_official_bundle_textures.py --source <dir> --out work\\<name> bundle1.en.unity3d ...
"""
import argparse
import csv
import sys
from pathlib import Path

import UnityPy

ROOT = Path(__file__).resolve().parents[1]
VI_SOURCES = [
    ROOT / "dist" / "StellaSora_Texture_VI" / "01_TruyenTranh_LoadingComics_VI",
    ROOT / "dist" / "StellaSora_Texture_VI" / "03_TieuDe_Logos_Headers_VI",
    ROOT / "dist" / "StellaSora_Texture_AnhVeChu_EN" / "04_NutBam_HuyHieu_Results_VI",
    ROOT / "dist" / "StellaSora_Texture_AnhVeChu_EN" / "05_SuKien_Banners_Tabs_VI",
    ROOT / "dist" / "StellaSora_Texture_VI" / "06_TrangPhuc_SkinArtText_VI",
]


def texture_names(path: Path):
    env = UnityPy.load(path.read_bytes())
    return {o.read().m_Name for o in env.objects if o.type.name == "Texture2D"}, env


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--old-vn", type=Path, default=ROOT / "dist" / "AssetBundles")
    ap.add_argument("bundles", nargs="+")
    a = ap.parse_args()
    vi_files = {p.name for d in VI_SOURCES if d.exists() for p in d.glob("*.png")}
    a.out.mkdir(parents=True, exist_ok=True)
    rows = []
    for b in a.bundles:
        stem = b[:-len(".en.unity3d")] if b.endswith(".en.unity3d") else b.rsplit(".", 1)[0]
        _, env = texture_names(a.source / b)
        old = a.old_vn / b
        old_names = texture_names(old)[0] if old.exists() else set()
        # container key per texture (via sprites/paths) is not needed: name is unique inside a bundle
        for o in env.objects:
            if o.type.name != "Texture2D":
                continue
            t = o.read()
            fname = f"{stem}__{t.m_Name}.png"
            t.image.save(a.out / fname)
            rows.append({
                "file": fname, "bundle": b, "texture": t.m_Name,
                "size": f"{t.m_Width}x{t.m_Height}", "format": t.m_TextureFormat,
                "lang_text": "yes" if t.m_Name.endswith("_lang") else "no",
                "has_vi": "yes" if fname in vi_files else "no",
                "in_old_vn_bundle": "yes" if t.m_Name in old_names else "no",
            })
    with open(a.out / "_status.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print("exported", len(rows), "textures to", a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
