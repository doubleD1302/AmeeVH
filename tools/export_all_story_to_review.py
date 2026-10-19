import json
from pathlib import Path

with open('StellaSora_VietHoa/tools/story_chapters_dump.json', 'r', encoding='utf-8') as f:
    chapters = json.load(f)

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

with open('StellaSora_VietHoa/tools/story_all_196.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))

print(f"Exported {len(cids)} chapters to story_all_196.txt")
