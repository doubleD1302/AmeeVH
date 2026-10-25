# -*- coding: utf-8 -*-
import json
from pathlib import Path
import re

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
rem = json.load(open(ROOT / "work/batches/remaining_lua_avg_cache.json", encoding="utf-8"))

names_check = {
    'Bloc': ['Khối', 'khối'],
    'Willow': ['Liễu', 'liễu', 'Cây Liễu'],
    'Firefly': ['Đom đóm', 'đom đóm'],
    'Amber': ['Hổ phách', 'hổ phách'],
    'Daisy': ['Hoa cúc', 'hoa cúc'],
    'Ginger': ['Gừng', 'gừng'],
    'Pepper': ['Hạt tiêu', 'hạt tiêu'],
    'Summer': ['Mùa hè', 'mùa hè'],
    'Winter': ['Mùa đông', 'mùa đông'],
    'Snow': ['Tuyết', 'tuyết'],
    'Rose': ['Hoa hồng', 'hoa hồng'],
    'Iris': ['Hoa Diên Vĩ', 'Diên Vĩ'],
    'Flora': ['Hệ thực vật', 'thực vật'],
    'Robin': ['Chim sẻ', 'chim sẻ', 'chim oanh'],
    'Gale': ['Gió lốc', 'cơn gió lốc'],
    'Shadow': ['Bóng râm', 'bóng ma'],
}

found_names = {}
for en, vi in rem.items():
    for name, bad_list in names_check.items():
        if re.search(r'\b' + name + r'\b', en):
            for bad in bad_list:
                if re.search(r'\b' + bad + r'\b', vi):
                    found_names.setdefault(name, []).append((en, vi, bad))
                    break

for name, items in found_names.items():
    print(f"Name '{name}': {len(items)} suspicious lines")
    for s_en, s_vi, s_bad in items[:2]:
        print(f"   [Found: {s_bad}]")
        print(f"   EN: {s_en}")
        print(f"   VI: {s_vi}")
