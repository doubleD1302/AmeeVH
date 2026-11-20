#!/usr/bin/env python3
"""Install staging/moderator_20261120/lua_patched_vi.arcx (TramVH moderator edits, 2026-11-20) into dist/ and the local game, with backup.
Does not upload anything. Updates dist/patch_manifest.json and dist/SHA256SUMS.txt."""
import hashlib, json, shutil
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
DIST, GAME = ROOT / "dist", ROOT.parent / "Persistent_Store"
BK = ROOT / "backups" / "pre_moderator_20261120"
NEW = ROOT / "staging" / "moderator_20261120" / "lua_patched_vi.arcx"
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while c := f.read(1 << 20): h.update(c)
    return h.hexdigest()
BK.mkdir(parents=True, exist_ok=True)
for src, name in ((DIST / "lua_patched_vi.arcx", "dist__lua_patched_vi.arcx"), (GAME / "Scripts" / "lua.arcx", "game__lua.arcx"),
                  (DIST / "patch_manifest.json", "patch_manifest.json"), (DIST / "SHA256SUMS.txt", "SHA256SUMS.txt")):
    if not (BK / name).exists(): shutil.copy2(src, BK / name)
shutil.copy2(NEW, DIST / "lua_patched_vi.arcx"); shutil.copy2(NEW, GAME / "Scripts" / "lua.arcx")
d, n = sha(NEW), NEW.stat().st_size
mp = DIST / "patch_manifest.json"; m = json.loads(mp.read_text(encoding="utf-8"))
m["files"]["Persistent_Store/Scripts/lua.arcx"].update(sha256=d, size=n); m["lua_arcx"].update(sha256=d, size_bytes=n)
mp.write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
sp = DIST / "SHA256SUMS.txt"; out = []
for line in sp.read_text(encoding="utf-8").splitlines():
    for fn in ("patch_manifest.json", "lua_patched_vi.arcx"):
        if line.rstrip().endswith("  " + fn): line = f"{sha(DIST / fn)}  {fn}"
    out.append(line)
sp.write_text("\n".join(out) + "\n", encoding="utf-8")
print("lua sha", d, n); print("backup:", BK)
