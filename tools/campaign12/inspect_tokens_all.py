import json
import re

TAG_PATTERN = re.compile(r'<[^>]+>|==[A-Z0-9_-]+==|\{[0-9]+\}')

for pref in ["stsp_09", "stsp_10", "stsp_11"]:
    with open(f"c:/YostarGames/StellaSora_EN/StellaSora_VietHoa/tools/campaign12/{pref}_items.json", "r", encoding="utf-8") as f:
        items = json.load(f)
    print(f"=== {pref.upper()} TOKENS ({len(items)} items) ===")
    for it in items:
        toks = TAG_PATTERN.findall(it["en"])
        if toks:
            print(it["id"], "TOKENS:", toks, "| EN:", repr(it["en"]))
