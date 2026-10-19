import json
from pathlib import Path
from collections import defaultdict

ROOT = Path(r"C:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
JSON_PATH = ROOT / "work" / "research" / "uitext_to_translate.json"

with open(JSON_PATH, "r", encoding="utf-8") as f:
    items = json.load(f)

# Group keys by major domain (prefix before first underscore or dot)
domains = defaultdict(list)
for k, v in items.items():
    p = k.split(".")[1] if "." in k else k
    dom = p.split("_")[0]
    domains[dom].append((k, v["en"], v["cn"]))

print(f"Total domains: {len(domains)}")
sorted_doms = sorted(domains.items(), key=lambda x: -len(x[1]))
for dom, entries in sorted_doms:
    print(f"{dom:20s}: {len(entries):4d} items | e.g. {entries[0][0]} -> {entries[0][1]!r} (CN: {entries[0][2]!r})")
