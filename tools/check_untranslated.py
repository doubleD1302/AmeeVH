import json
import re

with open(r'c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\editorial\side_stories_part2_editorial_20261025_r01\PARTITION_B_SOURCE.json', 'r', encoding='utf-8') as f:
    items = json.load(f)

print(f"Total items: {len(items)}")

untranslated = []
for it in items:
    iid = it['id']
    en = it.get('en', '')
    vi = it.get('current_vi', '')
    # Check if vi is almost identical to en or contains untranslated English sentences
    if vi == en:
        untranslated.append((iid, en))
    elif re.search(r'\b(isn\'t|don\'t|doesn\'t|can\'t|won\'t|about that|excuse me|let me guess|pretty much)\b', vi, re.I):
        untranslated.append((iid, vi))

print(f"Untranslated or half-translated count: {len(untranslated)}")
for u in untranslated:
    print(' ', u)
