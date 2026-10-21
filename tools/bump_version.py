# -*- coding: utf-8 -*-
from pathlib import Path

p = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\launcher\launcher_pc.py")
t = p.read_text(encoding="utf-8")
t = t.replace('"version": "0.8.5"', '"version": "0.9.0"')
p.write_text(t, encoding="utf-8")
print("Updated launcher_pc.py to 0.9.0!")

p2 = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\launcher\notifications.json")
t2 = p2.read_text(encoding="utf-8")
t2 = t2.replace('"version": "0.8.5"', '"version": "0.9.0"')
p2.write_text(t2, encoding="utf-8")
print("Updated notifications.json to 0.9.0!")
