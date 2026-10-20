import json

data = json.load(open('StellaSora_VietHoa/work/batches/dialogue_batch6_awakening_talk.json', encoding='utf-8'))

with open('StellaSora_VietHoa/tools/plot_dump.txt', 'w', encoding='utf-8') as f:
    for idx, it in enumerate(data):
        if it['table'] == 'Plot':
            f.write(f"[{it['key']}]\n  EN: {it['en']}\n  ZH: {it.get('zh', '')}\n  VI: {it.get('current_vi', '')}\n\n")

with open('StellaSora_VietHoa/tools/story_dump.txt', 'w', encoding='utf-8') as f:
    for idx, it in enumerate(data):
        if it['table'] == 'Story':
            f.write(f"[{it['key']}]\n  EN: {it['en']}\n  ZH: {it.get('zh', '')}\n  VI: {it.get('current_vi', '')}\n\n")

print("Dumps written successfully.")
