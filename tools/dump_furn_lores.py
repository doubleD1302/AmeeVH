import json
from pathlib import Path

ROOT = Path("StellaSora_VietHoa")
data = json.load(open(ROOT / "work/batches/furniture_pairs.json", encoding="utf-8"))

lines = []
for i, (en, zh) in enumerate(data["lores"]):
    lines.append(f"{i:3} | EN: {en!r}\n    | ZH: {zh!r}")

Path(ROOT / "work/batches/furniture_lores_dump.txt").write_text('\n'.join(lines), encoding="utf-8")
print(f"Dumped {len(data['lores'])} furniture lores!")
