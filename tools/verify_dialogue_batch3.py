import json
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
APPROVED_PATH = ROOT / "work" / "batches" / "dialogue_batch3_startower_approved.json"
ORIGINAL_PATH = ROOT / "work" / "batches" / "dialogue_batch3_startower_story.json"

with open(APPROVED_PATH, "r", encoding="utf-8") as f:
    approved = json.load(f)

with open(ORIGINAL_PATH, "r", encoding="utf-8") as f:
    orig = json.load(f)

orig_map = {it["key"]: it for it in orig}

print(f"Total approved items: {len(approved)}")
empty = [it for it in approved if not it["vi"]]
print(f"Empty items: {len(empty)}")

dialogue_items = [it for it in approved if not it["key"].endswith(".1")]
print(f"Dialogue lines: {len(dialogue_items)}")

for idx, it in enumerate(dialogue_items, 1):
    k = it["key"]
    old = orig_map.get(k, {}).get("current_vi", "")
    print(f"\n[{idx:02d}] {k}")
    print(f"  EN    : {it['en']}")
    print(f"  CN    : {it['cn']}")
    print(f"  OLD VI: {old}")
    print(f"  NEW VI: {it['vi']}")
