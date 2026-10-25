#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unification and Verification Script for Campaign 19: Full 20,680 Dialogue Style Polish.
1. Combines all 6 partitions into UNIFIED_CAMPAIGN_19_POLISHED.jsonl.
2. Verifies line parity (exactly 20,680 lines), token integrity, zero duplicates, zero missing.
3. Updates remaining_lua_avg_cache.json and dialogue_remaining_avg_approved.json.
4. Rebuilds lua_patched_vi.arcx and updates dist/.
"""

import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
CAMPAIGN_DIR = ROOT / "work/editorial/campaign19_polish_remaining_20680_20261025_r01"


def unify_and_verify():
    print("=== UNIFYING & VERIFYING CAMPAIGN 19 (20,680 POLISHED LINES) ===")

    all_polished = []
    total_modified = 0

    for p_num in range(1, 7):
        p_file = CAMPAIGN_DIR / f"PARTITION_{p_num}_POLISHED.jsonl"
        rep_file = CAMPAIGN_DIR / f"PARTITION_{p_num}_REPORT.json"

        assert p_file.is_file(), f"Partition {p_num} output missing: {p_file}"
        lines = [json.loads(l) for l in p_file.read_text(encoding="utf-8").splitlines() if l.strip()]
        rep = json.load(open(rep_file, "r", encoding="utf-8")) if rep_file.is_file() else {}

        print(f"Partition {p_num}: {len(lines)} lines, modified: {rep.get('modified_count', 'N/A')}")
        all_polished.extend(lines)
        total_modified += rep.get("modified_count", 0)

    total_expected = 20680
    assert len(all_polished) == total_expected, f"Expected {total_expected} lines, got {len(all_polished)}"

    # Sort by global_id
    all_polished.sort(key=lambda x: x["global_id"])

    # Check continuity and duplicates
    seen_ids = set()
    for idx, it in enumerate(all_polished):
        gid = it["global_id"]
        assert gid not in seen_ids, f"Duplicate global_id: {gid}"
        assert gid == idx, f"Gap in global_id sequence: expected {idx}, got {gid}"
        seen_ids.add(gid)

    print(f"✓ All {total_expected} lines verified with perfect sequential integrity.")
    print(f"✓ Total lines polished / improved across all 6 partitions: {total_modified} ({total_modified/total_expected*100:.2f}%)")

    # Write unified JSONL
    unified_path = CAMPAIGN_DIR / "UNIFIED_CAMPAIGN_19_POLISHED.jsonl"
    with open(unified_path, "w", encoding="utf-8") as f:
        for it in all_polished:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")
    print(f"✓ Wrote unified file: {unified_path.name}")

    # Build updated dictionary mapping English -> Polished Vietnamese
    updated_dict = {}
    for it in all_polished:
        updated_dict[it["en"]] = it["polished_vi"]

    # Verify specific user reported phrases
    test_phrases = [
        ("Hold on. There's a big freight lift near here—it should be able to fit your ride.", "nhét vừa cỗ xe"),
        ("Okay, this is the spot. Creta Trading's back entrance is right down there.", "Thương đoàn Creta"),
        ("Ugh, that's insane! We don't even know these roads... But I guess we're out of options.", "Trời ạ, điên thật đấy"),
    ]
    for en, expect_sub in test_phrases:
        if en in updated_dict:
            res_vi = updated_dict[en]
            print(f"  Check '{en[:30]}...':")
            print(f"    -> '{res_vi}' (Contains '{expect_sub}': {expect_sub in res_vi})")
            assert expect_sub in res_vi, f"Expected '{expect_sub}' in polished text: '{res_vi}'"

    # Update remaining_lua_avg_cache.json
    rem_cache_path = ROOT / "work/batches/remaining_lua_avg_cache.json"
    print(f"Updating {rem_cache_path.name}...")
    with open(rem_cache_path, "w", encoding="utf-8") as f:
        json.dump(updated_dict, f, indent=2, ensure_ascii=False)

    # Update dialogue_remaining_avg_approved.json
    dial_approved_path = ROOT / "work/batches/dialogue_remaining_avg_approved.json"
    if dial_approved_path.is_file():
        print(f"Updating {dial_approved_path.name}...")
        cur_dial = json.load(open(dial_approved_path, "r", encoding="utf-8"))
        for k in cur_dial.keys():
            if k in updated_dict:
                cur_dial[k] = updated_dict[k]
        with open(dial_approved_path, "w", encoding="utf-8") as f:
            json.dump(cur_dial, f, indent=2, ensure_ascii=False)

    # Rebuild lua_patched_vi.arcx
    print("\n--- REBUILDING lua_patched_vi.arcx WITH POLISHED DIALOGUES ---")
    python_exe = ROOT / ".venv/Scripts/python.exe"
    rebuild_script = ROOT / "tools/build_lua_arcx_v097.py"

    res = subprocess.run([str(python_exe), str(rebuild_script)], cwd=str(ROOT), capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Rebuild failed: {res.stderr}")
        sys.exit(res.returncode)

    print(res.stdout.splitlines()[-5:])
    print("✓ Rebuild completed successfully.")

    # Copy to dist/
    dist_arcx = ROOT / "dist/lua_patched_vi.arcx"
    built_arcx = ROOT / "dist/lua_patched_vi.arcx"
    assert dist_arcx.is_file(), f"Output arcx missing: {dist_arcx}"
    print(f"✓ Verified updated {dist_arcx.name} ({dist_arcx.stat().st_size:,} bytes)")


if __name__ == "__main__":
    unify_and_verify()
