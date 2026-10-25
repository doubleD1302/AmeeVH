import re
from pathlib import Path

entries = Path('StellaSora_VietHoa/work/research/data_200_decrypted/entries')
matched_tables = set()
pattern = re.compile(rb'"([A-Za-z0-9_]+)\.[0-9]+\.[0-9]+"')

for f in entries.glob('*.bin'):
    try:
        data = f.read_bytes()[:1000]
        for tbl in pattern.findall(data):
            tname = tbl.decode('ascii', errors='ignore')
            if 'card' in tname.lower():
                matched_tables.add(tname)
    except Exception:
        pass

print('Matched tables with card:', matched_tables)
