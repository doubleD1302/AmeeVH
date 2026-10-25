import re
import json
from pathlib import Path

entries = Path('StellaSora_VietHoa/work/research/data_200_decrypted/entries')
for f in entries.glob('*.bin'):
    data = f.read_bytes()
    if b'SoldierStrategyCard' in data:
        print('Found in file:', f.name, len(data))
        text = data.decode('utf-8', errors='ignore')
        parsed = json.loads(text)
        print('Total keys:', len(parsed))
        for k in list(parsed.keys())[:15]:
            print(k, '->', parsed[k])
        break
