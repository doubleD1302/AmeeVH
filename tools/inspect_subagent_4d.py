#!/usr/bin/env python3
import json
import re
from pathlib import Path

ROOT = Path(r"C:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
ENTRIES = ROOT / "work" / "research" / "data_decrypted" / "entries"

TABLES = [
    {
        "name": "ActivityTask",
        "en": "00507_0x5c7be7cfcb1d2241.bin",
        "cn": "00728_0xc316bcdb179b0d6e.bin",
    },
    {
        "name": "DatingCharacterEvent",
        "en": "00544_0xd46d025e8dae5d69.bin",
        "cn": "00765_0x733ee8fdb8a6a976.bin",
    },
    {
        "name": "Story",
        "en": "00669_0xdda397c15ce0b289.bin",
        "cn": "00890_0x939d4390e6e6b8fd.bin",
    },
    {
        "name": "ActivityStory",
        "en": "00506_0x0c2ee3471b91208e.bin",
        "cn": "00727_0x789e881d02a7ddcb.bin",
    },
    {
        "name": "AffinityQuest",
        "en": "00510_0xde9e039952f8c2d2.bin",
        "cn": "00731_0x1e77dcffbbba3b93.bin",
    },
    {
        "name": "DatingLandmarkEvent",
        "en": "00546_0xdc09272e31aceb9b.bin",
        "cn": "00767_0x43ac532f7df5c82a.bin",
    },
]

print("=== INSPECTING 4D TABLES ===")
all_en_unique_texts = set()
total_items = 0

for t in TABLES:
    en_file = ENTRIES / t["en"]
    cn_file = ENTRIES / t["cn"]
    
    if not en_file.exists():
        print(f"MISSING EN: {en_file}")
        continue
    if not cn_file.exists():
        print(f"MISSING CN: {cn_file}")
        continue
        
    en_data = json.loads(en_file.read_text(encoding="utf-8"))
    cn_data = json.loads(cn_file.read_text(encoding="utf-8"))
    
    print(f"\n[{t['name']}]")
    print(f"  EN entries: {len(en_data)} | CN entries: {len(cn_data)}")
    print(f"  Keys match: {set(en_data.keys()) == set(cn_data.keys())}")
    
    unique_texts = set(en_data.values())
    print(f"  Unique EN texts: {len(unique_texts)}")
    all_en_unique_texts.update(unique_texts)
    total_items += len(en_data)
    
    # Samples
    sample_keys = list(en_data.keys())[:3]
    for k in sample_keys:
        print(f"    Key {k}:")
        print(f"      EN: {repr(en_data[k])}")
        print(f"      CN: {repr(cn_data.get(k))}")

print(f"\nTotal items across 6 tables: {total_items}")
print(f"Total unique EN texts across 6 tables: {len(all_en_unique_texts)}")

# Check overlap with existing caches
batches_dir = ROOT / "work" / "batches"
known_caches = {}
for cf in batches_dir.glob("*cache*.json"):
    try:
        cdata = json.loads(cf.read_text(encoding="utf-8"))
        known_caches[cf.name] = cdata
        print(f"Loaded cache {cf.name}: {len(cdata)} entries")
    except Exception as e:
        pass

overlap_count = 0
for text in all_en_unique_texts:
    for cname, cdata in known_caches.items():
        if text in cdata:
            overlap_count += 1
            break

print(f"Unique EN texts already in existing caches: {overlap_count} / {len(all_en_unique_texts)}")

# Inspect tokens in all texts
token_patterns = [
    (r'\{[0-9a-zA-Z_]+\}', "format braces"),
    (r'<color=[^>]+>', "color tag"),
    (r'</color>', "close color"),
    (r'\x0b', "vtab"),
    (r'\n', "newline"),
    (r'&[a-zA-Z0-9_]+&', "amp param"),
    (r'##[^#]+#', "hash param"),
    (r'!NONEED!|!PENDING!', "special tags")
]

print("\nToken occurrences:")
for pat, desc in token_patterns:
    regex = re.compile(pat)
    matches = [txt for txt in all_en_unique_texts if regex.search(txt)]
    print(f"  {desc} ({pat}): {len(matches)} texts")
