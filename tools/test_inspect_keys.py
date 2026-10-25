import json
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
entries_dir = ROOT / "work" / "research" / "data_decrypted" / "entries"

for prefix in ['00553', '00582', '00591', '00635', '00661']:
    files = list(entries_dir.glob(f"{prefix}_*.bin"))
    if files:
        f = files[0]
        data = json.loads(f.read_text(encoding='utf-8'))
        sample_keys = list(data.keys())[:3]
        print(f"{f.name}: {len(data)} items. Sample keys: {sample_keys}")
        for k in sample_keys:
            print(f"  {k} = {repr(data[k])[:80]}")
