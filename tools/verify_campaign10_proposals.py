#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verification and Merge Tool for Campaign 10 (Đợt 2):
Act 4 Final Climax Story (STm09_00_a to STm09_07_a, 2,923 items across 21 scenes).
"""

import json
from pathlib import Path
import re
import sys
import unicodedata

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
CAMPAIGN_DIR = ROOT / "work/editorial/act4_final_story_editorial_20261024_r01"

SOURCE_A = CAMPAIGN_DIR / "PARTITION_A_SOURCE.json"
SOURCE_B = CAMPAIGN_DIR / "PARTITION_B_SOURCE.json"

PROP_A = CAMPAIGN_DIR / "PROPOSALS_PARTITION_A.jsonl"
PROP_B = CAMPAIGN_DIR / "PROPOSALS_PARTITION_B.jsonl"

UNIFIED_OUT = CAMPAIGN_DIR / "UNIFIED_ACT4_STORY_PROPOSALS.jsonl"

BANNED_WORDS = [
    r"\bMa Vương\b",
    r"\bchết tiệt\b",
    r"\bbạn biết đấy\b",
    r"\bcái quái gì\b",
    r"\blàm sao mà\b",
    r"\btrỗi dậy và tỏa sáng\b",
    r"\bnhảy ra khỏi lồng ngực\b",
    r"\bGrand Thanh tra\b",
    r"\bHòn Hồn Thạch\b",
    r"\bnhững kẻ buồn ngủ\b",
    r"\btrục mìn\b",
]

TAG_PATTERN = re.compile(r'<[^>]+>|==[A-Z0-9_-]+==|\{[0-9]+\}')

def check_tokens(src_tokens, dst_text):
    dst_tokens = TAG_PATTERN.findall(dst_text)
    return sorted(src_tokens) == sorted(dst_tokens), src_tokens, dst_tokens

def audit_partition(prop_path, src_path, part_name):
    print(f"--- Auditing {part_name} ({prop_path.name}) ---")
    if not prop_path.exists():
        print(f"WAITING: {prop_path.name} does not exist yet.")
        return False, []

    with open(src_path, 'r', encoding='utf-8') as f:
        src_data = json.load(f)
    src_map = {item['id']: item for item in src_data}

    props = []
    with open(prop_path, 'r', encoding='utf-8') as f:
        for idx, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
                props.append(item)
            except Exception as e:
                print(f"JSON Parse Error at line {idx}: {e}")
                return False, []

    print(f"Expected: {len(src_data)} | Actual: {len(props)}")
    if len(props) != len(src_data):
        print(f"ERROR: Line count mismatch in {part_name}!")
        return False, []

    blockers = []
    majors = []
    
    for item in props:
        iid = item.get("id")
        vi = item.get("vi_editorial", "")
        src_item = src_map.get(iid)
        if not src_item:
            blockers.append(f"[{iid}] ID not found in source dataset")
            continue
        
        # 1. NFC normalization check
        if vi != unicodedata.normalize('NFC', vi):
            majors.append(f"[{iid}] Text is not NFC normalized")

        # 2. Token preservation check
        src_en = src_item.get("en", "")
        src_tokens = TAG_PATTERN.findall(src_en)
        ok, st, dt = check_tokens(src_tokens, vi)
        if not ok:
            blockers.append(f"[{iid}] Token mismatch! Src: {st} vs Dst: {dt}")

        # 3. Banned word check
        for bw in BANNED_WORDS:
            if re.search(bw, vi, re.IGNORECASE):
                majors.append(f"[{iid}] Contains banned MT calque matching pattern '{bw}': {vi}")

        # 4. Untranslated / empty check
        if not vi.strip() and src_en.strip():
            blockers.append(f"[{iid}] Empty translation!")

    print(f"Audit results for {part_name}: {len(blockers)} Blockers, {len(majors)} Majors.")
    if blockers:
        for b in blockers[:10]:
            print("  [BLOCKER]", b)
    if majors:
        for m in majors[:10]:
            print("  [MAJOR]", m)

    return len(blockers) == 0, props

def main():
    ok_a, props_a = audit_partition(PROP_A, SOURCE_A, "Partition A")
    ok_b, props_b = audit_partition(PROP_B, SOURCE_B, "Partition B")

    if ok_a and ok_b:
        print("Both partitions PASSED audit! Writing UNIFIED proposals...")
        total_props = props_a + props_b
        with open(UNIFIED_OUT, 'w', encoding='utf-8') as f:
            for p in total_props:
                f.write(json.dumps(p, ensure_ascii=False) + "\n")
        print(f"Successfully created {UNIFIED_OUT.name} with {len(total_props)} items!")
        return 0
    else:
        print("Audit failed or waiting for partitions to finish.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
