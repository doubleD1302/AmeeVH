import os
import json
import re
import sys

viet_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa"
sys.path.insert(0, os.path.join(viet_dir, "tools"))
from extract_clean_10k_avg import extract_clean_lua53_strings

b1 = json.load(open(os.path.join(viet_dir, r"work\batches\batch_10000_avg_clean.json"), encoding="utf-8"))
b2 = json.load(open(os.path.join(viet_dir, r"work\batches\batch_10000_avg_clean_b2.json"), encoding="utf-8"))
b3 = json.load(open(os.path.join(viet_dir, r"work\batches\batch_10000_avg_clean_b3.json"), encoding="utf-8"))
b4 = json.load(open(os.path.join(viet_dir, r"work\batches\batch_10000_avg_clean_b4.json"), encoding="utf-8"))

all_translated = set(b1.keys()) | set(b2.keys()) | set(b3.keys()) | set(b4.keys())
print(f"Total story dialogues translated across Batch 1-4: {len(all_translated):,}")

lua_config_dir = os.path.join(viet_dir, r"work\research\lua_tree\Game\UI\Avg\_en\Config")
all_files = sorted(os.listdir(lua_config_dir))

def is_genuine_dialogue(s):
    s_strip = s.strip()
    if not s_strip or len(s_strip) < 2: return False
    if re.match(r"^[a-zA-Z0-9_]+$", s_strip) and " " not in s_strip: return False
    prefixes = ("ep_", "fx_", "story_", "white_", "black_", "Set", "Play", "avg", "bg_", "item_", "icon_", "eff_", "cam_", "ui_", "vo_", "se_", "snd_", "res_", "prefab_", "spine_", "ttc_", "btn_", "bgm_", "bgs_", "img_", "tex_")
    if s_strip.startswith(prefixes): return False
    if not any(c.isalpha() for c in s_strip): return False
    if " " in s_strip or any(p in s_strip for p in [".", "!", "?", ",", "…", ":", ";", "—", "-"]): return True
    return False

remaining_by_prefix = {}
total_remaining = 0

for f in all_files:
    if not f.endswith(".lua"): continue
    prefix = f.split("_")[0]
    fpath = os.path.join(lua_config_dir, f)
    slist = extract_clean_lua53_strings(fpath)
    base = f[:-4]
    for idx, s in enumerate(slist):
        if not is_genuine_dialogue(s): continue
        k = f"{base}.{idx+1}"
        if k not in all_translated:
            total_remaining += 1
            remaining_by_prefix[prefix] = remaining_by_prefix.get(prefix, 0) + 1

print(f"\nTOTAL GENUINE STORY DIALOGUES REMAINING IN GAME: {total_remaining:,}")
print("Breakdown by prefix:")
for p, c in sorted(remaining_by_prefix.items(), key=lambda x: -x[1]):
    print(f"  {p}: {c:,} lines")
