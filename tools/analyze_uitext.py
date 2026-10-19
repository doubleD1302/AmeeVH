import json
from collections import Counter

en = json.load(open('work/research/data_decrypted/entries/00704_0x87cc29ac0defc2d9.bin', encoding='utf-8'))
cn = json.load(open('work/research/data_decrypted/entries/00925_0x363690c09b175230.bin', encoding='utf-8'))

vals = Counter(v.strip() for v in en.values() if len(v.strip()) < 30)
print(f'Total unique short values: {len(vals)}')
print('Top 40 most frequent short values:')
for val, count in vals.most_common(40):
    sample_cn = next((cn[k] for k, v in en.items() if v.strip() == val), '')
    print(f'  {count:3d}x : {repr(val):25s} | CN: {sample_cn}')
