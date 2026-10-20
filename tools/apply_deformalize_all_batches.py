# -*- coding: utf-8 -*-
"""
Phase 1: De-formalize all 4 existing approved batches (40,000 strings).
Eliminates stiff Sino-Vietnamese, courtly archaic terms, and mechanical calques.
Logs every change for audit.
"""

import json
from pathlib import Path
import sys

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
sys.path.insert(0, str(ROOT / "tools"))
from deformalize_text import deformalize_text

BATCH_FILES = [
    "batch_10k_approved.json",
    "batch_10k_b2_approved.json",
    "batch_10k_b3_approved.json",
    "batch_10k_b4_approved.json",
]

def main():
    total_reviewed = 0
    total_changed = 0
    all_changes_log = []

    for bname in BATCH_FILES:
        bpath = ROOT / "work" / "batches" / bname
        if not bpath.exists():
            print(f"File not found: {bname}")
            continue

        data = json.load(open(bpath, "r", encoding="utf-8"))
        changed_in_file = 0

        for key, text in data.items():
            total_reviewed += 1
            new_text = deformalize_text(text)
            if new_text != text:
                changed_in_file += 1
                total_changed += 1
                all_changes_log.append({
                    "batch": bname,
                    "key": key,
                    "before": text,
                    "after": new_text
                })
                data[key] = new_text

        # Save de-formalized batch
        with open(bpath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"[{bname}] Reviewed {len(data)} items, de-formalized {changed_in_file} lines.")

    # Save log of changes
    log_path = ROOT / "work" / "batches" / "deformalize_changes_log.json"
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(all_changes_log, f, indent=2, ensure_ascii=False)

    print(f"\nPhase 1 COMPLETE: Total reviewed: {total_reviewed}, Total de-formalized: {total_changed}")
    print(f"Log saved to: {log_path}")

if __name__ == "__main__":
    main()
