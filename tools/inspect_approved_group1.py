import json

data = json.load(open('StellaSora_VietHoa/work/batches/final_wave_group1_gameplay_minigames_approved.json', encoding='utf-8'))

tables = {}
for it in data:
    tables.setdefault(it['table'], []).append(it)

for tbl, items in sorted(tables.items()):
    print(f"\n==========================================")
    print(f"TABLE: {tbl} ({len(items)} items)")
    print(f"==========================================")
    for it in items:
        k = it['key']
        en = it.get('en', '')
        zh = it.get('zh', '')
        vi = it.get('approved_vi') or it.get('vi', '')
        reason = it.get('reason', '')
        print(f"--- [{k}] ---")
        print(f"  EN: {en}")
        print(f"  ZH: {zh}")
        print(f"  VI: {vi}")
        if reason:
            print(f"  REASON: {reason}")
