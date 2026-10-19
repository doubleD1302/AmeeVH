import json

with open(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\candidates_survey.json", "r", encoding="utf-8") as f:
    candidates = json.load(f)

skins = [c for c in candidates.values() if c["category"] == "Trang Phục Nhân Vật"]

print(f"Total Character Skins: {len(skins)}")
for i, s in enumerate(skins):
    print(f"{i+1:3}. {s['en']:45} | CN: {s['cn']}")
