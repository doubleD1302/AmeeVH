import json

with open('StellaSora_VietHoa/work/subagents/remediation_v110_20261029_r01/story/en_defects.json', 'r', encoding='utf-8') as f:
    items = json.load(f)

for it in items:
    print("File:", it["file"], "| ID:", it["id"])
    print("EN:", repr(it["en"]))
    print("VI:", repr(it["vi"]))
    print("-" * 50)
