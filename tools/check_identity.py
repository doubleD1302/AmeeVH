import json
import re
from pathlib import Path

ROOT = Path(r"C:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
JSON_PATH = ROOT / "work" / "research" / "uitext_to_translate.json"

with open(JSON_PATH, "r", encoding="utf-8") as f:
    items = json.load(f)

print(f"Total items: {len(items)}")

# Let's see how many identical strings (like format strings or already VN)
identical = {}
for k, v in items.items():
    en = v['en'].strip()
    cn = v['cn'].strip()
    if en == cn and not re.search(r'[a-zA-Z\u4e00-\u9fff]', en):
        identical[k] = en
    elif en in ['Xem', 'Cao', 'Mua', 'Tham gia ngay']:
        identical[k] = en

print(f"Identical / No-trans / Already VN: {len(identical)}")
