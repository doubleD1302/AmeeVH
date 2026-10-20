import json
import os
import re

viet_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa"
data_dec = os.path.join(viet_dir, r"work\research\data_decrypted\entries")

untranslated_tables = []

for fname in os.listdir(data_dec):
    if not fname.endswith(".bin"):
        continue
    fpath = os.path.join(data_dec, fname)
    try:
        with open(fpath, "r", encoding="utf-8") as f:
            content = json.load(f)
        if not isinstance(content, dict):
            continue
        
        sample_vals = [v for v in content.values() if isinstance(v, str) and v.strip()]
        if not sample_vals:
            continue
        first_few = "".join(sample_vals[:5])
        cn_chars = len(re.findall(r'[\u4e00-\u9fff]', first_few))
        if cn_chars > len(first_few) * 0.3:
            continue
        
        en_strings = {}
        for k, v in content.items():
            if not isinstance(v, str) or not v.strip():
                continue
            s = v.strip()
            # If contains English letters and NOT Vietnamese diacritics
            has_vi = bool(re.search(r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ]', s))
            has_en = bool(re.search(r'[a-zA-Z]{2,}', s))
            # Also check if it's not a pure URL/asset path
            if has_en and not has_vi and not s.startswith("http") and not (s.startswith("Assets/") or s.startswith("UI/") or s.startswith("Audio/") or s.startswith("Prefabs/")):
                en_strings[k] = s
        
        if en_strings:
            first_k = next(iter(content.keys()), "")
            cat = first_k.split(".")[0] if "." in first_k else fname
            untranslated_tables.append({
                "file": fname,
                "category": cat,
                "total_rows": len(content),
                "untranslated_count": len(en_strings),
                "entries": en_strings
            })
    except Exception as e:
        pass

untranslated_tables.sort(key=lambda x: x["untranslated_count"], reverse=True)

out_file = os.path.join(viet_dir, r"work\batches\latest_resources_breakdown.json")
with open(out_file, "w", encoding="utf-8") as f:
    json.dump(untranslated_tables, f, indent=2, ensure_ascii=False)

print(f"Saved {len(untranslated_tables)} tables with {sum(x['untranslated_count'] for x in untranslated_tables)} strings to {out_file}")
for t in untranslated_tables[:25]:
    print(f"  {t['category']:30s} | {t['file']} | {t['untranslated_count']:5d} strings")
