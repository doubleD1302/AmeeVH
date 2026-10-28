# -*- coding: utf-8 -*-
import shutil
from pathlib import Path

root = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
dist_data = root / "dist" / "data_patched_vi.arcx"
dist_lua = root / "dist" / "lua_patched_vi.arcx"

targets_data = [
    Path(r"c:\YostarGames\StellaSora_EN\Persistent_Store\Tables\data.arcx"),
    Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stella Sora\Persistent_Store\Tables\data.arcx")
]

targets_lua = [
    Path(r"c:\YostarGames\StellaSora_EN\Persistent_Store\Scripts\lua.arcx"),
    Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stella Sora\Persistent_Store\Scripts\lua.arcx")
]

if dist_data.exists():
    for td in targets_data:
        if td.parent.exists():
            print(f"Deploying {dist_data.name} -> {td}")
            shutil.copy2(dist_data, td)

if dist_lua.exists():
    for tl in targets_lua:
        if tl.parent.exists():
            print(f"Deploying {dist_lua.name} -> {tl}")
            shutil.copy2(dist_lua, tl)

print("Deploy complete.")
