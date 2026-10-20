import json
import re
from pathlib import Path

ROOT = Path("c:/YostarGames/StellaSora_EN/StellaSora_VietHoa")
SRC_PATH = ROOT / "work/batches/batch_10k_b3_partA.json"
DST_PATH = ROOT / "work/batches/batch_10k_b3_partA_translated.json"

with open(SRC_PATH, "r", encoding="utf-8") as f:
    src = json.load(f)
with open(DST_PATH, "r", encoding="utf-8") as f:
    dst = json.load(f)

print(f"Total entries: {len(dst)}")
