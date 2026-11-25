#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Download TramVH moderator translations for STev_04_01..10 (Antithesis) and STev_10_01 (Crim),
patch dist/lua_patched_vi.arcx, update manifests & checksums, and deploy directly to Yostar and Steam."""

from __future__ import annotations

import collections
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from test_lua_roundtrip import Lua53Chunk, serialize_proto  # noqa: E402
from tools.arcx_adapter import (  # noqa: E402
    XXTEA_KEY,
    ArcxArchive,
    repack_archive,
    xxtea_decrypt,
    xxtea_encrypt,
)

OFFICIAL_LUA = Path(
    r"C:/YostarGames/StellaResourceDownloads/EN/2.1.0_2611141949_text_a9a03c7c2b63/files/Scripts/lua.arcx"
)
DIST_DIR = ROOT / "dist"
DIST_LUA = DIST_DIR / "lua_patched_vi.arcx"
YOSTAR_LUA = Path(r"C:/YostarGames/StellaSora_EN/Persistent_Store/Scripts/lua.arcx")
STEAM_LUA = Path(r"C:/Program Files (x86)/Steam/steamapps/common/Stella Sora/Persistent_Store/Scripts/lua.arcx")

RUN_DIR = ROOT / "work/runs/tramvh_stev_mod_20261125"
SNAPSHOT_JSON = RUN_DIR / "tramvh_stev_mod_lines.json"
STAGING_DIR = ROOT / "staging/tramvh_stev_mod_20261125"
STAGING_LUA = STAGING_DIR / "lua_patched_vi.arcx"
BACKUP_DIR = ROOT / "backups/pre_tramvh_stev_20261125"
AVG_MAP_PATH = ROOT / "work/research/avg_file_to_entry.json"

D1_SQL = (
    "SELECT line_id, en, new_vi, translator, approved_by, updated_at "
    "FROM lines "
    "WHERE chapter_id='Cot_Truyen_Su_Kien_STev' "
    "AND (line_id LIKE 'STev_04_%' OR line_id LIKE 'STev_10_01::%') "
    "AND approved_by LIKE '%(Moderator)%' "
    "ORDER BY line_id;"
)

TOK_RE = re.compile(r"==[A-Za-z0-9_]+==|<[^>]+>|\{[^}]+\}")
STR_KINDS = (4, 20)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(1 << 20):
            h.update(chunk)
    return h.hexdigest()


def fetch_d1_snapshot() -> list[dict]:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    res = subprocess.run(
        [
            "cmd",
            "/c",
            "npx",
            "wrangler",
            "d1",
            "execute",
            "tramvh-collaboration",
            "--remote",
            "--json",
            "--command",
            D1_SQL,
        ],
        cwd=str(ROOT / "web/story_translator"),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    payload = json.loads(res.stdout)
    SNAPSHOT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    rows = payload[0]["results"]

    by_mod = collections.Counter(r["approved_by"] for r in rows)
    if len(rows) != 189 or by_mod.get("Antithesis (Moderator)") != 173 or by_mod.get("Crim (Moderator)") != 16:
        raise RuntimeError(
            f"Unexpected D1 row count/breakdown: total={len(rows)}, by_mod={dict(by_mod)}"
        )
    print(f"Fetched {len(rows)} D1 rows ({dict(by_mod)}) -> {SNAPSHOT_JSON}")
    return rows


def validate_rows(rows: list[dict]) -> list[dict]:
    normalized = []
    for r in rows:
        en = r["en"]
        vi_raw = (r["new_vi"] or "").strip()
        if not vi_raw:
            raise RuntimeError(f"Empty new_vi for {r['line_id']}")
        vi_nfc = unicodedata.normalize("NFC", vi_raw)
        en_toks = collections.Counter(TOK_RE.findall(en))
        vi_toks = collections.Counter(TOK_RE.findall(vi_nfc))
        if en_toks != vi_toks:
            raise RuntimeError(
                f"Token mismatch at {r['line_id']}: EN={dict(en_toks)} VI={dict(vi_toks)}"
            )
        normalized.append({**r, "new_vi_nfc": vi_nfc})
    print(f"Pre-flight validation passed for all {len(normalized)} rows (NFC + token parity 0 errors).")
    return normalized


def backup_before_modify() -> None:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    targets = [
        (DIST_LUA, "dist__lua_patched_vi.arcx"),
        (DIST_DIR / "patch_manifest.json", "patch_manifest.json"),
        (DIST_DIR / "android_patch_manifest.json", "android_patch_manifest.json"),
        (DIST_DIR / "SHA256SUMS.txt", "SHA256SUMS.txt"),
        (YOSTAR_LUA, "yostar__lua.arcx"),
        (STEAM_LUA, "steam__lua.arcx"),
    ]
    for src, name in targets:
        dst = BACKUP_DIR / name
        if not src.exists():
            raise FileNotFoundError(f"Missing required source for backup: {src}")
        if not dst.exists():
            shutil.copy2(src, dst)
            print(f"Backed up {src} -> {dst} (sha256={sha256_file(dst)})")
        else:
            print(f"Backup already exists, preserved: {dst}")


def load_arc(path: Path):
    arc = ArcxArchive(path)
    raw = path.read_bytes()
    return arc, {e["hash"]: (e, arc.extract_entry(e, raw)) for e in arc.entries}


def parse_lua(enc: bytes):
    chunk = Lua53Chunk(xxtea_decrypt(enc, XXTEA_KEY))
    hdr = chunk.read_bytes(33)
    up = chunk.read_byte()
    proto = chunk.parse_proto()
    return hdr, up, proto


def const_str(c) -> str | None:
    kind, val = c
    if kind in STR_KINDS:
        return val[1].decode("utf-8", "replace")
    return None


def patch_lua_archive(rows: list[dict]) -> dict[int, list[tuple[int, str, str]]]:
    avg_map = json.loads(AVG_MAP_PATH.read_text(encoding="utf-8"))
    by_scene: dict[str, list[dict]] = collections.defaultdict(list)
    for r in rows:
        by_scene[r["line_id"].split("::")[0]].append(r)

    if len(by_scene) != 11:
        raise RuntimeError(f"Expected 11 scenes, got {len(by_scene)}: {sorted(by_scene)}")

    scene_by_hash: dict[int, tuple[str, list[dict]]] = {}
    for sc, srows in sorted(by_scene.items()):
        fname = f"{sc}.lua"
        info = avg_map.get(fname)
        if not info:
            raise RuntimeError(f"Missing avg_file_to_entry mapping for {fname}")
        h = int(info["entry"]["hash"])
        scene_by_hash[h] = (sc, srows)

    off_arc, off_map = load_arc(OFFICIAL_LUA)
    base_arc, base_map = load_arc(BACKUP_DIR / "dist__lua_patched_vi.arcx")

    work = Path(tempfile.mkdtemp(prefix="lua_tramvh_stev_"))
    entries_dir = work / "entries"
    entries_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "archive_name": "lua.arcx",
        "version": base_arc.version,
        "flag": base_arc.flag,
        "entry_count": base_arc.entry_count,
        "payload_decrypted": False,
        "entries": [],
    }

    expected_readback: dict[int, list[tuple[int, str, str]]] = {}
    stats = collections.Counter()

    try:
        for h in sorted(base_map, key=lambda x: base_map[x][0]["index"]):
            e, base_enc = base_map[h]
            if h in scene_by_hash:
                sc, srows = scene_by_hash[h]
                _, off_enc = off_map[h]
                _, _, off_proto = parse_lua(off_enc)
                hdr, up, dist_proto = parse_lua(base_enc)

                if len(off_proto["protos"]) != 0 or len(dist_proto["protos"]) != 0:
                    raise RuntimeError(f"{sc}: unexpected subprotos")
                if len(off_proto["constants"]) != len(dist_proto["constants"]):
                    raise RuntimeError(
                        f"{sc}: constant table length mismatch off={len(off_proto['constants'])} dist={len(dist_proto['constants'])}"
                    )

                off_strs = [const_str(c) for c in off_proto["constants"]]
                scene_checks: list[tuple[int, str, str]] = []

                for r in srows:
                    en = r["en"]
                    idxs = [i for i, s in enumerate(off_strs) if s == en]
                    if not idxs:
                        idxs = [i for i, s in enumerate(off_strs) if s is not None and s.strip() == en.strip()]
                    if len(idxs) != 1:
                        raise RuntimeError(f"{sc} {r['line_id']}: expected 1 constant match, found {len(idxs)}")
                    idx = idxs[0]

                    orig_s = off_strs[idx]
                    lpad = len(orig_s) - len(orig_s.lstrip())
                    rpad = len(orig_s) - len(orig_s.rstrip())
                    patched_str = (" " * lpad) + r["new_vi_nfc"] + (" " * rpad)

                    cur_kind, cur_val = dist_proto["constants"][idx]
                    if cur_kind not in STR_KINDS:
                        raise RuntimeError(f"{sc} {r['line_id']}: target constant {idx} is not a string (kind={cur_kind})")
                    cur_str = cur_val[1].decode("utf-8", "replace")
                    if cur_str == patched_str:
                        stats["already_matching"] += 1
                    else:
                        stats["updated"] += 1

                    data = patched_str.encode("utf-8")
                    n = len(data) + 1
                    dist_proto["constants"][idx] = (cur_kind, (0xFF if n >= 0xFF else n, data))
                    scene_checks.append((idx, r["line_id"], patched_str))

                serialized = hdr + bytes([up]) + serialize_proto(dist_proto)
                # Verify Lua53Chunk roundtrip before encrypting
                rt_chunk = Lua53Chunk(serialized)
                rt_chunk.read_bytes(33)
                rt_chunk.read_byte()
                rt_proto = rt_chunk.parse_proto()
                for idx, lid, exp_str in scene_checks:
                    got = const_str(rt_proto["constants"][idx])
                    if got != exp_str:
                        raise RuntimeError(f"Lua roundtrip mismatch at {sc} {lid} idx={idx}")

                payload = xxtea_encrypt(serialized, XXTEA_KEY)
                expected_readback[h] = scene_checks
                stats["scenes_patched"] += 1
            else:
                payload = base_enc
                stats["untouched_entries"] += 1

            fname = f"{e['index']:05d}_{e['hash_hex']}.bin"
            (entries_dir / fname).write_bytes(payload)
            manifest["entries"].append(
                {
                    "index": e["index"],
                    "hash": h,
                    "hash_hex": e["hash_hex"],
                    "filename": fname,
                    "origin_size": len(payload),
                    "payload_size": len(payload),
                }
            )

        (work / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        STAGING_DIR.mkdir(parents=True, exist_ok=True)
        repack_archive(work, STAGING_LUA, encrypt_payload=False)
    finally:
        shutil.rmtree(work, ignore_errors=True)

    print(f"Patched & repacked -> {STAGING_LUA} | stats={dict(stats)}")
    return expected_readback


def update_manifests_and_deploy(new_size: int, new_sha: str) -> None:
    shutil.copy2(STAGING_LUA, DIST_LUA)
    print(f"Installed to {DIST_LUA} (size={new_size:,}, sha256={new_sha})")

    # 1. Update dist/patch_manifest.json
    pm_path = DIST_DIR / "patch_manifest.json"
    pm = json.loads(pm_path.read_text(encoding="utf-8"))
    pm["files"]["Persistent_Store/Scripts/lua.arcx"]["sha256"] = new_sha
    pm["files"]["Persistent_Store/Scripts/lua.arcx"]["size"] = new_size
    pm["lua_arcx"]["sha256"] = new_sha
    pm["lua_arcx"]["size_bytes"] = new_size
    pm_path.write_text(json.dumps(pm, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # 2. Update dist/android_patch_manifest.json
    apm_path = DIST_DIR / "android_patch_manifest.json"
    apm = json.loads(apm_path.read_text(encoding="utf-8"))
    old_lua_size = None
    for item in apm["files"]:
        if item.get("path") == "Persistent_Store/Scripts/lua.arcx":
            old_lua_size = item["size"]
            item["sha256"] = new_sha
            item["size"] = new_size
            break
    if old_lua_size is None:
        raise RuntimeError("Missing Persistent_Store/Scripts/lua.arcx in android_patch_manifest.json")
    apm["total_size"] = apm["total_size"] + (new_size - old_lua_size)
    apm["lua_arcx"]["sha256"] = new_sha
    apm["lua_arcx"]["size_bytes"] = new_size
    apm_path.write_text(json.dumps(apm, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # 3. Update dist/SHA256SUMS.txt
    pm_sha = sha256_file(pm_path)
    apm_sha = sha256_file(apm_path)
    sums_path = DIST_DIR / "SHA256SUMS.txt"
    new_lines = []
    for line in sums_path.read_text(encoding="utf-8").splitlines():
        if line.rstrip().endswith("  lua_patched_vi.arcx"):
            new_lines.append(f"{new_sha}  lua_patched_vi.arcx")
        elif line.rstrip().endswith("  patch_manifest.json"):
            new_lines.append(f"{pm_sha}  patch_manifest.json")
        elif line.rstrip().endswith("  android_patch_manifest.json"):
            new_lines.append(f"{apm_sha}  android_patch_manifest.json")
        else:
            new_lines.append(line)
    sums_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    print(f"Updated patch_manifest.json ({pm_sha}), android_patch_manifest.json ({apm_sha}), SHA256SUMS.txt")

    # 4. Deploy strictly from dist/lua_patched_vi.arcx to both clients
    for client_name, target in (("Yostar", YOSTAR_LUA), ("Steam", STEAM_LUA)):
        shutil.copy2(DIST_LUA, target)
        deployed_sha = sha256_file(target)
        if deployed_sha != new_sha:
            raise RuntimeError(f"Deploy hash mismatch on {client_name}: expected {new_sha}, got {deployed_sha}")
        print(f"Deployed to {client_name}: {target} (sha256={deployed_sha})")


def post_repack_readback(expected_readback: dict[int, list[tuple[int, str, str]]]) -> None:
    bk_arc, bk_map = load_arc(BACKUP_DIR / "dist__lua_patched_vi.arcx")
    new_arc, new_map = load_arc(DIST_LUA)

    if new_arc.entry_count != bk_arc.entry_count:
        raise RuntimeError(f"Entry count changed: {bk_arc.entry_count} -> {new_arc.entry_count}")
    if list(new_map.keys()) != list(bk_map.keys()):
        raise RuntimeError("Entry hash set/order changed after repack")

    checked_lines = 0
    untouched_checked = 0
    for h in new_map:
        if h in expected_readback:
            _, _, proto = parse_lua(new_map[h][1])
            for idx, lid, exp_str in expected_readback[h]:
                got = const_str(proto["constants"][idx])
                if got != exp_str:
                    raise RuntimeError(f"Post-repack readback mismatch at {lid} idx={idx}")
                checked_lines += 1
        else:
            if new_map[h][1] != bk_map[h][1]:
                raise RuntimeError(f"Untouched entry mutated: {hex(h)}")
            untouched_checked += 1

    print(
        f"Post-repack readback PASSED: {checked_lines}/189 patched lines verified, "
        f"{untouched_checked} untouched entries byte-identical."
    )


def main() -> int:
    rows = validate_rows(fetch_d1_snapshot())
    backup_before_modify()
    expected_readback = patch_lua_archive(rows)
    new_size = STAGING_LUA.stat().st_size
    new_sha = sha256_file(STAGING_LUA)
    update_manifests_and_deploy(new_size, new_sha)
    post_repack_readback(expected_readback)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
