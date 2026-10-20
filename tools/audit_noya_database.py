import json
import os
import re

viet_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa"
dump_path = os.path.join(viet_dir, r"work\reviews\all_noya_entries.json")
with open(dump_path, "r", encoding="utf-8") as f:
    noya_data = json.load(f)

print("=" * 70)
print("AUDIT: All Entries Related to Noya (ID 112)")
print("=" * 70)

issues = []
total_entries = 0

for cat, items in noya_data.items():
    for item in items:
        total_entries += 1
        k = item["key"]
        v = item["value"]
        fname = item["file"]
        
        # Check for English fragments
        words = re.findall(r'[a-zA-Z]{2,}', re.sub(r'<[^>]+>|\{[^}]+\}|&[^&]+&', '', v))
        has_vi = bool(re.search(r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ]', v))
        
        # Whitelisted proper words
        filtered_words = [w for w in words if w not in [
            "Noya", "Amber", "Iris", "Tilia", "Dorra", "HP", "ATK", "DEF", "DMG", "CRIT", "CD", "MP", "SP", "Lv", "Ann", "Canace", "Fuyuka", "Stella", "StellaSora", "PS4_L1", "XboxOne_LB", "Q"
        ]]
        
        # Check for clunky phrases
        clunky_phrases = [
            "bản dựng", "kẻ thù", "được gánh chịu", "thực hiện đòn đánh",
            "cast", "bằng đòn tấn công tự động", "con chip", "Dragon Slash"
        ]
        has_clunky = any(cp in v.lower() for cp in clunky_phrases)
        
        if (filtered_words and not has_vi) or has_clunky or "cast" in v:
            issues.append({
                "category": cat,
                "file": fname,
                "key": k,
                "value": v,
                "reason": "English fragment" if (filtered_words and not has_vi) else "Clunky translation"
            })

print(f"Total Noya entries audited: {total_entries}")
print(f"Entries needing polish/repair: {len(issues)}")

print("\nSample entries needing repair:")
for iss in issues[:25]:
    print(f"[{iss['category']}] {iss['key']} ({iss['reason']}):")
    print(f"   {iss['value']}")
