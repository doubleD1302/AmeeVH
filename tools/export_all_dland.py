import json
from pathlib import Path

entries = Path('StellaSora_VietHoa/work/research/data_en_original/entries')
with open(entries / '00767_0x43ac532f7df5c82a.bin', 'r', encoding='utf-8') as f:
    cn_dland = json.load(f)
with open('StellaSora_VietHoa/work/polish/phase3_dataset.json', 'r', encoding='utf-8') as f:
    dland = json.load(f)['DatingLandmarkEvent']

out = []
for it in dland:
    k = it['key']
    en = it['en']
    cn = cn_dland.get(k, '')
    vi = it['vi_current']
    out.append(f"[{k}]")
    out.append(f"  EN: {en}")
    out.append(f"  CN: {cn}")
    out.append(f"  VI: {vi}")
    out.append("")

with open('StellaSora_VietHoa/tools/dland_all_262.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))

print(f"Exported {len(dland)} DatingLandmark entries to dland_all_262.txt")
