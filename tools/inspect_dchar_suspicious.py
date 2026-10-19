import json
from pathlib import Path

with open('StellaSora_VietHoa/work/polish/phase3_dataset.json', 'r', encoding='utf-8') as f:
    dchar = json.load(f)['DatingCharacterEvent']
with open('StellaSora_VietHoa/work/research/data_en_original/entries/00765_0x733ee8fdb8a6a976.bin', 'r', encoding='utf-8') as f:
    cn_dchar = json.load(f)

dchar_map = {it['key']: it for it in dchar}

keys_to_inspect = [
    'DatingCharacterEvent.103303.1',
    'DatingCharacterEvent.103303.2',
    'DatingCharacterEvent.103303.3',
    'DatingCharacterEvent.103303.5',
    'DatingCharacterEvent.107301.1',
    'DatingCharacterEvent.107301.3',
    'DatingCharacterEvent.126303.3',
    'DatingCharacterEvent.127303.2',
    'DatingCharacterEvent.140301.5',
    'DatingCharacterEvent.147303.2',
    'DatingCharacterEvent.156301.2',
    'DatingCharacterEvent.156301.5',
    'DatingCharacterEvent.156301.7',
    'DatingCharacterEvent.156303.2',
]

for k in keys_to_inspect:
    it = dchar_map.get(k)
    if it:
        print(f"[{k}]")
        print(f"  EN: {it['en']}")
        print(f"  CN: {cn_dchar.get(k, '')}")
        print(f"  VI: {it['vi_current']}\n")
