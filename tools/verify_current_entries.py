import json
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
entries = ROOT / "work" / "research" / "data_200_decrypted" / "entries"

discip = json.loads((entries / "00867_0x5d07838c4787cc54.bin").read_text(encoding="utf-8"))
item = json.loads((entries / "00900_0xdb546f14f2f79a11.bin").read_text(encoding="utf-8"))
mainskill = json.loads((entries / "00914_0xb09952a17d27201c.bin").read_text(encoding="utf-8"))
secskill = json.loads((entries / "00962_0x439a5df5068af46c.bin").read_text(encoding="utf-8"))
skill = json.loads((entries / "00963_0xe2b9fc03308736f9.bin").read_text(encoding="utf-8"))

print("=== CHECK DISCS ===")
test_discs = [211001, 213013, 214058, 214066, 214067]
for did in test_discs:
    print(f"Disc {did}: DiscIP.3={repr(discip.get(f'DiscIP.{did}.3'))} | Item.1={repr(item.get(f'Item.{did}.1'))}")

print("\n=== CHECK SKILLS ===")
test_skills = ["Skill.101000103.1", "Skill.100011102.1", "MainSkill.300101.1", "SecondarySkill.3014101.1"]
for k in test_skills:
    tname = k.split(".")[0]
    table = {"Skill": skill, "MainSkill": mainskill, "SecondarySkill": secskill}[tname]
    print(f"{k} = {repr(table.get(k))}")
