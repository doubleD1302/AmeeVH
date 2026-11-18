#!/usr/bin/env python3
"""Publish rebuilt VN texture bundles into dist/ (and optionally the local game) and refresh the manifest.

Takes every *.en.unity3d in --staged, backs up the files it replaces, then:
  - copies them to dist/AssetBundles (+ --game-dir if given)
  - updates dist/patch_manifest.json: files[...] sha/size, bundles[...] patched_sha256/size_bytes, package_zip sha/size
  - rebuilds dist/StellaSora_AssetBundles_VI.zip (entries AssetBundles/<name>, same order as before)
  - refreshes the patch_manifest.json and zip lines in dist/SHA256SUMS.txt
It does not upload anything. Upload with tools/upload_release_assets.ps1 (see docs/RELEASE_ASSET_UPLOAD.md).
"""
import argparse
import hashlib
import json
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while c := f.read(1 << 20):
            h.update(c)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--staged", required=True, type=Path)
    ap.add_argument("--backup", required=True, type=Path)
    ap.add_argument("--game-dir", type=Path, help="Persistent_Store/AssetBundles of the installed game")
    a = ap.parse_args()
    staged = sorted(a.staged.glob("*.en.unity3d"))
    names = [p.name for p in staged]
    a.backup.mkdir(parents=True, exist_ok=True)
    for p in staged:
        for d, tag in ((DIST / "AssetBundles", "dist"), (a.game_dir, "game")):
            if d is None:
                continue
            cur = d / p.name
            if cur.exists():
                shutil.copy2(cur, a.backup / f"{tag}__{p.name}")
            shutil.copy2(p, cur)
    man_path = DIST / "patch_manifest.json"
    m = json.loads(man_path.read_text(encoding="utf-8"))
    for p in staged:
        s, sz = sha256(p), p.stat().st_size
        ent = m["files"][f"Persistent_Store/AssetBundles/{p.name}"]
        ent["sha256"], ent["size"] = s, sz
        b = m.setdefault("bundles", {}).setdefault(p.name, {})
        b["patched_sha256"], b["size_bytes"] = s, sz
    zip_path = DIST / "StellaSora_AssetBundles_VI.zip"
    shutil.copy2(zip_path, a.backup / "StellaSora_AssetBundles_VI.zip.prev")
    with zipfile.ZipFile(a.backup / "StellaSora_AssetBundles_VI.zip.prev") as zin:
        order = zin.namelist()
    tmp = zip_path.with_suffix(".zip.tmp")
    with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        for arc in order:
            zout.write(DIST / arc, arcname=arc)  # arc = AssetBundles/<name>, read fresh from dist
    tmp.replace(zip_path)
    m["package_zip"]["size"], m["package_zip"]["sha256"] = zip_path.stat().st_size, sha256(zip_path)
    # The zip is re-uploaded to the CURRENT release; a URL left on an older tag serves different bytes.
    if m.get("release_tag"):
        m["package_zip"]["url"] = f"https://github.com/doubleD1302/AmeeVH/releases/download/{m['release_tag']}/{m['package_zip'].get('filename', zip_path.name)}"
    man_path.write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    sums = DIST / "SHA256SUMS.txt"
    out = []
    for line in sums.read_text(encoding="utf-8").splitlines():
        for fn in ("patch_manifest.json", "StellaSora_AssetBundles_VI.zip"):
            if line.rstrip().endswith(" " + fn) or line.rstrip().endswith("*" + fn):
                line = f"{sha256(DIST / fn)}  {fn}"
        out.append(line)
    sums.write_text("\n".join(out) + "\n", encoding="utf-8")
    print("replaced", len(names), "bundles:", ", ".join(names))
    print("zip", zip_path.stat().st_size, sha256(zip_path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
