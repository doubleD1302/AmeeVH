import json
from pathlib import Path
from collections import defaultdict

f = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\batches\untranslated_unique.json")
data = json.loads(f.read_text(encoding="utf-8"))

by_table = defaultdict(list)
for item in data:
    tables = {occ[0] for occ in item["occurrences"]}
    for t in tables:
        by_table[t].append(item["en"])

for t, lst in by_table.items():
    print(f"Table {t}: {len(lst)} unique strings")
