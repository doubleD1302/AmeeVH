#!/usr/bin/env python3
"""
Merge all approved pillars into decrypted table entries.
Prepares tables for ARCX repacking.
"""

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENTRIES_DIR = ROOT / "work" / "research" / "data_decrypted" / "entries"

APPROVED_FILES = [
    ROOT / "work" / "batches" / "pillar1_approved.json",
    ROOT / "work" / "batches" / "pillar2_approved.json",
    ROOT / "work" / "batches" / "pillar3_approved.json",
    ROOT / "work" / "batches" / "pillar4_approved.json"
]

def main():
    print("=" * 70)
    print("Merging Approved Pillars into Data Decrypted Entries")
    print("=" * 70)

    total_merged_strings = 0
    total_merged_tables = 0

    for app_path in APPROVED_FILES:
        if not app_path.exists():
            print(f"File not found: {app_path.name}")
            continue

        with open(app_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        print(f"\nProcessing {app_path.name}: {len(data)} tables")
        for tbl_name, tbl_info in data.items():
            fname = tbl_info.get("file")
            entries = tbl_info.get("entries", {})
            if not fname or not entries:
                continue

            target_entry_file = ENTRIES_DIR / fname
            if not target_entry_file.exists():
                print(f"Warning: target entry file {fname} not found!")
                continue

            # Load existing
            with open(target_entry_file, "r", encoding="utf-8") as f:
                target_data = json.load(f)

            # Update entries
            updated_count = 0
            for k, v in entries.items():
                target_data[k] = v
                updated_count += 1

            # Save back
            with open(target_entry_file, "w", encoding="utf-8") as f:
                json.dump(target_data, f, ensure_ascii=False, indent=2)

            total_merged_tables += 1
            total_merged_strings += updated_count

    print("\n" + "=" * 70)
    print(f"Merge Complete! Total merged: {total_merged_strings} strings across {total_merged_tables} tables.")
    print("=" * 70)

if __name__ == "__main__":
    main()
