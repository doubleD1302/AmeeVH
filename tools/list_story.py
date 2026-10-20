import json

data = json.load(open('StellaSora_VietHoa/work/batches/dialogue_batch6_awakening_talk.json', encoding='utf-8'))
story_items = [d for d in data if d['table'] == 'Story']

print(f"Total Story items: {len(story_items)}")
for i, it in enumerate(story_items):
    print(f"{i+1:2d}. [{it['key']}]")
    print(f"    EN: {it['en']}")
    print(f"    ZH: {it.get('zh', '')}")
    print(f"    VI: {it.get('current_vi', '')}")
