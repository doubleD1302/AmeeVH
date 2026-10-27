from pathlib import Path

# Fix launcher/core/__init__.py
p1 = Path(r"StellaSora_VietHoa/launcher/core/__init__.py")
t1 = p1.read_text(encoding="utf-8")
t1 = t1.replace("from launcher_next_r09.core.", "from .")
p1.write_text(t1, encoding="utf-8")
print("Fixed core/__init__.py")

# Fix launcher/core/diagnostics.py
p2 = Path(r"StellaSora_VietHoa/launcher/core/diagnostics.py")
t2 = p2.read_text(encoding="utf-8")
t2 = t2.replace("from launcher_next_r09.core.types import GameInfo", "from .types import GameInfo")
p2.write_text(t2, encoding="utf-8")
print("Fixed core/diagnostics.py")
