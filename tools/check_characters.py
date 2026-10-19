import json
import os

p4_path = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\batches\pillar4_system_gacha_shops.json"
p2_path = r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\work\batches\pillar2_voices_characters.json"

with open(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa\config\master_glossary.json", "r", encoding="utf-8") as f:
    mg = json.load(f)
terms = mg.get("terms", {})
terms_lower = {k.lower(): v for k, v in terms.items()}

# Characters
with open(p4_path, "r", encoding="utf-8") as f:
    p4_data = json.load(f)
with open(p2_path, "r", encoding="utf-8") as f:
    p2_data = json.load(f)

chars = set()
for k, v in p4_data.get("Character", {}).get("entries", {}).items():
    chars.add(v)

for k, v in p2_data.get("CharacterDes", {}).get("entries", {}).items():
    if k.endswith(".2"):
        chars.add(v)

print(f"Total characters found: {len(chars)}")
for c in sorted(chars):
    in_glossary = c.lower() in terms_lower
    print(f"  {c:25}: in_glossary={in_glossary} ({terms_lower.get(c.lower(), 'MISSING')})")
