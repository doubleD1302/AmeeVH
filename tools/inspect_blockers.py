import json
from pathlib import Path

p = Path(r"StellaSora_VietHoa/work/subagents/act3_story_editorial_20261024_r01/qa_reviewer_act3/QA_FINDINGS.json")
data = json.load(open(p, encoding="utf-8"))
for f in data.get("findings", []):
    if f.get("severity") == "BLOCKER":
        print(f"[{f.get('id')}] {f.get('issue')}")
        print("  EN:", repr(f.get("en"))[:80])
        print("  VI:", repr(f.get("vi"))[:80])
