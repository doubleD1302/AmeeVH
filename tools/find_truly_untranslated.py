import json
import os
import re

viet_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa"
data_dec = os.path.join(viet_dir, r"work\research\data_decrypted\entries")

# Check map_en_cn_tables.py or check how tables are paired
# Let's inspect the files that belong to EN
en_files = []
cn_files = []

for f in sorted(os.listdir(data_dec)):
    if not f.endswith(".bin"):
        continue
    fpath = os.path.join(data_dec, f)
    with open(fpath, "r", encoding="utf-8") as fp:
        try:
            d = json.load(fp)
            if not isinstance(d, dict) or not d:
                continue
            
            # Check content for CN characters vs Latin characters
            all_text = " ".join([v for v in d.values() if isinstance(v, str)][:20])
            cn_count = len(re.findall(r'[\u4e00-\u9fff]', all_text))
            latin_count = len(re.findall(r'[a-zA-Z]', all_text))
            
            # Extract category name
            first_k = next(iter(d.keys()))
            cat = first_k.split(".")[0] if "." in first_k else f
            
            if cn_count > 10 and cn_count > latin_count * 0.5:
                cn_files.append((f, cat, len(d)))
            else:
                en_files.append((f, cat, len(d)))
        except Exception:
            pass

print(f"EN tables count: {len(en_files)}")
print(f"CN tables count: {len(cn_files)}")

# Now for each EN table, let's find truly untranslated English strings!
# Untranslated means: has English words (letters >= 2) AND NO Vietnamese diacritics
truly_untranslated = []

for f, cat, total_len in en_files:
    fpath = os.path.join(data_dec, f)
    with open(fpath, "r", encoding="utf-8") as fp:
        d = json.load(fp)
    
    untrans = {}
    for k, v in d.items():
        if not isinstance(v, str) or not v.strip():
            continue
        s = v.strip()
        # Exclude technical strings like !NONEED!, !PENDING!, asset paths, URLs, color tags alone
        if s in ["!NONEED!", "!PENDING!", "NONE", "null", "N/A"]:
            continue
        if s.startswith("Assets/") or s.startswith("UI/") or s.startswith("Audio/") or s.startswith("Prefabs/") or s.startswith("http"):
            continue
        # Strip XML/HTML tags before checking language
        stripped = re.sub(r'<[^>]+>', '', s).strip()
        stripped = re.sub(r'\{[0-9]+\}', '', stripped).strip()
        stripped = re.sub(r'&Param[0-9]+&', '', stripped).strip()
        stripped = re.sub(r'#Param[0-9]+#', '', stripped).strip()
        
        has_vi = bool(re.search(r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ]', stripped))
        has_letters = bool(re.search(r'[a-zA-Z]{2,}', stripped))
        
        # If it has English letters and NO Vietnamese letters, it's untranslated!
        if has_letters and not has_vi:
            untrans[k] = s

    if untrans:
        truly_untranslated.append({
            "file": f,
            "category": cat,
            "total_rows": total_len,
            "untranslated_count": len(untrans),
            "entries": untrans
        })

truly_untranslated.sort(key=lambda x: x["untranslated_count"], reverse=True)
total_untrans_strings = sum(x["untranslated_count"] for x in truly_untranslated)
print(f"\nTRULY UNTRANSLATED EN TABLES: {len(truly_untranslated)}")
print(f"TOTAL UNTRANSLATED STRINGS: {total_untrans_strings}")

for t in truly_untranslated[:30]:
    sample = list(t["entries"].items())[:2]
    s_str = " | ".join([f"{k}: {v[:30]}" for k, v in sample])
    print(f"  {t['category']:28s} ({t['file']}) | {t['untranslated_count']:4d} strings | Sample: {s_str}")
