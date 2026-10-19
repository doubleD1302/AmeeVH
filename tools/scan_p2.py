import json
import os

p2_path = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\batches\pillar2_voices_characters.json"
entries_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\research\data_decrypted\entries"

with open(p2_path, "r", encoding="utf-8") as f:
    p2_data = json.load(f)

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

print("Scanning Pillar 2 tables...")

# 1. CharacterSkin
skin_en = p2_data.get("CharacterSkin", {}).get("entries", {})
skin_cn = get_cn_dict("CharacterSkin")
skins = {}
for k, v in skin_en.items():
    if k.endswith(".1"): # Skin name
        skins[v] = skin_cn.get(k, "")

print(f"\nTotal Character Skins: {len(skins)}")
for en, cn in list(skins.items())[:25]:
    print(f"  Skin: {en:35} | CN: {cn}")

# 2. CharacterArchiveVoice categories / cue names
voice_en = p2_data.get("CharacterArchiveVoice", {}).get("entries", {})
voice_cn = get_cn_dict("CharacterArchiveVoice")
voice_cues = {}
for k, v in voice_en.items():
    if k.endswith(".1"):
        if v not in voice_cues:
            voice_cues[v] = voice_cn.get(k, "")

print(f"\nUnique CharacterArchiveVoice cue titles: {len(voice_cues)}")
for en, cn in list(voice_cues.items())[:30]:
    print(f"  Cue: {en:35} | CN: {cn}")

# 3. CharacterArchiveBaseInfo fields
baseinfo_en = p2_data.get("CharacterArchiveBaseInfo", {}).get("entries", {})
baseinfo_cn = get_cn_dict("CharacterArchiveBaseInfo")
fields = set()
for k, v in baseinfo_en.items():
    if k.endswith(".1"):
        fields.add(v)
print(f"\nCharacterArchiveBaseInfo field titles: {fields}")

# 4. CharacterTag
tag_en = p2_data.get("CharacterTag", {}).get("entries", {})
tag_cn = get_cn_dict("CharacterTag")
tags = {}
for k, v in tag_en.items():
    if k.endswith(".1"):
        tags[v] = tag_cn.get(k, "")
print(f"\nCharacterTag titles: {tags}")
