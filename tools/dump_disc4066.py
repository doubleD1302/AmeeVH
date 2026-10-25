import json

data = json.load(open(r'StellaSora_VietHoa\work\editorial\final_cg_npc_and_disc_editorial_20261025_r01\cg_disc4066_raw.json', encoding='utf-8'))
print(f'Total items: {len(data)}')
with open(r'StellaSora_VietHoa\tools\cg_disc4066_dump.txt', 'w', encoding='utf-8') as f:
    for it in data:
        f.write(f"{it['id']} \t {it['tokens']} \t {it['en']}\n")
print('Dumped to tools/cg_disc4066_dump.txt')
