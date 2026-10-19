#!/usr/bin/env python3
"""Final Comprehensive QA and Audit Script for Phase 2A."""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POLISHED_PATH = ROOT / "work" / "polish" / "phase2a_polished.json"
DATASET_PATH = ROOT / "work" / "polish" / "phase2a_dataset.json"
ENTRIES_DIR = ROOT / "work" / "research" / "data_decrypted" / "entries"
ORIG_DIR = ROOT / "work" / "research" / "data_en_original" / "entries"

TABLE_FILES = {
    'Item': '00577_0xe60634348b826f41.bin',
    'Skill': '00636_0x998f849a64309b25.bin',
    'MainSkill': '00591_0x57e760255c1d3b2d.bin',
    'SecondarySkill': '00635_0x31a8814a91313129.bin',
    'EffectDesc': '00555_0xb5c092c120570535.bin'
}

BLACKLIST = [
    (re.compile(r'sao nhổ', re.I), "Sao nhổ"),
    (re.compile(r'cuộc chinh phục sao nhổ', re.I), "Cuộc chinh phục sao nhổ"),
    (re.compile(r'mất khả năng lao động', re.I), "mất khả năng lao động"),
    (re.compile(r'SPD chuyển động', re.I), "SPD chuyển động"),
    (re.compile(r'có thể được sử dụng trong', re.I), "có thể được sử dụng trong"),
    (re.compile(r'nó giải phóng những tài năng chôn vùi', re.I), "nó giải phóng những tài năng chôn vùi"),
    (re.compile(r'ở một mình trong vùng hoang dã', re.I), "ở một mình trong vùng hoang dã"),
    (re.compile(r'giấy vụn', re.I), "giấy vụn"),
    (re.compile(r'người đi bộ|người đi phượt', re.I), "người đi bộ / đi phượt"),
    (re.compile(r'nguyên khối', re.I), "nguyên khối"),
    (re.compile(r'mục tiêu ưu tú', re.I), "mục tiêu ưu tú"),
    (re.compile(r'\bthiệt hại\b', re.I), "thiệt hại"),
    (re.compile(r'Lính của họ', re.I), "Lính của họ"),
    (re.compile(r'\b(Aqua|Ignis|Ventus|Terra|Lux|Umbra)\s+(?:Lữ khách|Main|Support)', re.I), "Raw element before role"),
    (re.compile(r'đồng đội (?:Aqua|Ignis|Ventus|Terra|Lux|Umbra)\b', re.I), "Raw element in squadmates"),
]

def main():
    print("=" * 70)
    print("EXHAUSTIVE QUALITY ASSURANCE AUDIT - PHASE 2A")
    print("=" * 70)

    with open(POLISHED_PATH, 'r', encoding='utf-8') as f:
        polished = json.load(f)

    with open(DATASET_PATH, 'r', encoding='utf-8') as f:
        dataset = json.load(f)

    # 1. Check counts and schema
    total_items = 0
    for tname, fname in TABLE_FILES.items():
        pol_items = polished[tname]
        orig_items = dataset[tname]
        assert len(pol_items) == len(orig_items)
        total_items += len(pol_items)

        # Check bin file
        bin_p = ENTRIES_DIR / fname
        orig_p = ORIG_DIR / fname
        with open(bin_p, 'r', encoding='utf-8') as f:
            bin_data = json.load(f)
        with open(orig_p, 'r', encoding='utf-8') as f:
            orig_data = json.load(f)

        assert set(bin_data.keys()) == set(orig_data.keys()), f"Key set mismatch in {fname}"
        print(f"Table {tname:15}: {len(pol_items):5} items verified against {fname}")

    print(f"\nTotal items verified across 5 tables: {total_items}")

    # 2. Blacklist & Quality Audit
    print("\n--- Blacklist & Cliché Check ---")
    total_violations = 0
    for tname, items in polished.items():
        for it in items:
            vi = it['vi']
            for pattern, name in BLACKLIST:
                m = pattern.findall(vi)
                if m:
                    print(f"VIOLATION in {tname} [{it['key']}]: {name} -> {m}")
                    print(f"  Text: {vi}")
                    total_violations += 1

    if total_violations == 0:
        print("PERFECT: 0 violations found across all 8,452 entries!")
    else:
        print(f"WARNING: Found {total_violations} violations!")

    # 3. Before / After Sample Showcase
    print("\n" + "=" * 70)
    print("BEFORE / AFTER SHOWCASE ACROSS ALL 5 TABLES")
    print("=" * 70)

    showcase_keys = [
        ('Item', 'Item.1.2'),
        ('Item', 'Item.1.3'),
        ('Item', 'Item.1000.3'),
        ('Item', 'Item.1001.3'),
        ('Item', 'Item.1030.3'),
        ('Item', 'Item.11.2'),
        ('Item', 'Item.11.3'),
        ('Item', 'Item.29.3'),
        ('Item', 'Item.116016.1'),
        ('Item', 'Item.198026.2'),
        ('Item', 'Item.199000.1'),
        ('Skill', 'Skill.100010302.2'),
        ('Skill', 'Skill.10331000.13'),
        ('Skill', 'Skill.10331000.2'),
        ('Skill', 'Skill.10332000.13'),
        ('Skill', 'Skill.11131001.2'),
        ('MainSkill', 'MainSkill.300301.2'),
        ('MainSkill', 'MainSkill.400101.2'),
        ('MainSkill', 'MainSkill.400901.2'),
        ('MainSkill', 'MainSkill.405701.2'),
        ('MainSkill', 'MainSkill.405801.2'),
        ('MainSkill', 'MainSkill.405901.2'),
        ('SecondarySkill', 'SecondarySkill.3001101.2'),
        ('SecondarySkill', 'SecondarySkill.3003101.2'),
        ('SecondarySkill', 'SecondarySkill.4001101.2'),
        ('SecondarySkill', 'SecondarySkill.4002201.2'),
        ('SecondarySkill', 'SecondarySkill.4026101.2'),
        ('SecondarySkill', 'SecondarySkill.4027101.2'),
        ('SecondarySkill', 'SecondarySkill.4055201.2'),
        ('SecondarySkill', 'SecondarySkill.4060201.2'),
        ('EffectDesc', 'EffectDesc.120601.1'),
        ('EffectDesc', 'EffectDesc.120431.1'),
        ('EffectDesc', 'EffectDesc.990051.1')
    ]

    for tname, key in showcase_keys:
        p_item = next(x for x in polished[tname] if x['key'] == key)
        o_item = next(x for x in dataset[tname] if x['key'] == key)
        print(f"\n[{tname}] Key: {key}")
        print(f"  EN    : {p_item['en']}")
        print(f"  BEFORE: {o_item['vi_current']}")
        print(f"  AFTER : {p_item['vi']}")

if __name__ == '__main__':
    main()
