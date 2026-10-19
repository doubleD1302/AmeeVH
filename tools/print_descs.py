#!/usr/bin/env python3
import json
import sys

filename = sys.argv[1] if len(sys.argv) > 1 else 'unique_mainskill.json'
start = int(sys.argv[2]) if len(sys.argv) > 2 else 0
count = int(sys.argv[3]) if len(sys.argv) > 3 else 15

with open(f'StellaSora_VietHoa/work/polish/{filename}', 'r', encoding='utf-8') as f:
    items = json.load(f)

descs = [it for it in items if it['key'].endswith('.2')]
for i in range(start, min(start + count, len(descs))):
    it = descs[i]
    print(f"=== {i+1}/{len(descs)} [{it['key']}] ===")
    print("EN:", it['en'])
    print("CN:", it['cn'])
    print("VI:", it['vi_current'])
