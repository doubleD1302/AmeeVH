import json
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
items = json.loads((ROOT / "tools" / "all_items_with_en.json").read_text(encoding="utf-8"))

for tbl in ["DatingLandmarkEvent", "DatingCharacterEvent"]:
    sub = [x for x in items if x["table"] == tbl]
    print(f"=== {tbl} ({len(sub)}) ===")
    events = sorted(set(x["key"].rsplit(".", 1)[0] for x in sub))
    print(f"Unique events: {len(events)} -> {events}")
