import json
import re

with open('StellaSora_VietHoa/work/subagents/remediation_v110_20261029_r01/story/unique_binary_132.json', 'r', encoding='utf-8') as f:
    items = json.load(f)

# Let's inspect the types of commands and tokens
tokens = set()
for it in items:
    for text in (it['en'], it['vi']):
        # find sequences of printable chars preceded by \x04 or \x14
        m = re.findall(r'[\x04\x14][\x00-\x7f]([a-zA-Z0-9_\-\.]+)', text)
        for tok in m:
            tokens.add(tok)

print("Sample tokens found:", sorted(list(tokens))[:50])
