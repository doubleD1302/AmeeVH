#!/usr/bin/env python3
import json

for fname in ['unique_mainskill.json', 'unique_secskill.json']:
    with open('StellaSora_VietHoa/work/polish/' + fname, 'r', encoding='utf-8') as f:
        items = json.load(f)
    names = [it for it in items if not it['key'].endswith('.2')]
    print(f"=== {fname}: {len(names)} names ===")
    for it in names[:15]:
        print(f"  EN: {it['en']} | CN: {it['cn']} | VI: {it['vi_current']}")
