#!/usr/bin/env python3
"""Merge translated disc batches into 00553_0x1f924138769d46ec.bin."""

import json
from pathlib import Path

def main():
    root = Path(__file__).parent.parent
    entries_dir = root / 'work' / 'research' / 'data_decrypted' / 'entries'
    disc_ip_file = entries_dir / '00553_0x1f924138769d46ec.bin'
    orig_ip_file = root / 'work' / 'research' / 'data_en_original' / '00553_0x1f924138769d46ec.bin'

    if not disc_ip_file.exists():
        print("Error: 00553_0x1f924138769d46ec.bin not found!")
        return

    curr_data = json.load(open(disc_ip_file, 'r', encoding='utf-8'))
    orig_data = json.load(open(orig_ip_file, 'r', encoding='utf-8')) if orig_ip_file.exists() else {}

    merged_count = 0
    for b_idx in range(1, 5):
        batch_file = root / 'work' / 'research' / f'disc_batch_{b_idx}_vi.json'
        if not batch_file.exists():
            print(f"Warning: Batch {b_idx} file not found yet ({batch_file.name})")
            continue
        try:
            batch_data = json.load(open(batch_file, 'r', encoding='utf-8'))
        except Exception as e:
            print(f"Error reading Batch {b_idx}: {e}")
            continue

        for k, v in batch_data.items():
            if isinstance(v, str) and v.strip():
                curr_data[k] = v.strip()
                merged_count += 1
        print(f"✓ Merged Batch {b_idx}: {len(batch_data)} stories")

    with open(disc_ip_file, 'w', encoding='utf-8') as f:
        json.dump(curr_data, f, ensure_ascii=False, indent=2)

    total_keys = len(curr_data)
    untrans = sum(1 for k, v in curr_data.items() if orig_data and v == orig_data.get(k))
    print(f"\nTotal merged in this run: {merged_count}")
    print(f"00553 status: {total_keys - untrans}/{total_keys} translated ({(total_keys - untrans)*100/total_keys:.1f}%)")

if __name__ == '__main__':
    main()
