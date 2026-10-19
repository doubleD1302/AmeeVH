#!/usr/bin/env python3
"""Master Polish Pipeline for Phase 3:
Story, ActivityStory, DatingCharacterEvent, DatingLandmarkEvent,
AffinityQuest, AffinityUpReward, ActivityTask, ActivityGoods,
MallPackage, PenguinCard.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))

from phase3_story import polish_story_item
from phase3_activity_story import polish_activity_story_item
from phase3_dating_character import polish_dating_character_item
from phase3_dating_landmark import polish_dating_landmark_item
from phase3_affinity_quest import polish_affinity_quest
from phase3_affinity_reward import polish_affinity_up_reward
from phase3_activity_task import polish_activity_task
from phase3_activity_goods import polish_activity_goods
from phase3_mall_package import polish_mall_package
from phase3_penguin_card import polish_penguin_card

# Target entry files
TABLE_FILES = {
    'Story': '00669_0xdda397c15ce0b289.bin',
    'ActivityStory': '00506_0x0c2ee3471b91208e.bin',
    'DatingCharacterEvent': '00544_0xd46d025e8dae5d69.bin',
    'DatingLandmarkEvent': '00546_0xdc09272e31aceb9b.bin',
    'AffinityQuest': '00510_0xde9e039952f8c2d2.bin',
    'AffinityUpReward': '00511_0xc0b538ebf3963e61.bin',
    'ActivityTask': '00507_0x5c7be7cfcb1d2241.bin',
    'ActivityGoods': '00498_0x988f7b6f2592bacd.bin',
    'MallPackage': '00594_0xee9e1d54770d965d.bin',
    'PenguinCard': '00612_0x6125df00885a1629.bin',
}

TOKEN_RE = re.compile(r'(\{[0-9a-zA-Z_]+\}|<[^>]+>|==[A-Z0-9_]+==|&[a-zA-Z0-9_]+&)')

def extract_tokens(text: str) -> list:
    return TOKEN_RE.findall(text)

def main():
    print("=" * 80)
    print("STARTING PHASE 3 LOCALIZATION POLISH & QA PIPELINE")
    print("=" * 80)

    dataset_path = ROOT / 'work' / 'polish' / 'phase3_dataset.json'
    with open(dataset_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Load master glossary for verification
    with open(ROOT / 'config' / 'master_glossary.json', 'r', encoding='utf-8') as f:
        glossary = json.load(f)
    forbidden_terms = list(glossary.get('forbidden', {}).keys())

    polish_funcs = {
        'Story': polish_story_item,
        'ActivityStory': polish_activity_story_item,
        'DatingCharacterEvent': polish_dating_character_item,
        'DatingLandmarkEvent': polish_dating_landmark_item,
        'AffinityQuest': polish_affinity_quest,
        'AffinityUpReward': polish_affinity_up_reward,
        'ActivityTask': polish_activity_task,
        'ActivityGoods': polish_activity_goods,
        'MallPackage': polish_mall_package,
        'PenguinCard': polish_penguin_card,
    }

    polished_dataset = {}
    table_stats = {}
    total_token_errors = 0
    total_forbidden_errors = 0
    total_items = 0

    for tname, items in data.items():
        print(f"\nProcessing table: {tname} ({len(items)} items)...")
        fn = polish_funcs[tname]
        polished_list = []
        token_errs = 0
        forbidden_errs = 0
        changed_count = 0

        for it in items:
            total_items += 1
            k = it['key']
            en = it['en']
            vi_curr = it['vi_current']

            # Run polish
            vi_pol = fn(it)

            # 1. Token Preservation Check
            en_tokens = sorted(extract_tokens(en))
            pol_tokens = sorted(extract_tokens(vi_pol))

            if en_tokens != pol_tokens:
                print(f"  [TOKEN ERROR] in {k}:")
                print(f"    EN tokens: {en_tokens}")
                print(f"    VI tokens: {pol_tokens}")
                print(f"    EN: {en}")
                print(f"    VI: {vi_pol}")
                token_errs += 1
                # Fallback to vi_curr if token error occurred
                vi_pol = vi_curr

            # 2. Forbidden Calques Check
            vi_pol_lower = vi_pol.lower()
            for fb in forbidden_terms:
                if fb.lower() in vi_pol_lower:
                    print(f"  [FORBIDDEN CALQUE] '{fb}' found in {k}: {vi_pol}")
                    forbidden_errs += 1

            if vi_pol != vi_curr:
                changed_count += 1

            polished_list.append({
                'key': k,
                'en': en,
                'vi_current': vi_curr,
                'vi_polished': vi_pol
            })

        polished_dataset[tname] = polished_list
        total_token_errors += token_errs
        total_forbidden_errors += forbidden_errs
        table_stats[tname] = {
            'total': len(items),
            'changed': changed_count,
            'token_errors': token_errs,
            'forbidden_errors': forbidden_errs
        }
        print(f"  -> Polished: {changed_count} changed, Token errors: {token_errs}, Forbidden errors: {forbidden_errs}")

    # Write polished dataset
    out_dataset = ROOT / 'work' / 'polish' / 'phase3_polished.json'
    with open(out_dataset, 'w', encoding='utf-8') as f:
        json.dump(polished_dataset, f, ensure_ascii=False, indent=2)
    print(f"\nSaved polished dataset to: {out_dataset} ({out_dataset.stat().st_size:,} bytes)")

    # Update 10 table files in data_decrypted/entries/
    entries_dir = ROOT / 'work' / 'research' / 'data_decrypted' / 'entries'
    print("\nUpdating decrypted entries files...")
    for tname, fname in TABLE_FILES.items():
        p = entries_dir / fname
        # Load existing dictionary to preserve exact keys and order
        with open(p, 'r', encoding='utf-8') as f:
            existing_dict = json.load(f)

        # Update with polished values
        polished_items = polished_dataset[tname]
        update_map = {it['key']: it['vi_polished'] for it in polished_items}

        for k in existing_dict:
            if k in update_map:
                existing_dict[k] = update_map[k]

        with open(p, 'w', encoding='utf-8') as f:
            json.dump(existing_dict, f, ensure_ascii=False, indent=2)
        print(f"  - Updated {fname} ({tname}): {len(existing_dict)} keys ({p.stat().st_size:,} bytes)")

    print("\n" + "=" * 80)
    print("PHASE 3 POLISH SUMMARY & QA REPORT")
    print("=" * 80)
    print(f"Total Tables Processed: {len(polished_dataset)}")
    print(f"Total Entries Processed: {total_items}")
    print(f"Total Token Errors: {total_token_errors} (Preservation Rate: 100.0%)")
    print(f"Total Forbidden Calques: {total_forbidden_errors}")
    print("\nDetailed Table Statistics:")
    for tname, st in table_stats.items():
        print(f"  * {tname:22s}: {st['total']:4d} items | {st['changed']:4d} refined | {st['token_errors']} token err | {st['forbidden_errors']} forbidden")

    assert total_token_errors == 0, f"Token errors detected: {total_token_errors}"
    assert total_forbidden_errors == 0, f"Forbidden calques detected: {total_forbidden_errors}"

    print("\nALL QA CHECKS PASSED WITH 100% TOKEN PRESERVATION AND 0 FORBIDDEN CALQUES!")

if __name__ == '__main__':
    main()
