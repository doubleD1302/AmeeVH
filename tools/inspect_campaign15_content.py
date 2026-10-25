# -*- coding: utf-8 -*-
import json
from pathlib import Path
from collections import Counter
import re

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
CAMPAIGN_DIR = ROOT / "work/editorial/event_stories_part3_editorial_20261025_r01"

with open(CAMPAIGN_DIR / "CAMPAIGN_15_SOURCE_ALL.json", "r", encoding="utf-8") as f:
    items = json.load(f)

print(f"Loaded {len(items)} items.")

# 1. Analyze tokens
tokens_counter = Counter()
for it in items:
    for t in it['tokens']:
        tokens_counter[t] += 1

print("\nTop 20 tokens in Campaign 15:")
for t, cnt in tokens_counter.most_common(20):
    print(f"  {t}: {cnt}")

# 2. Check unclosed size tags
unclosed_sizes = []
for it in items:
    en = it['en']
    open_sizes = re.findall(r'<size=[^>]+>', en)
    close_sizes = re.findall(r'</size>', en)
    if len(open_sizes) > len(close_sizes):
        unclosed_sizes.append((it['id'], open_sizes))
print(f"\nLines with unclosed <size=XX> tags: {len(unclosed_sizes)}")
for iid, sz in unclosed_sizes:
    print(f"  {iid}: {sz}")

# 3. Check binary control opcodes
opcodes = []
for it in items:
    en = it['en']
    if any(ord(c) < 32 and c not in '\n\r\t' for c in en):
        opcodes.append((it['id'], repr(en[:30])))
print(f"\nBinary opcode lines: {len(opcodes)}")
for iid, op in opcodes:
    print(f"  {iid}: {op}")
