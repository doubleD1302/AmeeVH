import json
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
entries_dir = ROOT / "work" / "research" / "data_decrypted" / "entries"

table_map = {}
for f in entries_dir.glob("*.bin"):
    try:
        data = json.loads(f.read_text(encoding='utf-8'))
        first_key = next(iter(data.keys()), "")
        table_name = first_key.split(".")[0] if "." in first_key else ""
        table_map[table_name] = f.name
    except Exception as e:
        pass

for target in ["DiscIP", "Item", "MainSkill", "SecondarySkill", "Skill", "Potential", "Talent"]:
    print(f"{target} -> {table_map.get(target, 'NOT FOUND')}")
