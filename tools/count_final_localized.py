import json
import os
import re

viet_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa"
data_dec = os.path.join(viet_dir, r"work\research\data_decrypted\entries")

total_strings = 0
total_vi_strings = 0
tables_with_vi = 0

for fname in sorted(os.listdir(data_dec)):
    if not fname.endswith(".bin"):
        continue
    fpath = os.path.join(data_dec, fname)
    with open(fpath, "r", encoding="utf-8") as fp:
        try:
            d = json.load(fp)
        except Exception:
            continue
    if not isinstance(d, dict) or not d:
        continue
    
    # Check if this is CN table
    sample_text = " ".join([v for v in d.values() if isinstance(v, str)][:15])
    cn_chars = len(re.findall(r'[\u4e00-\u9fff]', sample_text))
    if cn_chars > 15:
        continue
    
    table_has_vi = False
    for k, v in d.items():
        if not isinstance(v, str) or not v.strip():
            continue
        total_strings += 1
        has_vi = bool(re.search(r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ]', v))
        if has_vi:
            total_vi_strings += 1
            table_has_vi = True
    
    if table_has_vi:
        tables_with_vi += 1

print(f"Total EN/VI Localization Tables: {tables_with_vi}")
print(f"Total Localized Strings in Game: {total_vi_strings} / {total_strings} ({total_vi_strings/total_strings*100:.2f}%)")
