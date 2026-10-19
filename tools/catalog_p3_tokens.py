import json
import re
from pathlib import Path
from collections import Counter

data_path = Path("StellaSora_VietHoa/work/polish/phase3_dataset.json")
with open(data_path, "r", encoding="utf-8") as f:
    data = json.load(f)

token_patterns = [
    r'\{[0-9a-zA-Z_]+\}',
    r'<color=[^>]+>',
    r'</color>',
    r'<sprite=[^>]+>',
    r'<sprite [^>]+>',
    r'<b>',
    r'</b>',
    r'<i>',
    r'</i>',
    r'&[0-9a-zA-Z_]+&',
    r'==[A-Z0-9_]+=='
]

combined_pat = re.compile('|'.join(f'({p})' for p in token_patterns))

total_tokens = 0
table_tokens = Counter()

for tname, items in data.items():
    for it in items:
        en = it['en']
        matches = combined_pat.findall(en)
        if matches:
            table_tokens[tname] += len(matches)
            total_tokens += len(matches)

print(f"Total tokens found in EN across Phase 3: {total_tokens}")
for tname, cnt in table_tokens.most_common():
    print(f"  {tname}: {cnt} tokens")
