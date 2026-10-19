import json
from pathlib import Path

ROOT = Path(r"C:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
CHUNKS_DIR = ROOT / "work" / "research" / "chunks"

for i in range(2, 6):
    in_file = CHUNKS_DIR / f"chunk_{i}.json"
    with open(in_file, "r", encoding="utf-8") as f:
        c = json.load(f)
    out_file = CHUNKS_DIR / f"chunk_{i}_review.txt"
    with open(out_file, "w", encoding="utf-8") as f:
        for j, (k, v) in enumerate(c.items()):
            f.write(f"[{j+1:03d}] {k}\n  EN: {v['en']}\n  CN: {v['cn']}\n\n")
    print(f"Written chunk_{i}_review.txt ({len(c)} items)")
