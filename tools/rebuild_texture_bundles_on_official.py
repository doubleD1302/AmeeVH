#!/usr/bin/env python3
"""Re-apply the Vietnamese textures on top of the CURRENT official *.en.unity3d bundles.

Why: a VN bundle replaces the official bundle of the same name. If it was built from an older official
bundle, every asset the newer official bundle added is missing from it, and the game shows a white
(empty) banner/tab/title for those assets. Always rebuild the VN bundles from the official file of the
resource version that is being shipped, never the other way round.

This writes ONLY to --out (default staging/bundles_rebuilt_<tag>). It does not touch dist/, the manifest
or the game folder. Use the project .venv (UnityPy + Pillow).

  .venv\\Scripts\\python tools\\rebuild_texture_bundles_on_official.py --source <dir of official *.en.unity3d>
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import UnityPy
from PIL import Image
from UnityPy.export import Texture2DConverter
from UnityPy.streams import EndianBinaryReader

ROOT = Path(__file__).resolve().parents[1]
TEXTURE_SOURCES = [
    ROOT / "dist" / "StellaSora_Texture_VI" / "01_TruyenTranh_LoadingComics_VI",
    ROOT / "dist" / "StellaSora_Texture_VI" / "03_TieuDe_Logos_Headers_VI",
    ROOT / "dist" / "StellaSora_Texture_AnhVeChu_EN" / "04_NutBam_HuyHieu_Results_VI",
    ROOT / "dist" / "StellaSora_Texture_AnhVeChu_EN" / "05_SuKien_Banners_Tabs_VI",
    ROOT / "dist" / "StellaSora_Texture_VI" / "06_TrangPhuc_SkinArtText_VI",
]


def collect_targets():
    targets = {}
    for d in TEXTURE_SOURCES:
        if d.exists():
            for p in d.glob("*.png"):
                targets[p.name] = p
        else:
            print("warning: missing source dir", d)
    by_bundle = {}
    for fname, p in sorted(targets.items()):
        parts = fname.split("__", 1)
        if len(parts) != 2:
            continue
        by_bundle.setdefault(f"{parts[0]}.en.unity3d", []).append((parts[1][:-4], p))
    return by_bundle


def rebuild_one(src: Path, items):
    env = UnityPy.load(src.read_bytes())
    tex_map = {}
    for obj in env.objects:
        if obj.type.name == "Texture2D":
            t = obj.read()
            tex_map[t.m_Name] = t
    matched = [(n, p) for n, p in items if n in tex_map]
    if not matched:
        return None, 0, [], []
    sample = tex_map[matched[0][0]]
    res_name = sample.m_StreamData.path.replace("\\", "/").rsplit("/", 1)[-1]
    node = env.file.files[res_name]
    res = bytearray(bytes(node.reader.bytes if hasattr(node, "reader") else node.bytes))
    done, skipped = 0, []
    for name, p in matched:
        t = tex_map[name]
        size = (t.m_Width, t.m_Height)
        start, length = int(t.m_StreamData.offset), int(t.m_StreamData.size)
        with Image.open(p) as im:
            im.load()
            vi = im.convert("RGBA")
        if vi.size == size:
            canvas = vi
        else:
            canvas = Image.new("RGBA", size, (0, 0, 0, 0))
            canvas.paste(vi, ((size[0] - vi.width) // 2, (size[1] - vi.height) // 2), vi)
        enc, _ = Texture2DConverter.image_to_texture2d(canvas, t.m_TextureFormat, t.object_reader.platform, t.m_PlatformBlob)
        if len(enc) != length:
            skipped.append(name)
            continue
        res[start:start + length] = enc
        done += 1
    for key, n in list(env.file.files.items()):
        raw = bytes(res) if key == res_name else bytes(n.reader.bytes if hasattr(n, "reader") else n.bytes)
        r = EndianBinaryReader(raw)
        r.flags = n.flags
        env.file.files[key] = r
    out = env.file.save(packer="original")
    # readback: every texture decodes, container identical to the official bundle
    chk = UnityPy.load(out)
    for o in chk.objects:
        if o.type.name == "Texture2D":
            _ = o.read().image
    same_keys = set(chk.container.keys()) == set(UnityPy.load(src.read_bytes()).container.keys())
    return out, done, skipped, [] if same_keys else ["container differs from official"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True, type=Path, help="dir with the official *.en.unity3d of the shipped resource version")
    ap.add_argument("--out", type=Path, default=ROOT / "staging" / "bundles_rebuilt_on_official")
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    by_bundle = collect_targets()
    total = bad = 0
    for name, items in sorted(by_bundle.items()):
        src = a.source / name
        if not src.exists():
            continue
        out, done, skipped, problems = rebuild_one(src, items)
        if out is None:
            continue
        if problems:
            bad += 1
            print("PROBLEM", name, problems)
            continue
        (a.out / name).write_bytes(out)
        total += done
        print(f"ok {name}: {done} textures{' skipped ' + str(skipped) if skipped else ''}")
    print("textures patched:", total, "| bundles with problems:", bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
