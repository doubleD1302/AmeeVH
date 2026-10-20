import json
import re
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
ENTRIES_DIR = ROOT / "work" / "research" / "data_200_decrypted" / "entries"

targets = [
    r"\bhoa hồng\b",
    r"\bbánh mì nướng\b",
    r"(Thành Phố\s+){2,}",
    r"(thành phố\s+){2,}",
    r"(Lữ Khách\s+){2,}",
    r"(của bạn\s+){2,}",
    r"\bbuổi sáng sắc nét\b",
    r"\bôi chao\b",
    r"\bLá cô ấy cho tôi\b",
    r"\bĐược cung cấp bởi\b",
    r"\bThần mèo meo meo\b",
    r"\bHạt giống nhau\b",
    r"\bHoned Sword Art\b",
]

found = []
for p in ENTRIES_DIR.glob("*.bin"):
    raw = p.read_bytes()
    if not raw.startswith(b"{"):
        continue
    try:
        data = json.loads(raw.decode("utf-8"))
        for k, v in data.items():
            if not isinstance(v, str):
                continue
            for pat in targets:
                if re.search(pat, v, re.IGNORECASE):
                    found.append((p.name, k, v, pat))
                    break
    except Exception:
        pass

print(f"Total defects found across all tables: {len(found)}")
for fname, k, v, pat in found[:20]:
    clean_v = v.replace("\n", " ")[:100]
    print(f"[{fname}] {k} (Pattern: {pat}): {clean_v}")
