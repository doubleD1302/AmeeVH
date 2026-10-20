import json
import os
import re

viet_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa"
data_dec = os.path.join(viet_dir, r"work\research\data_decrypted\entries")
data_en = os.path.join(viet_dir, r"work\research\data_en_original\entries")

# Check all EN/VI files in data_dec
# A file is EN/VI if it does NOT contain mostly CN characters
untranslated_summary = []

for fname in os.listdir(data_dec):
    if not fname.endswith(".bin"):
        continue
    fpath = os.path.join(data_dec, fname)
    try:
        with open(fpath, "r", encoding="utf-8") as f:
            content = json.load(f)
        if not isinstance(content, dict):
            continue
        
        # Check if this is a CN table
        sample_vals = [v for v in content.values() if isinstance(v, str) and v.strip()]
        if not sample_vals:
            continue
        first_few = "".join(sample_vals[:5])
        cn_chars = len(re.findall(r'[\u4e00-\u9fff]', first_few))
        if cn_chars > len(first_few) * 0.3:
            # This is a CN table
            continue
        
        # This is an EN/VI table. Count English strings vs Vietnamese strings
        en_strings = []
        vi_strings = []
        for k, v in content.items():
            if not isinstance(v, str) or not v.strip():
                continue
            s = v.strip()
            # If contains Vietnamese diacritics
            has_vi = bool(re.search(r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ]', s))
            has_en = bool(re.search(r'[a-zA-Z]{2,}', s))
            if has_vi:
                vi_strings.append((k, s))
            elif has_en:
                # English or untranslated
                en_strings.append((k, s))
        
        if en_strings:
            prefix = fname
            first_k = next(iter(content.keys()), "")
            cat = first_k.split(".")[0] if "." in first_k else fname
            untranslated_summary.append({
                "file": fname,
                "category": cat,
                "total": len(content),
                "vi_count": len(vi_strings),
                "en_count": len(en_strings),
                "samples": en_strings[:3]
            })
    except Exception as e:
        pass

untranslated_summary.sort(key=lambda x: x["en_count"], reverse=True)
print(f"Total tables with English strings remaining: {len(untranslated_summary)}")
total_en = sum(x["en_count"] for x in untranslated_summary)
print(f"Total English strings remaining in data.arcx: {total_en}")

print("\nTop 40 tables with English strings:")
for item in untranslated_summary[:40]:
    samps = " | ".join([f"{k}: {s[:30]}" for k, s in item["samples"][:2]])
    print(f"{item['category']:30s} ({item['file']}) | EN: {item['en_count']:5d} / {item['total']:5d} | Samples: {samps[:60]}")
