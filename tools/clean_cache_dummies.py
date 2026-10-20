import json
import re
import os

viet_dir = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa"
cache_path = os.path.join(viet_dir, r"work\batches\pillars_translation_cache.json")

with open(cache_path, "r", encoding="utf-8") as f:
    cache = json.load(f)

print(f"Total entries before cleaning: {len(cache)}")

cleaned_cache = {}
purged_count = 0

for k, v in cache.items():
    if k == v:
        words = re.findall(r'[a-zA-Z]{2,}', k)
        has_vi = bool(re.search(r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ]', k))
        # Keep single proper nouns like 'Amber', 'Noya', 'Portia'
        if len(words) >= 2 and not has_vi:
            purged_count += 1
            continue
    cleaned_cache[k] = v

print(f"Purged dummy entries: {purged_count}")
print(f"Cleaned cache entries: {len(cleaned_cache)}")

with open(cache_path, "w", encoding="utf-8") as f:
    json.dump(cleaned_cache, f, indent=2, ensure_ascii=False)

print("Saved cleaned cache successfully!")
