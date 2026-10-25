# -*- coding: utf-8 -*-
import json
from pathlib import Path
import re

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
rem = json.load(open(ROOT / "work/batches/remaining_lua_avg_cache.json", encoding="utf-8"))

characters = [
    'Noya', 'Amber', 'Bloc', 'Willow', 'Firefly', 'Fuyuka', 'Iris', 'Chitose',
    'Nazuna', 'Teresa', 'Freesia', 'Caterine', 'Donna', 'Karin', 'Eleanor',
    'Nanoha', 'Sharon', 'Tyrrhena', 'Minova', 'Asteria', 'Rainea', 'Allie',
    'Angie', 'Howard', 'Edda', 'Iori', 'Laru', 'Gerie', 'Claude', 'Dorra',
    'Dora', 'Noah', 'Igna', 'Kasiel', 'Lise', 'Shirley', 'Saphir', 'Chloe',
    'Tina', 'Kaguya'
]

missing_names = {}
for en, vi in rem.items():
    for char in characters:
        if re.search(r'\b' + char + r'\b', en):
            if not re.search(r'\b' + char + r'\b', vi, re.IGNORECASE):
                missing_names.setdefault(char, []).append((en, vi))

for char, items in missing_names.items():
    print(f"Character '{char}' missing in VI: {len(items)} lines")
    for s_en, s_vi in items[:2]:
        print(f"   EN: {s_en}")
        print(f"   VI: {s_vi}")
