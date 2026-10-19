import json
from pathlib import Path

ROOT = Path(r"C:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
CHUNK1_PATH = ROOT / "work" / "research" / "chunks" / "chunk_1.json"

with open(CHUNK1_PATH, "r", encoding="utf-8") as f:
    c1 = json.load(f)

# Print all 600 items to a formatted text file for easy inspection
OUT_PATH = ROOT / "work" / "research" / "chunks" / "chunk_1_review.txt"
with open(OUT_PATH, "w", encoding="utf-8") as f:
    for i, (k, v) in enumerate(c1.items()):
        f.write(f"[{i+1:03d}] {k}\n  EN: {v['en']}\n  CN: {v['cn']}\n\n")

print(f"Written {len(c1)} items to {OUT_PATH}")
