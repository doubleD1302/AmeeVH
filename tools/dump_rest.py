import sys, json
sys.path.append(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\tools")
from test_unmapped import unmapped
mp = json.load(open(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\batches\mp_to_translate.json", encoding="utf-8"))
ag = json.load(open(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\batches\ag_to_translate.json", encoding="utf-8"))
rest = [s for s in unmapped if s not in mp and s not in ag]

with open(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\batches\item_rest_to_translate.json", "w", encoding="utf-8") as f:
    json.dump(rest, f, indent=2, ensure_ascii=False)

print(f"Dumped {len(rest)} rest items to item_rest_to_translate.json")
