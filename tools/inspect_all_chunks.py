import json
from pathlib import Path
from collections import Counter

ROOT = Path(r"C:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
CHUNKS_DIR = ROOT / "work" / "research" / "chunks"

for i in range(1, 6):
    with open(CHUNKS_DIR / f"chunk_{i}.json", "r", encoding="utf-8") as f:
        c = json.load(f)
    prefixes = Counter(k.split(".")[1].split("_")[0] for k in c)
    top3 = [f"{p}:{cnt}" for p, cnt in prefixes.most_common(5)]
    print(f"Chunk {i} ({len(c)} items): {', '.join(top3)}")
