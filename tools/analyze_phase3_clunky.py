import json
import re
from pathlib import Path
from collections import Counter

data_path = Path("StellaSora_VietHoa/work/polish/phase3_dataset.json")
with open(data_path, "r", encoding="utf-8") as f:
    data = json.load(f)

clunky_patterns = [
    'sao nhổ',
    'có thể được',
    'được sử dụng',
    'được áp dụng',
    'thực hiện việc',
    'nó giải phóng',
    'bị chôn vùi',
    'chạm vào để',
    'nhấp vào',
    'được cấp',
    'được nhận',
    'tăng lên bởi',
    'giảm đi bởi',
    'gây ra bởi',
    'được kích hoạt bởi',
    'ở một mình trong',
    'những tài năng',
    'vùng hoang dã',
    'được tạo ra',
    'được coi là',
    'chuyến thám hiểm',
    'trại trẻ mồ côi',
    'lữ khách',
    'lữ đoàn',
    'tân tinh',
    'giai điệu',
    'khu bảo tồn',
    'thánh địa',
    'thăng thiên',
]

print("=== PHASE 3 STATS ===")
for tname, items in data.items():
    print(f"\n--- {tname} ({len(items)} items) ---")
    clunky_found = Counter()
    untrans = 0
    token_count = 0
    for it in items:
        en = it['en']
        vi = it['vi_current']
        if en == vi:
            untrans += 1
        vi_l = vi.lower()
        for p in clunky_patterns:
            if p in vi_l:
                clunky_found[p] += 1
        if re.search(r'\{[0-9a-zA-Z_]+\}|<[^>]+>|&[0-9a-zA-Z_]+&|==[A-Z0-9_]+==', en):
            token_count += 1

    print(f"  Untranslated / identical to EN: {untrans}")
    print(f"  Items with tokens/tags: {token_count}")
    if clunky_found:
        print(f"  Clunky patterns detected:")
        for pat, cnt in clunky_found.most_common(10):
            print(f"    - '{pat}': {cnt}")
