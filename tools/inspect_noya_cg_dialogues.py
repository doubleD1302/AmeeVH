import os
import re

lua_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\research\lua_tree\Game\UI\Avg\_en\Config"

for cg in ["CG_112_01.lua", "CG_112_02.lua", "CG_112_03.lua"]:
    fpath = os.path.join(lua_dir, cg)
    with open(fpath, "rb") as f:
        data = f.read()
    print(f"=== {cg} ({len(data)} bytes) ===")
    # Extract dialogue texts
    lines = re.findall(rb'[\x20-\x7e\n\r\t]{5,}', data)
    dialogues = [line.decode("latin1", errors="ignore") for line in lines if b" " in line and not line.startswith(b"@") and not line.startswith(b"avg") and not line.startswith(b"vo_")]
    print(f"Found {len(dialogues)} candidate text lines. First 15:")
    for d in dialogues[:15]:
        print("  ", d.strip()[:70])
