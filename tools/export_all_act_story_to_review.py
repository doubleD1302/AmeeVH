import json
from pathlib import Path

entries = Path('StellaSora_VietHoa/work/research/data_en_original/entries')
with open(entries / '00727_0x789e881d02a7ddcb.bin', 'r', encoding='utf-8') as f:
    cn_act = json.load(f)
with open('StellaSora_VietHoa/work/polish/phase3_dataset.json', 'r', encoding='utf-8') as f:
    act = json.load(f)['ActivityStory']

chapters = {}
for it in act:
    parts = it['key'].split('.')
    cid = '.'.join(parts[:2])
    field = parts[2]
    if cid not in chapters:
        chapters[cid] = {}
    chapters[cid][field] = {
        'en': it['en'],
        'cn': cn_act.get(it['key'], ''),
        'vi': it['vi_current']
    }

cids = sorted(chapters.keys(), key=lambda x: [int(p) if p.isdigit() else p for p in x.split('.')])

out = []
for cid in cids:
    fields = chapters[cid]
    t = fields.get('1', {})
    d = fields.get('2', {})
    c = fields.get('4', {})
    out.append(f"[{cid}]")
    out.append(f"  Title: {t.get('en')} | CN: {t.get('cn')} | VI: {t.get('vi')}")
    out.append(f"  Desc:  {d.get('en')} | CN: {d.get('cn')} | VI: {d.get('vi')}")
    out.append(f"  Code:  {c.get('en')} | CN: {c.get('cn')} | VI: {c.get('vi')}")
    out.append("")

with open('StellaSora_VietHoa/tools/act_story_all_124.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))

print(f"Exported {len(cids)} ActivityStory chapters to act_story_all_124.txt")
