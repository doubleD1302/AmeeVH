import json
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
ENTRIES_DIR = ROOT / "work" / "research" / "data_200_decrypted" / "entries"

ag_file = ENTRIES_DIR / "00557_0x988f7b6f2592bacd.bin"
mp_file = ENTRIES_DIR / "00671_0xee9e1d54770d965d.bin"
item_file = ENTRIES_DIR / "00653_0xe60634348b826f41.bin"

ag_data = json.loads(ag_file.read_text(encoding="utf-8"))
mp_data = json.loads(mp_file.read_text(encoding="utf-8"))
item_data = json.loads(item_file.read_text(encoding="utf-8"))

ag_list = json.loads((ROOT / "work/batches/ag_to_translate.json").read_text(encoding="utf-8"))
mp_list = json.loads((ROOT / "work/batches/mp_to_translate.json").read_text(encoding="utf-8"))

print(f"AG strings: {len(ag_list)}, MP strings: {len(mp_list)}")

# Map AG strings to keys
ag_keys = {}
for s in ag_list:
    for k, v in ag_data.items():
        if v == s:
            ag_keys.setdefault(s, []).append(k)
print(f"Mapped {len(ag_keys)} / {len(ag_list)} AG strings to keys.")

# Map MP strings to keys
mp_keys = {}
for s in mp_list:
    for k, v in mp_data.items():
        if v == s:
            mp_keys.setdefault(s, []).append(k)
print(f"Mapped {len(mp_keys)} / {len(mp_list)} MP strings to keys.")
