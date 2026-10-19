import json
from pathlib import Path

entries = Path('StellaSora_VietHoa/work/research/data_en_original/entries')
with open(entries / '00765_0x733ee8fdb8a6a976.bin', 'r', encoding='utf-8') as f:
    cn_dchar = json.load(f)
with open('StellaSora_VietHoa/work/polish/phase3_dataset.json', 'r', encoding='utf-8') as f:
    dchar = json.load(f)['DatingCharacterEvent']

out = []
for it in dchar:
    k = it['key']
    en = it['en']
    cn = cn_dchar.get(k, '')
    vi = it['vi_current']
    out.append(f"[{k}]")
    out.append(f"  EN: {en}")
    out.append(f"  CN: {cn}")
    out.append(f"  VI: {vi}")
    out.append("")

with open('StellaSora_VietHoa/tools/dchar_all_670.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))

print(f"Exported {len(dchar)} DatingCharacter entries to dchar_all_670.txt")
