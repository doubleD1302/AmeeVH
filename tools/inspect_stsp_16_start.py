import json

with open(r'c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\editorial\side_stories_part2_editorial_20261025_r01\PARTITION_B_SOURCE.json', 'r', encoding='utf-8') as f:
    items = json.load(f)

for it in items:
    if it['scene_id'] == 'STsp_16_01' and int(it['id'].split('.')[-1]) <= 30:
        print(f"{it['id']}: EN: {it['en']}")
        print(f"   VI: {it.get('current_vi')}\n")
