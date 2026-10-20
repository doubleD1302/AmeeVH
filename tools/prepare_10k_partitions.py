import json
import os

viet_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa"
full_batch_path = os.path.join(viet_dir, r"work\batches\batch_10000_avg_clean.json")

with open(full_batch_path, "r", encoding="utf-8") as f:
    all_data = json.load(f)

print(f"Total items in batch: {len(all_data)}")

partA = {}
partB = {}
partC = {}

for k, v in all_data.items():
    prefix = k.split(".")[0]
    if prefix.startswith("BBm") or prefix.startswith("STm01") or prefix.startswith("STm02"):
        partA[k] = v
    elif prefix.startswith("STm03") or prefix.startswith("PM"):
        partB[k] = v
    else:
        partC[k] = v

print(f"Part A (Main Story 1, 2 & Prologue): {len(partA)} items")
print(f"Part B (Main Story 3 & Phone Messages): {len(partB)} items")
print(f"Part C (Character Stories CG): {len(partC)} items")
print(f"Total: {len(partA) + len(partB) + len(partC)} items")

partA_path = os.path.join(viet_dir, r"work\batches\batch_10k_partA_mainstory1_2.json")
partB_path = os.path.join(viet_dir, r"work\batches\batch_10k_partB_mainstory3_phone.json")
partC_path = os.path.join(viet_dir, r"work\batches\batch_10k_partC_character_stories.json")

with open(partA_path, "w", encoding="utf-8") as f:
    json.dump(partA, f, indent=2, ensure_ascii=False)

with open(partB_path, "w", encoding="utf-8") as f:
    json.dump(partB, f, indent=2, ensure_ascii=False)

with open(partC_path, "w", encoding="utf-8") as f:
    json.dump(partC, f, indent=2, ensure_ascii=False)

print("Saved all 3 partition files successfully!")
