import json
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
items = json.loads((ROOT / "tools" / "untranslated_204.json").read_text(encoding="utf-8"))

for tbl in ["DatingCharacterEvent", "DatingLandmarkEvent"]:
    sub = [it for it in items if it["table"] == tbl]
    print(f"=== {tbl} ({len(sub)}) ===")
    for it in sub:
        print(f"[{it['key']}]")
        print(f"  EN: {it['en']}")
