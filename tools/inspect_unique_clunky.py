import json
from pathlib import Path

entries = Path('work/research/data_decrypted/entries')
orig_dir = Path('work/research/data_en_original/entries')

tables = [
    '00591_0x57e760255c1d3b2d.bin',
    '00635_0x31a8814a91313129.bin',
    '00624_0x02ce11eca01b5fc8.bin',
    '00680_0x3f0bd5f8db2389b6.bin',
    '00560_0x788d8a3db60dd08a.bin'
]

clunky_cases = []
for t in tables:
    d = json.load(open(entries / t, encoding='utf-8'))
    orig = json.load(open(orig_dir / t, encoding='utf-8'))
    for k, v in d.items():
        if not isinstance(v, str): continue
        en = orig.get(k, '')
        if ('điểm "' in v or 'với "' in v or 'sát thương mà hệ' in v 
            or 'gánh chịu từ các mục tiêu' in v or 'sát thương Tấn Công không tự động' in v 
            or 'sát thương nhận bởi' in v or 'mọi điểm' in v or 'gánh chịu' in v):
            clunky_cases.append((t, k, en, v))

print(f"Total clunky skill cases: {len(clunky_cases)}")
seen = set()
for t, k, en, vi in clunky_cases:
    # normalize key prefix to group identical skill levels
    prefix = k.rsplit('.', 1)[0]
    base_prefix = prefix[:-1] if prefix[-1].isdigit() else prefix
    if base_prefix not in seen:
        seen.add(base_prefix)
        print(f"[{t} : {k}]")
        print(f"  EN: {en}")
        print(f"  VI: {vi}\n")
