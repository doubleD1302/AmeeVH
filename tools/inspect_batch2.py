import json

data = json.load(open('work/research/data_decrypted/entries/00704_0x87cc29ac0defc2d9.bin', encoding='utf-8'))
for group in ['Settings_', 'Friend_', 'Mall_', 'Gacha_', 'Depot_', 'Battle_', 'StarTower_', 'Activity_']:
    items = {k: v for k, v in data.items() if k.startswith(f'UIText.{group}')}
    print(f'=== {group} ({len(items)} items) ===')
    for k, v in list(items.items())[:10]:
        print(f'  {k} = {repr(v)}')
