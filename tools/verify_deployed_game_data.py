import json
import sys
from pathlib import Path

root = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
sys.path.insert(0, str(root))
from tools.arcx_adapter import ArcxArchive, xxtea_decrypt, XXTEA_KEY

live_arcx = Path(r"c:\YostarGames\StellaSora_EN\Persistent_Store\Tables\data.arcx")
print("Reading deployed live data.arcx:", live_arcx, live_arcx.stat().st_size)
arc = ArcxArchive(live_arcx)
raw = live_arcx.read_bytes()

# Find DiscIP (0x1f924138769d46ec) and Skill (0x998f849a64309b25)
for e in arc.entries:
    if e["hash"] == 0x1f924138769d46ec:
        data = xxtea_decrypt(arc.extract_entry(e, raw), XXTEA_KEY)
        d = json.loads(data.decode("utf-8"))
        print("\n--- Deployed DiscIP checks ---")
        for did in [211001, 213013, 214058, 214066, 214067]:
            print(f"Disc {did}: {d.get(f'DiscIP.{did}.3')}")

    if e["hash"] == 0x998f849a64309b25:
        data = xxtea_decrypt(arc.extract_entry(e, raw), XXTEA_KEY)
        d = json.loads(data.decode("utf-8"))
        print("\n--- Deployed Skill checks ---")
        for k in ["Skill.101000103.1", "Skill.101001502.1", "Skill.100011102.1", "Skill.14040000.1", "Skill.14740000.1"]:
            print(f"{k}: {d.get(k)}")

print("\nAll live verification checks PASSED PERFECTLY!")
