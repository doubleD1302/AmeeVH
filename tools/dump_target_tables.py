import json
from pathlib import Path
from collections import defaultdict

f = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\batches\untranslated_unique.json")
data = json.loads(f.read_text(encoding="utf-8"))

for target in ["LevelQuestTarget", "ActivityTask", "MallPackage", "ActivityGoods"]:
    items = [d["en"] for d in data if any(occ[0] == target for occ in d["occurrences"])]
    print(f"\n=================== {target} ({len(items)}) ===================")
    for s in items:
        print(repr(s))
