import re
from pathlib import Path

p = Path(r"C:\Users\chann\.gemini\antigravity\brain\3e838693-cae5-4527-b44b-fab05f61cee2\scratch\test_sp01_trans.py")
if p.exists():
    text = p.read_text(encoding="utf-8")
    keys = re.findall(r'"(STsp_[^"]+)":', text)
    print("test_sp01_trans.py keys:", len(keys))
