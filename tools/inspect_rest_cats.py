import json
import re

rest = json.load(open(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\batches\item_rest_to_translate.json", encoding="utf-8"))

cats = {
    "dorm_tags": [],
    "camp_includes": [],
    "titles": [],
    "firstlight": [],
    "traits_gems": [],
    "tickets_packs": [],
    "dorm_furniture": [],
    "dorm_flavors": [],
    "other": []
}

for s in rest:
    if re.match(r"^\[(Wallpaper|Flooring|Elevator|Furniture|Ornament|Rug|Special|Wall decor)\]", s):
        cats["dorm_tags"].append(s)
    elif s.startswith("Includes "):
        cats["camp_includes"].append(s)
    elif "Title:" in s or s.startswith("Unlocks the Honor Title:") or s.startswith("Unlocks the Avatar:"):
        cats["titles"].append(s)
    elif "Firstlight" in s:
        cats["firstlight"].append(s)
    elif s.startswith("Simple Camping Set") or s.startswith("Chic ") or s.startswith("Cozy ") or s.startswith("Basic ") or s.startswith("Camp ") or s.startswith("Log Stool"):
        cats["dorm_furniture"].append(s)
    elif len(s.split()) <= 4 and "\n" not in s:
        cats["traits_gems"].append(s)
    else:
        cats["other"].append(s)

for k, v in cats.items():
    print(f"{k}: {len(v)}")
