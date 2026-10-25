import json
from pathlib import Path
import sys

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
sys.path.insert(0, str(ROOT))
from tools.polish_discs_list import DISC_POLISH_PROPOSALS
from tools.polish_skills_list import SKILL_POLISH_PROPOSALS

entries = ROOT / "work" / "research" / "data_200_decrypted" / "entries"
discip = json.loads((entries / "00620_0x1f924138769d46ec.bin").read_text(encoding="utf-8"))
item = json.loads((entries / "00653_0xe60634348b826f41.bin").read_text(encoding="utf-8"))
mainskill = json.loads((entries / "00667_0x57e760255c1d3b2d.bin").read_text(encoding="utf-8"))
secskill = json.loads((entries / "00715_0x31a8814a91313129.bin").read_text(encoding="utf-8"))
skill = json.loads((entries / "00716_0x998f849a64309b25.bin").read_text(encoding="utf-8"))

print("=== AUDIT DISCS CURRENT STATUS ===")
for did, info in DISC_POLISH_PROPOSALS.items():
    dk = f"DiscIP.{did}.3"
    ik = f"Item.{did}.1"
    cur_d = discip.get(dk, "<MISSING>")
    cur_i = item.get(ik, "<MISSING>")
    print(f"[{did}] {info[0]} | DiscIP: {repr(cur_d)} | Item: {repr(cur_i)} | Target: {repr(info[4])}")

print("\n=== AUDIT SKILLS CURRENT STATUS ===")
table_map = {"Skill": skill, "MainSkill": mainskill, "SecondarySkill": secskill}
for k, v in SKILL_POLISH_PROPOSALS.items():
    tname = k.split(".")[0]
    cur_v = table_map[tname].get(k, "<MISSING>")
    print(f"[{k}] {v[0]} | Cur: {repr(cur_v)} | Target: {repr(v[3])}")
