import json
from pathlib import Path

entries = Path('StellaSora_VietHoa/work/research/data_en_original/entries')
with open(entries / '00765_0x733ee8fdb8a6a976.bin', 'r', encoding='utf-8') as f:
    cn_dchar = json.load(f)
with open('StellaSora_VietHoa/work/polish/phase3_dataset.json', 'r', encoding='utf-8') as f:
    p3 = json.load(f)['DatingCharacterEvent']

print("=== DATING CHARACTER EVENT SAMPLES ===")
for it in p3[:15]:
    k = it['key']
    en = it['en']
    vi = it['vi_current']
    cn = cn_dchar.get(k, '')
    print(f"[{k}]")
    print(f"  EN: {en}")
    print(f"  CN: {cn}")
    print(f"  VI: {vi}")
