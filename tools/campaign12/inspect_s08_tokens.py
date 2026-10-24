import json
import re

TAG_PATTERN = re.compile(r'<[^>]+>|==[A-Z0-9_-]+==|\{[0-9]+\}')

with open("c:/YostarGames/StellaSora_EN/StellaSora_VietHoa/tools/campaign12/stsp_08_items.json", "r", encoding="utf-8") as f:
    items = json.load(f)

for it in items:
    toks = TAG_PATTERN.findall(it["en"])
    if toks:
        print(it["id"], "TOKENS:", toks, "| EN:", repr(it["en"]))
