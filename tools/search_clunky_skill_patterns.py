import json
import re
from pathlib import Path

entries = Path('work/research/data_decrypted/entries')
orig_dir = Path('work/research/data_en_original/entries')

patterns = [
    'gánh chịu',
    'sát thương nhận',
    'nhận bởi',
    'gây sát thương sau cho mục tiêu',
    'gây ra những điều sau đây',
    'mọi điểm',
    'điểm "',
    'với "',
    'bởi <color'
]

tables = [
    '00591_0x57e760255c1d3b2d.bin',
    '00635_0x31a8814a91313129.bin',
    '00624_0x02ce11eca01b5fc8.bin',
    '00680_0x3f0bd5f8db2389b6.bin',
    '00560_0x788d8a3db60dd08a.bin'
]

matches = []
for t in tables:
    f = entries / t
    if not f.exists(): continue
    d = json.load(open(f, encoding='utf-8'))
    orig_f = orig_dir / t
    orig = json.load(open(orig_f, encoding='utf-8')) if orig_f.exists() else {}

    for k, v in d.items():
        if isinstance(v, str):
            for pat in patterns:
                if pat in v:
                    matches.append((t, k, pat, v, orig.get(k, '')))
                    break

print(f"Total matches found: {len(matches)}")
for t, k, pat, vi, en in matches[:15]:
    print(f"[{t} : {k}] (pat: {pat})")
    print(f"  EN: {en}")
    print(f"  VI: {vi}\n")
