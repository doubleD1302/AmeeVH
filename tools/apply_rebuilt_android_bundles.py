#!/usr/bin/env python3
"""Publish rebuilt Android VN bundles into dist/ and refresh android_patch_manifest.json, the Android zip and SHA256SUMS.

Takes every *.en.unity3d in --staged, backs up what it replaces, copies it to dist/android_AssetBundles, updates
the matching `files` entries (sha256/size) and total_size, rebuilds dist/StellaSora_Android_AssetBundles_VI.zip
(entries Persistent_Store/AssetBundles/<name>, same order as before), updates package_zip and SHA256SUMS.txt.
Does not upload (see docs/RELEASE_ASSET_UPLOAD.md).
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
BUNDLES = DIST / "android_AssetBundles"
ZIP = DIST / "StellaSora_Android_AssetBundles_VI.zip"
MAN = DIST / "android_patch_manifest.json"


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
    a = ap.parse_args()
    staged = sorted(a.staged.glob("*.en.unity3d"))
    a.backup.mkdir(parents=True, exist_ok=True)
    m = json.loads(MAN.read_text(encoding="utf-8"))
    by_path = {f["path"]: f for f in m["files"]}
    delta = 0
    for p in staged:
        cur = BUNDLES / p.name
        if cur.exists():
            shutil.copy2(cur, a.backup / p.name)
        shutil.copy2(p, cur)
        ent = by_path[f"Persistent_Store/AssetBundles/{p.name}"]
        new_size = p.stat().st_size
        delta += new_size - ent["size"]
        ent["sha256"], ent["size"] = sha256(p), new_size
    m["total_size"] = m.get("total_size", 0) + delta
    shutil.copy2(ZIP, a.backup / "StellaSora_Android_AssetBundles_VI.zip.prev")
    with zipfile.ZipFile(a.backup / "StellaSora_Android_AssetBundles_VI.zip.prev") as zin:
        order = zin.namelist()
    tmp = ZIP.with_suffix(".zip.tmp")
    with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        for arc in order:
            zout.write(BUNDLES / Path(arc).name, arcname=arc)
    tmp.replace(ZIP)
    m["package_zip"]["size"], m["package_zip"]["sha256"] = ZIP.stat().st_size, sha256(ZIP)
    # The zip is re-uploaded to the CURRENT release; a URL left on an older tag serves different bytes (E-DL-VERIFY on the phone).
    if m.get("release_tag"):
        m["package_zip"]["url"] = f"https://github.com/doubleD1302/AmeeVH/releases/download/{m['release_tag']}/{m['package_zip'].get('filename', ZIP.name)}"
    MAN.write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    sums = DIST / "SHA256SUMS.txt"
    out = []
    for line in sums.read_text(encoding="utf-8").splitlines():
        for fn in ("android_patch_manifest.json", "StellaSora_Android_AssetBundles_VI.zip"):
            if line.rstrip().endswith(" " + fn) or line.rstrip().endswith("*" + fn):
                line = f"{sha256(DIST / fn)}  {fn}"
        out.append(line)
    sums.write_text("\n".join(out) + "\n", encoding="utf-8")
    print("replaced", len(staged), "bundles; zip", ZIP.stat().st_size, sha256(ZIP))
    return 0


if __name__ == "__main__":
    sys.exit(main())
