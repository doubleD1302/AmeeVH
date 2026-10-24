import json
from pathlib import Path
from collections import Counter

root = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
b3_path = root / "work/batches/batch_10k_b3_partC.json"

data = json.load(open(b3_path, encoding="utf-8"))
print(f"Total lines in batch_10k_b3_partC.json: {len(data)}")

scenes = Counter()
for k, v in data.items():
    sc = k.split(".")[0]
    scenes[sc] += 1

print(f"Total scenes: {len(scenes)}")
for sc, count in sorted(scenes.items(), key=lambda x: -x[1]):
    print(f"  {sc}: {count} lines")

# Check if there is an existing translated file or pristine en
tr_path = root / "work/batches/batch_10k_b3_partC_translated.json"
if tr_path.exists():
    tr_data = json.load(open(tr_path, encoding="utf-8"))
    print(f"\nExisting translated file: {tr_path.name} with {len(tr_data)} items")
else:
    print(f"\nNo existing {tr_path.name}")
