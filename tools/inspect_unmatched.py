import json
from collections import Counter

data = json.load(open('StellaSora_VietHoa/work/batches/cross_referenced_batch3.json', encoding='utf-8'))
unmatched = [d for d in data if not d['candidate']]
print(f"Total unmatched: {len(unmatched)}")

tbls = Counter(d['table'] for d in unmatched)
print("Unmatched by table:", tbls)

for d in unmatched[:20]:
    print(f"[{d['sample_key']}] EN: {d['en']!r} | ZH: {d['zh']!r}")
