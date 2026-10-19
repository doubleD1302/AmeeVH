import json
import os

p3_path = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\batches\pillar3_story_dating_quests.json"
entries_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\research\data_decrypted\entries"

with open(p3_path, "r", encoding="utf-8") as f:
    p3_data = json.load(f)

# Find CN tables directly
cn_tables = {}
for fname in os.listdir(entries_dir):
    if not fname.endswith(".bin"):
        continue
    fpath = os.path.join(entries_dir, fname)
    try:
        with open(fpath, "r", encoding="utf-8") as f:
            d = json.load(f)
        if isinstance(d, dict) and len(d) > 0:
            first_k = list(d.keys())[0]
            tbl_name = first_k.split(".")[0]
            first_v = str(list(d.values())[0])
            has_cn = any(u'\u4e00' <= ch <= u'\u9fff' for ch in first_v)
            if has_cn:
                cn_tables[tbl_name] = fpath
    except Exception:
        pass

def get_cn_dict(tbl_name):
    p = cn_tables.get(tbl_name)
    if p and os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

print("Scanning Pillar 3 tables...")

# 1. DatingLandmark
dl_en = p3_data.get("DatingLandmark", {}).get("entries", {})
dl_cn = get_cn_dict("DatingLandmark")
landmarks = {}
for k, v in dl_en.items():
    if k.endswith(".1"):
        landmarks[v] = dl_cn.get(k, "")
print(f"\nDatingLandmarks ({len(landmarks)}):")
for en, cn in landmarks.items():
    print(f"  Landmark: {en:30} | CN: {cn}")

# 2. NPCConfig
npc_en = p3_data.get("NPCConfig", {}).get("entries", {})
npc_cn = get_cn_dict("NPCConfig")
npcs = {}
for k, v in npc_en.items():
    if k.endswith(".1"):
        npcs[v] = npc_cn.get(k, "")
print(f"\nNPCs ({len(npcs)}):")
for en, cn in npcs.items():
    print(f"  NPC: {en:30} | CN: {cn}")

# 3. StoryChapter & StorySetChapter
sc_en = p3_data.get("StoryChapter", {}).get("entries", {})
sc_cn = get_cn_dict("StoryChapter")
print(f"\nStoryChapters ({len(sc_en)//3}):")
for k, v in sc_en.items():
    if k.endswith(".2"): # chapter title
        print(f"  Chapter: {v:30} | CN: {sc_cn.get(k, '')}")

ssc_en = p3_data.get("StorySetChapter", {}).get("entries", {})
ssc_cn = get_cn_dict("StorySetChapter")
print(f"\nStorySetChapters ({len(ssc_en)//2}):")
for k, v in ssc_en.items():
    if k.endswith(".2"):
        print(f"  Set Chapter: {v:35} | CN: {ssc_cn.get(k, '')}")

# 4. NPCAffinityPlot
nap_en = p3_data.get("NPCAffinityPlot", {}).get("entries", {})
nap_cn = get_cn_dict("NPCAffinityPlot")
print(f"\nNPCAffinityPlots ({len(nap_en)//2}):")
for k, v in nap_en.items():
    if k.endswith(".2"):
        print(f"  Affinity Plot: {v:30} | CN: {nap_cn.get(k, '')}")
