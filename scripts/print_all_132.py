import json
import re

with open('StellaSora_VietHoa/work/subagents/remediation_v110_20261029_r01/story/unique_binary_132.json', 'r', encoding='utf-8') as f:
    items = json.load(f)

for idx, it in enumerate(items):
    qid = it["id"]
    en = it["en"]
    vi = it["vi"]
    print(f"[{idx+1}] {qid}")
    print(f"  EN: {repr(en)}")
    print(f"  VI: {repr(vi)}")
