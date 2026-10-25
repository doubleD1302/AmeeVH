import json

items = json.load(open('StellaSora_VietHoa/work/editorial/tutorial_and_character_cg_editorial_20261025_r01/SLICE1_SOURCE.json', encoding='utf-8'))
for scene in ['STm10001_01', 'STm10001_02', 'STm10001_03']:
    scene_items = [it for it in items if it['scene_id'] == scene]
    with open(f'StellaSora_VietHoa/tools/{scene}_en.txt', 'w', encoding='utf-8') as f:
        for it in scene_items:
            f.write(f"{it['id']} \t {it['tokens']} \t {it['en']}\n")
print('Successfully dumped scene EN files.')
