import os
import re

lua_config_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\research\lua_tree\Game\UI\Avg\_en\Config"

files = os.listdir(lua_config_dir)
print(f"Total Lua AVG story files: {len(files)}")

# Count dialogue lines in sample files
sample_files = ["BBm00_01.lua", "STm01_01.lua", "CG_103_01.lua", "STsp_01_01.lua"]
for sf in sample_files:
    fpath = os.path.join(lua_config_dir, sf)
    if os.path.exists(fpath):
        with open(fpath, "rb") as f:
            data = f.read()
        # Find string constants
        # In Lua 5.3 bytecode, strings often have length prefix
        # Let's see what text strings exist
        lines = re.findall(rb'[\x20-\x7e\n\r\t]{5,}', data)
        # Filter for actual dialogue (contains letters and spaces)
        dialogues = [line.decode("latin1", errors="ignore") for line in lines if b" " in line and not line.startswith(b"@") and not line.startswith(b"avg") and not line.startswith(b"vo_")]
        print(f"File {sf} ({len(data)} bytes) has ~{len(dialogues)} dialogue candidates. Sample:")
        for d in dialogues[:5]:
            print(f"   - {d.strip()[:60]}")
