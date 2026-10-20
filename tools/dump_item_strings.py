import json
from pathlib import Path

f = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\batches\untranslated_unique.json")
data = json.loads(f.read_text(encoding="utf-8"))

item_strings = [d["en"] for d in data if any(occ[0] == "Item" for occ in d["occurrences"])]
print(f"Total Item unique untranslated: {len(item_strings)}")

with open(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\batches\item_untranslated_strings.txt", "w", encoding="utf-8") as out:
    for s in item_strings:
        out.write(s.replace("\n", "\\n") + "\n")

print("Saved to item_untranslated_strings.txt")
