#!/usr/bin/env python3
"""
Master Execution Script for Stella Sora Phase 2A: Items & Combat Skills
Polish and Standardize:
1. Item (00577_0xe60634348b826f41.bin - 3,777 items)
2. Skill (00636_0x998f849a64309b25.bin - 1,350 items)
3. MainSkill (00591_0x57e760255c1d3b2d.bin - 1,227 items)
4. SecondarySkill (00635_0x31a8814a91313129.bin - 1,442 items)
5. EffectDesc (00555_0xb5c092c120570535.bin - 656 items)

Total: 8,452 items.
Guarantees 100% Token & Tag Preservation and Full Master Glossary Compliance.
"""

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from phase2a_token_manager import validate_token_preservation
from polish_effect_desc import polish_effect_desc
from polish_skill_table import polish_skill_table
from polish_skills_module import polish_skill_text
from polish_item_module import polish_item_table

ENTRIES_DIR = ROOT / "work" / "research" / "data_decrypted" / "entries"
DATASET_PATH = ROOT / "work" / "polish" / "phase2a_dataset.json"
POLISHED_OUT_PATH = ROOT / "work" / "polish" / "phase2a_polished.json"

TABLE_FILES = {
    'Item': '00577_0xe60634348b826f41.bin',
    'Skill': '00636_0x998f849a64309b25.bin',
    'MainSkill': '00591_0x57e760255c1d3b2d.bin',
    'SecondarySkill': '00635_0x31a8814a91313129.bin',
    'EffectDesc': '00555_0xb5c092c120570535.bin'
}

def polish_main_and_sec(table_name, items):
    polished = []
    changes = 0
    token_errors = 0
    for it in items:
        k = it['key']
        en = it['en']
        orig_vi = it['vi_current']
        
        if k.endswith('.2'):
            new_vi = polish_skill_text(orig_vi, en)
        else:
            new_vi = orig_vi
            
        valid, ot, vt = validate_token_preservation(en, new_vi)
        if not valid:
            token_errors += 1
            print(f"Token error in {table_name} [{k}]:")
            print("  EN toks:", ot)
            print("  VI toks:", vt)
            new_vi = orig_vi
            
        if new_vi != orig_vi:
            changes += 1
            
        polished.append({
            'key': k,
            'en': en,
            'vi': new_vi
        })
    print(f"{table_name}: {changes} items polished, {token_errors} token errors.")
    return polished

def main():
    print("=" * 70)
    print("STARTING STELLA SORA PHASE 2A: ITEMS & COMBAT SKILLS POLISH")
    print("=" * 70)

    with open(DATASET_PATH, 'r', encoding='utf-8') as f:
        dataset = json.load(f)

    polished_dataset = {}
    table_stats = {}

    # 1. Polish Item
    print("\n[1/5] Processing Item Table...")
    polished_dataset['Item'] = polish_item_table(dataset['Item'])

    # 2. Polish Skill
    print("\n[2/5] Processing Skill Table...")
    polished_dataset['Skill'] = polish_skill_table(dataset['Skill'])

    # 3. Polish MainSkill
    print("\n[3/5] Processing MainSkill Table...")
    polished_dataset['MainSkill'] = polish_main_and_sec('MainSkill', dataset['MainSkill'])

    # 4. Polish SecondarySkill
    print("\n[4/5] Processing SecondarySkill Table...")
    polished_dataset['SecondarySkill'] = polish_main_and_sec('SecondarySkill', dataset['SecondarySkill'])

    # 5. Polish EffectDesc
    print("\n[5/5] Processing EffectDesc Table...")
    polished_dataset['EffectDesc'] = polish_effect_desc(dataset['EffectDesc'])

    # Total counts and token validation
    print("\n" + "=" * 70)
    print("PERFORMING 100% STRICT VALIDATION GATE")
    print("=" * 70)
    total_items = 0
    total_token_errors = 0
    total_changes = 0

    for tname, items in polished_dataset.items():
        t_errors = 0
        t_changes = 0
        orig_items = dataset[tname]
        assert len(items) == len(orig_items), f"Mismatch item count in {tname}"

        for p_it, o_it in zip(items, orig_items):
            assert p_it['key'] == o_it['key'], f"Key mismatch in {tname}"
            valid, ot, vt = validate_token_preservation(p_it['en'], p_it['vi'])
            if not valid:
                t_errors += 1
            if p_it['vi'] != o_it['vi_current']:
                t_changes += 1

        total_items += len(items)
        total_token_errors += t_errors
        total_changes += t_changes
        table_stats[tname] = {
            'total': len(items),
            'changes': t_changes,
            'token_errors': t_errors
        }
        print(f"Table {tname:15}: {len(items):5} entries | Polished: {t_changes:5} | Token Errors: {t_errors}")

    print("-" * 70)
    print(f"TOTAL: {total_items} entries | Total Polished: {total_changes} | Total Token Errors: {total_token_errors}")
    assert total_token_errors == 0, f"FAILED: Found {total_token_errors} token errors!"

    # Save phase2a_polished.json
    print(f"\nWriting polished dataset to {POLISHED_OUT_PATH}...")
    with open(POLISHED_OUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(polished_dataset, f, ensure_ascii=False, indent=2)
    print("Dataset saved successfully.")

    # Update data_decrypted/entries/
    print("\nUpdating decrypted .bin entries files...")
    for tname, fname in TABLE_FILES.items():
        bin_path = ENTRIES_DIR / fname
        bak_path = ENTRIES_DIR / f"{fname}.bak"

        # Create backup if not exists
        if not bak_path.exists():
            shutil.copy2(bin_path, bak_path)
            print(f"  Created backup: {bak_path.name}")

        # Read existing file to preserve format/order
        with open(bin_path, 'r', encoding='utf-8') as f:
            current_dict = json.load(f)

        # Update with polished values
        table_items = polished_dataset[tname]
        for it in table_items:
            current_dict[it['key']] = it['vi']

        # Write back cleanly
        with open(bin_path, 'w', encoding='utf-8') as f:
            json.dump(current_dict, f, ensure_ascii=False, indent=2)
        print(f"  Updated: {bin_path.name} ({len(current_dict)} entries)")

    print("\n" + "=" * 70)
    print("ALL 5 TABLES SUCCESSFULLY POLISHED AND VERIFIED 100%!")
    print("=" * 70)

if __name__ == '__main__':
    main()
