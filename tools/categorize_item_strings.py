import json, re
from pathlib import Path

lines = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\batches\item_untranslated_strings.txt").read_text(encoding="utf-8").splitlines()

categories = {
    "furniture_tag": [],
    "furniture_set": [],
    "title_season": [],
    "unlock_title": [],
    "proof": [],
    "titles_prefix_suffix": [],
    "short_names": [],
    "flavor_or_other": []
}

for l in lines:
    s = l.replace("\\n", "\n")
    if re.match(r"^\[(Wallpaper|Flooring|Elevator|Furniture|Ornament|Rug|Special)\]", s):
        categories["furniture_tag"].append(s)
    elif "furniture set for decorating" in s:
        categories["furniture_set"].append(s)
    elif re.match(r"^Season \d+ Survival Champ", s):
        categories["title_season"].append(s)
    elif s.startswith("Unlocks the Honor Title:") or s.startswith("Unlocks the Avatar:"):
        categories["unlock_title"].append(s)
    elif s.startswith("The proof of") or s.startswith("Proof of"):
        categories["proof"].append(s)
    elif s.startswith("Prefix Title:") or s.startswith("Suffix Title:"):
        categories["titles_prefix_suffix"].append(s)
    elif len(s.split()) <= 4 and "\n" not in s:
        categories["short_names"].append(s)
    else:
        categories["flavor_or_other"].append(s)

for k, v in categories.items():
    print(f"{k}: {len(v)} strings")
    for sample in v[:3]:
        print(f"  e.g. {repr(sample[:60])}")
