# -*- coding: utf-8 -*-
import json
from pathlib import Path

ROOT = Path("StellaSora_VietHoa")

batches = [
    'batch_10000_avg_clean.json', 'batch_10000_avg_clean_b2.json',
    'batch_10000_avg_clean_b3.json', 'batch_10000_avg_clean_b4.json'
]
appr_batches = [
    'batch_10k_approved.json', 'batch_10k_b2_approved.json',
    'batch_10k_b3_approved.json', 'batch_10k_b4_approved.json'
]

master_dict = {}
for en_f, vi_f in zip(batches, appr_batches):
    en_d = json.load(open(ROOT / 'work' / 'batches' / en_f, encoding='utf-8'))
    vi_d = json.load(open(ROOT / 'work' / 'batches' / vi_f, encoding='utf-8'))
    for k, en in en_d.items():
        if k in vi_d:
            master_dict[en.strip()] = vi_d[k].strip()

rem_cache = ROOT / 'work' / 'batches' / 'remaining_lua_avg_cache.json'
if rem_cache.exists():
    rem_d = json.load(open(rem_cache, encoding='utf-8'))
    master_dict.update({k.strip(): v.strip() for k, v in rem_d.items()})

test_keys = [
    'What a shame.',
    'That was a joke.',
    'Is that so?',
    'You are such a rare and precious specimen—if I don\'t do some research on you...',
    'I will regret it for the rest of my life~',
    'Alright then, I\'ll be looking forward to the day you visit my clinic of your own volition~',
    'This is the way to reach me',
    'This is my contact info.'
]

for k in test_keys:
    print(f'"{k}" -> "{master_dict.get(k)}"')
