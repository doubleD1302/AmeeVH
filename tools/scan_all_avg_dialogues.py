import os
import re
import json

viet_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa"
lua_config_dir = os.path.join(viet_dir, r"work\research\lua_tree\Game\UI\Avg\_en\Config")

print(f"Scanning AVG scripts in {lua_config_dir}...")
files = [f for f in os.listdir(lua_config_dir) if f.endswith(".lua")]
print(f"Total AVG script files: {len(files)}")

total_dialogues = 0
file_dialogue_counts = []

for f in sorted(files):
    fpath = os.path.join(lua_config_dir, f)
    with open(fpath, "rb") as fp:
        data = fp.read()
    
    # Extract string literals from Lua bytecode
    # Text strings typically contain ASCII characters, spaces, punctuation
    lines = re.findall(rb'[\x20-\x7e\n\r\t]{4,}', data)
    valid_lines = []
    for l in lines:
        s = l.decode("latin1", errors="ignore").strip()
        if s.startswith("@") or s.startswith("avg") or s.startswith("vo_") or s.startswith("__"):
            continue
        if s.startswith("Game/") or s.startswith("Assets/") or s.startswith("UI/") or s.startswith("Prefab"):
            continue
        if s in ["SetGroupId", "SetBubbleUIType", "SetBubble", "SetTalk", "SetBg", "SetBgm", "PlayVoice", "PlaySound", "SetCamera", "SetTransition", "SetWait", "True", "False"]:
            continue
        # Check if contains letters and spaces or is a meaningful sentence
        if any(c.isalpha() for c in s) and (" " in s or len(s) > 12):
            valid_lines.append(s)
    
    dedup = list(dict.fromkeys(valid_lines))
    if dedup:
        total_dialogues += len(dedup)
        file_dialogue_counts.append((f, len(dedup), dedup[:3]))

print(f"Total dialogue / narration strings across 596 AVG scripts: {total_dialogues}")

# Sort by count
file_dialogue_counts.sort(key=lambda x: x[1], reverse=True)
print("\nTop 30 AVG files by dialogue count:")
for f, c, samps in file_dialogue_counts[:30]:
    s_text = " | ".join([s[:40] for s in samps])
    print(f"  {f:25s} | {c:4d} lines | {s_text[:70]}")
