import json
import re

with open(r'c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\editorial\side_stories_part2_editorial_20261025_r01\PARTITION_B_SOURCE.json', 'r', encoding='utf-8') as f:
    items = json.load(f)

patterns = [
    r'bạn biết đấy',
    r'làm sao mà',
    r'cái quái gì',
    r'cái quái',
    r'chết tiệt',
    r'không có cách nào',
    r'người đàn ông',
    r'bạn biết không',
    r'làm thế nào mà',
]

for it in items:
    vi = it.get('current_vi', '')
    for p in patterns:
        if re.search(p, vi, re.I):
            print(f"[{p}] {it['id']}: EN: {it['en']}")
            print(f"       VI: {vi}\n")
