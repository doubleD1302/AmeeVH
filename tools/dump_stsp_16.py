import json

with open(r'c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\editorial\side_stories_part2_editorial_20261025_r01\PARTITION_B_SOURCE.json', 'r', encoding='utf-8') as f:
    items = json.load(f)

for s_id in ['STsp_16_01', 'STsp_16_02', 'STsp_16_03']:
    print(f"==================== {s_id} ====================")
    scene_items = [it for it in items if it['scene_id'] == s_id]
    for it in scene_items:
        print(f"[{it['id']}] EN: {it['en']}")
        print(f"         VI: {it.get('current_vi')}\n")
