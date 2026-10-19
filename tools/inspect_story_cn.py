import json
from pathlib import Path

entries = Path('StellaSora_VietHoa/work/research/data_en_original/entries')
with open(entries / '00890_0x939d4390e6e6b8fd.bin', 'r', encoding='utf-8') as f:
    cn_story = json.load(f)
with open('StellaSora_VietHoa/work/polish/phase3_dataset.json', 'r', encoding='utf-8') as f:
    p3 = json.load(f)['Story']

print("=== ALL STORY TITLES & DESCS SAMPLES ===")
for it in p3[:40]:
    k = it['key']
    en = it['en']
    vi = it['vi_current']
    cn = cn_story.get(k, '')
    if not (en.startswith('BT') or (en.isdigit()) or (len(en) <= 3 and en[-1] in 'ABCDE')):
        print(f"[{k}]")
        print(f"  EN: {en}")
        print(f"  CN: {cn}")
        print(f"  VI: {vi}")
