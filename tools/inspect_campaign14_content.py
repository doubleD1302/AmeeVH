# -*- coding: utf-8 -*-
import json
from pathlib import Path
from collections import Counter
import re

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
CAMPAIGN_DIR = ROOT / "work/editorial/event_stories_part2_editorial_20261025_r01"

with open(CAMPAIGN_DIR / "CAMPAIGN_14_SOURCE_ALL.json", "r", encoding="utf-8") as f:
    items = json.load(f)

print(f"Loaded {len(items)} items.")

# 1. Analyze tokens
tokens_counter = Counter()
for it in items:
    for t in it['tokens']:
        tokens_counter[t] += 1

print("\nTop 20 tokens in Campaign 14:")
for t, cnt in tokens_counter.most_common(20):
    print(f"  {t}: {cnt}")

# 2. Check unclosed size tags
unclosed_size_count = 0
for it in items:
    en = it['en']
    open_sizes = re.findall(r'<size=[^>]+>', en)
    close_sizes = re.findall(r'</size>', en)
    if len(open_sizes) > len(close_sizes):
        unclosed_size_count += 1
print(f"\nLines with unclosed <size=XX> tags: {unclosed_size_count}")

# 3. Check scenes breakdown
scenes = Counter(it['scene_id'] for it in items)
print("\nScenes count breakdown:")
for sc, cnt in sorted(scenes.items()):
    print(f"  {sc:15s}: {cnt:4d} lines")
