import json
from pathlib import Path

path = Path("StellaSora_VietHoa/work/batches/batch_light_group1_noya.json")
items = json.loads(path.read_text(encoding="utf-8"))

for i, x in enumerate(items):
    t = x.get("table")
    k = x.get("key")
    zh = x.get("zh", "")
    en = x.get("en", "")
    vi = x.get("current_vi", "")
    print(f"[{i+1:03d}] {t} | {k}")
    print(f"  ZH: {zh}")
    print(f"  EN: {en}")
    print(f"  VI: {vi}")
    print()
