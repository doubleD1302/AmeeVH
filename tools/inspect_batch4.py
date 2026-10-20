import json
import os

viet_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa"
b4_path = os.path.join(viet_dir, r"work\batches\batch_10000_avg_clean_b4.json")
with open(b4_path, "r", encoding="utf-8") as f:
    b4 = json.load(f)

files_in_b4 = set()
for k in b4.keys():
    files_in_b4.add(k.split(".")[0])

prefixes = {}
for fn in files_in_b4:
    p = fn.split("_")[0]
    prefixes[p] = prefixes.get(p, 0) + 1

print("Total files in Batch 4:", len(files_in_b4))
print("File breakdown by prefix:", sorted(prefixes.items()))

partA = json.load(open(os.path.join(viet_dir, r"work\batches\batch_10k_b4_partA.json"), encoding="utf-8"))
partB = json.load(open(os.path.join(viet_dir, r"work\batches\batch_10k_b4_partB.json"), encoding="utf-8"))
partC = json.load(open(os.path.join(viet_dir, r"work\batches\batch_10k_b4_partC.json"), encoding="utf-8"))

def get_files(d):
    return sorted(list(set(k.split(".")[0] for k in d.keys())))

print("\nPart A files (count:", len(get_files(partA)), "):", get_files(partA)[:10])
print("\nPart B files (count:", len(get_files(partB)), "):", get_files(partB)[:10])
print("\nPart C files (count:", len(get_files(partC)), "):", get_files(partC)[:10])
