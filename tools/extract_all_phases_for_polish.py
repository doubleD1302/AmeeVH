#!/usr/bin/env python3
"""Extract datasets for Phase 2A, 2B, and 3 for parallel localization polish."""

import json
from pathlib import Path

def extract_group(group_name, tables, p_orig, p_curr, out_dir):
    dataset = {}
    total_keys = 0
    for name, fname in tables.items():
        with open(p_orig / fname, 'r', encoding='utf-8') as f:
            orig = json.load(f)
        with open(p_curr / fname, 'r', encoding='utf-8') as f:
            curr = json.load(f)

        dataset[name] = []
        for k, en_val in orig.items():
            if not en_val:
                continue
            curr_val = curr.get(k, en_val)
            dataset[name].append({
                'key': k,
                'en': en_val,
                'vi_current': curr_val
            })
            total_keys += 1

    out_file = out_dir / f"{group_name}_dataset.json"
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)

    print(f"Extracted {group_name} -> {out_file}: {total_keys} keys across {len(tables)} tables.")
    for name, items in dataset.items():
        print(f"  - {name}: {len(items)} items")

def main():
    root = Path(__file__).parent.parent
    p_orig = root / 'work' / 'research' / 'data_en_original' / 'entries'
    p_curr = root / 'work' / 'research' / 'data_decrypted' / 'entries'
    out_dir = root / 'work' / 'polish'
    out_dir.mkdir(parents=True, exist_ok=True)

    # Phase 2A: Items & Skills
    tables_2a = {
        'Item': '00577_0xe60634348b826f41.bin',
        'Skill': '00636_0x998f849a64309b25.bin',
        'MainSkill': '00591_0x57e760255c1d3b2d.bin',
        'SecondarySkill': '00635_0x31a8814a91313129.bin',
        'EffectDesc': '00555_0xb5c092c120570535.bin'
    }
    extract_group('phase2a', tables_2a, p_orig, p_curr, out_dir)

    # Phase 2B: Talents & Potentials & FateCards
    tables_2b = {
        'Talent': '00680_0x3f0bd5f8db2389b6.bin',
        'Potential': '00624_0x02ce11eca01b5fc8.bin',
        'FateCard': '00560_0x788d8a3db60dd08a.bin'
    }
    extract_group('phase2b', tables_2b, p_orig, p_curr, out_dir)

    # Phase 3: Story, Dating, Quests & Economy
    tables_3 = {
        'Story': '00669_0xdda397c15ce0b289.bin',
        'ActivityStory': '00506_0x0c2ee3471b91208e.bin',
        'DatingCharacterEvent': '00544_0xd46d025e8dae5d69.bin',
        'DatingLandmarkEvent': '00546_0xdc09272e31aceb9b.bin',
        'AffinityQuest': '00510_0xde9e039952f8c2d2.bin',
        'AffinityUpReward': '00511_0xc0b538ebf3963e61.bin',
        'ActivityTask': '00507_0x5c7be7cfcb1d2241.bin',
        'ActivityGoods': '00498_0x988f7b6f2592bacd.bin',
        'MallPackage': '00594_0xee9e1d54770d965d.bin',
        'PenguinCard': '00612_0x6125df00885a1629.bin'
    }
    extract_group('phase3', tables_3, p_orig, p_curr, out_dir)

if __name__ == '__main__':
    main()
