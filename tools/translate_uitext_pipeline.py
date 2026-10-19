import json
import re
from pathlib import Path

ROOT = Path(r"C:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
JSON_PATH = ROOT / "work" / "research" / "uitext_to_translate.json"

with open(JSON_PATH, "r", encoding="utf-8") as f:
    items = json.load(f)

def show_range(start, end):
    for i, (k, v) in enumerate(list(items.items())[start:end]):
        print(f"[{start+i+1}] {k}")
        print(f"     EN: {repr(v['en'])}")
        print(f"     CN: {repr(v['cn'])}")

if __name__ == "__main__":
    show_range(50, 80)
