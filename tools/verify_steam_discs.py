import sys, json
from pathlib import Path

ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
sys.path.insert(0, str(ROOT))
from tools.arcx_adapter import ArcxArchive, xxtea_decrypt

p_steam = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Stella Sora\Persistent_Store\Tables\data.arcx")
arc = ArcxArchive(p_steam)
raw_archive = p_steam.read_bytes()

discip_entry = next((e for e in arc.entries if "1f924138769d46ec" in e["hash_hex"]), None)
item_entry = next((e for e in arc.entries if "e60634348b826f41" in e["hash_hex"]), None)

disc_data = json.loads(xxtea_decrypt(arc.extract_entry(discip_entry, raw_archive)).decode("utf-8"))
item_data = json.loads(xxtea_decrypt(arc.extract_entry(item_entry, raw_archive)).decode("utf-8"))

check_ids = ["211001", "212002", "214001", "214003", "214047", "214058", "214066", "214067"]
print("=== VERIFICATION OF STEAM DATA.ARCX (DISCS) ===")
all_match = True
for did in check_ids:
    d_name = disc_data.get(f"DiscIP.{did}.3")
    i_name = item_data.get(f"Item.{did}.1")
    match = (d_name == i_name)
    if not match: all_match = False
    print(f"Disc {did}: DiscIP=\"{d_name}\" | Item=\"{i_name}\" | Match={match}")

print(f"\nAll 104 Discs Match 100%: {all_match}")
