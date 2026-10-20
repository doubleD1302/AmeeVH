import os
import json
import struct
import re
import sys

viet_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa"
lua_config_dir = os.path.join(viet_dir, r"work\research\lua_tree\Game\UI\Avg\_en\Config")

b1_path = os.path.join(viet_dir, r"work\batches\batch_10000_avg_clean.json")
b2_path = os.path.join(viet_dir, r"work\batches\batch_10000_avg_clean_b2.json")
b3_path = os.path.join(viet_dir, r"work\batches\batch_10000_avg_clean_b3.json")

with open(b1_path, "r", encoding="utf-8") as f:
    b1 = json.load(f)
with open(b2_path, "r", encoding="utf-8") as f:
    b2 = json.load(f)
with open(b3_path, "r", encoding="utf-8") as f:
    b3 = json.load(f)

translated_keys = set(b1.keys()) | set(b2.keys()) | set(b3.keys())
print(f"Total already translated keys in Batch 1, 2, 3: {len(translated_keys)}")

sys.path.insert(0, os.path.join(viet_dir, "tools"))
from extract_clean_10k_avg import extract_clean_lua53_strings

all_files = sorted(os.listdir(lua_config_dir))

def is_genuine_dialogue(s):
    s_strip = s.strip()
    if not s_strip or len(s_strip) < 2:
        return False
    if re.match(r"^[a-zA-Z0-9_]+$", s_strip) and " " not in s_strip:
        return False
    prefixes = (
        "ep_", "fx_", "story_", "white_", "black_", "Set", "Play", "avg", "bg_",
        "item_", "icon_", "eff_", "cam_", "ui_", "vo_", "se_", "snd_", "res_",
        "prefab_", "spine_", "ttc_", "btn_", "bgm_", "bgs_", "img_", "tex_"
    )
    if s_strip.startswith(prefixes):
        return False
    if not any(c.isalpha() for c in s_strip):
        return False
    if " " in s_strip or any(p in s_strip for p in [".", "!", "?", ",", "…", ":", ";", "—", "-"]):
        return True
    return False

# Priority order for Batch 4:
# 1. Main story Ch 9 (STm09_*) & Special story (STsp_*, DP_*)
# 2. Event stories (STev_*)
# 3. CG character stories remaining (CG_*) & Phone messages remaining (PM_*)
def get_b4_priority(f):
    if f.startswith("STm09_"): return 1
    if f.startswith("STsp_"): return 2
    if f.startswith("DP_"): return 3
    if f.startswith("STev_"): return 4
    if f.startswith("CG_"): return 5
    if f.startswith("PM"): return 6
    return 10

ranked = sorted(all_files, key=lambda f: (get_b4_priority(f), f))

batch4 = []
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
        if k not in translated_keys:
            batch4.append((k, s))
            if len(batch4) == 10000:
                break
    if len(batch4) == 10000:
        break

print(f"Total pure dialogues extracted for Batch 4: {len(batch4)}")

# Save full clean batch 4
full_b4_dict = dict(batch4)
b4_full_path = os.path.join(viet_dir, r"work\batches\batch_10000_avg_clean_b4.json")
with open(b4_full_path, "w", encoding="utf-8") as f:
    json.dump(full_b4_dict, f, indent=2, ensure_ascii=False)

# Split into 3 partitions:
# Part A: 3334 items (STm09 + STsp + DP)
# Part B: 3333 items (STev Event Stories)
# Part C: 3333 items (CG Characters & PM Messages)
partA = dict(batch4[:3334])
partB = dict(batch4[3334:6667])
partC = dict(batch4[6667:10000])

print(f"Part A: {len(partA)} items")
print(f"Part B: {len(partB)} items")
print(f"Part C: {len(partC)} items")

partA_path = os.path.join(viet_dir, r"work\batches\batch_10k_b4_partA.json")
partB_path = os.path.join(viet_dir, r"work\batches\batch_10k_b4_partB.json")
partC_path = os.path.join(viet_dir, r"work\batches\batch_10k_b4_partC.json")

with open(partA_path, "w", encoding="utf-8") as f:
    json.dump(partA, f, indent=2, ensure_ascii=False)

with open(partB_path, "w", encoding="utf-8") as f:
    json.dump(partB, f, indent=2, ensure_ascii=False)

with open(partC_path, "w", encoding="utf-8") as f:
    json.dump(partC, f, indent=2, ensure_ascii=False)

print("Batch 4 clean preparation completed successfully!")
