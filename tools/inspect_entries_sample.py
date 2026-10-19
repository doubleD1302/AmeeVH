#!/usr/bin/env python3
"""Inspect target decrypted entries format and content."""
import json
from pathlib import Path

def main():
    root = Path(__file__).resolve().parent.parent
    entries_dir = root / "work" / "research" / "data_decrypted" / "entries"
    
    test_files = [
        "00528_0xd8b61831cfe58bf2.bin", # CharacterArchiveVoice
        "00501_0x3ba5283f46becc56.bin", # ActivityLevelsLevel
        "00605_0x6509b9fe31bc8029.bin", # MonsterManual
        "00623_0x8dc130b6f79ff422.bin", # Plot
        "00536_0x8dcf06b298f46b28.bin", # CharGetLines
        "00557_0x79d5a3cef377df0c.bin", # ErrorCode
    ]
    
    for fname in test_files:
        fpath = entries_dir / fname
        if not fpath.exists():
            print(f"File NOT found: {fname}")
            continue
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            print(f"File {fname}: type={type(data)}, length={len(data)}")
            # print sample
            if isinstance(data, dict):
                sample_keys = list(data.keys())[:3]
                print(f"  Sample keys: {sample_keys}")
                for k in sample_keys:
                    val = str(data[k])[:80].replace('\n', ' ')
                    print(f"    {k} -> {val}")
            elif isinstance(data, list):
                print(f"  Sample item: {str(data[0])[:120]}")
        except Exception as e:
            print(f"Error reading {fname}: {e}")

if __name__ == "__main__":
    main()
