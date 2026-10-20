import json
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
items = json.loads((ROOT / "tools" / "all_items_with_en.json").read_text(encoding="utf-8"))

for tbl in ["CharacterArchiveBaseInfo", "CharacterArchiveContent"]:
    sub = [x for x in items if x["table"] == tbl]
    print(f"=== {tbl} ({len(sub)}) ===")
    for it in sub:
        print(f"[{it['key']}]")
        print(f"  EN: {repr(it['en'][:80])}")
        print(f"  VI: {repr(it['current_vi'][:80])}")
