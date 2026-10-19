import json
from pathlib import Path

ROOT = Path(r"C:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
JSON_PATH = ROOT / "work" / "research" / "uitext_to_translate.json"
CHUNKS_DIR = ROOT / "work" / "research" / "chunks"
CHUNKS_DIR.mkdir(parents=True, exist_ok=True)

with open(JSON_PATH, "r", encoding="utf-8") as f:
    items = json.load(f)

item_list = list(items.items())
total = len(item_list)
chunk_size = 600

print(f"Total items: {total}")
for i in range(0, total, chunk_size):
    chunk_idx = (i // chunk_size) + 1
    chunk_items = dict(item_list[i : min(i + chunk_size, total)])
    out_file = CHUNKS_DIR / f"chunk_{chunk_idx}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(chunk_items, f, ensure_ascii=False, indent=2)
    print(f"Saved chunk_{chunk_idx}.json: {len(chunk_items)} items ({i} to {min(i + chunk_size, total) - 1})")
