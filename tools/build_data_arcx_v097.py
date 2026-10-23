#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build and Repack data_patched_vi.arcx for Client v0.9.7.
Applies all 2,670 Data table lines:
- Campaign 1 (Story Dating & StarTower tables): 1,008 lines
- Campaign 3 (Character Archives & Lore tables): 1,662 lines
Repacks into dist/data_patched_vi.arcx with XXTEA encrypted payload.
"""

import json
from pathlib import Path
import sys
import time

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
sys.path.insert(0, str(ROOT / "tools"))

from arcx_adapter import repack_archive, ArcxArchive

ENTRIES_DIR = ROOT / "work" / "research" / "data_200_decrypted" / "entries"
DEC_DIR = ROOT / "work" / "research" / "data_200_decrypted"
OUTPUT_ARCX = ROOT / "dist" / "data_patched_vi.arcx"

TABLE_FILES = {
    "AffinityQuest": "00823_0x1e77dcffbbba3b93.bin",
    "CharGetLines": "00850_0x17ba1c051ea16c44.bin",
    "CharacterArchiveContent": "00840_0x4a3c44844ee817d1.bin",
    "CharacterArchiveVoice": "00841_0x65c021091de910ba.bin",
    "DatingCharacterEvent": "00858_0x733ee8fdb8a6a976.bin",
    "DatingLandmarkEvent": "00860_0x43ac532f7df5c82a.bin",
    "Plot": "00950_0xc694fcb01ad6b937.bin",
    "StarTowerTalk": "00998_0x43be878a1ea77cbe.bin",
    "Story": "00999_0x939d4390e6e6b8fd.bin"
}

def main():
    print("=== STARTING DATA TABLES REPACK FOR v0.9.7 ===")
    
    # 1. Load proposals
    p1 = ROOT / "work/editorial/lightnovel_editorial_20261024_r02/UNIFIED_STORY_PROPOSALS.jsonl"
    p3 = ROOT / "work/editorial/character_archives_editorial_20261024_r01/UNIFIED_ARCHIVES_PROPOSALS.jsonl"
    
    lines_c1 = [json.loads(l) for l in p1.read_text(encoding="utf-8").splitlines() if l.strip()]
    lines_c3 = [json.loads(l) for l in p3.read_text(encoding="utf-8").splitlines() if l.strip()]
    
    print(f"Loaded Campaign 1: {len(lines_c1)} lines")
    print(f"Loaded Campaign 3: {len(lines_c3)} lines")
    
    # Load table json caches
    loaded_tables = {}
    for tbl, fname in TABLE_FILES.items():
        fpath = ENTRIES_DIR / fname
        if not fpath.exists():
            raise FileNotFoundError(f"Missing table entry file: {fpath}")
        loaded_tables[tbl] = json.loads(fpath.read_text(encoding="utf-8"))
        
    updated_counts = {tbl: 0 for tbl in TABLE_FILES}
    
    # Apply Campaign 1 table lines
    for it in lines_c1:
        sid = it.get("id") or ""
        tbl = sid.split(".")[0] if "." in sid else ""
        if tbl in loaded_tables:
            vi = it.get("vi")
            if vi and sid in loaded_tables[tbl]:
                loaded_tables[tbl][sid] = vi
                updated_counts[tbl] += 1
                
    # Apply Campaign 3 table lines
    for it in lines_c3:
        sid = it.get("id") or ""
        tbl = sid.split(".")[0] if "." in sid else ""
        if tbl in loaded_tables:
            vi = it.get("vi_editorial")
            if vi and sid in loaded_tables[tbl]:
                loaded_tables[tbl][sid] = vi
                updated_counts[tbl] += 1
                
    total_updated = sum(updated_counts.values())
    print("\nUpdated entries per table:")
    for tbl, count in sorted(updated_counts.items()):
        print(f"  {tbl}: {count} keys updated")
    print(f"Total keys updated: {total_updated} / 2670")
    assert total_updated == 2670, f"Expected 2670 updated keys, got {total_updated}!"
    
    # Write back to entries directory
    print("\nWriting updated table JSONs back to entries...")
    for tbl, fname in TABLE_FILES.items():
        fpath = ENTRIES_DIR / fname
        fpath.write_text(json.dumps(loaded_tables[tbl], indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  Wrote {fpath.name} ({fpath.stat().st_size:,} bytes)")
        
    # Repack archive
    OUTPUT_ARCX.parent.mkdir(parents=True, exist_ok=True)
    print(f"\nRepacking {DEC_DIR} into {OUTPUT_ARCX}...")
    t0 = time.time()
    repack_archive(DEC_DIR, OUTPUT_ARCX, encrypt_payload=True)
    elapsed = time.time() - t0
    
    arc = ArcxArchive(OUTPUT_ARCX)
    print(f"SUCCESS! Created {OUTPUT_ARCX} in {elapsed:.2f}s:")
    print(f"  Size: {OUTPUT_ARCX.stat().st_size:,} bytes")
    print(f"  Entries: {len(arc.entries)}")

if __name__ == "__main__":
    main()
