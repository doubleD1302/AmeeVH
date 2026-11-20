#!/usr/bin/env python3
"""Install the 2026-11-20 PC fix into dist/ and the local game (with backups). Does not upload anything.

  * 8 bundles rebuilt on the official 2611141949 prefabs (staging/bundles_rebuilt_2611141949_r2)
  * data_patched_vi.arcx with Story.<id>.4 codes restored (staging/data_fix_r2)
Updates dist/patch_manifest.json, dist/StellaSora_AssetBundles_VI.zip and dist/SHA256SUMS.txt.
"""
import hashlib, json, shutil, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
GAME = ROOT.parent / "Persistent_Store"
BK = ROOT / "backups" / "pre_fix_20261120"
BUNDLES = ROOT / "staging" / "bundles_rebuilt_2611141949_r2"
DATA = ROOT / "staging" / "data_fix_r2" / "data_patched_vi.arcx"


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while c := f.read(1 << 20):
            h.update(c)
    return h.hexdigest()


BK.mkdir(parents=True, exist_ok=True)
m_path = DIST / "patch_manifest.json"
m = json.loads(m_path.read_text(encoding="utf-8"))
shutil.copy2(m_path, BK / "patch_manifest.json")
shutil.copy2(DIST / "StellaSora_AssetBundles_VI.zip", BK / "StellaSora_AssetBundles_VI.zip")
shutil.copy2(DIST / "SHA256SUMS.txt", BK / "SHA256SUMS.txt")
shutil.copy2(DIST / "data_patched_vi.arcx", BK / "dist__data_patched_vi.arcx")
shutil.copy2(GAME / "Tables" / "data.arcx", BK / "game__data.arcx")

staged = sorted(BUNDLES.glob("*.en.unity3d"))
for p in staged:
    cur = GAME / "AssetBundles" / p.name
    shutil.copy2(cur, BK / f"game__{p.name}")
    shutil.copy2(p, cur)
    ent = m["files"][f"Persistent_Store/AssetBundles/{p.name}"]
    ent["sha256"], ent["size"] = sha(p), p.stat().st_size
    b = m["bundles"][p.name]
    b["patched_sha256"], b["size_bytes"] = ent["sha256"], ent["size"]

shutil.copy2(DATA, DIST / "data_patched_vi.arcx")
shutil.copy2(DATA, GAME / "Tables" / "data.arcx")
for key in ("Persistent_Store/Tables/data.arcx",):
    m["files"][key]["sha256"], m["files"][key]["size"] = sha(DATA), DATA.stat().st_size
m["data_arcx"]["sha256"], m["data_arcx"]["size_bytes"] = sha(DATA), DATA.stat().st_size

zp = DIST / "StellaSora_AssetBundles_VI.zip"
repl = {f"AssetBundles/{p.name}": p for p in staged}
tmp = zp.with_suffix(".zip.tmp")
with zipfile.ZipFile(BK / "StellaSora_AssetBundles_VI.zip") as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
    for n in zin.namelist():
        zout.writestr(n, repl[n].read_bytes() if n in repl else zin.read(n))
tmp.replace(zp)
m["package_zip"]["size"], m["package_zip"]["sha256"] = zp.stat().st_size, sha(zp)
m_path.write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

sums = DIST / "SHA256SUMS.txt"
out = []
for line in sums.read_text(encoding="utf-8").splitlines():
    for fn in ("patch_manifest.json", "StellaSora_AssetBundles_VI.zip", "data_patched_vi.arcx"):
        if line.rstrip().endswith("  " + fn):
            line = f"{sha(DIST / fn)}  {fn}"
    out.append(line)
sums.write_text("\n".join(out) + "\n", encoding="utf-8")
print("bundles:", [p.name for p in staged]); print("data sha", sha(DATA)); print("zip", zp.stat().st_size, sha(zp)); print("backup:", BK)
