import json

with open(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\candidates_survey.json", "r", encoding="utf-8") as f:
    candidates = json.load(f)

monsters = [c for c in candidates.values() if c["category"] == "Quái vật & Boss"]

print("=== Monsters 1 to 100 ===")
for i, m in enumerate(monsters[:100]):
    print(f"{i+1:3}. {m['en']:38} | CN: {m['cn']}")

print("\n=== Monsters 101 to 191 ===")
for i, m in enumerate(monsters[100:191], start=101):
    print(f"{i:3}. {m['en']:38} | CN: {m['cn']}")
