# -*- coding: utf-8 -*-
"""
Script to apply global story terminology and pronoun harmonizations across all source batches and proposals.
Target fixes:
1. "The Well of Worlds" / "Giếng Thế Giới" / "Giếng nước của thế giới" -> "Giếng Vạn Giới"
2. "The Well of Worlds Tyrant Development System" / "Hệ Thống Bồi Dưỡng Bạo Chúa - Giếng Thế Giới" -> "Hệ Thống Bồi Dưỡng Bạo Chúa Giếng Vạn Giới"
3. "Bạo Quân" -> "Bạo Chúa"
4. "ông chủ" (when referring to Boss / Main Character) -> "Sếp"
5. Main pronouns and partner pronouns -> "cậu" / "tôi" / "tớ"
"""

import json
from pathlib import Path
import re
import sys

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
sys.path.insert(0, str(ROOT / "tools"))
from comprehensive_dialogue_polisher import polish_line

def polish_string(s: str) -> str:
    if not isinstance(s, str) or not s.strip():
        return s
    return polish_line("", s)

def update_json_batch(filepath: Path):
    if not filepath.exists():
        return
    data = json.loads(filepath.read_text(encoding="utf-8"))
    modified = 0
    for k, v in data.items():
        if isinstance(v, str):
            new_v = polish_string(v)
            if new_v != v:
                data[k] = new_v
                modified += 1
    if modified > 0:
        filepath.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Updated {filepath.name}: {modified} strings polished.")

def update_jsonl_proposals(filepath: Path, vi_field: str):
    if not filepath.exists():
        return
    lines = filepath.read_text(encoding="utf-8").splitlines()
    new_lines = []
    modified = 0
    for l in lines:
        if not l.strip():
            continue
        obj = json.loads(l)
        v = obj.get(vi_field)
        if isinstance(v, str):
            new_v = polish_string(v)
            if new_v != v:
                obj[vi_field] = new_v
                modified += 1
        new_lines.append(json.dumps(obj, ensure_ascii=False))
    if modified > 0:
        filepath.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
        print(f"Updated {filepath.name}: {modified} lines polished.")

def main():
    print("=== STARTING GLOBAL STORY TERMINOLOGY AND PRONOUN HARMONIZATION ===")
    
    # 1. Update batch JSON files
    batch_files = [
        ROOT / "work/batches/batch_10k_approved.json",
        ROOT / "work/batches/batch_10k_b2_approved.json",
        ROOT / "work/batches/batch_10k_b3_approved.json",
        ROOT / "work/batches/batch_10k_b4_approved.json",
        ROOT / "work/batches/remaining_lua_avg_cache.json",
        ROOT / "work/batches/dialogue_remaining_avg_approved.json",
    ]
    for bf in batch_files:
        update_json_batch(bf)

    # 2. Update campaign proposals
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
    for pf, key in proposals:
        update_jsonl_proposals(pf, key)

    print("\nAll source batches and proposals updated successfully!")

if __name__ == "__main__":
    main()
