import json
data = json.load(open('StellaSora_VietHoa/work/batches/dialogue_batch1_noya_approved.json', encoding='utf-8'))
for it in data:
    if 'Plot' in it.get('key', ''):
        vi = it.get('approved_vi') or it.get('vi') or it.get('current_vi')
        print(f"[{it['key']}] EN: {it['en']}\n   VI: {vi}\n   Reason: {it.get('reason', '')}")
