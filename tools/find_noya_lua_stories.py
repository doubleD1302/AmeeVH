import os
import re

lua_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\research\lua_tree\Game\UI\Avg\_en\Config"

noya_lua_files = []
for f in sorted(os.listdir(lua_dir)):
    if not f.endswith(".lua"):
        continue
    fpath = os.path.join(lua_dir, f)
    with open(fpath, "rb") as fp:
        content = fp.read()
    if b"112" in f.encode() or b"Noya" in content or b"noya" in content:
        # Count occurrences of Noya
        noya_matches = len(re.findall(rb'noya', content, re.IGNORECASE))
        noya_lua_files.append((f, noya_matches, len(content)))

print(f"Total AVG Story scripts featuring Noya: {len(noya_lua_files)}")
for f, cnt, size in noya_lua_files[:20]:
    print(f"  {f:25s} | mentions: {cnt:3d} | size: {size:6d} bytes")
