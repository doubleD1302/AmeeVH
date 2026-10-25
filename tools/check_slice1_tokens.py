import json

items = json.load(open('StellaSora_VietHoa/work/editorial/tutorial_and_character_cg_editorial_20261025_r01/SLICE1_SOURCE.json', encoding='utf-8'))
tokened = [it for it in items if it['tokens']]
print(f'Items with tokens: {len(tokened)}')
for it in tokened:
    print(f"{it['id']}: tokens={it['tokens']} | text={it['en'][:70]}")
