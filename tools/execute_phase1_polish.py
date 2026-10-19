#!/usr/bin/env python3
"""Master Execution Script for Phase 1 Localization Polish.
Processes 6,535 items across 5 core tables:
1. UIText (4,151 items)
2. Word (340 items)
3. DictionaryDiagram (430 items)
4. MailTemplate (300 items)
5. Achievement (1,314 items)

Outputs:
- work/polish/phase1_polished.json
- Directly updates work/research/data_decrypted/entries/*.bin
- Verifies 0 forbidden calques and 100% token preservation.
"""

import json
from pathlib import Path

from token_validator import extract_tokens
from polish_word import polish_word_entries
from polish_dict import polish_dict_entries
from polish_mail import polish_mail_entries
from polish_ach import polish_ach_entries
from polish_uitext import polish_uitext_entries

def main():
    root = Path(__file__).parent.parent
    ds_path = root / 'work' / 'polish' / 'phase1_dataset.json'
    glossary_path = root / 'config' / 'master_glossary.json'
    decrypted_dir = root / 'work' / 'research' / 'data_decrypted' / 'entries'
    out_dir = root / 'work' / 'polish'

    print("=" * 70)
    print("STELLA SORA - PHASE 1 LOCALIZATION POLISH EXECUTION")
    print("=" * 70)

    # 1. Load Dataset
    print(f"\n[1/6] Loading Phase 1 dataset from {ds_path}...")
    with open(ds_path, 'r', encoding='utf-8') as f:
        dataset = json.load(f)

    # 2. Load Master Glossary
    print(f"[2/6] Loading Master Glossary from {glossary_path}...")
    with open(glossary_path, 'r', encoding='utf-8') as f:
        glossary = json.load(f)
    forbidden_terms = glossary.get('forbidden', {})

    # 3. Polish all 5 tables
    print(f"\n[3/6] Polishing tables with Senior Localization QA standards...")
    polished_dataset = {}

    print("  -> Polishing Word (340 items)...")
    polished_dataset['Word'] = polish_word_entries(dataset['Word'])

    print("  -> Polishing DictionaryDiagram (430 items)...")
    polished_dataset['DictionaryDiagram'] = polish_dict_entries(dataset['DictionaryDiagram'])

    print("  -> Polishing MailTemplate (300 items)...")
    polished_dataset['MailTemplate'] = polish_mail_entries(dataset['MailTemplate'])

    print("  -> Polishing Achievement (1,314 items)...")
    polished_dataset['Achievement'] = polish_ach_entries(dataset['Achievement'])

    print("  -> Polishing UIText (4,151 items)...")
    polished_dataset['UIText'] = polish_uitext_entries(dataset['UIText'])

    # 4. Rigorous QA Validation
    print(f"\n[4/6] Running Rigorous QA Checks (Forbidden Calques & Token Preservation)...")
    total_items = 0
    total_token_mismatches = 0
    forbidden_matches = {term: [] for term in forbidden_terms.keys()}
    extra_forbidden = ['bút def', 'mất khả năng lao động', 'sao nhổ', 'lao động', 'spd chuyển động']

    for tbl_name, items in dataset.items():
        pol_dict = polished_dataset[tbl_name]
        for it in items:
            total_items += 1
            k = it['key']
            en = it['en']
            vi = pol_dict[k]

            # Token check
            et = extract_tokens(en)
            vt = extract_tokens(vi)
            if et != vt:
                total_token_mismatches += 1
                print(f"  [ERROR] Token mismatch at [{tbl_name}][{k}]:")
                print(f"     EN Tokens: {et}")
                print(f"     VI Tokens: {vt}")

            # Forbidden calques check
            vi_lower = vi.lower()
            for fb in list(forbidden_terms.keys()) + extra_forbidden:
                if fb.lower() in vi_lower:
                    if fb not in forbidden_matches:
                        forbidden_matches[fb] = []
                    forbidden_matches[fb].append((tbl_name, k, vi))

    print(f"  - Total items processed: {total_items}")
    print(f"  - Token mismatches: {total_token_mismatches}")
    has_forbidden = False
    for fb, occurrences in forbidden_matches.items():
        if occurrences:
            has_forbidden = True
            print(f"  - [WARNING] Forbidden phrase '{fb}' found in {len(occurrences)} items:")
            for tbl, k, text in occurrences[:2]:
                print(f"      [{tbl}][{k}]: {text}")

    if total_token_mismatches == 0 and not has_forbidden:
        print("  -> [PASS] 100% Token Preservation & 0 Forbidden Calques Verified!")
    else:
        print("  -> [FAIL] Issues found, please review.")

    # 5. Save Polished Dataset
    out_file = out_dir / 'phase1_polished.json'
    print(f"\n[5/6] Saving polished dataset to {out_file}...")
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(polished_dataset, f, ensure_ascii=False, indent=2)
    print(f"  -> Successfully saved {total_items} polished entries.")

    # 6. Apply directly to decrypted entries .bin files
    print(f"\n[6/6] Applying polished text to data_decrypted/entries/...")
    target_files = {
        'UIText': '00704_0x87cc29ac0defc2d9.bin',
        'Word': '00713_0x78b1aa32bbcf433e.bin',
        'DictionaryDiagram': '00549_0x88d705ae9564e65e.bin',
        'MailTemplate': '00589_0x2aa9f7b7887bdb4d.bin',
        'Achievement': '00494_0x5b0fc2f5fe45a572.bin'
    }

    for tbl_name, fname in target_files.items():
        bin_path = decrypted_dir / fname
        with open(bin_path, 'r', encoding='utf-8') as f:
            bin_data = json.load(f)

        pol_dict = polished_dataset[tbl_name]
        updated_count = 0
        for k, vi in pol_dict.items():
            if k in bin_data:
                bin_data[k] = vi
                updated_count += 1

        with open(bin_path, 'w', encoding='utf-8') as f:
            json.dump(bin_data, f, ensure_ascii=False, indent=2)

        print(f"  -> Updated {fname} ({tbl_name}): {updated_count}/{len(bin_data)} entries written.")

    print("\n" + "=" * 70)
    print("PHASE 1 POLISH COMPLETED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == '__main__':
    main()
