#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prepare Campaign 5: Act 3 Main Story & Allies Phone Messages (3,333 lines).
Run ID: act3_story_editorial_20261024_r01
- Partition A (translator_act3_a): 1,585 lines (STm08_10 to STm08_18_b)
- Partition B (translator_act3_b): 1,748 lines (STm08_19_a to STm08_21 + PM11601 to PM12001)
- QA Reviewer (qa_reviewer_act3): Independent evaluation
"""

import json
import os
import re
import hashlib
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
RUN_ID = "act3_story_editorial_20261024_r01"
RUN_DIR = ROOT / "work/runs" / RUN_ID
SUBAGENT_BASE = ROOT / "work/subagents" / RUN_ID
EDITORIAL_DIR = ROOT / "work/editorial" / RUN_ID

def sha256_file(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def extract_tokens(text):
    tokens = []
    for m in re.findall(r"==[A-Z0-9_]+==|<[^>]+>|\{[0-9]+\}", text):
        if m not in tokens:
            tokens.append(m)
    return tokens

tech_patterns = [
    r"^SetPhoneMsgChoiceBegin$", r"^SetPhoneMsgChoiceJumpTo$",
    r"^SetPhoneMsgChoiceRollover$", r"^SetPhoneMsgChoiceEnd$",
    r"^SetPhoneMsg", r"^ep_", r"^story_", r"^bg_", r"^se_", r"^snd_", r"^vo_"
]

def is_tech_line(s):
    if not s or not s.strip(): return True
    return any(re.search(p, s) for p in tech_patterns)

def main():
    print(f"=== PREPARING CAMPAIGN 5: {RUN_ID} ===")
    
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    EDITORIAL_DIR.mkdir(parents=True, exist_ok=True)
    for sub in ["translator_act3_a", "translator_act3_b", "qa_reviewer_act3"]:
        (SUBAGENT_BASE / sub).mkdir(parents=True, exist_ok=True)

    b3_path = ROOT / "work/batches/batch_10k_b3_partC.json"
    tr_path = ROOT / "work/batches/batch_10k_b3_partC_translated.json"
    
    data_en = json.load(open(b3_path, encoding="utf-8"))
    data_tr = json.load(open(tr_path, encoding="utf-8")) if tr_path.exists() else {}
    
    print(f"Loaded {len(data_en)} lines from {b3_path.name}")
    
    # Split into Part A and Part B
    # Boundary: STm08_18_b is the end of Part A
    scenes_a = {
        'STm08_10', 'STm08_11', 'STm08_12', 'STm08_13', 'STm08_14',
        'STm08_15', 'STm08_16_a', 'STm08_16_b', 'STm08_17_a', 'STm08_17_b',
        'STm08_18_a', 'STm08_18_b'
    }
    
    part_a_lines = []
    part_b_lines = []
    
    for lid, en_text in data_en.items():
        sc = lid.split(".")[0]
        curr_vi = data_tr.get(lid, "")
        item = {
            "id": lid,
            "scene_id": sc,
            "en": en_text,
            "current_vi": curr_vi,
            "tokens": extract_tokens(en_text) if en_text else [],
            "is_tech": is_tech_line(en_text)
        }
        if sc in scenes_a:
            item["partition"] = "PARTITION_A"
            part_a_lines.append(item)
        else:
            item["partition"] = "PARTITION_B"
            part_b_lines.append(item)
            
    print(f"Partition A (Act 3 Part 1): {len(part_a_lines)} lines across {len(scenes_a)} scenes")
    scenes_b = set(x["scene_id"] for x in part_b_lines)
    print(f"Partition B (Act 3 Part 2 & PM): {len(part_b_lines)} lines across {len(scenes_b)} scenes")
    assert len(part_a_lines) + len(part_b_lines) == 3333, "Total must equal 3333!"
    
    # Write jsonl files
    p_a_path = SUBAGENT_BASE / "translator_act3_a" / "PARTITION_A_CANDIDATES.jsonl"
    p_b_path = SUBAGENT_BASE / "translator_act3_b" / "PARTITION_B_CANDIDATES.jsonl"
    
    with open(p_a_path, "w", encoding="utf-8") as f:
        for it in part_a_lines:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")
            
    with open(p_b_path, "w", encoding="utf-8") as f:
        for it in part_b_lines:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")
            
    print(f"Wrote {p_a_path} ({sha256_file(p_a_path)[:12]}...)")
    print(f"Wrote {p_b_path} ({sha256_file(p_b_path)[:12]}...)")

    # Generate Task Packets
    common_inputs = [
        {"path": "work/character_context_20261023_r02/CHARACTER_VOICE_BIBLE.md", "version": "r02"},
        {"path": "work/character_context_20261023_r02/CHARACTER_VOICE_PROFILES.json", "version": "r02"},
        {"path": "docs/LIGHTNOVEL_STYLE_BIBLE_VI.md", "version": "r01"},
        {"path": "docs/HUMOR_LOCALIZATION_VI.md", "version": "r01"},
        {"path": "docs/EDITORIAL_QA_RUBRIC.md", "version": "r01"}
    ]

    tasks_meta = [
        {
            "task_id": "translator_act3_a",
            "role": "TRANSLATOR_ACT3_A",
            "desc": "Translate Main Story Act 3 Part 1 (Desert Canyon & Scorpion Legion Siege: STm08_10 to STm08_18_b — 1,585 lines) into lively modern Light Novel Vietnamese.",
            "input_partition": str(p_a_path),
            "write_dir": str(SUBAGENT_BASE / "translator_act3_a")
        },
        {
            "task_id": "translator_act3_b",
            "role": "TRANSLATOR_ACT3_B",
            "desc": "Translate Main Story Act 3 Part 2 (Pinnacle Battle: STm08_19_a to STm08_21) and Allies Phone Messages (Ridge, Eleanor, Coronis, Nanoha, Canace: PM11601 to PM12001 — 1,748 lines) into lively modern Light Novel Vietnamese.",
            "input_partition": str(p_b_path),
            "write_dir": str(SUBAGENT_BASE / "translator_act3_b")
        }
    ]

    for t in tasks_meta:
        task_packet = {
            "schema": 1,
            "run_id": RUN_ID,
            "task_id": t["task_id"],
            "role": t["role"],
            "project_root": "C:/YostarGames/StellaSora_EN/StellaSora_VietHoa",
            "objective": t["desc"],
            "input_snapshots": common_inputs + [{"path": t["input_partition"], "sha256": sha256_file(t["input_partition"])}],
            "allowed_write_paths": [t["write_dir"]],
            "completion_criteria": [
                "100% of candidate dialogues translated into modern Light Novel Vietnamese",
                "Strict adherence to Character Voice Bible pronouns and personality markers",
                "Strict preservation of technical tokens: ==PLAYER_NAME==, ==W==, <color=...>, <r=...>, {0}, \\n",
                "Natural Vietnamese prose, witty and engaging dialogue; zero machine translation calques",
                "NFC Unicode UTF-8 compliance",
                "Outputs: PROPOSALS.jsonl, AUDIT.json, RESULT.json"
            ],
            "output_report": f"{t['write_dir']}/RESULT.json",
            "task_status": "assigned"
        }
        packet_path = RUN_DIR / f"{t['task_id']}.task.json"
        with open(packet_path, "w", encoding="utf-8") as f:
            json.dump(task_packet, f, ensure_ascii=False, indent=2)
        print(f"Created task packet: {packet_path.name}")

    print("\n=== PREPARATION FOR CAMPAIGN 5 COMPLETE ===")

if __name__ == "__main__":
    main()
