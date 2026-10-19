import json

p3 = json.load(open('c:/YostarGames/StellaSora_EN/StellaSora_VietHoa/work/batches/pillar3_translated.json', encoding='utf-8'))
p4 = json.load(open('c:/YostarGames/StellaSora_EN/StellaSora_VietHoa/work/batches/pillar4_translated.json', encoding='utf-8'))

s3 = sum(len(v.get('entries', {})) for v in p3.values())
s4 = sum(len(v.get('entries', {})) for v in p4.values())

print(f'Pillar 3: {len(p3)} tables, {s3} strings')
print(f'Pillar 4: {len(p4)} tables, {s4} strings')
print(f'Total: {len(p3) + len(p4)} tables, {s3 + s4} strings')

print('\nPillar 3 tables:')
for t, d in p3.items():
    print(f'  {t}: {len(d.get("entries", {}))}')

print(f'\nPillar 4 tables ({len(p4)} total):')
for t, d in list(p4.items()):
    print(f'  {t}: {len(d.get("entries", {}))}')
