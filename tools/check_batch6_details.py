import json
from pathlib import Path

p = Path("StellaSora_VietHoa/work/reviews/BATCH_06_POLISH_AND_RECONCILIATION_LEDGER.json")
if p.exists():
    d = json.loads(p.read_text(encoding="utf-8"))
    decisions = d.get("decisions", [])
    print(f"Ledger total: {len(decisions)} decisions")
    ed_items = [it for it in decisions if "CH04ED" in it.get("id", "")]
    print(f"CH04ED items: {len(ed_items)}")
    if ed_items:
        print("Sample CH04ED item:")
        print(json.dumps(ed_items[0], indent=2, ensure_ascii=False))

b6_prop = Path("StellaSora_VietHoa/work/batches/BATCH_FIX_06_POLISH_CANDIDATES.json")
d6 = json.loads(b6_prop.read_text(encoding="utf-8"))
for it in d6["entries"]:
    if "root:k" in it["id"]:
        print(it)
