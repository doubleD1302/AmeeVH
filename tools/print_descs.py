import json
from pathlib import Path

ROOT = Path("StellaSora_VietHoa")
data = json.load(open(ROOT / "work/batches/furniture_pairs.json", encoding="utf-8"))

for i, (en, zh) in enumerate(data["descs"]):
    print(f"{i:2} | EN: {en!r} | ZH: {zh!r}")
