import os
import re
import json

viet_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa"
lua_config_dir = os.path.join(viet_dir, r"work\research\lua_tree\Game\UI\Avg\_en\Config")

# Define priority groups for the 10,000 batch:
# Group A: Prologue & Main Story Chapters 1, 2, 3
# Group B: Character Stories (CG_103, CG_107, CG_111, CG_112, CG_115, CG_118, CG_120, CG_127, CG_134, CG_144)
# Group C: Phone Messages (PM103, PM107, PM111, PM112, PM120, PM126, PM127, PM132)

all_files = sorted(os.listdir(lua_config_dir))

def get_priority_weight(filename):
    if filename.startswith("BBm"): # Prologue
        return 1
    if filename.startswith("STm01_"): # Main Story Ch 1
        return 2
    if filename.startswith("STm02_"): # Main Story Ch 2
        return 3
    if filename.startswith("STm03_"): # Main Story Ch 3
        return 4
    if filename.startswith("CG_112_"): # Noya Story
        return 5
    if filename.startswith("CG_103_") or filename.startswith("CG_111_") or filename.startswith("CG_107_"):
        return 6
    if filename.startswith("CG_144_") or filename.startswith("CG_115_") or filename.startswith("CG_118_") or filename.startswith("CG_120_") or filename.startswith("CG_127_"):
        return 7
    if filename.startswith("PM"): # Phone chats
        return 8
    if filename.startswith("STm04_"):
        return 9
    if filename.startswith("CG_"):
        return 10
    if filename.startswith("STsp_"):
        return 11
    return 20

ranked_files = sorted(all_files, key=lambda f: (get_priority_weight(f), f))

batch_10000 = []
included_files = []

for f in ranked_files:
    if not f.endswith(".lua"):
        continue
    fpath = os.path.join(lua_config_dir, f)
    with open(fpath, "rb") as fp:
        data = fp.read()
    
    lines = re.findall(rb'[\x20-\x7e\n\r\t]{4,}', data)
    valid_lines = []
    for l in lines:
        s = l.decode("latin1", errors="ignore").strip()
        if s.startswith("@") or s.startswith("avg") or s.startswith("vo_") or s.startswith("__"):
            continue
        if s.startswith("Game/") or s.startswith("Assets/") or s.startswith("UI/") or s.startswith("Prefab"):
            continue
        if s.startswith("ttc_") or s.startswith("AvgStageEffect") or s.startswith("music_") or s.startswith("sound_"):
            continue
        if s in ["SetGroupId", "SetBubbleUIType", "SetBubble", "SetTalk", "SetBg", "SetBgm", "PlayVoice", "PlaySound", "SetCamera", "SetTransition", "SetWait", "True", "False"]:
            continue
        # Filter genuine text
        if any(c.isalpha() for c in s) and (" " in s or len(s) > 12):
            valid_lines.append(s)
    
    dedup = list(dict.fromkeys(valid_lines))
    if not dedup:
        continue
    
    file_items = []
    for idx, s in enumerate(dedup):
        item_id = f"{f[:-4]}.{idx+1}"
        file_items.append((item_id, s))
    
    if len(batch_10000) + len(file_items) <= 10200:
        batch_10000.extend(file_items)
        included_files.append((f, len(file_items), get_priority_weight(f)))
    else:
        # Take the rest up to 10,000
        needed = 10000 - len(batch_10000)
        if needed > 0:
            batch_10000.extend(file_items[:needed])
            included_files.append((f, needed, get_priority_weight(f)))
        break

print(f"Total selected items: {len(batch_10000)}")
print(f"Total AVG files covered: {len(included_files)}")

# Group by category
cats = {}
for f, count, weight in included_files:
    prefix = f.split("_")[0] if "_" in f else f[:4]
    cats[prefix] = cats.get(prefix, 0) + count

print("\nBreakdown of 10,000 items:")
for prefix, count in sorted(cats.items(), key=lambda x: x[1], reverse=True):
    print(f"  {prefix:20s}: {count:5d} items")

# Save batch to file
out_batch_file = os.path.join(viet_dir, r"work\batches\batch_10000_avg_stories.json")
batch_data = {item[0]: item[1] for item in batch_10000}
with open(out_batch_file, "w", encoding="utf-8") as fp:
    json.dump(batch_data, fp, indent=2, ensure_ascii=False)

print(f"\nSaved batch of {len(batch_data)} items to: {out_batch_file}")
