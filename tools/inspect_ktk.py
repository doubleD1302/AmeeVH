import json
import re
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
data = json.loads((ROOT / "work" / "batches" / "audit_batch1_dating_char.json").read_text(encoding="utf-8"))

matches = [d for d in data if re.search(r"\bkhông thể không\b", d["current_vi"], re.IGNORECASE)]
for m in matches:
    print(f"[{m['key']}]")
    print("EN:", repr(m["en"]))
    print("VI:", repr(m["current_vi"]))
    print("-" * 50)
