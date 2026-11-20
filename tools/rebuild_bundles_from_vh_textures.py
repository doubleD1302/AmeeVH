#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Re-apply the Vietnamese textures of an already shipped VN bundle onto the CURRENT official bundle.

Why: a VN bundle replaces the official bundle of the same name.  Several shipped bundles
(ui_activitystoryreview.en, ui_activity__500001.en, ui_activity__1110701.en, ui_activity_11100.en,
ui_activity_20104.en, ui_activity__510006.en, ui_gachacover_cover_11115.en, ui_gachacover_cover_1001.en)
were saved from a different prefab revision than the official 2.1.0 / 2611141949 one: GameObjects such as
``pivot`` (UnchartedMapStoryPanel/svStory/grid) are missing and parent/child links differ, so the Lua
panel fails to initialise and the game shows the prefab placeholders (white circles, Chinese sample text).

Method: start from the official bundle (structure untouched), find every Texture2D whose decoded pixels differ
between the shipped VN bundle and the official one, and write the VN pixels into the official bundle's
streamed texture data in place (same byte length required).  Writes only to --out.

  .venv\Scripts\python tools\rebuild_bundles_from_vh_textures.py --official <dir> --vh <dir> --out <dir> [--only a.en.unity3d,b.en.unity3d]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import UnityPy
from PIL import ImageChops
from UnityPy.export import Texture2DConverter
from UnityPy.streams import EndianBinaryReader


def textures(env):
    out = {}
    for o in env.objects:
        if o.type.name == "Texture2D":
            t = o.read()
            out.setdefault(t.m_Name, []).append(t)
    return out


def rebuild(official: Path, vh: Path):
    env = UnityPy.load(official.read_bytes())
    venv = UnityPy.load(vh.read_bytes())
    otex, vtex = textures(env), textures(venv)
    patches = {}  # resS name -> list of (start, bytes)
    names = []
    for name, olist in otex.items():
        vlist = vtex.get(name)
        if not vlist or len(vlist) != len(olist):
            continue
        for ot, vt in zip(olist, vlist):
            if (ot.m_Width, ot.m_Height, ot.m_TextureFormat) != (vt.m_Width, vt.m_Height, vt.m_TextureFormat):
                raise SystemExit(f"{official.name}:{name}: format/size differs from VN texture")
            oi, vi = ot.image.convert("RGBA"), vt.image.convert("RGBA")
            if ImageChops.difference(oi, vi).getbbox() is None:
                continue
            enc, _ = Texture2DConverter.image_to_texture2d(vi, ot.m_TextureFormat, ot.object_reader.platform, ot.m_PlatformBlob)
            length = int(ot.m_StreamData.size)
            if len(enc) != length:
                raise SystemExit(f"{official.name}:{name}: encoded length {len(enc)} != {length}")
            res_name = ot.m_StreamData.path.replace("\\", "/").rsplit("/", 1)[-1]
            patches.setdefault(res_name, []).append((int(ot.m_StreamData.offset), enc))
            names.append(name)
    if not patches:
        return None, []
    for key, n in list(env.file.files.items()):
        raw = bytearray(bytes(n.reader.bytes if hasattr(n, "reader") else n.bytes))
        for start, enc in patches.get(key, []):
            raw[start:start + len(enc)] = enc
        r = EndianBinaryReader(bytes(raw))
        r.flags = n.flags
        env.file.files[key] = r
    out = env.file.save(packer="original")
    chk = UnityPy.load(out)
    for o in chk.objects:
        if o.type.name == "Texture2D":
            _ = o.read().image
    return out, names


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--official", required=True, type=Path)
    ap.add_argument("--vh", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    only = [s.strip() for s in a.only.split(",") if s.strip()]
    files = [a.official / n for n in only] if only else sorted(a.official.glob("*.unity3d"))
    for f in files:
        out, names = rebuild(f, a.vh / f.name)
        if out is None:
            print(f"{f.name}: no VN texture differs from official, nothing to write")
            continue
        (a.out / f.name).write_bytes(out)
        print(f"ok {f.name}: {len(names)} VN textures re-applied {names[:4]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
