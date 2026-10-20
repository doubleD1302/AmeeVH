import json
from pathlib import Path

ROOT = Path('StellaSora_VietHoa')
batch_dir = ROOT / 'work' / 'batches'

for g in ['group1_noya', 'group2_jinglin_tilia', 'group3_firefly_shia', 'group4_minova_laru']:
    f = batch_dir / f'batch_light_{g}.json'
    items = json.loads(f.read_text(encoding='utf-8'))
    print(f'=== {g} ({len(items)} items) ===')
    tables = {}
    for x in items:
        tables[x['table']] = tables.get(x['table'], 0) + 1
    print('  Tables breakdown:', tables)
    for x in items[:2]:
        print(f"  [{x['table']}] {x['key']}")
        print(f"     EN: {x['en'][:60]}")
        print(f"     ZH: {x['zh'][:60]}")
        print(f"     VI: {x['current_vi'][:60]}")
