# -*- coding: utf-8 -*-
import json
import re
from pathlib import Path

entries_dir = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\research\data_200_decrypted\entries")

safe_patterns = [
    r"anh hùng", r"anh đào", r"tiếng anh", r"tinh anh", r"thạch anh", r"quyền anh",
    r"anh dũng", r"anh tuấn", r"anh kiệt", r"anh chàng", r"anh ta", r"anh ấy",
    r"tạ anh", r"anh em", r"dạ anh", r"lạc anh", r"anh trai", r"mấy anh"
]

items = {}
for f in sorted(entries_dir.glob("*.bin")):
    try:
        d = json.loads(f.read_text(encoding="utf-8"))
        for k, v in d.items():
            if not isinstance(v, str):
                continue
            v_lower = v.lower()
            if "anh" in v_lower:
                v_clean = v_lower
                for p in safe_patterns:
                    v_clean = re.sub(p, "___", v_clean)
                m = re.search(r"(.{0,30}\banh\b.{0,30})", v_clean)
                if m:
                    items[k] = (m.group(1).replace("\n", " "), v)
    except Exception:
        pass

print(f"Distinct keys found: {len(items)}")
for k, (snippet, full) in sorted(items.items()):
    print(f"[{k}] snippet: {snippet}")
