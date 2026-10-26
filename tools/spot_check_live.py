import json
from pathlib import Path
import sys
ROOT = Path(r"c:\YostarGames\StellaSora_EN\StellaSora_VietHoa")
sys.path.insert(0, str(ROOT / "tools"))
from arcx_adapter import ArcxArchive, xxtea_decrypt, XXTEA_KEY

live_data = Path(r"c:\YostarGames\StellaSora_EN\Persistent_Store\Tables\data.arcx")
arc = ArcxArchive(live_data)
raw = live_data.read_bytes()

targets = {
    "Potential.511025.2": None,
    "Agent.300303.3": None,
    "Item.11103.2": None,
    "UIText.GachaCover7.1": None,
    "DiscIP.211001.3": None
}

for e in arc.entries:
    try:
        data = xxtea_decrypt(arc.extract_entry(e, raw), XXTEA_KEY)
        d = json.loads(data.decode("utf-8"))
        if isinstance(d, dict):
            for k in targets:
                if k in d:
                    targets[k] = d[k]
    except Exception:
        pass

for k, v in targets.items():
    print(f"{k}: {v[:80] if v else 'NOT FOUND'}")
