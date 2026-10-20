import json

data = json.load(open('StellaSora_VietHoa/work/batches/dialogue_batch6_awakening_talk.json', encoding='utf-8'))
print(f'Total items: {len(data)}')

by_table = {}
for i, d in enumerate(data):
    by_table.setdefault(d['table'], []).append((i, d))

for t, items in by_table.items():
    print(f'\n=== Table: {t} ({len(items)} items) ===')
    for idx, it in items[:6]:
        print(f"[{it['key']}]\n  EN: {it['en']}\n  ZH: {it.get('zh', '')}\n  VI: {it.get('current_vi', '')}")
