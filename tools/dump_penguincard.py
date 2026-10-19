import json
from pathlib import Path

entries = Path('StellaSora_VietHoa/work/research/data_en_original/entries')
with open(entries / '00833_0x469c8ae265bf9745.bin', 'r', encoding='utf-8') as f:
    cn_peng = json.load(f)
with open('StellaSora_VietHoa/work/polish/phase3_dataset.json', 'r', encoding='utf-8') as f:
    peng = json.load(f)['PenguinCard']

names = [it for it in peng if it['key'].endswith('.1')]
descs = [it for it in peng if it['key'].endswith('.2')]

print(f"Total names: {len(names)}, Total descs: {len(descs)}")

# Print unique name translations
name_pairs = {}
for it in names:
    en = it['en']
    cn = cn_peng.get(it['key'], '').replace('[no trans]', '')
    vi = it['vi_current']
    name_pairs[it['key']] = (en, cn, vi)

with open('StellaSora_VietHoa/tools/penguincard_dump.json', 'w', encoding='utf-8') as f:
    json.dump({
        'names': name_pairs,
        'descs': {it['key']: (it['en'], cn_peng.get(it['key'], ''), it['vi_current']) for it in descs}
    }, f, ensure_ascii=False, indent=2)

print("Dumped penguincard_dump.json")
