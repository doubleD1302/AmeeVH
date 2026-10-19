import json
from pathlib import Path

entries = Path('StellaSora_VietHoa/work/research/data_en_original/entries')
with open(entries / '00833_0x469c8ae265bf9745.bin', 'r', encoding='utf-8') as f:
    cn = json.load(f)
with open(entries / '00612_0x6125df00885a1629.bin', 'r', encoding='utf-8') as f:
    en = json.load(f)
with open('StellaSora_VietHoa/work/polish/phase3_dataset.json', 'r', encoding='utf-8') as f:
    p3 = json.load(f)['PenguinCard']

p3_map = {it['key']: it['vi_current'] for it in p3}

for k, cn_val in list(cn.items())[:40]:
    if k.endswith('.1'):
        print(f"{k}: EN='{en.get(k, '')}' | CN='{cn_val}' | VI='{p3_map.get(k, '')}'")
