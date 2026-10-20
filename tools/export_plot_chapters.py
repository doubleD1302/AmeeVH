import json
import re

data = json.load(open('StellaSora_VietHoa/work/batches/dialogue_batch6_awakening_talk.json', encoding='utf-8'))
plot_items = [d for d in data if d['table'] == 'Plot']

groups = {}
for it in plot_items:
    m = re.match(r'Plot\.(\d+)\.(\d+)', it['key'])
    if m:
        cid = m.group(1)
        sub = m.group(2)
        groups.setdefault(cid, {})[sub] = it

with open('StellaSora_VietHoa/tools/all_120_plot_chapters.txt', 'w', encoding='utf-8') as f:
    for idx, (cid, subs) in enumerate(sorted(groups.items()), 1):
        t1 = subs.get('1', {})
        t2 = subs.get('2', {})
        f.write(f"=== Chapter {idx:3d} (ID: {cid}) ===\n")
        f.write(f"  [1] EN: {t1.get('en', '')}\n")
        f.write(f"      ZH: {t1.get('zh', '')}\n")
        f.write(f"      VI: {t1.get('current_vi', '')}\n")
        f.write(f"  [2] EN: {t2.get('en', '')}\n")
        f.write(f"      ZH: {t2.get('zh', '')}\n")
        f.write(f"      VI: {t2.get('current_vi', '')}\n\n")

print(f"Written all {len(groups)} chapters to StellaSora_VietHoa/tools/all_120_plot_chapters.txt")
