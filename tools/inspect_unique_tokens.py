import json
import re
from pathlib import Path

data_path = Path("StellaSora_VietHoa/work/polish/phase3_dataset.json")
with open(data_path, "r", encoding="utf-8") as f:
    data = json.load(f)

for tname in ['PenguinCard', 'AffinityQuest', 'DatingLandmarkEvent', 'DatingCharacterEvent', 'ActivityTask']:
    tokens = set()
    for it in data[tname]:
        en = it['en']
        t_found = re.findall(r'\{[^}]+\}|<[^>]+>|==[^=]+==|&[^&]+&', en)
        tokens.update(t_found)
    print(f"\n{tname} unique tokens ({len(tokens)}):")
    for t in sorted(tokens):
        print(f"  {t}")
