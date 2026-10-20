import json
import re
from pathlib import Path
from build_translation_dict import MAPPING, all_en

unmapped = [s for s in all_en if s not in MAPPING]
print(f"Unmapped: {len(unmapped)}")

# Check survival champ
for s in unmapped[:]:
    m1 = re.match(r"^Season (\d+) Survival Champ$", s)
    if m1:
        MAPPING[s] = f"Quán Quân Sinh Tồn Mùa {m1.group(1)}"
        unmapped.remove(s)
        continue
    m2 = re.match(r"^The proof of holding the line in Cataclysm Survivor Season (\d+)!$", s)
    if m2:
        MAPPING[s] = f"Minh chứng kiên cường giữ vững phòng tuyến trong Mùa {m2.group(1)} - Sinh Tồn Đại Họa!"
        unmapped.remove(s)
        continue
    m3 = re.match(r"^Unlocks the Honor Title: Season (\d+) Survival Champ\.$", s)
    if m3:
        MAPPING[s] = f"Mở khóa Danh Hiệu Danh Dự: Quán Quân Sinh Tồn Mùa {m3.group(1)}."
        unmapped.remove(s)
        continue

print(f"After survival champ, unmapped: {len(unmapped)}")
