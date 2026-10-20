import json, sys

data = json.load(open('StellaSora_VietHoa/work/batches/batch_light_group1_noya.json', encoding='utf-8'))

table_name = sys.argv[1] if len(sys.argv) > 1 else 'Skill'

for i, x in enumerate(data):
    if x['table'] == table_name:
        print(f"[{i:03d}] {x['key']}")
        print(f"  ZH: {x.get('zh')}")
        print(f"  EN: {x.get('en')}")
        print(f"  VI: {x.get('current_vi')}")
        print()
