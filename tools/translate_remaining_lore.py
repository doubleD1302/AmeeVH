import json
import os
import sys

viet_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa"
sys.path.insert(0, os.path.join(viet_dir, "tools"))
from pipeline_translator_engine import translate_batch, post_process_vietnamese, load_master_glossary

terms, forbidden = load_master_glossary()

fpath = os.path.join(viet_dir, r"work\research\data_decrypted\entries\00527_0x843b3b0812018dd2.bin")
with open(fpath, "r", encoding="utf-8") as f:
    d = json.load(f)

lore_keys = [
    "CharacterArchiveContent.11713.2",
    "CharacterArchiveContent.11812.2",
    "CharacterArchiveContent.14007.2",
    "CharacterArchiveContent.14910.2",
    "CharacterArchiveContent.15012.2",
    "CharacterArchiveContent.15612.2"
]

to_trans = [d[k] for k in lore_keys if k in d]
print(f"Translating {len(to_trans)} character lore stories...")

res = translate_batch(to_trans)
for k, trans in zip(lore_keys, res):
    polished = post_process_vietnamese(trans, terms, forbidden)
    d[k] = polished
    print(f"  [{k}] -> {polished[:60]}...")

with open(fpath, "w", encoding="utf-8") as f:
    json.dump(d, f, ensure_ascii=False, indent=2)

# Also fix ActivityLevelsLevel.2010108.1
act_lvl_path = os.path.join(viet_dir, r"work\research\data_decrypted\entries\00501_0x3ba5283f46becc56.bin")
with open(act_lvl_path, "r", encoding="utf-8") as f:
    act_d = json.load(f)
if "ActivityLevelsLevel.2010108.1" in act_d:
    act_d["ActivityLevelsLevel.2010108.1"] = "Khúc Thánh Ca & Chiếc Bếp Kỳ Lạ Ⅰ"
    with open(act_lvl_path, "w", encoding="utf-8") as f:
        json.dump(act_d, f, ensure_ascii=False, indent=2)
    print("Fixed ActivityLevelsLevel.2010108.1")

print("Character lore stories and remaining levels updated successfully!")
