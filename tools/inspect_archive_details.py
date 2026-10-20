import json
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
items = json.loads((ROOT / "tools" / "all_items_with_en.json").read_text(encoding="utf-8"))
sub = [x for x in items if x["table"] == "CharacterArchiveContent"]
print(f"Total CharacterArchiveContent: {len(sub)}")
for i, it in enumerate(sub):
    print(f"[{i+1}/{len(sub)}] {it['key']}")
    print(f"  EN: {repr(it['en'][:120])}")
    print(f"  CURRENT_VI: {repr(it['current_vi'][:120])}")
