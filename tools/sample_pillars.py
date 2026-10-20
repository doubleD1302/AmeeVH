import json
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
b1 = json.loads((ROOT / "work/batches/audit_batch1_dating_char.json").read_text(encoding="utf-8"))
b2 = json.loads((ROOT / "work/batches/audit_batch2_ui_sys_ach.json").read_text(encoding="utf-8"))
b3 = json.loads((ROOT / "work/batches/audit_batch3_item_mall_task.json").read_text(encoding="utf-8"))

print("=== SAMPLES PILLAR 1 ===")
for it in b1[20:25]:
    print(f"[{it['table']}] {it['key']}")
    print(f"  EN: {it['en']}")
    print(f"  VI: {it['current_vi']}")

print("\n=== SAMPLES PILLAR 2 ===")
for it in b2[40:45]:
    print(f"[{it['table']}] {it['key']}")
    print(f"  EN: {it['en']}")
    print(f"  VI: {it['current_vi']}")

print("\n=== SAMPLES PILLAR 3 ===")
for it in b3[50:55]:
    print(f"[{it['table']}] {it['key']}")
    print(f"  EN: {it['en']}")
    print(f"  VI: {it['current_vi']}")
