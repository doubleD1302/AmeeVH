import json
from pathlib import Path

entries_dir = Path('work/research/data_decrypted/entries')
tables = [
    '00591_0x57e760255c1d3b2d.bin',
    '00635_0x31a8814a91313129.bin',
    '00624_0x02ce11eca01b5fc8.bin',
    '00680_0x3f0bd5f8db2389b6.bin',
    '00560_0x788d8a3db60dd08a.bin'
]

print("=== 'điểm \"' occurrences ===")
for st in tables:
    f = entries_dir / st
    if not f.exists(): continue
    d = json.load(open(f, encoding='utf-8'))
    for k, v in d.items():
        if isinstance(v, str) and 'điểm "' in v:
            print(f"[{st} : {k}]\n  {v}\n")

print("=== 'với \"' occurrences ===")
for st in tables:
    f = entries_dir / st
    if not f.exists(): continue
    d = json.load(open(f, encoding='utf-8'))
    for k, v in d.items():
        if isinstance(v, str) and 'với "' in v:
            print(f"[{st} : {k}]\n  {v}\n")
