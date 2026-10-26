# -*- coding: utf-8 -*-
import json
import re

with open('StellaSora_VietHoa/work/batches/BATCH_FIX_04_STORY_SHORT_LINES.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

entries = data['entries']

# Check for banned phrases
banned = [
    'đó là lý do tại sao',
    'đó là lí do tại sao',
    'nắm ống hút',
    'cái xấu của tôi',
    'đọc phòng',
    'hình vuông',
    'hòa cô ấy',
    'ruột tôi hét lên'
]

banned_found = []
for idx, e in enumerate(entries):
    vi = e.get('text_vi', '').lower()
    for b in banned:
        if b in vi:
            banned_found.append((idx, e.get('id'), b, e.get('text_vi')))

print(f"Banned phrases check: {len(banned_found)} issues found.")
for b in banned_found:
    print(" ", b)
