import json
from pathlib import Path

with open('StellaSora_VietHoa/tools/story_chapters_dump.json', 'r', encoding='utf-8') as f:
    chapters = json.load(f)

print("Scanning all 196 Story chapters...")
for cid, fields in list(chapters.items())[:35]:
    t = fields.get('1', {})
    d = fields.get('2', {})
    c = fields.get('4', {})
    print(f"[{cid}]")
    print(f"  Title: EN='{t.get('en')}' | CN='{t.get('cn')}' | VI='{t.get('vi')}'")
    print(f"  Desc:  EN='{d.get('en')}' | CN='{d.get('cn')}' | VI='{d.get('vi')}'")
    if c.get('en') not in ('BT01', 'BT02', 'BT03', 'BT04', '01A', '02A', '03A', '04A', '05A', '06A', '1', '2', '3'):
        print(f"  Code:  EN='{c.get('en')}' | CN='{c.get('cn')}' | VI='{c.get('vi')}'")
