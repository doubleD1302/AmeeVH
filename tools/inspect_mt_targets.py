import json
import re
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
data = json.loads((ROOT / "work" / "batches" / "audit_batch1_dating_char.json").read_text(encoding="utf-8"))

def inspect_pattern(name, pat):
    matches = [d for d in data if re.search(pat, d["current_vi"], re.IGNORECASE)]
    print(f"=== {name} ({len(matches)}) ===")
    for m in matches:
        print(f"[{m['key']}]")
        print(f"  EN: {m['en'][:90]}")
        print(f"  VI: {m['current_vi'][:90]}")

inspect_pattern("không thể không", r"\bkhông thể không\b")
inspect_pattern("ở một mức độ", r"\bở một mức độ\b")
