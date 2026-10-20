import sys, json
sys.path.append(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\tools")
from test_unmapped import unmapped
untr = json.load(open(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\batches\untranslated_unique.json", encoding="utf-8"))
occ_map = {d["en"]: d["occurrences"] for d in untr}

mp = [s for s in unmapped if any(occ[0] == "MallPackage" for occ in occ_map.get(s, []))]
ag = [s for s in unmapped if any(occ[0] == "ActivityGoods" for occ in occ_map.get(s, []))]

with open(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\batches\mp_to_translate.json", "w", encoding="utf-8") as f:
    json.dump(mp, f, indent=2, ensure_ascii=False)

with open(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\batches\ag_to_translate.json", "w", encoding="utf-8") as f:
    json.dump(ag, f, indent=2, ensure_ascii=False)

print(f"Dumped {len(mp)} MP and {len(ag)} AG")
