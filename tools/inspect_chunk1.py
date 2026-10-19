import json
from pathlib import Path
from collections import Counter

ROOT = Path(r"C:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
CHUNK1_PATH = ROOT / "work" / "research" / "chunks" / "chunk_1.json"

with open(CHUNK1_PATH, "r", encoding="utf-8") as f:
    chunk1 = json.load(f)

print(f"Chunk 1 has {len(chunk1)} items.")
prefixes = Counter(k.split(".")[1].split("_")[0] for k in chunk1)
for p, c in prefixes.most_common(20):
    print(f"  {p:20s}: {c}")
