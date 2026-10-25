import json
import re

with open(r'c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\editorial\side_stories_part2_editorial_20261025_r01\PARTITION_B_SOURCE.json', 'r', encoding='utf-8') as f:
    items = json.load(f)

for it in items:
    if it['scene_id'].startswith('STsp_16'):
        en = it['en']
        vi = it.get('current_vi', '')
        if 'giấy tờ' in vi or 'sau đó' in vi.lower() or 'hủy bỏ' in vi:
            print(f"{it['id']}: EN: {en}")
            print(f"   VI: {vi}\n")
