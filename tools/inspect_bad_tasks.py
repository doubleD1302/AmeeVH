import json
from pathlib import Path

with open('StellaSora_VietHoa/work/research/data_en_original/entries/00728_0xc316bcdb179b0d6e.bin', 'r', encoding='utf-8') as f:
    cn_task = json.load(f)
with open('StellaSora_VietHoa/work/polish/phase3_dataset.json', 'r', encoding='utf-8') as f:
    tasks = json.load(f)['ActivityTask']

bad_tasks = [it for it in tasks if any(w in it['vi_current'].lower() for w in ['rõ ràng', 'xóa kho báu', 'xóa treasure', 'clear summer', 'clear '])]
print(f"Total bad tasks: {len(bad_tasks)}")
for it in bad_tasks[:15]:
    cn = cn_task.get(it['key'], '')
    print(f"[{it['key']}]")
    print(f"  EN: {it['en']}")
    print(f"  CN: {cn}")
    print(f"  VI: {it['vi_current']}\n")
