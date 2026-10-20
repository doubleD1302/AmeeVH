import json
from pathlib import Path

# Let's inspect short_names and flavor_or_other
import sys
sys.path.append(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\tools")
from categorize_item_strings import categories

with open(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\batches\item_short_names.txt", "w", encoding="utf-8") as out:
    for s in categories["short_names"]:
        out.write(s + "\n")

with open(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\batches\item_flavors.txt", "w", encoding="utf-8") as out:
    for s in categories["flavor_or_other"]:
        out.write(s.replace("\n", "\\n") + "\n")

print(f"Wrote {len(categories['short_names'])} short names and {len(categories['flavor_or_other'])} flavors.")
