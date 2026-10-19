import json
from pathlib import Path

entries = Path('StellaSora_VietHoa/work/research/data_en_original/entries')
with open(entries / '00890_0x939d4390e6e6b8fd.bin', 'r', encoding='utf-8') as f:
    cn_story = json.load(f)
with open('StellaSora_VietHoa/work/polish/phase3_dataset.json', 'r', encoding='utf-8') as f:
    story = json.load(f)['Story']

print("=== ALL STORY TITLES & DESCS ===")
for it in story:
    k = it['key']
    en = it['en']
    cn = cn_story.get(k, '')
    vi = it['vi_current']
    # If not code like BT01, 01A
    if len(en) > 4:
        print(f"[{k}] EN: {en} | CN: {cn} | VI: {vi}")
