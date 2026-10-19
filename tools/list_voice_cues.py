import json

with open(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\candidates_survey.json", "r", encoding="utf-8") as f:
    candidates = json.load(f)

cues = [c for c in candidates.values() if c["category"] == "Phân Loại Lồng Tiếng"]
print(f"Total voice cues: {len(cues)}")
# Unique base cues
base_cues = {}
for c in cues:
    en = c["en"]
    cn = c["cn"]
    base_cues[en] = cn

for en, cn in sorted(base_cues.items()):
    print(f"  {en:40} | CN: {cn}")
