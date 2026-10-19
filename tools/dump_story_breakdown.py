import json
from pathlib import Path

entries = Path('StellaSora_VietHoa/work/research/data_en_original/entries')
with open(entries / '00890_0x939d4390e6e6b8fd.bin', 'r', encoding='utf-8') as f:
    cn_story = json.load(f)
with open('StellaSora_VietHoa/work/polish/phase3_dataset.json', 'r', encoding='utf-8') as f:
    story = json.load(f)['Story']

print("Dumping story titles with CN...")
titles = [it for it in story if it['key'].endswith('.1')]
descs = [it for it in story if it['key'].endswith('.2')]
others = [it for it in story if not (it['key'].endswith('.1') or it['key'].endswith('.2'))]

print(f"Titles: {len(titles)}, Descs: {len(descs)}, Others: {len(others)}")
