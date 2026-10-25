import json
import re

TAG_PATTERN = re.compile(r'<[^>]+>|==[A-Z0-9_-]+==|\{[0-9]+\}')

with open(r'c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\editorial\side_stories_part2_editorial_20261025_r01\PARTITION_B_SOURCE.json', 'r', encoding='utf-8') as f:
    items = json.load(f)

for it in items:
    en = it['en']
    vi = it.get('current_vi', '')
    
    en_tags = TAG_PATTERN.findall(en)
    vi_tags = TAG_PATTERN.findall(vi)
    
    if sorted(en_tags) != sorted(vi_tags):
        print(f"ID: {it['id']}")
        print(f"  EN tags: {en_tags}")
        print(f"  VI tags: {vi_tags}")
        print(f"  EN: {repr(en)}")
        print(f"  VI: {repr(vi)}")
        print()
