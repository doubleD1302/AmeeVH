import json
import re
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
data = json.loads((ROOT / "work" / "batches" / "audit_batch1_dating_char.json").read_text(encoding="utf-8"))

queries = [
    ("không thể không", r"\bkhông thể không\b"),
    ("ở một mức độ", r"\bở một mức độ\b"),
    ("trong khi", r"\btrong khi\b"),
    ("một cách", r"\bmột cách\s+\w+"),
    ("của bạn", r"\bcủa bạn\b"),
    ("của tôi", r"\bcủa tôi\b"),
    ("của cô ấy", r"\bcủa cô ấy\b"),
]

for name, pat in queries:
    matches = [d for d in data if re.search(pat, d["current_vi"], re.IGNORECASE)]
    print(f"=== {name}: {len(matches)} matches ===")
    for m in matches[:5]:
        print(f"[{m['key']}]")
        print(f"  EN: {m['en'][:100]}")
        print(f"  VI: {m['current_vi'][:100]}")
