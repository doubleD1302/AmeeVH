# -*- coding: utf-8 -*-
"""
Script to apply comprehensive story terminology and pronoun consistency fixes across all story batches, proposals, and caches, and rebuild dist/lua_patched_vi.arcx.
"""

import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
sys.path.insert(0, str(ROOT / "tools"))
from comprehensive_dialogue_polisher import polish_line

def polish_dict(filepath: Path):
    if not filepath.exists():
        return
    print(f"Polishing {filepath.name}...")
    data = json.loads(filepath.read_text(encoding="utf-8"))
    modified = 0
    for k, v in data.items():
        if isinstance(v, str):
            pv = polish_line("", v)
            if pv != v:
                data[k] = pv
                modified += 1
    if modified > 0:
        filepath.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  -> {filepath.name}: {modified} lines polished.")

def polish_jsonl(filepath: Path, vi_field: str):
    if not filepath.exists():
        return
    print(f"Polishing {filepath.name}...")
    lines = filepath.read_text(encoding="utf-8").splitlines()
    new_lines = []
    modified = 0
    for l in lines:
        if not l.strip():
            continue
        obj = json.loads(l)
        v = obj.get(vi_field)
        if isinstance(v, str):
            pv = polish_line("", v)
            if pv != v:
                obj[vi_field] = pv
                modified += 1
        new_lines.append(json.dumps(obj, ensure_ascii=False))
    if modified > 0:
        filepath.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    print(f"  -> {filepath.name}: {modified} lines polished.")

def main():
    print("=== STARTING COMPREHENSIVE STORY TERMINOLOGY AND PRONOUN POLISH ===")
    t0 = time.time()

    # 1. Polish batch files
    batch_files = [
        ROOT / "work/batches/batch_10k_approved.json",
        ROOT / "work/batches/batch_10k_b2_approved.json",
        ROOT / "work/batches/batch_10k_b3_approved.json",
        ROOT / "work/batches/batch_10k_b4_approved.json",
        ROOT / "work/batches/remaining_lua_avg_cache.json",
        ROOT / "work/batches/dialogue_remaining_avg_approved.json",
    ]
    for bf in batch_files:
        polish_dict(bf)

    # 2. Polish campaign proposals
    proposals = [
        (ROOT / "work/editorial/lightnovel_editorial_20261024_r02/UNIFIED_STORY_PROPOSALS.jsonl", "vi"),
        (ROOT / "work/editorial/phone_messages_editorial_20261024_r01/UNIFIED_PHONE_PROPOSALS.jsonl", "vi_editorial"),
        (ROOT / "work/editorial/character_cg_stories_editorial_20261024_r01/UNIFIED_CG_PROPOSALS.jsonl", "vi_editorial"),
        (ROOT / "work/editorial/act3_story_editorial_20261024_r01/UNIFIED_ACT3_PROPOSALS.jsonl", "vi_editorial"),
        (ROOT / "work/editorial/act2_climax_story_editorial_20261024_r01/UNIFIED_ACT2_CLIMAX_PROPOSALS.jsonl", "vi_editorial"),
        (ROOT / "work/editorial/phone_messages_phase2_20261024_r01/UNIFIED_PM_PHASE2_PROPOSALS.jsonl", "vi_editorial"),
        (ROOT / "work/editorial/act1_act2_story_editorial_20261024_r01/UNIFIED_ACT1_ACT2_PROPOSALS.jsonl", "vi_editorial"),
        (ROOT / "work/editorial/act3_part1_story_editorial_20261024_r01/UNIFIED_ACT3_PART1_PROPOSALS.jsonl", "vi_editorial"),
        (ROOT / "work/editorial/act4_final_story_editorial_20261024_r01/UNIFIED_ACT4_STORY_PROPOSALS.jsonl", "vi_editorial"),
        (ROOT / "work/editorial/character_cg_part2_editorial_20261024_r01/UNIFIED_CG_PART2_PROPOSALS.jsonl", "vi_editorial"),
        (ROOT / "work/editorial/side_stories_part1_editorial_20261025_r01/UNIFIED_STSP_PART1_PROPOSALS.jsonl", "vi_editorial"),
        (ROOT / "work/editorial/side_stories_part2_editorial_20261025_r01/UNIFIED_CAMPAIGN13_PROPOSALS.jsonl", "vi_editorial"),
        (ROOT / "work/editorial/event_stories_part2_editorial_20261025_r01/UNIFIED_CAMPAIGN_14_PROPOSALS.jsonl", "vi_editorial"),
        (ROOT / "work/editorial/event_stories_part3_editorial_20261025_r01/UNIFIED_CAMPAIGN_15_PROPOSALS.jsonl", "vi_editorial"),
        (ROOT / "work/editorial/event_stories_part4_editorial_20261025_r01/UNIFIED_CAMPAIGN_16_PROPOSALS.jsonl", "vi_editorial"),
        (ROOT / "work/editorial/tutorial_and_character_cg_editorial_20261025_r01/UNIFIED_CAMPAIGN_17_PROPOSALS.jsonl", "vi_editorial"),
        (ROOT / "work/editorial/final_cg_npc_and_disc_editorial_20261025_r01/UNIFIED_CAMPAIGN_18_PROPOSALS.jsonl", "proposed_vi"),
        (ROOT / "work/editorial/campaign19_polish_remaining_20680_20261025_r01/UNIFIED_CAMPAIGN_19_POLISHED.jsonl", "polished_vi"),
    ]
    for pf, k in proposals:
        polish_jsonl(pf, k)

    # 3. Explicit high-priority overrides for child pronouns and specific scenes
    unified_p1 = ROOT / "work/editorial/lightnovel_editorial_20261024_r02/UNIFIED_STORY_PROPOSALS.jsonl"
    if unified_p1.exists():
        lines = unified_p1.read_text(encoding="utf-8").splitlines()
        new_lines = []
        for l in lines:
            if not l.strip(): continue
            obj = json.loads(l)
            if obj.get("id") == "STm01_07.112":
                obj["vi"] = "Em ước gì mình cũng có được một chiếc điện thoại màn hình to đùng như của Sếp, ==PLAYER_NAME== ơi!"
            elif obj.get("id") == "STm01_03.77":
                obj["vi"] = "Bastelina, cô có thể nhắc cho tôi nhớ xem cả nhóm chúng ta ở bên trong Cửa Hàng Hồn Thạch bao lâu rồi không?"
            new_lines.append(json.dumps(obj, ensure_ascii=False))
        unified_p1.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    print(f"\nAll files polished in {time.time()-t0:.1f}s.")

    # 4. Rebuild lua_patched_vi.arcx
    print("\nRebuilding lua_patched_vi.arcx via build_lua_arcx_v097.py...")
    py_exe = sys.executable
    rebuild_script = ROOT / "tools/build_lua_arcx_v097.py"
    t1 = time.time()
    res = subprocess.run([py_exe, str(rebuild_script)], cwd=str(ROOT), capture_output=True, text=True)
    if res.returncode != 0:
        print(f"ERROR: build_lua_arcx_v097 failed: {res.stderr}")
        sys.exit(res.returncode)
    print(res.stdout)
    print(f"Rebuild completed in {time.time()-t1:.1f}s.")

if __name__ == "__main__":
    main()
