import json

data = json.load(open('StellaSora_VietHoa/work/batches/dialogue_batch6_awakening_talk.json', encoding='utf-8'))
newlines = [it for it in data if '\n' in it.get('en', '') or '\n' in it.get('zh', '')]
print(f"Items with newlines: {len(newlines)}")
for it in newlines:
    print(f"[{it['key']}] EN: {repr(it.get('en'))}")
