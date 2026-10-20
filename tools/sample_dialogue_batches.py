import json
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
b1 = json.loads((ROOT / "work/batches/dialogue_batch1_noya_archive.json").read_text(encoding="utf-8"))
b2 = json.loads((ROOT / "work/batches/dialogue_batch2_dating_events.json").read_text(encoding="utf-8"))
b3 = json.loads((ROOT / "work/batches/dialogue_batch3_startower_story.json").read_text(encoding="utf-8"))

print("=== PACKAGE 1: NOYA ARCHIVE SAMPLES ===")
for it in b1:
    if it["table"] == "CharacterArchiveContent":
        print(f"[{it['key']}]")
        print(f"  EN: {it['en'][:80]}")
        print(f"  VI: {it['current_vi'][:80]}")
        print()
    if it["table"] == "Plot":
        print(f"[{it['key']}]")
        print(f"  EN: {it['en']}")
        print(f"  VI: {it['current_vi']}")
        print()

print("=== PACKAGE 2: DATING SAMPLES ===")
for it in b2[:5]:
    print(f"[{it['key']}]")
    print(f"  EN: {it['en'][:80]}")
    print(f"  VI: {it['current_vi'][:80]}")
    print()

print("=== PACKAGE 3: STAR TOWER SAMPLES ===")
for it in b3[:5]:
    print(f"[{it['key']}]")
    print(f"  EN: {it['en'][:80]}")
    print(f"  VI: {it['current_vi'][:80]}")
    print()
