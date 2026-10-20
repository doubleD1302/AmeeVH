import json

data = json.load(open('StellaSora_VietHoa/work/batches/dialogue_batch6_awakening_talk.json', encoding='utf-8'))
stt = [d for d in data if d['table'] == 'StarTowerTalk']
print(f"StarTowerTalk count: {len(stt)}")
for idx, it in enumerate(stt[:20]):
    print(f"[{it['key']}] EN: {it['en'][:60]} | ZH: {it.get('zh', '')[:30]} | VI: {it.get('current_vi', '')[:50]}")

print("\n--- Non-Portia items in StarTowerTalk ---")
for idx, it in enumerate(stt):
    if it['en'] != 'Portia':
        print(f"[{it['key']}] EN: {it['en']} | ZH: {it.get('zh', '')} | VI: {it.get('current_vi', '')}")
