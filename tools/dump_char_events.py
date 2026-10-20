import json
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
items = json.loads((ROOT / "tools" / "all_items_with_en.json").read_text(encoding="utf-8"))

char_event_items = [it for it in items if it["table"] == "DatingCharacterEvent"]
for it in char_event_items:
    print(f"'{it['key']}': '''{it['en']}''',")
