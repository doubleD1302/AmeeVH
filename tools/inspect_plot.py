import json
import re

data = json.load(open('StellaSora_VietHoa/work/batches/dialogue_batch6_awakening_talk.json', encoding='utf-8'))
plot_items = [d for d in data if d['table'] == 'Plot']

# Group by ID prefix
groups = {}
for it in plot_items:
    m = re.match(r'Plot\.(\d+)\.(\d+)', it['key'])
    if m:
        cid = m.group(1)
        sub = m.group(2)
        groups.setdefault(cid, {})[sub] = it

print(f"Total Plot chapters: {len(groups)}")
for cid, subs in sorted(groups.items()):
    t = subs.get('1', {}).get('en', '')
    tz = subs.get('1', {}).get('zh', '')
    tv = subs.get('1', {}).get('current_vi', '')
    d = subs.get('2', {}).get('en', '')
    dz = subs.get('2', {}).get('zh', '')
    dv = subs.get('2', {}).get('current_vi', '')
    print(f"[{cid}] (1) EN: {t} | ZH: {tz} | VI: {tv}")
    print(f"       (2) EN: {d} | ZH: {dz} | VI: {dv}")
