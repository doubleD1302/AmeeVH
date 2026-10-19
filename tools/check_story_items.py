import json
from pathlib import Path

entries = Path('StellaSora_VietHoa/work/research/data_en_original/entries')
with open(entries / '00890_0x939d4390e6e6b8fd.bin', 'r', encoding='utf-8') as f:
    cn_story = json.load(f)
with open('StellaSora_VietHoa/work/polish/phase3_dataset.json', 'r', encoding='utf-8') as f:
    story = json.load(f)['Story']

# Let's see how many items in Story are titles (.1) vs descs (.2) vs codes (.4)
print(f"Total story items: {len(story)}")
