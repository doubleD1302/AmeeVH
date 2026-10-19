import json
from pathlib import Path

p = Path('StellaSora_VietHoa/work/polish/phase3_polished.json')
with open(p, 'r', encoding='utf-8') as f:
    data = json.load(f)

print("=== BEFORE / AFTER HIGHLIGHTS FOR REPORT ===")
for tname, items in data.items():
    diffs = [it for it in items if it['vi_current'] != it['vi_polished']]
    print(f"\n### {tname} (Total: {len(items)}, Refined: {len(diffs)})")
    for it in diffs[:4]:
        en_short = it['en'].replace('\n', ' ')[:70]
        before = it['vi_current'].replace('\n', ' ')[:70]
        after = it['vi_polished'].replace('\n', ' ')[:70]
        print(f"  * Key: `{it['key']}`")
        print(f"    - EN:     {en_short}")
        print(f"    - Before: {before}")
        print(f"    - After:  {after}")
