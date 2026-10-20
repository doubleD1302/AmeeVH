import os
import re

avg_path = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\research\lua_tree\Game\UI\Avg\_en\Config\BBm00_01.lua"
with open(avg_path, "rb") as f:
    data = f.read()

print("File size:", len(data))
print("Header:", data[:16])

# Extract strings from Lua 5.3 bytecode
# In Lua 5.3 binary format, constants table contains strings prefixed by size
# Let's see if we can find text strings
text_candidates = re.findall(rb'[\x20-\x7e]{4,}', data)
print(f"Extracted {len(text_candidates)} text fragments. First 30:")
for t in text_candidates[:30]:
    s = t.decode("latin1", errors="ignore")
    if len(s) > 5 and not s.startswith("__"):
        print(" ", s)
