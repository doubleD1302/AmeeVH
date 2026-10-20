import json
import sys
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
sys.path.insert(0, str(ROOT / "tools"))
from pillar1_translations_part1 import TRANSLATIONS_BASEINFO, TRANSLATIONS_DES

ENTRIES_DIR = ROOT / "work" / "research" / "data_200_decrypted" / "entries"
baseinfo_file = ENTRIES_DIR / "00592_0x200c969f988e4634.bin"
des_file = ENTRIES_DIR / "00596_0x189f915177d3b2ff.bin"

baseinfo_data = json.loads(baseinfo_file.read_text(encoding="utf-8"))
des_data = json.loads(des_file.read_text(encoding="utf-8"))

mods = []

for k, v in TRANSLATIONS_BASEINFO.items():
    orig = baseinfo_data.get(k, "")
    if orig != v:
        baseinfo_data[k] = v
        mods.append({
            "table": "CharacterArchiveBaseInfo",
            "key": k,
            "before": orig,
            "after": v,
            "category": "Hẹn Hò & Nhân Vật",
            "reason": "Trau chuốt lý lịch nhân vật tự nhiên, dí dỏm, thuần Việt",
            "agent": "Dating & Character Specialist Subagent",
            "timestamp": "2026-10-21 01:55:00"
        })

for k, v in TRANSLATIONS_DES.items():
    orig = des_data.get(k, "")
    if orig != v:
        des_data[k] = v
        mods.append({
            "table": "CharacterDes",
            "key": k,
            "before": orig,
            "after": v,
            "category": "Hẹn Hò & Nhân Vật",
            "reason": "Trau chuốt lối chơi và tiểu sử nhân vật đậm chất anime RPG hào hùng",
            "agent": "Dating & Character Specialist Subagent",
            "timestamp": "2026-10-21 01:55:00"
        })

baseinfo_file.write_text(json.dumps(baseinfo_data, indent=2, ensure_ascii=False), encoding="utf-8")
des_file.write_text(json.dumps(des_data, indent=2, ensure_ascii=False), encoding="utf-8")

print(f"Applied {len(mods)} character translations to BaseInfo and CharacterDes.")

# Append to audit_batch1_modifications.json
b1_mod_path = ROOT / "work" / "batches" / "audit_batch1_modifications.json"
b1_mods = json.loads(b1_mod_path.read_text(encoding="utf-8"))
b1_mods.extend(mods)
b1_mod_path.write_text(json.dumps(b1_mods, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"audit_batch1_modifications.json now has {len(b1_mods)} items.")
