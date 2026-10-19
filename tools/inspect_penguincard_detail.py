import json
from pathlib import Path

entries = Path('StellaSora_VietHoa/work/research/data_en_original/entries')
with open(entries / '00833_0x469c8ae265bf9745.bin', 'r', encoding='utf-8') as f:
    cn_peng = json.load(f)
with open('StellaSora_VietHoa/work/polish/phase3_dataset.json', 'r', encoding='utf-8') as f:
    p3 = json.load(f)['PenguinCard']

names = [it for it in p3 if it['key'].endswith('.1')]
descs = [it for it in p3 if it['key'].endswith('.2')]

print(f"PenguinCard total: {len(p3)}, Names: {len(names)}, Descs: {len(descs)}")

print("\n--- Sample Names (with CN) ---")
for it in names[:20]:
    cn = cn_peng.get(it['key'], '')
    print(f"[{it['key']}] EN: '{it['en']}' | CN: '{cn}' | VI: '{it['vi_current']}'")

print("\n--- Sample Descs (with CN) ---")
for it in descs[:15]:
    cn = cn_peng.get(it['key'], '')
    print(f"[{it['key']}]")
    print(f"  EN: {it['en']}")
    print(f"  CN: {cn}")
    print(f"  VI: {it['vi_current']}")
