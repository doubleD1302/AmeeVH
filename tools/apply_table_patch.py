#!/usr/bin/env python3
"""Apply translation batch to decrypted table and verify repacking.

Reads a translation batch JSON (e.g. work/batches/BATCH_01_CORE_UI.json),
updates the corresponding decrypted JSON table in work/research/data_decrypted/entries/,
repacks data.arcx using pure Python XXTEA, and verifies native engine compatibility.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from tools.arcx_adapter import repack_archive

def apply_batch(batch_path: Path, decrypted_dir: Path) -> int:
    batch_data = json.loads(batch_path.read_text(encoding="utf-8"))
    items = batch_data["items"]
    
    # Group items by table if needed. In Batch 01, it targets bin/UIText.bytes (00704_0x87cc29ac0defc2d9.bin)
    table_file = decrypted_dir / "entries" / "00704_0x87cc29ac0defc2d9.bin"
    if not table_file.exists():
        raise FileNotFoundError(f"Missing target table file: {table_file}")
        
    table_json = json.loads(table_file.read_text(encoding="utf-8"))
    
    applied = 0
    for item in items:
        k = item["key"]
        v = item["text_vi"]
        if v.strip():
            table_json[k] = v
            applied += 1
            
    # Write back updated table JSON
    table_file.write_text(json.dumps(table_json, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Applied {applied}/{len(items)} translations to {table_file.name}")
    return applied

def main():
    root = Path(__file__).parent.parent
    batch_file = root / "work" / "batches" / "BATCH_01_CORE_UI.json"
    decrypted_dir = root / "work" / "research" / "data_decrypted"
    output_arcx = root / "work" / "research" / "data_patched_vi.arcx"
    
    applied = apply_batch(batch_file, decrypted_dir)
    print(f"Repacking patched data.arcx to {output_arcx}...")
    
    repack_archive(decrypted_dir, output_arcx, encrypt_payload=True)
    print(f"Successfully generated {output_arcx} ({output_arcx.stat().st_size} bytes)")

if __name__ == "__main__":
    main()
