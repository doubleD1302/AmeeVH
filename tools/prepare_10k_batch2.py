import os
import json
import struct
import re
import sys

viet_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa"
lua_config_dir = os.path.join(viet_dir, r"work\research\lua_tree\Game\UI\Avg\_en\Config")
batch1_path = os.path.join(viet_dir, r"work\batches\batch_10000_avg_clean.json")

sys.path.insert(0, os.path.join(viet_dir, "tools"))
from extract_clean_10k_avg import extract_clean_lua53_strings

with open(batch1_path, "r", encoding="utf-8") as f:
    b1 = json.load(f)
b1_keys = set(b1.keys())

all_files = sorted(os.listdir(lua_config_dir))

def is_genuine_dialogue(s):
    s_strip = s.strip()
    if not s_strip or len(s_strip) < 2:
        return False
    # If single word snake_case / identifier
    if re.match(r"^[a-zA-Z0-9_]+$", s_strip) and " " not in s_strip:
        return False
    # Common engine/asset prefixes
    prefixes = (
        "ep_", "fx_", "story_", "white_", "black_", "Set", "Play", "avg", "bg_",
        "item_", "icon_", "eff_", "cam_", "ui_", "vo_", "se_", "snd_", "res_",
        "prefab_", "spine_", "ttc_", "btn_", "bgm_", "bgs_", "img_", "tex_"
    )
    if s_strip.startswith(prefixes):
        return False
    if not any(c.isalpha() for c in s_strip):
        return False
    # Must look like dialogue or narrative sentence
    if " " in s_strip or any(p in s_strip for p in [".", "!", "?", ",", "…", ":", ";", "—", "-"]):
        return True
    return False

def get_b2_priority_balanced(f):
    if f.startswith("STm04_"): return 1
    if f.startswith("STm05_"): return 2
    if f.startswith("CG_"): return 3
    if f.startswith("STsp_"): return 4
    if f.startswith("STm06_"): return 5
    if f.startswith("STm07_"): return 6
    return 10

ranked = sorted(all_files, key=lambda f: (get_b2_priority_balanced(f), f))

batch2 = []
for f in ranked:
    if not f.endswith(".lua"):
        continue
    fpath = os.path.join(lua_config_dir, f)
    slist = extract_clean_lua53_strings(fpath)
    base = f[:-4]
    for idx, s in enumerate(slist):
        if not is_genuine_dialogue(s):
            continue
        k = f"{base}.{idx+1}"
        if k not in b1_keys:
            batch2.append((k, s))
            if len(batch2) == 10000:
                break
    if len(batch2) == 10000:
        break

print(f"Total pure dialogues extracted for Batch 2: {len(batch2)}")

# Save full clean batch 2
full_b2_dict = dict(batch2)
b2_full_path = os.path.join(viet_dir, r"work\batches\batch_10000_avg_clean_b2.json")
with open(b2_full_path, "w", encoding="utf-8") as f:
    json.dump(full_b2_dict, f, indent=2, ensure_ascii=False)

# Split into 3 partitions:
# Part A: 3334
# Part B: 3333
# Part C: 3333
partA = dict(batch2[:3334])
partB = dict(batch2[3334:6667])
partC = dict(batch2[6667:10000])

print(f"Part A: {len(partA)} items")
print(f"Part B: {len(partB)} items")
print(f"Part C: {len(partC)} items")

partA_path = os.path.join(viet_dir, r"work\batches\batch_10k_b2_partA.json")
partB_path = os.path.join(viet_dir, r"work\batches\batch_10k_b2_partB.json")
partC_path = os.path.join(viet_dir, r"work\batches\batch_10k_b2_partC.json")

with open(partA_path, "w", encoding="utf-8") as f:
    json.dump(partA, f, indent=2, ensure_ascii=False)

with open(partB_path, "w", encoding="utf-8") as f:
    json.dump(partB, f, indent=2, ensure_ascii=False)

with open(partC_path, "w", encoding="utf-8") as f:
    json.dump(partC, f, indent=2, ensure_ascii=False)

print("Batch 2 clean preparation completed successfully!")
